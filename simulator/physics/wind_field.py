"""
Wind field model with realistic statistical properties and spatial propagation.

Features:
  - Weibull distribution for long-term wind speed statistics
  - Autocorrelated turbulence (Kaimal-like spectrum, not white noise)
  - Coherent wind direction changes with inertia
  - Temperature daily cycle with realistic amplitude
  - Wind farm layout with turbine positions
  - Spatial wind event propagation (gust, ramp, direction shift)
  - Direction-aware wake effects

Can be used standalone or as part of the simulator.
Separate from wind_model.py (which handles profiles/overrides).
"""

import math
import numpy as np
from typing import Optional, List, Tuple
from dataclasses import dataclass


class TurbulenceGenerator:
    """
    Generates autocorrelated turbulence using an AR(1) process.

    Instead of white noise (random at every timestep), this produces
    realistic wind speed fluctuations with temporal correlation.

    Kaimal spectrum approximation:
      τ_turb ≈ L_u / V_mean  (L_u = integral length scale ≈ 340m for hub height 90m)

    At 12 m/s: τ ≈ 340/12 ≈ 28 seconds → fluctuations persist for ~30s
    """

    def __init__(self, seed: Optional[int] = None):
        self._rng = np.random.RandomState(seed)
        self._state = 0.0  # AR(1) state

    def step(self, mean_speed: float, turbulence_intensity: float,
             dt: float) -> float:
        """
        Generate turbulence component (m/s) for one timestep.

        Args:
            mean_speed: Mean wind speed (m/s)
            turbulence_intensity: TI (typically 0.08-0.20)
            dt: Timestep (seconds)

        Returns:
            Turbulence fluctuation (m/s), to be added to mean speed
        """
        if mean_speed < 0.5:
            self._state = 0.0
            return 0.0

        # Integral length scale (IEC 61400-1, hub height 90m)
        L_u = 340.0  # meters
        tau = L_u / max(mean_speed, 1.0)  # correlation time scale

        # AR(1) coefficient
        alpha = math.exp(-dt / tau)

        # Standard deviation of wind speed fluctuation
        sigma = mean_speed * turbulence_intensity

        # Driving noise (scaled for correct variance)
        noise = self._rng.normal(0, sigma * math.sqrt(1 - alpha ** 2))

        # AR(1) update
        self._state = alpha * self._state + noise

        return self._state


class WindDirectionModel:
    """
    Wind direction with realistic inertia and slow drift.

    Wind direction doesn't jump randomly — it has inertia from
    large-scale weather patterns, with small random perturbations.
    """

    def __init__(self, initial_direction: float = 270.0, seed: Optional[int] = None):
        self._rng = np.random.RandomState(seed)
        self.direction = initial_direction
        self._drift_rate = 0.0  # °/s, slowly varying

    def step(self, dt: float, override: Optional[float] = None) -> float:
        """Advance wind direction by one timestep."""
        if override is not None:
            # Manual override with small sensor noise
            return (override + self._rng.normal(0, 1.5)) % 360

        # Drift rate evolves slowly (random walk with mean reversion)
        self._drift_rate += self._rng.normal(0, 0.001 * dt)
        self._drift_rate *= 0.998  # decay towards zero
        self._drift_rate = max(-0.5, min(0.5, self._drift_rate))  # ±0.5 °/s max

        # Apply drift + small perturbation
        self.direction += self._drift_rate * dt + self._rng.normal(0, 0.3 * dt)
        self.direction %= 360

        return self.direction


# ─── Wind Farm Layout ───────────────────────────────────────────────────

@dataclass
class TurbinePosition:
    """Position of a turbine in the wind farm (meters, local coordinate system)."""
    x: float  # East-West (positive = East)
    y: float  # North-South (positive = North)


@dataclass
class TurbulencePocket:
    """A localized turbulence pocket (small-scale coherent eddy).

    Affects TI (turbulence intensity) only within its Gaussian influence
    radius, without shifting the mean wind speed. Represents convective
    structures, boundary-layer eddies, or broken-up upstream wakes with
    spatial scale ~100–500 m and lifetime ~30–180 s.
    """
    center_x: float          # pocket center position, east (m)
    center_y: float          # pocket center position, north (m)
    radius_m: float          # Gaussian 1-sigma radius (m)
    ti_multiplier: float     # TI boost at pocket center (e.g. 1.8 = +80%)
    origin_time: float       # sim_time when pocket was created
    rise_time: float         # seconds to ramp up to peak
    hold_time: float         # seconds at peak
    fall_time: float         # seconds to ramp down


def default_farm_layout(count: int = 14, spacing_m: float = 500.0) -> List[TurbinePosition]:
    """Generate a default wind farm layout.

    Uses a staggered 2-row grid typical for offshore/flat terrain farms.
    Row spacing is ~7D (rotor diameters), column spacing is ~5D.
    """
    positions = []
    cols = (count + 1) // 2
    for i in range(count):
        row = i // cols           # 0 or 1
        col = i % cols            # column index
        x = col * spacing_m + row * (spacing_m * 0.5)  # stagger offset
        y = row * spacing_m * 0.7
        positions.append(TurbinePosition(x=x, y=y))
    return positions


# ─── Wind Event Propagation ─────────────────────────────────────────────

@dataclass
class WindEvent:
    """A propagating wind event (gust, ramp, or direction shift)."""
    event_type: str        # "gust", "ramp", "direction_shift"
    origin_time: float     # sim_time when event was created
    speed_delta: float     # wind speed change (m/s), 0 for direction events
    direction_delta: float # direction change (degrees), 0 for speed events
    duration: float        # how long the event lasts at each point (seconds)
    propagation_speed: float  # how fast the front moves (m/s), typically ~wind speed
    propagation_direction: float  # direction the front moves FROM (degrees, meteorological)
    rise_time: float       # seconds to ramp up
    fall_time: float       # seconds to ramp down


class WindEventPropagation:
    """Manages propagating wind events across the farm.

    Wind events (gusts, ramps, direction shifts) don't hit all turbines
    simultaneously. They propagate as a "wave front" across the farm,
    with upwind turbines affected first and downwind turbines later.

    The time delay for each turbine depends on:
    - Its position projected along the propagation direction
    - The propagation speed (typically ~0.8× mean wind speed)
    """

    def __init__(self, positions: List[TurbinePosition], seed: int = 0):
        self._positions = positions
        self._rng = np.random.RandomState(seed)
        self._active_events: List[WindEvent] = []
        self._sim_time = 0.0

        # Pre-compute position arrays
        self._x = np.array([p.x for p in positions])
        self._y = np.array([p.y for p in positions])

    def add_event(self, event: WindEvent):
        """Queue a wind event (gust, ramp, direction shift) for farm-wide propagation."""
        self._active_events.append(event)

    def generate_natural_events(self, mean_wind: float, dt: float):
        """Stochastically generate natural wind events based on conditions.

        Higher wind speeds → more frequent gusts.
        Probability calibrated so events feel natural, not overwhelming.
        """
        # Gust probability: ~1 every 10-20 minutes at moderate wind
        gust_prob = dt * (0.0005 + 0.0003 * max(0, mean_wind - 6.0))
        if self._rng.uniform() < gust_prob:
            amplitude = self._rng.uniform(1.5, 4.0) * (mean_wind / 12.0)
            self._active_events.append(WindEvent(
                event_type="gust",
                origin_time=self._sim_time,
                speed_delta=amplitude,
                direction_delta=0.0,
                duration=self._rng.uniform(8.0, 25.0),
                propagation_speed=max(5.0, mean_wind * self._rng.uniform(0.6, 0.9)),
                propagation_direction=self._rng.uniform(0, 360),
                rise_time=self._rng.uniform(2.0, 5.0),
                fall_time=self._rng.uniform(4.0, 10.0),
            ))

        # Ramp probability: ~1 every 30-60 minutes
        ramp_prob = dt * 0.0002
        if self._rng.uniform() < ramp_prob:
            self._active_events.append(WindEvent(
                event_type="ramp",
                origin_time=self._sim_time,
                speed_delta=self._rng.uniform(-3.0, 3.0),
                direction_delta=0.0,
                duration=self._rng.uniform(60.0, 300.0),
                propagation_speed=max(5.0, mean_wind * self._rng.uniform(0.5, 0.8)),
                propagation_direction=self._rng.uniform(0, 360),
                rise_time=self._rng.uniform(15.0, 45.0),
                fall_time=self._rng.uniform(20.0, 60.0),
            ))

        # Direction shift: ~1 every 20-40 minutes
        dir_prob = dt * 0.0003
        if self._rng.uniform() < dir_prob:
            self._active_events.append(WindEvent(
                event_type="direction_shift",
                origin_time=self._sim_time,
                speed_delta=0.0,
                direction_delta=self._rng.uniform(-15.0, 15.0),
                duration=self._rng.uniform(30.0, 120.0),
                propagation_speed=max(5.0, mean_wind * self._rng.uniform(0.5, 0.8)),
                propagation_direction=self._rng.uniform(0, 360),
                rise_time=self._rng.uniform(10.0, 30.0),
                fall_time=self._rng.uniform(15.0, 40.0),
            ))

    def step(self, dt: float) -> Tuple[np.ndarray, np.ndarray]:
        """Advance events and compute per-turbine speed/direction deltas.

        Returns:
            speed_deltas: array of wind speed changes per turbine (m/s)
            dir_deltas: array of direction changes per turbine (degrees)
        """
        self._sim_time += dt
        n = len(self._positions)
        speed_deltas = np.zeros(n)
        dir_deltas = np.zeros(n)

        # Remove expired events
        self._active_events = [
            e for e in self._active_events
            if self._sim_time - e.origin_time < e.duration + e.fall_time + self._max_delay(e) + 10.0
        ]

        for event in self._active_events:
            # Compute propagation delay for each turbine
            delays = self._compute_delays(event)

            for i in range(n):
                # Time since this turbine was reached by the event front
                local_time = self._sim_time - event.origin_time - delays[i]

                if local_time < 0:
                    continue  # Event hasn't reached this turbine yet

                # Compute event envelope (rise → hold → fall)
                amplitude = self._envelope(local_time, event)

                if event.event_type in ("gust", "ramp"):
                    speed_deltas[i] += event.speed_delta * amplitude
                elif event.event_type == "direction_shift":
                    dir_deltas[i] += event.direction_delta * amplitude

        return speed_deltas, dir_deltas

    def _compute_delays(self, event: WindEvent) -> np.ndarray:
        """Compute propagation delay (seconds) for each turbine.

        Project turbine positions onto the propagation direction axis.
        Turbines further upwind (negative projection) are hit first.
        """
        # Convert meteorological direction to propagation vector
        # "from" direction → vector points in the direction the wind blows TO
        angle_rad = math.radians(event.propagation_direction)
        dx = -math.sin(angle_rad)  # East component
        dy = -math.cos(angle_rad)  # North component

        # Project positions onto propagation axis
        projections = self._x * dx + self._y * dy

        # Normalize: most upwind turbine has delay=0
        proj_min = projections.min()
        relative_dist = projections - proj_min  # all >= 0

        # Delay = distance / propagation_speed
        delays = relative_dist / max(event.propagation_speed, 1.0)
        return delays

    def _max_delay(self, event: WindEvent) -> float:
        """Maximum delay across all turbines for this event."""
        delays = self._compute_delays(event)
        return float(delays.max())

    @staticmethod
    def _envelope(local_time: float, event: WindEvent) -> float:
        """Compute event amplitude envelope at a given local time.

        Shape: ramp up → hold → ramp down
        """
        if local_time < 0:
            return 0.0
        elif local_time < event.rise_time:
            # Smooth ramp up (cosine curve for natural feel)
            return 0.5 * (1.0 - math.cos(math.pi * local_time / event.rise_time))
        elif local_time < event.rise_time + event.duration:
            return 1.0
        elif local_time < event.rise_time + event.duration + event.fall_time:
            t_fall = local_time - event.rise_time - event.duration
            return 0.5 * (1.0 + math.cos(math.pi * t_fall / event.fall_time))
        else:
            return 0.0


# ─── Per-Turbine Wind (upgraded) ────────────────────────────────────────

class PerTurbineWind:
    """
    Generate per-turbine wind variations with spatial propagation.

    Each turbine sees different wind due to:
    - Spatial separation (decorrelation with per-turbine turbulence)
    - Wake effects (direction-aware)
    - Propagating wind events (gusts, ramps, direction shifts)
    - Local terrain effects (persistent offset)
    - Wind shear (power-law vertical wind profile)
    """

    def __init__(self, turbine_count: int, seed: int = 0,
                 positions: Optional[List[TurbinePosition]] = None,
                 spacing_m: float = 500.0,
                 wind_shear_exponent: float = 0.2,
                 rotor_diameter: float = 70.65):
        self._rng = np.random.RandomState(seed)
        self._count = turbine_count
        self.wind_shear_exponent = wind_shear_exponent
        self._rotor_diameter = rotor_diameter

        # Turbine positions
        self._positions = positions or default_farm_layout(turbine_count, spacing_m)

        # Persistent per-turbine characteristics
        self._offsets = self._rng.normal(0, 0.35, turbine_count)
        self._wake_factors = np.ones(turbine_count)
        self._wake_deficits = np.zeros(turbine_count)  # reported fraction 0..1

        # Per-turbine turbulence generators for spatial decorrelation
        self._turb_gens = [TurbulenceGenerator(seed=seed + 1000 + i) for i in range(turbine_count)]

        # Wind event propagation system
        self._propagation = WindEventPropagation(self._positions, seed=seed + 2000)

        # Localized turbulence pockets (small-scale spatial TI structures)
        self._pocket_rng = np.random.RandomState(seed + 3000)
        self._pockets: List[TurbulencePocket] = []
        self._pocket_sim_time = 0.0
        self._current_ti_multipliers = np.ones(turbine_count)

        # Dynamic wake meandering (Larsen et al. 2008 DWM):
        # lateral oscillation angle of each turbine's wake centerline.
        # σ_θ ≈ 0.3·TI, AR(1) with τ ≈ 25 s (atmospheric integral timescale)
        self._meander_rng = np.random.RandomState(seed + 4000)
        self._meander_angles = np.zeros(turbine_count)  # radians, lateral
        self._meander_ref_distance_m = 3.0 * rotor_diameter  # 3D reference

        # State
        self._current_speed_deltas = np.zeros(turbine_count)
        self._current_dir_deltas = np.zeros(turbine_count)
        self._current_direction = 270.0

    def step(self, farm_wind: float, wind_direction: float,
             turbulence_intensity: float, dt: float):
        """Advance wind field by one timestep.

        Must be called once per step BEFORE get_local_wind().
        """
        self._current_direction = wind_direction

        # Advance wake meandering state before computing wake factors
        self._update_wake_meander(turbulence_intensity, dt)

        # Update wake factors based on current wind direction, speed, and TI
        self._update_wake_factors(wind_direction, farm_wind, turbulence_intensity)

        # Generate natural wind events stochastically
        self._propagation.generate_natural_events(farm_wind, dt)

        # Advance event propagation
        self._current_speed_deltas, self._current_dir_deltas = self._propagation.step(dt)

        # Localized turbulence pockets: stochastic spawn + per-turbine TI multiplier
        self._update_turbulence_pockets(farm_wind, dt)

        # Per-turbine turbulence (spatial decorrelation) — pocket-boosted TI
        for i in range(self._count):
            ti_local = turbulence_intensity * 0.4 * self._current_ti_multipliers[i]
            turb = self._turb_gens[i].step(farm_wind, ti_local, dt)
            self._current_speed_deltas[i] += turb

    def get_local_wind(self, farm_wind: float, turbine_index: int) -> float:
        """Get local wind speed for a specific turbine."""
        idx = min(turbine_index, self._count - 1)
        local = (
            farm_wind * self._wake_factors[idx]
            + self._offsets[idx]
            + self._current_speed_deltas[idx]
        )
        return max(0.0, local)

    def get_local_direction(self, farm_direction: float, turbine_index: int) -> float:
        """Get local wind direction for a specific turbine."""
        idx = min(turbine_index, self._count - 1)
        return (farm_direction + self._current_dir_deltas[idx]) % 360

    def add_event(self, event: WindEvent):
        """Inject a wind event (for API/testing)."""
        self._propagation.add_event(event)

    def add_pocket(self, pocket: TurbulencePocket):
        """Inject a localized turbulence pocket (for API/testing)."""
        self._pockets.append(pocket)

    def get_local_ti_multiplier(self, turbine_index: int) -> float:
        """Effective TI multiplier (1.0 = baseline) at a turbine location."""
        idx = min(turbine_index, self._count - 1)
        return float(self._current_ti_multipliers[idx])

    def get_wake_deficit(self, turbine_index: int) -> float:
        """Wake deficit fraction at a turbine (0.0 = free stream, 0.6 = deep wake)."""
        idx = min(turbine_index, self._count - 1)
        return float(self._wake_deficits[idx])

    def get_wake_meander_offset(self, turbine_index: int) -> float:
        """Lateral offset (m) of this turbine's own wake at the 3D reference point.

        Positive = wake centerline deflected to the cross-stream "+y_perp" direction
        (left when looking downstream). Used for SCADA reporting; the full
        per-downstream offset is computed inside `_update_wake_factors`.
        """
        idx = min(turbine_index, self._count - 1)
        return float(self._meander_angles[idx] * self._meander_ref_distance_m)

    def _update_wake_meander(self, turbulence_intensity: float, dt: float):
        """Advance per-turbine wake meander angle as an AR(1) process.

        Larsen DWM statistics:
            σ_y(x) ≈ 0.3 · σ_v · (x / U_∞)  =>  σ_θ ≈ 0.3 · TI   (radians)
            τ_m ≈ L_u / U ≈ 25 s   (atmospheric integral timescale)
        """
        tau = 25.0
        alpha = math.exp(-max(dt, 0.0) / tau)
        sigma_theta = 0.3 * max(turbulence_intensity, 0.02)
        noise_scale = sigma_theta * math.sqrt(max(0.0, 1.0 - alpha * alpha))
        for i in range(self._count):
            eta = self._meander_rng.normal(0.0, noise_scale) if noise_scale > 0 else 0.0
            self._meander_angles[i] = alpha * self._meander_angles[i] + eta

    def _update_turbulence_pockets(self, farm_wind: float, dt: float):
        """Spawn / expire pockets and compute per-turbine TI multipliers."""
        self._pocket_sim_time += dt

        # Stochastic spawn: mean ~1 pocket per 10–15 min at 10 m/s
        spawn_prob = dt * (0.0006 + 0.0004 * max(0.0, farm_wind - 6.0))
        if self._pocket_rng.uniform() < spawn_prob and self._count > 0:
            anchor = int(self._pocket_rng.randint(0, self._count))
            jitter_x = self._pocket_rng.uniform(-250.0, 250.0)
            jitter_y = self._pocket_rng.uniform(-250.0, 250.0)
            self._pockets.append(TurbulencePocket(
                center_x=self._positions[anchor].x + jitter_x,
                center_y=self._positions[anchor].y + jitter_y,
                radius_m=float(self._pocket_rng.uniform(180.0, 380.0)),
                ti_multiplier=float(self._pocket_rng.uniform(1.4, 2.0)),
                origin_time=self._pocket_sim_time,
                rise_time=float(self._pocket_rng.uniform(10.0, 25.0)),
                hold_time=float(self._pocket_rng.uniform(25.0, 90.0)),
                fall_time=float(self._pocket_rng.uniform(15.0, 40.0)),
            ))

        # Expire pockets past their full envelope
        self._pockets = [
            p for p in self._pockets
            if self._pocket_sim_time - p.origin_time < p.rise_time + p.hold_time + p.fall_time
        ]

        # Compute per-turbine TI multiplier: 1 + Σ(boost × Gaussian spatial weight × envelope)
        self._current_ti_multipliers = np.ones(self._count)
        for p in self._pockets:
            local_time = self._pocket_sim_time - p.origin_time
            if local_time < p.rise_time:
                env = 0.5 * (1.0 - math.cos(math.pi * local_time / max(p.rise_time, 1e-3)))
            elif local_time < p.rise_time + p.hold_time:
                env = 1.0
            else:
                t_fall = local_time - p.rise_time - p.hold_time
                env = 0.5 * (1.0 + math.cos(math.pi * t_fall / max(p.fall_time, 1e-3)))
            boost = max(0.0, p.ti_multiplier - 1.0) * env
            r2 = 2.0 * p.radius_m * p.radius_m
            for i in range(self._count):
                dx = self._positions[i].x - p.center_x
                dy = self._positions[i].y - p.center_y
                weight = math.exp(-(dx * dx + dy * dy) / max(r2, 1.0))
                self._current_ti_multipliers[i] += boost * weight

    def _update_wake_factors(self, wind_direction: float,
                             mean_wind: float = 10.0,
                             turbulence_intensity: float = 0.08):
        """Compute direction-aware wake factors using Bastankhah-Porté-Agel.

        Gaussian wake model (Bastankhah & Porté-Agel, Renew. Energy 70, 2014):
            ε/D    = 0.25 · √((1 + √(1 − Ct)) / (2·√(1 − Ct)))
            σ(x)/D = k* · (x/D) + ε/D
            C(x)   = 1 − √(1 − Ct / (8·(σ/D)²))
            ΔU/U   = C(x) · exp(−0.5·(r/σ)²)

        Wake expansion rate (Niayifar & Porté-Agel 2016):
            k* ≈ 0.38 · TI + 0.004  (≈0.04 at TI=0.1, typical offshore)

        Multiple wakes are superposed via sum-of-squares of deficits.
        """
        angle_rad = math.radians(wind_direction)
        wind_dx = -math.sin(angle_rad)  # wind blows FROM this direction
        wind_dy = -math.cos(angle_rad)
        # Cross-stream unit vector (perpendicular to wind, horizontal plane):
        # rotating wind vector +90° CCW → used as signed lateral axis.
        cross_dx = -wind_dy
        cross_dy = wind_dx

        n = self._count
        D = float(self._rotor_diameter)

        # Operating Ct heuristic: peaks near V≈8 m/s (Region 2), drops above rated
        V_rated = 11.0
        if mean_wind < 3.0:
            ct = 0.0
        elif mean_wind < V_rated:
            # Near-peak momentum extraction in Region 2
            ct = 0.82 - 0.015 * abs(mean_wind - 8.0)
        else:
            # Pitched rotor above rated: Ct drops with (V_rated/V)²
            ct = 0.82 * (V_rated / mean_wind) ** 2
        ct = max(0.05, min(0.90, ct))

        # Near-wake offset ε/D (Bastankhah eq. 7)
        one_minus_ct = max(0.01, 1.0 - ct)
        sqrt_one_minus_ct = math.sqrt(one_minus_ct)
        eps_over_D = 0.25 * math.sqrt(
            (1.0 + sqrt_one_minus_ct) / (2.0 * sqrt_one_minus_ct)
        )

        # TI-dependent wake expansion rate (Niayifar & Porté-Agel 2016)
        k_star = max(0.02, 0.38 * max(turbulence_intensity, 0.02) + 0.004)

        # Pre-compute Ct/8 for deficit discriminant
        ct_over_8 = ct / 8.0

        # Accumulate sum-of-squares deficits for each downstream turbine
        deficits_sq = np.zeros(n)

        if ct >= 0.05 and mean_wind > 2.0:
            for j in range(n):
                xj = self._positions[j].x
                yj = self._positions[j].y
                for i in range(n):
                    if i == j:
                        continue
                    dx = self._positions[i].x - xj
                    dy = self._positions[i].y - yj
                    # Downstream distance (along wind travel direction)
                    x_down = dx * wind_dx + dy * wind_dy
                    if x_down <= 0.5 * D:
                        continue  # upstream or abreast of j → no wake
                    # Signed cross-stream offset of target i from source j's
                    # wake centerline (projected onto the perpendicular-to-wind axis).
                    r_lat = dx * cross_dx + dy * cross_dy
                    # Apply wake meandering: source j's centerline drifts
                    # laterally by θ_m[j] · x_down at this downstream distance.
                    r_lat -= self._meander_angles[j] * x_down
                    r_sq = r_lat * r_lat

                    # Wake half-width at x_down
                    sigma_over_D = k_star * (x_down / D) + eps_over_D
                    sigma_sq_over_D_sq = sigma_over_D * sigma_over_D

                    # Max deficit (wake centerline). Need discriminant > 0.
                    discriminant = 1.0 - ct_over_8 / max(sigma_sq_over_D_sq, 1e-6)
                    if discriminant <= 0.0:
                        # Deep near-wake: cap at a physical upper bound
                        c_max = 0.70
                    else:
                        c_max = 1.0 - math.sqrt(discriminant)

                    # Gaussian radial profile
                    sigma_m_sq = sigma_sq_over_D_sq * D * D
                    radial = math.exp(-0.5 * r_sq / max(sigma_m_sq, 1.0))
                    deficit = c_max * radial

                    deficits_sq[i] += deficit * deficit

        # Sum-of-squares superposition: total deficit fraction
        total_deficit = np.sqrt(deficits_sq)
        self._wake_deficits = np.clip(total_deficit, 0.0, 0.70)
        self._wake_factors = 1.0 - self._wake_deficits

    @staticmethod
    def blade_shear_ratio(hub_height: float, rotor_radius: float,
                          blade_azimuth_rad: float, shear_exp: float) -> float:
        """Wind speed ratio V_blade/V_hub due to vertical wind shear.

        Power law: V(h) = V_hub × (h / h_hub)^α
        Blade tip height varies with azimuth: h = h_hub + R × cos(θ)
        where θ=0 is top-dead-center.
        """
        h_blade = hub_height + rotor_radius * math.cos(blade_azimuth_rad)
        h_blade = max(10.0, h_blade)
        return (h_blade / hub_height) ** shear_exp

    @staticmethod
    def blade_veer_offset_deg(rotor_radius: float,
                              blade_azimuth_rad: float,
                              veer_rate_deg_per_m: float) -> float:
        """Wind direction offset (degrees) at blade position due to wind veer.

        Ekman spiral: θ(h) = θ_hub + veer_rate × (h - h_hub).
        Blade height offset = R × cos(azimuth), where azimuth=0 is top-dead-center.
        Offshore typical veer_rate: 0.05–0.15 °/m.
        """
        h_offset = rotor_radius * math.cos(blade_azimuth_rad)
        return veer_rate_deg_per_m * h_offset


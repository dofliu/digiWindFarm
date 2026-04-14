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
    """

    def __init__(self, turbine_count: int, seed: int = 0,
                 positions: Optional[List[TurbinePosition]] = None,
                 spacing_m: float = 500.0):
        self._rng = np.random.RandomState(seed)
        self._count = turbine_count

        # Turbine positions
        self._positions = positions or default_farm_layout(turbine_count, spacing_m)

        # Persistent per-turbine characteristics
        self._offsets = self._rng.normal(0, 0.35, turbine_count)
        self._wake_factors = np.ones(turbine_count)

        # Per-turbine turbulence generators for spatial decorrelation
        self._turb_gens = [TurbulenceGenerator(seed=seed + 1000 + i) for i in range(turbine_count)]

        # Wind event propagation system
        self._propagation = WindEventPropagation(self._positions, seed=seed + 2000)

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

        # Update wake factors based on current wind direction
        self._update_wake_factors(wind_direction)

        # Generate natural wind events stochastically
        self._propagation.generate_natural_events(farm_wind, dt)

        # Advance event propagation
        self._current_speed_deltas, self._current_dir_deltas = self._propagation.step(dt)

        # Per-turbine turbulence (spatial decorrelation)
        for i in range(self._count):
            turb = self._turb_gens[i].step(farm_wind, turbulence_intensity * 0.4, dt)
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

    def _update_wake_factors(self, wind_direction: float):
        """Compute direction-aware wake factors.

        Turbines downwind of others lose 2-8% of wind speed.
        Wake strength depends on alignment with wind direction.
        """
        angle_rad = math.radians(wind_direction)
        wind_dx = -math.sin(angle_rad)  # wind blows FROM this direction
        wind_dy = -math.cos(angle_rad)

        n = self._count
        self._wake_factors = np.ones(n)

        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                # Vector from j to i
                dx = self._positions[i].x - self._positions[j].x
                dy = self._positions[i].y - self._positions[j].y
                dist = math.sqrt(dx * dx + dy * dy)
                if dist < 10.0:
                    continue

                # How aligned is j→i with wind direction?
                # cos_angle = 1.0 means i is directly downwind of j
                cos_angle = (dx * wind_dx + dy * wind_dy) / dist
                if cos_angle < 0.3:
                    continue  # Not in wake zone

                # Wake deficit: stronger when directly aligned, weaker at distance
                # Jensen/Park-like simple model
                alignment = max(0.0, (cos_angle - 0.3) / 0.7)
                wake_deficit = 0.08 * alignment * (200.0 / max(dist, 200.0)) ** 0.5
                self._wake_factors[i] *= (1.0 - wake_deficit)

        # Clamp to reasonable range
        self._wake_factors = np.clip(self._wake_factors, 0.85, 1.0)


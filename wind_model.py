# wind_model.py
"""
Multi-scale wind environment model for realistic long-term simulation.

Layers (from slowest to fastest):
  1. Seasonal — Weibull shape/scale vary by month
  2. Weather system — multi-day synoptic patterns (high/low pressure)
  3. Diurnal — daily thermal cycle (afternoon peak)
  4. Mesoscale — hour-scale ramps and lulls
  5. Turbulence — second-scale fluctuations (handled by TurbulenceGenerator)

Supports:
  - Auto mode: realistic multi-month patterns with no repetition
  - Manual override with configurable transition ramp
  - Predefined profiles (calm, moderate, rated, storm, etc.)
  - Accelerated time (time_scale > 1 for bulk data generation)
"""

import math
import numpy as np
from datetime import datetime, timedelta
from typing import Optional


# ─── Seasonal wind parameters (typical coastal/onshore site) ─────────
# month: (weibull_scale_m_s, weibull_shape_k)
# Higher scale = windier month, shape ~2 = Rayleigh distribution
SEASONAL_PARAMS = {
    1:  (10.5, 2.1),   # January — windy
    2:  (10.2, 2.0),   # February
    3:  (9.8,  2.0),   # March — spring transition
    4:  (8.5,  2.1),   # April
    5:  (7.5,  2.2),   # May — calmer
    6:  (7.0,  2.3),   # June — summer calm
    7:  (6.8,  2.3),   # July — lightest winds
    8:  (7.2,  2.2),   # August
    9:  (8.0,  2.1),   # September — autumn ramp
    10: (9.5,  2.0),   # October
    11: (10.0, 1.9),   # November — stormy
    12: (10.8, 1.9),   # December — peak winter
}


class WeatherSystem:
    """Simulates multi-day synoptic weather patterns."""

    def __init__(self, seed: int = 0):
        self._rng = np.random.RandomState(seed)
        # Current weather state
        self._pressure_state = 0.0     # normalized: -1 (low/stormy) to +1 (high/calm)
        self._front_timer = 0.0        # time until next front passage
        self._front_duration = 0.0     # how long the current front lasts
        self._in_front = False
        self._next_front()

    def _next_front(self):
        """Schedule next weather front passage."""
        # Fronts every 2-7 days
        self._front_timer = self._rng.uniform(2 * 86400, 7 * 86400)
        self._front_duration = self._rng.uniform(6 * 3600, 24 * 3600)
        self._in_front = False

    def step(self, dt: float) -> float:
        """Return wind speed multiplier (0.5 to 1.8) based on weather system."""
        self._front_timer -= dt

        if self._front_timer <= 0 and not self._in_front:
            self._in_front = True
            self._front_timer = self._front_duration

        if self._in_front:
            self._front_timer -= dt
            if self._front_timer <= 0:
                self._next_front()
                self._in_front = False

        # Pressure evolves slowly with mean reversion
        target = -0.5 if self._in_front else 0.3
        tau = 7200.0  # 2-hour time constant
        alpha = 1.0 - math.exp(-dt / tau)
        self._pressure_state += (target - self._pressure_state) * alpha
        self._pressure_state += self._rng.normal(0, 0.003 * math.sqrt(dt))
        self._pressure_state = max(-1.0, min(1.0, self._pressure_state))

        # Map pressure to wind multiplier
        # Low pressure (negative) → stronger wind
        # High pressure (positive) → calmer
        return 1.0 - self._pressure_state * 0.4


class WindEnvironmentModel:
    """Multi-scale wind environment model for realistic long-term simulation."""

    def __init__(self, seed: int = 0):
        self._rng = np.random.RandomState(seed)
        self.turbulence_intensity = 0.10
        self.base_ambient_temp = 25.0

        # Sub-models
        self._weather = WeatherSystem(seed=seed + 1)
        self._mesoscale_state = 0.0  # hour-scale ramp state

        # Simulation time tracking (for accelerated mode)
        self._sim_time_offset: Optional[timedelta] = None
        self.time_scale = 1.0  # 1.0 = real-time, 60.0 = 1min per second

        # Manual override
        self._override_wind_speed: Optional[float] = None
        self._override_wind_direction: Optional[float] = None
        self._override_ambient_temp: Optional[float] = None
        self._active_profile: Optional[str] = None
        self._profile_start_time: Optional[datetime] = None

        # Transition ramp for smooth profile switching
        self._transition_from: Optional[float] = None
        self._transition_to: Optional[float] = None
        self._transition_start: Optional[float] = None
        self._transition_duration: float = 30.0  # 30 seconds default ramp
        self._elapsed_real = 0.0  # real elapsed seconds

        # Weather system state (for deterministic long-term)
        self._last_weather_update = 0.0

    # ─── Override control ──────────────────────────────────────────────

    def set_override(self, wind_speed: Optional[float] = None,
                     wind_direction: Optional[float] = None,
                     ambient_temp: Optional[float] = None,
                     turbulence: Optional[float] = None):
        """Set manual wind conditions with smooth transition."""
        if wind_speed is not None and self._override_wind_speed != wind_speed:
            # Start transition ramp from current conditions
            self._transition_from = self._override_wind_speed or self._get_auto_wind(datetime.now())
            self._transition_to = wind_speed
            self._transition_start = self._elapsed_real

        self._override_wind_speed = wind_speed
        self._override_wind_direction = wind_direction
        self._override_ambient_temp = ambient_temp
        if turbulence is not None:
            self.turbulence_intensity = turbulence
        self._active_profile = "manual" if any(
            v is not None for v in [wind_speed, wind_direction, ambient_temp]
        ) else None

    def clear_override(self):
        """Return to automatic mode with smooth transition."""
        if self._override_wind_speed is not None:
            self._transition_from = self._override_wind_speed
            self._transition_to = None  # will use auto
            self._transition_start = self._elapsed_real
        self._override_wind_speed = None
        self._override_wind_direction = None
        self._override_ambient_temp = None
        self._active_profile = None

    def set_profile(self, profile: str):
        """Activate a predefined wind scenario with smooth transition.

        Profiles:
          'calm'        — 2 m/s, low turbulence
          'moderate'    — 8 m/s, normal turbulence
          'rated'       — 13 m/s, at rated power
          'strong'      — 18 m/s, pitch regulation
          'storm'       — 26 m/s, above cut-out
          'gusty'       — 10 m/s, high turbulence (0.30)
          'ramp_up'     — gradual increase 3→18 m/s over 10 minutes
          'ramp_down'   — gradual decrease 18→3 m/s over 10 minutes
          'auto'        — return to natural pattern
        """
        profiles = {
            'calm':     (2.0,  270, 20.0, 0.05),
            'moderate': (8.0,  270, 25.0, 0.10),
            'rated':    (13.0, 270, 25.0, 0.10),
            'strong':   (18.0, 285, 22.0, 0.12),
            'storm':    (26.0, 300, 18.0, 0.20),
            'gusty':    (10.0, 260, 25.0, 0.30),
        }

        if profile == 'auto':
            self.clear_override()
            return

        if profile in ('ramp_up', 'ramp_down'):
            self._active_profile = profile
            self._profile_start_time = datetime.now()
            self._override_wind_direction = 270.0
            self._override_ambient_temp = 25.0
            self.turbulence_intensity = 0.12
            # Start transition
            current = self._override_wind_speed or self._get_auto_wind(datetime.now())
            self._transition_from = current
            self._transition_to = 18.0 if profile == 'ramp_up' else 3.0
            self._transition_start = self._elapsed_real
            self._transition_duration = 120.0  # 2 minute ramp
            return

        if profile in profiles:
            ws, wd, temp, turb = profiles[profile]
            self.set_override(ws, wd, temp, turb)
            self._active_profile = profile

    def get_status(self) -> dict:
        return {
            "mode": "manual" if self._active_profile else "auto",
            "profile": self._active_profile,
            "override_wind_speed": self._override_wind_speed,
            "override_wind_direction": self._override_wind_direction,
            "override_ambient_temp": self._override_ambient_temp,
            "turbulence_intensity": self.turbulence_intensity,
            "time_scale": self.time_scale,
            "weather_pressure": self._weather._pressure_state,
            "weather_in_front": self._weather._in_front,
        }

    # ─── Core getters ──────────────────────────────────────────────────

    def get_wind_speed(self, timestamp: datetime) -> float:
        """Get wind speed at given timestamp (includes all layers)."""
        self._elapsed_real += 1.0  # approximate

        # Check for active transition ramp
        if self._transition_start is not None:
            elapsed = self._elapsed_real - self._transition_start
            progress = min(1.0, elapsed / self._transition_duration)
            # Smooth S-curve transition
            smooth = 0.5 - 0.5 * math.cos(progress * math.pi)

            if progress >= 1.0:
                self._transition_start = None  # transition complete

            from_val = self._transition_from or 0.0
            to_val = self._transition_to if self._transition_to is not None else self._get_auto_wind(timestamp)
            base = from_val + (to_val - from_val) * smooth
        elif self._active_profile in ('ramp_up', 'ramp_down') and self._profile_start_time:
            elapsed = (timestamp - self._profile_start_time).total_seconds()
            if self._active_profile == 'ramp_up':
                base = 3.0 + min(15.0, elapsed / 120.0 * 15.0)
            else:
                base = max(3.0, 18.0 - elapsed / 120.0 * 15.0)
        elif self._override_wind_speed is not None:
            base = self._override_wind_speed
        else:
            base = self._get_auto_wind(timestamp)

        return max(0, base)

    def _get_auto_wind(self, timestamp: datetime) -> float:
        """Multi-layer automatic wind speed model."""
        month = timestamp.month
        hour = timestamp.hour + timestamp.minute / 60.0

        # Layer 1: Seasonal baseline (Weibull mean)
        scale, shape = SEASONAL_PARAMS.get(month, (8.5, 2.1))
        seasonal_mean = scale * math.gamma(1.0 + 1.0 / shape)

        # Layer 2: Weather system (multi-day patterns)
        # Advance weather model (approximately, using 1s steps)
        weather_mult = self._weather.step(1.0)

        # Layer 3: Diurnal cycle (thermal effects)
        # Afternoon peak (14:00-16:00), overnight lull
        diurnal = 1.0 + 0.15 * math.sin((hour - 5) * math.pi / 12)

        # Layer 4: Mesoscale ramps (1-4 hour scale)
        self._mesoscale_state += self._rng.normal(0, 0.002)
        self._mesoscale_state *= 0.9995  # slow decay
        self._mesoscale_state = max(-0.3, min(0.3, self._mesoscale_state))
        mesoscale = 1.0 + self._mesoscale_state

        base = seasonal_mean * weather_mult * diurnal * mesoscale
        return max(0.5, base)

    def get_wind_direction(self, timestamp: datetime) -> float:
        if self._override_wind_direction is not None:
            return (self._override_wind_direction + self._rng.normal(0, 3)) % 360

        # Auto: slow drift with weather-driven backing/veering
        hour = timestamp.hour + timestamp.minute / 60
        base_direction = 270
        seasonal_shift = 20 * math.sin((timestamp.month - 1) * math.pi / 6)  # winter NW, summer SW
        diurnal_shift = 15 * math.sin((hour - 6) * math.pi / 12)  # sea breeze effect
        weather_shift = self._weather._pressure_state * 30  # fronts shift direction
        return (base_direction + seasonal_shift + diurnal_shift + weather_shift +
                self._rng.normal(0, 2.0)) % 360

    def get_ambient_temp(self, timestamp: datetime) -> float:
        if self._override_ambient_temp is not None:
            return self._override_ambient_temp + self._rng.normal(0, 0.3)

        month = timestamp.month
        hour = timestamp.hour + timestamp.minute / 60.0

        # Seasonal base temperature
        seasonal_temps = {
            1: 12, 2: 13, 3: 16, 4: 20, 5: 24, 6: 27,
            7: 29, 8: 28, 9: 26, 10: 22, 11: 17, 12: 13,
        }
        base = seasonal_temps.get(month, 22)

        # Diurnal: peak at 14:00, minimum at 05:00
        diurnal = 5.0 * math.sin((hour - 5) * math.pi / 12)

        # Weather: fronts bring temperature changes
        weather = -3.0 * self._weather._pressure_state

        return base + diurnal + weather + self._rng.normal(0, 0.3)

    # ─── Atmospheric stability (Monin-Obukhov diurnal coupling) ────────
    #
    # Realistic offshore/onshore boundary layers go through a strong diurnal
    # stability cycle that drives both the vertical wind-shear exponent α and
    # the turbulence intensity. We summarise it with a single continuous score
    # s ∈ [−1, +1]:
    #     −1 ⇒ strongly stable (nocturnal radiative cooling dominates)
    #      0 ⇒ neutral
    #     +1 ⇒ strongly unstable (daytime convective mixing)
    #
    # s = solar(t) · wind_damping(V) · cloud_damping(pressure)
    #
    #     solar(t)      = sin(π · (hour − 6)/12)       # +1 noon, 0 dawn/dusk, −1 midnight
    #     wind_damping  = 1 / (1 + (V/8)²)              # high wind → mechanical mixing
    #     cloud_damping = 1 − 0.5 · max(0, −pressure)   # low-pressure / fronts → clouds
    #
    # Manual override (profile / set_override) forces neutral to avoid
    # surprising users who fix wind conditions during demos.

    def get_atmospheric_stability(self, timestamp: datetime) -> float:
        """Continuous atmospheric stability score in [-1, +1].

        Negative = stable (night, clear sky, low wind → high α, low TI).
        Positive = unstable (convective afternoon → low α, high TI).
        Returns 0.0 (neutral) when any manual wind override is active.

        Uses the weather model's current state (no side effects) so this can be
        called multiple times per step without advancing RNG state.
        """
        if self._override_wind_speed is not None or self._active_profile is not None:
            return 0.0

        hour = timestamp.hour + timestamp.minute / 60.0
        solar = math.sin((hour - 6.0) * math.pi / 12.0)

        # Wind damping: use seasonal baseline × current weather multiplier
        # (mirrors _get_auto_wind but without advancing weather.step).
        month = timestamp.month
        scale, shape = SEASONAL_PARAMS.get(month, (8.5, 2.1))
        seasonal_mean = scale * math.gamma(1.0 + 1.0 / shape)
        # pressure_state already reflects current synoptic state
        weather_mult = 1.0 - self._weather._pressure_state * 0.4
        v = max(0.5, seasonal_mean * weather_mult)
        wind_damping = 1.0 / (1.0 + (v / 8.0) ** 2)

        # Cloud damping: low pressure / fronts suppress both extremes
        cloud_damping = 1.0 - 0.5 * max(0.0, -self._weather._pressure_state)

        s = solar * wind_damping * cloud_damping
        return max(-1.0, min(1.0, s))

    def get_shear_exponent(self, timestamp: datetime,
                           stability: Optional[float] = None) -> float:
        """Farm-level wind shear exponent α (power-law V(h)=V_hub·(h/h_hub)^α).

        α = clamp(0.14 − 0.10·s, 0.04, 0.30). Neutral value 0.14 follows
        common offshore measurements (e.g. FINO1, Lillgrund).

        Pass `stability` to avoid re-computing and re-mutating internal state.
        """
        s = stability if stability is not None else self.get_atmospheric_stability(timestamp)
        return max(0.04, min(0.30, 0.14 - 0.10 * s))

    def get_turbulence_multiplier(self, timestamp: datetime,
                                  stability: Optional[float] = None) -> float:
        """Multiplier applied on top of `turbulence_intensity` base (0.5 – 1.6).

        At very stable night ≈ 0.5× base TI; at convective afternoon ≈ 1.5× base TI.

        Pass `stability` to avoid re-computing and re-mutating internal state.
        """
        s = stability if stability is not None else self.get_atmospheric_stability(timestamp)
        return max(0.5, min(1.6, 1.0 + 0.5 * s))

    def get_ambient_humidity(self, timestamp: datetime) -> float:
        """Relative humidity (%) with seasonal/diurnal/weather modulation.

        Offshore wind sites sit in the marine boundary layer where RH is high
        year-round and peaks during rainy season and overnight.
        """
        if self._override_ambient_temp is not None:
            # During manual override we keep humidity stable to avoid surprising
            # coolant behavior during demos; still add a little sensor noise.
            return 65.0 + self._rng.normal(0, 1.0)

        month = timestamp.month
        hour = timestamp.hour + timestamp.minute / 60.0

        # Seasonal baseline — higher during East-Asian rainy / typhoon season
        seasonal_rh = {
            1: 72, 2: 74, 3: 76, 4: 78, 5: 82, 6: 85,
            7: 82, 8: 83, 9: 80, 10: 74, 11: 70, 12: 70,
        }
        base = seasonal_rh.get(month, 75)

        # Diurnal: overnight/near-dawn peak, mid-afternoon trough (≈±8%)
        diurnal = -8.0 * math.sin((hour - 5) * math.pi / 12)

        # Low-pressure fronts pull humidity up by ~10%
        weather = -10.0 * self._weather._pressure_state

        rh = base + diurnal + weather + self._rng.normal(0, 0.8)
        return max(15.0, min(100.0, rh))

    def get_ambient_pressure(self, timestamp: datetime) -> float:
        """Ambient atmospheric pressure P (Pa) from synoptic weather state (#106).

        Maps the continuous weather pressure state [-1, +1] to physical Pa
        with mid-latitude amplitude ±1500 Pa (≈ ±15 hPa). Matches typical
        temperate-zone frontal swings (1 σ ≈ 8 hPa, 2 σ ≈ 15 hPa).

        Manual overrides lock P at the ISA sea-level reference (101325 Pa) so
        demos are not disturbed by synthetic weather drift.
        """
        if self._override_wind_speed is not None or self._active_profile is not None:
            return 101325.0
        p = 101325.0 + self._weather._pressure_state * 1500.0
        return max(90000.0, min(105000.0, p))

    def get_air_density(self, timestamp: datetime,
                        ambient_temp: Optional[float] = None,
                        humidity: Optional[float] = None,
                        pressure_pa: Optional[float] = None) -> float:
        """Moist air density ρ (kg/m³) from ideal gas law + Magnus correction.

        ρ_dry   = P / (R_d · T_K)                R_d = 287.058 J/(kg·K)
        e_s(T)  = 611.2 · exp(17.67·T_C/(T_C+243.5))   (Pa, Buck/Magnus)
        ρ_moist = ρ_dry · (1 − 0.378·e/P)        e = (RH/100)·e_s

        Typical range: ~1.15 (32 °C / 95% RH) to ~1.34 (−10 °C / 50% RH).
        Pass `ambient_temp` / `humidity` / `pressure_pa` to avoid recomputing
        those upstream; when omitted they default to the current weather state
        (includes synoptic P swings, #106).
        """
        t_c = ambient_temp if ambient_temp is not None else self.get_ambient_temp(timestamp)
        rh = humidity if humidity is not None else self.get_ambient_humidity(timestamp)
        p_atm = pressure_pa if pressure_pa is not None else self.get_ambient_pressure(timestamp)
        t_k = t_c + 273.15
        e_s = 611.2 * math.exp(17.67 * t_c / (t_c + 243.5))
        e = max(0.0, min(1.0, rh / 100.0)) * e_s
        rho_dry = p_atm / (287.058 * t_k)
        rho = rho_dry * (1.0 - 0.378 * e / p_atm)
        return max(0.95, min(1.35, rho))

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
from typing import Optional, Dict


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

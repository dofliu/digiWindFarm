# wind_turbine_simulator/wind_model.py
import numpy as np
from datetime import datetime
from typing import Optional


class WindEnvironmentModel:
    """風場環境模型 — 支援自動日變化或手動覆寫模式"""

    def __init__(self):
        self.base_pattern = self._create_daily_pattern()
        self.turbulence_intensity = 0.1
        self.base_ambient_temp = 25.0

        # ── Manual override (None = auto mode) ──
        self._override_wind_speed: Optional[float] = None
        self._override_wind_direction: Optional[float] = None
        self._override_ambient_temp: Optional[float] = None

        # ── Wind event profiles ──
        self._active_profile: Optional[str] = None
        self._profile_start_time: Optional[datetime] = None

    # ─── Override control ──────────────────────────────────────────────

    def set_override(self, wind_speed: Optional[float] = None,
                     wind_direction: Optional[float] = None,
                     ambient_temp: Optional[float] = None,
                     turbulence: Optional[float] = None):
        """Set manual wind conditions. Pass None to keep auto mode for that parameter."""
        self._override_wind_speed = wind_speed
        self._override_wind_direction = wind_direction
        self._override_ambient_temp = ambient_temp
        if turbulence is not None:
            self.turbulence_intensity = turbulence
        self._active_profile = "manual" if any(
            v is not None for v in [wind_speed, wind_direction, ambient_temp]
        ) else None

    def clear_override(self):
        """Return to automatic daily pattern mode."""
        self._override_wind_speed = None
        self._override_wind_direction = None
        self._override_ambient_temp = None
        self._active_profile = None

    def set_profile(self, profile: str):
        """
        Activate a predefined wind scenario profile.

        Profiles:
          'calm'        — 2 m/s, low turbulence (below cut-in, turbines idle)
          'moderate'    — 8 m/s, normal turbulence (partial load)
          'rated'       — 12 m/s, turbines at rated power
          'strong'      — 18 m/s, pitch regulation active
          'storm'       — 26 m/s, above cut-out, emergency shutdown
          'gusty'       — 10 m/s base with high turbulence (0.3)
          'ramp_up'     — gradual increase 3→15 m/s over time
          'ramp_down'   — gradual decrease 15→3 m/s over time
          'auto'        — return to daily pattern
        """
        profiles = {
            'calm':     (2.0, 270, 20.0, 0.05),
            'moderate': (8.0, 270, 25.0, 0.10),
            'rated':    (12.0, 270, 25.0, 0.10),
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
            return

        if profile in profiles:
            ws, wd, temp, turb = profiles[profile]
            self.set_override(ws, wd, temp, turb)
            self._active_profile = profile

    def get_status(self) -> dict:
        """Return current wind model status for API."""
        return {
            "mode": "manual" if self._active_profile else "auto",
            "profile": self._active_profile,
            "override_wind_speed": self._override_wind_speed,
            "override_wind_direction": self._override_wind_direction,
            "override_ambient_temp": self._override_ambient_temp,
            "turbulence_intensity": self.turbulence_intensity,
        }

    # ─── Core getters ──────────────────────────────────────────────────

    def get_wind_speed(self, timestamp: datetime) -> float:
        """獲取指定時間的風速（含覆寫邏輯）"""
        # Ramp profiles
        if self._active_profile == 'ramp_up' and self._profile_start_time:
            elapsed = (timestamp - self._profile_start_time).total_seconds()
            base = 3.0 + min(12.0, elapsed / 60.0 * 2.0)  # +2 m/s per minute
        elif self._active_profile == 'ramp_down' and self._profile_start_time:
            elapsed = (timestamp - self._profile_start_time).total_seconds()
            base = max(3.0, 15.0 - elapsed / 60.0 * 2.0)
        elif self._override_wind_speed is not None:
            base = self._override_wind_speed
        else:
            # Auto: daily pattern
            hour_of_day = timestamp.hour + timestamp.minute / 60
            index = int(hour_of_day * 10)
            base = self.base_pattern[index % len(self.base_pattern)]

        # Add turbulence
        turbulence = np.random.normal(0, max(0.1, base * self.turbulence_intensity))
        return max(0, base + turbulence)

    def get_wind_direction(self, timestamp: datetime) -> float:
        """獲取風向"""
        if self._override_wind_direction is not None:
            # Small random variation around override value
            return (self._override_wind_direction + np.random.normal(0, 3)) % 360

        # Auto: slow drift
        base_direction = 270
        variation = 30 * np.sin(timestamp.hour * np.pi / 12)
        return (base_direction + variation) % 360

    def get_ambient_temp(self, timestamp: datetime) -> float:
        """獲取環境溫度"""
        if self._override_ambient_temp is not None:
            return self._override_ambient_temp + np.random.normal(0, 0.3)

        # Auto: daily cycle
        import math
        hour = timestamp.hour + timestamp.minute / 60.0
        return self.base_ambient_temp + 5 * math.sin((hour - 5) * math.pi / 12)

    def _create_daily_pattern(self):
        """創建日常風速模式"""
        hours = np.arange(0, 24, 0.1)
        pattern = np.zeros_like(hours)
        for i, hour in enumerate(hours):
            if 0 <= hour < 6:
                pattern[i] = 4 + np.sin(hour * np.pi / 6)
            elif 6 <= hour < 12:
                pattern[i] = 3 + 4 * (hour - 6) / 6
            elif 12 <= hour < 18:
                pattern[i] = 7 + 3 * np.sin((hour - 12) * np.pi / 6)
            else:
                pattern[i] = 4 + 2 * np.cos((hour - 18) * np.pi / 6)
        return pattern

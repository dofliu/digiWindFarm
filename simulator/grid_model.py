from datetime import datetime
from typing import Optional

import numpy as np


class GridEnvironmentModel:
    """Simple grid-side environment model for frequency and voltage events."""

    def __init__(self):
        self.base_frequency_hz = 50.0
        self.base_voltage_v = 690.0
        self._override_frequency: Optional[float] = None
        self._override_voltage: Optional[float] = None
        self._active_profile: Optional[str] = None
        self._profile_start_time: Optional[datetime] = None

    def set_override(self, frequency_hz: Optional[float] = None, voltage_v: Optional[float] = None):
        self._override_frequency = frequency_hz
        self._override_voltage = voltage_v
        self._active_profile = "manual" if frequency_hz is not None or voltage_v is not None else None
        if self._active_profile:
            self._profile_start_time = datetime.now()

    def clear_override(self):
        self._override_frequency = None
        self._override_voltage = None
        self._active_profile = None
        self._profile_start_time = None

    def set_profile(self, profile: str):
        profiles = {
            "nominal": (50.0, 690.0),
            "low_freq": (49.2, 690.0),
            "high_freq": (50.8, 690.0),
            "undervoltage": (50.0, 630.0),
            "overvoltage": (50.0, 740.0),
            "weak_grid": (49.6, 655.0),
        }
        if profile == "auto":
            self.clear_override()
            return
        if profile == "recovery":
            self._active_profile = profile
            self._profile_start_time = datetime.now()
            self._override_frequency = None
            self._override_voltage = None
            return
        if profile in profiles:
            freq, volt = profiles[profile]
            self._active_profile = profile
            self._profile_start_time = datetime.now()
            self._override_frequency = freq
            self._override_voltage = volt

    def get_status(self) -> dict:
        return {
            "mode": "manual" if self._active_profile else "auto",
            "profile": self._active_profile,
            "override_frequency_hz": self._override_frequency,
            "override_voltage_v": self._override_voltage,
        }

    def get_frequency(self, timestamp: datetime) -> float:
        if self._active_profile == "recovery" and self._profile_start_time:
            elapsed = (timestamp - self._profile_start_time).total_seconds()
            base = 49.0 + min(1.0, elapsed / 120.0)
            return base + np.random.normal(0, 0.03)
        if self._override_frequency is not None:
            return self._override_frequency + np.random.normal(0, 0.02)
        return self.base_frequency_hz + 0.05 * np.sin(timestamp.timestamp() / 180.0) + np.random.normal(0, 0.01)

    def get_voltage(self, timestamp: datetime) -> float:
        if self._active_profile == "recovery" and self._profile_start_time:
            elapsed = (timestamp - self._profile_start_time).total_seconds()
            base = 620.0 + min(70.0, elapsed / 120.0 * 70.0)
            return base + np.random.normal(0, 2.0)
        if self._override_voltage is not None:
            return self._override_voltage + np.random.normal(0, 1.5)
        return self.base_voltage_v + 5.0 * np.sin(timestamp.timestamp() / 240.0 + 0.5) + np.random.normal(0, 0.8)

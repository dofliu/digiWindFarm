from datetime import datetime
from typing import Optional

import numpy as np


class GridEnvironmentModel:
    """Simple grid-side environment model for frequency and voltage events."""

    def __init__(self, frequency_hz: float = 60.0, voltage_v: float = 3500.0):
        self.base_frequency_hz = frequency_hz
        self.base_voltage_v = voltage_v
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
        nom_f = self.base_frequency_hz
        nom_v = self.base_voltage_v
        profiles = {
            "nominal":      (nom_f, nom_v),
            "low_freq":     (nom_f - 0.8, nom_v),
            "high_freq":    (nom_f + 0.8, nom_v),
            "undervoltage": (nom_f, nom_v * 0.91),
            "overvoltage":  (nom_f, nom_v * 1.07),
            "weak_grid":    (nom_f - 0.4, nom_v * 0.95),
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
            base = (self.base_frequency_hz - 1.0) + min(1.0, elapsed / 120.0)
            return base + np.random.normal(0, 0.03)
        if self._override_frequency is not None:
            return self._override_frequency + np.random.normal(0, 0.02)
        return self.base_frequency_hz + 0.05 * np.sin(timestamp.timestamp() / 180.0) + np.random.normal(0, 0.01)

    def get_voltage(self, timestamp: datetime) -> float:
        nom = self.base_voltage_v
        if self._active_profile == "recovery" and self._profile_start_time:
            elapsed = (timestamp - self._profile_start_time).total_seconds()
            base = nom * 0.90 + min(nom * 0.10, elapsed / 120.0 * nom * 0.10)
            return base + np.random.normal(0, nom * 0.001)
        if self._override_voltage is not None:
            return self._override_voltage + np.random.normal(0, nom * 0.001)
        return nom + nom * 0.007 * np.sin(timestamp.timestamp() / 240.0 + 0.5) + np.random.normal(0, nom * 0.001)

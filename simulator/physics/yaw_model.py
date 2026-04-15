"""
Yaw system model with realistic control logic.
"""

import math
from typing import Dict

import numpy as np


class YawModel:
    """Physics-based yaw system with dead band, delay, rate shaping, and cable management."""

    def __init__(self):
        self.yaw_angle = 270.0
        self.cable_windup = 0.0

        # Z72 OEM values
        self.dead_band = 15.0             # Z72: auto yaw start outside [-15°, +15°]
        self.yaw_rate = 0.5               # Z72: nominal yaw speed 0.5 deg/s
        self.activation_delay = 60.0      # seconds before yaw activates
        self.post_hold_time = 30.0        # seconds to hold after alignment within [-2°, +2°]
        self.unwind_threshold = 2.0       # Z72: cable twist > 2 turns → unwind

        self._error_timer = 0.0
        self._hold_timer = 0.0
        self._is_yawing = False
        self._is_unwinding = False
        self._brake_pressure = 210.0      # Z72: high friction = 210 bar
        self._yaw_command_filter = 0.0

    def step(self, wind_direction: float, is_producing: bool, dt: float) -> Dict[str, float]:
        """Advance yaw model by one timestep, returning yaw angle, error, and motor status."""
        error = self._angle_diff(wind_direction, self.yaw_angle)

        if not is_producing:
            self._is_yawing = False
            self._error_timer = 0.0
            self._yaw_command_filter = 0.0
            self._brake_pressure = min(210.0, self._brake_pressure + 3.0 * dt)  # Z72: 210 bar = brakes dropped
            return self._output(error)

        if abs(self.cable_windup) > self.unwind_threshold:
            self._is_unwinding = True
        if self._is_unwinding:
            unwind_dir = -1.0 if self.cable_windup > 0 else 1.0
            self.yaw_angle = (self.yaw_angle + unwind_dir * self.yaw_rate * dt) % 360
            self.cable_windup += unwind_dir * self.yaw_rate * dt / 360
            self._brake_pressure = max(20.0, self._brake_pressure - 8.0 * dt)  # Z72: 20 bar = low friction
            if abs(self.cable_windup) < 0.3:
                self._is_unwinding = False
            return self._output(error, yawing=True)

        if abs(error) > self.dead_band:
            self._error_timer += dt
            if self._error_timer >= self.activation_delay:
                self._is_yawing = True
                self._hold_timer = 0.0
        else:
            self._error_timer = max(0.0, self._error_timer - dt * 2.0)
            if self._is_yawing:
                self._hold_timer += dt
                if self._hold_timer > self.post_hold_time:
                    self._is_yawing = False

        if self._is_yawing and abs(error) > 2.0:
            rate_gain = min(1.8, max(0.55, abs(error) / self.dead_band))
            target_rate = math.copysign(self.yaw_rate * rate_gain, error)
            self._yaw_command_filter += (target_rate - self._yaw_command_filter) * min(1.0, dt / 3.0)
            step_angle = self._yaw_command_filter * dt
            self.yaw_angle = (self.yaw_angle + step_angle) % 360
            self.cable_windup += step_angle / 360
            self.cable_windup = max(-4.0, min(4.0, self.cable_windup))
            self._brake_pressure = max(20.0, self._brake_pressure - 8.0 * dt)  # Z72: lifted for yaw
        else:
            self._yaw_command_filter *= max(0.0, 1.0 - dt / 2.0)
            self._brake_pressure = min(210.0, self._brake_pressure + 3.0 * dt)  # Z72: 210 bar = dropped

        return self._output(error, self._is_yawing)

    def _output(self, error: float, yawing: bool = False) -> Dict[str, float]:
        return {
            "yaw_angle": self.yaw_angle,
            "yaw_error": error,
            "brake_pressure": self._brake_pressure + np.random.normal(0, 0.5),
            "cable_windup": self.cable_windup,
            "is_yawing": 1.0 if yawing else 0.0,
        }

    @staticmethod
    def _angle_diff(target: float, current: float) -> float:
        diff = (target - current) % 360
        if diff > 180:
            diff -= 360
        return diff

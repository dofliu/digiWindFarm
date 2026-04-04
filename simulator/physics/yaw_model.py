"""
Yaw system model with realistic control logic.

Features:
  - Dead band: no yaw action within ±8° error (prevents constant hunting)
  - Activation delay: 60-second sustained error before yaw starts
  - Yaw rate: 0.3-0.5 °/s (typical for large turbines)
  - Post-action hold: 30-second pause after reaching alignment
  - Cable unwind: tracks windup, triggers unwind at ±2.5 turns
  - Hydraulic pressure: varies with yaw activity

Reference values:
  Yaw error normal: ±5°
  Yaw brake pressure: 140-180 bar (stationary), drops to 80-120 during yaw
  Cable windup limit: ±3 turns before auto-unwind

Can be replaced independently.
"""

import math
from typing import Dict


class YawModel:
    """Physics-based yaw system with dead band, delay, and cable management."""

    def __init__(self):
        self.yaw_angle = 270.0          # Current nacelle heading (°)
        self.cable_windup = 0.0         # turns (positive = CW from top view)

        # ── Control parameters ──
        self.dead_band = 8.0            # ° (no action within this range)
        self.yaw_rate = 0.4             # °/s
        self.activation_delay = 60.0    # seconds of sustained error before yaw starts
        self.post_hold_time = 30.0      # seconds to hold after reaching alignment
        self.unwind_threshold = 2.5     # turns before auto-unwind

        # ── Internal state ──
        self._error_timer = 0.0         # seconds of sustained error > dead_band
        self._hold_timer = 0.0          # seconds since last yaw action stopped
        self._is_yawing = False
        self._is_unwinding = False
        self._brake_pressure = 160.0    # bar

    def step(self, wind_direction: float, is_producing: bool,
             dt: float) -> Dict[str, float]:
        """
        Advance yaw system by one timestep.

        Returns:
            Dict with yaw_angle, yaw_error, brake_pressure, cable_windup, is_yawing
        """
        error = self._angle_diff(wind_direction, self.yaw_angle)

        if not is_producing:
            # Not producing → hold position, build brake pressure
            self._is_yawing = False
            self._error_timer = 0.0
            self._brake_pressure = min(180.0, self._brake_pressure + 3.0 * dt)
            return self._output(error)

        # ── Cable unwind check (highest priority) ──
        if abs(self.cable_windup) > self.unwind_threshold:
            self._is_unwinding = True
        if self._is_unwinding:
            # Unwind direction: opposite of windup
            unwind_dir = -1.0 if self.cable_windup > 0 else 1.0
            self.yaw_angle = (self.yaw_angle + unwind_dir * self.yaw_rate * dt) % 360
            self.cable_windup += unwind_dir * self.yaw_rate * dt / 360
            self._brake_pressure = max(80.0, self._brake_pressure - 5.0 * dt)
            if abs(self.cable_windup) < 0.3:
                self._is_unwinding = False
            return self._output(error, yawing=True)

        # ── Normal yaw control with dead band and delay ──
        if abs(error) > self.dead_band:
            self._error_timer += dt
            if self._error_timer >= self.activation_delay:
                self._is_yawing = True
                self._hold_timer = 0.0
        else:
            self._error_timer = max(0, self._error_timer - dt * 2)  # decay faster
            if self._is_yawing:
                # Reached alignment → start hold timer
                self._hold_timer += dt
                if self._hold_timer > self.post_hold_time:
                    self._is_yawing = False

        if self._is_yawing and abs(error) > 2.0:
            # Yaw towards wind direction
            step_angle = math.copysign(self.yaw_rate, error) * dt
            self.yaw_angle = (self.yaw_angle + step_angle) % 360
            self.cable_windup += step_angle / 360
            self.cable_windup = max(-4.0, min(4.0, self.cable_windup))
            self._brake_pressure = max(80.0, self._brake_pressure - 5.0 * dt)
        else:
            # Stationary → build brake pressure
            self._brake_pressure = min(180.0, self._brake_pressure + 3.0 * dt)

        return self._output(error, self._is_yawing)

    def _output(self, error: float, yawing: bool = False) -> Dict[str, float]:
        import numpy as np
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

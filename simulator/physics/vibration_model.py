"""
Nacelle vibration model.

Vibration sources:
  1. Rotational (1P): proportional to rotor speed, from mass imbalance
  2. Blade pass (3P): 3× rotor frequency, from tower shadow
  3. Aerodynamic: proportional to wind turbulence
  4. Structural broadband: random noise floor
  5. Power-dependent: drivetrain loading

Reference values (5MW, rated operation):
  Normal:  X = 0.5-2.0 mm/s,  Y = 0.4-1.5 mm/s
  Warning: > 4.0 mm/s
  Alarm:   > 7.0 mm/s

Can be replaced independently.
"""

import math
import numpy as np
from typing import Tuple


class VibrationModel:
    """
    Physics-based nacelle vibration model (X and Y directions).

    X-direction: fore-aft (wind direction), dominated by thrust and tower bending
    Y-direction: side-to-side, dominated by rotor imbalance
    """

    def __init__(self, seed: int = 0):
        self._rng = np.random.RandomState(seed)

        # Imbalance factors (unique per turbine, slight manufacturing variation)
        self._imbalance_x = 0.8 + self._rng.uniform(0, 0.4)
        self._imbalance_y = 0.6 + self._rng.uniform(0, 0.4)

        # Smoothing state (low-pass filter for realistic time behavior)
        self._vib_x_prev = 0.1
        self._vib_y_prev = 0.1

    def step(self, rotor_speed: float, wind_speed: float,
             power_kw: float, turbulence: float = 0.1,
             dt: float = 1.0) -> Tuple[float, float]:
        """
        Calculate vibration X, Y (mm/s) for current conditions.

        Args:
            rotor_speed: Rotor RPM
            wind_speed: m/s
            power_kw: Current power output
            turbulence: Wind turbulence intensity (0-0.5)
            dt: timestep

        Returns:
            (vib_x, vib_y) in mm/s
        """
        if rotor_speed < 0.5:
            # Standstill: very low ambient vibration
            target_x = 0.05 + self._rng.normal(0, 0.02)
            target_y = 0.03 + self._rng.normal(0, 0.02)
        else:
            # ── 1. Rotational component (1P frequency) ──
            rot_freq = rotor_speed / 60.0  # Hz
            rot_x = self._imbalance_x * rotor_speed * 0.03
            rot_y = self._imbalance_y * rotor_speed * 0.04

            # ── 2. Blade pass (3P) — tower shadow effect ──
            bp_x = rotor_speed * 0.008 * math.sin(2 * math.pi * 3 * rot_freq * self._rng.uniform(0, 1))
            bp_y = rotor_speed * 0.005

            # ── 3. Aerodynamic (turbulence-driven) ──
            aero_x = wind_speed * turbulence * 0.15
            aero_y = wind_speed * turbulence * 0.10

            # ── 4. Power/drivetrain load ──
            power_ratio = min(1.0, power_kw / 5000.0)
            load_x = power_ratio * 0.3
            load_y = power_ratio * 0.2

            # ── 5. Broadband noise ──
            noise_x = self._rng.normal(0, 0.08)
            noise_y = self._rng.normal(0, 0.06)

            target_x = rot_x + abs(bp_x) + aero_x + load_x + noise_x
            target_y = rot_y + bp_y + aero_y + load_y + noise_y

        # Low-pass filter (smoothing for realistic time behavior)
        alpha = min(1.0, dt / 2.0)  # ~2 second smoothing
        self._vib_x_prev += (target_x - self._vib_x_prev) * alpha
        self._vib_y_prev += (target_y - self._vib_y_prev) * alpha

        return max(0, self._vib_x_prev), max(0, self._vib_y_prev)

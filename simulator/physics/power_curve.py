"""
Aerodynamic power curve and rotor speed model.

Implements Region 1 (below cut-in), Region 2 (partial load, optimal TSR tracking),
and Region 3 (rated power, constant speed, pitch regulation).

Can be replaced independently for different turbine types.
"""

import math
import numpy as np
from typing import List, Tuple, Optional


# ─── Default Z72 5MW power curve (from typical 5MW offshore data) ────────
# (wind_speed_m_s, power_kw)
# Region 1: 0 → cut-in (0 kW)
# Region 2: cut-in → rated (cubic growth)
# Region 3: rated → cut-out (constant at rated)
DEFAULT_5MW_POWER_CURVE: List[Tuple[float, float]] = [
    (0.0, 0), (2.0, 0), (3.0, 0),          # Below cut-in
    (3.5, 40), (4.0, 100), (4.5, 180),      # Region 2 start
    (5.0, 290), (5.5, 430), (6.0, 610),
    (6.5, 830), (7.0, 1090), (7.5, 1400),
    (8.0, 1750), (8.5, 2150), (9.0, 2600),
    (9.5, 3050), (10.0, 3500), (10.5, 3950),
    (11.0, 4350), (11.5, 4700), (12.0, 4950),  # Approaching rated
    (12.5, 5000), (13.0, 5000), (14.0, 5000),  # Region 3 (constant)
    (15.0, 5000), (16.0, 5000), (17.0, 5000),
    (18.0, 5000), (19.0, 5000), (20.0, 5000),
    (21.0, 5000), (22.0, 5000), (23.0, 5000),
    (24.0, 5000), (25.0, 5000),                # Cut-out
    (25.5, 0), (26.0, 0),                       # Storm shutdown
]


class PowerCurveModel:
    """
    Lookup-table based power curve with physical Region 2/3 behavior.

    Region 2 (partial load): Power follows Cp × 0.5ρAV³, RPM tracks optimal TSR
    Region 3 (full load): Power = rated, RPM = rated RPM, pitch regulates
    """

    def __init__(self, power_curve: Optional[List[Tuple[float, float]]] = None,
                 rated_power_kw: float = 5000.0,
                 cut_in: float = 3.0, rated_speed: float = 12.0, cut_out: float = 25.0):
        self.rated_power_kw = rated_power_kw
        self.cut_in = cut_in
        self.rated_speed = rated_speed
        self.cut_out = cut_out

        # Build interpolation from power curve
        if power_curve:
            self._ws = np.array([p[0] for p in power_curve])
            self._pw = np.array([p[1] for p in power_curve])
        else:
            self._ws = np.array([p[0] for p in DEFAULT_5MW_POWER_CURVE])
            self._pw = np.array([p[1] for p in DEFAULT_5MW_POWER_CURVE])
            # Scale to rated power
            scale = rated_power_kw / 5000.0
            self._pw = self._pw * scale

    def get_power(self, wind_speed: float) -> float:
        """Get power output for a given wind speed (kW)."""
        if wind_speed < self.cut_in or wind_speed > self.cut_out:
            return 0.0
        return float(np.interp(wind_speed, self._ws, self._pw))

    def get_region(self, wind_speed: float) -> int:
        """Return operating region: 0=off, 1=below cut-in, 2=partial load, 3=rated."""
        if wind_speed < self.cut_in:
            return 1
        elif wind_speed < self.rated_speed:
            return 2
        elif wind_speed <= self.cut_out:
            return 3
        return 0


class RotorSpeedModel:
    """
    Rotor speed controller with Region 2/3 behavior.

    Region 2: Track optimal TSR → RPM proportional to wind speed
    Region 3: Hold rated RPM constant → pitch controls power
    """

    def __init__(self, rotor_diameter: float = 126.0,
                 optimal_tsr: float = 7.5,
                 max_rpm: float = 15.0,
                 rated_speed: float = 12.0,
                 gear_ratio: float = 100.0):
        self.rotor_diameter = rotor_diameter
        self.optimal_tsr = optimal_tsr
        self.max_rpm = max_rpm
        self.rated_speed = rated_speed
        self.gear_ratio = gear_ratio

        # Rated RPM at rated wind speed
        self.rated_rpm = min(
            (optimal_tsr * rated_speed * 60) / (math.pi * rotor_diameter),
            max_rpm
        )

        # Rotor inertia response (seconds to reach 63% of target)
        self.time_constant = 8.0  # seconds (realistic for large rotor)

    def get_target_rpm(self, wind_speed: float, cut_in: float = 3.0) -> float:
        """Calculate target rotor RPM for current wind speed."""
        if wind_speed < cut_in:
            return 0.0

        if wind_speed < self.rated_speed:
            # Region 2: optimal TSR tracking
            target = (self.optimal_tsr * wind_speed * 60) / (math.pi * self.rotor_diameter)
            return min(target, self.max_rpm)
        else:
            # Region 3: hold rated RPM
            return self.rated_rpm

    def step(self, current_rpm: float, wind_speed: float,
             cut_in: float, is_producing: bool, is_starting: bool,
             dt: float) -> float:
        """Advance rotor speed by one timestep with inertia."""
        if is_producing:
            target = self.get_target_rpm(wind_speed, cut_in)
            # First-order lag with realistic time constant
            alpha = 1.0 - math.exp(-dt / self.time_constant)
            return current_rpm + (target - current_rpm) * alpha
        elif is_starting:
            target = self.get_target_rpm(wind_speed, cut_in)
            # Slower acceleration during startup
            alpha = 1.0 - math.exp(-dt / (self.time_constant * 3))
            return current_rpm + (target - current_rpm) * alpha
        else:
            # Braking: mechanical + aero brake
            brake_rate = 0.5  # RPM/s
            return max(0.0, current_rpm - brake_rate * dt)

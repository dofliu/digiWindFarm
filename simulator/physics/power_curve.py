"""
Aerodynamic power curve and rotor speed model.

Implements Region 1 (below cut-in), Region 2 (partial load, optimal TSR tracking),
and Region 3 (rated power, constant speed, pitch regulation).

Includes:
  - Cp(lambda, beta) analytical surface model
  - Thrust coefficient Ct(lambda, beta)
  - Dynamic stall transient loading factor
  - Aero-load output for coupling into drivetrain and vibration

Can be replaced independently for different turbine types.
"""

import math
import numpy as np
from typing import List, Tuple, Optional, Dict


# ─── Default Z72-2000-MV power curve (Harakosan 2MW direct-drive) ────────
# (wind_speed_m_s, power_kw)
# Based on Z72 OEM data: rated 2000kW, cut-in 3m/s, rated 13m/s, cut-out 25m/s
# Rotor diameter 70.65m, direct-drive PMSG
DEFAULT_Z72_POWER_CURVE: List[Tuple[float, float]] = [
    (0.0, 0), (2.0, 0), (3.0, 0),          # Below cut-in
    (3.5, 15), (4.0, 40), (4.5, 75),       # Region 2 start
    (5.0, 120), (5.5, 175), (6.0, 245),
    (6.5, 330), (7.0, 435), (7.5, 555),
    (8.0, 690), (8.5, 845), (9.0, 1010),
    (9.5, 1185), (10.0, 1365), (10.5, 1540),
    (11.0, 1700), (11.5, 1830), (12.0, 1930),  # Approaching rated
    (12.5, 1980), (13.0, 2000), (14.0, 2000),  # Region 3 (constant)
    (15.0, 2000), (16.0, 2000), (17.0, 2000),
    (18.0, 2000), (19.0, 2000), (20.0, 2000),
    (21.0, 2000), (22.0, 2000), (23.0, 2000),
    (24.0, 2000), (25.0, 2000),                # Cut-out
    (25.5, 0), (26.0, 0),                       # Storm shutdown
]


# ─── Cp(λ, β) Analytical Surface Model ──────────────────────────────────
#
# Standard parametric model widely used in wind energy literature:
#   Cp(λ, β) = c1 · (c2/λi − c3·β − c4) · exp(−c5/λi) + c6·λ
#   where  1/λi = 1/(λ + 0.08·β) − 0.035/(β³ + 1)
#
# The coefficients below are tuned to produce Cp_max ≈ 0.48 at optimal TSR,
# consistent with modern 3-blade horizontal axis turbines.

class CpSurfaceModel:
    """Analytical Cp(λ, β) surface with thrust coefficient Ct."""

    def __init__(self, cp_max: float = 0.48,
                 c1: float = 0.5176, c2: float = 116.0, c3: float = 0.4,
                 c4: float = 5.0, c5: float = 21.0, c6: float = 0.0068):
        self.cp_max = cp_max
        self.c1 = c1
        self.c2 = c2
        self.c3 = c3
        self.c4 = c4
        self.c5 = c5
        self.c6 = c6

        # Compute raw peak and scaling factor so actual Cp_max matches cp_max
        raw_peak = self._cp_raw(8.1, 0.0)
        self._scale = cp_max / max(raw_peak, 0.01)

        # Dynamic stall state
        self._prev_wind = 0.0
        self._stall_factor = 1.0

    def _lambda_i(self, lam: float, beta: float) -> float:
        beta_r = max(beta, -2.0)
        denom1 = lam + 0.08 * beta_r
        denom2 = beta_r ** 3 + 1.0
        if abs(denom1) < 0.01:
            denom1 = 0.01
        if abs(denom2) < 0.01:
            denom2 = 0.01
        return 1.0 / (1.0 / denom1 - 0.035 / denom2)

    def _cp_raw(self, lam: float, beta: float) -> float:
        li = self._lambda_i(lam, beta)
        if abs(li) < 0.01:
            return 0.0
        return self.c1 * (self.c2 / li - self.c3 * beta - self.c4) * math.exp(-self.c5 / li) + self.c6 * lam

    def get_cp(self, tsr: float, pitch_deg: float) -> float:
        """Compute power coefficient Cp for given tip-speed ratio and pitch angle."""
        raw = self._cp_raw(tsr, pitch_deg)
        cp = raw * self._scale
        return max(0.0, min(self.cp_max, cp))

    def get_ct(self, tsr: float, pitch_deg: float) -> float:
        """Compute thrust coefficient Ct from Cp.

        Ct relates to axial force on rotor. Empirical relation:
          Ct ≈ (8/9) · Cp/λ · (λ² + λ·Ct_correction)
        Simplified here as a function of Cp and TSR with Glauert correction.
        """
        cp = self.get_cp(tsr, pitch_deg)
        if tsr < 0.5:
            return 0.0
        # Simplified momentum theory: Ct = 4a(1-a) where a ≈ 0.5(1 - sqrt(1 - Ct))
        # Approximate: Ct ≈ cp * (tsr + 1.5) / tsr capped at Betz-like limit
        ct = cp * (tsr + 1.5) / max(tsr, 1.0)
        return max(0.0, min(0.95, ct))

    def get_aero_thrust_kn(self, wind_speed: float, ct: float,
                           rotor_diameter: float, air_density: float = 1.225) -> float:
        """Compute aerodynamic thrust force in kN."""
        area = math.pi * (rotor_diameter / 2.0) ** 2
        thrust_n = 0.5 * air_density * area * ct * wind_speed ** 2
        return thrust_n / 1000.0

    def update_dynamic_stall(self, wind_speed: float, dt: float) -> float:
        """Compute dynamic stall factor: transient Cp reduction during rapid wind changes.

        When wind speed changes rapidly, airflow separation on blades causes
        temporary loss of aerodynamic efficiency. This models the transient.
        Returns a factor 0.0–1.0 to multiply with Cp.
        """
        wind_rate = abs(wind_speed - self._prev_wind) / max(dt, 0.1)
        self._prev_wind = wind_speed

        # Stall onset at >2 m/s² wind acceleration, full effect at >6 m/s²
        stall_target = 1.0
        if wind_rate > 2.0:
            stall_depth = min(0.35, (wind_rate - 2.0) * 0.085)
            stall_target = 1.0 - stall_depth

        # Recovery is slower than onset (aerodynamic hysteresis)
        tau = 1.5 if stall_target < self._stall_factor else 4.0
        alpha = 1.0 - math.exp(-dt / tau)
        self._stall_factor += (stall_target - self._stall_factor) * alpha
        return self._stall_factor


class AeroOutput:
    """Container for aerodynamic computation results per timestep."""
    __slots__ = ('power_kw', 'cp', 'ct', 'thrust_kn', 'tsr', 'stall_factor',
                 'aero_torque_knm', 'aero_load_factor')

    def __init__(self):
        self.power_kw: float = 0.0
        self.cp: float = 0.0
        self.ct: float = 0.0
        self.thrust_kn: float = 0.0
        self.tsr: float = 0.0
        self.stall_factor: float = 1.0
        self.aero_torque_knm: float = 0.0
        self.aero_load_factor: float = 0.0


class PowerCurveModel:
    """
    Lookup-table based power curve with physical Region 2/3 behavior,
    enhanced with Cp(λ,β) surface, thrust coefficient, and dynamic stall.

    Region 2 (partial load): Power follows Cp × 0.5ρAV³, RPM tracks optimal TSR
    Region 3 (full load): Power = rated, RPM = rated RPM, pitch regulates
    """

    def __init__(self, power_curve: Optional[List[Tuple[float, float]]] = None,
                 rated_power_kw: float = 5000.0,
                 cut_in: float = 3.0, rated_speed: float = 12.0, cut_out: float = 25.0,
                 rotor_diameter: float = 70.65, cp_max: float = 0.48,
                 air_density: float = 1.225):
        self.rated_power_kw = rated_power_kw
        self.cut_in = cut_in
        self.rated_speed = rated_speed
        self.cut_out = cut_out
        self.rotor_diameter = rotor_diameter
        self.air_density = air_density

        # Build interpolation from power curve (backward-compatible)
        if power_curve:
            self._ws = np.array([p[0] for p in power_curve])
            self._pw = np.array([p[1] for p in power_curve])
        else:
            self._ws = np.array([p[0] for p in DEFAULT_Z72_POWER_CURVE])
            self._pw = np.array([p[1] for p in DEFAULT_Z72_POWER_CURVE])
            scale = rated_power_kw / 2000.0
            self._pw = self._pw * scale

        # Cp surface model
        self.cp_surface = CpSurfaceModel(cp_max=cp_max)

        # Last computed aero output
        self._last_aero = AeroOutput()

    def get_power(self, wind_speed: float) -> float:
        """Get power output for a given wind speed (kW). Backward-compatible."""
        if wind_speed < self.cut_in or wind_speed > self.cut_out:
            return 0.0
        return float(np.interp(wind_speed, self._ws, self._pw))

    def get_power_cp(self, wind_speed: float, rotor_rpm: float,
                     pitch_deg: float, dt: float = 1.0) -> AeroOutput:
        """Compute power using Cp(λ,β) surface with dynamic stall and thrust.

        This is the full aerodynamic computation. The result includes power,
        Cp, Ct, thrust force, and aero load factor for coupling into
        drivetrain and vibration models.
        """
        out = AeroOutput()

        if wind_speed < self.cut_in or wind_speed > self.cut_out or rotor_rpm < 0.1:
            self._last_aero = out
            return out

        # Tip-speed ratio
        omega = rotor_rpm * 2.0 * math.pi / 60.0
        tsr = omega * (self.rotor_diameter / 2.0) / max(wind_speed, 0.5)
        out.tsr = tsr

        # Cp from surface model
        cp = self.cp_surface.get_cp(tsr, pitch_deg)

        # Dynamic stall factor
        out.stall_factor = self.cp_surface.update_dynamic_stall(wind_speed, dt)
        cp *= out.stall_factor
        out.cp = cp

        # Aerodynamic power: P = Cp × 0.5 × ρ × A × V³
        area = math.pi * (self.rotor_diameter / 2.0) ** 2
        p_aero_w = cp * 0.5 * self.air_density * area * wind_speed ** 3
        p_aero_kw = p_aero_w / 1000.0

        # Blend with lookup curve for stability: 70% Cp-based, 30% lookup
        p_lookup = self.get_power(wind_speed)
        out.power_kw = min(self.rated_power_kw, p_aero_kw * 0.7 + p_lookup * 0.3)

        # Thrust coefficient and force
        out.ct = self.cp_surface.get_ct(tsr, pitch_deg) * out.stall_factor
        out.thrust_kn = self.cp_surface.get_aero_thrust_kn(
            wind_speed, out.ct, self.rotor_diameter, self.air_density)

        # Aero torque (kNm) = P / ω
        if omega > 0.01:
            out.aero_torque_knm = (out.power_kw * 1000.0) / (omega * 1000.0)
        else:
            out.aero_torque_knm = 0.0

        # Aero load factor: normalized thrust for coupling (0-1 range)
        rated_thrust = self.cp_surface.get_aero_thrust_kn(
            self.rated_speed, 0.8, self.rotor_diameter, self.air_density)
        out.aero_load_factor = min(1.5, out.thrust_kn / max(rated_thrust, 1.0))

        self._last_aero = out
        return out

    @property
    def last_aero(self) -> AeroOutput:
        return self._last_aero

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

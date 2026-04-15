"""
Fatigue and structural load model for wind turbine simulation.

Provides:
  - Tower base bending moment (fore-aft, side-to-side)
  - Blade root bending moment (flapwise, edgewise)
  - Simplified rainflow cycle counting
  - Damage Equivalent Load (DEL) computation
  - Cumulative fatigue damage via Miner's rule

Reference:
  - IEC 61400-1 Ed.4 for load definitions
  - Miner's rule for linear damage accumulation
  - Simplified DEL from 1-Hz equivalent load range

No dependency on FastAPI, frontend, or storage; only numpy.
"""

import math
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class FatigueSpec:
    """Configuration for fatigue tracking."""

    # S-N curve exponent (Wöhler exponent m)
    # Steel (tower, shaft): m ≈ 4
    # Composite (blade): m ≈ 10
    sn_exp_tower: float = 4.0
    sn_exp_blade: float = 10.0

    # Reference cycles to failure at reference load (S-N anchor)
    n_ref_tower: float = 1e7
    n_ref_blade: float = 1e7

    # Reference load ranges (kNm) for S-N curve normalization
    load_ref_tower_fa: float = 3000.0   # tower fore-aft
    load_ref_tower_ss: float = 2000.0   # tower side-to-side
    load_ref_blade_flap: float = 1200.0  # blade flapwise
    load_ref_blade_edge: float = 800.0   # blade edgewise

    # DEL time basis (seconds) — 1-Hz equivalent
    del_time_basis: float = 600.0  # 10-minute basis for DEL

    # Cycle buffer length for rainflow counting
    rainflow_buffer_len: int = 600  # ~10 min at 1 Hz

    # Fatigue alarm thresholds (damage fraction 0→1)
    alarm_notice: float = 0.30    # level 1: 注意
    alarm_warning: float = 0.60   # level 2: 警告
    alarm_danger: float = 0.80    # level 3: 危險
    alarm_shutdown: float = 0.95  # level 4: 停機


class RainflowCounter:
    """Simplified online rainflow cycle counter.

    Uses a peak-valley extraction + 3-point rainflow method.
    Maintains a rolling buffer to compute cycle ranges.
    """

    def __init__(self, buffer_len: int = 600):
        self._buffer_len = buffer_len
        self._peaks: List[float] = []
        self._last_value: Optional[float] = None
        self._last_direction: Optional[int] = None  # +1 rising, -1 falling
        self._cycle_ranges: List[float] = []

    def add_sample(self, value: float):
        """Add a new load sample and extract peaks/valleys."""
        if self._last_value is None:
            self._last_value = value
            return

        diff = value - self._last_value
        if abs(diff) < 1e-6:
            return

        direction = 1 if diff > 0 else -1

        if self._last_direction is not None and direction != self._last_direction:
            # Reversal detected — record peak/valley
            self._peaks.append(self._last_value)
            if len(self._peaks) > self._buffer_len:
                self._peaks = self._peaks[-self._buffer_len:]
            self._extract_cycles()

        self._last_value = value
        self._last_direction = direction

    def _extract_cycles(self):
        """3-point rainflow extraction from peak/valley sequence."""
        i = 0
        while i < len(self._peaks) - 2:
            s0 = self._peaks[i]
            s1 = self._peaks[i + 1]
            s2 = self._peaks[i + 2]

            r1 = abs(s1 - s0)
            r2 = abs(s2 - s1)

            if r2 >= r1:
                # Full cycle extracted
                self._cycle_ranges.append(r1)
                self._peaks.pop(i + 1)
                self._peaks.pop(i)
                if i > 0:
                    i -= 1
            else:
                i += 1

    def get_cycle_ranges(self) -> List[float]:
        """Return extracted cycle ranges and clear buffer."""
        ranges = self._cycle_ranges
        self._cycle_ranges = []
        return ranges

    @property
    def peak_count(self) -> int:
        """Number of peaks currently in the rainflow buffer."""
        return len(self._peaks)


class FatigueModel:
    """Structural load and fatigue tracking for a single wind turbine.

    Computes instantaneous structural loads from operating conditions,
    tracks cycle history via rainflow counting, and accumulates fatigue
    damage using Miner's rule.
    """

    def __init__(self, spec: Optional[FatigueSpec] = None,
                 seed: Optional[int] = None,
                 rated_power_kw: float = 2000.0,
                 rotor_diameter: float = 70.65,
                 hub_height: float = 64.0):
        self.spec = spec or FatigueSpec()
        self._rng = np.random.RandomState(seed)
        self._rated_power_kw = rated_power_kw
        self._rotor_diameter = rotor_diameter
        self._hub_height = hub_height
        self._rotor_area = math.pi * (rotor_diameter / 2) ** 2

        # Per-turbine individuality (small persistent offsets)
        self._tower_stiffness_scale = 1.0 + self._rng.uniform(-0.06, 0.06)
        self._blade_stiffness_scale = 1.0 + self._rng.uniform(-0.08, 0.08)

        # Rainflow counters for each load channel
        buf_len = self.spec.rainflow_buffer_len
        self._rf_tower_fa = RainflowCounter(buf_len)
        self._rf_tower_ss = RainflowCounter(buf_len)
        self._rf_blade_flap = RainflowCounter(buf_len)
        self._rf_blade_edge = RainflowCounter(buf_len)

        # Cumulative damage (Miner's sum, 0→1)
        self.damage_tower_fa: float = 0.0
        self.damage_tower_ss: float = 0.0
        self.damage_blade_flap: float = 0.0
        self.damage_blade_edge: float = 0.0

        # Running DEL accumulators (for 10-min rolling window)
        self._del_cycle_buf_tower_fa: List[float] = []
        self._del_cycle_buf_tower_ss: List[float] = []
        self._del_cycle_buf_blade_flap: List[float] = []
        self._del_cycle_buf_blade_edge: List[float] = []
        self._del_time_accum: float = 0.0

        # Latest computed DEL values
        self.del_tower_fa: float = 0.0
        self.del_tower_ss: float = 0.0
        self.del_blade_flap: float = 0.0
        self.del_blade_edge: float = 0.0

        # Latest instantaneous loads
        self.load_tower_fa: float = 0.0
        self.load_tower_ss: float = 0.0
        self.load_blade_flap: float = 0.0
        self.load_blade_edge: float = 0.0

        # Alarm level tracking (0=normal, 1=notice, 2=warning, 3=danger, 4=shutdown)
        self.alarm_level_tower: int = 0
        self.alarm_level_blade: int = 0
        # Remaining useful life estimate (hours), -1 = insufficient data
        self.rul_hours: float = -1.0

        # Lifetime counters
        self._total_sim_time: float = 0.0
        self._total_production_time: float = 0.0

    def step(self, dt: float,
             wind_speed: float,
             rotor_speed_rpm: float,
             power_kw: float,
             pitch_angle_deg: float,
             yaw_error_deg: float,
             thrust_kn: float,
             turbulence_intensity: float,
             is_producing: bool,
             is_starting: bool,
             is_emergency_stop: bool) -> Dict[str, float]:
        """Advance fatigue model by one timestep.

        Args:
            dt: timestep in seconds
            wind_speed: effective wind speed (m/s)
            rotor_speed_rpm: current rotor speed
            power_kw: current power output
            pitch_angle_deg: current blade pitch angle
            yaw_error_deg: current yaw misalignment
            thrust_kn: aerodynamic thrust force
            turbulence_intensity: current TI
            is_producing: turbine in production state
            is_starting: turbine in startup state
            is_emergency_stop: turbine in emergency stop

        Returns:
            Dict of fatigue-related SCADA tag values
        """
        self._total_sim_time += dt
        if is_producing:
            self._total_production_time += dt

        # ── Compute instantaneous structural loads ──
        loads = self._compute_loads(
            wind_speed, rotor_speed_rpm, power_kw,
            pitch_angle_deg, yaw_error_deg, thrust_kn,
            turbulence_intensity, is_producing, is_starting,
            is_emergency_stop, dt,
        )

        self.load_tower_fa = loads["tower_fa"]
        self.load_tower_ss = loads["tower_ss"]
        self.load_blade_flap = loads["blade_flap"]
        self.load_blade_edge = loads["blade_edge"]

        # ── Feed into rainflow counters ──
        self._rf_tower_fa.add_sample(self.load_tower_fa)
        self._rf_tower_ss.add_sample(self.load_tower_ss)
        self._rf_blade_flap.add_sample(self.load_blade_flap)
        self._rf_blade_edge.add_sample(self.load_blade_edge)

        # ── Extract cycles and accumulate damage ──
        cycles_tfa = self._rf_tower_fa.get_cycle_ranges()
        cycles_tss = self._rf_tower_ss.get_cycle_ranges()
        cycles_bfl = self._rf_blade_flap.get_cycle_ranges()
        cycles_bed = self._rf_blade_edge.get_cycle_ranges()

        self.damage_tower_fa += self._miner_damage(
            cycles_tfa, self.spec.sn_exp_tower,
            self.spec.load_ref_tower_fa, self.spec.n_ref_tower)
        self.damage_tower_ss += self._miner_damage(
            cycles_tss, self.spec.sn_exp_tower,
            self.spec.load_ref_tower_ss, self.spec.n_ref_tower)
        self.damage_blade_flap += self._miner_damage(
            cycles_bfl, self.spec.sn_exp_blade,
            self.spec.load_ref_blade_flap, self.spec.n_ref_blade)
        self.damage_blade_edge += self._miner_damage(
            cycles_bed, self.spec.sn_exp_blade,
            self.spec.load_ref_blade_edge, self.spec.n_ref_blade)

        # ── Rolling DEL accumulation (10-min window) ──
        self._del_cycle_buf_tower_fa.extend(cycles_tfa)
        self._del_cycle_buf_tower_ss.extend(cycles_tss)
        self._del_cycle_buf_blade_flap.extend(cycles_bfl)
        self._del_cycle_buf_blade_edge.extend(cycles_bed)
        self._del_time_accum += dt

        if self._del_time_accum >= self.spec.del_time_basis:
            self.del_tower_fa = self._compute_del(
                self._del_cycle_buf_tower_fa, self.spec.sn_exp_tower,
                self._del_time_accum)
            self.del_tower_ss = self._compute_del(
                self._del_cycle_buf_tower_ss, self.spec.sn_exp_tower,
                self._del_time_accum)
            self.del_blade_flap = self._compute_del(
                self._del_cycle_buf_blade_flap, self.spec.sn_exp_blade,
                self._del_time_accum)
            self.del_blade_edge = self._compute_del(
                self._del_cycle_buf_blade_edge, self.spec.sn_exp_blade,
                self._del_time_accum)
            # Reset accumulators
            self._del_cycle_buf_tower_fa.clear()
            self._del_cycle_buf_tower_ss.clear()
            self._del_cycle_buf_blade_flap.clear()
            self._del_cycle_buf_blade_edge.clear()
            self._del_time_accum = 0.0

        # Clamp damage to [0, 1]
        self.damage_tower_fa = min(1.0, self.damage_tower_fa)
        self.damage_tower_ss = min(1.0, self.damage_tower_ss)
        self.damage_blade_flap = min(1.0, self.damage_blade_flap)
        self.damage_blade_edge = min(1.0, self.damage_blade_edge)

        # ── Alarm level from worst-case damage ──
        max_tower_dmg = max(self.damage_tower_fa, self.damage_tower_ss)
        max_blade_dmg = max(self.damage_blade_flap, self.damage_blade_edge)
        self.alarm_level_tower = self._damage_to_alarm(max_tower_dmg)
        self.alarm_level_blade = self._damage_to_alarm(max_blade_dmg)

        # ── RUL estimation from average damage rate ──
        prod_h = self._total_production_time / 3600.0
        max_dmg = max(max_tower_dmg, max_blade_dmg)
        if prod_h > 1.0 and max_dmg > 1e-10:
            rate_per_h = max_dmg / prod_h
            self.rul_hours = max(0.0, (1.0 - max_dmg) / rate_per_h)
        else:
            self.rul_hours = -1.0

        return {
            "tower_fa_moment_knm": round(self.load_tower_fa, 1),
            "tower_ss_moment_knm": round(self.load_tower_ss, 1),
            "blade_flap_moment_knm": round(self.load_blade_flap, 1),
            "blade_edge_moment_knm": round(self.load_blade_edge, 1),
            "del_tower_fa_knm": round(self.del_tower_fa, 1),
            "del_tower_ss_knm": round(self.del_tower_ss, 1),
            "del_blade_flap_knm": round(self.del_blade_flap, 1),
            "del_blade_edge_knm": round(self.del_blade_edge, 1),
            "damage_tower_fa": round(self.damage_tower_fa, 8),
            "damage_tower_ss": round(self.damage_tower_ss, 8),
            "damage_blade_flap": round(self.damage_blade_flap, 8),
            "damage_blade_edge": round(self.damage_blade_edge, 8),
            "production_hours": round(self._total_production_time / 3600.0, 2),
            "alarm_level_tower": self.alarm_level_tower,
            "alarm_level_blade": self.alarm_level_blade,
            "rul_hours": round(self.rul_hours, 1),
        }

    def _damage_to_alarm(self, damage: float) -> int:
        """Convert damage fraction to alarm level (0–4)."""
        s = self.spec
        if damage >= s.alarm_shutdown:
            return 4
        if damage >= s.alarm_danger:
            return 3
        if damage >= s.alarm_warning:
            return 2
        if damage >= s.alarm_notice:
            return 1
        return 0

    def _compute_loads(self, wind_speed: float, rotor_speed_rpm: float,
                       power_kw: float, pitch_deg: float,
                       yaw_error_deg: float, thrust_kn: float,
                       ti: float, is_producing: bool,
                       is_starting: bool, is_estop: bool,
                       dt: float) -> Dict[str, float]:
        """Compute instantaneous structural loads (kNm)."""
        rho = 1.225  # air density
        R = self._rotor_diameter / 2
        H = self._hub_height

        # ── Tower fore-aft bending moment ──
        # M_FA ≈ thrust × hub_height + gravity × mass_offset + turbulence_dynamic
        if thrust_kn > 0:
            thrust_moment = thrust_kn * H * self._tower_stiffness_scale
        else:
            # Parked/idle: wind drag on tower (simplified)
            drag_force = 0.5 * rho * 1.2 * (self._rotor_diameter * 0.05) * wind_speed ** 2 / 1000.0
            thrust_moment = drag_force * H * 0.5

        # Turbulence-induced dynamic load
        turb_dynamic = ti * wind_speed * 0.5 * rho * self._rotor_area / 1000.0 * H
        turb_noise = self._rng.normal(0, max(0.01, turb_dynamic * 0.15))

        tower_fa = thrust_moment + turb_dynamic * 0.3 + turb_noise

        # Emergency stop: transient load spike
        if is_estop:
            tower_fa *= 1.8 + self._rng.uniform(0, 0.3)

        # Starting: moderate loads
        if is_starting:
            tower_fa *= 0.4 + self._rng.uniform(0, 0.1)

        # ── Tower side-to-side bending moment ──
        # Driven by yaw error, rotor imbalance, and lateral turbulence
        yaw_rad = math.radians(yaw_error_deg)
        lateral_thrust = thrust_kn * abs(math.sin(yaw_rad)) if thrust_kn > 0 else 0.0
        rotor_imbalance = rotor_speed_rpm * 0.15 * self._rng.normal(1, 0.2) if rotor_speed_rpm > 1 else 0.0

        tower_ss = (lateral_thrust * H * 0.3 + rotor_imbalance +
                    abs(self._rng.normal(0, turb_dynamic * 0.08)))

        # ── Blade flapwise bending moment ──
        # Driven by thrust distribution along blade, pitch, and wind shear
        if is_producing and rotor_speed_rpm > 1:
            # Simplified: thrust per blade × 2/3 R (center of pressure)
            blade_thrust = thrust_kn / 3.0 if thrust_kn > 0 else 0.0
            blade_flap = blade_thrust * R * 0.667 * self._blade_stiffness_scale

            # Wind shear contribution (top vs bottom of rotor)
            shear_exp = 0.2  # power law exponent
            shear_load = (0.5 * rho * self._rotor_area / 3.0 *
                          wind_speed ** 2 * shear_exp * 0.1 * R / 1000.0)
            blade_flap += shear_load

            # Pitch effect: higher pitch → lower flap load
            pitch_factor = max(0.3, 1.0 - abs(pitch_deg) * 0.008)
            blade_flap *= pitch_factor

            # Turbulence
            blade_flap += abs(self._rng.normal(0, blade_flap * 0.1 * ti))
        else:
            # Parked: gravity + wind drag
            blade_flap = 0.5 * rho * 0.3 * R * 0.5 * wind_speed ** 2 / 1000.0 * R * 0.5

        if is_estop:
            blade_flap *= 1.5

        # ── Blade edgewise bending moment ──
        # Gravity-driven (1P cyclic) + aerodynamic torque
        if is_producing and rotor_speed_rpm > 1:
            # Gravity component (blade mass × R/3 × g × sin(azimuth))
            # We simulate the cycle envelope, not individual azimuth
            blade_mass_kg = 4000.0 * (R / 35.0) ** 2.5  # rough scaling
            gravity_moment = blade_mass_kg * 9.81 * R / 3.0 / 1000.0  # kNm

            # Aero torque contribution
            aero_torque_blade = power_kw / max(1.0, rotor_speed_rpm * math.pi / 30.0) / 3.0

            # 1P cyclic oscillation
            omega = rotor_speed_rpm * math.pi / 30.0
            phase = (self._total_sim_time * omega) % (2.0 * math.pi)
            cyclic = gravity_moment * math.sin(phase)

            blade_edge = abs(cyclic) + aero_torque_blade * 0.1 * self._blade_stiffness_scale
            blade_edge += abs(self._rng.normal(0, blade_edge * 0.05))
        else:
            blade_edge = 2.0 + abs(self._rng.normal(0, 0.5))  # parked gravity

        return {
            "tower_fa": max(0.0, tower_fa),
            "tower_ss": max(0.0, tower_ss),
            "blade_flap": max(0.0, blade_flap),
            "blade_edge": max(0.0, blade_edge),
        }

    @staticmethod
    def _miner_damage(cycle_ranges: List[float], m: float,
                      s_ref: float, n_ref: float) -> float:
        """Compute incremental Miner's damage from a list of cycle ranges.

        D = Σ (1 / N_i) where N_i = N_ref × (S_ref / S_i)^m
        """
        if not cycle_ranges or s_ref <= 0:
            return 0.0

        damage = 0.0
        for s_range in cycle_ranges:
            if s_range <= 0:
                continue
            n_i = n_ref * (s_ref / s_range) ** m
            damage += 1.0 / max(1.0, n_i)

        return damage

    @staticmethod
    def _compute_del(cycle_ranges: List[float], m: float,
                     time_span: float) -> float:
        """Compute Damage Equivalent Load for the given cycle ranges.

        DEL = (Σ S_i^m / n_eq)^(1/m)
        where n_eq = equivalent number of cycles at 1 Hz over time_span.
        """
        if not cycle_ranges or time_span <= 0:
            return 0.0

        n_eq = time_span  # 1 Hz equivalent
        sum_sm = sum(s ** m for s in cycle_ranges if s > 0)

        if sum_sm <= 0:
            return 0.0

        return (sum_sm / n_eq) ** (1.0 / m)

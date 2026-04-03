"""
Independent physics-based wind turbine model.

Produces all 39+ SCADA data points with physically-coupled relationships.
No dependency on FastAPI, frontend, or storage — only numpy.

Turbine specifications (cut-in, cut-out, rated power, power curve, etc.)
are configurable via TurbineSpec dataclass. Power curtailment is supported.
"""

import math
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class TurbineSpec:
    """Configurable wind turbine specifications."""

    # ── Basic parameters ──
    rated_power_kw: float = 5000.0       # kW
    rotor_diameter: float = 126.0        # m
    hub_height: float = 90.0             # m
    cut_in_speed: float = 3.0            # m/s
    rated_speed: float = 12.0            # m/s
    cut_out_speed: float = 25.0          # m/s

    # ── Drivetrain ──
    gear_ratio: float = 100.0
    generator_efficiency: float = 0.95
    generator_poles: int = 4
    nominal_voltage: float = 690.0       # V
    air_density: float = 1.225           # kg/m³

    # ── Rotor ──
    max_rotor_rpm: float = 15.0          # RPM
    optimal_tsr: float = 7.5             # Tip Speed Ratio
    cp_max: float = 0.48                 # Max power coefficient

    # ── Power curtailment (限載) ──
    curtailment_kw: Optional[float] = None   # None = no curtailment

    # ── Custom power curve (optional) ──
    # List of (wind_speed_m_s, power_kw) points. If provided, overrides Cp-based calculation.
    # Example: [(3,0), (5,200), (8,1500), (12,5000), (15,5000), (25,5000)]
    power_curve: Optional[List[Tuple[float, float]]] = None

    def to_dict(self) -> dict:
        d = {
            "rated_power_kw": self.rated_power_kw,
            "rotor_diameter": self.rotor_diameter,
            "hub_height": self.hub_height,
            "cut_in_speed": self.cut_in_speed,
            "rated_speed": self.rated_speed,
            "cut_out_speed": self.cut_out_speed,
            "gear_ratio": self.gear_ratio,
            "generator_efficiency": self.generator_efficiency,
            "generator_poles": self.generator_poles,
            "nominal_voltage": self.nominal_voltage,
            "air_density": self.air_density,
            "max_rotor_rpm": self.max_rotor_rpm,
            "optimal_tsr": self.optimal_tsr,
            "cp_max": self.cp_max,
            "curtailment_kw": self.curtailment_kw,
            "power_curve": self.power_curve,
        }
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "TurbineSpec":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


# ── Preset turbine specs ──────────────────────────────────────────────

TURBINE_PRESETS: Dict[str, TurbineSpec] = {
    "z72_5mw": TurbineSpec(),  # Default Z72 Bachmann 5MW
    "vestas_v90_3mw": TurbineSpec(
        rated_power_kw=3000, rotor_diameter=90, hub_height=80,
        cut_in_speed=4.0, rated_speed=13.0, cut_out_speed=25.0,
        gear_ratio=104.5, max_rotor_rpm=16.7, optimal_tsr=8.0,
    ),
    "sg_8mw": TurbineSpec(
        rated_power_kw=8000, rotor_diameter=167, hub_height=92,
        cut_in_speed=3.0, rated_speed=12.0, cut_out_speed=25.0,
        gear_ratio=1.0, generator_poles=300, max_rotor_rpm=10.6,
        optimal_tsr=9.0, cp_max=0.49,
    ),
    "goldwind_2.5mw": TurbineSpec(
        rated_power_kw=2500, rotor_diameter=121, hub_height=90,
        cut_in_speed=3.0, rated_speed=10.3, cut_out_speed=22.0,
        gear_ratio=1.0, generator_poles=96, max_rotor_rpm=11.5,
        optimal_tsr=8.5, cp_max=0.47,
    ),
}


class ThermalModel:
    """First-order thermal model: dT/dt = (Q_in - (T - T_amb) / R_th) / C_th"""

    def __init__(self, thermal_resistance: float, thermal_capacity: float,
                 initial_temp: float = 25.0):
        self.R_th = thermal_resistance
        self.C_th = thermal_capacity
        self.temperature = initial_temp

    def step(self, heat_input_kw: float, ambient_temp: float, dt: float) -> float:
        dT = (heat_input_kw - (self.temperature - ambient_temp) / self.R_th) / self.C_th * dt
        self.temperature += dT
        return self.temperature


class TurbinePhysicsModel:
    """
    Complete wind turbine physics model aligned to Z72 Bachmann SCADA tags.

    Output is a flat dict keyed by SCADA tag IDs (matching scada_registry.py).
    All internal state is encapsulated — caller only provides environmental inputs.
    """

    def __init__(self, spec: Optional[TurbineSpec] = None, seed: Optional[int] = None):
        self.spec = spec or TurbineSpec()
        self._rng = np.random.RandomState(seed)

        # Precompute power curve lookup if provided
        self._power_curve_interp = None
        if self.spec.power_curve:
            ws = [p[0] for p in self.spec.power_curve]
            pw = [p[1] for p in self.spec.power_curve]
            self._power_curve_interp = (np.array(ws), np.array(pw))

        # ── State variables ──
        self.tur_state = 1
        self.rotor_speed = 0.0
        self.pitch_angle = 90.0
        self._pitch_bl = [90.0, 90.0, 90.0]
        self.yaw_angle = 270.0
        self.cable_windup = 0.0

        # ── Thermal models ──
        self._gen_stator_temp = ThermalModel(0.015, 200.0, 35.0)
        self._gen_air_temp = ThermalModel(0.020, 150.0, 30.0)
        self._gen_bearing_temp = ThermalModel(0.012, 250.0, 30.0)
        self._cnv_cabin_temp = ThermalModel(0.010, 300.0, 28.0)
        self._cnv_igct_water_temp = ThermalModel(0.008, 400.0, 25.0)
        self._transformer_temp = ThermalModel(0.005, 500.0, 30.0)
        self._nacelle_temp = ThermalModel(0.030, 800.0, 25.0)
        self._nacelle_cab_temp = ThermalModel(0.025, 200.0, 28.0)
        self._rotor_temp = ThermalModel(0.035, 300.0, 25.0)
        self._hub_cab_temp = ThermalModel(0.030, 150.0, 28.0)

        self._yaw_brake_pressure = 150.0
        self._sim_time = 0.0

        # ── Operator control (set via API, maps to Modbus Coil/Contact) ──
        self.operator_stop = False           # Manual stop command (Coil[2])
        self.operator_start_pending = False  # Start command (Coil[1])
        self.service_mode = False            # Maintenance / inspection mode (WSRV_SrvOn)
        self.local_control = False           # Local/Remote (MBUS Contact[2])
        self.curtailment_kw: Optional[float] = None  # Per-turbine power limit (None=use spec)

        # ── Fault modifiers (set by FaultEngine) ──
        self.fault_modifiers: Dict[str, float] = {}

    def update_spec(self, spec: TurbineSpec):
        """Update turbine specifications at runtime."""
        self.spec = spec
        # Rebuild power curve interpolation
        if spec.power_curve:
            ws = [p[0] for p in spec.power_curve]
            pw = [p[1] for p in spec.power_curve]
            self._power_curve_interp = (np.array(ws), np.array(pw))
        else:
            self._power_curve_interp = None

    def step(self, wind_speed: float, wind_direction: float,
             ambient_temp: float = 25.0, dt: float = 1.0) -> Dict[str, float]:
        s = self.spec
        self._sim_time += dt

        # ── 1. State machine ──
        self._update_state(wind_speed)
        is_producing = self.tur_state == 6

        # ── 2. Rotor aerodynamics ──
        rotor_power_kw, rotor_torque = self._calc_rotor(wind_speed, dt, is_producing)

        # ── 3. Pitch control ──
        self._calc_pitch(wind_speed, is_producing, dt)

        # ── 4. Generator ──
        gen_speed = self.rotor_speed * s.gear_ratio if is_producing else 0.0
        gen_power_kw = rotor_power_kw * s.generator_efficiency if is_producing else 0.0

        # Apply power curve if defined
        if is_producing and self._power_curve_interp is not None:
            ws_arr, pw_arr = self._power_curve_interp
            gen_power_kw = float(np.interp(wind_speed, ws_arr, pw_arr))

        # Clamp to rated power
        gen_power_kw = min(gen_power_kw, s.rated_power_kw)

        # Apply curtailment (限載) — per-turbine overrides spec-level
        effective_limit = s.rated_power_kw
        if self.curtailment_kw is not None:
            effective_limit = min(effective_limit, self.curtailment_kw)
        elif s.curtailment_kw is not None:
            effective_limit = min(effective_limit, s.curtailment_kw)
        gen_power_kw = min(gen_power_kw, effective_limit)

        gen_freq = (gen_speed * s.generator_poles / 2) / 60.0 if is_producing else 0.0
        gen_voltage = s.nominal_voltage if is_producing else 0.0
        gen_current = (gen_power_kw * 1000 / (gen_voltage * math.sqrt(3) * 0.95)
                       if gen_voltage > 0 and gen_power_kw > 0 else 0.0)

        cnv_gn_pwr = gen_power_kw
        cnv_gd_pwr = gen_power_kw * 0.98
        cnv_dc_vtg = 1100.0 if is_producing else 0.0

        # ── 5. Yaw ──
        self._calc_yaw(wind_direction, is_producing, dt)
        yaw_error = self._angle_diff(wind_direction, self.yaw_angle)

        # ── 6. Thermal models ──
        heat_gen = gen_power_kw * (1 - s.generator_efficiency) if is_producing else 0.0
        heat_cnv = gen_power_kw * 0.02 if is_producing else 0.0
        heat_trf = cnv_gd_pwr * 0.01 if is_producing else 0.0
        heat_nac = heat_gen * 0.3 + heat_cnv * 0.5

        gen_sta_t = self._gen_stator_temp.step(heat_gen * 0.6, ambient_temp, dt)
        gen_air_t = self._gen_air_temp.step(heat_gen * 0.3, ambient_temp, dt)
        gen_brg_t = self._gen_bearing_temp.step(heat_gen * 0.1 + self.rotor_speed * 0.01, ambient_temp, dt)
        cnv_cab_t = self._cnv_cabin_temp.step(heat_cnv, ambient_temp, dt)
        cnv_wtr_t = self._cnv_igct_water_temp.step(heat_cnv * 0.7, ambient_temp, dt)
        trf_t = self._transformer_temp.step(heat_trf, ambient_temp, dt)
        nac_t = self._nacelle_temp.step(heat_nac, ambient_temp, dt)
        nac_cab_t = self._nacelle_cab_temp.step(heat_cnv * 0.2, nac_t, dt)
        rot_t = self._rotor_temp.step(0, ambient_temp, dt)
        hub_cab_t = self._hub_cab_temp.step(0, rot_t, dt)

        # ── 7. Vibration ──
        base_vib = 0.3 + self.rotor_speed * 0.05 if is_producing else 0.1
        vib_x = base_vib + self._rng.normal(0, 0.15)
        vib_y = base_vib * 0.8 + self._rng.normal(0, 0.12)

        # ── 8. Hydraulic / cooling ──
        igct_pres1 = 3.5 + self._rng.normal(0, 0.1) if is_producing else 0.0
        igct_pres2 = 3.3 + self._rng.normal(0, 0.1) if is_producing else 0.0
        igct_cond = 1.0 if is_producing else 0.0

        if abs(yaw_error) > 5 and is_producing:
            self._yaw_brake_pressure = max(80, self._yaw_brake_pressure - 2 * dt)
        else:
            self._yaw_brake_pressure = min(180, self._yaw_brake_pressure + 5 * dt)
        yaw_brake_prs = self._yaw_brake_pressure + self._rng.normal(0, 1)

        # ── 9. Status flags ──
        rotor_locked = 1 if self.tur_state in (1, 2, 9) else 0
        brake_active = 1 if self.tur_state in (1, 7, 9) else 0
        locking_pin = 1.0 if rotor_locked else 0.0

        # ── Build output ──
        output: Dict[str, float] = {
            "WTUR_TurSt": float(self.tur_state),
            "WTUR_TotPwrAt": round(cnv_gd_pwr, 2),
            "WGEN_GnPwrMs": round(gen_power_kw, 2),
            "WGEN_GnSpd": round(gen_speed, 2),
            "WGEN_GnVtgMs": round(gen_voltage, 2),
            "WGEN_GnCurMs": round(gen_current, 2),
            "WGEN_GnStaTmp1": round(gen_sta_t, 2),
            "WGEN_GnAirTmp1": round(gen_air_t, 2),
            "WGEN_GnBrgTmp1": round(gen_brg_t, 2),
            "WROT_RotSpd": round(self.rotor_speed, 3),
            "WROT_PtAngValBl1": round(self._pitch_bl[0], 2),
            "WROT_PtAngValBl2": round(self._pitch_bl[1], 2),
            "WROT_PtAngValBl3": round(self._pitch_bl[2], 2),
            "WROT_RotTmp": round(rot_t, 2),
            "WROT_RotCabTmp": round(hub_cab_t, 2),
            "WROT_LckngPnPos": locking_pin,
            "WROT_RotLckd": float(rotor_locked),
            "WROT_SrvcBrkAct": float(brake_active),
            "WCNV_CnvCabinTmp": round(cnv_cab_t, 2),
            "WCNV_CnvDClVtg": round(cnv_dc_vtg, 2),
            "WCNV_CnvGdPwrAt": round(cnv_gd_pwr, 2),
            "WCNV_CnvGnFrq": round(gen_freq, 3),
            "WCNV_CnvGnPwr": round(cnv_gn_pwr, 2),
            "WCNV_IGCTWtrCond": igct_cond,
            "WCNV_IGCTWtrPres1": round(igct_pres1, 2),
            "WCNV_IGCTWtrPres2": round(igct_pres2, 2),
            "WCNV_IGCTWtrTmp": round(cnv_wtr_t, 2),
            "WGDC_TrfCoreTmp": round(trf_t, 2),
            "WMET_WSpeedNac": round(wind_speed, 2),
            "WMET_WDirAbs": round(wind_direction % 360, 2),
            "WMET_TmpOutside": round(ambient_temp, 2),
            "WNAC_NacTmp": round(nac_t, 2),
            "WNAC_NacCabTmp": round(nac_cab_t, 2),
            "WNAC_VibMsNacXDir": round(max(0, vib_x), 3),
            "WNAC_VibMsNacYDir": round(max(0, vib_y), 3),
            "WYAW_YwVn1AlgnAvg5s": round(yaw_error, 2),
            "WYAW_YwBrkHyPrs": round(max(0, yaw_brake_prs), 2),
            "WYAW_CabWup": round(self.cable_windup, 2),
            "WSRV_SrvOn": 1.0 if self.service_mode else 0.0,
            "MBUS_Contact2": 1.0 if self.local_control else 0.0,
        }

        for tag_id, modifier in self.fault_modifiers.items():
            if tag_id in output:
                output[tag_id] += modifier

        return output

    # ─── State machine ─────────────────────────────────────────────────

    def _update_state(self, wind_speed: float):
        s = self.spec
        st = self.tur_state

        # ── Operator commands override (highest priority) ──
        if self.operator_stop or self.service_mode:
            if st == 6:  # Production → Normal Stop
                self.tur_state = 9
            elif st in (4, 5):  # Starting → Normal Stop
                self.tur_state = 9
            elif st == 9 and self.rotor_speed < 0.5:
                self.tur_state = 1  # Stop complete
            # Consume start command if stopped
            if self.operator_start_pending:
                self.operator_start_pending = False
            return

        # ── Operator start command ──
        if self.operator_start_pending and st in (1, 2, 9):
            self.operator_start_pending = False
            if s.cut_in_speed <= wind_speed <= s.cut_out_speed:
                self.tur_state = 4  # → Pre-Production
            return

        # ── Normal state transitions ──
        if st == 1:
            if s.cut_in_speed <= wind_speed <= s.cut_out_speed:
                self.tur_state = 2
        elif st == 2:
            if wind_speed >= s.cut_in_speed + 0.5:
                self.tur_state = 4
        elif st == 3:
            if s.cut_in_speed <= wind_speed <= s.cut_out_speed:
                self.tur_state = 4
        elif st == 4:
            self.tur_state = 5
        elif st == 5:
            if self.rotor_speed > 2.0:
                self.tur_state = 6
        elif st == 6:
            if wind_speed < s.cut_in_speed - 0.3:
                self.tur_state = 7
            elif wind_speed > s.cut_out_speed:
                self.tur_state = 7
        elif st == 7:
            if self.rotor_speed < 0.5:
                self.tur_state = 1
        elif st == 8:
            self.tur_state = 4
        elif st == 9:
            if self.rotor_speed < 0.5:
                self.tur_state = 1

    # ─── Rotor ─────────────────────────────────────────────────────────

    def _calc_rotor(self, wind_speed: float, dt: float, is_producing: bool) -> tuple:
        s = self.spec
        swept_area = math.pi * (s.rotor_diameter / 2) ** 2

        if is_producing and wind_speed > 0:
            tsr = ((self.rotor_speed * math.pi * s.rotor_diameter / 60) / wind_speed
                   if wind_speed > 0 else 0)
            cp = self._calc_cp(tsr)
            wind_power = 0.5 * s.air_density * swept_area * wind_speed ** 3
            rotor_power = wind_power * cp / 1000.0

            target_rpm = self._optimal_rpm(wind_speed)
            self.rotor_speed += (target_rpm - self.rotor_speed) * 0.1 * dt

            rotor_torque = (rotor_power * 1000 / (self.rotor_speed * 2 * math.pi / 60)
                            if self.rotor_speed > 0 else 0)
        else:
            self.rotor_speed = max(0, self.rotor_speed - 0.3 * dt)
            rotor_power = 0.0
            rotor_torque = 0.0
            if self.tur_state in (4, 5) and wind_speed >= s.cut_in_speed:
                target_rpm = self._optimal_rpm(wind_speed)
                self.rotor_speed += target_rpm * 0.05 * dt

        return rotor_power, rotor_torque

    def _calc_cp(self, tsr: float) -> float:
        s = self.spec
        if tsr <= 0 or tsr > 15:
            return 0.0
        return s.cp_max * math.exp(-0.5 * ((tsr - s.optimal_tsr) / 2.5) ** 2)

    def _optimal_rpm(self, wind_speed: float) -> float:
        s = self.spec
        rpm = (s.optimal_tsr * wind_speed * 60) / (math.pi * s.rotor_diameter)
        return min(rpm, s.max_rotor_rpm)

    # ─── Pitch ─────────────────────────────────────────────────────────

    def _calc_pitch(self, wind_speed: float, is_producing: bool, dt: float):
        s = self.spec
        max_rate = 8.0

        if not is_producing:
            target = 90.0
        elif wind_speed < s.rated_speed:
            target = 0.0
        else:
            target = min(30.0, (wind_speed - s.rated_speed) * 2.3)

        # Extra pitch if curtailed (per-turbine or spec-level)
        active_curtail = self.curtailment_kw if self.curtailment_kw is not None else s.curtailment_kw
        if is_producing and active_curtail is not None and active_curtail < s.rated_power_kw:
            curtail_ratio = active_curtail / s.rated_power_kw
            target = max(target, (1 - curtail_ratio) * 15.0)

        diff = target - self.pitch_angle
        change = max(-max_rate * dt, min(max_rate * dt, diff))
        self.pitch_angle += change

        for i in range(3):
            self._pitch_bl[i] = self.pitch_angle + self._rng.normal(0, 0.15)

    # ─── Yaw ───────────────────────────────────────────────────────────

    def _calc_yaw(self, wind_direction: float, is_producing: bool, dt: float):
        if not is_producing:
            return
        error = self._angle_diff(wind_direction, self.yaw_angle)
        if abs(error) > 5.0:
            yaw_rate = 0.3
            self.yaw_angle += math.copysign(yaw_rate, error) * dt
            self.yaw_angle %= 360
            self.cable_windup += math.copysign(yaw_rate * dt / 360, error)
            self.cable_windup = max(-4.0, min(4.0, self.cable_windup))

    @staticmethod
    def _angle_diff(target: float, current: float) -> float:
        diff = (target - current) % 360
        if diff > 180:
            diff -= 360
        return diff

    # ─── External control ──────────────────────────────────────────────

    def force_state(self, state: int):
        if 1 <= state <= 9:
            self.tur_state = state

    def cmd_stop(self):
        """Operator manual stop."""
        self.operator_stop = True
        self.operator_start_pending = False

    def cmd_start(self):
        """Operator manual start (clears stop/service mode)."""
        self.operator_stop = False
        self.service_mode = False
        self.operator_start_pending = True

    def cmd_reset(self):
        """Operator reset (clear faults, return to standby)."""
        self.operator_stop = False
        self.service_mode = False
        self.operator_start_pending = False
        self.fault_modifiers.clear()
        if self.tur_state in (7, 9):
            self.tur_state = 1  # Will auto-transition to standby

    def cmd_service(self, on: bool):
        """Enter/exit maintenance service mode."""
        self.service_mode = on
        if on:
            self.operator_stop = False

    def cmd_curtail(self, power_kw: Optional[float]):
        """Set per-turbine power curtailment. None = remove curtailment."""
        self.curtailment_kw = power_kw

    def get_control_status(self) -> dict:
        """Return current operator control status."""
        return {
            "operator_stop": self.operator_stop,
            "service_mode": self.service_mode,
            "local_control": self.local_control,
            "curtailment_kw": self.curtailment_kw,
            "tur_state": self.tur_state,
        }

    def reset(self):
        self.tur_state = 1
        self.rotor_speed = 0.0
        self.pitch_angle = 90.0
        self._pitch_bl = [90.0, 90.0, 90.0]
        self.operator_stop = False
        self.service_mode = False
        self.operator_start_pending = False
        self.curtailment_kw = None
        self.fault_modifiers.clear()

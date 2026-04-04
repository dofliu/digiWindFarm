"""
Independent physics-based wind turbine model.

Composes independent sub-models (each can be replaced separately):
  - PowerCurveModel:  Region 2/3 power output
  - RotorSpeedModel:  RPM tracking with inertia
  - ThermalSystem:    10-point temperature model
  - VibrationModel:   RPM + turbulence + load driven
  - YawModel:         Dead band + delay + cable management

No dependency on FastAPI, frontend, or storage — only numpy.
"""

import math
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from simulator.physics.power_curve import PowerCurveModel, RotorSpeedModel
from simulator.physics.thermal_model import ThermalSystem, ThermalSystemConfig
from simulator.physics.vibration_model import VibrationModel
from simulator.physics.yaw_model import YawModel


@dataclass
class TurbineSpec:
    """Configurable wind turbine specifications."""

    rated_power_kw: float = 5000.0
    rotor_diameter: float = 126.0
    hub_height: float = 90.0
    cut_in_speed: float = 3.0
    rated_speed: float = 12.0
    cut_out_speed: float = 25.0

    gear_ratio: float = 100.0
    generator_efficiency: float = 0.95
    generator_poles: int = 4
    nominal_voltage: float = 690.0
    air_density: float = 1.225

    max_rotor_rpm: float = 15.0
    optimal_tsr: float = 7.5
    cp_max: float = 0.48

    curtailment_kw: Optional[float] = None
    power_curve: Optional[List[Tuple[float, float]]] = None

    def to_dict(self) -> dict:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}

    @classmethod
    def from_dict(cls, d: dict) -> "TurbineSpec":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


TURBINE_PRESETS: Dict[str, TurbineSpec] = {
    "z72_5mw": TurbineSpec(),
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


class TurbinePhysicsModel:
    """
    Complete wind turbine physics model — composes independent sub-models.

    Each sub-model can be replaced by assigning a new instance:
        model.thermal = MyCustomThermalSystem()
        model.vibration = MyCustomVibrationModel()
    """

    def __init__(self, spec: Optional[TurbineSpec] = None, seed: Optional[int] = None):
        self.spec = spec or TurbineSpec()
        self._rng = np.random.RandomState(seed)
        _seed = seed or 0

        # ── Composable sub-models (each independently replaceable) ──
        self.power_curve = PowerCurveModel(
            power_curve=self.spec.power_curve,
            rated_power_kw=self.spec.rated_power_kw,
            cut_in=self.spec.cut_in_speed,
            rated_speed=self.spec.rated_speed,
            cut_out=self.spec.cut_out_speed,
        )
        self.rotor_model = RotorSpeedModel(
            rotor_diameter=self.spec.rotor_diameter,
            optimal_tsr=self.spec.optimal_tsr,
            max_rpm=self.spec.max_rotor_rpm,
            rated_speed=self.spec.rated_speed,
            gear_ratio=self.spec.gear_ratio,
        )
        self.thermal = ThermalSystem()
        self.vibration = VibrationModel(seed=_seed)
        self.yaw = YawModel()

        # ── State ──
        self.tur_state = 1
        self.rotor_speed = 0.0
        self.pitch_angle = 90.0
        self._pitch_bl = [90.0, 90.0, 90.0]
        self._sim_time = 0.0

        # ── Operator control ──
        self.operator_stop = False
        self.operator_start_pending = False
        self.service_mode = False
        self.local_control = False
        self.curtailment_kw: Optional[float] = None

        # ── Fault modifiers ──
        self.fault_modifiers: Dict[str, float] = {}

    def update_spec(self, spec: TurbineSpec):
        """Update turbine specifications and rebuild sub-models."""
        self.spec = spec
        self.power_curve = PowerCurveModel(
            power_curve=spec.power_curve,
            rated_power_kw=spec.rated_power_kw,
            cut_in=spec.cut_in_speed,
            rated_speed=spec.rated_speed,
            cut_out=spec.cut_out_speed,
        )
        self.rotor_model = RotorSpeedModel(
            rotor_diameter=spec.rotor_diameter,
            optimal_tsr=spec.optimal_tsr,
            max_rpm=spec.max_rotor_rpm,
            rated_speed=spec.rated_speed,
            gear_ratio=spec.gear_ratio,
        )

    def step(self, wind_speed: float, wind_direction: float,
             ambient_temp: float = 25.0, dt: float = 1.0) -> Dict[str, float]:
        s = self.spec
        self._sim_time += dt

        # ── 1. State machine ──
        self._update_state(wind_speed)
        is_producing = self.tur_state == 6
        is_starting = self.tur_state in (4, 5)

        # ── 2. Rotor speed (with realistic inertia) ──
        self.rotor_speed = self.rotor_model.step(
            self.rotor_speed, wind_speed, s.cut_in_speed,
            is_producing, is_starting, dt
        )

        # ── 3. Power (from realistic power curve) ──
        if is_producing:
            gen_power_kw = self.power_curve.get_power(wind_speed)
        else:
            gen_power_kw = 0.0

        # Apply curtailment
        effective_limit = s.rated_power_kw
        if self.curtailment_kw is not None:
            effective_limit = min(effective_limit, self.curtailment_kw)
        elif s.curtailment_kw is not None:
            effective_limit = min(effective_limit, s.curtailment_kw)
        gen_power_kw = min(gen_power_kw, effective_limit)

        # ── 4. Pitch control ──
        self._calc_pitch(wind_speed, gen_power_kw, is_producing, dt)

        # ── 5. Electrical ──
        gen_speed = self.rotor_speed * s.gear_ratio if is_producing else 0.0
        gen_freq = (gen_speed * s.generator_poles / 2) / 60.0 if is_producing else 0.0
        gen_voltage = s.nominal_voltage if is_producing else 0.0
        gen_current = (gen_power_kw * 1000 / (gen_voltage * math.sqrt(3) * 0.95)
                       if gen_voltage > 0 and gen_power_kw > 0 else 0.0)

        cnv_gn_pwr = gen_power_kw
        cnv_gd_pwr = gen_power_kw * 0.98
        cnv_dc_vtg = 1100.0 if is_producing else 0.0

        # ── 6. Yaw (with dead band, delay, cable management) ──
        yaw_out = self.yaw.step(wind_direction, is_producing, dt)

        # ── 7. Thermal (calibrated steady-state temperatures) ──
        temps = self.thermal.step(
            gen_power_kw, cnv_gd_pwr, self.rotor_speed,
            ambient_temp, s.generator_efficiency, dt
        )

        # ── 8. Vibration (RPM + turbulence + load) ──
        vib_x, vib_y = self.vibration.step(
            self.rotor_speed, wind_speed, gen_power_kw,
            turbulence=0.1, dt=dt
        )

        # ── 9. Hydraulic / cooling ──
        igct_pres1 = 3.5 + self._rng.normal(0, 0.08) if is_producing else 0.0
        igct_pres2 = 3.3 + self._rng.normal(0, 0.08) if is_producing else 0.0
        igct_cond = 1.0 if is_producing else 0.0

        # ── 10. Status flags ──
        rotor_locked = 1 if self.tur_state in (1, 2, 9) else 0
        brake_active = 1 if self.tur_state in (1, 7, 9) else 0

        # ── Build output ──
        output: Dict[str, float] = {
            "WTUR_TurSt": float(self.tur_state),
            "WTUR_TotPwrAt": round(cnv_gd_pwr, 2),
            "WGEN_GnPwrMs": round(gen_power_kw, 2),
            "WGEN_GnSpd": round(gen_speed, 2),
            "WGEN_GnVtgMs": round(gen_voltage, 2),
            "WGEN_GnCurMs": round(gen_current, 2),
            "WGEN_GnStaTmp1": temps["gen_stator"],
            "WGEN_GnAirTmp1": temps["gen_air"],
            "WGEN_GnBrgTmp1": temps["gen_bearing"],
            "WROT_RotSpd": round(self.rotor_speed, 3),
            "WROT_PtAngValBl1": round(self._pitch_bl[0], 2),
            "WROT_PtAngValBl2": round(self._pitch_bl[1], 2),
            "WROT_PtAngValBl3": round(self._pitch_bl[2], 2),
            "WROT_RotTmp": temps["rotor"],
            "WROT_RotCabTmp": temps["hub_cabinet"],
            "WROT_LckngPnPos": 1.0 if rotor_locked else 0.0,
            "WROT_RotLckd": float(rotor_locked),
            "WROT_SrvcBrkAct": float(brake_active),
            "WCNV_CnvCabinTmp": temps["cnv_cabinet"],
            "WCNV_CnvDClVtg": round(cnv_dc_vtg, 2),
            "WCNV_CnvGdPwrAt": round(cnv_gd_pwr, 2),
            "WCNV_CnvGnFrq": round(gen_freq, 3),
            "WCNV_CnvGnPwr": round(cnv_gn_pwr, 2),
            "WCNV_IGCTWtrCond": igct_cond,
            "WCNV_IGCTWtrPres1": round(igct_pres1, 2),
            "WCNV_IGCTWtrPres2": round(igct_pres2, 2),
            "WCNV_IGCTWtrTmp": temps["cnv_water"],
            "WGDC_TrfCoreTmp": temps["transformer"],
            "WMET_WSpeedNac": round(wind_speed, 2),
            "WMET_WDirAbs": round(wind_direction % 360, 2),
            "WMET_TmpOutside": round(ambient_temp, 2),
            "WNAC_NacTmp": temps["nacelle"],
            "WNAC_NacCabTmp": temps["nac_cabinet"],
            "WNAC_VibMsNacXDir": round(vib_x, 3),
            "WNAC_VibMsNacYDir": round(vib_y, 3),
            "WYAW_YwVn1AlgnAvg5s": round(yaw_out["yaw_error"], 2),
            "WYAW_YwBrkHyPrs": round(max(0, yaw_out["brake_pressure"]), 2),
            "WYAW_CabWup": round(yaw_out["cable_windup"], 2),
            "WSRV_SrvOn": 1.0 if self.service_mode else 0.0,
            "MBUS_Contact2": 1.0 if self.local_control else 0.0,
        }

        # Apply fault modifiers
        for tag_id, modifier in self.fault_modifiers.items():
            if tag_id in output:
                output[tag_id] += modifier

        return output

    # ─── State machine ─────────────────────────────────────────────────

    def _update_state(self, wind_speed: float):
        s = self.spec
        st = self.tur_state

        if self.operator_stop or self.service_mode:
            if st == 6:
                self.tur_state = 9
            elif st in (4, 5):
                self.tur_state = 9
            elif st == 9 and self.rotor_speed < 0.5:
                self.tur_state = 1
            if self.operator_start_pending:
                self.operator_start_pending = False
            return

        if self.operator_start_pending and st in (1, 2, 9):
            self.operator_start_pending = False
            if s.cut_in_speed <= wind_speed <= s.cut_out_speed:
                self.tur_state = 4
            return

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

    # ─── Pitch ─────────────────────────────────────────────────────────

    def _calc_pitch(self, wind_speed: float, power_kw: float,
                    is_producing: bool, dt: float):
        s = self.spec
        max_rate = 8.0  # °/s

        if not is_producing:
            target = 90.0  # feathered
        elif wind_speed < s.rated_speed:
            target = 0.0  # Region 2: fine pitch
        else:
            # Region 3: pitch to limit power to rated
            # More pitch = less power captured
            excess_wind = wind_speed - s.rated_speed
            target = min(30.0, excess_wind * 2.0 + excess_wind ** 2 * 0.1)

        # Curtailment pitch
        active_curtail = self.curtailment_kw if self.curtailment_kw is not None else s.curtailment_kw
        if is_producing and active_curtail is not None and active_curtail < s.rated_power_kw:
            curtail_ratio = active_curtail / s.rated_power_kw
            target = max(target, (1 - curtail_ratio) * 15.0)

        diff = target - self.pitch_angle
        change = max(-max_rate * dt, min(max_rate * dt, diff))
        self.pitch_angle += change

        for i in range(3):
            self._pitch_bl[i] = self.pitch_angle + self._rng.normal(0, 0.15)

    # ─── External control ──────────────────────────────────────────────

    def force_state(self, state: int):
        if 1 <= state <= 9:
            self.tur_state = state

    def cmd_stop(self):
        self.operator_stop = True
        self.operator_start_pending = False

    def cmd_start(self):
        self.operator_stop = False
        self.service_mode = False
        self.operator_start_pending = True

    def cmd_reset(self):
        self.operator_stop = False
        self.service_mode = False
        self.operator_start_pending = False
        self.fault_modifiers.clear()
        if self.tur_state in (7, 9):
            self.tur_state = 1

    def cmd_service(self, on: bool):
        self.service_mode = on
        if on:
            self.operator_stop = False

    def cmd_curtail(self, power_kw: Optional[float]):
        self.curtailment_kw = power_kw

    def get_control_status(self) -> dict:
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

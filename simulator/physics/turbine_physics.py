"""
Independent physics-based wind turbine model.

Composes independent sub-models (each can be replaced separately):
  - PowerCurveModel:  Region 2/3 power output
  - RotorSpeedModel:  RPM tracking with inertia
  - ThermalSystem:    10-point temperature model
  - VibrationModel:   RPM + turbulence + load driven
  - YawModel:         Dead band + delay + cable management

No dependency on FastAPI, frontend, or storage; only numpy.
"""

import math
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from simulator.physics.power_curve import PowerCurveModel, RotorSpeedModel
from simulator.physics.thermal_model import ThermalSystem
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
    Complete wind turbine physics model with staged startup and shutdown dynamics.

    TurState mapping:
      1: Shutdown
      2: Standby
      3: Wait Restart
      4: Pre-Production
      5: Start Production / Synchronization
      6: Production
      7: Emergency Stop
      8: Restart
      9: Normal Stop
    """

    def __init__(self, spec: Optional[TurbineSpec] = None, seed: Optional[int] = None):
        self.spec = spec or TurbineSpec()
        self._rng = np.random.RandomState(seed)
        _seed = seed or 0

        # Per-turbine individuality: small but persistent differences in efficiency,
        # cooling, sensor alignment, and control response.
        self._individuality = {
            "power_scale": 1.0 + self._rng.uniform(-0.035, 0.03),
            "cut_in_offset": self._rng.uniform(-0.18, 0.22),
            "yaw_sensor_bias": self._rng.uniform(-2.5, 2.5),
            "wind_sensor_scale": 1.0 + self._rng.uniform(-0.025, 0.025),
            "thermal_scale": 1.0 + self._rng.uniform(-0.08, 0.10),
            "cooling_scale": 1.0 + self._rng.uniform(-0.12, 0.10),
            "bearing_friction_scale": 1.0 + self._rng.uniform(-0.10, 0.14),
            "converter_loss_scale": 1.0 + self._rng.uniform(-0.06, 0.08),
            "grid_voltage_bias": self._rng.uniform(-6.0, 6.0),
            "pitch_response_scale": 1.0 + self._rng.uniform(-0.12, 0.12),
            "start_delay_offset": self._rng.uniform(-1.5, 2.0),
            "restart_delay_offset": self._rng.uniform(-3.0, 4.0),
            "drivetrain_stiffness_scale": 1.0 + self._rng.uniform(-0.18, 0.16),
            "shaft_damping_scale": 1.0 + self._rng.uniform(-0.15, 0.18),
            "normal_brake_scale": 1.0 + self._rng.uniform(-0.10, 0.12),
            "emergency_brake_scale": 1.0 + self._rng.uniform(-0.08, 0.10),
            "grid_freq_bias": self._rng.uniform(-0.04, 0.04),
            "grid_voltage_local_bias": self._rng.uniform(-8.0, 8.0),
            "grid_derate_sensitivity": 1.0 + self._rng.uniform(-0.18, 0.24),
            "grid_trip_margin_hz": self._rng.uniform(-0.10, 0.12),
            "grid_trip_margin_v": self._rng.uniform(-12.0, 14.0),
            "grid_ride_through_scale": 1.0 + self._rng.uniform(-0.22, 0.25),
            "grid_reconnect_delay": self._rng.uniform(-5.0, 8.0),
        }

        self.power_curve = PowerCurveModel(
            power_curve=self.spec.power_curve,
            rated_power_kw=self.spec.rated_power_kw,
            cut_in=self.spec.cut_in_speed + self._individuality["cut_in_offset"],
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

        self.tur_state = 1
        self.rotor_speed = 0.0
        self.pitch_angle = 90.0
        self._pitch_bl = [90.0, 90.0, 90.0]
        self._sim_time = 0.0
        self._generated_power_kw = 0.0
        self._generator_speed = 0.0
        self._grid_voltage = 0.0
        self._grid_frequency = 0.0
        self._sync_progress = 0.0
        self._drivetrain_twist = 0.0
        self._state_timer = 0.0
        self._wind_ready_timer = 0.0
        self._restart_wait_timer = 0.0
        self._restart_block_timer = 0.0
        self._stop_requested = False
        self._stop_mode = "normal"
        self._shutdown_cause = "idle"
        self._grid_phase = self._rng.uniform(0.0, math.tau)
        self._grid_local_phase = self._rng.uniform(0.0, math.tau)
        self._grid_voltage_ref = self.spec.nominal_voltage + self._individuality["grid_voltage_bias"]
        self._grid_frequency_ref = 50.0
        self._grid_normal_trip_accum = 0.0
        self._grid_emergency_trip_accum = 0.0
        self._pitch_offset_bl = [self._rng.normal(0, 0.12) for _ in range(3)]
        self._pitch_stiction = [0.0, 0.0, 0.0]
        self._sensor_bias: Dict[str, float] = {}
        self._sensor_stuck_until: Dict[str, float] = {}
        self._sensor_last: Dict[str, float] = {}

        self.operator_stop = False
        self.operator_start_pending = False
        self.service_mode = False
        self.local_control = False
        self.curtailment_kw: Optional[float] = None

        self.fault_modifiers: Dict[str, float] = {}
        self.active_faults: List[Dict] = []

    def update_spec(self, spec: TurbineSpec):
        """Update turbine specifications and rebuild sub-models."""
        self.spec = spec
        self.power_curve = PowerCurveModel(
            power_curve=spec.power_curve,
            rated_power_kw=spec.rated_power_kw,
            cut_in=spec.cut_in_speed + self._individuality["cut_in_offset"],
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
             ambient_temp: float = 25.0, dt: float = 1.0,
             grid_frequency_ref: Optional[float] = None,
             grid_voltage_ref: Optional[float] = None) -> Dict[str, float]:
        s = self.spec
        self._sim_time += dt
        self._update_grid_reference(dt, grid_frequency_ref, grid_voltage_ref)
        fault_physics = self._get_fault_physics()
        effective_wind_speed = max(
            0.0,
            wind_speed * fault_physics["wind_scale"] * self._individuality["wind_sensor_scale"]
        )
        grid_derate = self._get_grid_derate()
        grid_trip = self._check_grid_trip()

        self._update_state(effective_wind_speed, dt)
        is_producing = self.tur_state == 6
        is_starting = self.tur_state in (4, 5)
        is_normal_stop = self.tur_state == 9
        is_emergency_stop = self.tur_state == 7

        if grid_trip == "emergency":
            self.cmd_emergency_stop(cause="grid_trip")
            is_producing = self.tur_state == 6
            is_starting = self.tur_state in (4, 5)
            is_normal_stop = self.tur_state == 9
            is_emergency_stop = self.tur_state == 7
        elif grid_trip == "normal":
            self._request_stop("normal", "grid_protection")

        aero_rotor_speed = self.rotor_model.step(
            self.rotor_speed, effective_wind_speed, s.cut_in_speed,
            is_producing, is_starting, dt
        )
        aero_rotor_speed += fault_physics["rotor_speed_bias"] * dt
        (
            self.rotor_speed,
            gen_speed,
            drivetrain_loss_kw,
            brake_heat_kw,
            torsion_vib,
        ) = self._apply_drivetrain_dynamics(
            aero_rotor_speed=aero_rotor_speed,
            effective_wind_speed=effective_wind_speed,
            dt=dt,
            is_producing=is_producing,
            is_starting=is_starting,
            is_normal_stop=is_normal_stop,
            is_emergency_stop=is_emergency_stop,
        )

        aerodynamic_power_kw = (
            self.power_curve.get_power(effective_wind_speed)
            * fault_physics["power_scale"]
            * self._individuality["power_scale"]
            * grid_derate
        )
        effective_limit = s.rated_power_kw
        if self.curtailment_kw is not None:
            effective_limit = min(effective_limit, self.curtailment_kw)
        elif s.curtailment_kw is not None:
            effective_limit = min(effective_limit, s.curtailment_kw)
        aerodynamic_power_kw = min(aerodynamic_power_kw, effective_limit)

        if is_producing:
            target_power_kw = aerodynamic_power_kw
        elif is_starting:
            rotor_gate = min(1.0, self.rotor_speed / max(1.0, self.rotor_model.rated_rpm * 0.9))
            target_power_kw = aerodynamic_power_kw * self._sync_progress * rotor_gate * 0.2
        else:
            target_power_kw = 0.0

        ramp_tau = 4.0 if is_producing else 2.0
        if is_normal_stop:
            ramp_tau = 2.0
        elif is_emergency_stop:
            ramp_tau = 0.35
        alpha = 1.0 - math.exp(-dt / ramp_tau)
        self._generated_power_kw += (target_power_kw - self._generated_power_kw) * alpha
        gen_power_kw = max(0.0, self._generated_power_kw)

        self._calc_pitch(effective_wind_speed, is_producing, dt)
        self._pitch_bl[0] += fault_physics["blade1_pitch_bias"]

        mechanical_freq = (gen_speed * s.generator_poles / 2) / 60.0 if (is_producing or is_starting) else 0.0
        target_freq = self._grid_frequency_ref if is_producing else mechanical_freq if is_starting else 0.0
        target_voltage = self._grid_voltage_ref if (is_producing or is_starting) else 0.0
        elec_alpha = 1.0 - math.exp(-dt / (1.0 if is_producing else 0.75))
        self._grid_frequency += (target_freq - self._grid_frequency) * elec_alpha
        self._grid_voltage += (target_voltage - self._grid_voltage) * elec_alpha
        if is_normal_stop:
            self._grid_frequency = max(0.0, self._grid_frequency - 6.0 * dt)
            self._grid_voltage = max(0.0, self._grid_voltage - 95.0 * dt)
        elif is_emergency_stop:
            self._grid_frequency = max(0.0, self._grid_frequency - 30.0 * dt)
            self._grid_voltage = max(0.0, self._grid_voltage - 400.0 * dt)

        gen_freq = self._grid_frequency if (is_producing or is_starting) else 0.0
        gen_voltage = self._grid_voltage if (is_producing or is_starting) else 0.0
        gen_power_kw = max(0.0, gen_power_kw - drivetrain_loss_kw)
        gen_current = (
            gen_power_kw * 1000 / (gen_voltage * math.sqrt(3) * 0.95)
            if gen_voltage > 0 and gen_power_kw > 0 else 0.0
        )

        cnv_gn_pwr = gen_power_kw
        converter_eff = (0.985 if is_producing else 0.95) - (self._individuality["converter_loss_scale"] - 1.0) * 0.02
        converter_eff = max(0.90, min(0.992, converter_eff))
        cnv_gd_pwr = gen_power_kw * converter_eff
        if is_producing:
            cnv_dc_vtg = 1100.0
        elif is_starting:
            cnv_dc_vtg = 900.0 + self._sync_progress * 200.0
        else:
            cnv_dc_vtg = 0.0

        yaw_out = self.yaw.step(wind_direction, is_producing, dt)
        yaw_out["yaw_error"] += fault_physics["yaw_error_bias"] + self._individuality["yaw_sensor_bias"]
        yaw_out["brake_pressure"] += fault_physics["yaw_brake_bias"]

        temps = self.thermal.step(
            gen_power_kw, cnv_gd_pwr, self.rotor_speed,
            ambient_temp, s.generator_efficiency, dt,
            wind_speed=effective_wind_speed,
            tur_state=self.tur_state,
            sync_progress=self._sync_progress,
            extra_heat={
                key: value * self._individuality["thermal_scale"]
                for key, value in fault_physics["extra_heat"].items()
            } | {
                "bearing": drivetrain_loss_kw * 0.85,
                "rotor": brake_heat_kw * 0.30,
                "hub": brake_heat_kw * 0.24,
                "nacelle": brake_heat_kw * 0.10,
                "converter": max(0.0, cnv_gn_pwr - cnv_gd_pwr),
            },
            cooling_bias={
                key: value * self._individuality["cooling_scale"]
                for key, value in fault_physics["cooling_bias"].items()
            },
        )

        vib_x, vib_y = self.vibration.step(
            self.rotor_speed, effective_wind_speed, gen_power_kw,
            turbulence=0.1, dt=dt
        )
        vib_x += torsion_vib * 0.85
        vib_y += torsion_vib * 0.55
        vib_x += fault_physics["vibration_x"]
        vib_y += fault_physics["vibration_y"]
        if is_normal_stop:
            vib_x += 0.35 + abs(self._rng.normal(0, 0.12))
            vib_y += 0.30 + abs(self._rng.normal(0, 0.12))
        elif is_emergency_stop:
            vib_x += 1.30 + abs(self._rng.normal(0, 0.45))
            vib_y += 1.10 + abs(self._rng.normal(0, 0.40))

        if is_producing:
            igct_pres1 = 3.5 + self._rng.normal(0, 0.08)
            igct_pres2 = 3.3 + self._rng.normal(0, 0.08)
            igct_cond = 1.0
        elif is_starting:
            igct_pres1 = 2.4 + self._sync_progress * 0.8 + self._rng.normal(0, 0.05)
            igct_pres2 = 2.2 + self._sync_progress * 0.7 + self._rng.normal(0, 0.05)
            igct_cond = 0.65 + self._sync_progress * 0.35
        else:
            igct_pres1 = 0.4 if is_normal_stop else 0.1 if is_emergency_stop else 0.0
            igct_pres2 = 0.3 if is_normal_stop else 0.05 if is_emergency_stop else 0.0
            igct_cond = 0.2 if is_normal_stop else 0.0

        rotor_locked = 1 if self.tur_state in (1, 2, 3) else 0
        brake_active = 1 if self.tur_state in (1, 7, 9) else 0

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
            "WCNV_IGCTWtrCond": round(igct_cond, 3),
            "WCNV_IGCTWtrPres1": round(igct_pres1, 2),
            "WCNV_IGCTWtrPres2": round(igct_pres2, 2),
            "WCNV_IGCTWtrTmp": temps["cnv_water"],
            "WGDC_TrfCoreTmp": temps["transformer"],
            "WMET_WSpeedNac": round(effective_wind_speed, 2),
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

        for tag_id, modifier in self.fault_modifiers.items():
            if tag_id in output:
                output[tag_id] += modifier

        return self._apply_sensor_model(output)

    def _update_state(self, wind_speed: float, dt: float):
        s = self.spec
        st = self.tur_state
        wind_ok = s.cut_in_speed <= wind_speed <= s.cut_out_speed
        strong_wind = wind_speed >= s.cut_in_speed + 0.6
        sync_ok = (
            abs(self._grid_frequency_ref - ((self.rotor_speed * s.gear_ratio * s.generator_poles / 2) / 60.0 if self.rotor_speed > 0 else 0.0)) < 0.25
            and abs(self._grid_voltage_ref - self._grid_voltage) < 25.0
        )

        self._state_timer += dt
        self._restart_block_timer = max(0.0, self._restart_block_timer - dt)
        if wind_ok and strong_wind:
            self._wind_ready_timer += dt
        else:
            self._wind_ready_timer = 0.0

        if self.operator_stop or self.service_mode:
            self._request_stop("normal", "operator")
        if wind_speed > s.cut_out_speed + 0.5:
            self._request_stop("emergency", "cut_out")

        if self._stop_requested and st not in (7, 9):
            self._enter_state(9 if self._stop_mode == "normal" else 7)
            st = self.tur_state

        if self.operator_start_pending and st in (1, 2, 3) and wind_ok and self._restart_block_timer <= 0.0:
            self.operator_start_pending = False
            self._enter_state(8 if st == 3 else 4)
            st = self.tur_state

        if st == 1:
            self._sync_progress = 0.0
            if wind_ok:
                self._enter_state(2)
        elif st == 2:
            if not wind_ok:
                self._enter_state(1)
            elif not self.operator_stop and self._wind_ready_timer >= 10.0 + self._individuality["start_delay_offset"] and self._restart_block_timer <= 0.0:
                self._enter_state(4)
        elif st == 3:
            self._restart_wait_timer += dt
            restart_delay = (
                8.0
                + self._individuality["restart_delay_offset"]
                + max(0.0, self._individuality["grid_reconnect_delay"])
            )
            if self._restart_wait_timer >= restart_delay and wind_ok and not self.operator_stop and not self.service_mode and self._restart_block_timer <= 0.0:
                self._enter_state(2)
        elif st == 4:
            if not wind_ok:
                self._request_stop("normal", "low_wind")
            elif self._state_timer >= 3.0:
                self._enter_state(5)
        elif st == 5:
            self._sync_progress = min(1.0, self._state_timer / 7.0)
            if not wind_ok:
                self._request_stop("normal", "low_wind")
            elif self.rotor_speed >= max(2.5, self.rotor_model.rated_rpm * 0.35) and self._state_timer >= 7.0 and sync_ok:
                self._enter_state(6)
        elif st == 6:
            self._sync_progress = 1.0
            if wind_speed < s.cut_in_speed - 0.3:
                self._request_stop("normal", "below_cut_in")
            elif wind_speed > s.cut_out_speed:
                self._request_stop("emergency", "cut_out")
        elif st == 7:
            if self.rotor_speed < 0.3 and self._state_timer >= 4.0:
                self._stop_requested = False
                self._enter_state(3)
        elif st == 8:
            if wind_ok and self._restart_block_timer <= 0.0:
                self._enter_state(4)
            else:
                self._enter_state(3)
        elif st == 9:
            if self.rotor_speed < 0.3 and self._state_timer >= 12.0:
                self._stop_requested = False
                self._enter_state(1)

    def _calc_pitch(self, wind_speed: float, is_producing: bool, dt: float):
        s = self.spec
        max_rate = 8.0 * self._individuality["pitch_response_scale"]

        if self.tur_state == 7:
            target = 88.0
            max_rate = 18.0
        elif self.tur_state == 9:
            target = 90.0
            max_rate = 10.0
        elif self.tur_state == 4:
            target = 72.0
            max_rate = 6.0
        elif self.tur_state == 5:
            target = max(2.0, 65.0 - self._sync_progress * 60.0)
            max_rate = 7.5
        elif not is_producing:
            target = 90.0
        elif wind_speed < s.rated_speed:
            target = 0.0
        else:
            excess_wind = wind_speed - s.rated_speed
            target = min(30.0, excess_wind * 2.0 + excess_wind ** 2 * 0.1)

        active_curtail = self.curtailment_kw if self.curtailment_kw is not None else s.curtailment_kw
        if is_producing and active_curtail is not None and active_curtail < s.rated_power_kw:
            curtail_ratio = active_curtail / s.rated_power_kw
            target = max(target, (1 - curtail_ratio) * 15.0)

        diff = target - self.pitch_angle
        if abs(diff) < 0.25:
            diff = 0.0
        command = max(-max_rate * dt, min(max_rate * dt, diff))
        self.pitch_angle += command

        for i in range(3):
            blade_target = self.pitch_angle + self._pitch_offset_bl[i]
            blade_diff = blade_target - self._pitch_bl[i]
            if abs(blade_diff) < 0.18:
                blade_diff = 0.0
            blade_rate = max_rate * (0.92 + i * 0.03)
            blade_change = max(-blade_rate * dt, min(blade_rate * dt, blade_diff))
            self._pitch_bl[i] += blade_change
            spread = 0.18 if self.tur_state in (5, 7) else 0.08
            self._pitch_bl[i] += self._rng.normal(0, spread)

    def force_state(self, state: int):
        if 1 <= state <= 9:
            self._enter_state(state)

    def cmd_stop(self):
        self.operator_stop = True
        self.operator_start_pending = False
        self._request_stop("normal", "operator")

    def cmd_start(self):
        self.operator_stop = False
        self.service_mode = False
        self.operator_start_pending = True

    def cmd_reset(self):
        self.operator_stop = False
        self.service_mode = False
        self.operator_start_pending = False
        self._stop_requested = False
        self._stop_mode = "normal"
        self._shutdown_cause = "reset"
        self._restart_block_timer = 3.0
        self._generated_power_kw = 0.0
        self._generator_speed = 0.0
        self._grid_voltage = 0.0
        self._grid_frequency = 0.0
        self._sync_progress = 0.0
        self._drivetrain_twist = 0.0
        self._grid_normal_trip_accum = 0.0
        self._grid_emergency_trip_accum = 0.0
        self.fault_modifiers.clear()
        if self.tur_state in (3, 7, 8, 9):
            self._enter_state(1)

    def cmd_service(self, on: bool):
        self.service_mode = on
        if on:
            self.operator_stop = False
            self._request_stop("normal", "service")

    def cmd_curtail(self, power_kw: Optional[float]):
        self.curtailment_kw = power_kw

    def cmd_emergency_stop(self, cause: str = "emergency"):
        self.operator_start_pending = False
        self._request_stop("emergency", cause)

    def get_control_status(self) -> dict:
        return {
            "operator_stop": self.operator_stop,
            "service_mode": self.service_mode,
            "local_control": self.local_control,
            "curtailment_kw": self.curtailment_kw,
            "tur_state": self.tur_state,
            "stop_mode": self._stop_mode if self._stop_requested or self.tur_state == 7 else None,
            "shutdown_cause": self._shutdown_cause,
        }

    def reset(self):
        self.tur_state = 1
        self.rotor_speed = 0.0
        self.pitch_angle = 90.0
        self._pitch_bl = [90.0, 90.0, 90.0]
        self._sim_time = 0.0
        self._generated_power_kw = 0.0
        self._generator_speed = 0.0
        self._grid_voltage = 0.0
        self._grid_frequency = 0.0
        self._sync_progress = 0.0
        self._drivetrain_twist = 0.0
        self._state_timer = 0.0
        self._wind_ready_timer = 0.0
        self._restart_wait_timer = 0.0
        self._restart_block_timer = 0.0
        self._stop_requested = False
        self._stop_mode = "normal"
        self._shutdown_cause = "idle"
        self._grid_phase = self._rng.uniform(0.0, math.tau)
        self._grid_local_phase = self._rng.uniform(0.0, math.tau)
        self._grid_voltage_ref = self.spec.nominal_voltage
        self._grid_frequency_ref = 50.0
        self._grid_normal_trip_accum = 0.0
        self._grid_emergency_trip_accum = 0.0
        self.operator_stop = False
        self.service_mode = False
        self.operator_start_pending = False
        self.curtailment_kw = None
        self.fault_modifiers.clear()
        self.active_faults = []
        self._sensor_bias.clear()
        self._sensor_stuck_until.clear()
        self._sensor_last.clear()

    def _enter_state(self, state: int):
        self.tur_state = state
        self._state_timer = 0.0
        if state in (1, 2):
            self._sync_progress = 0.0
        elif state == 3:
            self._restart_wait_timer = 0.0
            self._sync_progress = 0.0
        elif state == 4:
            self._sync_progress = 0.0
        elif state == 5:
            self._sync_progress = 0.0
        elif state == 6:
            self._sync_progress = 1.0
        if state in (7, 9):
            self._restart_block_timer = max(self._restart_block_timer, 20.0 if state == 7 else 10.0)

    def _request_stop(self, mode: str, cause: Optional[str] = None):
        self._stop_requested = True
        self._stop_mode = mode
        self._shutdown_cause = cause or mode

    def _update_grid_reference(self, dt: float, grid_frequency_ref: Optional[float] = None,
                               grid_voltage_ref: Optional[float] = None):
        self._grid_phase = (self._grid_phase + dt * 0.03) % math.tau
        self._grid_local_phase = (self._grid_local_phase + dt * 0.05) % math.tau
        freq_base = 50.0 + 0.08 * math.sin(self._grid_phase) + self._rng.normal(0.0, 0.01)
        volt_base = self.spec.nominal_voltage + self._individuality["grid_voltage_bias"] + 6.0 * math.sin(self._grid_phase * 0.7 + 0.4) + self._rng.normal(0.0, 0.8)
        farm_freq = grid_frequency_ref if grid_frequency_ref is not None else freq_base
        farm_volt = grid_voltage_ref if grid_voltage_ref is not None else volt_base
        local_freq = (
            self._individuality["grid_freq_bias"]
            + 0.03 * self._individuality["grid_ride_through_scale"] * math.sin(self._grid_local_phase + 0.2)
            + self._rng.normal(0.0, 0.004)
        )
        local_volt = (
            self._individuality["grid_voltage_local_bias"]
            + 3.5 * self._individuality["grid_ride_through_scale"] * math.sin(self._grid_local_phase * 0.9 - 0.3)
            + self._rng.normal(0.0, 0.6)
        )
        self._grid_frequency_ref = farm_freq + local_freq
        self._grid_voltage_ref = farm_volt + local_volt

    def _get_grid_derate(self) -> float:
        freq_dev = abs(self._grid_frequency_ref - 50.0)
        volt_dev = abs(self._grid_voltage_ref - self.spec.nominal_voltage)
        sensitivity = self._individuality["grid_derate_sensitivity"]
        freq_scale = 1.0 if freq_dev < 0.15 else max(0.72, 1.0 - (freq_dev - 0.15) * 0.45 * sensitivity)
        volt_scale = 1.0 if volt_dev < 20.0 else max(0.68, 1.0 - ((volt_dev - 20.0) / 180.0) * sensitivity)
        return min(freq_scale, volt_scale)

    def _check_grid_trip(self) -> Optional[str]:
        freq = self._grid_frequency_ref
        volt = self._grid_voltage_ref
        hz_margin = self._individuality["grid_trip_margin_hz"]
        volt_margin = self._individuality["grid_trip_margin_v"]
        severe_limit = (
            freq < 48.6 + hz_margin
            or freq > 51.4 - hz_margin
            or volt < 560.0 + volt_margin
            or volt > 790.0 - volt_margin
        )
        normal_limit = (
            freq < 49.0 + hz_margin
            or freq > 51.0 - hz_margin
            or volt < 600.0 + volt_margin
            or volt > 760.0 - volt_margin
        )

        severe_tau = max(0.6, 1.4 / max(0.65, self._individuality["grid_ride_through_scale"]))
        normal_tau = max(1.5, 4.5 / max(0.65, self._individuality["grid_ride_through_scale"]))
        decay_normal = 0.55
        decay_severe = 0.45

        if severe_limit:
            self._grid_emergency_trip_accum += 1.0 / severe_tau
        else:
            self._grid_emergency_trip_accum = max(0.0, self._grid_emergency_trip_accum - decay_severe)

        if normal_limit:
            self._grid_normal_trip_accum += 1.0 / normal_tau
        else:
            self._grid_normal_trip_accum = max(0.0, self._grid_normal_trip_accum - decay_normal)

        if self._grid_emergency_trip_accum >= 1.0:
            self._grid_emergency_trip_accum = 0.0
            self._grid_normal_trip_accum = 0.0
            return "emergency"
        if self._grid_normal_trip_accum >= 1.0:
            self._grid_normal_trip_accum = 0.0
            return "normal"
        return None

    def _apply_drivetrain_dynamics(
        self,
        aero_rotor_speed: float,
        effective_wind_speed: float,
        dt: float,
        is_producing: bool,
        is_starting: bool,
        is_normal_stop: bool,
        is_emergency_stop: bool,
    ) -> Tuple[float, float, float, float, float]:
        gear_ratio = max(1.0, self.spec.gear_ratio)
        stiffness = 0.36 * self._individuality["drivetrain_stiffness_scale"]
        damping = 0.24 * self._individuality["shaft_damping_scale"]
        shaft_target = aero_rotor_speed * gear_ratio if (is_producing or is_starting) else 0.0
        slip_error = shaft_target - self._generator_speed

        # Elastic shaft twist lets rotor and generator speeds separate during transients.
        self._drivetrain_twist += (
            slip_error * 0.12 * stiffness - self._drivetrain_twist * damping
        ) * dt

        normal_brake = 0.0
        emergency_brake = 0.0
        if is_normal_stop:
            normal_brake = (
                (0.75 + 0.02 * self.pitch_angle + max(0.0, self.rotor_speed - 1.5) * 0.16)
                * self._individuality["normal_brake_scale"]
            )
        elif is_emergency_stop:
            emergency_brake = (
                (3.8 + 0.10 * self.pitch_angle + max(0.0, self.rotor_speed - 1.0) * 0.30)
                * self._individuality["emergency_brake_scale"]
            )

        rotor_brake_rate = normal_brake * 0.22 + emergency_brake * 0.44
        generator_brake_rate = normal_brake * 18.0 + emergency_brake * 40.0
        coupling_to_rotor = self._drivetrain_twist / (gear_ratio * 24.0)
        coupling_to_generator = self._drivetrain_twist * 0.62

        rotor_speed = aero_rotor_speed - rotor_brake_rate * dt - coupling_to_rotor
        if not (is_producing or is_starting) and not (is_normal_stop or is_emergency_stop):
            rotor_speed = max(0.0, rotor_speed - 0.30 * dt)
        rotor_speed = max(0.0, rotor_speed)

        self._generator_speed += (
            slip_error * 0.48 * stiffness + coupling_to_generator - generator_brake_rate
        ) * dt
        if not (is_producing or is_starting):
            coast_down = 12.0 if is_normal_stop else 26.0 if is_emergency_stop else 8.0
            self._generator_speed = max(0.0, self._generator_speed - coast_down * dt)
        else:
            self._generator_speed = max(0.0, self._generator_speed)

        # Avoid unrealistic negative slip during aggressive stops while preserving torsional lag.
        max_sync_speed = max(shaft_target, rotor_speed * gear_ratio)
        if is_producing or is_starting:
            self._generator_speed = min(self._generator_speed, max_sync_speed + 120.0)

        brake_heat_kw = (normal_brake * 6.0 + emergency_brake * 18.0) * (1.0 + 0.03 * effective_wind_speed)
        drivetrain_loss_kw = (
            abs(self._drivetrain_twist) * 0.06
            + rotor_speed * 0.8 * self._individuality["bearing_friction_scale"]
            + brake_heat_kw * 0.08
        )
        torsion_vib = min(
            2.8,
            abs(self._drivetrain_twist) * 0.02
            + abs((rotor_speed * gear_ratio) - self._generator_speed) / max(gear_ratio, 1.0) * 0.10,
        )
        return rotor_speed, self._generator_speed, drivetrain_loss_kw, brake_heat_kw, torsion_vib

    def _apply_sensor_model(self, output: Dict[str, float]) -> Dict[str, float]:
        sensorized: Dict[str, float] = {}
        for tag, value in output.items():
            if tag == "WTUR_TurSt":
                sensorized[tag] = round(value)
                continue
            cfg = self._get_sensor_config(tag)
            if cfg["drift"] > 0.0:
                self._sensor_bias[tag] = self._sensor_bias.get(tag, 0.0) + self._rng.normal(0.0, cfg["drift"])
                self._sensor_bias[tag] = max(-cfg["bias_limit"], min(cfg["bias_limit"], self._sensor_bias[tag]))
            if self._sim_time >= self._sensor_stuck_until.get(tag, 0.0) and self._rng.uniform() < cfg["stuck_prob"]:
                self._sensor_stuck_until[tag] = self._sim_time + self._rng.uniform(6.0, 20.0)
            if self._sim_time < self._sensor_stuck_until.get(tag, 0.0) and tag in self._sensor_last:
                sensorized[tag] = self._sensor_last[tag]
                continue
            measured = value + self._sensor_bias.get(tag, 0.0) + self._rng.normal(0.0, cfg["noise"])
            resolution = cfg["resolution"]
            if resolution > 0:
                measured = round(measured / resolution) * resolution
            measured = max(cfg["min"], measured) if cfg["min"] is not None else measured
            measured = min(cfg["max"], measured) if cfg["max"] is not None else measured
            self._sensor_last[tag] = measured
            sensorized[tag] = measured
        return sensorized

    def _get_sensor_config(self, tag: str) -> Dict[str, float]:
        if tag.startswith("WGEN_Gn") and "Tmp" in tag:
            return {"noise": 0.18, "drift": 0.002, "bias_limit": 1.5, "resolution": 0.1, "stuck_prob": 0.0002, "min": -40.0, "max": 180.0}
        if tag.startswith("WCNV_IGCTWtrPres"):
            return {"noise": 0.02, "drift": 0.0005, "bias_limit": 0.15, "resolution": 0.01, "stuck_prob": 0.00015, "min": 0.0, "max": 10.0}
        if "Tmp" in tag:
            return {"noise": 0.12, "drift": 0.0015, "bias_limit": 1.0, "resolution": 0.1, "stuck_prob": 0.00012, "min": -40.0, "max": 180.0}
        if "Spd" in tag or "Frq" in tag:
            return {"noise": 0.04, "drift": 0.0008, "bias_limit": 0.25, "resolution": 0.01, "stuck_prob": 0.0001, "min": 0.0, "max": 5000.0}
        if "Vtg" in tag:
            return {"noise": 1.5, "drift": 0.01, "bias_limit": 6.0, "resolution": 0.1, "stuck_prob": 0.00005, "min": 0.0, "max": 2000.0}
        if "Cur" in tag:
            return {"noise": 0.8, "drift": 0.01, "bias_limit": 3.0, "resolution": 0.1, "stuck_prob": 0.00005, "min": 0.0, "max": 10000.0}
        if "Pwr" in tag:
            return {"noise": 8.0, "drift": 0.08, "bias_limit": 35.0, "resolution": 1.0, "stuck_prob": 0.00008, "min": -500.0, "max": 10000.0}
        if "Vib" in tag:
            return {"noise": 0.03, "drift": 0.0008, "bias_limit": 0.25, "resolution": 0.01, "stuck_prob": 0.0002, "min": 0.0, "max": 30.0}
        if "PtAng" in tag or "YwVn" in tag or "WDir" in tag:
            return {"noise": 0.08, "drift": 0.001, "bias_limit": 0.8, "resolution": 0.01, "stuck_prob": 0.00012, "min": -360.0, "max": 360.0}
        return {"noise": 0.02, "drift": 0.0002, "bias_limit": 0.2, "resolution": 0.01, "stuck_prob": 0.0, "min": -1.0e9, "max": 1.0e9}

    def _get_fault_physics(self) -> Dict[str, object]:
        fault_physics = {
            "wind_scale": 1.0,
            "power_scale": 1.0,
            "rotor_speed_bias": 0.0,
            "blade1_pitch_bias": 0.0,
            "yaw_error_bias": 0.0,
            "yaw_brake_bias": 0.0,
            "vibration_x": 0.0,
            "vibration_y": 0.0,
            "extra_heat": {
                "generator": 0.0,
                "converter": 0.0,
                "transformer": 0.0,
                "bearing": 0.0,
                "nacelle": 0.0,
            },
            "cooling_bias": {
                "nacelle": 1.0,
                "exposed": 1.0,
                "cabinet": 1.0,
                "water": 1.0,
                "transformer": 1.0,
            },
        }

        for fault in self.active_faults:
            severity = float(fault.get("severity", 0.0))
            scenario_id = fault.get("scenario_id")
            if scenario_id == "bearing_wear":
                fault_physics["extra_heat"]["bearing"] += 18.0 * severity
                fault_physics["extra_heat"]["generator"] += 6.0 * severity
                fault_physics["vibration_x"] += 1.5 * severity
                fault_physics["vibration_y"] += 1.2 * severity
            elif scenario_id == "gearbox_overheat":
                fault_physics["extra_heat"]["nacelle"] += 10.0 * severity
                fault_physics["extra_heat"]["converter"] += 4.0 * severity
                fault_physics["cooling_bias"]["nacelle"] *= max(0.55, 1.0 - 0.30 * severity)
                fault_physics["vibration_x"] += 0.8 * severity
                fault_physics["vibration_y"] += 0.7 * severity
            elif scenario_id == "pitch_motor_fault":
                fault_physics["blade1_pitch_bias"] += 8.0 * severity
                fault_physics["power_scale"] *= max(0.78, 1.0 - 0.10 * severity)
                fault_physics["vibration_x"] += 0.9 * severity
                fault_physics["vibration_y"] += 0.5 * severity
            elif scenario_id == "converter_cooling_fault":
                fault_physics["extra_heat"]["converter"] += 16.0 * severity
                fault_physics["cooling_bias"]["water"] *= max(0.25, 1.0 - 0.70 * severity)
                fault_physics["cooling_bias"]["cabinet"] *= max(0.55, 1.0 - 0.35 * severity)
                fault_physics["power_scale"] *= max(0.82, 1.0 - 0.08 * severity)
            elif scenario_id == "yaw_misalignment":
                yaw_deg = 20.0 * severity
                fault_physics["yaw_error_bias"] += yaw_deg
                fault_physics["wind_scale"] *= max(0.72, math.cos(math.radians(min(35.0, abs(yaw_deg)))))
                fault_physics["yaw_brake_bias"] -= 25.0 * severity
            elif scenario_id == "generator_overspeed":
                fault_physics["rotor_speed_bias"] += 0.8 * severity
                fault_physics["vibration_x"] += 2.2 * severity
                fault_physics["vibration_y"] += 1.8 * severity
                fault_physics["extra_heat"]["generator"] += 8.0 * severity
            elif scenario_id == "transformer_overheat":
                fault_physics["extra_heat"]["transformer"] += 18.0 * severity
                fault_physics["cooling_bias"]["transformer"] *= max(0.45, 1.0 - 0.40 * severity)
                fault_physics["extra_heat"]["nacelle"] += 2.5 * severity

        return fault_physics

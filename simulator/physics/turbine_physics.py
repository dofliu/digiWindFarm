"""
Independent physics-based wind turbine model.

Produces all 39+ SCADA data points with physically-coupled relationships.
No dependency on FastAPI, frontend, or storage — only numpy.

Coupling chain:
  Wind → Rotor RPM → Generator RPM/Freq → Power/Current/Voltage
  Wind → Pitch control → 3 blade angles (independent, ±0.3° variation)
  Wind direction → Yaw error → Yaw action → Hydraulic pressure / Cable windup
  Power × time → Thermal models (generator, converter, transformer, nacelle)
  RPM + imbalance → Vibration XY
  Ambient temp → Nacelle temp → Cabinet temps
"""

import math
import numpy as np
from typing import Dict, Optional


class ThermalModel:
    """First-order thermal model: dT/dt = (Q_in - (T - T_amb) / R_th) / C_th"""

    def __init__(self, thermal_resistance: float, thermal_capacity: float,
                 initial_temp: float = 25.0):
        self.R_th = thermal_resistance   # °C/kW
        self.C_th = thermal_capacity     # kJ/°C  (time constant = R*C seconds)
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

    # ─── Turbine parameters (Z72 / ENERCON E-126, 5MW class) ──────────
    RATED_POWER_KW = 5000.0
    ROTOR_DIAMETER = 126.0       # m
    HUB_HEIGHT = 90.0            # m
    CUT_IN_SPEED = 3.0           # m/s
    RATED_SPEED = 12.0           # m/s
    CUT_OUT_SPEED = 25.0         # m/s
    AIR_DENSITY = 1.225          # kg/m³
    GEAR_RATIO = 100.0
    GENERATOR_EFFICIENCY = 0.95
    GENERATOR_POLES = 4
    NOMINAL_VOLTAGE = 690.0      # V

    def __init__(self, seed: Optional[int] = None):
        self._rng = np.random.RandomState(seed)

        # ── State variables ──
        self.tur_state = 1               # TurState 1-9 (Bachmann definition)
        self.rotor_speed = 0.0           # RPM
        self.pitch_angle = 90.0          # deg (feathered)
        self._pitch_bl = [90.0, 90.0, 90.0]  # individual blade angles
        self.yaw_angle = 270.0           # deg
        self.cable_windup = 0.0          # turns

        # ── Thermal models (R_th in °C/kW, C_th in kJ/°C) ──
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

        # ── Accumulated counters ──
        self._yaw_brake_pressure = 150.0  # bar
        self._sim_time = 0.0

        # ── Fault modifiers (set by FaultEngine) ──
        self.fault_modifiers: Dict[str, float] = {}

    def step(self, wind_speed: float, wind_direction: float,
             ambient_temp: float = 25.0, dt: float = 1.0) -> Dict[str, float]:
        """
        Advance simulation by dt seconds.

        Returns:
            Flat dict keyed by SCADA tag IDs with current values.
        """
        self._sim_time += dt

        # ── 1. State machine (Bachmann TurState 1-9) ──
        self._update_state(wind_speed)
        is_producing = self.tur_state == 6  # Production

        # ── 2. Rotor aerodynamics ──
        rotor_power_kw, rotor_torque = self._calc_rotor(wind_speed, dt, is_producing)

        # ── 3. Pitch control (3 independent blades) ──
        self._calc_pitch(wind_speed, is_producing, dt)

        # ── 4. Gearbox & Generator ──
        gen_speed = self.rotor_speed * self.GEAR_RATIO if is_producing else 0.0
        gen_power_kw = rotor_power_kw * self.GENERATOR_EFFICIENCY if is_producing else 0.0
        gen_power_kw = min(gen_power_kw, self.RATED_POWER_KW)

        gen_freq = (gen_speed * self.GENERATOR_POLES / 2) / 60.0 if is_producing else 0.0
        gen_voltage = self.NOMINAL_VOLTAGE if is_producing else 0.0
        gen_current = (gen_power_kw * 1000 / (gen_voltage * math.sqrt(3) * 0.95)
                       if gen_voltage > 0 and gen_power_kw > 0 else 0.0)

        # Converter values
        cnv_gn_pwr = gen_power_kw
        cnv_gd_pwr = gen_power_kw * 0.98  # grid-side after converter losses
        cnv_dc_vtg = 1100.0 if is_producing else 0.0

        # ── 5. Yaw system ──
        self._calc_yaw(wind_direction, is_producing, dt)
        yaw_error = self._angle_diff(wind_direction, self.yaw_angle)

        # ── 6. Thermal models ──
        heat_gen = gen_power_kw * (1 - self.GENERATOR_EFFICIENCY) if is_producing else 0.0
        heat_cnv = gen_power_kw * 0.02 if is_producing else 0.0
        heat_trf = cnv_gd_pwr * 0.01 if is_producing else 0.0
        heat_nac = heat_gen * 0.3 + heat_cnv * 0.5  # heat radiated into nacelle

        gen_sta_t = self._gen_stator_temp.step(heat_gen * 0.6, ambient_temp, dt)
        gen_air_t = self._gen_air_temp.step(heat_gen * 0.3, ambient_temp, dt)
        gen_brg_t = self._gen_bearing_temp.step(heat_gen * 0.1 + self.rotor_speed * 0.01,
                                                 ambient_temp, dt)
        cnv_cab_t = self._cnv_cabin_temp.step(heat_cnv, ambient_temp, dt)
        cnv_wtr_t = self._cnv_igct_water_temp.step(heat_cnv * 0.7, ambient_temp, dt)
        trf_t = self._transformer_temp.step(heat_trf, ambient_temp, dt)
        nac_t = self._nacelle_temp.step(heat_nac, ambient_temp, dt)
        nac_cab_t = self._nacelle_cab_temp.step(heat_cnv * 0.2, nac_t, dt)
        rot_t = self._rotor_temp.step(0, ambient_temp, dt)
        hub_cab_t = self._hub_cab_temp.step(0, rot_t, dt)

        # ── 7. Vibration model ──
        base_vib = 0.3 + self.rotor_speed * 0.05 if is_producing else 0.1
        vib_x = base_vib + self._rng.normal(0, 0.15)
        vib_y = base_vib * 0.8 + self._rng.normal(0, 0.12)

        # ── 8. Hydraulic / cooling ──
        igct_pres1 = 3.5 + self._rng.normal(0, 0.1) if is_producing else 0.0
        igct_pres2 = 3.3 + self._rng.normal(0, 0.1) if is_producing else 0.0
        igct_cond = 1.0 if is_producing else 0.0

        # Yaw brake pressure: high when stationary, drops during yaw action
        if abs(yaw_error) > 5 and is_producing:
            self._yaw_brake_pressure = max(80, self._yaw_brake_pressure - 2 * dt)
        else:
            self._yaw_brake_pressure = min(180, self._yaw_brake_pressure + 5 * dt)
        yaw_brake_prs = self._yaw_brake_pressure + self._rng.normal(0, 1)

        # ── 9. Status flags ──
        rotor_locked = 1 if self.tur_state in (1, 2, 9) else 0
        brake_active = 1 if self.tur_state in (1, 7, 9) else 0
        locking_pin = 1.0 if rotor_locked else 0.0
        srv_on = 0
        local_ctrl = 0  # 0=remote

        # ── Build output dict ──
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
            "WSRV_SrvOn": float(srv_on),
            "MBUS_Contact2": float(local_ctrl),
        }

        # Apply fault modifiers (additive or multiplicative offsets from FaultEngine)
        for tag_id, modifier in self.fault_modifiers.items():
            if tag_id in output:
                output[tag_id] += modifier

        return output

    # ─── State machine (Bachmann TurState 1-9) ─────────────────────────

    def _update_state(self, wind_speed: float):
        """Transition between Bachmann turbine states."""
        st = self.tur_state

        if st == 1:  # Shutdown
            if self.CUT_IN_SPEED <= wind_speed <= self.CUT_OUT_SPEED:
                self.tur_state = 2  # → Standby
        elif st == 2:  # Standby
            if wind_speed >= self.CUT_IN_SPEED + 0.5:
                self.tur_state = 4  # → Pre-Production
        elif st == 3:  # Wait Restart
            if self.CUT_IN_SPEED <= wind_speed <= self.CUT_OUT_SPEED:
                self.tur_state = 4
        elif st == 4:  # Pre-Production
            self.tur_state = 5  # → Start Production
        elif st == 5:  # Start Production
            if self.rotor_speed > 2.0:
                self.tur_state = 6  # → Production
        elif st == 6:  # Production
            if wind_speed < self.CUT_IN_SPEED - 0.3:
                self.tur_state = 7  # → Shutdown (low wind)
            elif wind_speed > self.CUT_OUT_SPEED:
                self.tur_state = 7  # → Shutdown (storm)
        elif st == 7:  # Shutdown (in progress)
            if self.rotor_speed < 0.5:
                self.tur_state = 1  # → Shutdown complete
        elif st == 8:  # Restart
            self.tur_state = 4  # → Pre-Production
        elif st == 9:  # Normal Stop
            if self.rotor_speed < 0.5:
                self.tur_state = 1

    # ─── Rotor aerodynamics ────────────────────────────────────────────

    def _calc_rotor(self, wind_speed: float, dt: float,
                    is_producing: bool) -> tuple:
        swept_area = math.pi * (self.ROTOR_DIAMETER / 2) ** 2

        if is_producing and wind_speed > 0:
            tsr = ((self.rotor_speed * math.pi * self.ROTOR_DIAMETER / 60) / wind_speed
                   if wind_speed > 0 else 0)
            cp = self._calc_cp(tsr)
            wind_power = 0.5 * self.AIR_DENSITY * swept_area * wind_speed ** 3
            rotor_power = wind_power * cp / 1000.0  # kW

            target_rpm = self._optimal_rpm(wind_speed)
            self.rotor_speed += (target_rpm - self.rotor_speed) * 0.1 * dt

            rotor_torque = (rotor_power * 1000 / (self.rotor_speed * 2 * math.pi / 60)
                            if self.rotor_speed > 0 else 0)
        else:
            # Decelerating
            self.rotor_speed = max(0, self.rotor_speed - 0.3 * dt)
            rotor_power = 0.0
            rotor_torque = 0.0

            # Starting up
            if self.tur_state in (4, 5) and wind_speed >= self.CUT_IN_SPEED:
                target_rpm = self._optimal_rpm(wind_speed)
                self.rotor_speed += target_rpm * 0.05 * dt

        return rotor_power, rotor_torque

    @staticmethod
    def _calc_cp(tsr: float) -> float:
        if tsr <= 0 or tsr > 15:
            return 0.0
        optimal_tsr = 7.5
        cp_max = 0.48
        return cp_max * math.exp(-0.5 * ((tsr - optimal_tsr) / 2.5) ** 2)

    def _optimal_rpm(self, wind_speed: float) -> float:
        optimal_tsr = 7.5
        rpm = (optimal_tsr * wind_speed * 60) / (math.pi * self.ROTOR_DIAMETER)
        return min(rpm, 15.0)  # max rotor RPM

    # ─── Pitch control ─────────────────────────────────────────────────

    def _calc_pitch(self, wind_speed: float, is_producing: bool, dt: float):
        max_rate = 8.0  # deg/s

        if not is_producing:
            target = 90.0  # feathered
        elif wind_speed < self.RATED_SPEED:
            target = 0.0  # optimal
        else:
            target = min(30.0, (wind_speed - self.RATED_SPEED) * 2.3)

        # Move main pitch angle
        diff = target - self.pitch_angle
        change = max(-max_rate * dt, min(max_rate * dt, diff))
        self.pitch_angle += change

        # Individual blades: ±0.3° mechanical tolerance
        for i in range(3):
            blade_offset = self._rng.normal(0, 0.15)
            self._pitch_bl[i] = self.pitch_angle + blade_offset

    # ─── Yaw system ───────────────────────────────────────────────────

    def _calc_yaw(self, wind_direction: float, is_producing: bool, dt: float):
        if not is_producing:
            return

        error = self._angle_diff(wind_direction, self.yaw_angle)

        if abs(error) > 5.0:
            yaw_rate = 0.3  # deg/s
            self.yaw_angle += math.copysign(yaw_rate, error) * dt
            self.yaw_angle %= 360

            # Cable windup accumulates with yaw rotation
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
        """Force turbine into a specific state (for fault injection)."""
        if 1 <= state <= 9:
            self.tur_state = state

    def reset(self):
        """Reset to initial idle state."""
        self.tur_state = 1
        self.rotor_speed = 0.0
        self.pitch_angle = 90.0
        self._pitch_bl = [90.0, 90.0, 90.0]
        self.fault_modifiers.clear()

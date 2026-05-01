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
from simulator.physics.drivetrain_model import DrivetrainModel, DrivetrainSpec
from simulator.physics.cooling_model import CoolingSystem, CoolingSpec
from simulator.physics.electrical_model import ElectricalModel, ElectricalSpec
from simulator.physics.vibration_spectral import SpectralVibrationModel
from simulator.physics.fatigue_model import FatigueModel, FatigueSpec


@dataclass
class TurbineSpec:
    """Configurable wind turbine specifications."""

    rated_power_kw: float = 2000.0
    rotor_diameter: float = 70.65
    hub_height: float = 64.0
    cut_in_speed: float = 3.0
    rated_speed: float = 13.0
    cut_out_speed: float = 25.0

    # Z72: direct-drive PMSG, no gearbox (gear_ratio=1)
    gear_ratio: float = 1.0
    generator_efficiency: float = 0.95
    generator_poles: int = 60
    nominal_voltage: float = 3500.0  # Z72 MV generator: 3.5kV
    air_density: float = 1.225

    max_rotor_rpm: float = 22.5
    optimal_tsr: float = 7.0
    cp_max: float = 0.45

    # Z72 protection setpoints
    overspeed_software_rpm: float = 26.5
    overspeed_hardware_rpm: float = 28.5
    power_limit_5s_pct: float = 1.10   # 110% of rated
    power_limit_10m_pct: float = 1.05  # 105% of rated
    max_restarts_per_hour: int = 3

    # Z72 pitch angles (degrees)
    pitch_vane: float = 86.0      # feathered / emergency
    pitch_startup: float = 30.0   # startup position
    pitch_work: float = -1.0      # optimal production
    pitch_emergency_rate: float = 5.0  # min deg/s for emergency pitch

    # Z72 temperature thresholds (°C)
    gen_stator_alarm: float = 140.0
    gen_stator_trip: float = 150.0
    gen_bearing_alarm: float = 85.0
    gen_bearing_trip: float = 95.0
    nacelle_cab_alarm: float = 45.0
    nacelle_cab_trip: float = 50.0
    rotor_cab_alarm: float = 45.0
    rotor_cab_trip: float = 50.0
    outside_temp_low: float = -25.0
    outside_temp_high: float = 45.0

    # Z72 yaw thresholds
    yaw_pressure_trip: float = 150.0     # bar, very low
    yaw_pressure_alarm: float = 170.0    # bar, low
    yaw_pressure_normal: float = 210.0   # bar, high friction
    cable_twist_limit: float = 2.5       # turns

    # Z72 grid (60Hz system)
    grid_frequency_nominal: float = 60.0

    curtailment_kw: Optional[float] = None
    power_curve: Optional[List[Tuple[float, float]]] = None

    rotor_diameter_m: Optional[float] = None  # alias for session tracking

    def to_dict(self) -> dict:
        """Serialize turbine spec to a plain dictionary."""
        d = {k: getattr(self, k) for k in self.__dataclass_fields__}
        d['rotor_diameter_m'] = self.rotor_diameter
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "TurbineSpec":
        """Construct a TurbineSpec from a dictionary, ignoring unknown keys."""
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


TURBINE_PRESETS: Dict[str, TurbineSpec] = {
    # Default: Z72-2000-MV (Harakosan, direct-drive PMSG, 60Hz)
    "z72_2mw": TurbineSpec(),
    "vestas_v90_3mw": TurbineSpec(
        rated_power_kw=3000, rotor_diameter=90, hub_height=80,
        cut_in_speed=4.0, rated_speed=13.0, cut_out_speed=25.0,
        gear_ratio=104.5, generator_poles=4, nominal_voltage=690.0,
        max_rotor_rpm=16.7, optimal_tsr=8.0,
        grid_frequency_nominal=60.0,
    ),
    "sg_8mw": TurbineSpec(
        rated_power_kw=8000, rotor_diameter=167, hub_height=92,
        cut_in_speed=3.0, rated_speed=12.0, cut_out_speed=25.0,
        gear_ratio=1.0, generator_poles=300, nominal_voltage=690.0,
        max_rotor_rpm=10.6, optimal_tsr=9.0, cp_max=0.49,
        grid_frequency_nominal=50.0,
    ),
    "goldwind_2.5mw": TurbineSpec(
        rated_power_kw=2500, rotor_diameter=121, hub_height=90,
        cut_in_speed=3.0, rated_speed=10.3, cut_out_speed=22.0,
        gear_ratio=1.0, generator_poles=96, nominal_voltage=690.0,
        max_rotor_rpm=11.5, optimal_tsr=8.5, cp_max=0.47,
        grid_frequency_nominal=50.0,
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

        # Per-turbine blade mass offsets (fractional, ±0.5% manufacturing tolerance)
        _blade_mass_offsets = [
            self._rng.normal(0, 0.005),
            self._rng.normal(0, 0.005),
            self._rng.normal(0, 0.005),
        ]

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
            "tower_shadow_amp": 0.12 + self._rng.uniform(-0.03, 0.03),
            # Per-turbine permanent shear offset (±0.04–0.06) applied on top
            # of the time-varying farm-level α from the atmospheric stability
            # model (see #99). Legacy key `wind_shear_exp` removed.
            "wind_shear_exp_offset": self._rng.uniform(-0.04, 0.06),
            "blade_mass_offsets": _blade_mass_offsets,
            "wind_veer_rate": 0.10 + self._rng.uniform(-0.03, 0.03),
        }

        self.power_curve = PowerCurveModel(
            power_curve=self.spec.power_curve,
            rated_power_kw=self.spec.rated_power_kw,
            cut_in=self.spec.cut_in_speed + self._individuality["cut_in_offset"],
            rated_speed=self.spec.rated_speed,
            cut_out=self.spec.cut_out_speed,
            rotor_diameter=self.spec.rotor_diameter,
            cp_max=self.spec.cp_max,
            air_density=self.spec.air_density,
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

        # Drivetrain model (#28)
        if self.spec.gear_ratio > 1.0:
            dt_spec = DrivetrainSpec.for_geared(overall_ratio=self.spec.gear_ratio)
        else:
            dt_spec = DrivetrainSpec.for_direct_drive()
        self.drivetrain = DrivetrainModel(spec=dt_spec, individuality=self._individuality)

        # Cooling system model (#29)
        self.cooling = CoolingSystem(
            spec=CoolingSpec(),
            individuality_scale=self._individuality["cooling_scale"],
        )

        # Electrical response model (frequency-watt, reactive power, ride-through)
        elec_spec = ElectricalSpec(
            apparent_power_max_mva=self.spec.rated_power_kw / 1000.0 * 1.15,
        )
        self.electrical = ElectricalModel(spec=elec_spec, individuality=self._individuality)

        # Spectral vibration model (frequency-band decomposition)
        self.vib_spectral = SpectralVibrationModel(
            seed=_seed,
            gear_ratio=self.spec.gear_ratio,
        )

        # Fatigue / structural load model (cloud version logic)
        self.fatigue = FatigueModel(
            spec=FatigueSpec(),
            seed=_seed,
            rated_power_kw=self.spec.rated_power_kw,
            rotor_diameter=self.spec.rotor_diameter,
        )

        self.tur_state = 1
        self.rotor_speed = 0.0
        self.pitch_angle = self.spec.pitch_vane  # Z72: vane position (86°)
        self._pitch_bl = [self.spec.pitch_vane] * 3
        self._rotor_azimuth = self._rng.uniform(0.0, math.tau)
        self._imbalance_force_kn = 0.0
        self._local_ti_multiplier = 1.0
        self._wake_deficit = 0.0
        self._wake_meander_offset_m = 0.0
        self._wake_yaw_deflection_m = 0.0
        # Wake-added TI fraction (Crespo-Hernández) — combined upstream contribution (#103)
        self._wake_added_ti = 0.0
        # Atmospheric stability coupling (#99): α is farm-level time-varying,
        # applied with per-turbine permanent offset from individuality.
        self._effective_shear_alpha = 0.2 + self._individuality.get("wind_shear_exp_offset", 0.0)
        self._atm_stability = 0.0
        # Air density ρ(T, RH, P) — updated per step from ambient temp + humidity + pressure (#101, #106)
        self._air_density = self.spec.air_density
        self._ambient_pressure_pa = 101325.0
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
        self._grid_frequency_ref = self.spec.grid_frequency_nominal
        self._grid_normal_trip_accum = 0.0
        self._grid_emergency_trip_accum = 0.0
        # Z72: restart tracking (max restarts per hour)
        self._restart_timestamps: List[float] = []
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
            rotor_diameter=spec.rotor_diameter,
            cp_max=spec.cp_max,
            air_density=spec.air_density,
        )
        self.rotor_model = RotorSpeedModel(
            rotor_diameter=spec.rotor_diameter,
            optimal_tsr=spec.optimal_tsr,
            max_rpm=spec.max_rotor_rpm,
            rated_speed=spec.rated_speed,
            gear_ratio=spec.gear_ratio,
        )
        if spec.gear_ratio > 1.0:
            dt_spec = DrivetrainSpec.for_geared(overall_ratio=spec.gear_ratio)
        else:
            dt_spec = DrivetrainSpec.for_direct_drive()
        self.drivetrain = DrivetrainModel(spec=dt_spec, individuality=self._individuality)

    def step(self, wind_speed: float, wind_direction: float,
             ambient_temp: float = 25.0, dt: float = 1.0,
             grid_frequency_ref: Optional[float] = None,
             grid_voltage_ref: Optional[float] = None,
             ambient_humidity_pct: float = 65.0,
             local_ti_multiplier: float = 1.0,
             wake_deficit: float = 0.0,
             wake_meander_offset_m: float = 0.0,
             wake_yaw_deflection_m: float = 0.0,
             wake_added_ti: float = 0.0,
             wind_shear_exp_base: float = 0.2,
             atm_stability: float = 0.0,
             air_density: float = 1.225,
             ambient_pressure_pa: float = 101325.0) -> Dict[str, float]:
        """Advance the turbine physics simulation by one timestep and return all SCADA tag values."""
        s = self.spec
        self._local_ti_multiplier = max(0.0, float(local_ti_multiplier))
        self._wake_deficit = max(0.0, min(0.70, float(wake_deficit)))
        self._wake_meander_offset_m = max(-80.0, min(80.0, float(wake_meander_offset_m)))
        self._wake_yaw_deflection_m = max(-80.0, min(80.0, float(wake_yaw_deflection_m)))
        # Wake-added TI fraction from upstream sources (Crespo-Hernández, #103)
        self._wake_added_ti = max(0.0, min(0.40, float(wake_added_ti)))
        # Atmospheric stability: farm-level α base + per-turbine permanent offset (#99)
        shear_offset = self._individuality.get("wind_shear_exp_offset", 0.0)
        self._effective_shear_alpha = max(
            0.04, min(0.35, float(wind_shear_exp_base) + float(shear_offset))
        )
        self._atm_stability = max(-1.0, min(1.0, float(atm_stability)))
        # Air density ρ(T, RH, P) drives aero power (P ∝ ρ·V³) and thrust (F ∝ ρ·V²) (#101, #106)
        self._air_density = max(0.95, min(1.35, float(air_density)))
        self.power_curve.air_density = self._air_density
        # Ambient pressure (#106): reported as hPa for SCADA trend readability
        self._ambient_pressure_pa = max(90000.0, min(105000.0, float(ambient_pressure_pa)))
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

        # Compute full aerodynamics via Cp(λ,β) surface (#27)
        aero_out = self.power_curve.get_power_cp(
            effective_wind_speed, self.rotor_speed, self.pitch_angle, dt)

        # Tower shadow: 3P torque/thrust modulation (#69)
        omega_rad = self.rotor_speed * math.pi / 30.0
        self._rotor_azimuth = (self._rotor_azimuth + omega_rad * dt) % math.tau
        ts_amp = self._individuality["tower_shadow_amp"]
        ts_sigma = 0.15
        ts_factor = 1.0
        for i in range(3):
            blade_az = (self._rotor_azimuth + i * math.tau / 3.0) % math.tau
            delta = abs(blade_az - math.pi)
            if delta > math.pi:
                delta = math.tau - delta
            ts_factor -= ts_amp / 3.0 * math.exp(-0.5 * (delta / ts_sigma) ** 2)
        aero_out.aero_torque_knm *= ts_factor
        aero_out.thrust_kn *= ts_factor
        aero_out.power_kw *= ts_factor

        # Wind shear: 1P torque modulation from vertical wind profile (#71)
        # V(h) = V_hub × (h/h_hub)^α — blade sweeps different wind speeds
        # α is now farm-level time-varying (diurnal stability, #99) + per-turbine offset
        shear_exp = self._effective_shear_alpha
        R = s.rotor_diameter / 2.0
        H = s.hub_height
        shear_torque_factor = 0.0
        for i in range(3):
            blade_az = (self._rotor_azimuth + i * math.tau / 3.0) % math.tau
            h_blade = H + R * 0.7 * math.cos(blade_az)
            h_blade = max(10.0, h_blade)
            shear_torque_factor += (h_blade / H) ** (shear_exp * 2.0)
        shear_torque_factor /= 3.0  # average across 3 blades, force ~ V²
        aero_out.aero_torque_knm *= shear_torque_factor
        aero_out.thrust_kn *= shear_torque_factor

        # Wind veer: direction offset with height → equivalent yaw error per blade (#79)
        # Stability × Ekman coupling (#111): veer rate scales with atmospheric
        # stability (Holton 5.3, Stull 8.5, van der Laan 2017). Stable ABL
        # (s<0) preserves the Ekman spiral → strong veer; convective ABL (s>0)
        # mixes it out → weak veer. Per-turbine offset stays as site/manufacturing
        # variance on top of the atmospheric trend.
        veer_base = self._individuality.get("wind_veer_rate", 0.10)
        veer_factor = max(0.3, min(2.5, 1.0 - 1.0 * self._atm_stability))
        veer_rate = veer_base * veer_factor
        if is_producing and omega_rad > 0.1 and veer_rate > 0:
            veer_power_loss = 0.0
            for i in range(3):
                blade_az = (self._rotor_azimuth + i * math.tau / 3.0) % math.tau
                veer_offset_rad = math.radians(veer_rate * R * math.cos(blade_az))
                veer_power_loss += (1.0 - math.cos(veer_offset_rad) ** 2) / 3.0
            aero_out.aero_torque_knm *= (1.0 - veer_power_loss)
            aero_out.power_kw *= (1.0 - veer_power_loss)

        # Blade mass imbalance: centrifugal force F = Δm × r_cg × ω² (#72)
        blade_mass_offsets = self._individuality["blade_mass_offsets"]
        blade_mass_kg = 4000.0 * (R / 35.0) ** 2.5
        r_cg = R / 3.0
        omega_sq = omega_rad ** 2
        imb_fx = 0.0
        imb_fy = 0.0
        for i in range(3):
            dm = blade_mass_offsets[i] * blade_mass_kg
            blade_az = (self._rotor_azimuth + i * math.tau / 3.0) % math.tau
            imb_fx += dm * r_cg * omega_sq * math.cos(blade_az)
            imb_fy += dm * r_cg * omega_sq * math.sin(blade_az)
        self._imbalance_force_kn = math.sqrt(imb_fx ** 2 + imb_fy ** 2) / 1000.0

        # Use new DrivetrainModel (#28) instead of inline dynamics
        (
            self.rotor_speed,
            gen_speed,
            drivetrain_loss_kw,
            brake_heat_kw,
            torsion_vib_lss,
            torsion_vib_hss,
        ) = self.drivetrain.step(
            aero_rotor_speed=aero_rotor_speed,
            current_rotor_speed=self.rotor_speed,
            aero_torque_knm=aero_out.aero_torque_knm,
            aero_load_factor=aero_out.aero_load_factor,
            dt=dt,
            is_producing=is_producing,
            is_starting=is_starting,
            is_normal_stop=is_normal_stop,
            is_emergency_stop=is_emergency_stop,
            ambient_temp=ambient_temp,
            gearbox_overheat_severity=next(
                (float(f.get("severity", 0.0)) for f in self.active_faults
                 if f.get("scenario_id") == "gearbox_overheat"),
                0.0,
            ),
        )
        # Combined torsion vibration (backward compatible single value)
        torsion_vib = torsion_vib_lss + torsion_vib_hss * 0.5

        # Use Cp-based power when producing, fallback to lookup otherwise
        if is_producing and aero_out.power_kw > 0:
            aerodynamic_power_kw = (
                aero_out.power_kw
                * fault_physics["power_scale"]
                * self._individuality["power_scale"]
                * grid_derate
            )
        else:
            aerodynamic_power_kw = (
                self.power_curve.get_power(effective_wind_speed)
                * fault_physics["power_scale"]
                * self._individuality["power_scale"]
                * grid_derate
            )
        # Allow brief overshoot matching power_curve Region 3 Cp-based output
        effective_limit = s.rated_power_kw * 1.04
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

        # Region 3: shorter ramp tau (2s) lets pitch-lag power variation pass through;
        # Region 2: keep 4s to smooth partial-load transitions
        region3 = is_producing and effective_wind_speed >= s.rated_speed
        ramp_tau = 2.0 if region3 else 4.0 if is_producing else 2.0
        if is_normal_stop:
            ramp_tau = 2.0
        elif is_emergency_stop:
            ramp_tau = 0.35
        alpha = 1.0 - math.exp(-dt / ramp_tau)
        self._generated_power_kw += (target_power_kw - self._generated_power_kw) * alpha
        gen_power_kw = max(0.0, self._generated_power_kw)

        self._calc_pitch(effective_wind_speed, is_producing, dt)
        self._pitch_bl[0] += fault_physics["blade1_pitch_bias"]

        # For direct-drive PMSG, the converter outputs grid frequency regardless of rotor speed
        mechanical_freq = (gen_speed * s.generator_poles / 2) / 60.0 if (is_producing or is_starting) else 0.0
        if s.gear_ratio <= 1.0:
            # Direct-drive: converter always outputs grid frequency when producing
            target_freq = self._grid_frequency_ref if (is_producing or is_starting) else 0.0
        else:
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
        cnv_gn_pwr = gen_power_kw
        converter_eff = (0.985 if is_producing else 0.95) - (self._individuality["converter_loss_scale"] - 1.0) * 0.02
        converter_eff = max(0.90, min(0.992, converter_eff))
        cnv_gd_pwr = gen_power_kw * converter_eff

        # Electrical response model: frequency-watt, reactive power, ride-through
        elec_out = self.electrical.step(
            gen_power_kw=cnv_gd_pwr,
            grid_frequency_hz=self._grid_frequency_ref,
            grid_voltage_v=self._grid_voltage_ref,
            nominal_freq_hz=s.grid_frequency_nominal,
            nominal_voltage_v=s.nominal_voltage,
            rated_power_kw=s.rated_power_kw,
            dt=dt,
            is_producing=is_producing,
            is_starting=is_starting,
        )

        # Apply frequency-watt derate to grid-side power
        if is_producing:
            cnv_gd_pwr = elec_out["active_power_kw"]

        # Check ride-through trip
        elec_trip = self.electrical.should_trip()
        if elec_trip and self.tur_state not in (7, 9, 1):
            self.cmd_emergency_stop(cause=f"ride_through:{elec_trip}")

        reactive_power_kvar = elec_out["reactive_power_kvar"]
        power_factor = elec_out["power_factor"]
        apparent_power_kva = elec_out["apparent_power_kva"]

        gen_current = (
            apparent_power_kva * 1000 / (gen_voltage * math.sqrt(3))
            if gen_voltage > 0 and apparent_power_kva > 0 else 0.0
        )
        if is_producing:
            cnv_dc_vtg = 1100.0
        elif is_starting:
            cnv_dc_vtg = 900.0 + self._sync_progress * 200.0
        else:
            cnv_dc_vtg = 0.0

        yaw_out = self.yaw.step(wind_direction, is_producing, dt)
        yaw_out["yaw_error"] += fault_physics["yaw_error_bias"] + self._individuality["yaw_sensor_bias"]
        yaw_out["brake_pressure"] += fault_physics["yaw_brake_bias"]

        # Coolant leak from converter_cooling_fault (#75)
        leak_rate = fault_physics.get("coolant_leak_lph", 0.0)
        self.cooling.water_loop.set_leak_rate(leak_rate)

        # Cooling system model (#29) — produces cooling_bias for thermal model.
        # Humidity (#89) derates air-cooled paths via density + condensation.
        cooling_bias = self.cooling.step(
            gen_power_kw, ambient_temp, effective_wind_speed, dt,
            turbine_running=is_producing,
            ambient_humidity_pct=ambient_humidity_pct,
        )
        # Merge fault cooling bias (multiplicative)
        for key in cooling_bias:
            cooling_bias[key] *= fault_physics["cooling_bias"].get(key, 1.0)

        # Separate main bearing and gearbox bearing heat (#28)
        main_brg_heat = self.drivetrain.main_bearing_heat_kw
        gbx_brg_heat = self.drivetrain.gearbox_bearing_heat_kw

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
                "bearing": main_brg_heat + gbx_brg_heat * 0.6,
                "rotor": brake_heat_kw * 0.30,
                "hub": brake_heat_kw * 0.24,
                "nacelle": brake_heat_kw * 0.10 + gbx_brg_heat * 0.4,
                "converter": max(0.0, cnv_gn_pwr - cnv_gd_pwr),
            },
            cooling_bias=cooling_bias,
        )

        vib_x, vib_y = self.vibration.step(
            self.rotor_speed, effective_wind_speed, gen_power_kw,
            turbulence=0.1, dt=dt
        )
        # Aero-load coupling into vibration (#27): thrust transients cause nacelle vibration
        vib_x += torsion_vib * 0.85 + aero_out.thrust_kn * 0.0008
        vib_y += torsion_vib * 0.55
        # HSS torsional mode adds higher-frequency vibration component
        vib_x += torsion_vib_hss * 0.35
        vib_y += torsion_vib_hss * 0.20
        vib_x += fault_physics["vibration_x"]
        vib_y += fault_physics["vibration_y"]
        if is_normal_stop:
            vib_x += 0.35 + abs(self._rng.normal(0, 0.12))
            vib_y += 0.30 + abs(self._rng.normal(0, 0.12))
        elif is_emergency_stop:
            vib_x += 1.30 + abs(self._rng.normal(0, 0.45))
            vib_y += 1.10 + abs(self._rng.normal(0, 0.40))

        # Spectral vibration bands (frequency decomposition + fault signatures)
        vib_bands = self.vib_spectral.step(
            rotor_speed_rpm=self.rotor_speed,
            wind_speed=effective_wind_speed,
            power_kw=gen_power_kw,
            rated_power_kw=s.rated_power_kw,
            turbulence=0.1,
            dt=dt,
            active_faults=self.active_faults,
            imbalance_force_kn=self._imbalance_force_kn,
            tooth_wear_index=self.drivetrain.tooth_wear_index,
            mesh_stiffness_ripple=self.drivetrain.mesh_stiffness_variation,
        )

        # Vibration alarm thresholds (local feature)
        vib_alarms = self.vib_spectral.compute_alarms(
            bands=vib_bands,
            rotor_speed_rpm=self.rotor_speed,
            power_kw=gen_power_kw,
            rated_power_kw=s.rated_power_kw,
            dt=dt,
        )

        # Fatigue / structural load tracking (cloud feature)
        fatigue_out = self.fatigue.step(
            dt=dt,
            wind_speed=effective_wind_speed,
            rotor_speed_rpm=self.rotor_speed,
            power_kw=gen_power_kw,
            pitch_angle_deg=self._pitch_bl[0],
            yaw_error_deg=yaw_out["yaw_error"],
            thrust_kn=aero_out.thrust_kn,
            turbulence_intensity=0.1,
            is_producing=is_producing,
            is_starting=is_starting,
            is_emergency_stop=is_emergency_stop,
            rotor_azimuth_rad=self._rotor_azimuth,
            wind_shear_exponent=self._effective_shear_alpha,
            imbalance_force_kn=self._imbalance_force_kn,
            wind_veer_rate=veer_rate,
        )

        # IGCT water pressure now driven by cooling system pump (#29)
        water_pres = self.cooling.water_loop.pressure_bar
        if is_producing:
            igct_pres1 = water_pres * 1.0 + self._rng.normal(0, 0.08)
            igct_pres2 = water_pres * 0.94 + self._rng.normal(0, 0.08)
            igct_cond = min(1.0, self.cooling.water_loop.flow_lpm / max(self.cooling.spec.pump_flow_rated_lpm, 1.0))
        elif is_starting:
            igct_pres1 = water_pres * 0.7 + self._sync_progress * 0.8 + self._rng.normal(0, 0.05)
            igct_pres2 = water_pres * 0.65 + self._sync_progress * 0.7 + self._rng.normal(0, 0.05)
            igct_cond = 0.65 + self._sync_progress * 0.35
        else:
            igct_pres1 = water_pres * 0.3 if is_normal_stop else 0.1 if is_emergency_stop else 0.0
            igct_pres2 = water_pres * 0.25 if is_normal_stop else 0.05 if is_emergency_stop else 0.0
            igct_cond = 0.2 if is_normal_stop else 0.0

        rotor_locked = 1 if self.tur_state in (1, 2, 3) else 0
        brake_active = 1 if self.tur_state in (1, 7, 9) else 0

        # ── Nacelle Anemometer Transfer Function (#117, IEC 61400-12-1 Annex D) ──
        # ── + Glauert yaw skewed-flow correction (#125, Burton et al. 2011 §3.10) ──
        # Real cup/sonic anemometer sits ~1.5R behind hub on top of nacelle, so it
        # reads systematically below free-stream because of axial induction.
        # a = 0.5(1 − √(1 − Ct)) (1-D momentum theory); k_pos≈0.55 weights the
        # induction at the anemometer position. Under yaw misalignment γ the rotor
        # blocks less axial flow, so induction follows Glauert/Coleman skewed-wake:
        # a_skew = a · cos²(γ).  γ clamped to ±45° (validity of skewed-momentum).
        # Stopped/parked rotor sees a small bluff-body speed-up (+4%) instead.
        ct_clip = max(0.0, min(0.95, aero_out.ct))
        induction_a = 0.5 * (1.0 - math.sqrt(1.0 - ct_clip)) if ct_clip > 0 else 0.0
        gamma_deg = max(-45.0, min(45.0, yaw_out["yaw_error"]))
        cos_gamma = math.cos(math.radians(gamma_deg))
        if (is_producing or is_starting) and self.rotor_speed > 1.0:
            ntf_factor = 1.0 - 0.55 * induction_a * cos_gamma * cos_gamma
        else:
            ntf_factor = 1.04
        ntf_factor = max(0.78, min(1.10, ntf_factor))
        nac_anem_raw = effective_wind_speed * ntf_factor

        # ── Nacelle Wind Vane Transfer Function (#119, IEC 61400-12-2 Annex E) ──
        # ── + yaw projection (#125, Burton et al. 2011 §3.7 + projection geometry) ──
        # Real wind vane on top of nacelle reads systematic swirl bias from rotor wake.
        # θ_swirl ≈ Ct / (2·λ) [rad] (Burton et al. 2011, Wind Energy Handbook §3.7).
        # Right-handed rotor (industry standard, clockwise from upwind) → +bias.
        # Under yaw γ, the swirl vector projects onto the nacelle plane → ×cos(γ).
        if (is_producing or is_starting) and self.rotor_speed > 1.0 and aero_out.tsr > 1.0:
            swirl_rad = (ct_clip / (2.0 * aero_out.tsr)) * cos_gamma
            vane_bias_deg = math.degrees(swirl_rad)
        else:
            vane_bias_deg = 0.0
        vane_bias_deg = max(-8.0, min(8.0, vane_bias_deg))
        nac_vane_raw = (wind_direction + vane_bias_deg) % 360.0

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
            "WMET_HumOutside": round(self.cooling.last_ambient_humidity, 2),
            "WMET_LocalTi": round(self._local_ti_multiplier * 100.0, 1),
            "WMET_WakeDef": round(self._wake_deficit * 100.0, 2),
            "WMET_WakeMndr": round(self._wake_meander_offset_m, 2),
            "WMET_WakeDefl": round(self._wake_yaw_deflection_m, 2),
            "WMET_WakeTi": round(self._wake_added_ti * 100.0, 2),
            "WMET_ShearAlpha": round(self._effective_shear_alpha, 4),
            "WMET_AtmStab": round(self._atm_stability, 3),
            "WMET_AirDensity": round(self._air_density, 4),
            "WMET_AmbPressure": round(self._ambient_pressure_pa / 100.0, 1),
            "WMET_WSpeedRaw": round(nac_anem_raw, 2),
            "WMET_WDirRaw": round(nac_vane_raw, 2),
            "WNAC_NacTmp": temps["nacelle"],
            "WNAC_NacCabTmp": temps["nac_cabinet"],
            "WNAC_VibMsNacXDir": round(vib_x, 3),
            "WNAC_VibMsNacYDir": round(vib_y, 3),
            "WYAW_YwVn1AlgnAvg5s": round(yaw_out["yaw_error"], 2),
            "WYAW_YwBrkHyPrs": round(max(0, yaw_out["brake_pressure"]), 2),
            "WYAW_CabWup": round(yaw_out["cable_windup"], 2),
            "WSRV_SrvOn": 1.0 if self.service_mode else 0.0,
            "MBUS_Contact2": 1.0 if self.local_control else 0.0,
            # ── Drivetrain tags ──
            "WDRV_GbxOilTmp": round(self.drivetrain.oil_temperature, 2),
            "WDRV_GbxToothWear": round(self.drivetrain.tooth_wear_index * 100.0, 3),
            # ── Electrical response tags ──
            "WCNV_ReactPwr": round(reactive_power_kvar, 2),
            "WCNV_PwrFactor": round(power_factor, 4),
            "WCNV_AppPwr": round(apparent_power_kva, 2),
            "WCNV_FreqWattDerate": round(elec_out["freq_watt_derate"], 4),
            "WCNV_InertiaPwr": round(elec_out["inertia_power_kw"], 2),
            "WCNV_CnvMode": float({"idle": 0, "starting": 1, "normal": 2,
                                    "freq_response": 3, "voltage_support": 4,
                                    "ride_through": 5}.get(elec_out["converter_mode"], 0)),
            "WCNV_RtBand": float(elec_out["ride_through_band"]),
            # ── Vibration spectral band tags ──
            "WVIB_Band1pX": round(vib_bands.band_1p_x, 4),
            "WVIB_Band1pY": round(vib_bands.band_1p_y, 4),
            "WVIB_Band3pX": round(vib_bands.band_3p_x, 4),
            "WVIB_Band3pY": round(vib_bands.band_3p_y, 4),
            "WVIB_BandGearX": round(vib_bands.band_gear_x, 4),
            "WVIB_BandGearY": round(vib_bands.band_gear_y, 4),
            "WVIB_BandHfX": round(vib_bands.band_hf_x, 4),
            "WVIB_BandHfY": round(vib_bands.band_hf_y, 4),
            "WVIB_BandBbX": round(vib_bands.band_bb_x, 4),
            "WVIB_BandBbY": round(vib_bands.band_bb_y, 4),
            "WVIB_CrestFactor": round(vib_bands.crest_factor, 3),
            "WVIB_Kurtosis": round(vib_bands.kurtosis, 3),
            # ── Vibration alarm threshold tags (local feature) ──
            "WVIB_Alarm1p": float(vib_alarms.alarm_1p),
            "WVIB_Alarm3p": float(vib_alarms.alarm_3p),
            "WVIB_AlarmGear": float(vib_alarms.alarm_gear),
            "WVIB_AlarmHf": float(vib_alarms.alarm_hf),
            "WVIB_AlarmBb": float(vib_alarms.alarm_bb),
            "WVIB_AlarmCrest": float(vib_alarms.alarm_crest),
            "WVIB_AlarmKurt": float(vib_alarms.alarm_kurtosis),
            "WVIB_AlarmOverall": float(vib_alarms.alarm_overall),
            "WVIB_Thresh1pWarn": round(vib_alarms.thresh_1p_warn, 4),
            "WVIB_Thresh1pAlrm": round(vib_alarms.thresh_1p_alrm, 4),
            "WVIB_BpfoFreq": round(vib_bands.bpfo_freq, 2),
            "WVIB_BpfiFreq": round(vib_bands.bpfi_freq, 2),
            "WVIB_BpfoAmp": round(vib_bands.bpfo_amp, 4),
            "WVIB_BpfiAmp": round(vib_bands.bpfi_amp, 4),
            "WVIB_GmfFreq": round(vib_bands.gmf_freq, 2),
            "WVIB_Sideband1Amp": round(vib_bands.sideband_1_amp, 4),
            "WVIB_Sideband2Amp": round(vib_bands.sideband_2_amp, 4),
            "WVIB_SidebandRatio": round(vib_bands.sideband_ratio, 4),
            # ── Fatigue / structural load tags (cloud convention) ──
            "WLOD_TwrFaMom": fatigue_out["tower_fa_moment_knm"],
            "WLOD_TwrSsMom": fatigue_out["tower_ss_moment_knm"],
            "WLOD_BldFlapMom": fatigue_out["blade_flap_moment_knm"],
            "WLOD_BldEdgeMom": fatigue_out["blade_edge_moment_knm"],
            "WLOD_DelTwrFa": fatigue_out["del_tower_fa_knm"],
            "WLOD_DelTwrSs": fatigue_out["del_tower_ss_knm"],
            "WLOD_DelBldFlap": fatigue_out["del_blade_flap_knm"],
            "WLOD_DelBldEdge": fatigue_out["del_blade_edge_knm"],
            "WLOD_DmgTwrFa": fatigue_out["damage_tower_fa"],
            "WLOD_DmgTwrSs": fatigue_out["damage_tower_ss"],
            "WLOD_DmgBldFlap": fatigue_out["damage_blade_flap"],
            "WLOD_DmgBldEdge": fatigue_out["damage_blade_edge"],
            "WLOD_ProdHours": fatigue_out["production_hours"],
            "WLOD_AlmTwr": fatigue_out["alarm_level_tower"],
            "WLOD_AlmBld": fatigue_out["alarm_level_blade"],
            "WLOD_RulHours": fatigue_out["rul_hours"],
            # ── Rotor imbalance tag (#72) ──
            "WROT_ImbForce": round(self._imbalance_force_kn, 4),
            # ── Coolant level tags (#75) ──
            "WCOL_CoolantLvl": round(self.cooling.water_loop.coolant_level_pct, 1),
            "WCOL_CoolantAlm": float(self.cooling.water_loop.coolant_alarm_level),
        }

        # NOTE: fault_modifiers tag-offset path has been removed.
        # All fault effects now flow through _get_fault_physics() which
        # modifies physical causes (heat, friction, wind, cooling, pitch)
        # with operating-condition coupling. This ensures ML models must
        # learn physically grounded fault signatures.

        return self._apply_sensor_model(output)

    def _max_restarts_exceeded(self) -> bool:
        """Z72: Check if max restarts per hour has been exceeded."""
        cutoff = self._sim_time - 3600.0
        self._restart_timestamps = [t for t in self._restart_timestamps if t > cutoff]
        return len(self._restart_timestamps) >= self.spec.max_restarts_per_hour

    def _update_state(self, wind_speed: float, dt: float):
        s = self.spec
        st = self.tur_state
        wind_ok = s.cut_in_speed <= wind_speed <= s.cut_out_speed
        strong_wind = wind_speed >= s.cut_in_speed + 0.6
        # Z72 direct-drive: converter decouples gen freq from grid freq.
        # For direct-drive (gear_ratio <= 1), sync is based on rotor speed threshold.
        # For geared turbines, sync requires frequency/voltage matching.
        if s.gear_ratio <= 1.0:
            # Direct-drive: converter ready when rotor reaches ~6 RPM (Z72 OEM spec)
            sync_ok = self.rotor_speed >= 6.0
        else:
            gen_mech_freq = (self.rotor_speed * s.gear_ratio * s.generator_poles / 2) / 60.0 if self.rotor_speed > 0 else 0.0
            sync_ok = (
                abs(self._grid_frequency_ref - gen_mech_freq) < 0.25
                and abs(self._grid_voltage_ref - self._grid_voltage) < 25.0
            )

        self._state_timer += dt
        self._restart_block_timer = max(0.0, self._restart_block_timer - dt)
        if wind_ok and strong_wind:
            self._wind_ready_timer += dt
        else:
            self._wind_ready_timer = 0.0

        # Z72: Software overspeed protection (Event 041 / 027)
        if self.rotor_speed > s.overspeed_software_rpm and st not in (7,):
            self._request_stop("emergency", "overspeed_software")
        if self.rotor_speed > s.overspeed_hardware_rpm and st not in (7,):
            self._request_stop("emergency", "overspeed_hardware")

        if self.operator_stop or self.service_mode:
            self._request_stop("normal", "operator")
        if wind_speed > s.cut_out_speed + 0.5:
            self._request_stop("emergency", "cut_out")

        if self._stop_requested and st not in (7, 9):
            self._enter_state(9 if self._stop_mode == "normal" else 7)
            st = self.tur_state

        if self.operator_start_pending and st in (1, 2, 3) and wind_ok and self._restart_block_timer <= 0.0:
            if not self._max_restarts_exceeded():
                self.operator_start_pending = False
                self._restart_timestamps.append(self._sim_time)
                self._enter_state(8 if st == 3 else 4)
                st = self.tur_state

        if st == 1:
            self._sync_progress = 0.0
            if wind_ok and not self._max_restarts_exceeded():
                self._enter_state(2)
        elif st == 2:
            if not wind_ok:
                self._enter_state(1)
            elif self._max_restarts_exceeded():
                pass  # Z72: stay in standby if max restarts exceeded
            elif not self.operator_stop and self._wind_ready_timer >= 10.0 + self._individuality["start_delay_offset"] and self._restart_block_timer <= 0.0:
                self._restart_timestamps.append(self._sim_time)
                self._enter_state(4)
        elif st == 3:
            self._restart_wait_timer += dt
            restart_delay = (
                8.0
                + self._individuality["restart_delay_offset"]
                + max(0.0, self._individuality["grid_reconnect_delay"])
            )
            if self._max_restarts_exceeded():
                # Z72: max restarts exceeded → go to Shutdown (state 1)
                self._enter_state(1)
            elif self._restart_wait_timer >= restart_delay and wind_ok and not self.operator_stop and not self.service_mode and self._restart_block_timer <= 0.0:
                self._enter_state(2)
        elif st == 4:
            # Z72 Pre-Production: converter to standby, yaw to auto
            if not wind_ok:
                self._request_stop("normal", "low_wind")
            elif self._state_timer >= 3.0:
                self._enter_state(5)
        elif st == 5:
            # Z72 Start Production: blades to startup (30°), then to work when rotor > 3.5 rpm
            self._sync_progress = min(1.0, self._state_timer / 7.0)
            if not wind_ok:
                self._request_stop("normal", "low_wind")
            # Z72: rotor > 3.5 rpm → blades move to work; rotor > 6.0 rpm → converter production
            elif self.rotor_speed >= 3.5 and self._state_timer >= 7.0 and sync_ok:
                self._enter_state(6)
        elif st == 6:
            self._sync_progress = 1.0
            if wind_speed < s.cut_in_speed - 0.3:
                self._request_stop("normal", "below_cut_in")
            elif wind_speed > s.cut_out_speed:
                self._request_stop("emergency", "cut_out")
        elif st == 7:
            # Z72 Emergency Stop: blades go to vane (86°) via emergency pitch
            if self.rotor_speed < 0.3 and self._state_timer >= 4.0:
                self._stop_requested = False
                self._enter_state(3)
        elif st == 8:
            if wind_ok and self._restart_block_timer <= 0.0 and not self._max_restarts_exceeded():
                self._restart_timestamps.append(self._sim_time)
                self._enter_state(4)
            else:
                self._enter_state(3)
        elif st == 9:
            # Z72 Normal Stop: blades to vane via servo
            if self.rotor_speed < 0.3 and self._state_timer >= 12.0:
                self._stop_requested = False
                self._enter_state(1)

    def _calc_pitch(self, wind_speed: float, is_producing: bool, dt: float):
        """Z72 pitch control with real setpoints from OEM manual.

        Angles:  vane=86°, startup=30°, work=-1°
        Emergency pitch: battery-driven DC motor, min 5°/s
        Normal servo: DC servo motor per blade
        """
        s = self.spec
        max_rate = 8.0 * self._individuality["pitch_response_scale"]

        if self.tur_state == 7:
            # Z72 Emergency: batteries drive blades to vane (86°)
            target = s.pitch_vane
            max_rate = max(s.pitch_emergency_rate, 18.0)  # emergency pitch speed
        elif self.tur_state == 9:
            # Z72 Normal Stop: servo drives blades to vane (86°)
            target = s.pitch_vane
            max_rate = 10.0
        elif self.tur_state == 4:
            # Z72 Pre-Production: blades stay near vane, preparing
            target = s.pitch_vane - 10.0  # ~76°, slight move from vane
            max_rate = 6.0
        elif self.tur_state == 5:
            # Z72 Start Production: blades go to startup (30°), then to work as rotor spins up
            if self._sync_progress < 0.4:
                target = s.pitch_startup  # 30°
            else:
                # Transition from startup to work position
                target = s.pitch_startup - self._sync_progress * (s.pitch_startup - s.pitch_work)
            max_rate = 7.5
        elif not is_producing:
            # Z72 Standby/Shutdown: blades at vane
            target = s.pitch_vane
        elif wind_speed < s.rated_speed:
            # Z72 Region 2 (partial load): pitch at work position for max Cp
            target = s.pitch_work  # -1°
        else:
            # Z72 Region 3 (full load): pitch to limit power
            excess_wind = wind_speed - s.rated_speed
            target = max(s.pitch_work, s.pitch_work + excess_wind * 2.0 + excess_wind ** 2 * 0.1)
            target = min(30.0, target)

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
        """Force the turbine into a specific state (1-9) for testing purposes."""
        if 1 <= state <= 9:
            self._enter_state(state)

    def cmd_stop(self):
        """Request a normal (controlled) shutdown initiated by the operator."""
        self.operator_stop = True
        self.operator_start_pending = False
        self._request_stop("normal", "operator")

    def cmd_start(self):
        """Request turbine startup; clears stop and service flags."""
        self.operator_stop = False
        self.service_mode = False
        self.operator_start_pending = True

    def cmd_reset(self):
        """Reset turbine to idle state, clearing all faults and control flags."""
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
        self.drivetrain.reset()
        if self.tur_state in (3, 7, 8, 9):
            self._enter_state(1)

    def cmd_service(self, on: bool):
        """Enter or exit service/maintenance mode."""
        self.service_mode = on
        if on:
            self.operator_stop = False
            self._request_stop("normal", "service")

    def cmd_curtail(self, power_kw: Optional[float]):
        """Set or clear power curtailment limit in kW."""
        self.curtailment_kw = power_kw

    def cmd_emergency_stop(self, cause: str = "emergency"):
        """Trigger immediate emergency stop with rapid braking."""
        self.operator_start_pending = False
        self._request_stop("emergency", cause)

    def get_control_status(self) -> dict:
        """Return current control flags and operational state summary."""
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
        """Full reset of turbine physics state to initial idle conditions."""
        self.tur_state = 1
        self.rotor_speed = 0.0
        self.pitch_angle = self.spec.pitch_vane  # Z72: vane position (86°)
        self._pitch_bl = [self.spec.pitch_vane] * 3
        self._rotor_azimuth = self._rng.uniform(0.0, math.tau)
        self._imbalance_force_kn = 0.0
        self._local_ti_multiplier = 1.0
        self._wake_deficit = 0.0
        self._wake_meander_offset_m = 0.0
        self._wake_yaw_deflection_m = 0.0
        # Wake-added TI fraction (Crespo-Hernández) — combined upstream contribution (#103)
        self._wake_added_ti = 0.0
        # Atmospheric stability coupling (#99): α is farm-level time-varying,
        # applied with per-turbine permanent offset from individuality.
        self._effective_shear_alpha = 0.2 + self._individuality.get("wind_shear_exp_offset", 0.0)
        self._atm_stability = 0.0
        # Air density ρ(T, RH, P) — updated per step from ambient temp + humidity + pressure (#101, #106)
        self._air_density = self.spec.air_density
        self._ambient_pressure_pa = 101325.0
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
        self._grid_frequency_ref = self.spec.grid_frequency_nominal
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
        self.drivetrain.reset()
        self.cooling.reset()
        self.electrical.reset()

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
        freq_base = self.spec.grid_frequency_nominal + 0.08 * math.sin(self._grid_phase) + self._rng.normal(0.0, 0.01)
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
        freq_dev = abs(self._grid_frequency_ref - self.spec.grid_frequency_nominal)
        volt_dev = abs(self._grid_voltage_ref - self.spec.nominal_voltage)
        nom_volt = self.spec.nominal_voltage
        sensitivity = self._individuality["grid_derate_sensitivity"]
        freq_scale = 1.0 if freq_dev < 0.15 else max(0.72, 1.0 - (freq_dev - 0.15) * 0.45 * sensitivity)
        # Voltage derate relative to nominal (works for both 690V and 3500V)
        volt_pct_dev = volt_dev / nom_volt  # fraction of nominal
        volt_scale = 1.0 if volt_pct_dev < 0.03 else max(0.68, 1.0 - (volt_pct_dev - 0.03) * 3.5 * sensitivity)
        return min(freq_scale, volt_scale)

    def _check_grid_trip(self) -> Optional[str]:
        freq = self._grid_frequency_ref
        volt = self._grid_voltage_ref
        hz_margin = self._individuality["grid_trip_margin_hz"]
        volt_margin = self._individuality["grid_trip_margin_v"]
        nom_freq = self.spec.grid_frequency_nominal
        nom_volt = self.spec.nominal_voltage

        # Grid protection limits relative to nominal (works for 50Hz/690V and 60Hz/3500V)
        severe_limit = (
            freq < nom_freq - 1.4 + hz_margin        # e.g. 60 Hz → < 58.6 Hz
            or freq > nom_freq + 1.4 - hz_margin      # e.g. 60 Hz → > 61.4 Hz
            or volt < nom_volt * 0.81 + volt_margin    # e.g. 3500V → < 2835V
            or volt > nom_volt * 1.15 - volt_margin    # e.g. 3500V → > 4025V
        )
        normal_limit = (
            freq < nom_freq - 1.0 + hz_margin
            or freq > nom_freq + 1.0 - hz_margin
            or volt < nom_volt * 0.87 + volt_margin
            or volt > nom_volt * 1.10 - volt_margin
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

    def _apply_sensor_model(self, output: Dict[str, float]) -> Dict[str, float]:
        # Tags that should not be filtered through the sensor model
        _integer_tags = {"WTUR_TurSt", "WCNV_CnvMode", "WCNV_RtBand",
                         "WROT_RotLckd", "WROT_SrvcBrkAct", "WROT_LckngPnPos",
                         "WSRV_SrvOn", "MBUS_Contact2",
                         # Vibration alarm levels (discrete integers)
                         "WVIB_Alarm1p", "WVIB_Alarm3p", "WVIB_AlarmGear",
                         "WVIB_AlarmHf", "WVIB_AlarmBb",
                         "WVIB_AlarmCrest", "WVIB_AlarmKurt", "WVIB_AlarmOverall",
                         # Fatigue alarm levels (discrete integers)
                         "WLOD_AlmTwr", "WLOD_AlmBld"}
        # Computed metrics — pass through without sensor noise
        _passthrough_tags = {"WLOD_DmgTwrFa", "WLOD_DmgTwrSs", "WLOD_DmgBldFlap",
                             "WLOD_DmgBldEdge", "WLOD_ProdHours",
                             "WLOD_DelTwrFa", "WLOD_DelTwrSs",
                             "WLOD_DelBldFlap", "WLOD_DelBldEdge",
                             "WVIB_Thresh1pWarn", "WVIB_Thresh1pAlrm",
                             "WLOD_RulHours"}
        sensorized: Dict[str, float] = {}
        for tag, value in output.items():
            if tag in _integer_tags:
                sensorized[tag] = round(value)
                continue
            if tag in _passthrough_tags:
                sensorized[tag] = value
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
        # Electrical response tags — small noise, no stuck
        if tag == "WCNV_PwrFactor":
            return {"noise": 0.003, "drift": 0.0001, "bias_limit": 0.01, "resolution": 0.001, "stuck_prob": 0.0, "min": -1.0, "max": 1.0}
        if tag in ("WCNV_FreqWattDerate",):
            return {"noise": 0.002, "drift": 0.0001, "bias_limit": 0.005, "resolution": 0.001, "stuck_prob": 0.0, "min": 0.0, "max": 1.0}
        # Structural load moment tags — small noise, clamped to 0
        if tag.startswith("WLOD_Twr") or tag.startswith("WLOD_Bld"):
            return {"noise": 5.0, "drift": 0.05, "bias_limit": 15.0, "resolution": 0.1, "stuck_prob": 0.00005, "min": 0.0, "max": 50000.0}
        # Fatigue load tags (legacy WFAT support if needed)
        if tag.startswith("WFAT_TwrBs") or tag.startswith("WFAT_BldRt"):
            return {"noise": 2.0, "drift": 0.05, "bias_limit": 8.0, "resolution": 0.1, "stuck_prob": 0.0001, "min": 0.0, "max": 10000.0}
        # Vibration spectral bands — similar to main vibration
        if tag.startswith("WVIB_Band") or tag.startswith("WVIB_Crest") or tag.startswith("WVIB_Kurt"):
            return {"noise": 0.005, "drift": 0.0003, "bias_limit": 0.05, "resolution": 0.001, "stuck_prob": 0.0001, "min": 0.0, "max": 30.0}
        if "Tmp" in tag:
            return {"noise": 0.12, "drift": 0.0015, "bias_limit": 1.0, "resolution": 0.1, "stuck_prob": 0.00012, "min": -40.0, "max": 180.0}
        if "Spd" in tag or "Frq" in tag:
            return {"noise": 0.04, "drift": 0.0008, "bias_limit": 0.25, "resolution": 0.01, "stuck_prob": 0.0001, "min": 0.0, "max": 5000.0}
        if "Vtg" in tag:
            return {"noise": 1.5, "drift": 0.01, "bias_limit": 6.0, "resolution": 0.1, "stuck_prob": 0.00005, "min": 0.0, "max": 5000.0}
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
        """Compute physical effects of all active faults.

        All fault effects flow through physical causes (heat, friction, wind,
        pitch, cooling) rather than direct tag offsets. Effects scale with
        current operating conditions so ML models must learn to separate
        load-dependent fault signatures from normal operational variation.
        """
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
            "coolant_leak_lph": 0.0,
        }

        # Operating condition factors for load-dependent fault coupling.
        # Use previous-step values (available before current step computes).
        rated_pwr = max(self.spec.rated_power_kw, 1.0)
        power_ratio = max(0.0, min(1.0, self._generated_power_kw / rated_pwr))
        speed_ratio = max(0.0, min(1.0, self.rotor_speed / max(self.spec.max_rotor_rpm, 1.0)))
        load_factor = max(power_ratio, speed_ratio)  # general load indicator

        for fault in self.active_faults:
            severity = float(fault.get("severity", 0.0))
            scenario_id = fault.get("scenario_id")

            # ── bearing_wear ─────────────────────────────────────────
            # Bearing friction generates heat proportional to speed.
            # Vibration increases with both speed and load.
            if scenario_id == "bearing_wear":
                speed_coupling = 0.3 + 0.7 * speed_ratio
                load_coupling = 0.4 + 0.6 * load_factor
                fault_physics["extra_heat"]["bearing"] += 18.0 * severity * speed_coupling
                fault_physics["extra_heat"]["generator"] += 6.0 * severity * load_coupling
                fault_physics["vibration_x"] += 1.5 * severity * speed_coupling
                fault_physics["vibration_y"] += 1.2 * severity * speed_coupling

            # ── generator_overspeed ──────────────────────────────────
            # Control failure lets rotor accelerate. Worse at high wind.
            elif scenario_id == "generator_overspeed":
                fault_physics["rotor_speed_bias"] += 0.8 * severity
                fault_physics["vibration_x"] += 2.2 * severity * (0.5 + 0.5 * speed_ratio)
                fault_physics["vibration_y"] += 1.8 * severity * (0.5 + 0.5 * speed_ratio)
                fault_physics["extra_heat"]["generator"] += 8.0 * severity * (0.4 + 0.6 * load_factor)

            # ── converter_cooling_fault ──────────────────────────────
            # Cooling degradation. Heat accumulates faster at high power.
            elif scenario_id == "converter_cooling_fault":
                fault_physics["extra_heat"]["converter"] += 16.0 * severity * (0.3 + 0.7 * power_ratio)
                fault_physics["cooling_bias"]["water"] *= max(0.25, 1.0 - 0.70 * severity)
                fault_physics["cooling_bias"]["cabinet"] *= max(0.55, 1.0 - 0.35 * severity)
                fault_physics["power_scale"] *= max(0.82, 1.0 - 0.08 * severity)
                # O-ring degradation causes coolant leak proportional to severity
                fault_physics["coolant_leak_lph"] += 0.8 * severity

            # ── transformer_overheat ─────────────────────────────────
            # Transformer losses scale with power squared (I²R).
            elif scenario_id == "transformer_overheat":
                power_sq = power_ratio ** 2
                fault_physics["extra_heat"]["transformer"] += 18.0 * severity * (0.2 + 0.8 * power_sq)
                fault_physics["cooling_bias"]["transformer"] *= max(0.45, 1.0 - 0.40 * severity)
                fault_physics["extra_heat"]["nacelle"] += 2.5 * severity * (0.3 + 0.7 * power_ratio)

            # ── pitch_imbalance ──────────────────────────────────────
            # Blade 1 calibration drift. Causes 1P vibration (speed-dependent)
            # and aerodynamic power loss (wind-dependent).
            elif scenario_id == "pitch_imbalance":
                fault_physics["blade1_pitch_bias"] += 3.0 * severity
                fault_physics["power_scale"] *= max(0.88, 1.0 - 0.04 * severity * load_factor)
                fault_physics["vibration_x"] += 1.5 * severity * speed_ratio
                fault_physics["vibration_y"] += 0.8 * severity * speed_ratio
                fault_physics["extra_heat"]["bearing"] += 3.0 * severity * speed_ratio

            # ── yaw_sensor_drift ─────────────────────────────────────
            # Position sensor drifts. Power loss from misalignment is
            # proportional to cos(yaw_error) — more loss at higher wind.
            elif scenario_id == "yaw_sensor_drift":
                yaw_deg = 12.0 * severity
                fault_physics["yaw_error_bias"] += yaw_deg
                cos_loss = math.cos(math.radians(min(30.0, abs(yaw_deg))))
                fault_physics["wind_scale"] *= max(0.75, cos_loss)

            # ── stator_winding_degradation ───────────────────────────
            # Insulation resistance decreases. Extra I²R losses at load.
            # Temperature-vs-power slope changes — key ML feature.
            elif scenario_id == "stator_winding_degradation":
                power_sq = power_ratio ** 2
                fault_physics["extra_heat"]["generator"] += 20.0 * severity * (0.15 + 0.85 * power_sq)
                # Slight current increase from reduced insulation efficiency
                fault_physics["power_scale"] *= max(0.92, 1.0 - 0.03 * severity * power_ratio)

            # ── hydraulic_leak ───────────────────────────────────────
            # Slow pressure drop. Yaw slippage under high wind loads.
            # Yaw error variance increases with load (thrust force).
            elif scenario_id == "hydraulic_leak":
                fault_physics["yaw_brake_bias"] -= 80.0 * severity
                # Under load, thrust causes yaw slippage
                slip_amplitude = 5.0 * severity * load_factor
                fault_physics["yaw_error_bias"] += slip_amplitude * math.sin(self._sim_time * 0.08)

            # ── blade_icing ──────────────────────────────────────────
            # Aerodynamic imbalance. Power loss and asymmetric vibration.
            # Effect is independent of load (ice doesn't care about power)
            # but vibration couples with rotation speed.
            elif scenario_id == "blade_icing":
                fault_physics["power_scale"] *= max(0.60, 1.0 - 0.25 * severity)
                fault_physics["rotor_speed_bias"] -= 1.5 * severity
                fault_physics["vibration_x"] += 4.0 * severity * speed_ratio
                fault_physics["vibration_y"] += 6.0 * severity * speed_ratio  # asymmetric
                fault_physics["blade1_pitch_bias"] += 2.0 * severity

            # ── grid_voltage_sag ─────────────────────────────────────
            # Converter stress from grid fluctuations.
            # Switching losses increase, especially at high power.
            elif scenario_id == "grid_voltage_sag":
                fault_physics["extra_heat"]["converter"] += 8.0 * severity * (0.3 + 0.7 * power_ratio)
                fault_physics["power_scale"] *= max(0.80, 1.0 - 0.10 * severity * power_ratio)
                fault_physics["cooling_bias"]["cabinet"] *= max(0.75, 1.0 - 0.15 * severity)

            # ── nacelle_cooling_failure ───────────────────────────────
            # Main ventilation failure. Multiple components heat up.
            # Heat accumulation is proportional to power dissipation.
            elif scenario_id == "nacelle_cooling_failure":
                heat_scale = 0.25 + 0.75 * power_ratio
                fault_physics["cooling_bias"]["nacelle"] *= max(0.30, 1.0 - 0.55 * severity)
                fault_physics["cooling_bias"]["cabinet"] *= max(0.40, 1.0 - 0.45 * severity)
                fault_physics["extra_heat"]["nacelle"] += 15.0 * severity * heat_scale
                fault_physics["extra_heat"]["generator"] += 8.0 * severity * heat_scale
                fault_physics["extra_heat"]["converter"] += 6.0 * severity * heat_scale
                fault_physics["extra_heat"]["bearing"] += 4.0 * severity * heat_scale

            # ── legacy aliases (from older physics path) ─────────────
            elif scenario_id == "gearbox_overheat":
                fault_physics["extra_heat"]["nacelle"] += 10.0 * severity * (0.3 + 0.7 * load_factor)
                fault_physics["extra_heat"]["converter"] += 4.0 * severity * load_factor
                fault_physics["cooling_bias"]["nacelle"] *= max(0.55, 1.0 - 0.30 * severity)
                fault_physics["vibration_x"] += 0.8 * severity * speed_ratio
                fault_physics["vibration_y"] += 0.7 * severity * speed_ratio
            elif scenario_id == "pitch_motor_fault":
                fault_physics["blade1_pitch_bias"] += 8.0 * severity
                fault_physics["power_scale"] *= max(0.78, 1.0 - 0.10 * severity * load_factor)
                fault_physics["vibration_x"] += 0.9 * severity * speed_ratio
                fault_physics["vibration_y"] += 0.5 * severity * speed_ratio
            elif scenario_id == "yaw_misalignment":
                yaw_deg = 20.0 * severity
                fault_physics["yaw_error_bias"] += yaw_deg
                fault_physics["wind_scale"] *= max(0.72, math.cos(math.radians(min(35.0, abs(yaw_deg)))))
                fault_physics["yaw_brake_bias"] -= 25.0 * severity

        return fault_physics

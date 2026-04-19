"""
Drivetrain model with gearbox stages, bearing separation, torsional modes,
and brake pressure dynamics.

Replaces the inline drivetrain logic in turbine_physics.py with a
dedicated model that provides:

  - Multi-stage gearbox with per-stage gear ratio, efficiency, and inertia
  - Separate main bearing and gearbox bearing thermal/friction contributions
  - Two torsional modes (low-speed shaft and high-speed shaft)
  - Hydraulic brake pressure build-up dynamics
  - Aero-load coupling input from the Cp surface model

For direct-drive turbines (gear_ratio=1), the gearbox stages are bypassed
and the model reduces to a single-shaft system with main bearing only.
"""

import math
from dataclasses import dataclass, field
from typing import Tuple, Optional


@dataclass
class GearboxStageSpec:
    """Specification for a single gearbox stage."""
    ratio: float = 1.0
    efficiency: float = 0.985
    inertia_kgm2: float = 50.0


@dataclass
class DrivetrainSpec:
    """Drivetrain configuration parameters."""

    # Gearbox stages (empty list = direct-drive)
    gearbox_stages: list = field(default_factory=list)

    # Overall gear ratio (product of stage ratios, set automatically)
    total_gear_ratio: float = 1.0

    # Low-speed shaft (rotor side)
    lss_inertia_kgm2: float = 5_000_000.0
    lss_stiffness: float = 0.36
    lss_damping: float = 0.24

    # High-speed shaft (generator side, only for geared)
    hss_inertia_kgm2: float = 200.0
    hss_stiffness: float = 0.50
    hss_damping: float = 0.30

    # Main bearing (supports rotor)
    main_bearing_friction_coeff: float = 0.0012
    main_bearing_preload_kn: float = 50.0

    # Gearbox bearings (inside gearbox, only for geared)
    gearbox_bearing_friction_coeff: float = 0.0008
    gearbox_bearing_preload_kn: float = 20.0

    # Brake system
    brake_pressure_max_bar: float = 180.0
    brake_pressure_rise_rate: float = 25.0    # bar/s for normal stop
    brake_emergency_rise_rate: float = 90.0   # bar/s for emergency stop
    brake_pressure_release_rate: float = 40.0  # bar/s release
    brake_torque_per_bar: float = 0.15        # kNm per bar of pressure

    # Gear tooth contact (HSS pinion of last stage — dominant mesh excitation)
    hss_pinion_teeth: int = 23              # pinion teeth on high-speed pinion
    contact_ratio: float = 1.55             # typical helical ε_α ∈ [1.3, 1.8]
    mesh_stiffness_ripple_base: float = 0.04  # baseline ΔK/K at rated (healthy)
    tooth_wear_rate_per_hour: float = 3.5e-6  # wear index growth at rated (Δ/h)

    @classmethod
    def for_direct_drive(cls, **kwargs) -> "DrivetrainSpec":
        """Create a spec for direct-drive turbines (no gearbox)."""
        return cls(gearbox_stages=[], total_gear_ratio=1.0, **kwargs)

    @classmethod
    def for_geared(cls, overall_ratio: float = 104.5, **kwargs) -> "DrivetrainSpec":
        """Create a 3-stage gearbox typical for MW-class geared turbines."""
        # Typical split: planetary (1:~5) + planetary (1:~5) + helical (1:~4)
        r1 = round(overall_ratio ** (1 / 3) * 1.3, 1)  # stage 1 planetary
        r2 = round(overall_ratio ** (1 / 3) * 1.1, 1)  # stage 2 planetary
        r3 = round(overall_ratio / (r1 * r2), 2)        # stage 3 helical

        stages = [
            GearboxStageSpec(ratio=r1, efficiency=0.982, inertia_kgm2=120.0),
            GearboxStageSpec(ratio=r2, efficiency=0.985, inertia_kgm2=60.0),
            GearboxStageSpec(ratio=r3, efficiency=0.990, inertia_kgm2=25.0),
        ]
        return cls(
            gearbox_stages=stages,
            total_gear_ratio=r1 * r2 * r3,
            hss_inertia_kgm2=150.0,
            hss_stiffness=0.55,
            hss_damping=0.35,
            gearbox_bearing_preload_kn=30.0,
            **kwargs,
        )


class DrivetrainModel:
    """
    Multi-stage drivetrain model with torsional dynamics and brake hydraulics.
    """

    def __init__(self, spec: Optional[DrivetrainSpec] = None,
                 individuality: Optional[dict] = None):
        self.spec = spec or DrivetrainSpec()
        ind = individuality or {}

        self._stiffness_scale = ind.get("drivetrain_stiffness_scale", 1.0)
        self._damping_scale = ind.get("shaft_damping_scale", 1.0)
        self._normal_brake_scale = ind.get("normal_brake_scale", 1.0)
        self._emergency_brake_scale = ind.get("emergency_brake_scale", 1.0)
        self._bearing_friction_scale = ind.get("bearing_friction_scale", 1.0)

        self.is_geared = len(self.spec.gearbox_stages) > 0

        # Shaft state
        self._lss_twist = 0.0  # low-speed shaft torsional deflection
        self._hss_twist = 0.0  # high-speed shaft torsional deflection
        self._generator_speed = 0.0

        # Brake state
        self._brake_pressure = 0.0  # current brake pressure (bar)
        self._brake_command = "released"  # "released", "normal", "emergency"

        # Per-stage speed and loss tracking
        self._stage_speeds: list = []
        self._stage_losses_kw: list = []

        # Bearing heat outputs (for thermal model coupling)
        self.main_bearing_heat_kw = 0.0
        self.gearbox_bearing_heat_kw = 0.0

        # Gearbox oil temperature and viscosity state
        self._oil_temp = 25.0
        self._running_seconds = 0.0
        self._oil_temp_ref = 60.0  # reference temperature for viscosity ratio
        self._visc_alpha = -0.03   # Walther-type coefficient (1/°C)

        # Gear tooth contact state (#76)
        # Time-varying mesh stiffness comes from the cyclical alternation between
        # single-tooth contact (lower K) and double-tooth contact (higher K).
        # Contact ratio ε_α determines the fraction of time spent in each region.
        # Wear gradually flattens the load sharing, increasing ripple at GMF.
        self._mesh_phase = 0.0
        self._tooth_wear_index = 0.0  # 0 = new gears, 1 = failure threshold
        self._ripple_individuality = 1.0 + (
            ind.get("gear_mesh_ripple_scale", 1.0) - 1.0
        ) if "gear_mesh_ripple_scale" in ind else 1.0
        # gmf_excitation output (kNm) — contributes to HSS torsion excitation
        self.gmf_excitation_knm = 0.0

    @property
    def generator_speed(self) -> float:
        """Current generator speed in RPM."""
        return self._generator_speed

    @property
    def brake_pressure(self) -> float:
        """Current brake hydraulic pressure in bar."""
        return self._brake_pressure

    @property
    def oil_temperature(self) -> float:
        """Current gearbox oil temperature (°C)."""
        return self._oil_temp

    @property
    def tooth_wear_index(self) -> float:
        """Gear tooth wear index 0–1 (0 healthy, 1 at expected replacement)."""
        return self._tooth_wear_index

    @property
    def mesh_stiffness_variation(self) -> float:
        """Current ΔK/K ripple amplitude at gear mesh frequency (0 if ungeared)."""
        if not self.is_geared:
            return 0.0
        # Contact-ratio envelope: (ε-1) is double-tooth fraction.
        # Ripple amplitude scales with (2-ε) (more single-tooth → more ripple)
        # and is amplified by wear (tooth surface deterioration).
        s = self.spec
        envelope = max(0.0, 2.0 - s.contact_ratio)
        wear_gain = 1.0 + 3.0 * self._tooth_wear_index
        return s.mesh_stiffness_ripple_base * envelope * wear_gain * self._ripple_individuality

    def step(
        self,
        aero_rotor_speed: float,
        current_rotor_speed: float,
        aero_torque_knm: float,
        aero_load_factor: float,
        dt: float,
        is_producing: bool,
        is_starting: bool,
        is_normal_stop: bool,
        is_emergency_stop: bool,
        ambient_temp: float = 25.0,
        gearbox_overheat_severity: float = 0.0,
    ) -> Tuple[float, float, float, float, float, float]:
        """Advance drivetrain by one timestep.

        Returns:
            rotor_speed: Updated rotor speed (RPM)
            gen_speed: Generator speed (RPM)
            drivetrain_loss_kw: Total drivetrain losses
            brake_heat_kw: Heat from braking
            torsion_vib_lss: Low-speed shaft torsional vibration
            torsion_vib_hss: High-speed shaft torsional vibration
        """
        s = self.spec
        gear_ratio = max(1.0, s.total_gear_ratio)

        if is_producing or is_starting:
            self._running_seconds += dt

        # ── Brake pressure dynamics ──
        self._update_brake_pressure(is_normal_stop, is_emergency_stop, dt)

        # ── Bearing friction ──
        main_brg_friction = self._calc_main_bearing_friction(
            current_rotor_speed, aero_load_factor)
        gbx_brg_friction = self._calc_gearbox_bearing_friction(
            current_rotor_speed * gear_ratio) if self.is_geared else 0.0

        # ── Gearbox stage losses ──
        gearbox_loss_kw = 0.0
        if self.is_geared:
            gearbox_loss_kw = self._calc_gearbox_losses(current_rotor_speed, aero_torque_knm)

        # ── Low-speed shaft torsional dynamics ──
        lss_stiffness = s.lss_stiffness * self._stiffness_scale
        lss_damping = s.lss_damping * self._damping_scale

        shaft_target = aero_rotor_speed * gear_ratio if (is_producing or is_starting) else 0.0
        slip_error = shaft_target - self._generator_speed

        self._lss_twist += (
            slip_error * 0.12 * lss_stiffness - self._lss_twist * lss_damping
        ) * dt

        # ── Gear tooth contact: mesh excitation + wear (#76) ──
        # The cyclic alternation between single- and double-tooth contact
        # produces a deterministic torque ripple at GMF. This ripple is
        # modulated by the per-tooth load distribution, which degrades as
        # the tooth surfaces wear or overheat.
        self.gmf_excitation_knm = 0.0
        if self.is_geared and (is_producing or is_starting):
            hss_rpm = max(0.0, current_rotor_speed * gear_ratio)
            gmf_hz = hss_rpm * s.hss_pinion_teeth / 60.0
            self._mesh_phase = (self._mesh_phase + 2.0 * math.pi * gmf_hz * dt) % (2.0 * math.pi)
            # Square-wave-like ripple approximated by single sinusoid at GMF
            ripple = self.mesh_stiffness_variation * math.cos(self._mesh_phase)
            # HSS torque at rated condition; excitation scales with aero torque / ratio
            mean_hss_torque = aero_torque_knm / max(1.0, gear_ratio)
            self.gmf_excitation_knm = ripple * abs(mean_hss_torque)

        # ── High-speed shaft torsional dynamics (geared only) ──
        if self.is_geared:
            hss_stiffness = s.hss_stiffness * self._stiffness_scale
            hss_damping = s.hss_damping * self._damping_scale
            hss_speed_error = (current_rotor_speed * gear_ratio - self._generator_speed)
            self._hss_twist += (
                hss_speed_error * 0.08 * hss_stiffness - self._hss_twist * hss_damping
                + self.gmf_excitation_knm * 0.015
            ) * dt
        else:
            self._hss_twist = self._lss_twist * 0.3  # Coupled for direct-drive

        # ── Brake torque from pressure ──
        brake_torque = self._brake_pressure * s.brake_torque_per_bar
        if is_emergency_stop:
            brake_torque *= self._emergency_brake_scale
        elif is_normal_stop:
            brake_torque *= self._normal_brake_scale

        brake_heat_kw = brake_torque * current_rotor_speed * 2.0 * math.pi / (60.0 * 1000.0) if current_rotor_speed > 0.1 else 0.0

        # ── Rotor speed update ──
        rotor_brake_rate = brake_torque * 0.22 / max(1.0, gear_ratio ** 0.3)
        gen_brake_rate = brake_torque * 18.0
        coupling_to_rotor = self._lss_twist / (gear_ratio * 24.0)
        coupling_to_gen = self._lss_twist * 0.62 + self._hss_twist * 0.35

        rotor_speed = aero_rotor_speed - rotor_brake_rate * dt - coupling_to_rotor
        # Add main bearing friction drag
        if current_rotor_speed > 0.1:
            rotor_speed -= main_brg_friction * 0.001 * dt

        if not (is_producing or is_starting) and not (is_normal_stop or is_emergency_stop):
            rotor_speed = max(0.0, rotor_speed - 0.30 * dt)
        rotor_speed = max(0.0, rotor_speed)

        # ── Generator speed update ──
        self._generator_speed += (
            slip_error * 0.48 * lss_stiffness + coupling_to_gen - gen_brake_rate
        ) * dt

        if not (is_producing or is_starting):
            coast_down = 12.0 if is_normal_stop else 26.0 if is_emergency_stop else 8.0
            self._generator_speed = max(0.0, self._generator_speed - coast_down * dt)
        else:
            self._generator_speed = max(0.0, self._generator_speed)

        # ── Oil temperature and viscosity effects (geared only) ──
        visc_loss_kw = 0.0
        if self.is_geared:
            heat_in = gearbox_loss_kw + gbx_brg_friction
            oil_tau = 800.0 if heat_in > 0 else 1800.0
            oil_target = ambient_temp + heat_in * 0.45
            alpha = 1.0 - math.exp(-dt / max(1.0, oil_tau))
            self._oil_temp += (oil_target - self._oil_temp) * alpha

            visc_ratio = math.exp(self._visc_alpha * (self._oil_temp - self._oil_temp_ref))
            cold_start_factor = 1.0 + 0.5 * math.exp(-self._running_seconds / 600.0)
            visc_loss_kw = gearbox_loss_kw * abs(1.0 - visc_ratio) * 0.3 * cold_start_factor

            # ── Tooth wear accumulation (#76) ──
            # Archard-like wear proxy: grows with sliding speed × contact pressure
            # surrogated by (hss_speed × torque). Overheat accelerates it via
            # reduced lubrication film.
            if is_producing:
                hss_rpm_wear = max(0.0, current_rotor_speed * gear_ratio)
                speed_norm = hss_rpm_wear / 1800.0
                load_norm = max(0.0, aero_torque_knm) / 1200.0
                overheat_mult = 1.0 + 6.0 * gearbox_overheat_severity
                # rate per hour → per second
                dwear = (
                    s.tooth_wear_rate_per_hour / 3600.0
                    * speed_norm * load_norm * overheat_mult
                )
                self._tooth_wear_index = min(
                    1.5, self._tooth_wear_index + dwear * dt
                )
        else:
            self._oil_temp = ambient_temp

        # ── Total drivetrain loss ──
        drivetrain_loss_kw = main_brg_friction + gbx_brg_friction + gearbox_loss_kw + visc_loss_kw

        # ── Bearing heat for thermal model ──
        self.main_bearing_heat_kw = main_brg_friction + brake_heat_kw * 0.15
        self.gearbox_bearing_heat_kw = gbx_brg_friction + gearbox_loss_kw * 0.4 + visc_loss_kw * 0.8

        # ── Torsional vibration outputs ──
        torsion_vib_lss = min(2.0, abs(self._lss_twist) * 0.65)
        torsion_vib_hss = min(1.5, abs(self._hss_twist) * 0.12) if self.is_geared else min(0.8, abs(self._hss_twist) * 0.4)

        return (
            rotor_speed,
            self._generator_speed,
            drivetrain_loss_kw,
            brake_heat_kw,
            torsion_vib_lss,
            torsion_vib_hss,
        )

    def _update_brake_pressure(self, is_normal_stop: bool, is_emergency_stop: bool, dt: float):
        s = self.spec

        if is_emergency_stop:
            target = s.brake_pressure_max_bar
            rate = s.brake_emergency_rise_rate
        elif is_normal_stop:
            target = s.brake_pressure_max_bar * 0.7
            rate = s.brake_pressure_rise_rate
        else:
            target = 0.0
            rate = s.brake_pressure_release_rate

        if self._brake_pressure < target:
            self._brake_pressure = min(target, self._brake_pressure + rate * dt)
        elif self._brake_pressure > target:
            self._brake_pressure = max(target, self._brake_pressure - rate * dt)

    def _calc_main_bearing_friction(self, rotor_rpm: float, aero_load_factor: float) -> float:
        """Main bearing friction loss (kW). Increases with thrust load."""
        s = self.spec
        omega = rotor_rpm * 2.0 * math.pi / 60.0
        axial_load = s.main_bearing_preload_kn * (1.0 + aero_load_factor * 1.5)
        friction_torque = s.main_bearing_friction_coeff * axial_load * self._bearing_friction_scale
        return friction_torque * omega  # kW (kN·m · rad/s = kW)

    def _calc_gearbox_bearing_friction(self, hss_rpm: float) -> float:
        """Gearbox internal bearing friction loss (kW)."""
        s = self.spec
        omega = hss_rpm * 2.0 * math.pi / 60.0
        friction_torque = (s.gearbox_bearing_friction_coeff *
                           s.gearbox_bearing_preload_kn *
                           self._bearing_friction_scale)
        return friction_torque * omega * 0.001  # Scale down for HSS

    def _calc_gearbox_losses(self, rotor_rpm: float, aero_torque_knm: float) -> float:
        """Per-stage gearbox losses based on torque and speed."""
        total_loss = 0.0
        speed = rotor_rpm
        torque = aero_torque_knm

        self._stage_speeds = []
        self._stage_losses_kw = []

        for stage in self.spec.gearbox_stages:
            omega = speed * 2.0 * math.pi / 60.0
            power_in = max(0.0, torque * omega)  # kW
            loss = power_in * (1.0 - stage.efficiency)
            total_loss += loss

            self._stage_speeds.append(speed)
            self._stage_losses_kw.append(loss)

            speed *= stage.ratio
            torque = torque / stage.ratio * stage.efficiency

        return total_loss

    def get_stage_info(self) -> list:
        """Get per-stage speed and loss info for diagnostics."""
        result = []
        for i, stage in enumerate(self.spec.gearbox_stages):
            result.append({
                "stage": i + 1,
                "ratio": stage.ratio,
                "efficiency": stage.efficiency,
                "speed_rpm": self._stage_speeds[i] if i < len(self._stage_speeds) else 0.0,
                "loss_kw": self._stage_losses_kw[i] if i < len(self._stage_losses_kw) else 0.0,
            })
        return result

    def reset(self):
        """Reset all drivetrain state to initial conditions.

        Tooth wear is persistent asset state and is NOT reset here (a stop/start
        should not un-wear the gears). Use `reset_wear()` for test tear-down.
        """
        self._lss_twist = 0.0
        self._hss_twist = 0.0
        self._generator_speed = 0.0
        self._brake_pressure = 0.0
        self._brake_command = "released"
        self._stage_speeds = []
        self._stage_losses_kw = []
        self.main_bearing_heat_kw = 0.0
        self.gearbox_bearing_heat_kw = 0.0
        self._oil_temp = 25.0
        self._running_seconds = 0.0
        self._mesh_phase = 0.0
        self.gmf_excitation_knm = 0.0

    def reset_wear(self):
        """Explicit reset for cumulative tooth wear (e.g. after gearbox overhaul)."""
        self._tooth_wear_index = 0.0

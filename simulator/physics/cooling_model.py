"""
Cooling system model with active component state tracking.

Models the cooling subsystems that remove heat from turbine components:

  - Water cooling loop (pump + coolant flow + pressure)
  - Nacelle ventilation fans
  - Cabinet fans
  - Fouling / degradation over time

Each cooling component has an independent state (running/stopped/degraded)
and produces a cooling_bias dict that feeds into the existing ThermalSystem.

This module does NOT replace ThermalSystem. It sits upstream and modulates
the cooling_bias parameters that ThermalSystem already accepts.
"""

import math
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class CoolingSpec:
    """Cooling system parameters."""

    # Water cooling loop
    pump_flow_rated_lpm: float = 120.0       # rated coolant flow (liters/min)
    pump_pressure_rated_bar: float = 3.5     # rated loop pressure
    pump_power_kw: float = 2.5               # pump motor power
    coolant_volume_liters: float = 80.0      # total coolant volume
    radiator_effectiveness: float = 0.85     # heat exchanger effectiveness

    # Nacelle fans
    nacelle_fan_count: int = 2
    nacelle_fan_power_kw: float = 0.8        # per fan

    # Cabinet fans
    cabinet_fan_count: int = 3
    cabinet_fan_power_kw: float = 0.3        # per fan

    # Fouling / degradation
    fouling_rate_per_hour: float = 0.000005  # very slow degradation
    fouling_max: float = 0.35                # max fouling factor (35% reduction)
    cleaning_restores_to: float = 0.02       # residual after cleaning


class CoolingComponent:
    """Base class for a cooling component with on/off state and degradation."""

    def __init__(self, name: str, rated_power_kw: float = 1.0):
        self.name = name
        self.rated_power_kw = rated_power_kw
        self.is_running = False
        self.health = 1.0        # 1.0 = perfect, 0.0 = failed
        self._run_hours = 0.0
        self._effectiveness = 1.0

    @property
    def effectiveness(self) -> float:
        """Current cooling effectiveness (0-1)."""
        return self._effectiveness * self.health if self.is_running else 0.0

    def start(self):
        """Activate this cooling component."""
        self.is_running = True

    def stop(self):
        """Deactivate this cooling component."""
        self.is_running = False

    def step(self, dt: float):
        """Track runtime hours for maintenance scheduling."""
        if self.is_running:
            self._run_hours += dt / 3600.0


class WaterCoolingLoop:
    """Water/glycol cooling loop with pump, flow, and pressure dynamics."""

    def __init__(self, spec: CoolingSpec):
        self.spec = spec
        self.pump = CoolingComponent("water_pump", spec.pump_power_kw)
        self.pump.start()  # normally running

        # State variables
        self._flow_lpm = 0.0              # current flow rate
        self._pressure_bar = 0.0          # current loop pressure
        self._coolant_temp_c = 25.0       # bulk coolant temperature
        self._fouling_factor = 0.0        # 0=clean, fouling_max=fully fouled
        self._coolant_level_pct = 100.0   # coolant level (100% = full)
        self._leak_rate_lph = 0.0         # leak rate in litres/hour (0 = no leak)

    @property
    def flow_lpm(self) -> float:
        """Coolant flow rate in litres per minute."""
        return self._flow_lpm

    @property
    def pressure_bar(self) -> float:
        """Coolant loop pressure in bar."""
        return self._pressure_bar

    @property
    def coolant_temp(self) -> float:
        """Bulk coolant temperature in degrees Celsius."""
        return self._coolant_temp_c

    @property
    def fouling(self) -> float:
        """Heat exchanger fouling factor (0 = clean)."""
        return self._fouling_factor

    @property
    def coolant_level_pct(self) -> float:
        """Coolant level as percentage (0-100)."""
        return self._coolant_level_pct

    @property
    def coolant_alarm_level(self) -> int:
        """Coolant alarm: 0=normal, 1=low(<70%), 2=very_low(<50%), 3=critical(<30%)."""
        if self._coolant_level_pct < 30.0:
            return 3
        if self._coolant_level_pct < 50.0:
            return 2
        if self._coolant_level_pct < 70.0:
            return 1
        return 0

    def set_leak_rate(self, rate_lph: float):
        """Set coolant leak rate in litres per hour."""
        self._leak_rate_lph = max(0.0, rate_lph)

    def refill(self):
        """Refill coolant to 100%."""
        self._coolant_level_pct = 100.0

    def step(self, heat_load_kw: float, ambient_temp: float,
             wind_speed: float, dt: float, turbine_running: bool) -> float:
        """Advance cooling loop by one timestep.

        Returns: cooling effectiveness factor (0-1) for thermal model.
        """
        s = self.spec
        self.pump.step(dt)

        # ── Auto start/stop pump based on turbine state ──
        if turbine_running and not self.pump.is_running:
            self.pump.start()

        # ── Coolant level depletion from leak ──
        if self._leak_rate_lph > 0 and self._coolant_level_pct > 0:
            lost_litres = self._leak_rate_lph * (dt / 3600.0)
            lost_pct = (lost_litres / s.coolant_volume_liters) * 100.0
            self._coolant_level_pct = max(0.0, self._coolant_level_pct - lost_pct)

        # ── Pump flow dynamics (first-order response) ──
        if self.pump.is_running and self.pump.health > 0.1:
            target_flow = s.pump_flow_rated_lpm * self.pump.health
        else:
            target_flow = 0.0

        # Fouling reduces effective flow
        flow_reduction = 1.0 - self._fouling_factor * 0.6
        target_flow *= flow_reduction

        # Low coolant level causes pump cavitation and flow reduction
        level = self._coolant_level_pct
        if level < 70.0:
            cavitation_factor = max(0.05, (level - 10.0) / 60.0)
            target_flow *= cavitation_factor

        tau_flow = 3.0  # seconds to reach target flow
        alpha = 1.0 - math.exp(-dt / tau_flow)
        self._flow_lpm += (target_flow - self._flow_lpm) * alpha

        # ── Pressure follows flow ──
        flow_ratio = self._flow_lpm / max(s.pump_flow_rated_lpm, 1.0)
        target_pressure = s.pump_pressure_rated_bar * flow_ratio ** 2
        # Fouling increases pressure (restriction)
        target_pressure *= (1.0 + self._fouling_factor * 0.8)
        tau_pressure = 1.5
        alpha_p = 1.0 - math.exp(-dt / tau_pressure)
        self._pressure_bar += (target_pressure - self._pressure_bar) * alpha_p

        # ── Coolant temperature ──
        # Heat absorbed by coolant
        if self._flow_lpm > 1.0:
            # Q = m_dot × cp × ΔT → ΔT = Q / (m_dot × cp)
            # flow in kg/s ≈ lpm / 60 (water density ~1 kg/L)
            mass_flow = self._flow_lpm / 60.0
            cp_water = 4.18  # kJ/(kg·°C)
            heat_rise = heat_load_kw / max(mass_flow * cp_water, 0.1)
        else:
            heat_rise = heat_load_kw * 0.5  # Stagnant coolant heats up fast

        # Radiator cooling: effectiveness reduced by fouling
        rad_eff = s.radiator_effectiveness * (1.0 - self._fouling_factor * 0.5)
        # Wind assists radiator cooling
        wind_boost = min(0.15, wind_speed * 0.01)
        rad_eff = min(0.98, rad_eff + wind_boost)

        target_temp = ambient_temp + heat_rise * (1.0 - rad_eff)
        tau_temp = s.coolant_volume_liters * 0.5  # Larger volume = slower response
        alpha_t = 1.0 - math.exp(-dt / max(tau_temp, 5.0))
        self._coolant_temp_c += (target_temp - self._coolant_temp_c) * alpha_t

        # ── Fouling accumulation ──
        if self._flow_lpm > 1.0:
            self._fouling_factor = min(
                s.fouling_max,
                self._fouling_factor + s.fouling_rate_per_hour * (dt / 3600.0)
            )

        # ── Return cooling effectiveness ──
        if self._flow_lpm < 5.0:
            return 0.3  # Minimal cooling without flow
        base_eff = flow_ratio * rad_eff
        return max(0.25, min(1.3, base_eff))

    def clean(self):
        """Simulate maintenance cleaning of the cooling loop."""
        self._fouling_factor = self.spec.cleaning_restores_to


class FanBank:
    """Group of cooling fans (nacelle or cabinet)."""

    def __init__(self, name: str, count: int, power_per_fan_kw: float):
        self.name = name
        self.fans = [CoolingComponent(f"{name}_fan_{i}", power_per_fan_kw)
                     for i in range(count)]
        # Start all fans by default
        for f in self.fans:
            f.start()

        self._fouling_factor = 0.0

    @property
    def active_count(self) -> int:
        """Number of fans currently running with usable health."""
        return sum(1 for f in self.fans if f.is_running and f.health > 0.1)

    @property
    def total_count(self) -> int:
        """Total number of installed fans."""
        return len(self.fans)

    def step(self, dt: float, turbine_running: bool) -> float:
        """Advance fans and return cooling effectiveness (0-1)."""
        for f in self.fans:
            if turbine_running and not f.is_running and f.health > 0.1:
                f.start()
            f.step(dt)

        if self.total_count == 0:
            return 1.0

        active_ratio = self.active_count / self.total_count
        # Each fan contributes proportionally, with some redundancy margin
        effectiveness = min(1.0, active_ratio * 1.1)
        # Fouling reduces filter/radiator airflow
        effectiveness *= (1.0 - self._fouling_factor * 0.4)
        return max(0.2, effectiveness)


class CoolingSystem:
    """
    Complete cooling system managing water loop, nacelle fans, and cabinet fans.

    Produces a cooling_bias dict compatible with ThermalSystem.step().
    """

    def __init__(self, spec: Optional[CoolingSpec] = None,
                 individuality_scale: float = 1.0):
        self.spec = spec or CoolingSpec()
        self._individuality = individuality_scale

        self.water_loop = WaterCoolingLoop(self.spec)
        self.nacelle_fans = FanBank(
            "nacelle", self.spec.nacelle_fan_count, self.spec.nacelle_fan_power_kw)
        self.cabinet_fans = FanBank(
            "cabinet", self.spec.cabinet_fan_count, self.spec.cabinet_fan_power_kw)

        # Fouling rates vary by component
        self._sim_hours = 0.0

    def step(self, gen_power_kw: float, ambient_temp: float,
             wind_speed: float, dt: float,
             turbine_running: bool) -> Dict[str, float]:
        """Advance cooling system and return cooling_bias for ThermalSystem.

        Returns dict with keys: nacelle, exposed, cabinet, water, transformer
        """
        self._sim_hours += dt / 3600.0

        # Water loop handles converter and generator cooling
        water_heat_load = gen_power_kw * 0.03  # ~3% of gen power as heat to water
        water_eff = self.water_loop.step(
            water_heat_load, ambient_temp, wind_speed, dt, turbine_running)

        # Fan banks
        nacelle_fan_eff = self.nacelle_fans.step(dt, turbine_running)
        cabinet_fan_eff = self.cabinet_fans.step(dt, turbine_running)

        # Apply individuality scaling
        scale = self._individuality

        # Build cooling_bias dict
        # These multiply into ThermalSystem's cooling_factor calculations
        cooling_bias: Dict[str, float] = {
            "nacelle": nacelle_fan_eff * scale,
            "exposed": nacelle_fan_eff * 0.8 * scale + 0.2,  # Exposed gets some natural cooling
            "cabinet": cabinet_fan_eff * scale,
            "water": water_eff * scale,
            "transformer": nacelle_fan_eff * 0.5 * scale + 0.5,  # Transformer has its own cooling
        }

        return cooling_bias

    def get_status(self) -> Dict:
        """Get cooling system status for diagnostics / SCADA display."""
        return {
            "water_pump_running": self.water_loop.pump.is_running,
            "water_pump_health": round(self.water_loop.pump.health, 3),
            "water_flow_lpm": round(self.water_loop.flow_lpm, 1),
            "water_pressure_bar": round(self.water_loop.pressure_bar, 2),
            "water_coolant_temp_c": round(self.water_loop.coolant_temp, 1),
            "water_fouling": round(self.water_loop.fouling, 4),
            "coolant_level_pct": round(self.water_loop.coolant_level_pct, 1),
            "coolant_alarm_level": self.water_loop.coolant_alarm_level,
            "nacelle_fans_active": self.nacelle_fans.active_count,
            "nacelle_fans_total": self.nacelle_fans.total_count,
            "cabinet_fans_active": self.cabinet_fans.active_count,
            "cabinet_fans_total": self.cabinet_fans.total_count,
            "sim_hours": round(self._sim_hours, 1),
        }

    def degrade_pump(self, health: float):
        """Simulate pump degradation (health: 0.0-1.0)."""
        self.water_loop.pump.health = max(0.0, min(1.0, health))

    def fail_fan(self, bank: str, index: int):
        """Simulate a fan failure."""
        fans = self.nacelle_fans if bank == "nacelle" else self.cabinet_fans
        if 0 <= index < len(fans.fans):
            fans.fans[index].health = 0.0
            fans.fans[index].stop()

    def repair_fan(self, bank: str, index: int):
        """Simulate fan repair."""
        fans = self.nacelle_fans if bank == "nacelle" else self.cabinet_fans
        if 0 <= index < len(fans.fans):
            fans.fans[index].health = 1.0
            fans.fans[index].start()

    def set_coolant_leak(self, rate_lph: float):
        """Set coolant leak rate (litres/hour). Simulates O-ring degradation."""
        self.water_loop.set_leak_rate(rate_lph)

    def refill_coolant(self):
        """Refill coolant to 100% (maintenance action)."""
        self.water_loop.refill()

    def clean_water_loop(self):
        """Simulate maintenance cleaning."""
        self.water_loop.clean()

    def reset(self):
        """Reset cooling system to initial state."""
        self.water_loop = WaterCoolingLoop(self.spec)
        self.nacelle_fans = FanBank(
            "nacelle", self.spec.nacelle_fan_count, self.spec.nacelle_fan_power_kw)
        self.cabinet_fans = FanBank(
            "cabinet", self.spec.cabinet_fan_count, self.spec.cabinet_fan_power_kw)
        self._sim_hours = 0.0

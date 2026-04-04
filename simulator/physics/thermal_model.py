"""
Thermal models for wind turbine components.

Each component uses a first-order RC thermal model calibrated to
produce realistic steady-state temperatures at rated power.

Reference values (5MW turbine at rated load, 25°C ambient):
  Generator stator:  80-110°C
  Generator air gap: 60-85°C
  Generator bearing:  50-75°C
  Nacelle:           35-45°C
  Nacelle cabinet:   35-48°C
  Converter cabinet: 35-50°C
  IGCT water:        30-42°C
  Transformer core:  50-80°C
  Hub/rotor:         ambient + 5-10°C
  Hub cabinet:       ambient + 8-15°C

Can be replaced independently for different turbine types.
"""

from dataclasses import dataclass
from typing import Dict


class ThermalElement:
    """
    First-order thermal model: τ × dT/dt = Q_in × R_th - (T - T_amb)

    Parameters calibrated so that:
      T_steady = T_amb + Q_in × R_th

    Where τ = R_th × C_th (time constant in seconds).
    """

    def __init__(self, thermal_resistance: float, time_constant: float,
                 initial_temp: float = 25.0):
        """
        Args:
            thermal_resistance: R_th (°C per kW of heat input)
            time_constant: τ = R×C (seconds to reach 63% of steady state)
            initial_temp: Starting temperature (°C)
        """
        self.R_th = thermal_resistance
        self.tau = time_constant  # seconds
        self.C_th = time_constant / thermal_resistance  # kJ/°C (derived)
        self.temperature = initial_temp

    def step(self, heat_input_kw: float, ambient_temp: float, dt: float) -> float:
        """Advance one timestep. Returns new temperature."""
        T_target = ambient_temp + heat_input_kw * self.R_th
        import math
        alpha = 1.0 - math.exp(-dt / self.tau)
        self.temperature += (T_target - self.temperature) * alpha
        return self.temperature

    def reset(self, temp: float):
        self.temperature = temp


@dataclass
class ThermalSystemConfig:
    """Calibrated thermal parameters for a 5MW turbine."""

    # (R_th °C/kW, time_constant seconds, initial °C)
    # R_th is chosen so that at rated heat load, T_steady = T_amb + Q × R_th

    # Generator stator: ~250kW heat loss at 5MW, target +60°C above ambient → R=0.24
    gen_stator:  tuple = (0.24, 600, 35.0)
    # Generator air gap: ~125kW, target +40°C → R=0.32
    gen_air:     tuple = (0.32, 450, 30.0)
    # Generator bearing: ~50kW (heat + friction), target +35°C → R=0.70
    gen_bearing: tuple = (0.70, 900, 30.0)

    # Converter cabinet: ~100kW, target +20°C → R=0.20
    cnv_cabinet: tuple = (0.20, 500, 28.0)
    # IGCT water cooling: ~70kW, target +12°C → R=0.17
    cnv_water:   tuple = (0.17, 300, 25.0)

    # Transformer: ~50kW, target +35°C → R=0.70
    transformer: tuple = (0.70, 1200, 30.0)

    # Nacelle: diffuse heat, target +12°C → R=0.08
    nacelle:     tuple = (0.08, 1800, 25.0)
    # Nacelle cabinet: smaller volume, target +15°C from nacelle temp → R=0.75
    nac_cabinet: tuple = (0.75, 300, 28.0)

    # Hub/rotor: mostly ambient-driven
    rotor:       tuple = (0.10, 600, 25.0)
    hub_cabinet: tuple = (0.30, 300, 28.0)


class ThermalSystem:
    """
    Complete turbine thermal system — manages all thermal elements.

    Heat flow model at rated (5MW):
      Generator loss: 5000 × (1-0.95) = 250 kW
        → stator:  60% = 150 kW → ΔT = 150×0.24 = 36°C → T ≈ 61°C
        → air gap: 30% = 75 kW  → ΔT = 75×0.32  = 24°C → T ≈ 49°C
        → bearing: 10% = 25 kW + friction 15kW = 40kW → ΔT = 40×0.70 = 28°C → T ≈ 53°C

      Converter loss: 5000 × 0.02 = 100 kW
        → cabinet: 100 kW → ΔT = 100×0.20 = 20°C → T ≈ 45°C
        → water:   70 kW  → ΔT = 70×0.17  = 12°C → T ≈ 37°C

      Transformer: 4900 × 0.01 = 49 kW → ΔT = 49×0.70 = 34°C → T ≈ 59°C
      Nacelle: ~150 kW diffuse → ΔT = 150×0.08 = 12°C → T ≈ 37°C
    """

    def __init__(self, config: ThermalSystemConfig = None):
        cfg = config or ThermalSystemConfig()

        self.gen_stator = ThermalElement(*cfg.gen_stator)
        self.gen_air = ThermalElement(*cfg.gen_air)
        self.gen_bearing = ThermalElement(*cfg.gen_bearing)
        self.cnv_cabinet = ThermalElement(*cfg.cnv_cabinet)
        self.cnv_water = ThermalElement(*cfg.cnv_water)
        self.transformer = ThermalElement(*cfg.transformer)
        self.nacelle = ThermalElement(*cfg.nacelle)
        self.nac_cabinet = ThermalElement(*cfg.nac_cabinet)
        self.rotor = ThermalElement(*cfg.rotor)
        self.hub_cabinet = ThermalElement(*cfg.hub_cabinet)

    def step(self, gen_power_kw: float, grid_power_kw: float,
             rotor_speed: float, ambient_temp: float,
             gen_efficiency: float, dt: float) -> Dict[str, float]:
        """
        Advance all thermal models by one timestep.

        Returns dict with all temperature values.
        """
        is_running = gen_power_kw > 10  # threshold

        # ── Heat sources ──
        heat_gen = gen_power_kw * (1.0 - gen_efficiency) if is_running else 0.0
        heat_cnv = gen_power_kw * 0.02 if is_running else 0.0
        heat_trf = grid_power_kw * 0.01 if is_running else 0.0
        heat_bearing_friction = rotor_speed * 1.5 if is_running else 0.0  # kW, RPM-dependent

        # Diffuse heat into nacelle from all sources
        heat_nac = heat_gen * 0.15 + heat_cnv * 0.3 + heat_bearing_friction * 0.2

        # ── Step each element ──
        gen_sta_t = self.gen_stator.step(heat_gen * 0.60, ambient_temp, dt)
        gen_air_t = self.gen_air.step(heat_gen * 0.30, ambient_temp, dt)
        gen_brg_t = self.gen_bearing.step(
            heat_gen * 0.10 + heat_bearing_friction, ambient_temp, dt)

        cnv_cab_t = self.cnv_cabinet.step(heat_cnv, ambient_temp, dt)
        cnv_wtr_t = self.cnv_water.step(heat_cnv * 0.70, ambient_temp, dt)

        trf_t = self.transformer.step(heat_trf, ambient_temp, dt)

        nac_t = self.nacelle.step(heat_nac, ambient_temp, dt)
        # Cabinet temp is relative to nacelle, not ambient
        nac_cab_t = self.nac_cabinet.step(heat_cnv * 0.10, nac_t, dt)

        rot_t = self.rotor.step(heat_bearing_friction * 0.1, ambient_temp, dt)
        hub_cab_t = self.hub_cabinet.step(0, rot_t, dt)

        return {
            "gen_stator": round(gen_sta_t, 2),
            "gen_air": round(gen_air_t, 2),
            "gen_bearing": round(gen_brg_t, 2),
            "cnv_cabinet": round(cnv_cab_t, 2),
            "cnv_water": round(cnv_wtr_t, 2),
            "transformer": round(trf_t, 2),
            "nacelle": round(nac_t, 2),
            "nac_cabinet": round(nac_cab_t, 2),
            "rotor": round(rot_t, 2),
            "hub_cabinet": round(hub_cab_t, 2),
        }

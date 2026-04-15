"""
Thermal models for wind turbine components.

This version adds:
  - residual heat memory after startup / shutdown
  - different cooling behavior for running vs stopped states
  - heat soak between nearby components
  - wind-assisted cooling for exposed components
"""

import math
from dataclasses import dataclass
from typing import Dict


class ThermalElement:
    """
    First-order thermal model for one component.
    """

    def __init__(self, thermal_resistance: float, time_constant: float, initial_temp: float = 25.0):
        self.R_th = thermal_resistance
        self.tau = time_constant
        self.C_th = time_constant / thermal_resistance
        self.temperature = initial_temp

    def step(self, heat_input_kw: float, ambient_temp: float, dt: float, cooling_factor: float = 1.0) -> float:
        """Advance one timestep. Higher cooling_factor means faster response to ambient."""
        target = ambient_temp + heat_input_kw * self.R_th
        effective_tau = max(1.0, self.tau / max(0.25, cooling_factor))
        alpha = 1.0 - math.exp(-dt / effective_tau)
        self.temperature += (target - self.temperature) * alpha
        return self.temperature

    def reset(self, temp: float):
        """Reset the thermal node temperature to a given value."""
        self.temperature = temp


@dataclass
class ThermalSystemConfig:
    """Calibrated thermal parameters for Z72-2000-MV turbine.

    Z72 OEM thresholds:
      Gen stator: alarm 140°C, trip 150°C
      Gen bearing: alarm 85°C, trip 95°C
      Rotor cabinet: alarm 45°C, trip 50°C
      Nacelle cabinet: alarm 45°C, trip 50°C
    Tuned so normal operation reaches ~60-80% of alarm thresholds.
    """

    # (thermal_resistance_°C/kW, time_constant_s, initial_temp_°C)
    # Z72-2000-MV: direct-drive PMSG, rated 2MW
    # Heat at rated: gen_loss = 2000*(1-0.95) = 100kW, cnv = 2000*0.02 = 40kW
    # R_th chosen so rated operation reaches ~60-75% of alarm:
    #   Stator: R=0.65 → 100*0.65 = +65°C → ~90°C (alarm@140)
    #   Bearing: R=0.35 → rotor heat ~33kW → +12°C → ~55°C (alarm@85)
    #   Air gap: R=0.55 → ~80°C
    gen_stator: tuple = (0.65, 600, 35.0)    # ~90°C at rated (alarm@140)
    gen_air: tuple = (0.55, 450, 30.0)       # ~80°C at rated
    gen_bearing: tuple = (0.35, 900, 30.0)   # ~55°C at rated (alarm@85)

    cnv_cabinet: tuple = (0.28, 500, 28.0)   # ~39°C at rated
    cnv_water: tuple = (0.22, 300, 25.0)     # ~34°C at rated

    transformer: tuple = (0.80, 1200, 30.0)  # ~46°C at rated

    nacelle: tuple = (0.12, 1800, 25.0)      # ~30°C
    nac_cabinet: tuple = (0.80, 300, 28.0)   # ~34°C (alarm@45)

    rotor: tuple = (0.15, 600, 25.0)         # ~30°C
    hub_cabinet: tuple = (0.35, 300, 28.0)   # ~33°C (alarm@45)


class ThermalSystem:
    """
    Complete turbine thermal system with startup / shutdown thermal inertia.
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

        # Residual heat states. These decay slower than electrical load.
        self._mem_gen = 0.0
        self._mem_cnv = 0.0
        self._mem_trf = 0.0
        self._mem_bearing = 0.0

    def step(
        self,
        gen_power_kw: float,
        grid_power_kw: float,
        rotor_speed: float,
        ambient_temp: float,
        gen_efficiency: float,
        dt: float,
        wind_speed: float = 0.0,
        tur_state: int = 1,
        sync_progress: float = 0.0,
        extra_heat: Dict[str, float] | None = None,
        cooling_bias: Dict[str, float] | None = None,
    ) -> Dict[str, float]:
        """Advance all thermal models by one timestep."""
        extra_heat = extra_heat or {}
        cooling_bias = cooling_bias or {}
        is_running = tur_state == 6
        is_starting = tur_state in (4, 5, 8)
        is_stopping = tur_state in (7, 9)
        running_factor = 1.0 if is_running else max(
            0.0,
            min(1.0, sync_progress if is_starting else 0.15 if is_stopping else 0.0),
        )

        heat_gen_raw = gen_power_kw * (1.0 - gen_efficiency) * max(0.2, running_factor)
        heat_cnv_raw = gen_power_kw * 0.02 * max(0.15, running_factor)
        heat_trf_raw = grid_power_kw * 0.01 * max(0.15, running_factor)
        heat_bearing_raw = rotor_speed * 1.5 * max(0.25, min(1.0, rotor_speed / 4.0))

        self._mem_gen = self._update_memory(self._mem_gen, heat_gen_raw, dt, rise_tau=45.0, fall_tau=900.0)
        self._mem_cnv = self._update_memory(self._mem_cnv, heat_cnv_raw, dt, rise_tau=35.0, fall_tau=480.0)
        self._mem_trf = self._update_memory(self._mem_trf, heat_trf_raw, dt, rise_tau=90.0, fall_tau=1800.0)
        self._mem_bearing = self._update_memory(self._mem_bearing, heat_bearing_raw, dt, rise_tau=25.0, fall_tau=700.0)

        heat_gen = max(heat_gen_raw, self._mem_gen * (0.35 if not is_running else 1.0)) + extra_heat.get("generator", 0.0)
        heat_cnv = max(heat_cnv_raw, self._mem_cnv * (0.30 if not is_running else 1.0)) + extra_heat.get("converter", 0.0)
        heat_trf = max(heat_trf_raw, self._mem_trf * (0.45 if not is_running else 1.0)) + extra_heat.get("transformer", 0.0)
        heat_bearing = max(heat_bearing_raw, self._mem_bearing * (0.35 if rotor_speed < 1.0 else 1.0)) + extra_heat.get("bearing", 0.0)

        airflow = max(0.0, wind_speed)
        nacelle_cooling = (0.7 + min(airflow / 14.0, 0.9)) * cooling_bias.get("nacelle", 1.0)
        exposed_cooling = (0.9 + min(airflow / 10.0, 1.1)) * cooling_bias.get("exposed", 1.0)
        cabinet_cooling = (0.45 if not is_running else 1.15) * cooling_bias.get("cabinet", 1.0)
        water_cooling = (0.50 if not is_running else 1.25) * cooling_bias.get("water", 1.0)
        transformer_cooling = (0.8 + min(airflow / 16.0, 0.7)) * cooling_bias.get("transformer", 1.0)

        heat_nac = heat_gen * 0.18 + heat_cnv * 0.32 + heat_bearing * 0.22 + heat_trf * 0.08 + extra_heat.get("nacelle", 0.0)

        stator_env = ambient_temp + max(0.0, self.nacelle.temperature - ambient_temp) * 0.12
        air_env = ambient_temp + max(0.0, self.gen_stator.temperature - ambient_temp) * 0.10
        bearing_env = ambient_temp + max(0.0, self.gen_stator.temperature - ambient_temp) * 0.08
        cabinet_env = ambient_temp + max(0.0, self.nacelle.temperature - ambient_temp) * 0.18

        gen_sta_t = self.gen_stator.step(
            heat_gen * 0.60,
            stator_env,
            dt,
            cooling_factor=0.85 + exposed_cooling * 0.25,
        )
        gen_air_t = self.gen_air.step(
            heat_gen * 0.30 + max(0.0, gen_sta_t - ambient_temp) * 0.08,
            air_env,
            dt,
            cooling_factor=0.9 + nacelle_cooling * 0.3,
        )
        gen_brg_t = self.gen_bearing.step(
            heat_gen * 0.10 + heat_bearing + max(0.0, gen_sta_t - ambient_temp) * 0.03,
            bearing_env,
            dt,
            cooling_factor=0.8 + exposed_cooling * 0.35,
        )

        cnv_cab_t = self.cnv_cabinet.step(
            heat_cnv + max(0.0, self.cnv_water.temperature - ambient_temp) * 0.04,
            cabinet_env,
            dt,
            cooling_factor=cabinet_cooling,
        )
        cnv_wtr_t = self.cnv_water.step(
            heat_cnv * 0.70,
            ambient_temp,
            dt,
            cooling_factor=water_cooling + airflow / 18.0,
        )

        trf_t = self.transformer.step(
            heat_trf + max(0.0, self.nacelle.temperature - ambient_temp) * 0.02,
            ambient_temp,
            dt,
            cooling_factor=transformer_cooling,
        )

        nac_t = self.nacelle.step(
            heat_nac + max(0.0, trf_t - ambient_temp) * 0.02,
            ambient_temp,
            dt,
            cooling_factor=nacelle_cooling,
        )
        nac_cab_t = self.nac_cabinet.step(
            heat_cnv * 0.10 + max(0.0, cnv_cab_t - nac_t) * 0.05,
            nac_t,
            dt,
            cooling_factor=cabinet_cooling,
        )

        rot_t = self.rotor.step(
            heat_bearing * 0.12
            + max(0.0, gen_brg_t - ambient_temp) * 0.02
            + extra_heat.get("rotor", 0.0),
            ambient_temp,
            dt,
            cooling_factor=exposed_cooling,
        )
        hub_cab_t = self.hub_cabinet.step(
            max(0.0, rot_t - ambient_temp) * 0.03 + extra_heat.get("hub", 0.0),
            rot_t,
            dt,
            cooling_factor=0.6 + exposed_cooling * 0.25,
        )

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

    @staticmethod
    def _update_memory(current: float, target: float, dt: float, rise_tau: float, fall_tau: float) -> float:
        tau = rise_tau if target > current else fall_tau
        alpha = 1.0 - math.exp(-dt / max(1.0, tau))
        return current + (target - current) * alpha

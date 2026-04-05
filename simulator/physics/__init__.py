# Physics-based wind turbine simulation engine
# Independent module - no dependency on FastAPI, frontend, or storage
#
# Architecture: Composable sub-models (each independently replaceable)
#   TurbinePhysicsModel  ← main orchestrator
#     ├── PowerCurveModel     (power_curve.py)  + CpSurfaceModel
#     ├── RotorSpeedModel     (power_curve.py)
#     ├── DrivetrainModel     (drivetrain_model.py)
#     ├── ThermalSystem       (thermal_model.py)
#     ├── CoolingSystem       (cooling_model.py)
#     ├── VibrationModel      (vibration_model.py)
#     ├── YawModel            (yaw_model.py)
#     └── ScadaRegistry       (scada_registry.py)
#
# Wind field models (optional, used by engine):
#     ├── TurbulenceGenerator (wind_field.py)
#     ├── WindDirectionModel  (wind_field.py)
#     └── PerTurbineWind      (wind_field.py)

from simulator.physics.scada_registry import SCADA_REGISTRY, ScadaTag
from simulator.physics.turbine_physics import TurbinePhysicsModel, TurbineSpec, TURBINE_PRESETS
from simulator.physics.fault_engine import FaultEngine, FaultScenario
from simulator.physics.power_curve import PowerCurveModel, RotorSpeedModel, CpSurfaceModel
from simulator.physics.thermal_model import ThermalSystem, ThermalSystemConfig
from simulator.physics.vibration_model import VibrationModel
from simulator.physics.yaw_model import YawModel
from simulator.physics.wind_field import TurbulenceGenerator, WindDirectionModel, PerTurbineWind
from simulator.physics.drivetrain_model import DrivetrainModel, DrivetrainSpec
from simulator.physics.cooling_model import CoolingSystem, CoolingSpec

__all__ = [
    "SCADA_REGISTRY", "ScadaTag",
    "TurbinePhysicsModel", "TurbineSpec", "TURBINE_PRESETS",
    "FaultEngine", "FaultScenario",
    "PowerCurveModel", "RotorSpeedModel", "CpSurfaceModel",
    "ThermalSystem", "ThermalSystemConfig",
    "DrivetrainModel", "DrivetrainSpec",
    "CoolingSystem", "CoolingSpec",
    "VibrationModel", "YawModel",
    "TurbulenceGenerator", "WindDirectionModel", "PerTurbineWind",
]

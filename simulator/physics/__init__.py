# Physics-based wind turbine simulation engine
# Independent module - no dependency on FastAPI, frontend, or storage
#
# Usage:
#   from simulator.physics import TurbinePhysicsModel, FaultEngine, SCADA_REGISTRY
#   model = TurbinePhysicsModel()
#   output = model.step(wind_speed=10.0, wind_direction=270.0, ambient_temp=25.0, dt=1.0)
#   # output is a flat dict keyed by SCADA tag IDs

from simulator.physics.scada_registry import SCADA_REGISTRY, ScadaTag
from simulator.physics.turbine_physics import TurbinePhysicsModel, TurbineSpec, TURBINE_PRESETS
from simulator.physics.fault_engine import FaultEngine, FaultScenario

__all__ = [
    "SCADA_REGISTRY",
    "ScadaTag",
    "TurbinePhysicsModel",
    "TurbineSpec",
    "TURBINE_PRESETS",
    "FaultEngine",
    "FaultScenario",
]

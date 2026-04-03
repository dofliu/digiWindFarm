from fastapi import APIRouter
from server.models import DataSourceConfig, SimulationConfig, DataSourceMode

router = APIRouter(prefix="/api/config", tags=["config"])


def get_broker():
    from server.app import broker
    return broker


@router.get("")
async def get_config():
    """Get current data source configuration."""
    b = get_broker()
    return {
        "mode": b.mode.value,
        "turbineCount": len(b.turbine_ids),
        "isRunning": b.simulator.is_running if b.simulator else False,
    }


@router.post("/datasource")
async def set_datasource(config: DataSourceConfig):
    """Switch data source mode (simulation / opc_da)."""
    b = get_broker()
    b.switch_mode(config)
    return {"status": "ok", "mode": b.mode.value}


@router.post("/simulation")
async def set_simulation(config: SimulationConfig):
    """Update simulation parameters and restart simulator."""
    b = get_broker()
    ds_config = DataSourceConfig(mode=DataSourceMode.SIMULATION)
    b.switch_mode(ds_config, config)
    return {
        "status": "ok",
        "turbineCount": config.turbineCount,
        "baseWindSpeed": config.baseWindSpeed,
    }

from fastapi import APIRouter, HTTPException
from server.models import DataSourceConfig, SimulationConfig, DataSourceMode, WindOverrideRequest

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


@router.get("/wind")
async def get_wind_status():
    """Get current wind model status (auto/manual, override values)."""
    b = get_broker()
    if not b.simulator:
        raise HTTPException(400, "Simulator not running")
    return b.simulator.wind_model.get_status()


@router.post("/wind")
async def set_wind(req: WindOverrideRequest):
    """Set wind conditions manually, or activate a profile.

    Profiles: calm, moderate, rated, strong, storm, gusty, ramp_up, ramp_down, auto
    Or set individual values: windSpeed, windDirection, ambientTemp, turbulence
    """
    b = get_broker()
    if not b.simulator:
        raise HTTPException(400, "Simulator not running")

    wm = b.simulator.wind_model
    if req.profile:
        wm.set_profile(req.profile)
    else:
        wm.set_override(
            wind_speed=req.windSpeed,
            wind_direction=req.windDirection,
            ambient_temp=req.ambientTemp,
            turbulence=req.turbulence,
        )
    return wm.get_status()


@router.post("/wind/clear")
async def clear_wind():
    """Return to automatic daily pattern wind model."""
    b = get_broker()
    if not b.simulator:
        raise HTTPException(400, "Simulator not running")
    b.simulator.wind_model.clear_override()
    return {"status": "ok", "mode": "auto"}

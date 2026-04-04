from fastapi import APIRouter, HTTPException
from server.models import DataSourceConfig, SimulationConfig, DataSourceMode, WindOverrideRequest, GridOverrideRequest

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
    """Update simulation parameters. Only restarts if turbine count changed."""
    b = get_broker()

    # Only restart if turbine count actually changed
    current_count = len(b.turbine_ids) if b.simulator else 0
    if b.simulator and b.simulator.is_running and config.turbineCount == current_count:
        # Just update wind model parameters without restarting
        b.simulator.wind_model.turbulence_intensity = config.turbulenceIntensity
        return {
            "status": "ok",
            "turbineCount": config.turbineCount,
            "baseWindSpeed": config.baseWindSpeed,
            "restarted": False,
        }

    # Turbine count changed — full restart required
    ds_config = DataSourceConfig(mode=DataSourceMode.SIMULATION)
    b.switch_mode(ds_config, config)
    return {
        "status": "ok",
        "turbineCount": config.turbineCount,
        "baseWindSpeed": config.baseWindSpeed,
        "restarted": True,
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
    b.close_open_events("wind", source="config")
    if req.profile:
        wm.set_profile(req.profile)
    else:
        wm.set_override(
            wind_speed=req.windSpeed,
            wind_direction=req.windDirection,
            ambient_temp=req.ambientTemp,
            turbulence=req.turbulence,
        )
    b.record_event(
        event_type="wind",
        source="config",
        title=f"Wind config updated{f': {req.profile}' if req.profile else ''}",
        detail="Wind profile or override changed",
        payload=req.model_dump(),
    )
    return wm.get_status()


@router.post("/wind/clear")
async def clear_wind():
    """Return to automatic daily pattern wind model."""
    b = get_broker()
    if not b.simulator:
        raise HTTPException(400, "Simulator not running")
    b.simulator.wind_model.clear_override()
    b.close_open_events("wind", source="config")
    b.record_event(
        event_type="wind",
        source="config",
        title="Wind config cleared",
        detail="Returned wind model to auto mode",
        payload={"mode": "auto"},
    )
    return {"status": "ok", "mode": "auto"}


@router.get("/grid")
async def get_grid_status():
    b = get_broker()
    if not b.simulator:
        raise HTTPException(400, "Simulator not running")
    return b.simulator.grid_model.get_status()


@router.post("/grid")
async def set_grid(req: GridOverrideRequest):
    b = get_broker()
    if not b.simulator:
        raise HTTPException(400, "Simulator not running")

    gm = b.simulator.grid_model
    b.close_open_events("grid", source="config")
    if req.profile:
        gm.set_profile(req.profile)
    else:
        gm.set_override(req.frequencyHz, req.voltageV)
    b.record_event(
        event_type="grid",
        source="config",
        title=f"Grid config updated{f': {req.profile}' if req.profile else ''}",
        detail="Grid profile or override changed",
        payload=req.model_dump(),
    )
    return gm.get_status()


@router.post("/grid/clear")
async def clear_grid():
    b = get_broker()
    if not b.simulator:
        raise HTTPException(400, "Simulator not running")
    b.simulator.grid_model.clear_override()
    b.close_open_events("grid", source="config")
    b.record_event(
        event_type="grid",
        source="config",
        title="Grid config cleared",
        detail="Returned grid model to auto mode",
        payload={"mode": "auto"},
    )
    return {"status": "ok", "mode": "auto"}


# ─── Turbine Specification ─────────────────────────────────────────────

@router.get("/turbine-spec")
async def get_turbine_spec():
    """Get current turbine specification."""
    b = get_broker()
    if not b.simulator or not b.simulator.turbines:
        raise HTTPException(400, "Simulator not running")
    # Return spec from first turbine (all share same spec)
    first_tid = list(b.simulator.turbines.keys())[0]
    model = b.simulator.turbines[first_tid]
    return model.spec.to_dict()


@router.post("/turbine-spec")
async def set_turbine_spec(spec_dict: dict):
    """Update turbine specifications for all turbines.

    Accepts partial updates — only provided fields are changed.
    Example: {"rated_power_kw": 3000, "cut_in_speed": 4.0, "curtailment_kw": 2000}

    Or use a preset: {"preset": "vestas_v90_3mw"}
    Available presets: z72_5mw, vestas_v90_3mw, sg_8mw, goldwind_2.5mw
    """
    b = get_broker()
    if not b.simulator:
        raise HTTPException(400, "Simulator not running")

    from simulator.physics import TurbineSpec, TURBINE_PRESETS

    # Check for preset
    preset_name = spec_dict.pop("preset", None)
    if preset_name:
        if preset_name not in TURBINE_PRESETS:
            raise HTTPException(404, f"Unknown preset: {preset_name}. Available: {list(TURBINE_PRESETS.keys())}")
        new_spec = TURBINE_PRESETS[preset_name]
    else:
        # Get current spec and merge updates
        first_model = list(b.simulator.turbines.values())[0]
        current = first_model.spec.to_dict()
        current.update({k: v for k, v in spec_dict.items() if v is not None})
        new_spec = TurbineSpec.from_dict(current)

    # Apply to all turbines
    for model in b.simulator.turbines.values():
        model.update_spec(new_spec)

    return {"status": "ok", "spec": new_spec.to_dict()}


@router.get("/turbine-spec/presets")
async def list_turbine_presets():
    """List available turbine specification presets."""
    from simulator.physics import TURBINE_PRESETS
    return {
        name: spec.to_dict() for name, spec in TURBINE_PRESETS.items()
    }

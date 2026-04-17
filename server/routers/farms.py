"""
Wind Farm management API — CRUD, activate, clone, export.
"""

import io
import json
import re
import zipfile
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/api/farms", tags=["farms"])


def _get_registry():
    from server.app import farm_registry
    return farm_registry


def _get_broker():
    from server.app import broker
    return broker


def _sanitize_id(name: str) -> str:
    """Convert a display name to a valid farm_id slug."""
    s = re.sub(r"[^\w\s-]", "", name.lower())
    s = re.sub(r"[\s]+", "_", s.strip())
    return s[:60] or "farm"


# ── List / Get ──────────────────────────────────────────────────────────

@router.get("")
async def list_farms():
    """List all wind farm projects."""
    reg = _get_registry()
    farms = reg.list_farms()
    active_id = reg.get_active_farm_id()
    return {
        "active_farm_id": active_id,
        "farms": [f.to_dict() | {"is_active": f.farm_id == active_id} for f in farms],
    }


@router.get("/active")
async def get_active_farm():
    """Get the currently active wind farm."""
    reg = _get_registry()
    farm_id = reg.get_active_farm_id()
    if not farm_id:
        raise HTTPException(404, "No active farm")
    farm = reg.get_farm(farm_id)
    return farm.to_dict() | {"is_active": True}


@router.get("/{farm_id}")
async def get_farm(farm_id: str):
    """Get details of a specific wind farm."""
    farm = _get_registry().get_farm(farm_id)
    if not farm:
        raise HTTPException(404, f"Farm not found: {farm_id}")
    active_id = _get_registry().get_active_farm_id()
    return farm.to_dict() | {"is_active": farm_id == active_id}


# ── Create ──────────────────────────────────────────────────────────────

@router.post("")
async def create_farm(body: dict):
    """Create a new wind farm project.

    Required: name
    Optional: farm_id, turbine_count, preset, turbine_spec,
              wind_profile, grid_profile, location, description
    """
    reg = _get_registry()
    name = body.get("name")
    if not name:
        raise HTTPException(400, "name is required")

    farm_id = body.get("farm_id") or _sanitize_id(name)
    if reg.get_farm(farm_id):
        raise HTTPException(409, f"Farm already exists: {farm_id}")

    turbine_count = body.get("turbine_count", 14)
    turbine_spec = body.get("turbine_spec", {})

    preset_name = body.get("preset")
    if preset_name:
        from simulator.physics.turbine_physics import TURBINE_PRESETS
        if preset_name not in TURBINE_PRESETS:
            raise HTTPException(404, f"Unknown preset: {preset_name}. Available: {list(TURBINE_PRESETS.keys())}")
        turbine_spec = TURBINE_PRESETS[preset_name].to_dict()

    farm = reg.create_farm(
        farm_id=farm_id,
        name=name,
        turbine_count=turbine_count,
        turbine_spec=turbine_spec,
        wind_profile=body.get("wind_profile", {}),
        grid_profile=body.get("grid_profile", {}),
        layout=body.get("layout", {}),
        location=body.get("location", ""),
        description=body.get("description", ""),
    )
    return {"status": "created", "farm": farm.to_dict()}


# ── Update ──────────────────────────────────────────────────────────────

@router.patch("/{farm_id}")
async def update_farm(farm_id: str, body: dict):
    """Update farm metadata (name, description, location, turbine_spec, etc.)."""
    farm = _get_registry().update_farm(farm_id, **body)
    if not farm:
        raise HTTPException(404, f"Farm not found: {farm_id}")
    return {"status": "updated", "farm": farm.to_dict()}


# ── Delete ──────────────────────────────────────────────────────────────

@router.delete("/{farm_id}")
async def delete_farm(farm_id: str):
    """Delete a wind farm and all its data. Requires confirmation."""
    reg = _get_registry()
    if reg.get_active_farm_id() == farm_id:
        raise HTTPException(400, "Cannot delete the active farm. Switch to another farm first.")
    ok = reg.delete_farm(farm_id)
    if not ok:
        raise HTTPException(404, f"Farm not found: {farm_id}")
    return {"status": "deleted", "farm_id": farm_id}


# ── Activate ────────────────────────────────────────────────────────────

@router.post("/{farm_id}/activate")
async def activate_farm(farm_id: str):
    """Switch the simulator to this wind farm."""
    b = _get_broker()
    ok = b.switch_farm(farm_id)
    if not ok:
        raise HTTPException(404, f"Farm not found: {farm_id}")
    farm = _get_registry().get_farm(farm_id)
    return {"status": "activated", "farm": farm.to_dict()}


# ── Clone ───────────────────────────────────────────────────────────────

@router.post("/{farm_id}/clone")
async def clone_farm(farm_id: str, body: dict):
    """Clone a farm. Options: new_name (required), new_farm_id, include_data (bool)."""
    reg = _get_registry()
    new_name = body.get("new_name")
    if not new_name:
        raise HTTPException(400, "new_name is required")

    new_id = body.get("new_farm_id") or _sanitize_id(new_name)
    if reg.get_farm(new_id):
        raise HTTPException(409, f"Farm already exists: {new_id}")

    include_data = body.get("include_data", False)
    farm = reg.clone_farm(farm_id, new_id, new_name, include_data=include_data)
    if not farm:
        raise HTTPException(404, f"Source farm not found: {farm_id}")
    return {"status": "cloned", "farm": farm.to_dict()}


# ── Export ──────────────────────────────────────────────────────────────

@router.post("/{farm_id}/export")
async def export_farm(farm_id: str, body: dict = {}):
    """Export a farm as a zip file containing CSV data, events, and config.

    Options:
      format: "csv" (default)
      include_events: true (default)
    """
    reg = _get_registry()
    farm = reg.get_farm(farm_id)
    if not farm:
        raise HTTPException(404, f"Farm not found: {farm_id}")

    from server.storage import Storage
    db_path = str(reg.get_farm_db_path(farm_id))
    if not Path(db_path).exists():
        raise HTTPException(404, f"No data for farm: {farm_id}")

    storage = Storage(db_path=db_path)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("config.json", json.dumps(farm.to_dict(), indent=2, ensure_ascii=False))

        history = storage.query_history(limit=500000)
        if history:
            import csv
            csv_buf = io.StringIO()
            writer = csv.DictWriter(csv_buf, fieldnames=history[0].keys())
            writer.writeheader()
            for row in history:
                writer.writerow(dict(row))
            zf.writestr("history.csv", csv_buf.getvalue())

        include_events = body.get("include_events", True)
        if include_events:
            events = storage.query_events(limit=100000)
            if events:
                events_list = [dict(e) for e in events]
                zf.writestr("events.json", json.dumps(events_list, indent=2, ensure_ascii=False))

    buf.seek(0)
    filename = f"{farm_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Dataset Generation ──────────────────────────────────────────────────

@router.post("/{farm_id}/datasets/generate")
async def generate_dataset(farm_id: str, body: dict):
    """Generate a complete simulated dataset for a farm scenario.

    This is the one-click "set up scenario → run → get data" endpoint.

    Parameters:
      duration_hours: hours of simulation (required, max 8760)
      time_step: physics step in seconds (default 10)
      wind_profile: {base_speed, turbulence_intensity, ...} (optional override)
      grid_profile: {profile: "nominal"/"low_freq"/...} (optional)
      fault_steps: [{offset_hours, scenario_id, turbine_id, severity_rate, initial_severity}]
      output_format: "csv" (default)
    """
    reg = _get_registry()
    farm = reg.get_farm(farm_id)
    if not farm:
        raise HTTPException(404, f"Farm not found: {farm_id}")

    duration = body.get("duration_hours")
    if not duration or duration <= 0:
        raise HTTPException(400, "duration_hours is required and must be > 0")
    if duration > 8760:
        raise HTTPException(400, "Maximum 8760 hours (1 year)")

    time_step = body.get("time_step", 10.0)
    fault_steps = body.get("fault_steps", [])

    # Use a temporary simulator + storage for this farm
    from simulator.engine import WindFarmSimulator
    from simulator.physics.turbine_physics import TurbineSpec
    from server.storage import Storage

    spec = TurbineSpec.from_dict(farm.turbine_spec) if farm.turbine_spec else TurbineSpec()
    wind_cfg = body.get("wind_profile") or farm.wind_profile or {}
    base_wind = wind_cfg.get("base_speed", 10.0)
    turb_intensity = wind_cfg.get("turbulence_intensity", 0.12)

    sim = WindFarmSimulator(
        turbine_count=farm.turbine_count,
        base_wind_speed=base_wind,
        turbulence_intensity=turb_intensity,
    )
    for model in sim.turbines.values():
        model.update_spec(spec)

    # Use the farm's DB for storage
    db_path = str(reg.get_farm_db_path(farm_id))
    storage = Storage(db_path=db_path)
    session_id = storage.create_session(
        data_source="dataset_generation",
        turbine_count=farm.turbine_count,
        rated_power_kw=spec.rated_power_kw,
        rotor_diameter_m=spec.rotor_diameter,
        model_name=farm.name,
        config={
            "duration_hours": duration,
            "time_step": time_step,
            "wind_profile": wind_cfg,
            "fault_steps": fault_steps,
        },
    )

    # Sort fault steps by offset
    sorted_faults = sorted(fault_steps, key=lambda s: s.get("offset_hours", 0))
    fault_idx = 0

    total_steps = int(duration * 3600 / time_step)
    total_readings = 0

    from datetime import timedelta
    sim_time = datetime.now()

    for i in range(total_steps):
        if not sim._running:
            break

        sim_seconds = i * time_step

        # Inject scheduled faults
        while fault_idx < len(sorted_faults):
            fs = sorted_faults[fault_idx]
            offset_s = fs.get("offset_hours", 0) * 3600
            if offset_s > sim_seconds:
                break
            sim.fault_engine.inject(
                scenario_id=fs["scenario_id"],
                turbine_id=fs.get("turbine_id", "WT001"),
                severity_rate=fs.get("severity_rate", 0.001),
                initial_severity=fs.get("initial_severity", 0.0),
            )
            fault_idx += 1

        sim_time += timedelta(seconds=time_step)
        readings = sim._run_one_step(sim_time, time_step)
        total_readings += len(readings)
        storage.store_readings(readings, session_id)

    storage.run_downsampling()
    storage.end_session(session_id)
    sim.stop()

    return {
        "status": "ok",
        "farm_id": farm_id,
        "session_id": session_id,
        "duration_hours": duration,
        "time_step": time_step,
        "total_readings": total_readings,
        "fault_steps_executed": fault_idx,
        "export_url": f"/api/farms/{farm_id}/export",
    }

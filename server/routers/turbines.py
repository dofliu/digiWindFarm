from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from server.models import TurbineReading, FarmStatus

router = APIRouter(prefix="/api/turbines", tags=["turbines"])


def get_broker():
    from server.app import broker
    return broker


@router.get("", response_model=List[TurbineReading])
async def list_turbines():
    """List all turbines with latest data."""
    return get_broker().get_all_turbines()


@router.get("/farm-status", response_model=FarmStatus)
async def farm_status():
    """Get farm-level KPIs."""
    return get_broker().get_farm_status()


@router.get("/{turbine_id}", response_model=TurbineReading)
async def get_turbine(turbine_id: str):
    """Get single turbine current data."""
    reading = get_broker().get_turbine(turbine_id)
    if not reading:
        raise HTTPException(status_code=404, detail=f"Turbine {turbine_id} not found")
    return reading


@router.get("/{turbine_id}/history")
async def get_turbine_history(
    turbine_id: str,
    start: Optional[str] = Query(None, description="ISO datetime start"),
    end: Optional[str] = Query(None, description="ISO datetime end"),
    limit: int = Query(500, ge=1, le=10000),
):
    """Get turbine historical data (from SQLite)."""
    rows = get_broker().get_history(turbine_id, start, end, limit)
    return {"turbineId": turbine_id, "count": len(rows), "data": rows}


@router.get("/{turbine_id}/trend")
async def get_turbine_trend(
    turbine_id: str,
    tags: str = Query("WTUR_TotPwrAt,WMET_WSpeedNac", description="Comma-separated SCADA tag IDs"),
    limit: int = Query(120, ge=1, le=3600, description="Max data points"),
):
    """Get in-memory trend data for specific SCADA tags.

    Returns time-series arrays for each requested tag from the simulator's
    in-memory history buffer (up to 3600 points at 1Hz = 1 hour).
    Ideal for real-time trend charts.

    Example: /api/turbines/WT001/trend?tags=WTUR_TotPwrAt,WGEN_GnBrgTmp1,WNAC_VibMsNacXDir&limit=120
    """
    b = get_broker()
    if not b.simulator:
        raise HTTPException(400, "Simulator not running")

    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    history = b.simulator.get_history(turbine_id, limit=limit)

    if not history:
        raise HTTPException(404, f"No history for {turbine_id}")

    # Build time-series: [{timestamp, tag1, tag2, ...}, ...]
    series = []
    for point in history:
        scada = point.get("scada", {})
        ts = point.get("timestamp", "")
        entry = {"timestamp": ts}
        for tag in tag_list:
            entry[tag] = scada.get(tag)
        series.append(entry)

    return {
        "turbineId": turbine_id,
        "tags": tag_list,
        "count": len(series),
        "data": series,
    }

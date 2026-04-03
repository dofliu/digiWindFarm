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
    """Get turbine historical data."""
    rows = get_broker().get_history(turbine_id, start, end, limit)
    return {"turbineId": turbine_id, "count": len(rows), "data": rows}

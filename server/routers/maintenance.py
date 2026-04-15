"""
Maintenance work order and technician management API.

Replaces the frontend mock data with real persistent storage.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(prefix="/api/maintenance", tags=["maintenance"])


def get_broker():
    """Return the shared DataBroker instance from the main app module."""
    from server.app import broker
    return broker


# ── Request / Response Models ──

class CreateWorkOrderRequest(BaseModel):
    turbineId: int
    turbineName: str
    faultDescription: str
    technicianId: Optional[int] = None


class UpdateWorkOrderRequest(BaseModel):
    status: Optional[str] = None   # OPEN, IN_PROGRESS, COMPLETED
    notes: Optional[str] = None
    photos: Optional[List[str]] = None  # base64 strings


class UpdateTechnicianRequest(BaseModel):
    status: str  # ON_DUTY, OFF_DUTY, DISPATCHED


class CreateTechnicianRequest(BaseModel):
    name: str
    status: str = "ON_DUTY"


# ── Work Order Endpoints ──

@router.get("/work-orders")
async def list_work_orders(
    status: Optional[str] = Query(None, description="Filter by status"),
    turbine_id: Optional[int] = Query(None, description="Filter by turbine"),
    limit: int = Query(100, ge=1, le=1000),
):
    """List all work orders, newest first."""
    storage = get_broker().storage
    orders = storage.query_work_orders(status=status, turbine_id=turbine_id, limit=limit)
    return {"count": len(orders), "data": orders}


@router.post("/work-orders")
async def create_work_order(req: CreateWorkOrderRequest):
    """Create a new work order and optionally dispatch a technician."""
    storage = get_broker().storage
    wo = storage.create_work_order(
        turbine_id=req.turbineId,
        turbine_name=req.turbineName,
        fault_description=req.faultDescription,
        technician_id=req.technicianId,
    )

    # If technician assigned, set them to DISPATCHED
    if req.technicianId is not None:
        storage.update_technician(req.technicianId, status="DISPATCHED")

    # Record event
    get_broker().record_event(
        event_type="operator",
        source="maintenance",
        title="Work order created",
        turbine_id=f"WT{req.turbineId:03d}",
        detail=f"WO {wo['id']}: {req.faultDescription}",
        payload={"workOrderId": wo["id"], "turbineId": req.turbineId, "technicianId": req.technicianId},
    )
    return wo


@router.get("/work-orders/{work_order_id}")
async def get_work_order(work_order_id: str):
    """Get a single work order by ID."""
    storage = get_broker().storage
    wo = storage.get_work_order(work_order_id)
    if not wo:
        raise HTTPException(404, f"Work order {work_order_id} not found")
    return wo


@router.patch("/work-orders/{work_order_id}")
async def update_work_order(work_order_id: str, req: UpdateWorkOrderRequest):
    """Update work order status, notes, or photos."""
    storage = get_broker().storage
    wo = storage.get_work_order(work_order_id)
    if not wo:
        raise HTTPException(404, f"Work order {work_order_id} not found")

    updates = {}
    if req.status is not None:
        if req.status not in ("OPEN", "IN_PROGRESS", "COMPLETED"):
            raise HTTPException(400, f"Invalid status: {req.status}")
        updates["status"] = req.status
    if req.notes is not None:
        updates["notes"] = req.notes
    if req.photos is not None:
        updates["photos"] = req.photos

    updated = storage.update_work_order(work_order_id, **updates)

    # If completed, release technician
    if req.status == "COMPLETED" and wo.get("technician_id"):
        storage.update_technician(wo["technician_id"], status="ON_DUTY")

    # Record event
    if req.status:
        get_broker().record_event(
            event_type="operator",
            source="maintenance",
            title=f"Work order {req.status.lower()}",
            turbine_id=f"WT{wo.get('turbine_id', 0):03d}" if wo.get("turbine_id") else None,
            detail=f"WO {work_order_id} status changed to {req.status}",
            payload={"workOrderId": work_order_id, "status": req.status},
        )

    return updated


# ── Technician Endpoints ──

@router.get("/technicians")
async def list_technicians():
    """List all technicians."""
    storage = get_broker().storage
    techs = storage.query_technicians()
    return {"count": len(techs), "data": techs}


@router.post("/technicians")
async def create_technician(req: CreateTechnicianRequest):
    """Create a new technician."""
    storage = get_broker().storage
    tech = storage.create_technician(req.name, req.status)
    return tech


@router.patch("/technicians/{technician_id}/status")
async def update_technician_status(technician_id: int, req: UpdateTechnicianRequest):
    """Update technician duty status."""
    storage = get_broker().storage
    if req.status not in ("ON_DUTY", "OFF_DUTY", "DISPATCHED"):
        raise HTTPException(400, f"Invalid status: {req.status}")
    updated = storage.update_technician(technician_id, status=req.status)
    if not updated:
        raise HTTPException(404, f"Technician {technician_id} not found")
    return updated


# ── Multi-Turbine Event Comparison ──

@router.get("/events/compare")
async def compare_turbine_events(
    turbine_ids: str = Query(..., description="Comma-separated turbine IDs (e.g. WT001,WT002,WT003)"),
    start: Optional[str] = Query(None, description="ISO datetime start"),
    end: Optional[str] = Query(None, description="ISO datetime end"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    limit: int = Query(500, ge=1, le=5000),
):
    """Compare events across multiple turbines side-by-side.

    Returns events grouped by turbine for timeline comparison.
    """
    tid_list = [t.strip() for t in turbine_ids.split(",") if t.strip()]
    if not tid_list:
        raise HTTPException(400, "At least one turbine_id is required")
    if len(tid_list) > 14:
        raise HTTPException(400, "Maximum 14 turbines for comparison")

    storage = get_broker().storage
    result = {}
    all_events = []

    for tid in tid_list:
        events = storage.query_events(turbine_id=tid, start=start, end=end, limit=limit)
        if event_type:
            events = [e for e in events if e.get("event_type") == event_type]
        result[tid] = events
        for ev in events:
            ev["_turbine_id"] = tid
            all_events.append(ev)

    # Also get farm-wide events (turbine_id is NULL)
    farm_events = storage.query_events(turbine_id=None, start=start, end=end, limit=limit)
    if event_type:
        farm_events = [e for e in farm_events if e.get("event_type") == event_type]

    # Build timeline: merge all events sorted by time
    all_events.sort(key=lambda e: e.get("timestamp", ""), reverse=True)

    # Summary statistics
    summary = {}
    for tid in tid_list:
        tid_events = result[tid]
        summary[tid] = {
            "total": len(tid_events),
            "by_type": {},
        }
        for ev in tid_events:
            et = ev.get("event_type", "other")
            summary[tid]["by_type"][et] = summary[tid]["by_type"].get(et, 0) + 1

    return {
        "turbines": tid_list,
        "per_turbine": result,
        "farm_events": farm_events,
        "timeline": all_events[:limit],
        "summary": summary,
    }

"""Fault injection API — inject, monitor, and clear simulated faults."""

from fastapi import APIRouter, HTTPException
from server.models import FaultInjectionRequest, FaultClearRequest

router = APIRouter(prefix="/api/faults", tags=["faults"])


def get_broker():
    from server.app import broker
    return broker


@router.get("/scenarios")
async def list_scenarios():
    """List all available fault scenarios (for UI dropdown)."""
    b = get_broker()
    if not b.simulator:
        raise HTTPException(400, "Simulator not running")

    scenarios = b.simulator.fault_engine.get_scenarios()
    return [
        {
            "id": s.id,
            "name_en": s.name_en,
            "name_zh": s.name_zh,
            "description_en": s.description_en,
            "description_zh": s.description_zh,
            "affected_tags": list(s.affected_tags.keys()),
            "alarm_codes": s.alarm_codes,
        }
        for s in scenarios.values()
    ]


@router.post("/inject")
async def inject_fault(req: FaultInjectionRequest):
    """Inject a fault into a specific turbine."""
    b = get_broker()
    if not b.simulator:
        raise HTTPException(400, "Simulator not running")

    ok = b.simulator.fault_engine.inject(
        scenario_id=req.scenarioId,
        turbine_id=req.turbineId,
        severity_rate=req.severityRate,
        initial_severity=req.initialSeverity,
    )
    if not ok:
        raise HTTPException(404, f"Unknown scenario: {req.scenarioId}")

    return {"status": "injected", "scenarioId": req.scenarioId, "turbineId": req.turbineId}


@router.get("/active")
async def get_active_faults():
    """Get status of all active faults across the farm."""
    b = get_broker()
    if not b.simulator:
        return []
    return b.simulator.fault_engine.get_fault_status()


@router.post("/clear")
async def clear_faults(req: FaultClearRequest):
    """Clear faults. Omit both fields to clear all."""
    b = get_broker()
    if not b.simulator:
        raise HTTPException(400, "Simulator not running")

    b.simulator.fault_engine.clear(
        turbine_id=req.turbineId,
        scenario_id=req.scenarioId,
    )
    # Reset tripped turbines back to normal
    if req.turbineId and req.turbineId in b.simulator.turbines:
        b.simulator.turbines[req.turbineId].reset()

    return {"status": "cleared"}

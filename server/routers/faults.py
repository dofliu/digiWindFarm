"""Fault injection API — inject, monitor, and clear simulated faults.

Includes test plan system for automated fault sequences.
"""

from fastapi import APIRouter, HTTPException
from server.models import FaultInjectionRequest, FaultClearRequest
from simulator.physics.fault_engine import TEST_PLANS

router = APIRouter(prefix="/api/faults", tags=["faults"])


def get_broker():
    """Return the shared DataBroker instance from the main app module."""
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

    b.record_event(
        event_type="fault",
        source="faults",
        title=f"Fault injected: {req.scenarioId}",
        turbine_id=req.turbineId,
        detail=f"Injected {req.scenarioId} on {req.turbineId}",
        payload={
            "scenarioId": req.scenarioId,
            "turbineId": req.turbineId,
            "severityRate": req.severityRate,
            "initialSeverity": req.initialSeverity,
        },
    )

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

    b.record_event(
        event_type="fault",
        source="faults",
        title="Faults cleared",
        turbine_id=req.turbineId,
        detail=f"Cleared faults for {req.turbineId or 'all turbines'}",
        payload={"turbineId": req.turbineId, "scenarioId": req.scenarioId},
    )

    return {"status": "cleared"}


# ─── Test Plans ───────────────────────────────────────────────────────

@router.get("/test-plans")
async def list_test_plans():
    """List available fault injection test plans."""
    plans = []
    for plan_id, plan in TEST_PLANS.items():
        plans.append({
            "id": plan_id,
            "name_en": plan["name_en"],
            "name_zh": plan["name_zh"],
            "description_en": plan["description_en"],
            "description_zh": plan["description_zh"],
            "duration_hours": plan["duration_hours"],
            "fault_count": len(plan["steps"]),
            "turbines_affected": list(set(s.turbine_id for s in plan["steps"])),
            "scenarios_used": list(set(s.scenario_id for s in plan["steps"])),
        })
    return plans


@router.post("/test-plans/{plan_id}/run")
async def run_test_plan(plan_id: str, body: dict = {}):
    """Run a test plan: generate bulk data with scheduled fault injections.

    This generates the full duration of simulated data with faults injected
    at their scheduled offsets. Data is written to SQLite.

    Options:
      time_step: physics step in seconds (default 10)
    """
    b = get_broker()
    if not b.simulator:
        raise HTTPException(400, "Simulator not running")

    plan = TEST_PLANS.get(plan_id)
    if not plan:
        raise HTTPException(404, f"Unknown test plan: {plan_id}. Available: {list(TEST_PLANS.keys())}")

    time_step = body.get("time_step", 10.0)
    duration = plan["duration_hours"]
    steps = sorted(plan["steps"], key=lambda s: s.offset_seconds)

    # Clear any existing faults
    b.simulator.fault_engine.clear()

    session_id = b._session_id
    total_steps = int(duration * 3600 / time_step)
    step_idx = 0  # next fault step to inject
    total_readings = 0
    from datetime import datetime, timedelta
    sim_time = datetime.now()

    for i in range(total_steps):
        if not b.simulator._running:
            break

        sim_seconds = i * time_step

        # Check if any fault steps should be injected at this time
        while step_idx < len(steps) and steps[step_idx].offset_seconds <= sim_seconds:
            s = steps[step_idx]
            b.simulator.fault_engine.inject(
                scenario_id=s.scenario_id,
                turbine_id=s.turbine_id,
                severity_rate=s.severity_rate,
                initial_severity=s.initial_severity,
            )
            b.record_event(
                event_type="fault",
                source="test_plan",
                title=f"Test plan: {s.scenario_id} on {s.turbine_id}",
                turbine_id=s.turbine_id,
                detail=s.description,
                payload={
                    "plan_id": plan_id,
                    "scenarioId": s.scenario_id,
                    "severityRate": s.severity_rate,
                },
            )
            step_idx += 1

        # Run physics step
        sim_time += timedelta(seconds=time_step)
        readings = b.simulator._run_one_step(sim_time, time_step)
        total_readings += len(readings)

        # Store to database
        b.storage.store_readings(readings, session_id)

    # Downsampling after bulk generation
    b.storage.run_downsampling()

    # Get final fault status
    fault_status = b.simulator.fault_engine.get_fault_status()

    stats = b.storage.get_db_stats()
    return {
        "status": "completed",
        "plan_id": plan_id,
        "duration_hours": duration,
        "total_readings": total_readings,
        "faults_injected": len(steps),
        "final_fault_status": fault_status,
        "storage_stats": stats,
    }

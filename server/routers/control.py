"""Turbine operator control API — stop/start/reset/curtail/service mode."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/control", tags=["control"])


def get_broker():
    from server.app import broker
    return broker


class TurbineCommand(BaseModel):
    """Command payload for turbine control."""
    turbineId: str
    command: str   # "stop", "emergency_stop", "start", "reset", "service_on", "service_off"


class CurtailCommand(BaseModel):
    """Set per-turbine power curtailment."""
    turbineId: str
    powerLimitKw: Optional[float] = None  # None = remove curtailment


@router.post("/command")
async def send_command(cmd: TurbineCommand):
    """Send operator command to a turbine.

    Commands (mapped to Bachmann Modbus Coil[1-3]):
      - stop:        Manual stop (Coil[2], normal shutdown)
      - emergency_stop: Immediate shutdown / trip-style stop
      - start:       Manual start (Coil[1], resume from stop/standby)
      - reset:       Reset faults & restart (Coil[3])
      - service_on:  Enter maintenance/inspection mode (WSRV_SrvOn=1)
      - service_off: Exit maintenance mode (WSRV_SrvOn=0)
    """
    b = get_broker()
    if not b.simulator:
        raise HTTPException(400, "Simulator not running")

    model = b.simulator.turbines.get(cmd.turbineId)
    if not model:
        raise HTTPException(404, f"Turbine {cmd.turbineId} not found")

    if cmd.command == "stop":
        model.cmd_stop()
    elif cmd.command == "emergency_stop":
        model.cmd_emergency_stop(cause="operator_emergency")
    elif cmd.command == "start":
        model.cmd_start()
    elif cmd.command == "reset":
        model.cmd_reset()
        # Also clear faults from fault engine
        b.simulator.fault_engine.clear(turbine_id=cmd.turbineId)
    elif cmd.command == "service_on":
        model.cmd_service(True)
    elif cmd.command == "service_off":
        model.cmd_service(False)
    else:
        raise HTTPException(400, f"Unknown command: {cmd.command}. Use: stop, emergency_stop, start, reset, service_on, service_off")

    b.record_event(
        event_type="operator",
        source="control",
        title=f"Operator command: {cmd.command}",
        turbine_id=cmd.turbineId,
        detail=f"Command {cmd.command} issued to {cmd.turbineId}",
        payload={"command": cmd.command, "turbineId": cmd.turbineId},
    )

    return {
        "status": "ok",
        "turbineId": cmd.turbineId,
        "command": cmd.command,
        "control": model.get_control_status(),
    }


@router.post("/curtail")
async def set_curtailment(cmd: CurtailCommand):
    """Set per-turbine power curtailment (限載).

    Set powerLimitKw to limit output. Set to null to remove curtailment.
    Pitch angle will automatically adjust to maintain the power limit.
    """
    b = get_broker()
    if not b.simulator:
        raise HTTPException(400, "Simulator not running")

    model = b.simulator.turbines.get(cmd.turbineId)
    if not model:
        raise HTTPException(404, f"Turbine {cmd.turbineId} not found")

    model.cmd_curtail(cmd.powerLimitKw)
    b.record_event(
        event_type="operator",
        source="control",
        title="Curtailment updated",
        turbine_id=cmd.turbineId,
        detail=f"Curtailment set to {cmd.powerLimitKw if cmd.powerLimitKw is not None else 'off'} kW",
        payload={"turbineId": cmd.turbineId, "powerLimitKw": cmd.powerLimitKw},
    )
    return {
        "status": "ok",
        "turbineId": cmd.turbineId,
        "curtailment_kw": cmd.powerLimitKw,
        "control": model.get_control_status(),
    }


@router.get("/{turbine_id}/status")
async def get_control_status(turbine_id: str):
    """Get current operator control status for a turbine."""
    b = get_broker()
    if not b.simulator:
        raise HTTPException(400, "Simulator not running")

    model = b.simulator.turbines.get(turbine_id)
    if not model:
        raise HTTPException(404, f"Turbine {turbine_id} not found")

    return {
        "turbineId": turbine_id,
        **model.get_control_status(),
    }

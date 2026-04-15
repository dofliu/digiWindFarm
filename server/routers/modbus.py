"""Modbus TCP simulator server control API."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/modbus", tags=["modbus"])


def get_broker():
    """Return the shared DataBroker instance from the main app module."""
    from server.app import broker
    return broker


class ModbusStartRequest(BaseModel):
    port: int = 5020


@router.get("/status")
async def modbus_status():
    """Get Modbus server status."""
    b = get_broker()
    if not b.simulator:
        return {"running": False, "message": "Simulator not running"}
    if not b.simulator.modbus_server:
        return {"running": False, "message": "Modbus server not created"}
    return b.simulator.modbus_server.get_status()


@router.post("/start")
async def modbus_start(req: ModbusStartRequest):
    """Start the Modbus TCP simulator server."""
    b = get_broker()
    if not b.simulator:
        raise HTTPException(400, "Simulator not running")

    from simulator.modbus_server import ModbusSimServer
    if b.simulator.modbus_server and b.simulator.modbus_server.is_running:
        return {"status": "already_running", **b.simulator.modbus_server.get_status()}

    b.simulator.modbus_server = ModbusSimServer(
        port=req.port,
        turbine_count=len(b.simulator.turbines),
    )
    b.simulator.modbus_server.start()
    return {"status": "started", "port": req.port, "turbine_count": len(b.simulator.turbines)}


@router.post("/stop")
async def modbus_stop():
    """Stop the Modbus TCP simulator server."""
    b = get_broker()
    if b.simulator and b.simulator.modbus_server:
        b.simulator.modbus_server.stop()
        b.simulator.modbus_server = None
    return {"status": "stopped"}


@router.get("/registers")
async def get_register_map():
    """Get the Modbus register map (for documentation)."""
    from simulator.modbus_server import ModbusSimServer
    return ModbusSimServer.get_register_map()

import asyncio
import json
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import List

from server.models import DataSourceConfig, DataSourceMode, SimulationConfig
from server.farm_registry import FarmRegistry
from server.data_broker import DataBroker

# Global instances
farm_registry = FarmRegistry()
broker = DataBroker(farm_registry=farm_registry)

# WebSocket connection manager
ws_clients: List[WebSocket] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle: start simulator and Modbus on startup, clean up on shutdown."""
    # Migrate legacy DB if it exists
    from pathlib import Path
    legacy_path = Path(__file__).parent.parent / "wind_farm_data.db"
    migrated = farm_registry.migrate_legacy_db(legacy_path)
    if migrated:
        print(f"[Server] Migrated legacy database to farm '{migrated}'")

    # Determine active farm and its config
    farm_id = farm_registry.ensure_default_farm()
    farm = farm_registry.get_farm(farm_id)
    turbine_count = farm.turbine_count if farm else 14
    print(f"[Server] Active farm: {farm_id} ({turbine_count} turbines)")

    # Startup: start simulator with active farm
    config = DataSourceConfig(mode=DataSourceMode.SIMULATION)
    sim_config = SimulationConfig(turbineCount=turbine_count)
    broker.start(config, sim_config)

    # Apply farm turbine spec if defined
    if farm and farm.turbine_spec and broker.simulator:
        from simulator.physics.turbine_physics import TurbineSpec
        try:
            spec = TurbineSpec.from_dict(farm.turbine_spec)
            for model in broker.simulator.turbines.values():
                model.update_spec(spec)
            print("[Server] Applied turbine spec from farm config")
        except Exception as e:
            print(f"[Server] Warning: could not apply farm spec: {e}")

    print(f"[Server] Wind farm simulator started with {turbine_count} turbines")

    # Auto-start Modbus TCP server
    if broker.simulator:
        from simulator.modbus_server import ModbusSimServer
        modbus_port = int(os.environ.get("MODBUS_PORT", "5020"))
        broker.simulator.modbus_server = ModbusSimServer(
            port=modbus_port, turbine_count=len(broker.simulator.turbines)
        )
        broker.simulator.modbus_server.start()
        print(f"[Server] Modbus TCP server started on port {modbus_port}")

    # Start WebSocket broadcast task
    task = asyncio.create_task(_ws_broadcast_loop())

    yield

    # Shutdown
    task.cancel()
    if broker.simulator and broker.simulator.modbus_server:
        broker.simulator.modbus_server.stop()
    broker.stop()
    print("[Server] Shutdown complete")


app = FastAPI(
    title="Wind Farm Monitor API",
    description="Real-time wind farm monitoring with simulation and OPC DA support",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers (after app creation to avoid circular imports)
from server.routers.turbines import router as turbines_router  # noqa: E402
from server.routers.config import router as config_router  # noqa: E402
from server.routers.export import router as export_router  # noqa: E402
from server.routers.faults import router as faults_router  # noqa: E402
from server.routers.i18n import router as i18n_router  # noqa: E402
from server.routers.modbus import router as modbus_router  # noqa: E402
from server.routers.control import router as control_router  # noqa: E402
from server.routers.maintenance import router as maintenance_router  # noqa: E402
from server.routers.farms import router as farms_router  # noqa: E402

app.include_router(turbines_router)
app.include_router(config_router)
app.include_router(export_router)
app.include_router(faults_router)
app.include_router(i18n_router)
app.include_router(modbus_router)
app.include_router(control_router)
app.include_router(maintenance_router)
app.include_router(farms_router)


@app.get("/api/health")
async def health():
    """Return system health status including data source mode and turbine count."""
    return {
        "status": "ok",
        "mode": broker.mode.value,
        "turbineCount": len(broker.turbine_ids),
        "activeFarmId": broker.active_farm_id,
    }


@app.websocket("/ws/realtime")
async def websocket_realtime(ws: WebSocket):
    """Handle a WebSocket connection for real-time SCADA data streaming."""
    await ws.accept()
    ws_clients.append(ws)
    try:
        while True:
            # Keep connection alive, receive any client messages (ignored)
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        if ws in ws_clients:
            ws_clients.remove(ws)


async def _ws_broadcast_loop():
    """Broadcast turbine data to all WebSocket clients every 2 seconds."""
    while True:
        await asyncio.sleep(2)
        if not ws_clients:
            continue

        turbines = broker.get_all_turbines()
        if not turbines:
            continue

        data = json.dumps(
            [t.model_dump(mode='json') for t in turbines],
            default=str,
        )

        disconnected = []
        for ws in ws_clients:
            try:
                await ws.send_text(data)
            except Exception:
                disconnected.append(ws)

        for ws in disconnected:
            if ws in ws_clients:
                ws_clients.remove(ws)

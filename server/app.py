import asyncio
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import List

from server.models import DataSourceConfig, DataSourceMode, SimulationConfig
from server.data_broker import DataBroker

# Global broker instance
broker = DataBroker()

# WebSocket connection manager
ws_clients: List[WebSocket] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: start simulator
    config = DataSourceConfig(mode=DataSourceMode.SIMULATION)
    sim_config = SimulationConfig(turbineCount=14)
    broker.start(config, sim_config)
    print("[Server] Wind farm simulator started with 14 turbines")

    # Start WebSocket broadcast task
    task = asyncio.create_task(_ws_broadcast_loop())

    yield

    # Shutdown
    task.cancel()
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

# Register routers
from server.routers.turbines import router as turbines_router
from server.routers.config import router as config_router
from server.routers.export import router as export_router
from server.routers.faults import router as faults_router
from server.routers.i18n import router as i18n_router

app.include_router(turbines_router)
app.include_router(config_router)
app.include_router(export_router)
app.include_router(faults_router)
app.include_router(i18n_router)


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "mode": broker.mode.value,
        "turbineCount": len(broker.turbine_ids),
    }


@app.websocket("/ws/realtime")
async def websocket_realtime(ws: WebSocket):
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

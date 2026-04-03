# Wind Farm Monitor Platform

## Quick Start

```bash
# Backend (port 8000)
cd digiWindTurbine
pip install -r requirements.txt
python run.py

# Frontend (port 3000, another terminal)
cd digiWindTurbine/frontend
npm install
npm run dev
```

Open http://localhost:3000 → Settings → select "Physics Simulation (Backend)" to use real-time simulation data.

---

## Project Overview

Integrated wind farm monitoring platform combining:
1. **Physics-based wind turbine simulator** — produces realistic SCADA data (wind speed, power, temperatures, vibrations...)
2. **OPC DA adapter** — connects to real Bachmann/Vestas wind farm controllers
3. **FastAPI backend** — REST API + WebSocket for real-time data streaming
4. **React frontend** — monitoring dashboard with AI fault diagnosis, maintenance dispatch

The platform can **switch between simulated and real data sources** at runtime via the Settings page or API.

---

## Architecture

```
┌─ Data Source (switchable) ────────────────────────┐
│  Simulator (Physics)  ←→  OPC DA (Real Wind Farm) │
│  wind_model.py             opc_adapter.py         │
│  turbine_model.py          (Bachmann/Vestas)      │
│  subsystems.py (7 subsystems)                     │
└──────────────┬────────────────────────────────────┘
               │
        ┌──────▼──────┐
        │ DataBroker   │  unified interface
        └──────┬──────┘
               │
┌──────────────▼────────────────────────────────────┐
│  FastAPI Backend (port 8000)                       │
│  REST: /api/turbines, /api/config, /api/export     │
│  WebSocket: /ws/realtime (2s push)                 │
│  SQLite: wind_farm_data.db (persistent history)    │
└──────────────┬────────────────────────────────────┘
               │
┌──────────────▼────────────────────────────────────┐
│  React 19 Frontend (port 3000)                     │
│  useRealtimeData hook (WS + REST fallback)         │
│  FarmOverview / TurbineDetail / MaintenanceHub     │
└───────────────────────────────────────────────────┘
```

---

## Directory Structure

```
digiWindTurbine/
├── run.py                     # Entry point: starts FastAPI + simulator
├── requirements.txt           # Python deps: fastapi, uvicorn, numpy, pydantic
│
├── server/                    # FastAPI backend
│   ├── app.py                 # FastAPI app, WebSocket broadcast, lifespan
│   ├── data_broker.py         # DataBroker: unified interface, mode switching
│   ├── models.py              # Pydantic models (TurbineReading, FarmStatus, configs)
│   ├── storage.py             # SQLite persistence (wind_farm_data.db)
│   ├── opc_adapter.py         # OPC DA adapter (Bachmann Z72, Vestas CK1/CK2 tag maps)
│   └── routers/
│       ├── turbines.py        # GET /api/turbines, /api/turbines/{id}/history, /farm-status
│       ├── config.py          # GET/POST /api/config, /api/config/simulation, /datasource
│       └── export.py          # GET /api/export/snapshot, /api/export/history?format=csv
│
├── simulator/                 # Refactored simulation engine
│   └── engine.py              # WindFarmSimulator class (callback-based, thread-safe)
│
├── wind_model.py              # Original: wind environment model (daily pattern + turbulence)
├── turbine_model.py           # Original: WindTurbine class (physics model)
├── subsystems.py              # Original: 7 subsystems (rotor, gearbox, generator, pitch, yaw, hydraulic, control)
├── common_types.py            # Original: TurbineParameters dataclass
│
├── main.py                    # Original standalone simulator (preserved, not used by platform)
├── opcua_interface.py         # Original OPC UA server (preserved, not used by platform)
├── scada_system.py            # Original SCADA + SQLite (preserved, not used by platform)
├── dashboard.py               # Original Dash dashboard (preserved, not used by platform)
│
├── frontend/                  # React 19 + Vite + Tailwind
│   ├── App.tsx                # Main app (auto-switches mock ↔ realtime based on settings)
│   ├── types.ts               # TurbineData, AppSettings, DataSourceType enums
│   ├── vite.config.ts         # Dev proxy: /api → :8000, /ws → ws://:8000
│   ├── hooks/
│   │   ├── useRealtimeData.ts # NEW: WebSocket + REST connection to FastAPI backend
│   │   ├── useMockTurbineData.ts  # Frontend-only mock (for dev without backend)
│   │   ├── useMockMaintenanceData.ts
│   │   └── useSettings.ts    # Modified: syncs dataSource/simulation config to backend
│   ├── components/
│   │   ├── FarmOverview.tsx   # Wind farm overview with turbine grid
│   │   ├── TurbineDetail.tsx  # Single turbine detail + AI diagnosis
│   │   ├── SettingsPage.tsx   # Modified: simulation params + OPC DA + data source toggle
│   │   ├── MaintenanceHub.tsx # Work order management
│   │   ├── DispatchModal.tsx  # Technician dispatch
│   │   ├── Gauge.tsx, MiniTrendChart.tsx, StatusIndicator.tsx, DataCard.tsx
│   │   └── icons.tsx
│   └── services/
│       └── geminiService.ts   # Gemini AI integration for fault diagnosis
│
├── wind_farm_data.db          # Auto-created SQLite database (gitignore this)
└── config/                    # Reserved for future YAML configs
```

---

## API Reference

### Turbine Data
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Server status, mode, turbine count |
| GET | `/api/turbines` | All turbines with latest data (TurbineReading[]) |
| GET | `/api/turbines/{id}` | Single turbine (e.g., `WT001`) |
| GET | `/api/turbines/{id}/history?start=&end=&limit=` | Historical time-series |
| GET | `/api/turbines/farm-status` | Farm KPIs (FarmStatus) |

### Configuration
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/config` | Current mode and turbine count |
| POST | `/api/config/datasource` | Switch mode: `{"mode": "simulation"}` or `{"mode": "opc_da", "opcProgId": "..."}` |
| POST | `/api/config/simulation` | Set simulation params: `{"turbineCount": 14, "baseWindSpeed": 10.0, "turbulenceIntensity": 0.1}` |

### Data Export (for external analysis projects)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/export/snapshot` | Current state of all turbines as JSON |
| GET | `/api/export/history?turbine_id=WT001&format=json` | History as JSON |
| GET | `/api/export/history?turbine_id=WT001&format=csv` | History as CSV download |

### WebSocket
| Endpoint | Description |
|----------|-------------|
| `ws://localhost:8000/ws/realtime` | Pushes TurbineReading[] every 2 seconds |

---

## Data Model (TurbineReading)

```python
class TurbineReading:
    turbineId: str          # "WT001"
    name: str               # "WTG-01"
    timestamp: datetime
    status: str             # OPERATING, IDLE, FAULT, OFFLINE
    windSpeed: float        # m/s
    powerOutput: float      # MW
    rotorSpeed: float       # RPM
    bladeAngle: float       # degrees (pitch)
    temperature: float      # generator temp °C
    vibration: float        # gearbox vibration mm/s
    voltage: float          # V
    current: float          # A
    yawAngle: float         # degrees
    gearboxTemp: float      # °C
    frequency: float | None # Hz
    hydraulicPressure: float | None  # bar
    history: list | None    # [{time, power}] for frontend chart
```

This model matches the frontend `TurbineData` interface in `frontend/types.ts`.

---

## Physics Simulator Details

The simulator uses physical models to generate realistic wind turbine data:

- **Wind Model** (`wind_model.py`): Daily pattern (3-10 m/s cycle) + configurable turbulence intensity
- **Turbine Model** (`turbine_model.py`): P = 0.5 * rho * A * V^3 * Cp, state machine (IDLE→STARTING→RUNNING→STOPPING)
- **Subsystems** (`subsystems.py`):
  - Rotor: Cp curve (Gaussian, max 0.48 at TSR ~7.5), momentum theory
  - Gearbox: 100:1 ratio, thermal model, vibration
  - Generator: 95% efficiency, 690V nominal, thermal model
  - Pitch: 0° at rated, linear ramp to 30° above rated wind
  - Yaw: error-correction, 0.5°/step adjustment
  - Hydraulic: pressure model
  - Control: state management

**TurbineParameters defaults**: 5MW rated, 126m rotor, 90m hub, cut-in 3 m/s, rated 12 m/s, cut-out 25 m/s.

---

## OPC DA Adapter

`server/opc_adapter.py` supports real wind farm connections:

| Farm | OPC Server | Turbines | Tags |
|------|-----------|----------|------|
| Z72 (Bachmann) | `BACHMANN.OPCEnterpriseServer.2` | 30 (H01-H30) | WSpeedNacAvg10m, TurSt, ActiveAlarm[0-9] |
| CK1 (Vestas) | `Vestas.VOBOPCServerDA.3` | 23 (WTG01-23) | WindSpeed, Power, RPM, Temperature, State |
| CK2 (Vestas) | `Vestas.VOBOPCServerDA.3` | 8 (WTG24-31) | same as CK1 |

Requires: OpenOPC2 + Graybox.OPC.DAWrapper (Windows, 32-bit Python). Falls back to simulation if OPC not available.

Reference implementation: `opc_bachmann/VestasOPCconnect/` (production OPC readers, config files).

---

## Frontend Data Flow

```
Settings page → dataSource = MOCK | SIMULATION | OPC_DA

MOCK → useMockTurbineData.ts (frontend random, no backend needed)
SIMULATION/OPC_DA → useRealtimeData.ts → WebSocket ws://:8000/ws/realtime
                                         + REST fallback GET /api/turbines
```

Both hooks return the same `{ turbines, updateTurbineStatus }` interface so components are data-source agnostic.

---

## Known Issues / TODO

1. **Fault injection not implemented** — simulator produces only normal operation, no fault scenarios yet
2. **WorkOrderDetailModal.tsx** has a pre-existing TypeScript error (Blob type mismatch) — from original windfFrmSCADA, doesn't affect build
3. **OPC DA adapter** is skeleton-level — tag mapping exists but not tested against real OPC servers in this integrated setup
4. **No authentication** — all API endpoints are open; add JWT if deploying beyond local dev
5. **Gemini AI service** needs `GEMINI_API_KEY` in `frontend/.env.local` for AI diagnosis feature
6. **History data grows unbounded** — consider adding a cleanup job or switching to TimescaleDB for production
7. **Frontend `npm run dev`** proxies to backend; for production, build with `npm run build` and serve `dist/` from FastAPI

---

## Related Projects (same parent folder)

These projects are NOT part of the platform but share data formats:

- `H127_Diagnosis/` — Power forecasting & fault diagnosis research (real SCADA CSV data)
- `z72TurbulenceAnalyze/` — Turbulence intensity analysis for Z72 wind farm
- `z72_SCADA_etech/` — Existing Nuxt 3 + Koa + MongoDB operations platform (yitai-corp-cms)

The `/api/export/` endpoints are designed to feed data into these analysis projects.

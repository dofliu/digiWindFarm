# digiWindTurbine

Wind farm monitoring and digital twin platform with:
- physics-based wind turbine simulation
- 90 SCADA tags aligned to Bachmann Z72 definitions
- fault injection and degradation scenarios
- wind and grid condition control
- Modbus TCP simulation
- FastAPI backend with WebSocket streaming
- React frontend for dashboard, detail, history, and settings

## Quick Start

### Local Development

```bash
# Backend + simulator + Modbus TCP (default port 8100)
pip install -r requirements.txt
python run.py

# Frontend (default port 3100, another terminal)
cd frontend
npm install
npm run dev
```

Open [http://localhost:3100](http://localhost:3100).

### Docker Compose

```bash
docker compose up --build
```

Open [http://localhost:3100](http://localhost:3100). Backend runs on port 8100, Modbus TCP on 5020.

Ports are configured in `.env` (copy from `.env.example`):
- Backend: `BACKEND_PORT=8100`
- Frontend: `VITE_PORT=3100`
- Modbus: `MODBUS_PORT=5020`

Use `python run.py --auto-port` to auto-find an available port if the default is busy.
In `Settings`, select `Physics Simulation (Backend)` to use backend realtime simulation data.

## Current Scope

Implemented and usable today:
- turbine startup, synchronization, production, normal stop, and emergency stop
- separated rotor and generator speeds with first drivetrain torsion model
- 10-point thermal model with residual heat behavior
- vibration, yaw, wind field, wake, and per-turbine individuality
- 7 fault scenarios with fault-to-physics coupling
- grid frequency and voltage events with per-turbine ride-through differences
- sensor noise, drift, stuck values, and quantization
- history page with event markers, event details, focus windows, and CSV export
- electrical response model (frequency-watt, reactive power, power factor, ride-through)
- spectral vibration model (1P/3P/gear/HF/broadband bands, crest factor, kurtosis, BPFO/BPFI bearing defect frequencies, gear mesh sideband analysis)
- fatigue/load model (tower/blade moments, rainflow cycle counting, DEL, Miner's damage, alarm thresholds, RUL estimation, tower SDOF dynamic response, tower shadow 3P blade load modulation)
- fault lifecycle tracking with start/end duration events
- event export API (JSON/CSV) with severity grouping
- Docker Compose deployment (backend + frontend with nginx reverse proxy)

Physics model tracking:
- [`docs/physics_model_status.md`](./docs/physics_model_status.md)

## Architecture

```text
Physics / OPC Data Source
  -> DataBroker
  -> FastAPI REST + WebSocket
  -> SQLite history storage
  -> React dashboard / detail / history / settings
  -> Modbus TCP simulator
```

Main modules:
- `simulator/physics/`
  - `turbine_physics.py`
  - `power_curve.py`
  - `thermal_model.py`
  - `vibration_model.py`
  - `yaw_model.py`
  - `wind_field.py`
  - `fault_engine.py`
  - `electrical_model.py`
  - `vibration_spectral.py`
  - `fatigue_model.py`
  - `scada_registry.py`
- `simulator/grid_model.py`
- `server/`
- `frontend/`

## Key Features

### Physics Simulation
- turbine state mapping `1-9`
- cut-in / startup / sync / production / stop / cut-out behavior
- distinct normal-stop and emergency-stop curves
- curtailment, service mode, and operator commands

### Fault Injection
- `bearing_wear`
- `gearbox_overheat`
- `pitch_motor_fault`
- `converter_cooling_fault`
- `yaw_misalignment`
- `generator_overspeed`
- `transformer_overheat`

### Grid Control
- profiles: `nominal`, `low_freq`, `high_freq`, `undervoltage`, `overvoltage`, `weak_grid`, `recovery`
- manual frequency and voltage override
- per-turbine derate, trip, and reconnect differences

### History
- `GET /api/turbines/{id}/history`
- `GET /api/export/history`
- backend history events stored in SQLite
- history events include operator, fault, grid, wind, and state transitions
- `grid` and `wind` config events support start/end durations
- frontend `History` page supports:
  - turbine, time range, and sample-size controls
  - custom tag selection
  - event filters and event search
  - event detail panel with payload
  - focus windows around selected events
  - CSV export for current range or focused window

## Core APIs

### Health
- `GET /api/health`

### Turbines
- `GET /api/turbines`
- `GET /api/turbines/{id}`
- `GET /api/turbines/{id}/history`
- `GET /api/turbines/{id}/trend`
- `GET /api/turbines/farm-status`
- `GET /api/turbines/farm-trend`

### Config
- `GET /api/config`
- `POST /api/config/datasource`
- `POST /api/config/simulation`
- `GET /api/config/wind`
- `POST /api/config/wind`
- `POST /api/config/wind/clear`
- `GET /api/config/simulation/time-scale`
- `POST /api/config/simulation/time-scale`
- `POST /api/config/simulation/generate-bulk`
- `GET /api/config/grid`
- `POST /api/config/grid`
- `POST /api/config/grid/clear`
- `GET /api/config/storage/stats`
- `GET /api/config/sessions`
- `POST /api/config/storage/maintenance`
- `GET /api/config/turbine-spec`
- `POST /api/config/turbine-spec`
- `GET /api/config/turbine-spec/presets`

### Control
- `POST /api/control/command`
- `POST /api/control/curtail`
- `GET /api/control/{id}/status`

### Faults
- `GET /api/faults/scenarios`
- `POST /api/faults/inject`
- `GET /api/faults/active`
- `POST /api/faults/clear`
- `GET /api/faults/test-plans`
- `POST /api/faults/test-plans/{plan_id}/run`

### Maintenance
- `GET /api/maintenance/work-orders`
- `POST /api/maintenance/work-orders`
- `GET /api/maintenance/work-orders/{id}`
- `PATCH /api/maintenance/work-orders/{id}`
- `GET /api/maintenance/technicians`
- `POST /api/maintenance/technicians`
- `PATCH /api/maintenance/technicians/{id}/status`
- `GET /api/maintenance/events/compare?turbine_ids=WT001,WT002`

### i18n (Tag Translation)
- `GET /api/i18n/tags`
- `GET /api/i18n/tags/all`
- `GET /api/i18n/tags/registry`

### Modbus TCP
- `GET /api/modbus/status`
- `POST /api/modbus/start`
- `POST /api/modbus/stop`
- `GET /api/modbus/registers`

### Export / Realtime
- `GET /api/export/snapshot`
- `GET /api/export/history?format=csv`
- `GET /api/export/events?format=json` (also supports `csv`, with severity grouping)
- `ws://localhost:8100/ws/realtime`

## Frontend Pages

- `Dashboard`
- `Turbine Detail`
- `History`
- `Settings`
- `MaintenanceHub`

Note:
- maintenance work order backend and technician management are implemented
- the frontend MaintenanceHub uses real API backend (SQLite-backed)

## Data Storage

- realtime data: in-memory trend buffer
- historical data: SQLite
- historical events: SQLite `history_events`
- database file: `wind_farm_data.db`

Historical storage currently grows continuously and does not yet have a cleanup policy.

## Documentation

- roadmap: [`TODO.md`](./TODO.md)
- physics model status: [`docs/physics_model_status.md`](./docs/physics_model_status.md)
- original Z72 tag reference: `docs/1040610-Z72_PLC_OPC_TAG_1040510.xlsx`

## Known Gaps

- deployment hardening: JWT, RBAC, HTTPS not yet implemented (Docker Compose is available)
- spectral alarm threshold curves not yet implemented; BPFO/BPFI, gear mesh sideband analysis, and crest factor/kurtosis anomaly alarms completed
- full protection relay coordination not yet implemented
- frontend RUL visualization pending (fatigue alarm thresholds, RUL estimation, and alarm event integration implemented — see #57)
- dependency security vulnerabilities pending upgrade (see #48)
- use the status and roadmap docs as the source of truth for current implementation state

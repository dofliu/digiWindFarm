# digiWindTurbine

Wind farm monitoring and digital twin platform with:
- physics-based wind turbine simulation
- 59 SCADA tags aligned to Bachmann Z72 definitions
- fault injection and degradation scenarios
- wind and grid condition control
- Modbus TCP simulation
- FastAPI backend with WebSocket streaming
- React frontend for dashboard, detail, history, and settings

## Quick Start

```bash
# Backend + simulator + Modbus TCP
pip install -r requirements.txt
python run.py

# Frontend
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).
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
- spectral vibration model (1P/3P/gear/HF/broadband bands, crest factor, kurtosis)
- fault lifecycle tracking with start/end duration events
- event export API (JSON/CSV) with severity grouping

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

### Turbines
- `GET /api/turbines`
- `GET /api/turbines/{id}`
- `GET /api/turbines/{id}/history`
- `GET /api/turbines/{id}/trend`
- `GET /api/turbines/farm-status`

### Config
- `GET /api/config`
- `POST /api/config/wind`
- `POST /api/config/wind/clear`
- `GET /api/config/turbine-spec`
- `POST /api/config/turbine-spec`
- `GET /api/config/grid`
- `POST /api/config/grid`
- `POST /api/config/grid/clear`

### Control
- `POST /api/control/command`
- `POST /api/control/curtail`
- `GET /api/control/{id}/status`

### Faults
- `GET /api/faults/scenarios`
- `POST /api/faults/inject`
- `GET /api/faults/active`
- `POST /api/faults/clear`

### Export / Realtime
- `GET /api/export/snapshot`
- `GET /api/export/history?format=csv`
- `GET /api/export/events?format=json` (also supports `csv`, with severity grouping)
- `ws://localhost:8000/ws/realtime`

## Frontend Pages

- `Dashboard`
- `Turbine Detail`
- `History`
- `Settings`
- `MaintenanceHub`

Note:
- maintenance / work order backend is still not implemented
- the frontend maintenance flow still uses mock-oriented behavior

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

- maintenance / work order backend CRUD not implemented
- history retention / cleanup job not implemented
- event export and advanced multi-turbine comparison are still limited
- advanced aerodynamics, spectral vibration modeling, and deeper electrical control are still pending
- use the status and roadmap docs as the source of truth for current implementation state

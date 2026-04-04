# Wind Farm Monitor Platform

## Quick Start

```bash
# Backend (port 8000) + Modbus TCP (port 5020) — auto-starts both
pip install -r requirements.txt
python run.py

# Frontend (port 3000, another terminal)
cd frontend
npm install
npm run dev
```

Open http://localhost:3000 → Settings → select "Physics Simulation (Backend)" to use real-time simulation data.

---

## Project Overview

Integrated wind farm monitoring platform combining:
1. **Physics-based wind turbine simulator** — 40 SCADA tags aligned to Bachmann Z72 original OPC definitions
2. **Fault injection engine** — 7 gradual degradation scenarios for analyst diagnostics
3. **Wind condition control** — 9 preset profiles + custom override
4. **Modbus TCP simulator** — pymodbus server exposing register map from original Bachmann Excel
5. **OPC DA adapter** — connects to real Bachmann/Vestas wind farm controllers
6. **FastAPI backend** — REST API + WebSocket for real-time data streaming
7. **React frontend** — monitoring dashboard with SCADA panels, trend charts, fault injection, i18n, AI diagnosis

---

## Architecture

```
┌─ Data Source (switchable) ────────────────────────────┐
│  Physics Engine          OPC DA (Real Wind Farm)      │
│  simulator/physics/      opc_adapter.py               │
│  ├─ turbine_physics.py   (Bachmann Z72 / Vestas)      │
│  ├─ power_curve.py       ★ Region 2/3 power curve     │
│  ├─ thermal_model.py     ★ 10-point calibrated temps   │
│  ├─ vibration_model.py   ★ 5-source vibration model    │
│  ├─ yaw_model.py         ★ dead band + delay + unwind  │
│  ├─ wind_field.py        ★ AR(1) turbulence + wake     │
│  ├─ fault_engine.py                                    │
│  └─ scada_registry.py (40 tags, i18n)                  │
│                                                        │
│  Wind Model (wind_model.py)                            │
│  ├─ Auto: daily pattern + Kaimal-like turbulence       │
│  ├─ Profiles: calm/moderate/rated/strong/storm/gusty   │
│  └─ Custom: manual wind speed/direction/temp override  │
└──────────────┬────────────────────────────────────────┘
               │
        ┌──────▼──────┐
        │ DataBroker   │  unified interface
        └──────┬──────┘
               │
┌──────────────▼────────────────────────────────────────┐
│  FastAPI Backend (port 8000)                           │
│  REST: /api/turbines, /config, /faults, /i18n, /modbus│
│  REST: /api/control (stop/start/curtail/service)       │
│  WebSocket: /ws/realtime (2s push)                     │
│  SQLite: wind_farm_data.db (scada_json column)         │
├────────────────────────────────────────────────────────┤
│  Modbus TCP Server (port 5020, auto-start)             │
│  14 slaves × 65 registers (Bachmann HldReg map)        │
└──────────────┬────────────────────────────────────────┘
               │
┌──────────────▼────────────────────────────────────────┐
│  React 19 Frontend (port 3000)                         │
│  3 dashboard modes (cards/summary/table)               │
│  6 SCADA subsystem panels / Trend charts / i18n        │
│  Fault injection / Wind control / Turbine spec         │
│  Operator control (stop/start/curtail/service mode)    │
│  FarmOverview / TurbineDetail / MaintenanceHub         │
└───────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
digiWindFarm/
├── run.py                     # Entry point: starts FastAPI + simulator + Modbus
├── requirements.txt           # Python deps: fastapi, uvicorn, numpy, pydantic, pymodbus
│
├── simulator/                 # Simulation engine
│   ├── engine.py              # WindFarmSimulator (orchestrates physics + faults + Modbus)
│   ├── modbus_server.py       # Modbus TCP server (pymodbus, Bachmann register map)
│   └── physics/               # ★ Independent physics module (no FastAPI dependency)
│       ├── __init__.py        # Exports all sub-models
│       ├── scada_registry.py  # 40 SCADA tag definitions + i18n (en/zh-TW) + OPC/Modbus mapping
│       ├── turbine_physics.py # Main model: composes all sub-models below
│       ├── power_curve.py     # ★ PowerCurveModel + RotorSpeedModel (Region 2/3)
│       ├── thermal_model.py   # ★ ThermalSystem (10 calibrated thermal elements)
│       ├── vibration_model.py # ★ VibrationModel (5-source: 1P, 3P, aero, load, noise)
│       ├── yaw_model.py       # ★ YawModel (dead band, delay, cable unwind)
│       ├── wind_field.py      # ★ TurbulenceGenerator (AR1/Kaimal) + PerTurbineWind (wake)
│       └── fault_engine.py    # 7 fault scenarios with gradual degradation curves
│
├── wind_model.py              # Wind environment (daily pattern + manual override + profiles)
├── turbine_model.py           # Original WindTurbine class (legacy, used as reference)
├── subsystems.py              # Original 7 subsystems (legacy, replaced by physics/)
├── common_types.py            # TurbineParameters dataclass
│
├── server/                    # FastAPI backend
│   ├── app.py                 # FastAPI app, WebSocket, lifespan (auto-starts Modbus)
│   ├── data_broker.py         # DataBroker: unified interface, maps 40 SCADA tags
│   ├── models.py              # Pydantic models (51-field TurbineReading, fault/wind configs)
│   ├── storage.py             # SQLite persistence (scada_json column for full tags)
│   ├── opc_adapter.py         # OPC DA adapter (TAG_MAPS aligned to scada_registry)
│   └── routers/
│       ├── turbines.py        # /api/turbines, /{id}/history, /{id}/trend, /farm-status
│       ├── config.py          # /api/config, /simulation, /datasource, /wind, /turbine-spec
│       ├── control.py         # /api/control/command, /curtail, /{id}/status
│       ├── faults.py          # /api/faults/scenarios, /inject, /active, /clear
│       ├── i18n.py            # /api/i18n/tags, /tags/all, /tags/registry
│       ├── modbus.py          # /api/modbus/start, /stop, /status, /registers
│       └── export.py          # /api/export/snapshot, /history?format=csv (40-col flattened)
│
├── frontend/                  # React 19 + Vite + Tailwind
│   ├── App.tsx                # Main app (nav, language toggle, fault badge, live data)
│   ├── types.ts               # TurbineData (51 fields), FaultInfo, ScadaTagI18n
│   ├── hooks/
│   │   ├── useRealtimeData.ts # WebSocket + REST, maps all 40 SCADA fields
│   │   ├── useI18n.ts         # Language toggle (en/zh-TW), SCADA tag labels
│   │   ├── useMockTurbineData.ts
│   │   ├── useMockMaintenanceData.ts
│   │   └── useSettings.ts    # Smart sync (doesn't restart simulator unnecessarily)
│   ├── components/
│   │   ├── FarmOverview.tsx   # ★ 3 view modes: cards / summary+stats / table (10 cols)
│   │   ├── TurbineDetail.tsx  # 6 SCADA panels + gauges + operator control + AI diagnosis
│   │   ├── TrendChartPanel.tsx # Multi-tag real-time trend chart (6 presets + custom)
│   │   ├── FaultInjectionPanel.tsx # Inject/monitor/clear faults
│   │   ├── SettingsPage.tsx   # Data source + wind control + turbine spec + curtailment
│   │   ├── MaintenanceHub.tsx # Work order management
│   │   ├── DispatchModal.tsx, WorkOrderDetailModal.tsx
│   │   ├── Gauge.tsx, MiniTrendChart.tsx, StatusIndicator.tsx, DataCard.tsx
│   │   └── icons.tsx
│   └── services/
│       └── geminiService.ts   # Gemini AI fault diagnosis
│
├── docs/
│   └── 1040610-Z72_PLC_OPC_TAG_1040510.xlsx  # Original Bachmann Z72 tag definitions
│
└── wind_farm_data.db          # Auto-created SQLite (gitignore)
```

---

## Physics Sub-Model Architecture

Each sub-model is an **independent class** that can be replaced separately:

```python
# Example: replace vibration model with a custom one
model = TurbinePhysicsModel()
model.vibration = MyAdvancedVibrationModel()
model.thermal = CFDBasedThermalSystem()
```

### PowerCurveModel (`power_curve.py`)
- Lookup-table based, default 5MW curve with 30+ points
- Region 2 (partial load): power ∝ V³, tracks optimal TSR
- Region 3 (rated): constant power, pitch regulates
- Supports custom power curves via `power_curve` parameter

### RotorSpeedModel (`power_curve.py`)
- Region 2: RPM proportional to wind speed (optimal TSR tracking)
- Region 3: constant rated RPM (13.6 RPM for 5MW)
- First-order inertia (τ = 8 seconds, realistic for 126m rotor)
- Startup/braking dynamics

### ThermalSystem (`thermal_model.py`)
10 calibrated thermal elements with realistic steady-state temperatures:

| Component | R_th | τ (sec) | Steady-state at rated | Real range |
|-----------|------|---------|----------------------|------------|
| Gen Stator | 0.24 | 600 | ~60°C | 70-110°C |
| Gen Air Gap | 0.32 | 450 | ~49°C | 60-85°C |
| Gen Bearing | 0.70 | 900 | ~53°C | 50-75°C |
| Cnv Cabinet | 0.20 | 500 | ~45°C | 35-50°C |
| IGCT Water | 0.17 | 300 | ~37°C | 30-42°C |
| Transformer | 0.70 | 1200 | ~59°C | 50-80°C |
| Nacelle | 0.08 | 1800 | ~37°C | 30-45°C |

### VibrationModel (`vibration_model.py`)
5-source model: rotational (1P), blade-pass (3P), aerodynamic (turbulence),
drivetrain load, broadband noise. Low-pass filtered for realistic time behavior.
- Normal: 0.5-2.0 mm/s, Warning: >4.0, Alarm: >7.0

### YawModel (`yaw_model.py`)
- Dead band: ±8° (no action within)
- Activation delay: 60 seconds sustained error before yaw starts
- Post-action hold: 30 seconds after alignment
- Cable unwind: auto-unwind at ±2.5 turns
- Brake pressure: 140-180 bar (stationary), 80-120 during yaw

### Wind Field (`wind_field.py`)
- TurbulenceGenerator: AR(1) process, Kaimal-like spectrum (τ = L/V, L=340m)
- PerTurbineWind: spatial decorrelation + wake effect (2-6% deficit)

### Power Curve Validation (5MW Z72, steady state)
```
Wind    Power     RPM   Pitch  GenTemp  BrgTemp
  3       0kW    0.00   90.0°   31°C    29°C
  5     284kW    5.68    0.1°   30°C    30°C
  7    1068kW    7.96    0.0°   31°C    32°C
  9    2548kW   10.23    0.0°   36°C    35°C
 12    4851kW   13.64    0.2°   52°C    47°C   ← rated
 16    4900kW   13.64    9.6°   58°C    51°C   ← Region 3
 20    4900kW   13.64   22.5°   60°C    54°C
 25    4900kW   13.64   30.0°   60°C    55°C
 26       0kW    0.00   90.2°    --      --    ← cut-out
```

---

## API Reference

### Turbine Data
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Server status, mode, turbine count |
| GET | `/api/turbines` | All turbines (51-field TurbineReading[]) |
| GET | `/api/turbines/{id}` | Single turbine with full SCADA tags |
| GET | `/api/turbines/{id}/history` | Historical data (from SQLite) |
| GET | `/api/turbines/{id}/trend?tags=TAG1,TAG2&limit=120` | In-memory trend data for specific tags |
| GET | `/api/turbines/farm-status` | Farm KPIs |

### Wind Condition Control
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/config/wind` | Current wind model status |
| POST | `/api/config/wind` | Set wind profile or custom values |
| POST | `/api/config/wind/clear` | Return to auto daily pattern |

Wind profiles: `calm` (2m/s), `moderate` (8m/s), `rated` (12m/s), `strong` (18m/s), `storm` (26m/s), `gusty`, `ramp_up`, `ramp_down`, `auto`

### Turbine Specification
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/config/turbine-spec` | Current turbine spec |
| POST | `/api/config/turbine-spec` | Update spec or use preset: `{"preset":"vestas_v90_3mw"}` |
| GET | `/api/config/turbine-spec/presets` | List available presets |

Presets: `z72_5mw` (5MW), `vestas_v90_3mw` (3MW), `sg_8mw` (8MW), `goldwind_2.5mw` (2.5MW)

### Operator Control
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/control/command` | `{"turbineId":"WT001","command":"stop\|start\|reset\|service_on\|service_off"}` |
| POST | `/api/control/curtail` | `{"turbineId":"WT003","powerLimitKw":3000}` (null = remove) |
| GET | `/api/control/{id}/status` | Current operator control status |

### Fault Injection
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/faults/scenarios` | List 7 fault scenarios |
| POST | `/api/faults/inject` | `{"scenarioId":"bearing_wear","turbineId":"WT003","severityRate":0.005}` |
| GET | `/api/faults/active` | Active faults with severity, phase, alarms |
| POST | `/api/faults/clear` | Clear faults (all or by turbine/scenario) |

### i18n
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/i18n/tags?lang=zh` | Tag labels in specified language |
| GET | `/api/i18n/tags/all` | Full bilingual dict |
| GET | `/api/i18n/tags/registry` | Complete tag definitions (OPC, Modbus, units, ranges) |

### Modbus TCP Simulator
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/modbus/status` | Server running status |
| POST | `/api/modbus/start` | Start on specified port (default 5020) |
| POST | `/api/modbus/stop` | Stop server |
| GET | `/api/modbus/registers` | Full register map documentation |

### Configuration
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/config` | Current mode and turbine count |
| POST | `/api/config/datasource` | Switch mode: simulation / opc_da |
| POST | `/api/config/simulation` | Set simulation params |

### Data Export
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/export/snapshot` | Current state as JSON |
| GET | `/api/export/history?turbine_id=WT001&format=csv` | History as CSV (40 cols flattened) |

### WebSocket
| Endpoint | Description |
|----------|-------------|
| `ws://localhost:8000/ws/realtime` | Pushes TurbineReading[] every 2 seconds |

---

## SCADA Tags (40 points, aligned to Bachmann Z72)

Based on `docs/1040610-Z72_PLC_OPC_TAG_1040510.xlsx` sheet "簡化-每部風力機頁面顯示".

| Subsystem | Tags | Key Points |
|-----------|------|-----------|
| **WTUR** (Turbine) | TurSt, TotPwrAt | State machine 1-9, active power |
| **WGEN** (Generator) | GnPwrMs, GnSpd, GnVtgMs, GnCurMs, GnStaTmp1, GnAirTmp1, GnBrgTmp1 | Multi-point thermal model |
| **WROT** (Rotor/Pitch) | RotSpd, PtAngValBl1/2/3, RotTmp, RotCabTmp, RotLckd, SrvcBrkAct, LckngPnPos | 3 independent blade angles |
| **WCNV** (Converter) | CnvCabinTmp, CnvDClVtg, CnvGdPwrAt, CnvGnFrq, CnvGnPwr, IGCTWtrCond/Pres1/Pres2/Tmp | IGCT water cooling |
| **WGDC** (Grid) | TrfCoreTmp | Transformer thermal |
| **WMET** (Met) | WSpeedNac, WDirAbs, TmpOutside | Environment |
| **WNAC** (Nacelle) | NacTmp, NacCabTmp, VibMsNacXDir, VibMsNacYDir | XY vibration |
| **WYAW** (Yaw) | YwVn1AlgnAvg5s, YwBrkHyPrs, CabWup | Alignment, hydraulic, cable |

Full definitions: `simulator/physics/scada_registry.py`

---

## Fault Scenarios

7 gradual degradation patterns with 4 severity curves (linear, quadratic, exponential, logarithmic):

| Scenario | Affected Tags | Alarm Codes |
|----------|--------------|-------------|
| `bearing_wear` | GnBrgTmp1, VibX/Y, GnStaTmp1, GnAirTmp1 | A→T2→T1 trip |
| `gearbox_overheat` | NacTmp, VibX/Y, CnvCabinTmp | A→T2→T1 |
| `pitch_motor_fault` | PtAngValBl1, VibX/Y, TotPwrAt↓ | A→T1 |
| `converter_cooling_fault` | IGCTWtrTmp, IGCTWtrPres↓, CnvCabinTmp, Power↓ | A→T1 |
| `yaw_misalignment` | YwVn1Algn, Power↓, YwBrkHyPrs↓ | A→T2 |
| `generator_overspeed` | RotSpd, GnSpd, VibX/Y | T1 (fast trip) |
| `transformer_overheat` | TrfCoreTmp, NacTmp | A→T2 |

---

## Modbus TCP Register Map

Auto-starts on port 5020. Each turbine = one slave/device ID (WT001→1, WT002→2, ...).

Key Holding Registers:
| HR Address | Scale | Description |
|-----------|-------|-------------|
| 224 | ×1 | Turbine state (1-9) |
| 228 | ×100 | Rotor speed RPM |
| 230-232 | ×10 | Blade angles 1/2/3 |
| 248 | ×10 | Wind speed m/s |
| 267 | ×1 | Active power kW |
| 274 | ×100 | Generator frequency Hz |
| 501-517 | ×10 | Temperature points °C |
| 244-245 | ×100 | Vibration X/Y mm/s |

Full map: `GET /api/modbus/registers` or `simulator/modbus_server.py`

---

## Known Issues / TODO

1. ~~Fault injection not implemented~~ ✅ Done (7 scenarios)
2. **WorkOrderDetailModal.tsx** has a pre-existing TypeScript error (Blob type mismatch) — doesn't affect build
3. **OPC DA adapter** — tag mapping aligned but not tested against real OPC servers
4. **No authentication** — add JWT if deploying beyond local dev
5. **Gemini AI service** needs `GEMINI_API_KEY` in `frontend/.env.local`
6. **History data grows unbounded** — consider adding a cleanup job
7. **Maintenance work orders** — frontend uses mock data, backend CRUD API not yet implemented

See `TODO.md` for full development roadmap and future plans.

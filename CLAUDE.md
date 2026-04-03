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
│  ├─ fault_engine.py                                    │
│  └─ scada_registry.py (40 tags, i18n)                  │
│                                                        │
│  Wind Model (wind_model.py)                            │
│  ├─ Auto: daily pattern + turbulence                   │
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
│  WebSocket: /ws/realtime (2s push)                     │
│  SQLite: wind_farm_data.db (scada_json column)         │
├────────────────────────────────────────────────────────┤
│  Modbus TCP Server (port 5020, auto-start)             │
│  14 slaves × 65 registers (Bachmann HldReg map)        │
└──────────────┬────────────────────────────────────────┘
               │
┌──────────────▼────────────────────────────────────────┐
│  React 19 Frontend (port 3000)                         │
│  6 SCADA subsystem panels / Trend charts / i18n        │
│  Fault injection console / Wind condition control      │
│  FarmOverview / TurbineDetail / MaintenanceHub         │
└───────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
digiWindTurbine/
├── run.py                     # Entry point: starts FastAPI + simulator + Modbus
├── requirements.txt           # Python deps: fastapi, uvicorn, numpy, pydantic, pymodbus
│
├── simulator/                 # Simulation engine
│   ├── engine.py              # WindFarmSimulator (orchestrates physics + faults + Modbus)
│   ├── modbus_server.py       # Modbus TCP server (pymodbus, Bachmann register map)
│   └── physics/               # ★ Independent physics module (no FastAPI dependency)
│       ├── __init__.py
│       ├── scada_registry.py  # 40 SCADA tag definitions + i18n (en/zh-TW) + OPC/Modbus mapping
│       ├── turbine_physics.py # Full turbine physics model (coupling chain, thermal models)
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
│       ├── config.py          # /api/config, /simulation, /datasource, /wind
│       ├── faults.py          # /api/faults/scenarios, /inject, /active, /clear
│       ├── i18n.py            # /api/i18n/tags, /tags/all, /tags/registry
│       ├── modbus.py          # /api/modbus/start, /stop, /status, /registers
│       └── export.py          # /api/export/snapshot, /history?format=csv
│
├── frontend/                  # React 19 + Vite + Tailwind
│   ├── App.tsx                # Main app (nav, language toggle, fault badge)
│   ├── types.ts               # TurbineData (51 fields), FaultInfo, ScadaTagI18n
│   ├── hooks/
│   │   ├── useRealtimeData.ts # WebSocket + REST, maps all 40 SCADA fields
│   │   ├── useI18n.ts         # Language toggle (en/zh-TW), SCADA tag labels
│   │   ├── useMockTurbineData.ts
│   │   ├── useMockMaintenanceData.ts
│   │   └── useSettings.ts
│   ├── components/
│   │   ├── FarmOverview.tsx   # Turbine cards with TurState, fault badges
│   │   ├── TurbineDetail.tsx  # 6 SCADA subsystem panels + gauges + AI diagnosis
│   │   ├── TrendChartPanel.tsx # ★ Multi-tag real-time trend chart (6 presets + custom)
│   │   ├── FaultInjectionPanel.tsx # ★ Inject/monitor/clear faults
│   │   ├── SettingsPage.tsx   # Data source + wind control (profiles + custom)
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
| GET | `/api/export/history?turbine_id=WT001&format=csv` | History as CSV |

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

## Physics Model Coupling Chain

```
Wind Speed → Rotor RPM → Generator RPM/Freq → Power/Current/Voltage
             ↓                  ↓
          Blade Angles      Converter Power
             ↓                  ↓
        Pitch Motor Cur     IGCT Temperature
                                ↓
                           Transformer Temp

Wind Speed → Nacelle Vibration (X,Y)
Wind Dir → Yaw Error → Yaw Action → Hydraulic Pressure / Cable Windup
Ambient Temp → Nacelle Temp → Cabinet Temps
Power × Time → Thermal rise (generator stator, bearings, air gap)
```

Independent module at `simulator/physics/` — no dependency on FastAPI/frontend/storage.

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

# digiWindTurbine

Wind farm monitoring and digital twin platform with:
- physics-based wind turbine simulation
- 103 SCADA tags aligned to Bachmann Z72 definitions
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
- separated rotor and generator speeds with first drivetrain torsion model, gearbox oil temperature/viscosity effects, and gear tooth contact-ratio mesh stiffness ripple + tooth wear index
- 10-point thermal model with residual heat behavior
- vibration, yaw, wind field, wake, and per-turbine individuality
- 7 fault scenarios with fault-to-physics coupling
- grid frequency and voltage events with per-turbine ride-through differences
- sensor noise, drift, stuck values, and quantization
- history page with event markers, event details, focus windows, and CSV export
- electrical response model (frequency-watt, reactive power, power factor, ride-through)
- spectral vibration model (1P/3P/gear/HF/broadband bands, crest factor, kurtosis, BPFO/BPFI bearing defect frequencies, gear mesh sideband analysis)
- fatigue/load model (tower/blade moments, rainflow cycle counting, DEL, Miner's damage, alarm thresholds, RUL estimation, tower SDOF dynamic response, tower shadow 3P blade load modulation, wind shear 1P azimuth-dependent blade loading, blade mass imbalance ω² force coupling)
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
- coolant level / leak detection implemented (level tracking, pump cavitation, fault coupling) — see #75
- ambient humidity effect on air cooling implemented (moist-air density + dew-point condensation penalty) — see #89
- localized turbulence pockets implemented (Gaussian spatial TI boost pockets, per-turbine TI multiplier, `WMET_LocalTi` tag) — see #91
- wake model upgraded to Bastankhah-Porté-Agel Gaussian (TI-dependent expansion, Ct-coupled deficit, sum-of-squares superposition, `WMET_WakeDef` tag) — see #93
- dynamic wake meandering implemented (Larsen-DWM lateral AR(1) oscillation of wake centerline, σ_θ=0.3·TI, τ≈25 s, new `WMET_WakeMndr` SCADA tag) — see #95
- yaw-induced wake deflection implemented (Bastankhah 2016 θ_c initial skew, per-source δ_y(x)=tan(θ_c)·x coupled to yaw_error, new `WMET_WakeDefl` SCADA tag; driven by yaw_misalignment fault and transient yaw lag) — see #97
- atmospheric stability / diurnal shear-TI coupling implemented (Monin-Obukhov-simplified continuous stability score s ∈ [−1, +1] from solar time × wind mechanical mixing × cloud damping; drives wind shear exponent α ∈ [0.04, 0.30] and turbulence intensity multiplier ∈ [0.5, 1.6]; new `WMET_ShearAlpha` + `WMET_AtmStab` SCADA tags) — see #99
- air density coupling implemented (moist-air ρ from ideal gas law + Buck/Magnus vapor correction; updated every step from ambient temp + humidity and injected into `PowerCurveModel.air_density` so aerodynamic power P ∝ ρ·V³ and thrust F ∝ ρ·V² both respond; ±10% swing between cold-winter and hot-humid days; new `WMET_AirDensity` SCADA tag) — see #101
- wake-added turbulence intensity implemented (Crespo-Hernández 1996: TI_w(x, r=0) = 0.73·a^0.8325·TI_∞^0.0325·(x/D)^-0.32 with a = 0.5·(1−√(1−Ct)), near-field capped at x/D=5; shared Bastankhah Gaussian σ for radial decay; Frandsen sum-of-squares across upstream sources; combined with pocket TI in quadrature before AR(1) generator so downstream σ_v observably rises — T1 at ~7D sees 12% wake-added TI and +36% wind-speed std vs free-stream T0 in self-test; new `WMET_WakeTi` SCADA tag) — see #103
- dynamic atmospheric pressure P(t) implemented (synoptic `_pressure_state` continuous score in [−1, +1] mapped to ±1500 Pa around ISA 101325 Pa, covering typical mid-latitude frontal amplitude 1013±15 hPa; fed through `WindEnvironmentModel.get_air_density(ts, ..., pressure_pa=...)` so ρ gains another ±1.5% time variability from weather fronts on top of #101's T/RH coupling; manual override locks P at ISA reference; new `WMET_AmbPressure` SCADA tag, hPa) — see #106
- atmospheric-stability × wake-expansion coupling implemented (Bastankhah `k* = k_neutral · clamp(1 + 0.30·s, 0.55, 1.45)` following Abkar & Porté-Agel 2015 / Peña et al. 2016; stable ABL slows wake recovery, convective ABL speeds it up; at 6 D / V=10 m/s / TI=8 % the self-test shows +33.8 % wake deficit at s=−1 and −22.0 % at s=+1; no new SCADA tag — observable via `WMET_WakeDef × WMET_AtmStab` correlation) — see #109
- atmospheric-stability × wind-veer coupling implemented (per-turbine `wind_veer_rate` (#79) is multiplied by `clamp(1 − s, 0.3, 2.5)`, following Holton §5.3 / Stull §8.5 / van der Laan et al. 2017; stable nocturnal ABL preserves the Ekman spiral → ~0.20 °/m and +37 % tower side-side moment vs neutral, convective afternoon mixes it out → ~0.03 °/m and −26 %; effective veer rate is shared between the aero power-loss block and `fatigue_model.step()` so structural loads and aero power stay consistent; no new SCADA tag — observable via `WMET_AtmStab × WLOD_TwrSsMom` correlation) — see #111
- atmospheric-stability × wake-meander τ_m coupling implemented (the Larsen-DWM atmospheric integral timescale is now `τ_m = 25 · clamp(1 − 0.6·s, 0.4, 2.0)` s following Counihan 1975 / Larsen DWM 2008 / Peña & Hahmann 2012; stable ABL → 40 s slow meander, neutral → 25 s baseline, convective → 10 s fast turnover; lateral amplitude σ_θ stays at 0.3·TI so the amplitude path is owned by #99 TI-mult while τ_m owns the timescale path; self-test on a 4000 s AR(1) series shows lag-25 s autocorrelation 0.45 (stable) vs 0.28 (neutral) vs 0.01 (convective) and zero-crossing rate 0.082 vs 0.140 — slower meander under stable conditions and faster turnover under convection; no new SCADA tag — observable via `WMET_WakeMndr × WMET_AtmStab` autocorrelation) — see #113
- atmospheric-stability × turbulence integral length scale L_u coupling implemented (`TurbulenceGenerator.step()` applies `L_u_eff = 340 · clamp(1 − 0.6·s, 0.4, 2.0)` m on top of the IEC 61400-1 neutral baseline so the AR(1) wind-speed autocorrelation timescale `τ = L_u/V` is stability-modulated. Stable nocturnal ABL → L_u=544 m, τ ≈ 54 s @ 10 m/s; neutral → 340 m, 34 s; convective afternoon → 136 m, 14 s. Validated on a 4000 s series at TI=0.10: observed lag-30 s autocorrelation 0.574 / 0.401 / 0.097 vs analytical 0.576 / 0.414 / 0.110 (stable / neutral / convective); steady-state σ_v stays at TI·V ≈ 1.0 m/s in all cases — the amplitude path is owned by #99's TI multiplier, this PR adds only the orthogonal timescale path. The same s ∈ [−1, +1] feeds both the farm-wide `_turbulence_gen` and every per-turbine `_turb_gens[i].step(...)` so the whole farm shares one ABL timescale. No new SCADA tag — observable via `WMET_AtmStab × WROT_RotSpd` low-frequency autocorrelation. References: Counihan 1975 / Kaimal & Finnigan 1994 / Peña & Hahmann 2012 / IEC 61400-1 ed.4 Annex C — see #115)
- nacelle anemometer transfer function (NTF) implemented (IEC 61400-12-1 Annex D: real cup/sonic anemometer sits ~1.5R behind hub on top of nacelle, reads systematically below free-stream because of axial induction. NTF formula `V_raw = V_∞ · (1 − 0.55·a)` with `a = 0.5·(1 − √(1 − Ct))` derived from the 1-D momentum theory and the existing `aero_out.ct`. Stopped/parked rotor: bluff-body speed-up `1.04·V_∞` instead of induction. Self-test (7/7 + monotonicity): Region 2 Ct≈0.82 → 0.84·V_∞; Region 2.5 → 0.89·V_∞; Region 3 Ct≈0.30 → 0.96·V_∞; cut-out → 1.04·V_∞. Backwards compatible — `WMET_WSpeedNac` keeps free-stream semantics so `examples/data_quality_analysis.py` and OPC adapter consumers still get the same number; new `WMET_WSpeedRaw` SCADA tag exposes the as-measured anemometer reading for power-curve verification studies. 103 SCADA tags total — see #117)
- nacelle wind vane transfer function (WVTF) implemented (IEC 61400-12-2 Annex E / Burton et al. 2011 *Wind Energy Handbook* §3.7 / Pedersen et al. 2008 Risø-R-1602 / Kragh & Hansen 2014: real wind vane on top of nacelle reads a systematic swirl bias from rotor wake rotation. Swirl angle `θ_s ≈ Ct / (2·λ)` rad derived from BEM tangential induction `a' = Ct / (4·λ)`. Right-handed rotor convention → +bias on the nacelle vane. Operating-state branching: producing or starting with `rotor_speed > 1 RPM` and `λ > 1` applies the swirl bias; otherwise (rotor stopped/parked or pre-spin) bias = 0. Final clamp to ±8° (Pedersen 2008 measured 3–8° in field). Self-test (10/10 + Ct↑→bias↑ and λ↑→bias↓ monotonicity + clamp + 360°-wrap): stopped → 0°; Region 2 peak Cp (Ct=0.82, λ=7) → +3.36°; Region 2.5 (Ct=0.65, λ=6) → +3.10°; Region 3 pitched-down (Ct=0.30, λ=5) → +1.72°; extreme Ct=0.95, λ=1.5 → +8.00° clamp. Reuses `aero_out.ct` + `aero_out.tsr` already computed in `step()` — no extra cost, no new RNG. Backwards compatible — `WMET_WDirAbs` is intentionally kept as the free-stream direction so the frontend wind-rose, wake-source indexing, and `yaw_model` control-error logic are all unchanged; new `WMET_WDirRaw` SCADA tag exposes the as-measured vane reading for vane-miscalibration / systematic yaw-misalignment failure scenarios. With #117 NTF this completes the IEC 61400-12-1/2 nacelle sensor transfer-function pair: NTF describes "what speed the sensor sees", WVTF describes "what direction the sensor sees". 104 SCADA tags total — see #119)
- full protection relay coordination not yet implemented
- frontend RUL visualization pending (fatigue alarm thresholds, RUL estimation, and alarm event integration implemented — see #57)
- dependency security vulnerabilities pending upgrade (see #48)
- use the status and roadmap docs as the source of truth for current implementation state

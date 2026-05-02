# digiWindTurbine

Wind farm monitoring and digital twin platform with:
- physics-based wind turbine simulation
- 104 SCADA tags aligned to Bachmann Z72 definitions
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
- nacelle wind vane transfer function (WVTF) implemented (IEC 61400-12-2 Annex E: real wind vane co-located with the nacelle anemometer reads systematic swirl bias from rotor wake, since the rotor converts linear inflow into linear+rotational outflow (angular-momentum conservation). Closed form `θ_s ≈ Ct/(2·λ) [rad]` (Burton, Sharpe, Jenkins & Bossanyi 2011 *Wind Energy Handbook* 2nd ed. §3.7) reuses `aero_out.ct` and `aero_out.tsr` already computed by `power_curve.get_power_cp`, so there is zero extra cost and no new RNG mutation. Right-handed rotor (industry standard, clockwise from upwind) → +bias on the downstream vane. Operating-state branching: producing/starting with `rotor_speed > 1 RPM` and `tsr > 1` applies the swirl bias; otherwise (stopped/parked, no rotor swirl) bias = 0°. Final clamp `±8°` keeps the result inside physically observed bounds. Self-test (8/8 + Ct↑→bias↑ + λ↑→bias↓ monotonicity): Region 2 (Ct≈0.82, λ≈7) → +3.36°; Region 2.5 (Ct≈0.65, λ≈6) → +3.10°; Region 3 (Ct≈0.30, λ≈5) → +1.72°; starting (Ct≈0.55, λ≈6) → +2.63°; stopped/cut-out → 0°; extreme Ct=0.95/λ=2 clamps at +8°; 360° wrap-around verified (358° + 3.4° → 1.36°). Backwards compatible — `WMET_WDirAbs` intentionally keeps free-stream semantics so the wake-model upstream indexing, yaw controller (`yaw_model.py`), frontend wind rose, and OPC adapter consumers are all unchanged; new `WMET_WDirRaw` (REAL32, °, 0–360) exposes the as-measured vane reading for IEC 61400-12-2 nacelle power-curve studies, vane-miscalibration fault simulation, and the `WMET_WDirRaw - yaw_angle` observation channel that mirrors how field engineers diagnose systematic yaw misalignment. Pairs with #117 NTF to form a complete IEC 61400-12-1/2 nacelle sensor transfer function chain. 104 SCADA tags total (was 103): +1 raw nacelle wind vane tag (`WMET_WDirRaw`) — see #119
- Glauert yaw skewed-flow correction on NTF + WVTF (#125, Glauert 1935 / Burton et al. 2011 §3.7+§3.10): the IEC 61400-12-1/2 nacelle-sensor chain (#117 + #119) now stays valid when the rotor is yawed (`yaw_misalignment` faults, ±5° dead-band, gust transients). NTF gains `a_skew = a · cos²(γ)` (Glauert/Coleman skewed-momentum) → `V_raw = V_∞ · (1 − 0.55·a·cos²(γ))`; WVTF gains `θ_s_eff = (Ct/(2·λ)) · cos(γ)` (planar projection of the swirl vector onto the nacelle plane). Reuses `yaw_out["yaw_error"]` already computed in `step()` and a single `cos(γ)` for both blocks — zero extra cost, no new state, no new SCADA tag, no new RNG. γ clamped ±45° (validity bound of skewed-momentum). Self-test (18/18 PASS) — γ=0° preserves the existing #117/#119 baseline exactly; γ=15° → NTF reduction × 0.933, WVTF bias × 0.966; γ=30° → 0.75 / 0.866; γ=45° → 0.50 / 0.707; symmetry γ→−γ exact (cos is even); monotonicity |γ|↑ → factor↑ / bias↓ verified. Side effect: clears two duplicate `WMET_WDirRaw` keys leftover from the #119 merge (`turbine_physics.py:777`, `scada_registry.py:151`); `ruff F601` clean across `simulator/`, `server/`, `wind_model.py`. Observable via `(WMET_WSpeedRaw / WMET_WSpeedNac)` ratio against `WYAW_YwVn1AlgnAvg5s` and `(WMET_WDirRaw − WMET_WDirAbs)` channel — see #125
- cup-anemometer overspeeding bias (#127, IEC 61400-12-1 ed.2 §6.3.4 + Annex H / Kristensen 1998 Risø-R-1024 / Pedersen 2006 Risø-R-1473): real cup-type anemometers respond faster to gusts than to lulls (asymmetric drag torque, D ∝ V²), producing a long-term mean reading biased high by `k_overspeed · TI²`. k=1.5 for heated Risø Class 1 cup (industry typical); sonic anemometers k≈0. Applied multiplicatively after the #117/#125 NTF block: `nac_anem_raw *= 1 + 1.5·TI_local²` with `TI_local = sqrt((effective_ti·_local_ti_multiplier)² + _wake_added_ti²)` — quadrature combine of #99 ABL TI × #91 pocket multiplier and #103 wake-added TI as independent stochastic sources. Clamp ≤+10% (physical upper bound). Operating-state branching: stopped/parked → bias = 1.0 (cup not turning, no overspeeding); producing/starting with `rotor_speed > 1 RPM` applies the bias. Self-test (19/19 PASS): TI=0 → 1.000 (#117 baseline preserved); TI=0.06 → +0.5%; TI=0.10 → +1.5%; TI=0.15 → +3.4%; TI=0.20 → +6.0%; TI=0.30 → clamped at +10%; pocket multiplier 1.5×TI=0.10 → +3.4%; composite eff=0.10/mult=1.3/wake=0.07 → +3.27%; monotonicity TI↑ → bias↑ verified; rotor_speed=0 → bias=1.0 verified. Reuses existing `effective_ti` from `engine.py:112` and `_local_ti_multiplier` / `_wake_added_ti` already in `step()` state — no extra cost, no new state, no new RNG, **no new SCADA tag**. First time three TI paths (`#99 ABL`, `#91 pocket`, `#103 wake-added`) couple back into the sensor reading. Closes IEC 61400-12-1 mean (Annex D, #117) + Glauert yaw (#125) + statistical bias (Annex H, #127) chain for cup-style nacelle anemometers. 104 SCADA tags total (unchanged) — observable via `WMET_WSpeedRaw / WMET_WSpeedNac × WMET_LocalTi × WMET_WakeTi` correlation — see #127
- full protection relay coordination not yet implemented
- frontend RUL visualization pending (fatigue alarm thresholds, RUL estimation, and alarm event integration implemented — see #57)
- dependency security vulnerabilities pending upgrade (see #48)
- use the status and roadmap docs as the source of truth for current implementation state

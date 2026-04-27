# TODO / Development Roadmap

## Tracking Docs

- Physics model status:
  - `docs/physics_model_status.md`

## Completed

### Simulation / Physics
- [x] 40 SCADA tags aligned with Bachmann Z72 definitions
- [x] Turbine main state machine with staged startup / sync / production / stop
- [x] Normal stop and emergency stop behavior
- [x] Power curve and rotor speed model
- [x] Drivetrain slip / shaft twist / brake torque first version
- [x] 10-point thermal model with heat inertia
- [x] Vibration model
- [x] Yaw model
- [x] Turbulence + per-turbine wind variation + simple wake
- [x] Fault injection with 7 scenarios
- [x] Fault-to-physics coupling
- [x] Per-turbine individuality model
- [x] Sensor noise / drift / stuck / quantization
- [x] Grid frequency / voltage model
- [x] Per-turbine grid derate / trip / reconnect difference
- [x] Cp(λ,β) aerodynamic surface model with thrust coefficient and dynamic stall
- [x] Multi-stage drivetrain: gearbox stages, bearing separation, torsional modes, brake dynamics
- [x] Cooling system: pump/fan state, coolant flow/pressure, fouling propagation
- [x] Wind event propagation: gust front, ramp, direction shift across farm
- [x] Farm layout with turbine positions and direction-aware wake model
- [x] Fault physics path unified — all 11 scenarios through physical causes with load coupling
- [x] Electrical response model: frequency-watt droop, reactive power, power factor, LVRT/HVRT ride-through, synthetic inertia, converter modes
- [x] Spectral vibration model: 1P/3P/gear-mesh/HF/broadband bands with fault-specific signatures, crest factor, kurtosis
- [x] 59 SCADA tags total (was 40): +7 electrical response + 12 vibration spectral bands
- [x] Vibration spectral alarm thresholds with ISO 10816-inspired zones and hysteresis
- [x] Fatigue/load model: tower/blade bending moments, rainflow cycle counting, DEL, Miner's damage
- [x] 80 SCADA tags total (was 59): +8 vibration alarm + 13 structural load/fatigue + 3 fatigue alarm/RUL
- [x] Bearing defect frequency model (BPFO/BPFI) with geometry-based computation
- [x] 84 SCADA tags total (was 80): +4 bearing defect frequency/amplitude
- [x] Gear mesh sideband analysis (GMF ± n×shaft frequency, sideband energy ratio)
- [x] 88 SCADA tags total (was 84): +4 gear mesh sideband tags
- [x] Crest factor / kurtosis anomaly alarms with hysteresis logic
- [x] 90 SCADA tags total (was 88): +2 crest factor/kurtosis alarm tags
- [x] Gearbox oil temperature and viscosity effects (Walther-type model, cold-start decay) — see #73
- [x] 91 SCADA tags total (was 90): +1 gearbox oil temperature tag
- [x] Gear tooth contact modeling (time-varying mesh stiffness, contact ratio, tooth wear index, GMF excitation → HSS torsion) — see #76
- [x] 92 SCADA tags total (was 91): +1 gear tooth wear tag (`WDRV_GbxToothWear`)
- [x] Ambient humidity effect on air cooling (moist-air density + dew-point condensation penalty on nacelle/cabinet fans) — see #89
- [x] 93 SCADA tags total (was 92): +1 outside relative humidity tag (`WMET_HumOutside`)
- [x] Localized turbulence pockets (Gaussian spatial TI boost per pocket, AR(1) turbulence × per-turbine TI multiplier) — see #91
- [x] 94 SCADA tags total (was 93): +1 local TI multiplier tag (`WMET_LocalTi`)
- [x] Bastankhah-Porté-Agel Gaussian wake model (TI-dependent expansion k* = 0.38·TI+0.004, Ct-coupled max deficit, Gaussian radial profile, sum-of-squares multi-wake superposition) — see #93
- [x] 95 SCADA tags total (was 94): +1 wake velocity deficit tag (`WMET_WakeDef`)
- [x] Dynamic wake meandering (Larsen-DWM lateral AR(1) oscillation of wake centerline, σ_θ=0.3·TI, τ=25 s, applied per-source to Bastankhah Gaussian r_lat) — see #95
- [x] 96 SCADA tags total (was 95): +1 wake meander lateral offset tag (`WMET_WakeMndr`)
- [x] Yaw-induced wake deflection (Bastankhah 2016 θ_c=0.3·γ·(1−√(1−Ct·cos γ))/cos γ initial skew, δ_y(x)=tan(θ_c)·x applied per-source inside Bastankhah Gaussian r_lat, engine feeds per-turbine yaw_error back each step, ±45° clamp) — see #97
- [x] 97 SCADA tags total (was 96): +1 yaw-induced wake deflection tag (`WMET_WakeDefl`)
- [x] Atmospheric stability / diurnal shear-TI coupling (continuous score s=solar·wind_damping·cloud_damping, α=0.14−0.10·s clamped [0.04, 0.30], TI_mult=1+0.5·s clamped [0.5, 1.6], strong-wind mechanical mixing, override-neutral, per-turbine α offset renamed) — see #99
- [x] 99 SCADA tags total (was 97): +2 atmospheric stability tags (`WMET_ShearAlpha`, `WMET_AtmStab`)
- [x] Air density coupling (ideal gas + Magnus moist-air correction; ρ fed per-step into PowerCurveModel; aero power P ∝ ρ·V³ and thrust F ∝ ρ·V² respond to ambient T / RH) — see #101
- [x] 100 SCADA tags total (was 99): +1 air density tag (`WMET_AirDensity`)
- [x] Wake-added turbulence intensity (Crespo-Hernández 1996: TI_w=0.73·a^0.8325·TI_∞^0.0325·(x/D)^-0.32, a=0.5·(1−√(1−Ct)); shared Bastankhah Gaussian σ for radial decay; Frandsen sum-of-squares across upstream sources; combined with pocket TI in quadrature so AR(1) generator sees real downstream σ_v rise) — see #103
- [x] 101 SCADA tags total (was 100): +1 wake-added TI tag (`WMET_WakeTi`)
- [x] Dynamic atmospheric pressure P(t) (synoptic `_pressure_state` ∈ [−1, +1] scaled to ±1500 Pa around 101325 Pa; fed through `get_air_density` so ρ gains another ±1.5% frontal swing on top of T/RH; override rejects to ISA reference) — see #106
- [x] 102 SCADA tags total (was 101): +1 ambient pressure tag (`WMET_AmbPressure`)
- [x] Atmospheric-stability × Bastankhah wake-expansion coupling (k* = k_neutral · clamp(1 + 0.30·s, 0.55, 1.45); stable ABL → longer wake, convective ABL → shorter wake; no new tag, observable via `WMET_WakeDef × WMET_AtmStab`) — see #109
- [x] Removed duplicate `get_wake_added_ti` definition in `PerTurbineWind` (F811 fix after #103/#106 merge) — see #108
- [x] Atmospheric-stability × wind veer coupling (#111): `veer_rate_eff = veer_base · clamp(1 − s, 0.3, 2.5)` (Holton/Stull/van der Laan 2017); stable ABL preserves Ekman spiral (~0.20 °/m, +37% TwrSS), convective ABL mixes it out (~0.03 °/m, −26%); per-turbine `wind_veer_rate` retained as site variance; effective rate flows to both aero power-loss and fatigue load paths; no new SCADA tag — see #111
- [x] Atmospheric-stability × wake meander timescale τ_m coupling (#113): `τ_m_eff = 25 · clamp(1 − 0.6·s, 0.4, 2.0)` s (Counihan 1975 / Larsen DWM 2008 / Peña & Hahmann 2012); stable ABL → 40 s slow meander, neutral → 25 s, convective → 10 s fast turnover; lag-25 s autocorrelation 0.45 vs 0.28 vs 0.01; σ_θ amplitude path stays 0.3·TI (owned by #99 TI mult) so only the timescale path is added; 102 SCADA physics tags unchanged — observable via `WMET_WakeMndr × WMET_AtmStab` autocorrelation — see #113
- [x] Atmospheric-stability × turbulence integral length scale L_u coupling (#115): `L_u_eff = 340 · clamp(1 − 0.6·s, 0.4, 2.0)` m (Counihan 1975 / Kaimal & Finnigan 1994 / Peña & Hahmann 2012 / IEC 61400-1 ed.4 Annex C); stable nocturnal ABL → L_u=544 m / τ≈54 s @ 10 m/s, neutral → 340 m / 34 s, convective afternoon → 136 m / 14 s; validated lag-30 s autocorr 0.574 / 0.401 / 0.097 (stable / neutral / convective) vs analytical 0.576 / 0.414 / 0.110; σ_v amplitude unchanged (owned by #99 TI mult); applied to both farm-wide `_turbulence_gen` and per-turbine `_turb_gens[i]`; 102 SCADA physics tags unchanged — observable via `WMET_AtmStab × WROT_RotSpd` low-frequency autocorrelation — see #115
- [x] Nacelle anemometer transfer function (#117, IEC 61400-12-1 Annex D): real cup/sonic anemometer sits ~1.5R behind hub on top of nacelle, reads systematically below free-stream because of axial induction. NTF formula `V_raw = V_∞ · (1 − k_pos·a)` with `a = 0.5·(1 − √(1 − Ct))` (1-D momentum theory) and `k_pos = 0.55` (anemometer position weight). Operating-state branching: stopped/parked uses bluff-body speed-up `1.04·V_∞`; producing/starting with `rotor_speed > 1 RPM` applies the induction reduction. Self-test (7/7 + monotonicity): Region 2 (Ct=0.82) → 0.84·V_∞; Region 3 (Ct=0.30) → 0.96·V_∞; stopped → 1.04·V_∞; clamped to [0.78, 1.10]. Reuses `aero_out.ct` already computed in `step()` (no extra cost, no new RNG mutation). Backwards compatible: existing `WMET_WSpeedNac` keeps free-stream semantics so `examples/data_quality_analysis.py` and OPC adapter consumers still get the same number; new `WMET_WSpeedRaw` exposes the as-measured anemometer reading (Bachmann OPC suffix `WMET.Z72PLC__UI_Loc_WMET_Analogue_WSpeedRaw`). 103 SCADA tags total (was 102): +1 raw nacelle anemometer tag (`WMET_WSpeedRaw`).
- [x] 103 SCADA tags total (was 102): +1 raw nacelle anemometer tag (`WMET_WSpeedRaw`) — see #117

### Backend
- [x] FastAPI REST APIs
- [x] WebSocket realtime stream
- [x] SQLite history persistence
- [x] SQLite history event persistence
- [x] Modbus TCP simulator
- [x] Wind profile control
- [x] Turbine spec presets
- [x] Grid control API
- [x] Control API: start / stop / reset / service / emergency stop / curtail
- [x] Event export API (JSON/CSV) with severity grouping
- [x] Fault lifecycle event tracking (start/end/phase transitions)
- [x] History retention / downsampling / cleanup policy

### Frontend
- [x] Dashboard and turbine detail views
- [x] Trend chart panel
- [x] Fault injection UI
- [x] Wind and turbine settings UI
- [x] Grid control UI
- [x] History data page
- [x] Event markers, filters, search, details, and focus windows in History
- [x] CSV export entry
- [x] Dashboard default to summary view
- [x] Turbine detail compact layout: metrics bar + side-by-side subsystem/trend
- [x] Multi-turbine event comparison view with timeline, summary, and severity badges

## In Progress Quality Level

These parts are implemented, but still first-generation models:
- [x] Aerodynamics: Cp(λ,β) surface, thrust coefficient, dynamic stall
- [x] Drivetrain: multi-stage gearbox, bearing separation, torsional modes, brake dynamics
- [x] Cooling system: pump/fan state, coolant flow/pressure, fouling propagation
- [x] Wind-event propagation across the farm
- [x] Fault physics unified path with operating-condition coupling
- [x] Vibration feature / frequency-band realism
- [x] Advanced converter / electrical control detail

## Next Priorities

### Priority A: Event Visibility
- [x] Store grid events as explicit history events
- [x] Store operator actions as explicit history events
- [x] Store fault events as explicit history events
- [x] Store automatic state / trip events
- [x] Show event markers in history charts
- [x] Add event filters, search, detail panel, and focus windows
- [x] Add start/end duration for grid and wind config events

### Priority A.1: Event Layer Upgrade
- [x] Add start/end duration for fault lifecycle events
- [x] Add event export as JSON / CSV
- [x] Add event severity grouping / alarm-level badges
- [x] Add multi-turbine event comparison view

### Priority B: Wind Event Realism
- [x] Gust front propagation
- [x] Ramp propagation across turbines
- [x] Direction-shift propagation
- [x] Stronger time-space coupling in farm wind model

### Priority C: Electrical Response Detail
- [x] Frequency-watt response
- [x] Reactive power / power factor
- [x] Improved grid-code style ride-through behavior
- [x] Converter control mode detail

### Priority D: Vibration Upgrade
- [x] Fault-specific vibration signatures
- [x] Frequency-band outputs
- [x] Bearing defect style indicators

### Priority E: Fatigue / Load Modeling
- [x] Tower base bending moments (fore-aft, side-to-side)
- [x] Blade root bending moments (flapwise, edgewise)
- [x] Rainflow cycle counting
- [x] Damage Equivalent Load (DEL) computation
- [x] Cumulative fatigue damage (Miner's rule)
- [x] Frontend load/fatigue tab
- [x] History trend chart preset for load data
- [x] Fatigue alarm thresholds (4-level: notice/warning/danger/shutdown) — see #57
- [x] Remaining Useful Life (RUL) estimation from damage rate — see #57
- [x] Fatigue alarm event integration (auto-generate history events on threshold crossing) — see #57
- [ ] Frontend RUL display and alarm level visualization — see #57

### Priority F: Vibration Condition Monitoring
- [ ] Spectral alarm threshold curves per frequency band — see #58
- [x] Crest factor / kurtosis anomaly alarms — see #58
- [x] Sideband analysis (gear mesh modulation) — see #58
- [x] Bearing defect frequency simulation (BPFO/BPFI) — see #58

## Product / Platform Gaps

### History and Storage
- [x] Add retention / cleanup policy for SQLite history
- [x] Add clearer history query filters and limits
- [x] Add richer event query filters on the backend
- [x] Vibration spectral alarm threshold curves
- [x] Advanced fatigue / DEL load metrics

### Maintenance
- [x] Work order backend schema
- [x] Work order CRUD API
- [x] Technician management API
- [x] Connect `MaintenanceHub` to real backend instead of mock data

### Documentation / External Access
- [x] API Guide for students/researchers (`docs/API_GUIDE.md`)
- [x] Python example scripts (`examples/fetch_scada_data.py`)
- [x] Data quality analysis script (`examples/data_quality_analysis.py`)

### Data Quality Validation (2026-04-12)
- [x] 2-hour multi-scenario simulation with fault injection + wind variation
- [x] Automated analysis: power curve, temperature, vibration, load, correlation
- [x] Report: 18/21 checks passed

## Known Issues / Next Improvements

### Physics Realism (from data quality analysis)
- [x] Region 3 power CV too low (0.8-0.9%): switched to Cp aerodynamic model, pitch lag now creates realistic variation — see #61
- [x] Spectral sideband analysis (modulated harmonics around gear mesh) — see #58
- [x] Bearing defect frequency computation (BPFO/BPFI from geometry) — see #58
- [x] Tower fore-aft dynamic response (SDOF first-mode filter, fn≈0.28 Hz) — see #62
- [x] Tower shadow effect: rotor azimuth tracking + 3P Gaussian torque/thrust/load modulation — see #69
- [x] Wind shear profile: power-law V(h) with azimuth-dependent blade loading, 1P torque modulation — see #71
- [x] Blade mass imbalance: per-turbine blade mass offsets, centrifugal force F=Δm×r_cg×ω², 1P vibration + load coupling — see #72
- [x] Gearbox oil temperature/viscosity: Walther equation, cold-start efficiency loss, overheat degradation — see #73
- [x] Ambient humidity effect on air cooling: moist-air density factor + dew-point condensation penalty, seasonal/diurnal humidity profile — see #89
- [x] Localized turbulence pockets: Gaussian spatial pockets with stochastic spawn (~1 per 10–15 min), per-turbine TI multiplier boost, exposed via `WMET_LocalTi` — see #91
- [x] Wake model upgrade: Bastankhah-Porté-Agel Gaussian wake (replaces simplified Jensen top-hat); TI-dependent expansion, Ct-coupled deficit, sum-of-squares multi-wake superposition, exposed via `WMET_WakeDef` — see #93
- [x] Dynamic wake meandering: Larsen-DWM AR(1) lateral oscillation applied per source (σ_θ=0.3·TI, τ=25 s), downstream `WMET_WakeDef` now has realistic time variability, new `WMET_WakeMndr` tag — see #95
- [x] Yaw-induced wake deflection: Bastankhah 2016 initial skew θ_c=0.3·γ·(1−√(1−Ct·cos γ))/cos γ, δ_y(x)=tan(θ_c)·x coupled per-source; engine feeds per-turbine yaw_error back each step; new `WMET_WakeDefl` tag — see #97
- [x] Atmospheric stability / diurnal shear-TI coupling: Monin-Obukhov-simplified continuous score s ∈ [−1, +1] from solar time × mechanical mixing × cloud damping; drives α (0.04–0.30) and TI multiplier (0.5–1.6); new `WMET_ShearAlpha` + `WMET_AtmStab` tags — see #99
- [x] Air density coupling: ρ(T, RH) = P/(R_d·T) · (1 − 0.378·e/P) with Magnus vapor pressure; fed per-step into `PowerCurveModel.air_density`; power and thrust vary ±10% between cold-dry and hot-humid conditions; new `WMET_AirDensity` tag — see #101
- [x] Wake-added turbulence intensity (Crespo-Hernández 1996): TI_w = 0.73·a^0.8325·TI_∞^0.0325·(x/D)^-0.32 with a = 0.5·(1−√(1−Ct)), near-field capped at x/D=5; shared Bastankhah σ for Gaussian radial decay (no new parameter); Frandsen sum-of-squares across upstream sources; combined with pocket TI (#91) in quadrature before AR(1) generator so downstream σ_v observably rises (+36% at T1 in 3-in-line self-test); new `WMET_WakeTi` tag — see #103
- [x] Dynamic atmospheric pressure P(t): `_pressure_state ∈ [−1, +1]` → `P(t) = 101325 + s·1500 Pa` (mid-latitude ±15 hPa amplitude); fed into `get_air_density(ts, ..., pressure_pa=...)`, so ρ gains another ±1.5% time variability from synoptic weather fronts on top of #101's T/RH coupling; manual override locks P at ISA reference; new `WMET_AmbPressure` tag (hPa) — see #106
- [x] Atmospheric-stability × wake-expansion coupling: Bastankhah k* modulated by the existing #99 continuous stability score s; `k* = k_neutral · clamp(1 + 0.30·s, 0.55, 1.45)`, clamp [0.015, 0.08]. Stable ABL (s<0) slows wake recovery (longer wake, larger deficit at same spacing); convective ABL (s>0) speeds it up. At V=10 m/s, TI=8%, 6 D downstream: stable s=−1 ≈ +34% deficit vs neutral; convective s=+1 ≈ −22%. No new SCADA tag — observable via `WMET_WakeDef × WMET_AtmStab` correlation (expected r < −0.4 at downstream turbines during diurnal cycling) — see #109
- [x] Atmospheric-stability × wind-veer coupling: per-turbine `wind_veer_rate` (#79) is now multiplied by `clamp(1 − s, 0.3, 2.5)` driven by the same #99 continuous stability score s. Stable ABL (s<0) preserves the Ekman spiral → strong veer (~0.20 °/m at s=−1) → +37% tower side-side moment, −13 kW power loss vs neutral; convective ABL (s>0) mixes it out → weak veer (~0.03 °/m at s=+1) → −26% TwrSS. Per-turbine `wind_veer_rate` retained as site/manufacturing variance on top of atmospheric trend. Effective rate flows into both `turbine_physics`'s aero power-loss block (azimuth-dependent equivalent yaw error) and `fatigue_model.step(wind_veer_rate=...)` so structural loads and aero power stay consistent. No new SCADA tag — observable via `WMET_AtmStab × WLOD_TwrSsMom` correlation — see #111
- [x] Atmospheric-stability × wake-meander timescale coupling (#113): the Larsen-DWM AR(1) integral timescale (#95) `τ_m = 25 s` is now stability-dependent: `τ_m_eff = 25 · clamp(1 − 0.6·s, 0.4, 2.0)` s, driven by the same #99 score s. Stable ABL (s<0, suppressed vertical mixing, larger atmospheric integral length scale L_u) → τ_m=40 s (slow, persistent meander); neutral (s=0) → 25 s baseline; convective ABL (s>0, vigorous overturning, shorter L_u) → τ_m=10 s (fast turnover). σ_θ amplitude path is unchanged at 0.3·TI — the amplitude per-stability response is already carried by #99's TI multiplier (0.5–1.6×), so this adds the orthogonal timescale path only. Validation on a 4000 s AR(1) sequence (TI=0.10): lag-25 s autocorrelation 0.45 (stable) / 0.28 (neutral) / 0.01 (convective); zero-crossing rate 0.082 / 0.098 / 0.140 — confirming slower meander under stable conditions and faster turnover under convection. Implementation is a 6-line change in `_update_wake_meander` reusing the `atm_stability` already passed through `PerTurbineWind.step(...)` for #109. No new SCADA tag — observable via `WMET_WakeMndr × WMET_AtmStab` autocorrelation. References: Counihan (1975) *Atmos. Environ.* 9, 871–905; Larsen et al. (2008) *Wind Energy* 11, 289–301; Peña & Hahmann (2012) *Wind Energy* 15, 717–731; IEC 61400-1 ed.4 Annex C — see #113
- [x] Atmospheric-stability × turbulence integral length scale L_u coupling (#115): the Kaimal-style AR(1) integral length scale `L_u = 340 m` (IEC 61400-1 ed.4 hub-height neutral baseline) is now stability-dependent: `L_u_eff = 340 · clamp(1 − 0.6·s, 0.4, 2.0)` m, driven by the same #99 score s. Mapping (V=10 m/s): s=−1 (stable, suppressed mixing, elongated streamwise eddies) → L_u=544 m, τ≈54 s; s=0 (neutral) → 340 m, 34 s; s=+1 (convective, vigorous overturning, broken-up eddies) → 136 m, 14 s. σ_v amplitude path is unchanged at TI·V — the amplitude per-stability response is already carried by #99's TI multiplier (0.5–1.6×), so this adds the orthogonal timescale path only, exactly parallel to #113 for wake meander. Validation on a 4000 s AR(1) sequence (TI=0.10, V=10 m/s): lag-30 s autocorrelation 0.574 (stable) / 0.401 (neutral) / 0.097 (convective) vs analytical exp(−30/τ) = 0.576 / 0.414 / 0.110 — within 1.4 / 3.1 / 1.3 % of the closed form; steady-state σ_v measured at 0.99 / 0.98 / 0.99 m/s vs expected 1.00 — amplitude unchanged. Same s passed to both `_turbulence_gen` (farm base wind in `engine.py`) and every `_turb_gens[i].step(...)` (per-turbine spatial decorrelation in `PerTurbineWind.step`), so the whole farm shares one ABL timescale. No new SCADA tag — observable via `WMET_AtmStab × WROT_RotSpd` low-frequency autocorrelation, plus indirect lift to low-frequency `WLOD_TwrFaMom` content on stable nights. References: Counihan (1975) *Atmos. Environ.* 9, 871–905; Kaimal & Finnigan (1994) *Atmospheric Boundary Layer Flows* §1.6 / §3; Peña & Hahmann (2012) *Wind Energy* 15, 717–731; IEC 61400-1 ed.4 Annex C — see #115

### Deployment (low priority — lab-only use currently)
- [ ] JWT authentication
- [ ] Basic RBAC
- [x] `.env` cleanup (configurable DB_PATH, Docker env vars)
- [x] Docker Compose (backend + frontend + nginx reverse proxy)
- [ ] Reverse proxy / HTTPS (standalone, Docker uses nginx internally)

### Security
- [ ] Upgrade `cryptography` (41.0.7 → ≥46.0.6, 7 CVEs) — see #48
- [ ] Upgrade `pyjwt` (2.7.0 → ≥2.12.0, 1 CVE) — see #48
- [ ] Upgrade `setuptools` (68.1.2 → ≥78.1.1, 3 CVEs) — see #48
- [ ] Add `pip-audit` to CI / development workflow

### Storage
- [ ] Decide whether long-term storage should stay on SQLite or move to time-series DB

### Testing
- [ ] Set up pytest and basic test infrastructure — see #52
- [ ] Unit tests for physics models (`simulator/physics/`)
- [ ] Integration tests for API endpoints (`server/routers/`)
- [ ] Simulation engine state machine tests (`simulator/engine.py`)

### New Feature Requests
- [ ] External data API documentation and access — see #50
- [ ] RAG-based alert analysis with manufacturer manuals — see #51

## Notes

- `README.md` and this roadmap now reflect the actual implemented state.
- Physics-specific status should be maintained in `docs/physics_model_status.md`.
- Data quality report available at `examples/data_quality_report.txt`.
- API reference for external users at `docs/API_GUIDE.md`.

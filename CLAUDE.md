# Project Notes

## Current Position

A working wind farm simulation platform with 100 SCADA tags, comprehensive physics models, and full API access for external data consumers.

Platform includes:
- backend REST + WebSocket APIs (40+ endpoints)
- realtime streaming (2s broadcast cycle)
- SQLite history with retention/downsampling
- physics-based turbine simulation (14 turbines)
- 11 fault scenarios with physics-coupled injection
- grid and wind environment controls
- Modbus TCP simulation
- frontend dashboard, detail, settings, history, and maintenance views
- fatigue/DEL load monitoring
- vibration spectral alarm thresholds (ISO 10816-inspired)

## Current Development Priority

The main priority is physics realism and signal realism.

Primary focus (next improvements):
- Region 3 power variation — fixed: Cp model replaces lookup table, pitch lag creates natural variation — see #61
- tower dynamic response — fixed: SDOF first-mode filter (fn≈0.28 Hz) with structural+aero damping — see #62
- spectral sideband analysis — fixed: gear mesh sideband model with fault-coupled amplitude modulation — see #58
- bearing defect frequency (BPFO/BPFI) — fixed: geometry-based BPFO/BPFI with fault-coupled amplitude — see #58
- tower shadow effect — fixed: rotor azimuth tracking + Gaussian 3P torque/thrust/load modulation — see #69
- gearbox oil temperature/viscosity — fixed: Walther-type viscosity model with cold-start loss decay — see #73
- gear tooth contact — fixed: contact-ratio mesh stiffness ripple + tooth wear index + GMF HSS-torsion excitation — see #76
- ambient humidity air-cooling — fixed: moist-air density factor + dew-point condensation penalty on nacelle/cabinet fans — see #89
- localized turbulence pockets — fixed: spatial Gaussian pockets boost per-turbine TI, observable via `WMET_LocalTi` — see #91
- wake model upgrade — fixed: Bastankhah-Porté-Agel Gaussian wake (TI-dependent expansion, Ct-coupled deficit, sum-of-squares superposition), observable via `WMET_WakeDef` — see #93
- dynamic wake meandering — fixed: Larsen-DWM AR(1) lateral oscillation of wake centerline (σ_θ≈0.3·TI, τ≈25 s), downstream `WMET_WakeDef` now has realistic time variability — see #95
- yaw-induced wake deflection (wake steering) — fixed: Bastankhah 2016 θ_c = 0.3·γ·(1−√(1−Ct·cos γ))/cos γ coupled to per-turbine yaw_error, new `WMET_WakeDefl` tag — see #97
- atmospheric stability / diurnal shear-TI coupling — fixed: continuous score s=solar·wind_damping·cloud_damping drives α ∈ [0.04, 0.30] and TI multiplier ∈ [0.5, 1.6], new `WMET_ShearAlpha` / `WMET_AtmStab` tags — see #99
- air density coupling — fixed: ρ(T, RH) from ideal gas law + Magnus moist-air correction, updated every step and fed into PowerCurveModel so P ∝ ρ·V³ and F ∝ ρ·V² vary with temperature and humidity; new `WMET_AirDensity` tag — see #101

Secondary focus:
- deployment hardening (JWT, Docker) — only when ready to share externally

## Data Quality Status (2026-04-12)

Ran 2-hour automated analysis with mixed wind conditions + fault injection.
Result: **18/21 checks passed**.

Issues found:
- Region 3 power CV=0.8-0.9% (should be 3-5%) — **fixed** in #61: switched to Cp aerodynamic model
- Turbine spread 36.8% (partly due to mixed operating conditions in test, not a real issue)

All physical correlations verified:
- Power curve shape ✓, temperature inertia ✓, vibration-RPM coupling ✓
- Load-thrust correlation ✓, stopped-state behavior ✓, fault signatures ✓

Report: `examples/data_quality_report.txt`

## External API Access

- **API Guide**: `docs/API_GUIDE.md` (complete reference for students/researchers)
- **Example scripts**: `examples/fetch_scada_data.py` (8 ready-to-use patterns)
- **Data quality analysis**: `examples/data_quality_analysis.py`
- **Swagger UI**: `http://<server-ip>:8100/docs`
- No authentication (lab-internal use only)
- CORS open, host binding 0.0.0.0

## Pending Improvements

Still pending or incomplete:
- deployment hardening (JWT, RBAC, HTTPS) — see #26
- spectral alarm threshold curves — see #58; BPFO/BPFI, sideband analysis, and crest factor/kurtosis anomaly alarms completed
- full protection relay coordination (LVRT/OVRT) — see #67
- coolant level / leak detection — done: level tracking + pump cavitation + fault coupling — see #75
- gear tooth contact modeling — done: mesh stiffness ripple + tooth wear + GMF excitation — see #76
- wind veer (directional shear with height) — done: Ekman spiral model + blade lateral force coupling — see #79
- ambient humidity effect on air cooling — done: moist-air density + dew-point condensation penalty (#89)
- localized turbulence pockets — done: Gaussian spatial pockets with per-turbine TI boost + `WMET_LocalTi` tag (#91)
- wake model (Bastankhah-Porté-Agel Gaussian) — done: TI-dependent expansion, Ct-coupled max deficit, sum-of-squares superposition + `WMET_WakeDef` tag (#93)
- dynamic wake meandering — done: Larsen-DWM lateral AR(1) oscillation (σ_θ=0.3·TI, τ=25 s) applied to source wake centerline, new `WMET_WakeMndr` tag (#95)
- yaw-induced wake deflection — done: Bastankhah 2016 skew angle coupled to per-turbine yaw_error, new `WMET_WakeDefl` tag (#97)
- atmospheric stability / diurnal shear-TI coupling — done: Monin-Obukhov-simplified score s drives α ∈ [0.04, 0.30] and TI multiplier ∈ [0.5, 1.6], new `WMET_ShearAlpha` + `WMET_AtmStab` tags (#99)
- air density coupling — done: moist-air ρ(T, RH) via ideal gas + Magnus, fed per-step to PowerCurveModel; aero power and thrust now vary ±10% with temperature/humidity; new `WMET_AirDensity` tag (#101)
- SQLite vs time-series DB architecture decision — see #24
- dependency security vulnerabilities (cryptography, pyjwt, etc.) — see #48
- no automated test suite (pytest) — see #52
- external data API documentation — see #50
- RAG-based alert analysis — see #51
- frontend RUL visualization — see #57 (fatigue alarm event integration completed)

## Source of Truth

Use these files for planning:
- `TODO.md` — development roadmap and known issues
- `docs/physics_model_status.md` — per-model completion status
- `docs/API_GUIDE.md` — external API reference
- `STATUS.yaml` — project metadata

## Working Principle

When making simulation changes:
- prefer changing physical causes over directly offsetting output tags
- prefer persistent per-turbine differences over random noise-only variation
- prefer time-dependent transitions over instant jumps
- keep new work observable in history charts whenever possible
- validate changes with `examples/data_quality_analysis.py`

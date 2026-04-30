# Project Notes

## Current Position

A working wind farm simulation platform with 104 SCADA tags, comprehensive physics models, and full API access for external data consumers.

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
- wake-added turbulence intensity — fixed: Crespo-Hernández (1996) TI_w = 0.73·a^0.8325·TI_∞^0.0325·(x/D)^-0.32, shared Bastankhah Gaussian radial + Frandsen quadrature; combined with pocket TI (#91) in the AR(1) generator so downstream σ_v actually rises; new `WMET_WakeTi` tag — see #103
- dynamic atmospheric pressure coupling — fixed: `_pressure_state → P(t) = 101325 + s·1500 Pa` mapped synoptic state to Pa, fed into `get_air_density` so ρ gains another ±1.5% time variability from weather fronts; new `WMET_AmbPressure` tag — see #106
- atmospheric stability × wake expansion coupling — fixed: Bastankhah `k* = k_neutral · clamp(1 + 0.30·s, 0.55, 1.45)` (Abkar & Porté-Agel 2015 / Peña 2016); stable night → longer wake (≈+34% deficit at 6 D), convective afternoon → shorter wake (≈−22% deficit); no new SCADA tag, observable via `WMET_WakeDef × WMET_AtmStab` correlation — see #109
- atmospheric stability × wind veer coupling — fixed: `veer_rate_eff = veer_base · clamp(1 − s, 0.3, 2.5)` (Holton §5.3, Stull §8.5, van der Laan 2017); stable night ABL preserves Ekman spiral (~0.20 °/m, +37% TwrSS moment vs neutral), convective afternoon mixes it out (~0.03 °/m, −26%); no new SCADA tag, observable via `WMET_AtmStab × WLOD_TwrSsMom` correlation — see #111
- atmospheric stability × wake meander timescale coupling — fixed: `τ_m_eff = 25 · clamp(1 − 0.6·s, 0.4, 2.0)` s (Counihan 1975 / Larsen DWM 2008); stable ABL → 40 s slow meander (lag-25 s autocorr ≈ 0.45), convective ABL → 10 s fast turnover (autocorr ≈ 0.01); σ_θ stays 0.3·TI, only timescale modulated; no new SCADA tag, observable via `WMET_WakeMndr × WMET_AtmStab` autocorrelation — see #113
- atmospheric stability × turbulence integral length scale L_u coupling — fixed: `L_u_eff = 340 · clamp(1 − 0.6·s, 0.4, 2.0)` m (Counihan 1975 / Kaimal & Finnigan 1994 / Peña & Hahmann 2012); stable nocturnal ABL → 544 m, τ ≈ 54 s @ 10 m/s (lag-30 s autocorr ≈ 0.57), neutral → 340 m, τ ≈ 34 s (≈ 0.40), convective afternoon → 136 m, τ ≈ 14 s (≈ 0.10); σ_v amplitude unchanged (TI path owned by #99), only AR(1) timescale modulated; applied to both farm-wide `_turbulence_gen` and per-turbine `_turb_gens[i]`; no new SCADA tag, observable via `WMET_AtmStab × WROT_RotSpd` low-frequency autocorrelation — see #115
- nacelle anemometer transfer function (NTF) — fixed: IEC 61400-12-1 Annex D NTF `V_raw = V_∞ · (1 − 0.55·a)` with `a = 0.5·(1 − √(1 − Ct))`; Region 2 (Ct≈0.82) → ≈0.84·V_∞, Region 3 (Ct≈0.30) → ≈0.96·V_∞, stopped → 1.04·V_∞ (bluff-body speed-up); reuses existing `aero_out.ct` so no extra computation; `WMET_WSpeedNac` keeps free-stream semantics (analysis backwards compat), new `WMET_WSpeedRaw` exposes the as-measured anemometer reading — see #117
- nacelle wind vane transfer function (WVTF) — fixed: IEC 61400-12-2 Annex E swirl bias `θ_s ≈ Ct/(2·λ)` (Burton et al. 2011 §3.7); right-handed rotor → +bias; Region 2 (Ct≈0.82, λ≈7) ≈ +3.4°, Region 3 (Ct≈0.30, λ≈5) ≈ +1.7°, stopped/cut-out → 0°; clamp ±8°; reuses existing `aero_out.ct` and `aero_out.tsr`; `WMET_WDirAbs` keeps free-stream direction (analysis backwards compat, wake & yaw control unchanged), new `WMET_WDirRaw` exposes the as-measured vane reading — see #119
- duplicate `get_wake_added_ti` in `PerTurbineWind` (F811 leftover from #103/#106 merge) — fixed — see #108

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
- wake-added turbulence intensity — done: Crespo-Hernández 1996, shared Bastankhah σ for radial decay, Frandsen quadrature for multi-source, combined with pocket TI in the AR(1) generator so downstream σ_v observably rises; new `WMET_WakeTi` tag (#103)
- dynamic atmospheric pressure P(t) — done: `_pressure_state` (OU random walk, τ≈2 h, frontal cycle 2–7 days) scaled to ±1500 Pa around 101325, fed through `get_air_density` so ρ gains another ±1.5% frontal swing on top of T/RH; new `WMET_AmbPressure` tag (#106)
- atmospheric-stability × Bastankhah k* coupling — done: k* = k_neutral·(1 + 0.30·s) clamped to [0.55, 1.45]×; stable ABL yields ~+34% wake deficit at 6 D, convective ~−22%; no new SCADA tag (uses existing `WMET_WakeDef × WMET_AtmStab`) (#109)
- atmospheric-stability × wind veer coupling — done: `veer_rate_eff = veer_base · clamp(1 − s, 0.3, 2.5)` (Holton/Stull/van der Laan 2017); stable night ~0.20 °/m with +37% TwrSS moment, convective afternoon ~0.03 °/m with −26%; per-turbine veer_rate retained as site/manufacturing variance; effective rate is shared between aero power-loss and fatigue tower/blade load paths; no new SCADA tag (#111)
- atmospheric-stability × wake meander τ_m coupling — done: integral timescale `τ_m = 25 · clamp(1 − 0.6·s, 0.4, 2.0)` s (Counihan 1975 / Larsen DWM 2008 / Peña 2012); stable ABL → 40 s slow meander, convective ABL → 10 s fast turnover; σ_θ stays 0.3·TI (amplitude path is #99 TI mult); validated lag-25 s autocorr 0.45 vs 0.01 for stable vs convective; no new SCADA tag (`WMET_WakeMndr × WMET_AtmStab` autocorrelation) (#113)
- atmospheric-stability × turbulence integral length scale L_u coupling — done: `L_u_eff = 340 · clamp(1 − 0.6·s, 0.4, 2.0)` m (Counihan 1975 / Kaimal & Finnigan 1994 / Peña & Hahmann 2012); stable nocturnal ABL → 544 m / τ ≈ 54 s @ 10 m/s, neutral → 340 m / τ ≈ 34 s, convective afternoon → 136 m / τ ≈ 14 s; validated lag-30 s AR(1) autocorr 0.57 vs 0.40 vs 0.10 (stable / neutral / convective); σ_v amplitude unchanged (TI path owned by #99); applied to both farm-wide `_turbulence_gen` and per-turbine `_turb_gens[i]`; no new SCADA tag (#115)
- nacelle anemometer transfer function (NTF) — done: IEC 61400-12-1 Annex D NTF `V_raw = V_∞ · (1 − 0.55·a)` with `a = 0.5·(1 − √(1 − Ct))` derived from existing `aero_out.ct`; Region 2 → 0.84·V_∞, Region 3 → 0.96·V_∞, stopped → 1.04·V_∞; backwards compat — `WMET_WSpeedNac` keeps free-stream semantics, new `WMET_WSpeedRaw` exposes the as-measured anemometer reading (#117)
- nacelle wind vane transfer function (WVTF) — done: IEC 61400-12-2 Annex E swirl-bias model `θ_swirl ≈ Ct / (2·λ)` rad (Burton et al. 2011, Wind Energy Handbook §3.7) for right-handed rotor; reuses `aero_out.ct` and `aero_out.tsr` already computed for #117 (no extra cost); Region 2 (Ct=0.82, λ=7) → +3.36°, Region 2.5 (Ct=0.65, λ=6) → +3.10°, Region 3 (Ct=0.30, λ=5) → +1.72°, stopped → 0°; clamp ±8°; double monotonicity Ct↑→bias↑ and λ↑→bias↓ verified; backwards compat — `WMET_WDirAbs` keeps free-stream semantics (wake-model upstream indexing + yaw-controller logic untouched), new `WMET_WDirRaw` exposes the as-measured vane reading; pairs with #117 to complete the IEC 61400-12-1/2 nacelle sensor transfer function chain (#119)
- nacelle wind vane transfer function (WVTF) — done: IEC 61400-12-2 Annex E swirl bias `θ_s ≈ Ct/(2·λ)` rad (Burton et al. 2011 §3.7) reusing `aero_out.ct` / `aero_out.tsr` already in `step()`; right-handed rotor → +bias; Region 2 (Ct=0.82, λ=7) → +3.36°, Region 3 (Ct=0.30, λ=5) → +1.72°, stopped → 0°; clamped to ±8°; `WMET_WDirAbs` keeps free-stream semantics for wake indexing/yaw control, new `WMET_WDirRaw` exposes the as-measured vane reading (#119); 11/11 self-tests PASS including 360° wrap-around and Ct↑/λ↑ monotonicity
- nacelle wind vane transfer function (WVTF) — done: IEC 61400-12-2 Annex E swirl bias `θ_swirl ≈ Ct / (2·λ)` rad (Burton et al. 2011 §3.7, derived from BEM tangential induction `a' = Ct/(4·λ)`); Region 2 (Ct≈0.82, λ≈7) → +3.4°, Region 3 (Ct≈0.30, λ≈5) → +1.7°, stopped → 0°; clamp ±8° (Pedersen 2008 measured 3–8° on real machines); right-handed rotor convention (industry standard); reuses `aero_out.ct` + `aero_out.tsr` (no extra cost, no new RNG); 10/10 self-test PASS + Ct↑→bias↑ + λ↑→bias↓ monotonicity + 360° wrap correctness; backwards compat — `WMET_WDirAbs` keeps free-stream semantics (yaw_model control-error and wake-source indexing unchanged), new `WMET_WDirRaw` exposes as-measured vane reading; with #117 NTF this completes the IEC 61400-12-1/2 nacelle sensor transfer-function pair (#119)
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

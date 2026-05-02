# Physics Model Status

Last updated: 2026-05-02 (cup-anemometer overspeeding bias on NTF, IEC 61400-12-1 Annex H, #127)

This document tracks the current completion status of the wind turbine physics models.
It is intended to be the single reference for:
- what is already modeled,
- what exists but still needs refinement,
- what has not been modeled yet,
- and what should be prioritized next.

## 1. Completed Models

### 1.1 Turbine Main State Machine
File: `simulator/physics/turbine_physics.py`

Status: implemented

Included:
- Turbine state mapping `1-9`
- delayed startup sequence
- synchronization stage before production
- normal stop flow
- emergency stop flow
- operator stop/start/reset/service logic
- curtailment handling
- restart inhibit / cooldown logic

Current realism level:
- Good enough for operational trend simulation and state transitions.
- Startup, stop, and restart no longer jump directly to steady-state values.

### 1.2 Power Curve and Rotor Speed
File: `simulator/physics/power_curve.py`

Status: implemented

Included:
- Region 2 / Region 3 power behavior
- cut-in / rated / cut-out handling
- rotor inertia via first-order response
- rated-speed holding behavior

Current realism level:
- Good trend-level realism.
- Region 3 now uses Cp(λ,β) aerodynamic model — pitch controller lag and dead-band create realistic 3-5% power variation around rated (previously locked to constant lookup table). See #61.
- Suitable for SCADA-like output and operator demo use.

### 1.3 Drivetrain and Brake Dynamics
File: `simulator/physics/turbine_physics.py`

Status: first usable version implemented

Included:
- rotor-side and generator-side speed separation
- shaft twist / slip dynamics
- normal brake torque
- emergency brake torque
- torsion-induced vibration contribution
- brake heat coupling into thermal model

Current realism level:
- Good transient realism for start/stop/trip events.
- Enough to make `WROT_RotSpd`, `WGEN_GnSpd`, and `WCNV_CnvGnFrq` behave less ideally.

### 1.4 Thermal Model
File: `simulator/physics/thermal_model.py`

Status: implemented

Included:
- 10 thermal elements
- startup / shutdown thermal inertia
- residual heat memory
- wind-assisted cooling
- nacelle / cabinet / exposed component cooling differences
- heat soak between nearby components
- fault heat injection
- brake heat and drivetrain loss heat coupling

Current realism level:
- Good SCADA trend realism.
- Temperatures now behave like thermal systems instead of following power directly.

### 1.5 Vibration Model
File: `simulator/physics/vibration_model.py`

Status: implemented

Included:
- rotational component (1P)
- blade-pass component (3P)
- aerodynamic turbulence contribution
- drivetrain/load contribution
- broadband noise
- low-pass smoothing
- extra contributions from faults and drivetrain torsion

Current realism level:
- Good trend-level monitoring realism.
- Enough for alarm trend and comparative fault behavior.

### 1.6 Yaw Model
File: `simulator/physics/yaw_model.py`

Status: implemented

Included:
- yaw deadband
- activation delay
- post-action hold
- cable unwind
- brake pressure behavior
- smoother yaw command response

Current realism level:
- Good operational realism for alignment trends and yaw-induced performance effects.

### 1.7 Wind Field Model
File: `simulator/physics/wind_field.py`

Status: implemented

Included:
- turbulence generator
- spatial decorrelation
- simple wake deficit
- per-turbine wind variation

Current realism level:
- Good first-stage farm-wide wind realism.
- Enough to make nearby turbines non-identical.

### 1.8 Fault-to-Physics Coupling
Files:
- `simulator/physics/fault_engine.py`
- `simulator/physics/turbine_physics.py`

Status: implemented

Included:
- 7 fault scenarios
- gradual severity progression
- physical influence on heat, vibration, pitch, yaw, speed, power, and cooling
- emergency stop interaction for tripping faults

Current realism level:
- Good enough for diagnostics demos and trend analysis.
- Faults are no longer only output-tag offsets.

### 1.9 Grid Model and Grid-Side Response
Files:
- `simulator/grid_model.py`
- `simulator/physics/turbine_physics.py`

Status: implemented

Included:
- grid frequency and voltage profiles
- manual override
- recovery profile
- per-turbine local grid bias
- per-turbine derate sensitivity
- per-turbine trip margin
- ride-through accumulation logic
- per-turbine reconnect delay

Current realism level:
- Good farm-event realism.
- Same grid event can now produce different turbine-level responses.

### 1.10 Sensor Model
File: `simulator/physics/turbine_physics.py`

Status: implemented

Included:
- measurement noise
- slow drift
- quantization
- occasional stuck/frozen values
- tag-dependent sensor behavior

Current realism level:
- Good SCADA realism.
- Prevents signals from looking overly clean and synthetic.

## 2. Implemented But Still Needs Refinement

These areas exist and are usable, but are still first-generation models.

### 2.1 Aerodynamics — Cp(λ,β) Surface Model
File: `simulator/physics/power_curve.py`

Status: **upgraded** (previously lookup-only, now has Cp surface)

Implemented:
- `Cp(λ, β)` analytical surface model (parametric c1–c6 coefficients)
- dynamic stall factor (transient Cp reduction during rapid wind changes)
- thrust coefficient `Ct(λ, β)` with Glauert correction
- aerodynamic thrust force computation
- aero torque output for drivetrain coupling
- aero load factor output for vibration coupling
- Region 2: Cp-based with lookup safety floor; Region 3: full Cp model (pitch lag creates variation)
- 4% overshoot allowance for transient pitch-lag behavior

Newly implemented:
- tower shadow effect: rotor azimuth tracking, Gaussian per-blade shadow model, 3P torque/thrust/power modulation (see #69)
- wind shear profile: power-law V(h) = V_hub × (h/h_hub)^α, azimuth-dependent blade loading, 1P torque modulation, per-turbine shear exponent individuality (see #71)

Still missing:
- full BEM (blade element momentum) method
- detailed blade aerodynamic loading distribution

### 2.2 Drivetrain — Multi-Stage Gearbox Model
File: `simulator/physics/drivetrain_model.py`

Status: **upgraded** (previously inline, now dedicated model with gearbox stages)

Implemented:
- `DrivetrainModel` class with `DrivetrainSpec` configuration
- multi-stage gearbox (3 stages for geared turbines: 2 planetary + 1 helical)
- per-stage gear ratio, efficiency, and loss calculation
- main bearing friction with axial load (thrust) coupling
- gearbox bearing friction (separate from main bearing)
- two torsional modes: low-speed shaft (LSS) and high-speed shaft (HSS)
- hydraulic brake pressure build-up dynamics (pressure rise/fall rate)
- brake torque from pressure (proportional model)
- separate bearing heat outputs for thermal model coupling
- automatic direct-drive vs geared selection from TurbineSpec
- per-turbine individuality for stiffness, damping, and brake response

Newly implemented:
- gearbox oil temperature tracking (first-order thermal model from gearbox losses)
- Walther-type viscosity ratio with cold-start loss decay (~10 min)
- viscosity-adjusted drivetrain losses feed back into gearbox bearing heat
- new SCADA tag: `WDRV_GbxOilTmp` (see #73)

Newly implemented:
- gear tooth contact model (#76): cyclic mesh-stiffness ripple from contact ratio (ε_α), deterministic GMF torque ripple fed into HSS torsion, Archard-like tooth wear accumulator with `gearbox_overheat` coupling, wear-driven GMF band + sideband amplification
- new SCADA tag: `WDRV_GbxToothWear`

Still missing:
- per-tooth pitting/spalling frequency model (individual tooth defect)

### 2.3 Vibration Spectral Model
File: `simulator/physics/vibration_spectral.py`

Status: **upgraded** (previously trend-only, now has frequency-band decomposition)

Implemented:
- `SpectralVibrationModel` class with per-turbine permanent characteristics
- 5 frequency bands: 1P (rotor imbalance), 3P (blade pass), gear mesh, high-frequency, broadband
- X and Y direction separation for each band
- crest factor (peak/RMS ratio — bearing defect indicator)
- kurtosis (signal impulsiveness — condition indicator)
- fault-specific vibration signatures for all 11 fault scenarios:
  - bearing_wear → elevated HF, high crest factor and kurtosis
  - pitch_imbalance → elevated 1P (asymmetric Y dominant)
  - gearbox_overheat → elevated gear mesh band
  - blade_icing → elevated 1P + 3P (mass + aero imbalance)
  - generator_overspeed → elevated HF
  - yaw_misalignment → elevated 3P
  - stator_winding_degradation → elevated HF (electrical noise)
  - hydraulic_leak → elevated broadband
- operating-condition coupling (speed, power, load)
- low-pass smoothing for realistic time behavior
- BPFO/BPFI bearing defect frequency computation from geometry (n=23, d/D=0.18, α=10°)
- fault-coupled BPFO/BPFI amplitude (grows with bearing_wear severity)
- per-turbine ±3% bearing geometry variation (manufacturing tolerance)

- gear mesh sideband analysis: GMF computation, 1st/2nd order sideband amplitudes, sideband energy ratio
- sideband fault coupling: gearbox_overheat amplifies sidebands with severity × load_factor

### 2.4 Cooling System — Active Component Model
File: `simulator/physics/cooling_model.py`

Status: **upgraded** (previously implicit, now explicit cooling component model)

Implemented:
- `CoolingSystem` class with `CoolingSpec` configuration
- water cooling loop: pump state, flow rate dynamics, pressure dynamics
- coolant temperature tracking with heat load and radiator effectiveness
- nacelle fan bank (2 fans, independent health/state)
- cabinet fan bank (3 fans, independent health/state)
- fouling / degradation accumulation over time
- fouling reduces flow rate and radiator effectiveness
- fouling increases loop pressure (restriction)
- cooling_bias output feeds directly into existing ThermalSystem
- IGCT water pressure now driven by actual pump state
- API hooks for pump degradation, fan failure/repair, loop cleaning

Newly implemented:
- coolant level tracking with leak detection: level state variable (0-100%), leak rate input (L/h), pump cavitation at low level (<70%), 3-level alarm (low/very_low/critical), `converter_cooling_fault` triggers O-ring degradation leak, maintenance refill API (see #75)

Newly implemented:
- ambient humidity effect on air cooling (#89): moist-air density factor `1 − 0.0007 × max(0, RH − 50)` (floor 0.965), dew-point condensation penalty `max(0, (5 − (T − T_d)) × 0.01)` (floor 0.94), applied to nacelle and cabinet fan effectiveness; seasonal/diurnal/weather-front humidity profile from `WindEnvironmentModel.get_ambient_humidity`; new SCADA tag `WMET_HumOutside`

Still missing:
- detailed radiator fin model

### 2.5 Electrical / Converter Response
File: `simulator/physics/electrical_model.py`

Status: **upgraded** (previously inline, now dedicated model with full grid-code behavior)

Implemented:
- `ElectricalModel` class with `ElectricalSpec` configuration
- frequency-watt (droop) response with deadband and per-turbine droop variation
- reactive power dispatch from voltage support and PF setpoint
- power factor computation (active/reactive/apparent power triangle)
- apparent power limiter (converter MVA rating)
- LVRT ride-through curves (0V/50%/80%/90% voltage bands with time limits)
- HVRT ride-through curves (110%/120% voltage bands)
- ride-through trip logic with band accumulation
- synthetic inertia response (virtual H constant, df/dt → power injection)
- converter operating mode tracking (idle/starting/normal/freq_response/voltage_support/ride_through)
- per-turbine individuality for droop sensitivity and reactive power bias

Still missing:
- full reactive power dispatch curve by grid code
- protection coordination relay model
- detailed sub-transient behavior

### 2.6 Wind Event Realism
File: `simulator/physics/wind_field.py`

Status: **upgraded** (previously static offsets, now full spatial propagation)

Implemented:
- wind farm layout model with turbine positions (staggered 2-row grid)
- gust front propagation across turbines with time delay
- wind speed ramp propagation (gradual increase/decrease wave)
- wind direction shift propagation
- cosine-shaped event envelope (rise → hold → fall)
- direction-aware wake model (Jensen/Park-like)
- per-turbine turbulence generators (spatial decorrelation)
- stochastic natural event generation (gusts ~10-20 min, ramps ~30-60 min, dir shifts ~20-40 min)
- API for injecting custom wind events

Newly implemented:
- wind shear profile: power-law vertical wind profile with configurable exponent (default α=0.2, per-turbine variation ±0.04-0.06), azimuth-dependent blade loading in fatigue model (see #71)

Newly implemented:
- wind veer (directional shear with height): linear Ekman spiral model, per-turbine veer rate (0.07–0.13 °/m), azimuth-dependent blade direction offset, lateral force coupling to tower SS and blade flapwise moments (see #79). The per-turbine `wind_veer_rate` is now the *baseline* component; the actual rate fed to the aero / fatigue paths is dynamically modulated by atmospheric stability (#111).

Newly implemented:
- localized turbulence pockets (#91): Gaussian spatial pockets (R=180–380 m), stochastic spawn (~1 per 10–15 min at 10 m/s), TI multiplier 1.4–2.0× at pocket center with Gaussian falloff, rise/hold/fall envelope; applies per-turbine TI boost to `TurbulenceGenerator`; new SCADA tag `WMET_LocalTi` (local TI multiplier %)

Newly implemented:
- Bastankhah-Porté-Agel Gaussian wake model (#93): replaces the simplified Jensen top-hat. Implements ε/D near-wake offset, linear wake expansion σ(x)/D = k*·(x/D)+ε/D with TI-dependent k* (Niayifar & Porté-Agel 2016 k*≈0.38·TI+0.004), Ct-coupled max deficit C(x)=1−√(1−Ct/(8·(σ/D)²)), Gaussian radial profile, and sum-of-squares multi-wake superposition. Ct heuristically follows operating point (~0.82 in Region 2, drops with V² above rated). New SCADA tag `WMET_WakeDef` (wake velocity deficit %).

Newly implemented:
- Dynamic wake meandering (#95, Larsen DWM 2008): each turbine's wake centerline oscillates laterally as an AR(1) process with σ_θ ≈ 0.3·TI (radians) and τ ≈ 25 s (atmospheric integral timescale). The meander offset θ_m[source]·x_down is applied to the signed cross-stream distance inside the Bastankhah Gaussian deficit term, so downstream turbines now see time-varying deficit (±1% std at TI=0.08, 500 m spacing). New SCADA tag `WMET_WakeMndr` (wake lateral offset at 3D reference, m, ±50).

Newly implemented:
- Yaw-induced wake deflection / wake steering (#97, Bastankhah & Porté-Agel 2016): for each source turbine j with yaw misalignment γ_j (=yaw_error, clamped ±45°), the initial skew angle is θ_c = 0.3·γ·(1−√(1−Ct·cos γ))/cos γ. Near-wake lateral deflection δ_y(x) = tan(θ_c)·x_down is added per-source to the signed cross-stream distance (alongside DWM meander). Engine captures per-turbine `WYAW_YwVn1AlgnAvg5s` each step and feeds it back to `PerTurbineWind.set_yaw_misalignments()` before the next wake update, so the `yaw_misalignment` fault and transient yaw lag both drive end-to-end wake steering. At γ=15°/Ct=0.82 the wake centerline deflects ~9.4 m @ 3D (exact closed-form match), ~22 m @ 500 m downstream. New SCADA tag `WMET_WakeDefl` (m, ±50).

Newly implemented:
- Atmospheric stability / diurnal shear-TI coupling (#99, Monin-Obukhov simplified): continuous stability score s ∈ [−1, +1] composed from solar(t) · wind_damping(V) · cloud_damping(pressure). Drives:
  - wind shear exponent α = clamp(0.14 − 0.10·s, 0.04, 0.30) — nighttime 0.18–0.22, convective afternoon 0.08–0.11
  - turbulence multiplier TI_mult = clamp(1.0 + 0.5·s, 0.5, 1.6) — applied to base TI in both the global and per-turbine turbulence generators
  - Strong-wind regime (V > 15 m/s) damps |s| toward 0 (mechanical mixing)
  - Low-pressure / frontal weather damps |s| toward 0 (cloud cover)
  - Manual wind overrides force neutral s = 0
  - per-turbine permanent α offset (±0.04–0.06) renamed to `wind_shear_exp_offset` and stacks on farm-level α
  - New SCADA tags: `WMET_ShearAlpha` (α), `WMET_AtmStab` (s)

Newly implemented:
- Air density coupling (#101): moist-air ρ from ideal gas law + Buck/Magnus vapor correction,
  `ρ = P/(R_d·T_K) · (1 − 0.378·e/P)`, P=101325 Pa, R_d=287.058. `WindEnvironmentModel.get_air_density(ts, temp?, rh?)` shares the temp/humidity already computed for stability, so no extra RNG mutation per step. Engine passes ρ to every turbine (same airmass), and `turbine_physics.step()` writes it into `PowerCurveModel.air_density` each tick so aero power `P = Cp·0.5·ρ·A·V³` and thrust `F = 0.5·ρ·A·Ct·V²` both respond automatically. Verified: 15 °C / 0% RH → 1.2250 (ISA), −10 °C / 50% RH → 1.3406 (+9.4%), 32 °C / 95% RH → 1.1372 (−7.2%), cold/hot power ratio 1.123. Clamp [0.95, 1.35]. New SCADA tag `WMET_AirDensity`.

Newly implemented:
- Wake-added turbulence intensity (#103, Crespo-Hernández 1996 / IEC 61400-1 Annex E):
  per source-target pair, `TI_added(x, r) = 0.73·a^0.8325·TI_amb^0.0325·(x/D)^-0.32 · gauss(r)` where `a = 0.5·(1−√(1−Ct))` is the axial induction factor. Multi-source contributions combine as sum-of-squares; the result is then quadratically combined with the localized-pocket TI multiplier (#91) — `TI_eff² = (TI_amb·pocket_mult)² + TI_w²` — and fed back into the per-turbine AR(1) wind generator so downstream wind_speed σ rises naturally (downstream/upstream σ ratio measured at 2.12× in self-test). Reuses the Bastankhah Gaussian envelope (#93) and the meander/yaw deflection geometry (#95/#97), so no new pair-distance loop. Self-test: isolated → 0%, 5D downstream → ~14%, 12D → ~10%, multi-row sum-of-squares accumulating, Region 2 (Ct≈0.82) > Region 3 (Ct≈0.31). New SCADA tag `WMET_WakeTi` (REAL32, %, 0–40).

Newly implemented:
- Dynamic atmospheric pressure coupling (#106, extends #101): the existing synoptic weather state `_pressure_state ∈ [−1, +1]` (OU random walk, τ≈2 h, frontal cycle 2–7 days) is mapped to real pressure via `P(t) = 101325 + s·1500 Pa`, bounded to [90000, 105000] Pa. Mid-latitude amplitude ±15 hPa matches temperate-zone frontal statistics (1 σ ≈ 8 hPa, 2 σ ≈ 15 hPa). `WindEnvironmentModel.get_air_density(ts, ..., pressure_pa=...)` now accepts the per-step P so ρ responds to synoptic swings on top of T/RH. With identical T=15 °C / RH=50%, high-P (+15 hPa) vs low-P (−15 hPa) gives ρ=1.2392 vs 1.2030 (Δρ = 3.01%). `WindFarmSimulator._run_one_step` computes P once and hands it to both `get_air_density` and every `turbine.step(..., ambient_pressure_pa=...)` so the whole farm shares the same airmass P. Manual overrides lock P at ISA reference (101325 Pa) to keep demos predictable. New SCADA tag `WMET_AmbPressure` (hPa, 900–1050).

Newly implemented:
- Atmospheric-stability × wake-expansion coupling (#109, connects #99 × #93, Abkar & Porté-Agel 2015 / Peña et al. 2016): the Bastankhah wake expansion rate `k* = 0.38·TI + 0.004` is now modulated by the existing #99 stability score `s ∈ [−1, +1]`: `k*_eff = k*_neutral · clamp(1 + 0.30·s, 0.55, 1.45)`, clamped to `[0.015, 0.08]`. Stable ABL (s<0, nocturnal / low wind / clear sky) suppresses vertical mixing → smaller k* → wake persists farther. Convective ABL (s>0, afternoon surface heating) enhances mixing → larger k* → wake recovers faster. Self-test on a 3-turbine row at 6 D spacing, V=10 m/s, TI=8 %: stable s=−1 → wake deficit +33.8 %; convective s=+1 → deficit −22.0 %. No new SCADA tag is introduced — the effect is directly observable via correlation between existing `WMET_WakeDef` (per-turbine deficit) and `WMET_AtmStab` (farm-level s). `simulator/engine.py::_run_one_step` passes `atm_stability` into `PerTurbineWind.step(..., atm_stability=...)` which forwards to `_update_wake_factors(..., stability=...)`.

Newly implemented:
- Atmospheric-stability × wind-veer coupling (#111, connects #99 × #79, Holton *Atmospheric Dynamics* §5.3 / Stull *Boundary Layer Met* §8.5 / van der Laan et al. 2017 *Wind Energy* 20, 1191–1208): the per-turbine `wind_veer_rate` (#79 baseline 0.10 ± 0.03 °/m) is now multiplied by `factor = clamp(1 − 1.0·s, 0.3, 2.5)` driven by the existing #99 stability score `s ∈ [−1, +1]`. Stable ABL (s<0, nocturnal) preserves the Ekman spiral → strong veer; convective ABL (s>0, afternoon mixing) mixes the directional gradient out → weak veer. Mapping: s=−1 → veer ≈ 0.20 °/m; s=0 → 0.10 °/m (neutral baseline); s=+1 → 0.03 °/m (clamped). Self-test (12 m/s steady, 200 s warm-up): tower side-side moment 255.9 kNm at s=−1 vs 137.2 kNm at s=+1 (+37 % / −26 % vs 186.2 kNm neutral); aero power loss differs by ~13 kW between extremes. Per-turbine `wind_veer_rate` is retained as site/manufacturing variance on top of the atmospheric trend. The effective `veer_rate` is computed once per step in `turbine_physics.step()` (block #79 aero power-loss) and the same value is passed to `fatigue_model.step(wind_veer_rate=...)` so structural loads and aero power stay numerically consistent. No new SCADA tag — observable via `WMET_AtmStab × WLOD_TwrSsMom` correlation; expected r < −0.4 at producing turbines during diurnal cycling.

Newly implemented:
- Atmospheric-stability × wake-meander τ_m coupling (#113, connects #99 × #95, Counihan 1975 *Atmos. Environ.* 9, 871–905 / Larsen et al. 2008 *Wind Energy* 11, 289–301 / Peña & Hahmann 2012 *Wind Energy* 15, 717–731 / IEC 61400-1 ed.4 Annex C): the DWM AR(1) atmospheric integral timescale (#95 baseline `τ_m = 25 s`) is now stability-dependent. `_update_wake_meander(turbulence_intensity, dt, stability)` computes `τ_m_eff = 25 · clamp(1 − 0.6·s, 0.4, 2.0)` s using the existing #99 score `s ∈ [−1, +1]`. Mapping: s=−1 (stable, suppressed vertical mixing, larger streamwise integral length scale L_u) → τ_m=40 s (slow meander); s=0 (neutral) → 25 s baseline; s=+1 (convective, vigorous overturning) → τ_m=10 s (fast turnover). σ_θ amplitude path is unchanged (still `0.3·TI`) — the amplitude response to stability is already owned by #99's TI multiplier (0.5–1.6×), so this PR adds the orthogonal timescale path only. Self-test on a 4000 s AR(1) sequence at TI=0.10 (1 turbine, σ_θ ≈ 0.030 rad theoretical): lag-25 s autocorrelation 0.452 (stable) / 0.283 (neutral) / 0.010 (convective), matching the analytical `exp(−25/τ)` of 0.535 / 0.368 / 0.082; zero-crossing rate of `WMET_WakeMndr` 0.082 / 0.098 / 0.140 — slower waveform under stable ABL, faster turnover under convection. Implementation is a 6-line change inside `_update_wake_meander` plus passing `stability=atm_stability` from `PerTurbineWind.step(...)` (the kwarg was already plumbed through for #109). No new SCADA tag — directly observable via `WMET_WakeMndr × WMET_AtmStab` autocorrelation; the persistent meander on stable nights also feeds back into downstream blade DEL through the existing wake-meander → Bastankhah deficit path so `WLOD_BldFlapMom` low-frequency content should mirror the lag-25 s rise.

Newly implemented:
- Nacelle anemometer transfer function (#117, IEC 61400-12-1 ed.2 Annex D / IEC 61400-12-2 / Smaïli & Masson 2004 / Antoniou & Pedersen 1997): the SCADA tag `WMET_WSpeedNac` previously aliased the free-stream wind `effective_wind_speed`, which is what the model uses internally for `Cp(λ,β)` and `Ct(λ,β)`. A real cup/sonic anemometer mounted on top of the nacelle sits ~1.5R behind the hub, in the rotor's induction zone, so it reads systematically below free-stream. The NTF derives the as-measured reading from momentum theory `a = 0.5·(1 − √(1 − Ct))` and a position weight `k_pos = 0.55`: `V_raw = V_∞ · (1 − 0.55·a)`. Operating-state branching: producing or starting with `rotor_speed > 1 RPM` applies the induction reduction; otherwise (rotor stopped/parked, no induction) the bluff-body speed-up at the nacelle top dominates → `V_raw = 1.04·V_∞`. Final clamp to `[0.78, 1.10]` keeps the factor inside physically observed bounds. Self-test (7/7 + monotonicity check on a fixed `aero_out.ct` sweep): Region 2 (Ct=0.82) → 0.84·V_∞; Region 2.5 (Ct=0.65) → 0.89·V_∞; Region 3 (Ct=0.30) → 0.96·V_∞; stopped/cut-out → 1.04·V_∞; clamp triggers at Ct=0.95 → 0.79·V_∞. Implementation reuses `aero_out.ct` already computed by `power_curve.get_power_cp(...)` so there is zero extra cost and no new RNG mutation. Backwards compatibility: the existing `WMET_WSpeedNac` is intentionally left as the free-stream wind so that `examples/data_quality_analysis.py` (which uses it as the X-axis of the power curve), `server/routers/turbines.py`, `server/opc_adapter.py`, the frontend trend chart panel, and the `data_quality_report.txt` 18/21 pass-rate are all unchanged. The new `WMET_WSpeedRaw` (REAL32, m/s, 0–40, OPC suffix `WMET.Z72PLC__UI_Loc_WMET_Analogue_WSpeedRaw`) carries the as-measured reading so downstream consumers can opt in to the more realistic signal — for instance, IEC 61400-12-2 power performance verification scripts can apply the inverse NTF to recover the free-stream wind, exactly as is done in field measurements. 103 SCADA tags total (was 102): +1 raw nacelle anemometer tag (`WMET_WSpeedRaw`).
- Nacelle wind vane transfer function (#119, IEC 61400-12-2 ed.1 §6.4 + Annex E / Burton, Sharpe, Jenkins, Bossanyi 2011 *Wind Energy Handbook* 2nd ed. §3.7 / Pedersen et al. 2008 Risø-R-1602 / Kragh & Hansen 2014 *J. Sol. Energy Eng.* 136): the SCADA tag `WMET_WDirAbs` previously aliased the free-stream wind direction `wind_direction`. A real wind vane (cup or ultrasonic) mounted on top of the nacelle sits ~1.5R behind the hub, in the rotor's swirl zone, and reads a systematic angular bias because the rotor converts linear inflow into linear+rotational outflow (angular momentum conservation, Euler turbine equation). Burton et al. §3.7 derives the swirl angle from blade-element-momentum theory: tangential induction `a' = Ct / (4·λ)` produces a downstream swirl angle `θ_s ≈ 2·a' = Ct / (2·λ)` rad. The sign follows the rotor sense; modern utility-scale turbines are right-handed (clockwise from the upwind side, e.g. Vestas V236, GE Haliade-X, Siemens Gamesa SG 14-222 DD), giving a positive vane bias downstream of the hub. Operating-state branching: stopped/parked (`is_producing == False and is_starting == False`) or `rotor_speed ≤ 1 RPM` or `tsr ≤ 1` → 0° (no rotor torque, no swirl); producing/starting with `rotor_speed > 1 RPM` and `tsr > 1` → `vane_bias_deg = degrees(Ct / (2·λ))`. Final clamp to `±8°` mirrors the largest realistic field observations even at extreme Ct/λ. Self-test (8/8 + double monotonicity, against a fixed (Ct, λ, rotor_state) sweep): Region 2 (Ct=0.82, λ=7) → +3.36°; Region 2.5 (Ct=0.65, λ=6) → +3.10°; Region 3 (Ct=0.30, λ=5) → +1.72°; starting (Ct=0.55, λ=6) → +2.63°; stopped/cut-out → 0.00°; extreme Ct=0.95/λ=4 → +6.80° (within ±8° clamp); 360°-wrap (358° + 3.36° → 1.36°) ✓. Monotonicity Ct↑ → bias↑ (Ct=0,0.3,0.5,0.7,0.82,0.9 at λ=7 → 0.00, 1.23, 2.05, 2.87, 3.36, 3.68°) and λ↑ → bias↓ (λ=3,5,6,7,8,10 at Ct=0.82 → 7.83, 4.70, 3.92, 3.36, 2.94, 2.35°) verified. Implementation reuses both `aero_out.ct` and `aero_out.tsr` already computed by `power_curve.get_power_cp(...)` for the #117 NTF block, so zero extra cost, no new RNG mutation, no new state. Backwards compatibility: the existing `WMET_WDirAbs` is intentionally left as the free-stream wind direction so that `wind_field.py` upstream-turbine indexing (which uses absolute direction to find which turbines are upstream of which), `yaw_model.py` controller error calculation, `farm_layout.py` direction-aware wake routing, frontend wind rose, and any downstream analysis that relies on absolute geographic direction all keep working without change. The new `WMET_WDirRaw` (REAL32, deg, 0–360, OPC suffix `WMET.Z72PLC__UI_Loc_WMET_Analogue_WDirRaw`) carries the as-measured vane reading so downstream consumers can opt in to the more realistic signal — for instance, IEC 61400-12-2 nacelle-power-performance verification can apply the inverse WVTF to recover free-stream direction, exactly as is done in field measurements; future fault scenarios can simulate "vane miscalibration → systematic yaw misalignment → power loss" by injecting a constant offset on top of WVTF, mirroring a well-known industry failure mode. Pairs with #117 NTF as the second half of the IEC 61400-12-1/2 nacelle-sensor transfer-function chain — `WMET_WSpeedRaw` for the anemometer (axial induction reduces apparent speed), `WMET_WDirRaw` for the vane (rotor swirl shifts apparent direction). 104 SCADA tags total (was 103): +1 raw nacelle wind vane tag (`WMET_WDirRaw`).

Newly implemented:
- Nacelle wind vane transfer function (#119, IEC 61400-12-2 Annex E / Burton, Sharpe, Jenkins, Bossanyi 2011 *Wind Energy Handbook* 2nd ed. §3.7 / Pedersen et al. 2008 Risø-R-1602 / Kragh & Hansen 2014 *J. Sol. Energy Eng.* 136): the SCADA tag `WMET_WDirAbs` previously aliased the free-stream wind direction `wind_direction`, which is what the engine and `yaw_model` use internally for control-error and wake source-direction logic. A real wind vane / yaw misalignment sensor sits on top of the nacelle, downstream of the rotor, and reads a systematic swirl bias from the rotor wake's tangential induction (Euler turbine equation). From the blade-element / momentum-theory tangential induction `a' = C_t / (4·λ)`, the swirl angle at the nacelle position is approximately `θ_swirl ≈ C_t / (2·λ)` rad (Burton et al. 2011). Right-handed rotor (industry standard: clockwise from upwind) → +bias. Operating-state branching: producing or starting with `rotor_speed > 1 RPM` and `λ > 1` applies the swirl bias; otherwise (rotor stopped/parked, no induction, or pre-spin) bias = 0. Final clamp to ±8° keeps the bias inside physically observed bounds (Pedersen et al. 2008 measured 3–8° on real machines). Self-test (10/10 + Ct↑→bias↑ and λ↑→bias↓ monotonicity + clamp): stopped → 0°; starting (Ct=0.55, λ=6) → 2.63°; Region 2 peak Cp (Ct=0.82, λ=7) → 3.36°; Region 2.5 (Ct=0.65, λ=6) → 3.10°; Region 3 pitched-down (Ct=0.30, λ=5) → 1.72°; extreme Ct=0.95, λ=1.5 → +8.00° (clamp); 360°-wrap-around correctness verified (358° + 3.36° → 1.36°). Implementation reuses both `aero_out.ct` (already needed for #117 NTF) and `aero_out.tsr` (already computed in `power_curve.get_power_cp(...)`) so there is zero extra cost and no new RNG mutation. Backwards compatibility: the existing `WMET_WDirAbs` is intentionally left as the free-stream direction so that the frontend wind-rose, the upstream-turbine indexing inside the wake model, and the `yaw_model` control-error logic are all unchanged. The new `WMET_WDirRaw` (REAL32, deg, 0–360, OPC suffix `WMET.Z72PLC__UI_Loc_WMET_Analogue_WDirRaw`) carries the as-measured reading so downstream consumers can opt in to the more realistic signal — for instance, vane-miscalibration / systematic yaw-misalignment failure scenarios (a known field-data fault mode) can now be reproduced as `(WMET_WDirRaw - yaw_angle)` deviating from the expected swirl curve. With #117 NTF for the cup/sonic anemometer this PR completes the IEC 61400-12-1/2 nacelle sensor transfer-function pair: NTF describes "what speed the sensor sees", WVTF describes "what direction the sensor sees". 104 SCADA tags total (was 103): +1 raw nacelle wind vane tag (`WMET_WDirRaw`).

Newly implemented:
- Nacelle wind vane transfer function (#119, IEC 61400-12-2 Annex E / Burton, Sharpe, Jenkins & Bossanyi 2011 *Wind Energy Handbook* 2nd ed. §3.7 / Pedersen et al. 2008 Risø-R-1602 / Kragh & Hansen 2014 *J. Sol. Energy Eng.* 136): completes the IEC 61400-12-1/2 nacelle sensor pair started by #117. The previous SCADA tag `WMET_WDirAbs` aliased the free-stream wind direction, which the model uses internally for the wake-model upstream indexing and `yaw_model.py` control-error computation. A real wind vane mounted alongside the anemometer ~1.5R behind the hub on top of the nacelle reads a systematic swirl bias from rotor wake, because the rotor converts linear inflow into linear+rotational outflow (angular-momentum conservation, Euler turbine equation). The closed-form swirl angle is `θ_s ≈ Ct / (2·λ) [rad]`, equivalent to `2·a'` with the tangential induction `a' = Ct / (4·λ)` from blade-element / momentum theory. Right-handed rotor (industry standard, clockwise viewed from upwind) produces a positive bias on the downstream vane. Implementation reuses `aero_out.ct` and `aero_out.tsr` already computed by `power_curve.get_power_cp(...)` in `step()` so there is zero extra cost and no new RNG mutation. Operating-state branching: `is_producing or is_starting` AND `rotor_speed > 1 RPM` AND `aero_out.tsr > 1.0` applies the swirl bias; otherwise (stopped/parked/cut-out, no rotor swirl) bias = 0°. Final clamp `±8°` matches Pedersen et al. 2008 field measurements (typical bias 3–8° on commercial turbines). 360° wrap-around handled with `% 360.0`. Self-test (8/8 + Ct↑→bias↑ + λ↑→bias↓ monotonicity on a fixed sweep): stopped/cut-out → 0.00°; starting (Ct=0.55, λ=6) → +2.63°; Region 2 peak Cp (Ct=0.82, λ=7) → +3.36°; Region 2.5 transition (Ct=0.65, λ=6) → +3.10°; Region 3 pitching (Ct=0.30, λ=5) → +1.72°; extreme Ct=0.95 / λ=2 clamps at +8.00°; wrap-around 358° + 3.36° → 1.36° verified. Monotonicity Ct↑→bias↑ at fixed λ=6: 0.00 / 0.95 / 1.91 / 2.86 / 3.82 / 4.54° for Ct ∈ {0.0, 0.2, 0.4, 0.6, 0.8, 0.95}. Inverse monotonicity λ↑→bias↓ at fixed Ct=0.82: 7.83 / 4.70 / 3.36 / 2.61 / 2.14° for λ ∈ {3, 5, 7, 9, 11}. Backwards compatibility: existing `WMET_WDirAbs` is intentionally left as the free-stream direction so that the `PerTurbineWind` direction-based wake upstream indexing, `yaw_model.py` control-error computation, the frontend wind rose, the OPC adapter consumers, and any existing analytics scripts are all unchanged. The new `WMET_WDirRaw` (REAL32, °, 0–360, OPC suffix `WMET.Z72PLC__UI_Loc_WMET_Analogue_WDirRaw`) carries the as-measured vane reading so downstream consumers can opt in to the more realistic signal. Downstream applications: IEC 61400-12-2 nacelle power-curve studies (apply the inverse swirl correction to recover the free-stream direction), vane-miscalibration fault simulation (#51 RAG-based diagnostic flow), and the `WMET_WDirRaw − yaw_angle` channel as a vane-observed misalignment metric, mirroring how field engineers diagnose systematic yaw bias. WVTF + NTF together form the complete IEC 61400-12-1/2 nacelle sensor transfer function chain. 104 SCADA tags total (was 103): +1 raw nacelle wind vane tag (`WMET_WDirRaw`).

Newly implemented:
- Atmospheric-stability × turbulence integral length scale L_u coupling (#115, connects #99 × Kaimal AR(1) hub-height wind, parallel to #113, Counihan 1975 *Atmos. Environ.* 9, 871–905 / Kaimal & Finnigan 1994 *Atmospheric Boundary Layer Flows* §1.6 / §3 / Peña & Hahmann 2012 *Wind Energy* 15, 717–731 / IEC 61400-1 ed.4 Annex C): `TurbulenceGenerator.step(...)` (the AR(1) wind-speed generator that drives both the farm base wind and every per-turbine spatial-decorrelation channel) now applies `L_u_eff = 340 · clamp(1 − 0.6·s, 0.4, 2.0)` m on top of the IEC 61400-1 hub-height neutral baseline. Because `τ = L_u / V`, the AR(1) coefficient `α = exp(−dt/τ)` becomes stability-dependent without touching the noise-scaling factor `σ·√(1−α²)`. Mapping at V=10 m/s: s=−1 (stable, suppressed vertical mixing, elongated streamwise eddies) → L_u=544 m, τ≈54 s; s=0 (neutral) → 340 m, 34 s; s=+1 (convective, vigorous overturning, broken-up eddies) → 136 m, 14 s. Validation on a 4000 s sequence at TI=0.10 (warm-up 200 s discarded): lag-30 s observed autocorrelation 0.574 / 0.401 / 0.097 vs analytical exp(−30/τ) = 0.576 / 0.414 / 0.110 — within 1.4 % / 3.1 % / 1.3 % of closed form; steady-state σ_v measured at 0.99 / 0.98 / 0.99 m/s vs expected TI·V = 1.00 m/s — amplitude path is preserved (TI multiplier under #99 still owns it). Backwards compatibility verified: omitting the new `stability` kwarg reproduces the prior behaviour bit-for-bit (diff = 0). The same s ∈ [−1, +1] is forwarded from `engine._run_one_step` to both the farm-wide `_turbulence_gen.step(..., stability=atm_stability)` and from `PerTurbineWind.step(..., atm_stability=...)` to every `_turb_gens[i].step(..., stability=atm_stability)`, so the whole farm shares one ABL timescale (consistent with the physical fact that L_u is set by the boundary layer, not by individual rotors). No new SCADA tag — observable via `WMET_AtmStab × WROT_RotSpd` low-frequency autocorrelation; expected lag-30 s autocorr ≥ 0.4 on stable nights vs ≤ 0.15 in convective afternoons. The persistent low-frequency wind on stable nights should also lift low-frequency content of `WLOD_TwrFaMom` and smooth `WYAW_YwVn1AlgnAvg5s` variability, completing the five-link ABL chain (#99 amplitude → #109 wake k* → #111 veer → #113 wake τ_m → #115 wind τ).

Newly implemented:
- Nacelle wind vane transfer function (#119, IEC 61400-12-2 ed.1 Annex E / Burton, Sharpe, Jenkins, Bossanyi 2011 *Wind Energy Handbook* 2nd ed. §3.7 / Pedersen et al. 2008 Risø-R-1602 / Kragh & Hansen 2014 *J. Sol. Energy Eng.* 136): the SCADA tag `WMET_WDirAbs` previously aliased the free-stream wind direction `wind_direction`, which is what the model uses internally for wake routing and yaw control. A real wind vane mounted on top of the nacelle sits at the same ~1.5R behind-hub position as the cup anemometer (#117), inside the wake of the rotating blades. Conservation of angular momentum (Euler turbine equation) means the rotor extracts axial momentum *and* injects a tangential swirl into the slipstream; the downstream vane therefore reads a wind direction biased by the swirl angle `θ_s ≈ Ct/(2·λ)` rad, derived from `a' = Ct/(4·λ)` (blade element + momentum theory) with the standard `θ_s ≈ 2·a'`. Right-handed rotor (clockwise from upwind, industry standard for modern utility-scale turbines including the Z72 reference) → positive (clockwise) bias on the downstream vane. Operating-state branching: producing or starting with `rotor_speed > 1 RPM` *and* `tsr > 1` applies the swirl correction; otherwise (rotor stopped/parked, no rotation, no swirl) the bias is exactly 0°. The `tsr > 1` guard avoids divide-by-tiny artifacts at very low TSR (cut-in / runaway). Final clamp to `±8°` keeps the bias inside physically observed bounds (Pedersen et al. 2008 measured 3–8° on a 2 MW turbine across operating range). Self-test (11/11 + monotonicity check on Ct and λ sweeps): stopped → 0°; starting (Ct=0.55, λ=6) → +2.63°; Region 2 peak Cp (Ct=0.82, λ=7) → +3.36°; Region 2.5 (Ct=0.65, λ=6) → +3.10°; Region 3 (Ct=0.30, λ=5) → +1.72°; cut-out → 0°; extreme Ct=0.95 / λ=4 → +6.80° within ±8° clamp; very low TSR=0.5 → 0° (clamp guard); 360° wrap-around 358° + 3.36° → 1.36°; Ct↑ → bias↑ (0.819 / 1.637 / 2.456 / 3.274 / 3.888°) and λ↑ → bias↓ (7.83 / 4.70 / 3.36 / 2.61 / 2.14°) both monotonic. Implementation reuses `aero_out.ct` and `aero_out.tsr` already computed by `power_curve.get_power_cp(...)` so there is zero extra cost, no new RNG mutation, and no additional state. Backwards compatibility: the existing `WMET_WDirAbs` is intentionally left as the free-stream direction so that `wind_field.py` upstream-wake indexing, `yaw_model.py` controller error computation (still uses `wind_direction` as the reference for `yaw_error`), the frontend wind-rose, and existing data analysis scripts are all unchanged. The new `WMET_WDirRaw` (REAL32, deg, 0–360, OPC suffix `WMET.Z72PLC__UI_Loc_WMET_Analogue_WDirRaw`) carries the as-measured vane reading so downstream consumers can opt in to the more realistic signal — for instance, IEC 61400-12-2 nacelle-mounted vane studies, or future "vane miscalibration → systematic yaw error" fault scenarios that need a physically-grounded baseline reading. Forms a complete IEC 61400-12-1/2 nacelle-sensor pair with #117 (anemometer NTF) — both reuse the same `aero_out.ct`. 104 SCADA tags total (was 103): +1 raw nacelle vane tag (`WMET_WDirRaw`).

Newly implemented:
- Cup-anemometer overspeeding bias (#127, IEC 61400-12-1 ed.2 §6.3.4 + Annex H / Kristensen 1998 Risø-R-1024 *J. Atmos. Oceanic Technol.* 15, 5–17 / Pedersen et al. 2006 Risø-R-1473 / Westermann 1996 *Wind Engineering* 20): real cup-type anemometers respond faster to gusts than to lulls because the drag torque is asymmetric in `V` (D ∝ V², so a +ΔV gust contributes more torque than a −ΔV lull subtracts). Over averaging windows of 1 s and longer, the mean reading is biased high by `Δ⟨V⟩/⟨V⟩ ≈ k_overspeed · TI²` (Kristensen 1998 closed form; Pedersen 2006 measured k=1.0–2.5 on commercial Risø Class 1 cups). k=1.5 is taken as the heated Risø Class 1 default in this simulator (industry typical >70%); sonic anemometers have k≈0 and therefore zero overspeeding. The bias is applied multiplicatively after the #117/#125 NTF block — `nac_anem_raw *= 1 + 1.5·TI_local²` — where the local TI is the quadrature combine of the per-turbine atmospheric TI (`effective_ti × _local_ti_multiplier`, integrating #99 ABL TI multiplier and #91 pocket multiplier) and the wake-added TI (`_wake_added_ti` from #103 Crespo-Hernández): `TI_local = sqrt((effective_ti·local_mult)² + wake_added_ti²)`. Quadrature is the correct combination because pocket TI and wake-added TI are independent stochastic sources (different physical mechanisms — atmospheric overturning vs rotor wake). Clamp ≤+10% reflects the physical upper bound (cup torque saturates and the bias formula breaks down beyond TI≈0.27). Operating-state branching: `(is_producing or is_starting) and rotor_speed > 1 RPM` applies the bias; stopped/parked rotor has no overspeeding because the cup is not turning (a real cup at rest with airflow simply tilts on its hub bearing without registering). Self-test (19/19 PASS): TI=0.00 → 1.000 (#117 baseline preserved exactly); TI=0.06 (offshore / stable nocturnal) → +0.5% (barely visible in trend charts); TI=0.10 (neutral, IEC reference) → +1.5% (calibration practice subtracts this); TI=0.15 (onshore / convective afternoon) → +3.4% (IEC Annex H typical scale); TI=0.20 (high-TI / strong gusts) → +6.0% (significant); TI=0.25 → +9.4%; TI=0.30 → clamped at +10%; pocket multiplier 1.5×TI=0.10 → +3.4% (matches direct TI=0.15, confirms the multiplier path); pocket multiplier 0.5×TI=0.10 → +0.4% (confirms low-TI case); composite eff=0.10/mult=1.3/wake=0.07 → +3.27% (quadrature combine); monotonicity TI↑ → bias↑ verified across {0.05, 0.10, 0.15, 0.20, 0.25}; bounds [1.00, 1.10] verified across all cases; rotor_speed=0 → bias=1.0 verified (cup not turning); rotor_speed=0.5 → bias=1.0 verified; rotor_speed=1.5 → bias applies. Implementation reuses the existing `effective_ti` from `engine.py:112` (passed through as a new keyword argument to `model.step(...)`) and the per-turbine `_local_ti_multiplier` / `_wake_added_ti` already in `step()` state from #91 / #103, so there is zero extra cost, no new state, no new RNG mutation, and no new SCADA tag. This is the **first time three TI paths (#99 ABL, #91 pocket, #103 wake-added)** couple back into the as-measured sensor reading — previously they only affected the AR(1) wind field and structural loads. Closes the IEC 61400-12-1 mean (Annex D, #117) + Glauert yaw correction (#125) + statistical bias (Annex H, #127) chain for cup-style nacelle anemometers; in field data both the NTF and the overspeeding bias must be inverted to recover the free-stream wind for power-curve analysis. Observable via `WMET_WSpeedRaw / WMET_WSpeedNac × WMET_LocalTi × WMET_WakeTi` correlation: at high TI the ratio should rise above the NTF baseline by 3–6%, at low TI it should sit on the NTF baseline. 104 SCADA tags total (unchanged): no new tag (the bias is folded into the existing `WMET_WSpeedRaw`).

Bug fixes:
- #108: removed duplicate `PerTurbineWind.get_wake_added_ti` definition in `wind_field.py` (F811 lint error introduced by PR merge conflict of #103 and #106; both bodies were identical so the fix is purely cleanup — no behavior change).

Still missing:
- curled-wake model for skewed inflow (yaw-deflection is handled via Bastankhah linear form; curled-wake adds counter-rotating vortex pair detail)

## 3. Not Yet Modeled

These are not implemented yet, or only exist as placeholders/concepts.

### 3.1 Spectral Condition Monitoring Model
Status: **alarm thresholds implemented** (see 2.3)

Implemented:
- ISO 10816-inspired alarm threshold curves (A/B/C/D zones)
- Operating-point-dependent thresholds (scale with rotor speed)
- Per-band alarm levels: 0=normal, 1=warning, 2=alarm
- Hysteresis logic (85% clear ratio, 5s minimum hold time)
- Per-turbine threshold variation (±10%)
- 8 new SCADA tags: WVIB_Alarm1p/3p/Gear/Hf/Bb/Overall + Thresh1pWarn/Alrm

Newly implemented:
- BPFO/BPFI bearing defect frequency computation (4 new SCADA tags)
- gear mesh sideband analysis: GMF, 1st/2nd order sidebands, sideband energy ratio (4 new SCADA tags)

Newly implemented:
- crest factor anomaly alarms (warning > 5.0, alarm > 7.0) with hysteresis
- kurtosis anomaly alarms (warning > 5.0, alarm > 8.0) with hysteresis
- 2 new SCADA tags: WVIB_AlarmCrest, WVIB_AlarmKurt

Still not implemented:
- spectral alarm threshold curves per frequency band (dynamic curves for frontend display)

### 3.2 Advanced Electrical Grid Interaction
Status: **first version implemented** (see 2.5)

Still not implemented:
- full reactive power dispatch curve per grid code
- detailed sub-transient behavior
- protection relay coordination model

### 3.3 Fatigue / Load Modeling
Status: **first version implemented**

Implemented:
- `FatigueModel` class in `simulator/physics/fatigue_model.py`
- tower base fore-aft bending moment (thrust × hub height + turbulence dynamic + SDOF first-mode filter)
- tower SDOF dynamic response: fn≈0.28 Hz, structural+aerodynamic damping, per-turbine ±6% individuality
- tower base side-to-side bending moment (lateral thrust + rotor imbalance)
- blade root flapwise bending moment (thrust distribution + wind shear + pitch)
- blade root edgewise bending moment (gravity 1P cyclic + aero torque)
- rainflow cycle counting (online 3-point method with rolling buffer)
- Damage Equivalent Load (DEL) computation (10-min rolling window)
- cumulative fatigue damage via Miner's rule (S-N curve based)
- per-turbine individuality (stiffness scale offsets and material fatigue ±15%)
- emergency stop transient load amplification (1.8× tower FA)
- 16 SCADA tags (WLOD_ prefix), including 3 alarm/RUL tags
- frontend Load/Fatigue tab with instantaneous loads, DEL, and damage
- fault coupling: blade_icing, pitch_imbalance, yaw_misalignment, bearing_wear, gearbox_overheat
- fatigue alarm thresholds: 4-level alarm (notice ≥0.30, warning ≥0.60, danger ≥0.80, shutdown ≥0.95)
- remaining useful life (RUL) estimation from average damage rate

Newly implemented:
- 3P tower shadow modulation on blade flapwise moment (rotor azimuth-dependent, see #69)
- azimuth-dependent wind shear blade loading: V²-scaled flapwise moment per blade position (see #71)
- blade mass imbalance: per-turbine blade mass offsets (±0.5%), centrifugal force F=Δm×r_cg×ω², coupling to 1P vibration + tower SS moment + blade flapwise (see #72)

Still missing:
- full aeroelastic tower/blade FEM coupling (SDOF first-mode is in place)
- frontend RUL display and alarm level visualization

### 3.4 Event Layer for Historical Analysis
Status: **implemented**

Implemented:
- explicit history event storage in SQLite
- operator, fault, grid, wind, and state events
- automatic trip / transition events from the simulator
- alarm-threshold-crossing fault events
- chart markers on the history page
- event search, filtering, detail panel, and focus windows
- start/end duration support for grid and wind config events
- fault lifecycle tracking with start/end duration events
- event export API (JSON/CSV) with severity grouping
- multi-turbine event comparison view with timeline, summary, and severity badges

### 3.5 Expanded SCADA Tag Set
Not yet implemented:
- deeper protection tags
- deeper cooling loop tags
- more converter internal tags
- more service / maintenance state tags

## 4. Suggested Next Priorities

### Priority A: Event Visibility
Current first version:
- done

Recommended next:
- add duration tracking for more event classes
- add event export and correlation tools

Why:
- the existing physical behavior is already much stronger than before,
- and the event layer now makes trend changes explainable,
- but cross-turbine and lifecycle analysis are still limited.

### Priority B: Wind Event Realism
Status: **done**

Implemented:
- gust front propagation with time delay
- ramp propagation across turbines
- direction shift propagation
- farm layout model with direction-aware wake

### Priority C: Electrical Response Detail
Status: **done**

Implemented:
- frequency-watt droop response with deadband
- reactive power / power factor / apparent power
- LVRT/HVRT ride-through curves with band accumulation
- synthetic inertia response
- converter operating mode tracking

### Priority D: Vibration Feature Upgrade
Status: **done**

Implemented:
- fault-specific vibration signatures for all 11 fault scenarios
- 5 frequency-band outputs (1P/3P/gear-mesh/HF/broadband)
- crest factor and kurtosis condition indicators
- X and Y direction separation

## 5. Quick Summary

### Already Strong
- startup / shutdown realism
- thermal behavior
- grid-event response
- turbine individuality
- SCADA signal realism
- aerodynamic Cp surface and thrust
- multi-stage drivetrain with gearbox
- active cooling system with fouling
- electrical response (frequency-watt, reactive power, ride-through)
- spectral vibration bands with fault-specific signatures
- vibration alarm thresholds with ISO 10816-inspired zones
- fatigue / load modeling (tower + blade moments, DEL, Miner's damage, alarm thresholds, RUL, tower SDOF dynamics)
- 104 SCADA tags (electrical + vibration + structural load + alarm/RUL + bearing diagnostics + gear mesh sidebands + crest/kurtosis alarms + gearbox oil temp + tooth wear + outside humidity + local TI multiplier + Bastankhah wake deficit + wake meander offset + yaw-induced wake deflection + atmospheric stability + shear α + air density + wake-added TI + ambient pressure + raw nacelle anemometer + raw nacelle wind vane)

### Still Weak
- spectral alarm threshold curves — see #58 (crest factor/kurtosis anomaly alarms now completed)
- full protection relay coordination (LVRT/OVRT)
- aeroelastic coupling (BEM; tower first-mode SDOF is implemented)
- frontend RUL visualization — see #57 (alarm event integration completed)
- full blade element loading distribution (tower shadow 3P + wind shear 1P + wind veer implemented, full BEM missing)
- ~~blade mass imbalance and rotor dynamic imbalance~~ → done (#72, centrifugal force ω² coupling)
- ~~gearbox oil temperature and viscosity effects~~ → done (#73, Walther equation)
- ~~coolant level / leak detection~~ → done (#75, level tracking + pump cavitation + fault coupling)
- ~~wind veer (directional shear with height)~~ → done (#79, Ekman spiral + blade lateral force coupling)
- ~~gear tooth contact modeling~~ → done (#76, time-varying mesh stiffness + tooth wear index + GMF coupling)

### Recommended Immediate Direction
1. ~~blade mass imbalance with speed² coupling for 1P vibration~~ → done (#72)
2. ~~gearbox oil temperature/viscosity model~~ → done (#73)
2b. ~~coolant level / leak detection~~ → done (#75)
3. frontend RUL display and alarm level visualization (see #57)
4. spectral alarm threshold curves per frequency band (see #58)
5. ~~spectral sideband analysis (harmonics/fault signatures)~~ → done (#58, GMF sideband model)
6. ~~detailed bearing defect frequency computation (BPFO/BPFI)~~ → done (#58, geometry-based)
7. ~~tower dynamic natural frequency response~~ → done (#62, SDOF first-mode filter)
8. ~~tower shadow effect~~ → done (#69, rotor azimuth tracking + 3P Gaussian shadow model)
9. ~~wind shear profile~~ → done (#71, power-law V(h) with azimuth-dependent blade loading)
10. ~~wind veer (directional shear with height)~~ → done (#79, Ekman spiral model)
11. ~~gear tooth contact modeling~~ → done (#76, contact-ratio mesh stiffness + tooth wear)
12. ~~localized turbulence pockets~~ → done (#91, Gaussian spatial TI boost pockets)
13. ~~Bastankhah-Porté-Agel Gaussian wake model~~ → done (#93, TI-dependent expansion + Ct-coupled deficit + sum-of-squares)
14. ~~dynamic wake meandering (Larsen DWM)~~ → done (#95, AR(1) lateral wake centerline with σ_θ=0.3·TI, τ=25 s)
15. ~~yaw-induced wake deflection / wake steering (Bastankhah 2016)~~ → done (#97, θ_c initial skew + δ_y(x)=tan(θ_c)·x, `WMET_WakeDefl`)
16. ~~atmospheric stability / diurnal shear-TI coupling~~ → done (#99, s ∈ [−1, +1] → α, TI_mult, `WMET_ShearAlpha`, `WMET_AtmStab`)
17. ~~air density coupling~~ → done (#101, moist-air ρ(T,RH) → PowerCurveModel per step, `WMET_AirDensity`)
18. ~~wake-added turbulence intensity (Crespo-Hernández)~~ → done (#103, TI_w = 0.73·a^0.8325·TI_∞^0.0325·(x/D)^-0.32, shared Bastankhah σ, Frandsen quadrature, AR(1) σ_v uplift, `WMET_WakeTi`)
19. ~~dynamic atmospheric pressure P(t) coupling~~ → done (#106, `_pressure_state → P = 101325 + s·1500 Pa`, passed through `get_air_density(ts, ..., pressure_pa=...)`, adds ±1.5% ρ swing from synoptic fronts, `WMET_AmbPressure`)
20. ~~atmospheric-stability × Bastankhah k\* coupling~~ → done (#109, `k* = k_neutral · clamp(1 + 0.30·s, 0.55, 1.45)`, stable +34 % deficit @ 6 D / convective −22 %, no new tag)
21. ~~atmospheric-stability × wind-veer coupling~~ → done (#111, `veer_rate_eff = veer_base · clamp(1 − s, 0.3, 2.5)`, stable ~0.20 °/m / convective ~0.03 °/m, +37 % / −26 % TwrSS, no new tag)
22. ~~atmospheric-stability × wake-meander τ_m coupling~~ → done (#113, `τ_m_eff = 25 · clamp(1 − 0.6·s, 0.4, 2.0)` s, stable 40 s / neutral 25 s / convective 10 s, lag-25 s autocorr 0.45 vs 0.01, no new tag)
23. ~~atmospheric-stability × turbulence integral length scale L_u coupling~~ → done (#115, `L_u_eff = 340 · clamp(1 − 0.6·s, 0.4, 2.0)` m, stable 544 m / neutral 340 m / convective 136 m, lag-30 s autocorr 0.57 vs 0.10 @ 10 m/s, σ_v amplitude unchanged, no new tag)
24. ~~nacelle anemometer transfer function (NTF, IEC 61400-12-1 Annex D)~~ → done (#117, `V_raw = V_∞·(1 − 0.55·a)`, Region 2 → 0.84·V_∞ / Region 3 → 0.96·V_∞ / stopped → 1.04·V_∞, `WMET_WSpeedRaw`)
25. ~~nacelle wind vane transfer function (WVTF, IEC 61400-12-2 Annex E)~~ → done (#119, `θ_s ≈ Ct/(2·λ)`, Region 2 → +3.36° / Region 3 → +1.72° / stopped → 0°, clamp ±8°, `WMET_WDirRaw`)
26. ~~Glauert yaw skewed-flow correction on NTF + WVTF~~ → done (#125, `a_skew = a·cos²(γ)` for NTF, `θ_s_eff = θ_s·cos(γ)` for WVTF, γ clamped ±45°; closes IEC 61400-12-1/2 chain under yaw misalignment; γ=0 baseline preserved exactly; γ=15° → NTF ratio 0.933×, WVTF ratio 0.966×; γ=30° → 0.75× / 0.866×; γ=45° → 0.50× / 0.707×; reuses `yaw_out["yaw_error"]` already in step()`, no extra cost, no new SCADA tag)
27. ~~cup-anemometer overspeeding bias (IEC 61400-12-1 Annex H)~~ → done (#127, `bias = 1 + 1.5·TI_local²` with `TI_local = sqrt((effective_ti·local_mult)² + wake_added_ti²)`, clamp ≤+10%; TI=0.10 → +1.5% / TI=0.15 → +3.4% / TI=0.20 → +6.0% / TI≥0.27 → clamped +10%; closes IEC 61400-12-1 mean (Annex D) + Glauert (#125) + statistical (Annex H) chain; first TI-coupling into sensor reading; no new SCADA tag)
28. deployment hardening (JWT auth, RBAC, Docker Compose)

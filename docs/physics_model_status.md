# Physics Model Status

Last updated: 2026-04-24 (atmospheric-stability × wake-expansion coupling, #109; F811 dedup, #108)

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
- wind veer (directional shear with height): linear Ekman spiral model, per-turbine veer rate (0.07–0.13 °/m), azimuth-dependent blade direction offset, lateral force coupling to tower SS and blade flapwise moments (see #79)

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
- 102 SCADA tags (electrical + vibration + structural load + alarm/RUL + bearing diagnostics + gear mesh sidebands + crest/kurtosis alarms + gearbox oil temp + tooth wear + outside humidity + local TI multiplier + Bastankhah wake deficit + wake meander offset + yaw-induced wake deflection + atmospheric stability + shear α + air density + wake-added TI + ambient pressure)

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
20. deployment hardening (JWT auth, RBAC, Docker Compose)
18. ~~wake-added turbulence intensity (Crespo-Hernández)~~ → done (#103, IEC 61400-1 Annex E, sum-of-squares per source × Bastankhah Gaussian envelope, `WMET_WakeTi`)
19. deployment hardening (JWT auth, RBAC, Docker Compose)

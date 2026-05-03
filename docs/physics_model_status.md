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

Newly implemented (詳述見 changelog.md):
- (#71) wind shear profile — 詳細紀錄見 [`docs/changelog.md` §PR-71](changelog.md#pr-71)
- (#79) wind veer — 詳細紀錄見 [`docs/changelog.md` §PR-79](changelog.md#pr-79)
- (#91) localized turbulence pockets — 詳細紀錄見 [`docs/changelog.md` §PR-91](changelog.md#pr-91)
- (#93) Bastankhah-Porté-Agel Gaussian wake model — 詳細紀錄見 [`docs/changelog.md` §PR-93](changelog.md#pr-93)
- (#95) Dynamic wake meandering — 詳細紀錄見 [`docs/changelog.md` §PR-95](changelog.md#pr-95)
- (#97) Yaw-induced wake deflection / wake steering — 詳細紀錄見 [`docs/changelog.md` §PR-97](changelog.md#pr-97)
- (#99) Atmospheric stability / diurnal shear-TI coupling — 詳細紀錄見 [`docs/changelog.md` §PR-99](changelog.md#pr-99)
- (#101) Air density coupling — 詳細紀錄見 [`docs/changelog.md` §PR-101](changelog.md#pr-101)
- (#103) Wake-added turbulence intensity — 詳細紀錄見 [`docs/changelog.md` §PR-103](changelog.md#pr-103)
- (#106) Dynamic atmospheric pressure coupling — 詳細紀錄見 [`docs/changelog.md` §PR-106](changelog.md#pr-106)
- (#109) Atmospheric-stability × wake-expansion coupling — 詳細紀錄見 [`docs/changelog.md` §PR-109](changelog.md#pr-109)
- (#111) Atmospheric-stability × wind-veer coupling — 詳細紀錄見 [`docs/changelog.md` §PR-111](changelog.md#pr-111)
- (#113) Atmospheric-stability × wake-meander τ_m coupling — 詳細紀錄見 [`docs/changelog.md` §PR-113](changelog.md#pr-113)
- (#117) Nacelle anemometer transfer function — 詳細紀錄見 [`docs/changelog.md` §PR-117](changelog.md#pr-117)
- (#119) Nacelle wind vane transfer function — 詳細紀錄見 [`docs/changelog.md` §PR-119](changelog.md#pr-119)
- (#115) Atmospheric-stability × turbulence integral length scale L_u coupling — 詳細紀錄見 [`docs/changelog.md` §PR-115](changelog.md#pr-115)
- (#127) Cup-anemometer overspeeding bias — 詳細紀錄見 [`docs/changelog.md` §PR-127](changelog.md#pr-127)
Bug fixes:
- (#108) bug fix: removed duplicate `get_wake_added_ti` definition — 詳細紀錄見 [`docs/changelog.md` §PR-108](changelog.md#pr-108)
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

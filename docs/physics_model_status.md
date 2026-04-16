# Physics Model Status

Last updated: 2026-04-16

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

Still missing:
- full BEM (blade element momentum) method
- detailed blade aerodynamic loading distribution
- tower shadow effect

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

Still missing:
- gear tooth contact modeling
- oil temperature / viscosity effects

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

Still missing:
- coolant level / leak detection
- detailed radiator fin model
- ambient humidity effect on air cooling

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

Still missing:
- localized turbulence pockets
- terrain-dependent wind shear
- more sophisticated wake model (e.g. Frandsen, Bastankhah)

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
- 90 SCADA tags (electrical + vibration + structural load + alarm/RUL + bearing diagnostics + gear mesh sidebands + crest/kurtosis alarms)

### Still Weak
- spectral alarm threshold curves — see #58 (crest factor/kurtosis anomaly alarms now completed)
- full protection relay coordination (LVRT/OVRT)
- aeroelastic coupling (BEM; tower first-mode SDOF is implemented)
- frontend RUL visualization — see #57 (alarm event integration completed)

### Recommended Immediate Direction
1. frontend RUL display and alarm level visualization (see #57)
2. spectral alarm threshold curves per frequency band (see #58)
3. ~~spectral sideband analysis (harmonics/fault signatures)~~ → done (#58, GMF sideband model)
4. ~~detailed bearing defect frequency computation (BPFO/BPFI)~~ → done (#58, geometry-based)
5. ~~tower dynamic natural frequency response~~ → done (#62, SDOF first-mode filter)
5. deployment hardening (JWT auth, RBAC, Docker Compose)

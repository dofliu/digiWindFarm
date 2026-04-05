# Physics Model Status

Last updated: 2026-04-05

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
- blended output (70% Cp-based + 30% lookup) for stability

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
- detailed bearing defect frequency computation

### 2.3 Vibration Feature Detail
Current state:
- trend-level vibration behavior is implemented
- HSS and LSS torsional vibration now contribute separately

Missing detail:
- frequency-band features
- bearing defect signatures
- sideband behavior
- fault-specific vibration fingerprints beyond amplitude changes

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

### 2.5 Electrical / Converter Detail
Current state:
- voltage, current, frequency, derate, sync, and trip logic are implemented

Missing detail:
- reactive power
- power factor
- converter control modes
- protection coordination detail
- grid-code style ride-through curves

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
Not yet implemented:
- FFT-like band outputs
- 1P/3P amplitude tracking by band
- bearing fault band signatures
- spectral alarm features

### 3.2 Advanced Electrical Grid Interaction
Not yet implemented:
- reactive power dispatch
- voltage support control
- LVRT / HVRT curve logic by turbine type
- frequency-watt response
- synthetic inertia response

### 3.3 Advanced Fatigue / Load Modeling
Not yet implemented:
- tower load
- blade root load
- fatigue accumulation
- DEL-style damage metrics

### 3.4 Event Layer for Historical Analysis
Status: first usable version implemented

Implemented:
- explicit history event storage in SQLite
- operator, fault, grid, wind, and state events
- automatic trip / transition events from the simulator
- alarm-threshold-crossing fault events
- chart markers on the history page
- event search, filtering, detail panel, and focus windows
- start/end duration support for grid and wind config events

Still missing:
- start/end duration for full fault lifecycle events
- richer event export
- stronger multi-turbine event correlation tools

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
Recommended next:
- gust front
- ramp propagation
- direction shift propagation

Why:
- this will improve farm-wide realism without destabilizing the current turbine models.

### Priority C: Electrical Response Detail
Recommended next:
- frequency-watt response
- reactive power / power factor
- more detailed sync / ride-through logic

Why:
- the grid model already exists, so this is a natural extension.

### Priority D: Vibration Feature Upgrade
Recommended next:
- fault-specific signatures
- basic frequency-band outputs

Why:
- this would make diagnostics and AI explanation features significantly stronger.

## 5. Quick Summary

### Already Strong
- startup / shutdown realism
- thermal behavior
- grid-event response
- turbine individuality
- SCADA signal realism
- aerodynamic Cp surface and thrust (new)
- multi-stage drivetrain with gearbox (new)
- active cooling system with fouling (new)

### Still Weak
- spectral vibration realism
- detailed electrical control behavior
- farm-event visualization / wind propagation

### Recommended Immediate Direction
1. wind-event propagation realism
2. electrical response refinement
3. vibration feature upgrade
4. event lifecycle and multi-turbine analysis

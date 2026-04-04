# Project Overview

## Project Name

digiWindTurbine: Wind Farm Monitoring and Digital Twin Platform

## Purpose

This project provides a practical wind farm digital twin for:
- realtime SCADA-style monitoring
- realistic turbine behavior simulation
- fault injection and diagnostics workflows
- grid-event and wind-event response analysis
- integration testing through REST, WebSocket, and Modbus TCP

It is designed as both:
- a product prototype for wind farm monitoring workflows
- and a simulation sandbox for improving physics realism over time

## Current Product Direction

The current focus is not maintenance workflow first.
The current focus is:
- making the generated turbine data look more like real machine behavior
- making startup, stop, grid events, and faults produce believable trends
- making history data explorable and explainable from the frontend

This means the most important development track is the physics and signal realism track.

## System Architecture

```text
Wind / Grid / Fault Inputs
  -> Physics Engine
  -> DataBroker
  -> FastAPI Backend
  -> SQLite History + WebSocket + REST
  -> React Frontend
  -> Modbus TCP Simulator
```

### Main Runtime Layers

#### 1. Environment Layer
Files:
- `wind_model.py`
- `simulator/grid_model.py`
- `simulator/physics/wind_field.py`

Responsibilities:
- base wind profiles
- turbulence
- wake and per-turbine wind variation
- grid frequency and voltage conditions

#### 2. Turbine Physics Layer
Files:
- `simulator/physics/turbine_physics.py`
- `simulator/physics/power_curve.py`
- `simulator/physics/thermal_model.py`
- `simulator/physics/vibration_model.py`
- `simulator/physics/yaw_model.py`
- `simulator/physics/fault_engine.py`

Responsibilities:
- turbine operating state machine
- power and rotor-speed behavior
- drivetrain and brake transient behavior
- temperatures and cooling behavior
- vibration response
- yaw behavior
- fault-to-physics coupling
- sensor realism

#### 3. Platform Layer
Files:
- `server/`
- `simulator/engine.py`
- `server/data_broker.py`
- `server/storage.py`

Responsibilities:
- API delivery
- realtime streaming
- history storage
- history event storage
- export
- Modbus register updates

#### 4. Frontend Layer
Files:
- `frontend/App.tsx`
- `frontend/components/`
- `frontend/hooks/`

Responsibilities:
- dashboard and turbine detail
- history browsing
- event browsing and event-focused analysis
- fault injection
- wind and grid control
- operator commands

## Current Physics Scope

The current implemented model already includes:

### Implemented
- staged turbine startup
- synchronization before production
- normal stop and emergency stop
- curtailment and operator control
- Region 2 / Region 3 power behavior
- rotor and generator speed separation
- drivetrain twist and brake torque first version
- 10-point thermal system with residual heat
- vibration trend model
- yaw model with delay and deadband
- turbulence and wake first version
- fault progression and trip behavior
- sensor noise, drift, stuck values, and quantization
- grid-event response with per-turbine differences

### Still Weak
- advanced aerodynamics
- spectral vibration behavior
- detailed electrical control response
- advanced cooling loop behavior
- farm-wide wind-event propagation

Detailed tracking lives in:
- `docs/physics_model_status.md`

## Data Model Philosophy

The simulation is not only generating final display values.
The current design aims to:
- model physical causes first
- let SCADA tags emerge from those internal states
- avoid direct fake offsets whenever possible

Examples:
- faults should affect heat, vibration, control, cooling, or alignment first
- startup should consume time and pass through states
- emergency stop should differ from normal stop in speed, vibration, and thermal behavior
- different turbines should not behave identically under the same farm condition

## Interface Surfaces

### REST
Used for:
- current turbine data
- history queries
- history event queries
- settings
- grid and wind control
- fault injection
- operator control
- export

### WebSocket
Used for:
- realtime turbine updates

### Modbus TCP
Used for:
- industrial integration testing
- exposing simulated registers that mirror SCADA behavior

## Storage Strategy

Current storage:
- SQLite for history persistence
- SQLite for history event persistence
- in-memory buffers for short-term trend access

Current limitation:
- history growth is unbounded

This means a future retention or cleanup strategy is still required.

## Recommended Near-Term Roadmap

### 1. Event Explainability
Current first version is done:
- explicit event storage for fault, grid, operator, wind, and state events
- event markers in history charts
- event detail panel and focus windows

Recommended next:
- fault lifecycle start/end durations
- event export
- multi-turbine event comparison

### 2. Wind Event Realism
Improve farm behavior with:
- gust front propagation
- direction-shift propagation
- ramp propagation

### 3. Electrical Response Detail
Improve:
- frequency-watt response
- reactive power / power factor
- ride-through curves
- converter behavior detail

### 4. Vibration Feature Upgrade
Improve:
- fault-specific signatures
- banded vibration outputs
- diagnostics-oriented condition indicators

## Product Gaps Outside Physics

Still pending:
- maintenance work order backend
- authentication and deployment hardening
- history cleanup policy
- stronger historical event analysis tools

## Document Roles

Use the documents in this way:
- `README.md`: entry point and current feature summary
- `TODO.md`: roadmap and pending work
- `docs/physics_model_status.md`: physics completion tracking
- `project.md`: architecture and product direction

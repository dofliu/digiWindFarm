# Project Notes

## Current Position

This repository is no longer only an early concept.
It already contains a working wind farm simulation platform with:
- backend APIs
- realtime streaming
- history storage
- physics-based turbine simulation
- fault injection
- grid and wind controls
- Modbus TCP simulation
- frontend dashboard, detail, settings, and history views

## Current Development Priority

The main priority is physics realism and signal realism.

Primary focus:
- startup / stop realism
- thermal realism
- drivetrain realism
- grid-event response
- turbine individuality
- historical analysis usability

Secondary focus:
- maintenance workflow
- deployment hardening

## Current Gaps

Still pending or incomplete:
- maintenance work order backend
- history retention / cleanup
- advanced aerodynamics
- spectral vibration modeling
- deeper electrical control behavior
- historical event visualization expansion

## Source of Truth

Use these files for planning:
- `README.md`
- `TODO.md`
- `docs/physics_model_status.md`
- `project.md`

## Working Principle

When making simulation changes:
- prefer changing physical causes over directly offsetting output tags
- prefer persistent per-turbine differences over random noise-only variation
- prefer time-dependent transitions over instant jumps
- keep new work observable in history charts whenever possible

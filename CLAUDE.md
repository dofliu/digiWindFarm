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
- deployment hardening (JWT, RBAC, HTTPS) — see #26
- sideband vibration detail and spectral alarm thresholds — see #58
- full protection relay coordination
- SQLite vs time-series DB architecture decision — see #24
- dependency security vulnerabilities (cryptography, pyjwt, etc.) — see #48
- no automated test suite (pytest) — see #52
- external data API documentation — see #50
- RAG-based alert analysis — see #51
- frontend RUL visualization — see #57 (fatigue alarm event integration completed)

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

# TODO / Development Roadmap

## Tracking Docs

- Physics model status:
  - `docs/physics_model_status.md`

## Completed

### Simulation / Physics
- [x] 40 SCADA tags aligned with Bachmann Z72 definitions
- [x] Turbine main state machine with staged startup / sync / production / stop
- [x] Normal stop and emergency stop behavior
- [x] Power curve and rotor speed model
- [x] Drivetrain slip / shaft twist / brake torque first version
- [x] 10-point thermal model with heat inertia
- [x] Vibration model
- [x] Yaw model
- [x] Turbulence + per-turbine wind variation + simple wake
- [x] Fault injection with 7 scenarios
- [x] Fault-to-physics coupling
- [x] Per-turbine individuality model
- [x] Sensor noise / drift / stuck / quantization
- [x] Grid frequency / voltage model
- [x] Per-turbine grid derate / trip / reconnect difference

### Backend
- [x] FastAPI REST APIs
- [x] WebSocket realtime stream
- [x] SQLite history persistence
- [x] SQLite history event persistence
- [x] Modbus TCP simulator
- [x] Wind profile control
- [x] Turbine spec presets
- [x] Grid control API
- [x] Control API: start / stop / reset / service / emergency stop / curtail

### Frontend
- [x] Dashboard and turbine detail views
- [x] Trend chart panel
- [x] Fault injection UI
- [x] Wind and turbine settings UI
- [x] Grid control UI
- [x] History data page
- [x] Event markers, filters, search, details, and focus windows in History
- [x] CSV export entry

## In Progress Quality Level

These parts are implemented, but still first-generation models:
- [x] Aerodynamics: Cp(λ,β) surface, thrust coefficient, dynamic stall
- [x] Drivetrain: multi-stage gearbox, bearing separation, torsional modes, brake dynamics
- [x] Cooling system: pump/fan state, coolant flow/pressure, fouling propagation
- [ ] Vibration feature / frequency-band realism
- [ ] Advanced converter / electrical control detail
- [ ] Wind-event propagation across the farm

## Next Priorities

### Priority A: Event Visibility
- [x] Store grid events as explicit history events
- [x] Store operator actions as explicit history events
- [x] Store fault events as explicit history events
- [x] Store automatic state / trip events
- [x] Show event markers in history charts
- [x] Add event filters, search, detail panel, and focus windows
- [x] Add start/end duration for grid and wind config events

### Priority A.1: Event Layer Upgrade
- [ ] Add start/end duration for fault lifecycle events
- [ ] Add event export as JSON / CSV
- [ ] Add event severity grouping / alarm-level badges
- [ ] Add multi-turbine event comparison view

### Priority B: Wind Event Realism
- [ ] Gust front propagation
- [ ] Ramp propagation across turbines
- [ ] Direction-shift propagation
- [ ] Stronger time-space coupling in farm wind model

### Priority C: Electrical Response Detail
- [ ] Frequency-watt response
- [ ] Reactive power / power factor
- [ ] Improved grid-code style ride-through behavior
- [ ] Converter control mode detail

### Priority D: Vibration Upgrade
- [ ] Fault-specific vibration signatures
- [ ] Frequency-band outputs
- [ ] Bearing defect style indicators

## Product / Platform Gaps

### History and Storage
- [ ] Add retention / cleanup policy for SQLite history
- [ ] Add clearer history query filters and limits
- [ ] Add richer event query filters on the backend
- [ ] Decide whether long-term storage should stay on SQLite or move to time-series DB

### Maintenance
- [ ] Work order backend schema
- [ ] Work order CRUD API
- [ ] Connect `MaintenanceHub` to real backend instead of mock data

### Deployment
- [ ] JWT authentication
- [ ] Basic RBAC
- [ ] `.env` cleanup
- [ ] Docker Compose
- [ ] Reverse proxy / HTTPS

## Notes

- `README.md` and this roadmap now reflect the actual implemented state.
- Physics-specific status should be maintained in `docs/physics_model_status.md`.

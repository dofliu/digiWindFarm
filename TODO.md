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
- [x] Cp(λ,β) aerodynamic surface model with thrust coefficient and dynamic stall
- [x] Multi-stage drivetrain: gearbox stages, bearing separation, torsional modes, brake dynamics
- [x] Cooling system: pump/fan state, coolant flow/pressure, fouling propagation
- [x] Wind event propagation: gust front, ramp, direction shift across farm
- [x] Farm layout with turbine positions and direction-aware wake model
- [x] Fault physics path unified — all 11 scenarios through physical causes with load coupling
- [x] Electrical response model: frequency-watt droop, reactive power, power factor, LVRT/HVRT ride-through, synthetic inertia, converter modes
- [x] Spectral vibration model: 1P/3P/gear-mesh/HF/broadband bands with fault-specific signatures, crest factor, kurtosis
- [x] Fatigue/load model: tower/blade bending moments, rainflow cycle counting, DEL, Miner's damage
- [x] 72 SCADA tags total (was 59): +13 structural load/fatigue tags

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
- [x] Event export API (JSON/CSV) with severity grouping
- [x] Fault lifecycle event tracking (start/end/phase transitions)
- [x] History retention / downsampling / cleanup policy

### Frontend
- [x] Dashboard and turbine detail views
- [x] Trend chart panel
- [x] Fault injection UI
- [x] Wind and turbine settings UI
- [x] Grid control UI
- [x] History data page
- [x] Event markers, filters, search, details, and focus windows in History
- [x] CSV export entry
- [x] Dashboard default to summary view
- [x] Turbine detail compact layout: metrics bar + side-by-side subsystem/trend
- [x] Multi-turbine event comparison view with timeline, summary, and severity badges

## In Progress Quality Level

These parts are implemented, but still first-generation models:
- [x] Aerodynamics: Cp(λ,β) surface, thrust coefficient, dynamic stall
- [x] Drivetrain: multi-stage gearbox, bearing separation, torsional modes, brake dynamics
- [x] Cooling system: pump/fan state, coolant flow/pressure, fouling propagation
- [x] Wind-event propagation across the farm
- [x] Fault physics unified path with operating-condition coupling
- [x] Vibration feature / frequency-band realism
- [x] Advanced converter / electrical control detail

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
- [x] Add start/end duration for fault lifecycle events
- [x] Add event export as JSON / CSV
- [x] Add event severity grouping / alarm-level badges
- [x] Add multi-turbine event comparison view

### Priority B: Wind Event Realism
- [x] Gust front propagation
- [x] Ramp propagation across turbines
- [x] Direction-shift propagation
- [x] Stronger time-space coupling in farm wind model

### Priority C: Electrical Response Detail
- [x] Frequency-watt response
- [x] Reactive power / power factor
- [x] Improved grid-code style ride-through behavior
- [x] Converter control mode detail

### Priority D: Vibration Upgrade
- [x] Fault-specific vibration signatures
- [x] Frequency-band outputs
- [x] Bearing defect style indicators

### Priority E: Fatigue / Load Modeling
- [x] Tower base bending moments (fore-aft, side-to-side)
- [x] Blade root bending moments (flapwise, edgewise)
- [x] Rainflow cycle counting
- [x] Damage Equivalent Load (DEL) computation
- [x] Cumulative fatigue damage (Miner's rule)
- [x] Frontend load/fatigue tab
- [x] History trend chart preset for load data

## Product / Platform Gaps

### History and Storage
- [x] Add retention / cleanup policy for SQLite history
- [x] Add clearer history query filters and limits
- [x] Add richer event query filters on the backend
- [ ] Decide whether long-term storage should stay on SQLite or move to time-series DB

### Maintenance
- [x] Work order backend schema
- [x] Work order CRUD API
- [x] Technician management API
- [x] Connect `MaintenanceHub` to real backend instead of mock data

### Deployment
- [ ] JWT authentication
- [ ] Basic RBAC
- [x] `.env` cleanup (configurable DB_PATH, Docker env vars)
- [x] Docker Compose (backend + frontend + nginx reverse proxy)
- [ ] Reverse proxy / HTTPS (standalone, Docker uses nginx internally)

## Notes

- `README.md` and this roadmap now reflect the actual implemented state.
- Physics-specific status should be maintained in `docs/physics_model_status.md`.

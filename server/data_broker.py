import sys
import os
import threading
import time as _time
from datetime import datetime
from typing import List, Optional, Dict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from server.models import (
    TurbineReading, TurbineStatus, DataSourceMode,
    DataSourceConfig, SimulationConfig, FarmStatus,
)
from server.storage import Storage
from simulator.engine import WindFarmSimulator


def _map_state(state: str) -> TurbineStatus:
    mapping = {
        "RUNNING": TurbineStatus.OPERATING,
        "STARTING": TurbineStatus.OPERATING,
        "IDLE": TurbineStatus.IDLE,
        "STOPPING": TurbineStatus.IDLE,
        "FAULT": TurbineStatus.FAULT,
    }
    return mapping.get(state, TurbineStatus.OFFLINE)


def _sim_output_to_reading(output: Dict, history_points: Optional[List[Dict]] = None,
                            fault_info: Optional[List[Dict]] = None) -> TurbineReading:
    """Convert simulator output dict to TurbineReading model (39 SCADA tags)."""
    scada = output.get('scada', {})
    rotor = output.get('rotor', {})
    gen = output.get('generator', {})
    gb = output.get('gearbox', {})
    yaw = output.get('yaw', {})
    hyd = output.get('hydraulic', {})

    power_w = output.get('total_power', gen.get('power', 0))
    power_mw = power_w / 1_000_000

    tid = output.get('turbine_id', 'WT001')
    idx = int(tid.replace('WT', '')) if tid.startswith('WT') else 1
    name = f"WTG-{idx:02d}"

    ts = output.get('timestamp')
    if isinstance(ts, str):
        try:
            ts = datetime.fromisoformat(ts)
        except ValueError:
            ts = datetime.now()
    elif ts is None:
        ts = datetime.now()

    # Build mini history for frontend chart
    history = None
    if history_points:
        history = []
        for h in history_points[-30:]:
            hp = h.get('total_power', h.get('generator', {}).get('power', 0))
            ht = h.get('timestamp')
            if isinstance(ht, str):
                try:
                    ht_dt = datetime.fromisoformat(ht)
                    ht_ms = int(ht_dt.timestamp() * 1000)
                except ValueError:
                    ht_ms = 0
            else:
                ht_ms = int(ht.timestamp() * 1000) if isinstance(ht, datetime) else 0
            history.append({"time": ht_ms, "power": round(hp / 1_000_000, 2)})

    # Determine turbine status — check if any fault has tripped
    op_state = output.get('operational_state', 'IDLE')
    status = _map_state(op_state)
    if fault_info:
        for f in fault_info:
            if f.get('tripped'):
                status = TurbineStatus.FAULT

    tur_state = int(scada.get("WTUR_TurSt", 6)) if scada else 6

    return TurbineReading(
        turbineId=tid,
        name=name,
        timestamp=ts,
        status=status,
        turState=tur_state,

        # ── Original fields (backward-compatible) ──
        windSpeed=round(output.get('wind_speed', 0), 2),
        powerOutput=round(power_mw, 2),
        rotorSpeed=round(scada.get("WROT_RotSpd", rotor.get('rotor_speed', 0)), 3),
        bladeAngle=round(scada.get("WROT_PtAngValBl1", output.get('pitch_angle', 0)), 2),
        temperature=round(scada.get("WGEN_GnStaTmp1", gen.get('temperature', 45)), 2),
        vibration=round(scada.get("WNAC_VibMsNacXDir", gb.get('vibration', 0)), 3),
        voltage=round(scada.get("WGEN_GnVtgMs", gen.get('voltage', 690)), 2),
        current=round(scada.get("WGEN_GnCurMs", gen.get('current', 0)), 2),
        yawAngle=round(scada.get("WYAW_YwVn1AlgnAvg5s", yaw.get('yaw_angle', 0)), 2),
        gearboxTemp=round(scada.get("WNAC_NacTmp", gb.get('temperature', 40)), 2),
        frequency=scada.get("WCNV_CnvGnFrq", gen.get('frequency')),
        hydraulicPressure=scada.get("WYAW_YwBrkHyPrs", hyd.get('pressure')),
        history=history,

        # ── WGEN expanded ──
        genPower=scada.get("WGEN_GnPwrMs"),
        genSpeed=scada.get("WGEN_GnSpd"),
        genStatorTemp1=scada.get("WGEN_GnStaTmp1"),
        genAirTemp1=scada.get("WGEN_GnAirTmp1"),
        genBearingTemp1=scada.get("WGEN_GnBrgTmp1"),

        # ── WROT expanded ──
        bladeAngle1=scada.get("WROT_PtAngValBl1"),
        bladeAngle2=scada.get("WROT_PtAngValBl2"),
        bladeAngle3=scada.get("WROT_PtAngValBl3"),
        rotorTemp=scada.get("WROT_RotTmp"),
        hubCabinetTemp=scada.get("WROT_RotCabTmp"),
        rotorLocked=int(scada.get("WROT_RotLckd", 0)) if scada.get("WROT_RotLckd") is not None else None,
        brakeActive=int(scada.get("WROT_SrvcBrkAct", 0)) if scada.get("WROT_SrvcBrkAct") is not None else None,

        # ── WCNV ──
        cnvCabinetTemp=scada.get("WCNV_CnvCabinTmp"),
        cnvDcVoltage=scada.get("WCNV_CnvDClVtg"),
        cnvGridPower=scada.get("WCNV_CnvGdPwrAt"),
        cnvGenFreq=scada.get("WCNV_CnvGnFrq"),
        cnvGenPower=scada.get("WCNV_CnvGnPwr"),
        igctWaterCond=scada.get("WCNV_IGCTWtrCond"),
        igctWaterPres1=scada.get("WCNV_IGCTWtrPres1"),
        igctWaterPres2=scada.get("WCNV_IGCTWtrPres2"),
        igctWaterTemp=scada.get("WCNV_IGCTWtrTmp"),

        # ── WGDC ──
        transformerTemp=scada.get("WGDC_TrfCoreTmp"),

        # ── WMET ──
        windDirection=scada.get("WMET_WDirAbs"),
        outsideTemp=scada.get("WMET_TmpOutside"),

        # ── WNAC ──
        nacelleTemp=scada.get("WNAC_NacTmp"),
        nacelleCabTemp=scada.get("WNAC_NacCabTmp"),
        vibrationX=scada.get("WNAC_VibMsNacXDir"),
        vibrationY=scada.get("WNAC_VibMsNacYDir"),

        # ── WYAW ──
        yawError=scada.get("WYAW_YwVn1AlgnAvg5s"),
        yawBrakePressure=scada.get("WYAW_YwBrkHyPrs"),
        cableWindup=scada.get("WYAW_CabWup"),

        # ── WCNV — Electrical Response ──
        reactivePower=scada.get("WCNV_ReactPwr"),
        powerFactor=scada.get("WCNV_PwrFactor"),
        apparentPower=scada.get("WCNV_AppPwr"),
        freqWattDerate=scada.get("WCNV_FreqWattDerate"),
        inertiaPower=scada.get("WCNV_InertiaPwr"),
        converterMode=int(scada.get("WCNV_CnvMode", 0)) if scada.get("WCNV_CnvMode") is not None else None,
        rideThroughBand=int(scada.get("WCNV_RtBand", 0)) if scada.get("WCNV_RtBand") is not None else None,

        # ── WVIB — Vibration Spectral Bands ──
        vibBand1pX=scada.get("WVIB_Band1pX"),
        vibBand1pY=scada.get("WVIB_Band1pY"),
        vibBand3pX=scada.get("WVIB_Band3pX"),
        vibBand3pY=scada.get("WVIB_Band3pY"),
        vibBandGearX=scada.get("WVIB_BandGearX"),
        vibBandGearY=scada.get("WVIB_BandGearY"),
        vibBandHfX=scada.get("WVIB_BandHfX"),
        vibBandHfY=scada.get("WVIB_BandHfY"),
        vibBandBbX=scada.get("WVIB_BandBbX"),
        vibBandBbY=scada.get("WVIB_BandBbY"),
        vibCrestFactor=scada.get("WVIB_CrestFactor"),
        vibKurtosis=scada.get("WVIB_Kurtosis"),

        # ── WLOD — Structural Load & Fatigue ──
        towerFaMoment=scada.get("WLOD_TwrFaMom"),
        towerSsMoment=scada.get("WLOD_TwrSsMom"),
        bladeFlapMoment=scada.get("WLOD_BldFlapMom"),
        bladeEdgeMoment=scada.get("WLOD_BldEdgeMom"),
        delTowerFa=scada.get("WLOD_DelTwrFa"),
        delTowerSs=scada.get("WLOD_DelTwrSs"),
        delBladeFlap=scada.get("WLOD_DelBldFlap"),
        delBladeEdge=scada.get("WLOD_DelBldEdge"),
        damageTowerFa=scada.get("WLOD_DmgTwrFa"),
        damageTowerSs=scada.get("WLOD_DmgTwrSs"),
        damageBladeFlap=scada.get("WLOD_DmgBldFlap"),
        damageBladeEdge=scada.get("WLOD_DmgBldEdge"),
        productionHours=scada.get("WLOD_ProdHours"),

        # ── Fault info ──
        activeFaults=fault_info,

        # ── Raw SCADA dict ──
        scadaTags=scada if scada else None,
    )


class DataBroker:
    """Unified data interface for simulation and real OPC data.

    Storage strategy:
      - Simulator runs at 1Hz, in-memory buffer keeps 1 hour
      - SQLite writes throttled to every 10 seconds (configurable)
      - Events trigger 1s snapshot capture (±10 min around event)
      - Background task does downsampling and cleanup
    """

    # Default: write to SQLite every N seconds
    WRITE_INTERVAL_S = 10
    # Raw data retention (days)
    RAW_RETENTION_DAYS = 3
    # 1-min aggregate retention (days)
    AGG_1M_RETENTION_DAYS = 90
    # Snapshot window: seconds of 1s data to capture before/after event
    SNAPSHOT_WINDOW_S = 600  # 10 minutes

    def __init__(self):
        self.mode = DataSourceMode.SIMULATION
        self.storage = Storage()
        self.simulator: Optional[WindFarmSimulator] = None
        self._sim_config = SimulationConfig()
        self._last_tur_state: Dict[str, int] = {}
        self._last_shutdown_cause: Dict[str, Optional[str]] = {}
        self._last_fault_trip: Dict[str, bool] = {}
        self._last_fault_alarm_keys: Dict[str, set[str]] = {}
        # Fault lifecycle tracking: {turbine_id: {scenario_id: phase}}
        self._last_fault_phases: Dict[str, Dict[str, str]] = {}
        # Track active fault scenario keys for lifecycle start/end
        self._active_fault_keys: Dict[str, set] = {}  # {turbine_id: {scenario_id, ...}}
        # Fatigue alarm level tracking: {turbine_id: (tower_level, blade_level)}
        self._last_fatigue_alarm: Dict[str, tuple] = {}
        # Session tracking
        self._session_id: Optional[int] = None
        # Write throttle state
        self._last_write_time: float = 0
        # Snapshot state: when an event occurs, capture 1s data for a window
        self._snapshot_active: Dict[str, float] = {}  # turbine_id -> end_time
        self._snapshot_event_ref: Dict[str, str] = {}
        # Background maintenance thread
        self._maintenance_thread: Optional[threading.Thread] = None
        self._maintenance_running = False

    def start(self, config: Optional[DataSourceConfig] = None,
              sim_config: Optional[SimulationConfig] = None):
        """Start the data broker in simulation or OPC mode and launch background maintenance."""
        if sim_config:
            self._sim_config = sim_config
        if config:
            self.mode = config.mode

        if self.mode == DataSourceMode.SIMULATION:
            self._start_simulator()
        else:
            self._start_opc(config)

        # Start background maintenance (downsampling + cleanup)
        self._start_maintenance()

    def _start_simulator(self):
        if self.simulator and self.simulator.is_running:
            self.simulator.stop()

        # End previous session if any
        if self._session_id is not None:
            self.storage.end_session(self._session_id)

        self._last_tur_state.clear()
        self._last_shutdown_cause.clear()
        self._last_fault_trip.clear()
        self._last_fault_alarm_keys.clear()
        self._last_fault_phases.clear()
        self._active_fault_keys.clear()
        self._last_fatigue_alarm.clear()

        self.simulator = WindFarmSimulator(
            turbine_count=self._sim_config.turbineCount,
            base_wind_speed=self._sim_config.baseWindSpeed,
            turbulence_intensity=self._sim_config.turbulenceIntensity,
        )

        # Create a new session
        self._session_id = self.storage.create_session(
            data_source="simulation",
            turbine_count=self._sim_config.turbineCount,
            rated_power_kw=2000,  # Z72-2000-MV default
            model_name="Z72-2000-MV",
            config={
                "baseWindSpeed": self._sim_config.baseWindSpeed,
                "turbulenceIntensity": self._sim_config.turbulenceIntensity,
                "timeStep": self._sim_config.timeStep,
            },
        )
        print(f"[DataBroker] Created session #{self._session_id}")

        # Register data callback (throttled writes)
        self.simulator.on_data(self._on_sim_data)
        self.simulator.start(time_step=self._sim_config.timeStep)

    def _start_opc(self, config: Optional[DataSourceConfig]):
        # OPC DA adapter - lazy import to avoid dependency issues
        try:
            from server.opc_adapter import OPCDAAdapter
            self._opc_adapter = OPCDAAdapter(config)
            self._opc_adapter.on_data(self._on_opc_data)
            self._opc_adapter.start()
        except ImportError:
            print("[DataBroker] OPC adapter not available, falling back to simulation")
            self.mode = DataSourceMode.SIMULATION
            self._start_simulator()

    def _on_sim_data(self, readings: List[Dict]):
        """Callback from simulator — called every 1s.

        - Always checks for events (state changes, faults)
        - Writes to SQLite only every WRITE_INTERVAL_S seconds
        - If a snapshot is active for a turbine, writes 1s data to snapshots table
        """
        now = _time.time()
        self._detect_sim_events(readings)

        # Check if any turbine has an active snapshot window
        for reading in readings:
            tid = reading.get('turbine_id', '')
            snap_end = self._snapshot_active.get(tid)
            if snap_end and now < snap_end:
                event_ref = self._snapshot_event_ref.get(tid, '')
                self.storage.store_snapshot(reading, event_ref, self._session_id)
            elif snap_end and now >= snap_end:
                del self._snapshot_active[tid]
                del self._snapshot_event_ref[tid]

        # Throttled regular writes
        if now - self._last_write_time >= self.WRITE_INTERVAL_S:
            self._last_write_time = now
            self.storage.store_readings(readings, self._session_id)

    def _trigger_snapshot(self, turbine_id: str, event_ref: str):
        """Activate 1s snapshot capture for a turbine around an event.

        Also retroactively saves recent in-memory history as snapshot data.
        """
        now = _time.time()
        self._snapshot_active[turbine_id] = now + self.SNAPSHOT_WINDOW_S
        self._snapshot_event_ref[turbine_id] = event_ref

        # Retroactively save recent history from in-memory buffer
        if self.simulator:
            recent = self.simulator.get_history(turbine_id, limit=self.SNAPSHOT_WINDOW_S)
            if recent:
                self.storage.store_snapshots(recent, event_ref, self._session_id)

    def _on_opc_data(self, readings: List[Dict]):
        """Callback from OPC adapter — uses same throttled write."""
        now = _time.time()
        if now - self._last_write_time >= self.WRITE_INTERVAL_S:
            self._last_write_time = now
            self.storage.store_readings(readings, self._session_id)

    def stop(self):
        """Stop the active data source, end the current session, and halt maintenance."""
        self._stop_maintenance()
        if self.simulator and self.simulator.is_running:
            self.simulator.stop()
        if self._session_id is not None:
            self.storage.end_session(self._session_id)
            self._session_id = None

    def switch_mode(self, config: DataSourceConfig,
                    sim_config: Optional[SimulationConfig] = None):
        """Switch between simulation and OPC data source modes."""
        self.stop()
        self.mode = config.mode
        self.start(config, sim_config)

    # ── Background maintenance ──

    def _start_maintenance(self):
        """Start background thread for downsampling and cleanup."""
        if self._maintenance_running:
            return
        self._maintenance_running = True
        self._maintenance_thread = threading.Thread(
            target=self._maintenance_loop, daemon=True, name="storage-maintenance"
        )
        self._maintenance_thread.start()

    def _stop_maintenance(self):
        self._maintenance_running = False
        if self._maintenance_thread:
            self._maintenance_thread.join(timeout=5)
            self._maintenance_thread = None

    def _maintenance_loop(self):
        """Run downsampling every 5 minutes, cleanup every hour."""
        last_cleanup = 0
        while self._maintenance_running:
            _time.sleep(300)  # 5 minutes
            if not self._maintenance_running:
                break
            try:
                self.storage.run_downsampling()
                now = _time.time()
                if now - last_cleanup > 3600:  # hourly
                    self.storage.run_cleanup(
                        raw_retention_days=self.RAW_RETENTION_DAYS,
                        agg_1m_retention_days=self.AGG_1M_RETENTION_DAYS,
                    )
                    last_cleanup = now
            except Exception as e:
                print(f"[DataBroker] Maintenance error: {e}")

    def get_all_turbines(self) -> List[TurbineReading]:
        """Return current readings for all turbines, sorted by turbine ID."""
        if self.mode == DataSourceMode.SIMULATION and self.simulator:
            current = self.simulator.get_current_data()
            fault_status = self.simulator.fault_engine.get_fault_status()
            result = []
            for tid, output in current.items():
                hist = self.simulator.get_history(tid, limit=30)
                tid_faults = [f for f in fault_status if f['turbine_id'] == tid]
                result.append(_sim_output_to_reading(output, hist, tid_faults or None))
            return sorted(result, key=lambda r: r.turbineId)
        return []

    def get_turbine(self, turbine_id: str) -> Optional[TurbineReading]:
        """Return the current reading for a single turbine, or None if not found."""
        if self.mode == DataSourceMode.SIMULATION and self.simulator:
            output = self.simulator.get_turbine_data(turbine_id)
            if output:
                hist = self.simulator.get_history(turbine_id, limit=30)
                fault_status = self.simulator.fault_engine.get_fault_status()
                tid_faults = [f for f in fault_status if f['turbine_id'] == turbine_id]
                return _sim_output_to_reading(output, hist, tid_faults or None)
        return None

    def get_history(self, turbine_id: str, start: Optional[str] = None,
                    end: Optional[str] = None, limit: int = 1000) -> List[dict]:
        """Query stored SCADA history for a turbine within an optional time range."""
        return self.storage.query_history(turbine_id, start, end, limit)

    def get_history_events(self, turbine_id: Optional[str] = None, start: Optional[str] = None,
                           end: Optional[str] = None, limit: int = 500) -> List[dict]:
        """Query stored history events (faults, grid, operator actions) with optional filters."""
        return self.storage.query_events(turbine_id, start, end, limit)

    def record_event(self, event_type: str, source: str, title: str,
                     turbine_id: Optional[str] = None, detail: Optional[str] = None,
                     payload: Optional[Dict] = None, end_timestamp: Optional[str] = None):
        """Persist a history event (fault, grid change, operator action, etc.) to storage."""
        self.storage.record_event(
            event_type=event_type,
            source=source,
            title=title,
            turbine_id=turbine_id,
            detail=detail,
            payload=payload,
            end_timestamp=end_timestamp,
        )

    def close_open_events(self, event_type: str, source: Optional[str] = None,
                          turbine_id: Optional[str] = None, closed_at: Optional[str] = None):
        """Close open-ended events by setting their end timestamp."""
        self.storage.close_open_events(
            event_type=event_type,
            source=source,
            turbine_id=turbine_id,
            closed_at=closed_at,
        )

    def _detect_sim_events(self, readings: List[Dict]):
        if not self.simulator:
            return

        fault_status = self.simulator.fault_engine.get_fault_status()
        fault_by_turbine = {
            tid: [f for f in fault_status if f.get("turbine_id") == tid]
            for tid in self.simulator.turbines.keys()
        }

        for reading in readings:
            turbine_id = reading.get("turbine_id")
            if not turbine_id:
                continue

            scada = reading.get("scada", {})
            current_state = int(scada.get("WTUR_TurSt", 0) or 0)
            last_state = self._last_tur_state.get(turbine_id)
            model = self.simulator.turbines.get(turbine_id)
            control = model.get_control_status() if model else {}
            shutdown_cause = control.get("shutdown_cause")
            last_cause = self._last_shutdown_cause.get(turbine_id)

            if last_state is None:
                self._last_tur_state[turbine_id] = current_state
                self._last_shutdown_cause[turbine_id] = shutdown_cause
            elif last_state != current_state:
                self._record_state_transition_event(
                    turbine_id=turbine_id,
                    previous_state=last_state,
                    current_state=current_state,
                    shutdown_cause=shutdown_cause,
                )
                self._last_tur_state[turbine_id] = current_state
                self._last_shutdown_cause[turbine_id] = shutdown_cause
            elif shutdown_cause != last_cause:
                self._last_shutdown_cause[turbine_id] = shutdown_cause

            active_faults = fault_by_turbine.get(turbine_id, [])
            current_tripped = any(bool(f.get("tripped")) for f in active_faults)
            last_tripped = self._last_fault_trip.get(turbine_id)
            if last_tripped is None:
                self._last_fault_trip[turbine_id] = current_tripped
            elif last_tripped != current_tripped:
                if current_tripped:
                    tripped_faults = [f.get("scenario_id") for f in active_faults if f.get("tripped")]
                    event_ref = f"fault_trip:{turbine_id}:{datetime.now().isoformat()}"
                    self.record_event(
                        event_type="fault",
                        source="simulator",
                        title="Automatic fault trip",
                        turbine_id=turbine_id,
                        detail=f"Trip triggered by {', '.join(tripped_faults) if tripped_faults else 'active fault'}",
                        payload={"turbineId": turbine_id, "faults": tripped_faults},
                    )
                    # Trigger high-frequency snapshot capture
                    self._trigger_snapshot(turbine_id, event_ref)
                else:
                    self.record_event(
                        event_type="fault",
                        source="simulator",
                        title="Fault trip cleared in simulator",
                        turbine_id=turbine_id,
                        detail=f"{turbine_id} no longer has a tripped fault state",
                        payload={"turbineId": turbine_id},
                    )
                self._last_fault_trip[turbine_id] = current_tripped

            current_alarm_keys = set()
            last_alarm_keys = self._last_fault_alarm_keys.get(turbine_id, set())
            for fault in active_faults:
                scenario_id = str(fault.get("scenario_id") or "")
                phase = str(fault.get("phase") or "")
                severity = fault.get("severity")
                for alarm in fault.get("active_alarms") or []:
                    alarm_type = str(alarm.get("type") or "")
                    alarm_code = str(alarm.get("code") or "")
                    alarm_key = f"{scenario_id}:{alarm_type}:{alarm_code}"
                    current_alarm_keys.add(alarm_key)
                    if alarm_key not in last_alarm_keys:
                        self.record_event(
                            event_type="fault",
                            source="simulator",
                            title=f"Fault alarm threshold reached: {scenario_id}",
                            turbine_id=turbine_id,
                            detail=f"{scenario_id} entered {phase} with alarm {alarm_type}{alarm_code and f' {alarm_code}'} at severity {severity}",
                            payload={
                                "turbineId": turbine_id,
                                "scenarioId": scenario_id,
                                "phase": phase,
                                "severity": severity,
                                "alarm": alarm,
                            },
                        )
            self._last_fault_alarm_keys[turbine_id] = current_alarm_keys

            # ── Fault lifecycle: track start/end + phase transitions ──
            current_fault_keys = set()
            current_phases: Dict[str, str] = {}
            for fault in active_faults:
                sid = str(fault.get("scenario_id") or "")
                phase = str(fault.get("phase") or "")
                current_fault_keys.add(sid)
                current_phases[sid] = phase

            prev_keys = self._active_fault_keys.get(turbine_id, set())
            prev_phases = self._last_fault_phases.get(turbine_id, {})

            # New faults → lifecycle start event (open-ended)
            for sid in current_fault_keys - prev_keys:
                phase = current_phases.get(sid, "incipient")
                sev = next((f.get("severity", 0) for f in active_faults
                            if f.get("scenario_id") == sid), 0)
                self.record_event(
                    event_type="fault_lifecycle",
                    source="simulator",
                    title=f"Fault started: {sid}",
                    turbine_id=turbine_id,
                    detail=f"{sid} entered {phase} phase on {turbine_id}",
                    payload={
                        "turbineId": turbine_id,
                        "scenarioId": sid,
                        "phase": phase,
                        "severity": sev,
                        "lifecycle": "start",
                    },
                )

            # Removed faults → close lifecycle event
            for sid in prev_keys - current_fault_keys:
                self.storage.close_open_events(
                    event_type="fault_lifecycle",
                    source="simulator",
                    turbine_id=turbine_id,
                )
                self.record_event(
                    event_type="fault_lifecycle",
                    source="simulator",
                    title=f"Fault ended: {sid}",
                    turbine_id=turbine_id,
                    detail=f"{sid} cleared on {turbine_id}",
                    payload={
                        "turbineId": turbine_id,
                        "scenarioId": sid,
                        "lifecycle": "end",
                    },
                )

            # Phase transitions for ongoing faults
            for sid in current_fault_keys & prev_keys:
                old_phase = prev_phases.get(sid)
                new_phase = current_phases.get(sid)
                if old_phase and new_phase and old_phase != new_phase:
                    sev = next((f.get("severity", 0) for f in active_faults
                                if f.get("scenario_id") == sid), 0)
                    self.record_event(
                        event_type="fault_lifecycle",
                        source="simulator",
                        title=f"Fault phase change: {sid}",
                        turbine_id=turbine_id,
                        detail=f"{sid} transitioned from {old_phase} to {new_phase}",
                        payload={
                            "turbineId": turbine_id,
                            "scenarioId": sid,
                            "fromPhase": old_phase,
                            "toPhase": new_phase,
                            "severity": sev,
                            "lifecycle": "phase_change",
                        },
                    )

            self._active_fault_keys[turbine_id] = current_fault_keys
            self._last_fault_phases[turbine_id] = current_phases

            # ── Fatigue alarm level changes ──
            alm_twr = int(scada.get("WLOD_AlmTwr", 0) or 0)
            alm_bld = int(scada.get("WLOD_AlmBld", 0) or 0)
            prev_alm = self._last_fatigue_alarm.get(turbine_id)
            if prev_alm is None:
                self._last_fatigue_alarm[turbine_id] = (alm_twr, alm_bld)
            else:
                prev_twr, prev_bld = prev_alm
                alarm_names = {0: "正常", 1: "注意", 2: "警告", 3: "危險", 4: "停機"}
                for label, prev_lvl, cur_lvl in [
                    ("塔架", prev_twr, alm_twr),
                    ("葉片", prev_bld, alm_bld),
                ]:
                    if cur_lvl != prev_lvl and cur_lvl > 0:
                        direction = "升級" if cur_lvl > prev_lvl else "降級"
                        rul = scada.get("WLOD_RulHours", -1)
                        self.record_event(
                            event_type="fatigue",
                            source="simulator",
                            title=f"疲勞警報{direction}：{label} Lv{cur_lvl} ({alarm_names.get(cur_lvl, '')})",
                            turbine_id=turbine_id,
                            detail=f"{turbine_id} {label}疲勞警報從 Lv{prev_lvl} {direction}至 Lv{cur_lvl}，RUL={rul}h",
                            payload={
                                "turbineId": turbine_id,
                                "component": label,
                                "fromLevel": prev_lvl,
                                "toLevel": cur_lvl,
                                "levelName": alarm_names.get(cur_lvl, ""),
                                "rulHours": rul,
                            },
                        )
                self._last_fatigue_alarm[turbine_id] = (alm_twr, alm_bld)

    def _record_state_transition_event(self, turbine_id: str, previous_state: int,
                                       current_state: int, shutdown_cause: Optional[str]):
        state_name = self._state_name(current_state)
        detail = f"{turbine_id} moved from {self._state_name(previous_state)} to {state_name}"
        payload = {
            "turbineId": turbine_id,
            "fromState": previous_state,
            "toState": current_state,
            "shutdownCause": shutdown_cause,
        }

        if current_state == 6:
            self.record_event(
                event_type="state",
                source="simulator",
                title="Entered production",
                turbine_id=turbine_id,
                detail=detail,
                payload=payload,
            )
            return

        if current_state in (7, 9):
            event_type = "state"
            title = "Turbine stopping"
            if shutdown_cause in ("grid_trip", "grid_protection"):
                event_type = "grid"
                title = "Automatic grid protection stop"
            elif isinstance(shutdown_cause, str) and shutdown_cause.startswith("fault:"):
                event_type = "fault"
                title = f"Automatic fault stop: {shutdown_cause.split(':', 1)[1]}"
            elif shutdown_cause in ("operator", "operator_emergency", "service"):
                event_type = "operator"
                title = "Operator-driven stop"

            # Trigger snapshot for emergency stops and fault-caused stops
            if current_state == 7 or (isinstance(shutdown_cause, str) and
                                       ("fault" in shutdown_cause or "grid" in shutdown_cause or "emergency" in shutdown_cause)):
                event_ref = f"stop:{turbine_id}:{current_state}:{datetime.now().isoformat()}"
                self._trigger_snapshot(turbine_id, event_ref)

            self.record_event(
                event_type=event_type,
                source="simulator",
                title=title,
                turbine_id=turbine_id,
                detail=f"{detail} ({shutdown_cause or 'unknown cause'})",
                payload=payload,
            )
            return

        if current_state in (4, 5, 8):
            self.record_event(
                event_type="state",
                source="simulator",
                title="Startup / restart transition",
                turbine_id=turbine_id,
                detail=detail,
                payload=payload,
            )
            return

        if current_state in (1, 2, 3):
            self.record_event(
                event_type="state",
                source="simulator",
                title="Returned to idle state",
                turbine_id=turbine_id,
                detail=detail,
                payload=payload,
            )

    @staticmethod
    def _state_name(state: int) -> str:
        return {
            1: "Shutdown",
            2: "Standby",
            3: "Wait Restart",
            4: "Pre-Production",
            5: "Synchronization",
            6: "Production",
            7: "Emergency Stop",
            8: "Restart",
            9: "Normal Stop",
        }.get(state, f"State {state}")

    def get_farm_status(self) -> FarmStatus:
        """Aggregate current turbine states into a farm-level status summary."""
        turbines = self.get_all_turbines()
        now = datetime.now()
        if not turbines:
            return FarmStatus(
                totalTurbines=0, operatingCount=0, idleCount=0,
                faultCount=0, offlineCount=0, totalPowerMW=0,
                avgWindSpeed=0, timestamp=now,
            )
        return FarmStatus(
            totalTurbines=len(turbines),
            operatingCount=sum(1 for t in turbines if t.status == TurbineStatus.OPERATING),
            idleCount=sum(1 for t in turbines if t.status == TurbineStatus.IDLE),
            faultCount=sum(1 for t in turbines if t.status == TurbineStatus.FAULT),
            offlineCount=sum(1 for t in turbines if t.status == TurbineStatus.OFFLINE),
            totalPowerMW=round(sum(t.powerOutput for t in turbines), 2),
            avgWindSpeed=round(sum(t.windSpeed for t in turbines) / len(turbines), 2),
            timestamp=now,
        )

    @property
    def turbine_ids(self) -> List[str]:
        """List of active turbine IDs from the running simulator."""
        if self.simulator:
            return self.simulator.turbine_ids
        return []

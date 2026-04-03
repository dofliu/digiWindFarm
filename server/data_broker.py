import sys
import os
from datetime import datetime
from typing import List, Optional, Dict
from collections import deque

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


def _sim_output_to_reading(output: Dict, history_points: Optional[List[Dict]] = None) -> TurbineReading:
    """Convert simulator output dict to TurbineReading model."""
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

    return TurbineReading(
        turbineId=tid,
        name=name,
        timestamp=ts,
        status=_map_state(output.get('operational_state', 'IDLE')),
        windSpeed=round(output.get('wind_speed', 0), 2),
        powerOutput=round(power_mw, 2),
        rotorSpeed=round(rotor.get('rotor_speed', 0), 2),
        bladeAngle=round(output.get('pitch_angle', 0), 2),
        temperature=round(gen.get('temperature', 45), 2),
        vibration=round(gb.get('vibration', 0), 2),
        voltage=round(gen.get('voltage', 690), 2),
        current=round(gen.get('current', 0), 2),
        yawAngle=round(yaw.get('yaw_angle', 0), 2),
        gearboxTemp=round(gb.get('temperature', 40), 2),
        frequency=gen.get('frequency'),
        hydraulicPressure=hyd.get('pressure'),
        history=history,
    )


class DataBroker:
    """Unified data interface for simulation and real OPC data."""

    def __init__(self):
        self.mode = DataSourceMode.SIMULATION
        self.storage = Storage()
        self.simulator: Optional[WindFarmSimulator] = None
        self._sim_config = SimulationConfig()

    def start(self, config: Optional[DataSourceConfig] = None,
              sim_config: Optional[SimulationConfig] = None):
        if sim_config:
            self._sim_config = sim_config
        if config:
            self.mode = config.mode

        if self.mode == DataSourceMode.SIMULATION:
            self._start_simulator()
        else:
            self._start_opc(config)

    def _start_simulator(self):
        if self.simulator and self.simulator.is_running:
            self.simulator.stop()

        self.simulator = WindFarmSimulator(
            turbine_count=self._sim_config.turbineCount,
            base_wind_speed=self._sim_config.baseWindSpeed,
            turbulence_intensity=self._sim_config.turbulenceIntensity,
        )
        # Store every reading to SQLite
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
        """Callback from simulator."""
        self.storage.store_readings(readings)

    def _on_opc_data(self, readings: List[Dict]):
        """Callback from OPC adapter."""
        self.storage.store_readings(readings)

    def stop(self):
        if self.simulator and self.simulator.is_running:
            self.simulator.stop()

    def switch_mode(self, config: DataSourceConfig,
                    sim_config: Optional[SimulationConfig] = None):
        self.stop()
        self.mode = config.mode
        self.start(config, sim_config)

    def get_all_turbines(self) -> List[TurbineReading]:
        if self.mode == DataSourceMode.SIMULATION and self.simulator:
            current = self.simulator.get_current_data()
            result = []
            for tid, output in current.items():
                hist = self.simulator.get_history(tid, limit=30)
                result.append(_sim_output_to_reading(output, hist))
            return sorted(result, key=lambda r: r.turbineId)
        return []

    def get_turbine(self, turbine_id: str) -> Optional[TurbineReading]:
        if self.mode == DataSourceMode.SIMULATION and self.simulator:
            output = self.simulator.get_turbine_data(turbine_id)
            if output:
                hist = self.simulator.get_history(turbine_id, limit=30)
                return _sim_output_to_reading(output, hist)
        return None

    def get_history(self, turbine_id: str, start: Optional[str] = None,
                    end: Optional[str] = None, limit: int = 1000) -> List[dict]:
        return self.storage.query_history(turbine_id, start, end, limit)

    def get_farm_status(self) -> FarmStatus:
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
        if self.simulator:
            return self.simulator.turbine_ids
        return []

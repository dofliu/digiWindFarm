import sys
import os
import time
import threading
from datetime import datetime
from typing import Dict, List, Callable, Optional
from collections import deque

# Add parent directory so we can import original modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from wind_model import WindEnvironmentModel
from simulator.grid_model import GridEnvironmentModel
from simulator.physics import TurbinePhysicsModel, FaultEngine
from simulator.physics.wind_field import TurbulenceGenerator, PerTurbineWind
from simulator.modbus_server import ModbusSimServer


class WindFarmSimulator:
    """Wind farm simulator engine — produces realistic SCADA data via callbacks.

    Uses the independent physics model (simulator/physics/) for each turbine,
    plus a shared FaultEngine for fault injection across the farm.
    Optionally exposes data via Modbus TCP server.
    """

    def __init__(self, turbine_count: int = 14, base_wind_speed: float = 10.0,
                 turbulence_intensity: float = 0.1):
        self.wind_model = WindEnvironmentModel()
        self.grid_model = GridEnvironmentModel()
        self.wind_model.turbulence_intensity = turbulence_intensity
        self.turbines: Dict[str, TurbinePhysicsModel] = {}
        self.latest_data: Dict[str, Dict] = {}
        self.history: Dict[str, deque] = {}
        self.history_maxlen = 3600  # ~1 hour at 1Hz

        self.fault_engine = FaultEngine()
        self.modbus_server: Optional[ModbusSimServer] = None

        # Per-turbine wind variation and turbulence
        self._turbulence_gen = TurbulenceGenerator(seed=42)
        self._per_turbine_wind = PerTurbineWind(turbine_count, seed=99)

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._callbacks: List[Callable] = []
        self._lock = threading.Lock()

        # Initialize turbines
        for i in range(1, turbine_count + 1):
            tid = f"WT{i:03d}"
            self.add_turbine(tid, seed=i)

    def add_turbine(self, turbine_id: str, seed: Optional[int] = None):
        self.turbines[turbine_id] = TurbinePhysicsModel(seed=seed)
        self.latest_data[turbine_id] = {}
        self.history[turbine_id] = deque(maxlen=self.history_maxlen)

    def on_data(self, callback: Callable[[List[Dict]], None]):
        """Register a callback that receives a list of turbine readings each step."""
        self._callbacks.append(callback)

    def start(self, time_step: float = 1.0):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._loop, args=(time_step,), daemon=True
        )
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

    def _loop(self, time_step: float):
        while self._running:
            try:
                now = datetime.now()
                base_wind = self.wind_model.get_wind_speed(now)
                wind_direction = self.wind_model.get_wind_direction(now)
                ambient_temp = self.wind_model.get_ambient_temp(now)
                grid_frequency = self.grid_model.get_frequency(now)
                grid_voltage = self.grid_model.get_voltage(now)

                # Add autocorrelated turbulence
                turb_component = self._turbulence_gen.step(
                    base_wind, self.wind_model.turbulence_intensity, time_step
                )
                farm_wind = max(0, base_wind + turb_component)

                # Advance fault engine
                fault_modifiers = self.fault_engine.step(dt=time_step)

                readings = []
                for tid, model in self.turbines.items():
                    # Per-turbine wind variation (wake effect + spatial decorrelation)
                    idx = int(tid[2:]) - 1
                    local_wind = self._per_turbine_wind.get_local_wind(farm_wind, idx)

                    # Apply fault modifiers for this turbine
                    model.fault_modifiers = fault_modifiers.get(tid, {})
                    model.active_faults = [
                        {
                            "scenario_id": fault.scenario_id,
                            "severity": fault.severity,
                            "tripped": fault.tripped,
                        }
                        for fault in self.fault_engine.active_faults
                        if fault.turbine_id == tid
                    ]

                    # Check if fault engine tripped this turbine
                    for fault in self.fault_engine.active_faults:
                        if fault.turbine_id == tid and fault.tripped:
                            model.cmd_emergency_stop(cause=f"fault:{fault.scenario_id}")

                    # Run physics step
                    scada_output = model.step(
                        local_wind,
                        wind_direction,
                        ambient_temp,
                        time_step,
                        grid_frequency_ref=grid_frequency,
                        grid_voltage_ref=grid_voltage,
                    )

                    # Build output dict (compatible with data_broker expectations)
                    output = self._scada_to_output(tid, now, scada_output, local_wind, wind_direction)

                    with self._lock:
                        self.latest_data[tid] = output
                        self.history[tid].append(output)

                    readings.append(output)

                    # Update Modbus registers
                    if self.modbus_server and self.modbus_server.is_running:
                        self.modbus_server.update_turbine(tid, scada_output)

                for cb in self._callbacks:
                    try:
                        cb(readings)
                    except Exception:
                        pass

                time.sleep(time_step)
            except Exception as e:
                print(f"[Simulator] Error: {e}")
                time.sleep(1)

    @staticmethod
    def _scada_to_output(tid: str, timestamp: datetime,
                         scada: Dict[str, float],
                         wind_speed: float, wind_direction: float) -> Dict:
        """Convert flat SCADA dict to the nested output format expected by data_broker."""
        return {
            'timestamp': timestamp.isoformat(),
            'turbine_id': tid,
            'operational_state': _tur_state_to_str(int(scada.get("WTUR_TurSt", 1))),
            'wind_speed': wind_speed,
            'wind_direction': wind_direction,
            'scada': scada,  # Full SCADA tags dict
            'rotor': {
                'rotor_speed': scada.get("WROT_RotSpd", 0),
                'rotor_torque': 0,
            },
            'pitch_angle': scada.get("WROT_PtAngValBl1", 0),
            'gearbox': {
                'temperature': scada.get("WNAC_NacTmp", 40),
                'vibration': scada.get("WNAC_VibMsNacXDir", 0),
            },
            'generator': {
                'power': scada.get("WTUR_TotPwrAt", 0) * 1000,  # kW → W
                'voltage': scada.get("WGEN_GnVtgMs", 0),
                'current': scada.get("WGEN_GnCurMs", 0),
                'temperature': scada.get("WGEN_GnStaTmp1", 45),
                'frequency': scada.get("WCNV_CnvGnFrq", 0),
            },
            'yaw': {
                'yaw_angle': scada.get("WYAW_YwVn1AlgnAvg5s", 0),
                'yaw_error': scada.get("WYAW_YwVn1AlgnAvg5s", 0),
            },
            'hydraulic': {
                'pressure': scada.get("WYAW_YwBrkHyPrs", 0),
            },
            'total_power': scada.get("WTUR_TotPwrAt", 0) * 1000,  # kW → W
        }

    def get_current_data(self) -> Dict[str, Dict]:
        with self._lock:
            return dict(self.latest_data)

    def get_turbine_data(self, turbine_id: str) -> Optional[Dict]:
        with self._lock:
            return self.latest_data.get(turbine_id)

    def get_history(self, turbine_id: str, limit: int = 100) -> List[Dict]:
        with self._lock:
            h = self.history.get(turbine_id, deque())
            return list(h)[-limit:]

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def turbine_ids(self) -> List[str]:
        return list(self.turbines.keys())


def _tur_state_to_str(state: int) -> str:
    """Map Bachmann TurState (1-9) to internal state string."""
    mapping = {
        1: "IDLE",       # Shutdown
        2: "IDLE",       # Standby
        3: "IDLE",       # Wait Restart
        4: "STARTING",   # Pre-Production
        5: "STARTING",   # Start Production
        6: "RUNNING",    # Production
        7: "STOPPING",   # Shutdown (in progress)
        8: "STARTING",   # Restart
        9: "STOPPING",   # Normal Stop
    }
    return mapping.get(state, "IDLE")

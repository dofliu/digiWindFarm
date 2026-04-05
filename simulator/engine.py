import sys
import os
import time
import threading
from datetime import datetime, timedelta
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
        self._time_step = time_step
        self._thread = threading.Thread(
            target=self._loop, args=(time_step,), daemon=True
        )
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

    @property
    def time_scale(self) -> float:
        """Current time acceleration factor. 1.0=real-time, 60=1min/s."""
        return self.wind_model.time_scale

    @time_scale.setter
    def time_scale(self, value: float):
        self.wind_model.time_scale = max(1.0, value)

    def _run_one_step(self, sim_time: datetime, time_step: float):
        """Execute one physics timestep for all turbines. Returns readings list."""
        base_wind = self.wind_model.get_wind_speed(sim_time)
        wind_direction = self.wind_model.get_wind_direction(sim_time)
        ambient_temp = self.wind_model.get_ambient_temp(sim_time)
        grid_frequency = self.grid_model.get_frequency(sim_time)
        grid_voltage = self.grid_model.get_voltage(sim_time)

        turb_component = self._turbulence_gen.step(
            base_wind, self.wind_model.turbulence_intensity, time_step
        )
        farm_wind = max(0, base_wind + turb_component)

        # FaultEngine.step() advances severity progression and alarm tracking.
        # Tag offsets are no longer used — all fault effects flow through
        # _get_fault_physics() inside each TurbinePhysicsModel.
        self.fault_engine.step(dt=time_step)

        readings = []
        for tid, model in self.turbines.items():
            idx = int(tid[2:]) - 1
            local_wind = self._per_turbine_wind.get_local_wind(farm_wind, idx)

            model.active_faults = [
                {
                    "scenario_id": fault.scenario_id,
                    "severity": fault.severity,
                    "tripped": fault.tripped,
                }
                for fault in self.fault_engine.active_faults
                if fault.turbine_id == tid
            ]

            for fault in self.fault_engine.active_faults:
                if fault.turbine_id == tid and fault.tripped:
                    model.cmd_emergency_stop(cause=f"fault:{fault.scenario_id}")

            scada_output = model.step(
                local_wind,
                wind_direction,
                ambient_temp,
                time_step,
                grid_frequency_ref=grid_frequency,
                grid_voltage_ref=grid_voltage,
            )

            output = self._scada_to_output(tid, sim_time, scada_output, local_wind, wind_direction)

            with self._lock:
                self.latest_data[tid] = output
                self.history[tid].append(output)

            readings.append(output)

            if self.modbus_server and self.modbus_server.is_running:
                self.modbus_server.update_turbine(tid, scada_output)

        return readings

    def _loop(self, time_step: float):
        """Main simulation loop. Supports time_scale for accelerated simulation.

        time_scale=1: real-time (1 physics second per wall second)
        time_scale=60: 60 physics seconds per wall second (1 min/s)
        time_scale=3600: 1 hour of simulation per wall second
        """
        sim_time = datetime.now()

        while self._running:
            try:
                ts = self.wind_model.time_scale
                if ts <= 1.0:
                    # Real-time mode: 1 step per wall-clock second
                    sim_time = datetime.now()
                    readings = self._run_one_step(sim_time, time_step)
                    for cb in self._callbacks:
                        try:
                            cb(readings)
                        except Exception:
                            pass
                    time.sleep(time_step)
                else:
                    # Accelerated mode: run multiple physics steps per wall second
                    # Each wall second advances sim_time by time_scale seconds
                    steps_per_tick = int(ts)
                    wall_sleep = max(0.1, time_step / ts * steps_per_tick)

                    for _ in range(steps_per_tick):
                        if not self._running:
                            break
                        sim_time += timedelta(seconds=time_step)
                        readings = self._run_one_step(sim_time, time_step)

                    # Only fire callbacks once per wall-tick (with latest readings)
                    for cb in self._callbacks:
                        try:
                            cb(readings)
                        except Exception:
                            pass

                    time.sleep(wall_sleep)

            except Exception as e:
                print(f"[Simulator] Error: {e}")
                time.sleep(1)

    def generate_bulk(self, duration_hours: float, time_step: float = 10.0,
                      callback=None, progress_callback=None) -> int:
        """Generate bulk historical data without real-time waiting.

        Runs the full physics simulation at maximum speed, writing data
        via callbacks. Useful for generating months of training data.

        Args:
            duration_hours: How many hours of simulated data to generate
            time_step: Physics step interval (10s default for storage efficiency)
            callback: Called with readings each step (same as on_data callbacks)
            progress_callback: Called with (current_hours, total_hours) periodically

        Returns:
            Total number of readings generated
        """
        total_steps = int(duration_hours * 3600 / time_step)
        sim_time = datetime.now()
        total_readings = 0
        report_interval = max(1, total_steps // 100)  # report every 1%

        for step_i in range(total_steps):
            if not self._running:
                break
            sim_time += timedelta(seconds=time_step)
            readings = self._run_one_step(sim_time, time_step)
            total_readings += len(readings)

            if callback:
                callback(readings)

            if progress_callback and step_i % report_interval == 0:
                current_hours = step_i * time_step / 3600
                progress_callback(current_hours, duration_hours)

        return total_readings

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

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
from turbine_model import WindTurbine


class WindFarmSimulator:
    """Wind farm simulator engine - produces realistic turbine data via callbacks."""

    def __init__(self, turbine_count: int = 14, base_wind_speed: float = 10.0,
                 turbulence_intensity: float = 0.1):
        self.wind_model = WindEnvironmentModel()
        self.wind_model.turbulence_intensity = turbulence_intensity
        self.turbines: Dict[str, WindTurbine] = {}
        self.latest_data: Dict[str, Dict] = {}
        self.history: Dict[str, deque] = {}
        self.history_maxlen = 3600  # ~1 hour at 1Hz

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._callbacks: List[Callable] = []
        self._lock = threading.Lock()

        # Initialize turbines
        for i in range(1, turbine_count + 1):
            tid = f"WT{i:03d}"
            self.add_turbine(tid)

    def add_turbine(self, turbine_id: str):
        self.turbines[turbine_id] = WindTurbine(turbine_id)
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
                wind_speed = self.wind_model.get_wind_speed(now)
                wind_direction = self.wind_model.get_wind_direction(now)

                readings = []
                for tid, turbine in self.turbines.items():
                    # Add per-turbine wind variation (wake effect approximation)
                    idx = int(tid[2:])
                    variation = (idx - 1) * 0.3  # slight offset per turbine
                    local_wind = max(0, wind_speed + variation * (0.5 - hash(tid) % 100 / 100))

                    output = turbine.simulate_step(local_wind, wind_direction, now, time_step)

                    with self._lock:
                        self.latest_data[tid] = output
                        self.history[tid].append(output)

                    readings.append(output)

                for cb in self._callbacks:
                    try:
                        cb(readings)
                    except Exception:
                        pass

                time.sleep(time_step)
            except Exception as e:
                print(f"[Simulator] Error: {e}")
                time.sleep(1)

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

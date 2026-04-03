"""
OPC DA Adapter - wraps opc_bachmann reading logic for integration with DataBroker.

This adapter connects to real wind farm OPC DA servers (Bachmann, Vestas)
and produces readings in the same format as the simulator.

Requires: OpenOPC2 + Graybox.OPC.DAWrapper (Windows only, 32-bit Python)
"""

import time
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Callable

from server.models import DataSourceConfig


# Tag mapping for different wind farm types
TAG_MAPS = {
    "z72": {
        "server": "BACHMANN.OPCEnterpriseServer.2",
        "turbine_prefix": "Z72.H{:02d}",
        "turbine_range": range(1, 31),
        "tags": {
            "wind_speed": "WMET.Z72PLC__UI_Loc_WMET_Analogue_WSpeedNacAvg10m",
            "status": "WTUR.Z72PLC__UI_Loc_WTUR_State_TurSt",
        },
    },
    "ck1": {
        "server": "Vestas.VOBOPCServerDA.3",
        "turbine_prefix": "Chankong1.WTG{:02d}",
        "turbine_range": range(1, 24),
        "tags": {
            "wind_speed": "Ambient.WindSpeed",
            "power": "Grid.Power",
            "generator_rpm": "Generator.RPM",
            "rotor_rpm": "RotorSystem.RotorRPM",
            "gen_temp": "Generator.Phase1Temperature",
            "status": "System.OperationStateInt",
        },
    },
    "ck2": {
        "server": "Vestas.VOBOPCServerDA.3",
        "turbine_prefix": "Chankong2.WTG{:02d}",
        "turbine_range": range(24, 32),
        "tags": {
            "wind_speed": "Ambient.WindSpeed",
            "power": "Grid.Power",
            "generator_rpm": "Generator.RPM",
            "rotor_rpm": "RotorSystem.RotorRPM",
            "gen_temp": "Generator.Phase1Temperature",
            "status": "System.OperationStateInt",
        },
    },
}


class OPCDAAdapter:
    """Connects to real OPC DA servers and produces standardized turbine readings."""

    def __init__(self, config: Optional[DataSourceConfig] = None):
        self.config = config
        self._client = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._callbacks: List[Callable] = []
        self._poll_interval = 17  # seconds (Z72 default)

    def on_data(self, callback: Callable[[List[Dict]], None]):
        self._callbacks.append(callback)

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=10)

    def _connect(self):
        """Connect to OPC DA server using OpenOPC2."""
        try:
            import openopc2
            self._client = openopc2.client()
            server = self.config.opcProgId if self.config else "BACHMANN.OPCEnterpriseServer.2"
            host = self.config.opcHost if self.config else "localhost"
            self._client.connect(server, host)
            print(f"[OPCAdapter] Connected to {server} on {host}")
            return True
        except Exception as e:
            print(f"[OPCAdapter] Connection failed: {e}")
            return False

    def _poll_loop(self):
        """Poll OPC server and convert to standard readings."""
        connected = self._connect()
        if not connected:
            print("[OPCAdapter] Could not connect, adapter stopped")
            self._running = False
            return

        while self._running:
            try:
                readings = self._read_all_turbines()
                for cb in self._callbacks:
                    try:
                        cb(readings)
                    except Exception:
                        pass
                time.sleep(self._poll_interval)
            except Exception as e:
                print(f"[OPCAdapter] Error: {e}")
                time.sleep(5)

    def _read_all_turbines(self) -> List[Dict]:
        """Read data from all turbines and return in simulator-compatible format."""
        readings = []
        # Determine farm type from config
        farm_type = "z72"  # default
        if self.config and self.config.opcProgId:
            if "Vestas" in self.config.opcProgId:
                farm_type = "ck1"

        tag_map = TAG_MAPS.get(farm_type, TAG_MAPS["z72"])

        for idx in tag_map["turbine_range"]:
            prefix = tag_map["turbine_prefix"].format(idx)
            turbine_id = f"WT{idx:03d}"
            now = datetime.now()

            # Build tag list
            tags_to_read = []
            for key, tag_suffix in tag_map["tags"].items():
                full_tag = f"{prefix}.{tag_suffix}"
                tags_to_read.append((key, full_tag))

            # Read from OPC
            values = {}
            try:
                tag_names = [t[1] for t in tags_to_read]
                results = self._client.read(tag_names, sync=True, source="device", timeout=10000)
                for i, (key, _) in enumerate(tags_to_read):
                    if i < len(results):
                        val = results[i][1] if results[i][1] is not None else 0
                        values[key] = float(val) if isinstance(val, (int, float)) else 0
            except Exception as e:
                print(f"[OPCAdapter] Read error for {turbine_id}: {e}")
                continue

            # Convert to simulator-compatible output format
            reading = {
                'timestamp': now.isoformat(),
                'turbine_id': turbine_id,
                'operational_state': self._map_opc_status(values.get('status', 0)),
                'wind_speed': values.get('wind_speed', 0),
                'wind_direction': 0,
                'rotor': {
                    'rotor_speed': values.get('rotor_rpm', 0),
                    'rotor_torque': 0,
                },
                'pitch_angle': 0,
                'gearbox': {
                    'temperature': 0,
                    'vibration': 0,
                },
                'generator': {
                    'power': values.get('power', 0) * 1000,  # kW → W
                    'voltage': 690,
                    'current': 0,
                    'temperature': values.get('gen_temp', 0),
                    'frequency': 50,
                },
                'yaw': {'yaw_angle': 0, 'yaw_error': 0},
                'hydraulic': {'pressure': 0},
                'total_power': values.get('power', 0) * 1000,
            }
            readings.append(reading)

        return readings

    @staticmethod
    def _map_opc_status(value) -> str:
        """Map OPC turbine state integer to string."""
        try:
            v = int(value)
        except (ValueError, TypeError):
            return "IDLE"
        # Common Vestas/Bachmann state codes
        if v in (1, 2, 3, 4):   # various running states
            return "RUNNING"
        elif v in (5, 6, 7):     # stopping/standby
            return "IDLE"
        elif v in (8, 9, 10):    # fault/trip
            return "FAULT"
        return "IDLE"

import sqlite3
import json
import threading
from datetime import datetime
from typing import List, Optional
from pathlib import Path


DB_PATH = Path(__file__).parent.parent / "wind_farm_data.db"


class Storage:
    """SQLite-based time-series storage for turbine readings (39 SCADA tags)."""

    def __init__(self, db_path: str = str(DB_PATH)):
        self._db_path = db_path
        self._local = threading.local()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(self._db_path)
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    def _init_db(self):
        conn = sqlite3.connect(self._db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS turbine_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                turbine_id TEXT NOT NULL,
                status TEXT,
                tur_state INTEGER,
                wind_speed REAL,
                power_output REAL,
                rotor_speed REAL,
                blade_angle REAL,
                temperature REAL,
                vibration REAL,
                voltage REAL,
                current_amp REAL,
                yaw_angle REAL,
                gearbox_temp REAL,
                frequency REAL,
                hydraulic_pressure REAL,
                -- Extended SCADA fields (v2)
                scada_json TEXT
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_turbine_time
            ON turbine_data (turbine_id, timestamp)
        """)
        # Add scada_json column if upgrading from v1 schema
        try:
            conn.execute("SELECT scada_json FROM turbine_data LIMIT 1")
        except sqlite3.OperationalError:
            conn.execute("ALTER TABLE turbine_data ADD COLUMN scada_json TEXT")
        try:
            conn.execute("SELECT tur_state FROM turbine_data LIMIT 1")
        except sqlite3.OperationalError:
            conn.execute("ALTER TABLE turbine_data ADD COLUMN tur_state INTEGER")
        conn.commit()
        conn.close()

    def store_reading(self, reading: dict):
        """Store a single turbine reading (from simulator output dict)."""
        conn = self._get_conn()

        def to_float(v, default=0.0):
            try:
                return float(v) if v is not None else default
            except (TypeError, ValueError):
                return default

        # Serialize full SCADA dict if available
        scada = reading.get('scada', {})
        scada_json = json.dumps(scada) if scada else None

        tur_state = int(scada.get("WTUR_TurSt", 0)) if scada else None

        conn.execute("""
            INSERT INTO turbine_data
            (timestamp, turbine_id, status, tur_state, wind_speed, power_output,
             rotor_speed, blade_angle, temperature, vibration, voltage,
             current_amp, yaw_angle, gearbox_temp, frequency, hydraulic_pressure,
             scada_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(reading.get('timestamp', datetime.now().isoformat())),
            str(reading.get('turbine_id', '')),
            str(reading.get('operational_state', 'IDLE')),
            tur_state,
            to_float(reading.get('wind_speed', 0)),
            to_float(reading.get('total_power', 0)) / 1_000_000,
            to_float(scada.get('WROT_RotSpd', reading.get('rotor', {}).get('rotor_speed', 0))),
            to_float(scada.get('WROT_PtAngValBl1', reading.get('pitch_angle', 0))),
            to_float(scada.get('WGEN_GnStaTmp1', reading.get('generator', {}).get('temperature', 0))),
            to_float(scada.get('WNAC_VibMsNacXDir', reading.get('gearbox', {}).get('vibration', 0))),
            to_float(scada.get('WGEN_GnVtgMs', reading.get('generator', {}).get('voltage', 0))),
            to_float(scada.get('WGEN_GnCurMs', reading.get('generator', {}).get('current', 0))),
            to_float(scada.get('WYAW_YwVn1AlgnAvg5s', reading.get('yaw', {}).get('yaw_angle', 0))),
            to_float(scada.get('WNAC_NacTmp', reading.get('gearbox', {}).get('temperature', 0))),
            to_float(scada.get('WCNV_CnvGnFrq', reading.get('generator', {}).get('frequency')), None),
            to_float(scada.get('WYAW_YwBrkHyPrs', reading.get('hydraulic', {}).get('pressure')), None),
            scada_json,
        ))
        conn.commit()

    def store_readings(self, readings: List[dict]):
        for r in readings:
            self.store_reading(r)

    def query_history(self, turbine_id: str, start: Optional[str] = None,
                      end: Optional[str] = None, limit: int = 1000) -> List[dict]:
        conn = self._get_conn()
        query = "SELECT * FROM turbine_data WHERE turbine_id = ?"
        params: list = [turbine_id]

        if start:
            query += " AND timestamp >= ?"
            params.append(start)
        if end:
            query += " AND timestamp <= ?"
            params.append(end)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        rows = conn.execute(query, params).fetchall()
        result = []
        for row in rows:
            d = dict(row)
            # Expand scada_json back to dict if available
            if d.get('scada_json'):
                try:
                    d['scada'] = json.loads(d['scada_json'])
                except (json.JSONDecodeError, TypeError):
                    pass
            result.append(d)
        return result

    def query_latest(self, turbine_id: str) -> Optional[dict]:
        rows = self.query_history(turbine_id, limit=1)
        return rows[0] if rows else None

    def query_all_latest(self) -> List[dict]:
        conn = self._get_conn()
        rows = conn.execute("""
            SELECT t1.* FROM turbine_data t1
            INNER JOIN (
                SELECT turbine_id, MAX(timestamp) as max_ts
                FROM turbine_data
                GROUP BY turbine_id
            ) t2 ON t1.turbine_id = t2.turbine_id AND t1.timestamp = t2.max_ts
            ORDER BY t1.turbine_id
        """).fetchall()
        return [dict(row) for row in rows]

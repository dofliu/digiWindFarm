import sqlite3
import json
import threading
import time as _time
from datetime import datetime, timedelta
from typing import List, Optional
from pathlib import Path


import os as _os
DB_PATH = Path(_os.environ.get("DB_PATH", str(Path(__file__).parent.parent / "wind_farm_data.db")))


class Storage:
    """SQLite-based time-series storage for turbine readings and history events.

    Data tiers:
      - turbine_data:        10s writes (configurable), 3-day retention for raw
      - turbine_data_1m:     1-min aggregates, 90-day retention
      - turbine_data_10m:    10-min aggregates, permanent
      - turbine_snapshots:   1s high-freq capture around events, permanent
      - sessions:            tracks simulation/data source configs
    """

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

        # ── Main raw data table (10s interval writes) ──
        conn.execute("""
            CREATE TABLE IF NOT EXISTS turbine_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                turbine_id TEXT NOT NULL,
                session_id INTEGER,
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
                scada_json TEXT
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_turbine_time
            ON turbine_data (turbine_id, timestamp)
        """)

        # ── 1-minute aggregate table ──
        conn.execute("""
            CREATE TABLE IF NOT EXISTS turbine_data_1m (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                turbine_id TEXT NOT NULL,
                session_id INTEGER,
                power_output_avg REAL,
                power_output_max REAL,
                power_output_min REAL,
                wind_speed_avg REAL,
                wind_speed_max REAL,
                rotor_speed_avg REAL,
                temperature_avg REAL,
                vibration_avg REAL,
                vibration_max REAL,
                sample_count INTEGER
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_1m_turbine_time
            ON turbine_data_1m (turbine_id, timestamp)
        """)

        # ── 10-minute aggregate table ──
        conn.execute("""
            CREATE TABLE IF NOT EXISTS turbine_data_10m (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                turbine_id TEXT NOT NULL,
                session_id INTEGER,
                power_output_avg REAL,
                power_output_max REAL,
                power_output_min REAL,
                wind_speed_avg REAL,
                wind_speed_max REAL,
                rotor_speed_avg REAL,
                temperature_avg REAL,
                vibration_avg REAL,
                vibration_max REAL,
                sample_count INTEGER
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_10m_turbine_time
            ON turbine_data_10m (turbine_id, timestamp)
        """)

        # ── Event snapshots (1s high-freq around events) ──
        conn.execute("""
            CREATE TABLE IF NOT EXISTS turbine_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                turbine_id TEXT NOT NULL,
                session_id INTEGER,
                event_ref TEXT,
                wind_speed REAL,
                power_output REAL,
                rotor_speed REAL,
                scada_json TEXT
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_snapshots_turbine_time
            ON turbine_snapshots (turbine_id, timestamp)
        """)

        # ── Sessions table ──
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TEXT NOT NULL,
                ended_at TEXT,
                data_source TEXT NOT NULL,
                turbine_count INTEGER,
                rated_power_kw REAL,
                rotor_diameter_m REAL,
                model_name TEXT,
                config_json TEXT
            )
        """)

        # ── History events (existing) ──
        conn.execute("""
            CREATE TABLE IF NOT EXISTS history_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                end_timestamp TEXT,
                turbine_id TEXT,
                event_type TEXT NOT NULL,
                source TEXT NOT NULL,
                title TEXT NOT NULL,
                detail TEXT,
                payload_json TEXT
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_history_events_turbine_time
            ON history_events (turbine_id, timestamp)
        """)

        # ── Work Orders ──
        conn.execute("""
            CREATE TABLE IF NOT EXISTS work_orders (
                id TEXT PRIMARY KEY,
                turbine_id INTEGER NOT NULL,
                turbine_name TEXT NOT NULL,
                technician_id INTEGER,
                status TEXT NOT NULL DEFAULT 'OPEN',
                created_at TEXT NOT NULL,
                completed_at TEXT,
                fault_description TEXT NOT NULL,
                notes TEXT DEFAULT '',
                photos_json TEXT DEFAULT '[]'
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_work_orders_status
            ON work_orders (status)
        """)

        # ── Technicians ──
        conn.execute("""
            CREATE TABLE IF NOT EXISTS technicians (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'ON_DUTY'
            )
        """)

        # Seed default technicians if empty
        existing = conn.execute("SELECT COUNT(*) FROM technicians").fetchone()[0]
        if existing == 0:
            for name, status in [
                ("Alice Johnson", "ON_DUTY"),
                ("Bob Williams", "ON_DUTY"),
                ("Charlie Brown", "ON_DUTY"),
                ("Diana Miller", "OFF_DUTY"),
            ]:
                conn.execute("INSERT INTO technicians (name, status) VALUES (?, ?)", (name, status))

        # ── Migrations for existing DBs ──
        self._migrate_columns(conn, "turbine_data", [
            ("scada_json", "TEXT"),
            ("tur_state", "INTEGER"),
            ("session_id", "INTEGER"),
        ])
        self._migrate_columns(conn, "history_events", [
            ("end_timestamp", "TEXT"),
        ])

        conn.commit()
        conn.close()

    def _migrate_columns(self, conn, table: str, columns: list):
        """Add missing columns to existing tables."""
        for col_name, col_type in columns:
            try:
                conn.execute(f"SELECT {col_name} FROM {table} LIMIT 1")
            except sqlite3.OperationalError:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")

    # ══════════════════════════════════════════════════════════════════
    #  Session Management
    # ══════════════════════════════════════════════════════════════════

    def create_session(self, data_source: str, turbine_count: int,
                       rated_power_kw: float = None, rotor_diameter_m: float = None,
                       model_name: str = None, config: dict = None) -> int:
        """Create a new session and return its ID."""
        conn = self._get_conn()
        cursor = conn.execute("""
            INSERT INTO sessions (started_at, data_source, turbine_count,
                                  rated_power_kw, rotor_diameter_m, model_name, config_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            data_source,
            turbine_count,
            rated_power_kw,
            rotor_diameter_m,
            model_name,
            json.dumps(config) if config else None,
        ))
        conn.commit()
        return cursor.lastrowid

    def end_session(self, session_id: int):
        """Mark a session as ended."""
        conn = self._get_conn()
        conn.execute("UPDATE sessions SET ended_at = ? WHERE id = ?",
                     (datetime.now().isoformat(), session_id))
        conn.commit()

    def get_sessions(self, limit: int = 20) -> List[dict]:
        """Return the most recent sessions, newest first."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM sessions ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        result = []
        for row in rows:
            d = dict(row)
            if d.get("config_json"):
                try:
                    d["config"] = json.loads(d["config_json"])
                except (json.JSONDecodeError, TypeError):
                    pass
            result.append(d)
        return result

    def get_active_session(self) -> Optional[dict]:
        """Return the latest session that has not ended, or None."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM sessions WHERE ended_at IS NULL ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if row:
            d = dict(row)
            if d.get("config_json"):
                try:
                    d["config"] = json.loads(d["config_json"])
                except (json.JSONDecodeError, TypeError):
                    pass
            return d
        return None

    # ══════════════════════════════════════════════════════════════════
    #  Data Writing
    # ══════════════════════════════════════════════════════════════════

    def record_event(
        self,
        event_type: str,
        source: str,
        title: str,
        turbine_id: Optional[str] = None,
        detail: Optional[str] = None,
        payload: Optional[dict] = None,
        timestamp: Optional[str] = None,
        end_timestamp: Optional[str] = None,
    ):
        """Store a history event for chart markers and audit-style review."""
        conn = self._get_conn()
        conn.execute("""
            INSERT INTO history_events
            (timestamp, end_timestamp, turbine_id, event_type, source, title, detail, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp or datetime.now().isoformat(),
            end_timestamp,
            turbine_id,
            event_type,
            source,
            title,
            detail,
            json.dumps(payload) if payload is not None else None,
        ))
        conn.commit()

    def close_open_events(
        self,
        event_type: str,
        source: Optional[str] = None,
        turbine_id: Optional[str] = None,
        closed_at: Optional[str] = None,
    ):
        """Close open-ended events by setting end_timestamp."""
        conn = self._get_conn()
        query = """
            UPDATE history_events
            SET end_timestamp = ?
            WHERE event_type = ? AND end_timestamp IS NULL
        """
        params: list = [closed_at or datetime.now().isoformat(), event_type]
        if source is not None:
            query += " AND source = ?"
            params.append(source)
        if turbine_id is None:
            query += " AND turbine_id IS NULL"
        else:
            query += " AND turbine_id = ?"
            params.append(turbine_id)
        conn.execute(query, params)
        conn.commit()

    def store_reading(self, reading: dict, session_id: int = None):
        """Store a single turbine reading (from simulator output dict)."""
        conn = self._get_conn()

        def to_float(v, default=0.0):
            try:
                return float(v) if v is not None else default
            except (TypeError, ValueError):
                return default

        scada = reading.get('scada', {})
        scada_json = json.dumps(scada) if scada else None
        tur_state = int(scada.get("WTUR_TurSt", 0)) if scada else None

        conn.execute("""
            INSERT INTO turbine_data
            (timestamp, turbine_id, session_id, status, tur_state, wind_speed, power_output,
             rotor_speed, blade_angle, temperature, vibration, voltage,
             current_amp, yaw_angle, gearbox_temp, frequency, hydraulic_pressure,
             scada_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(reading.get('timestamp', datetime.now().isoformat())),
            str(reading.get('turbine_id', '')),
            session_id,
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

    def store_readings(self, readings: List[dict], session_id: int = None):
        """Store a batch of turbine readings."""
        for r in readings:
            self.store_reading(r, session_id)

    def store_snapshot(self, reading: dict, event_ref: str, session_id: int = None):
        """Store a 1s snapshot reading linked to an event."""
        conn = self._get_conn()
        scada = reading.get('scada', {})
        scada_json = json.dumps(scada) if scada else None

        def to_float(v, default=0.0):
            try:
                return float(v) if v is not None else default
            except (TypeError, ValueError):
                return default

        conn.execute("""
            INSERT INTO turbine_snapshots
            (timestamp, turbine_id, session_id, event_ref, wind_speed, power_output,
             rotor_speed, scada_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(reading.get('timestamp', datetime.now().isoformat())),
            str(reading.get('turbine_id', '')),
            session_id,
            event_ref,
            to_float(reading.get('wind_speed', 0)),
            to_float(reading.get('total_power', 0)) / 1_000_000,
            to_float(scada.get('WROT_RotSpd', reading.get('rotor', {}).get('rotor_speed', 0))),
            scada_json,
        ))
        conn.commit()

    def store_snapshots(self, readings: List[dict], event_ref: str, session_id: int = None):
        """Store a batch of 1s snapshot readings for an event."""
        for r in readings:
            self.store_snapshot(r, event_ref, session_id)

    # ══════════════════════════════════════════════════════════════════
    #  Data Retention & Downsampling
    # ══════════════════════════════════════════════════════════════════

    def run_downsampling(self):
        """Create 1-minute and 10-minute aggregates from raw data.

        Called periodically by the background maintenance task.
        """
        conn = self._get_conn()
        now = datetime.now()

        # ── Build 1-minute aggregates from raw data older than 5 minutes ──
        cutoff_1m = (now - timedelta(minutes=5)).isoformat()
        # Find the latest 1m aggregate timestamp to avoid re-processing
        latest_1m = conn.execute(
            "SELECT MAX(timestamp) FROM turbine_data_1m"
        ).fetchone()[0]
        from_ts = latest_1m or "2000-01-01T00:00:00"

        conn.execute("""
            INSERT INTO turbine_data_1m
                (timestamp, turbine_id, session_id,
                 power_output_avg, power_output_max, power_output_min,
                 wind_speed_avg, wind_speed_max, rotor_speed_avg,
                 temperature_avg, vibration_avg, vibration_max, sample_count)
            SELECT
                MIN(timestamp),
                turbine_id,
                session_id,
                AVG(power_output), MAX(power_output), MIN(power_output),
                AVG(wind_speed), MAX(wind_speed), AVG(rotor_speed),
                AVG(temperature), AVG(vibration), MAX(vibration),
                COUNT(*)
            FROM turbine_data
            WHERE timestamp > ? AND timestamp <= ?
            GROUP BY turbine_id,
                     CAST(strftime('%s', timestamp) AS INTEGER) / 60
            HAVING COUNT(*) > 0
        """, (from_ts, cutoff_1m))
        conn.commit()

        # ── Build 10-minute aggregates from 1-min data older than 15 minutes ──
        cutoff_10m = (now - timedelta(minutes=15)).isoformat()
        latest_10m = conn.execute(
            "SELECT MAX(timestamp) FROM turbine_data_10m"
        ).fetchone()[0]
        from_ts_10m = latest_10m or "2000-01-01T00:00:00"

        conn.execute("""
            INSERT INTO turbine_data_10m
                (timestamp, turbine_id, session_id,
                 power_output_avg, power_output_max, power_output_min,
                 wind_speed_avg, wind_speed_max, rotor_speed_avg,
                 temperature_avg, vibration_avg, vibration_max, sample_count)
            SELECT
                MIN(timestamp),
                turbine_id,
                session_id,
                AVG(power_output_avg), MAX(power_output_max), MIN(power_output_min),
                AVG(wind_speed_avg), MAX(wind_speed_max), AVG(rotor_speed_avg),
                AVG(temperature_avg), AVG(vibration_avg), MAX(vibration_max),
                SUM(sample_count)
            FROM turbine_data_1m
            WHERE timestamp > ? AND timestamp <= ?
            GROUP BY turbine_id,
                     CAST(strftime('%s', timestamp) AS INTEGER) / 600
            HAVING COUNT(*) > 0
        """, (from_ts_10m, cutoff_10m))
        conn.commit()

    def run_cleanup(self, raw_retention_days: int = 3, agg_1m_retention_days: int = 90):
        """Delete old raw data and old 1-minute aggregates.

        - Raw (turbine_data): keep last `raw_retention_days` days (default 3)
        - 1-minute aggregates: keep last `agg_1m_retention_days` days (default 90)
        - 10-minute aggregates: keep forever
        - Snapshots: keep forever
        """
        conn = self._get_conn()
        now = datetime.now()

        raw_cutoff = (now - timedelta(days=raw_retention_days)).isoformat()
        deleted_raw = conn.execute(
            "DELETE FROM turbine_data WHERE timestamp < ?", (raw_cutoff,)
        ).rowcount

        agg_cutoff = (now - timedelta(days=agg_1m_retention_days)).isoformat()
        deleted_1m = conn.execute(
            "DELETE FROM turbine_data_1m WHERE timestamp < ?", (agg_cutoff,)
        ).rowcount

        conn.commit()

        if deleted_raw > 0 or deleted_1m > 0:
            print(f"[Storage] Cleanup: removed {deleted_raw} raw rows, {deleted_1m} 1m-agg rows")

        return {"deleted_raw": deleted_raw, "deleted_1m": deleted_1m}

    def get_db_stats(self) -> dict:
        """Return row counts and estimated sizes for each table."""
        conn = self._get_conn()
        tables = ["turbine_data", "turbine_data_1m", "turbine_data_10m",
                   "turbine_snapshots", "history_events", "sessions"]
        stats = {}
        for table in tables:
            try:
                count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                stats[table] = count
            except sqlite3.OperationalError:
                stats[table] = 0

        # DB file size
        db_path = Path(self._db_path)
        stats["db_size_mb"] = round(db_path.stat().st_size / (1024 * 1024), 1) if db_path.exists() else 0
        return stats

    # ══════════════════════════════════════════════════════════════════
    #  Data Queries
    # ══════════════════════════════════════════════════════════════════

    def query_history(self, turbine_id: str, start: Optional[str] = None,
                      end: Optional[str] = None, limit: int = 1000) -> List[dict]:
        """Query raw turbine data with optional time-range filter."""
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
            if d.get('scada_json'):
                try:
                    d['scada'] = json.loads(d['scada_json'])
                except (json.JSONDecodeError, TypeError):
                    pass
            result.append(d)
        return result

    def query_latest(self, turbine_id: str) -> Optional[dict]:
        """Return the most recent reading for a single turbine."""
        rows = self.query_history(turbine_id, limit=1)
        return rows[0] if rows else None

    def query_events(
        self,
        turbine_id: Optional[str] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        limit: int = 500,
    ) -> List[dict]:
        """Query history events with optional turbine and time-range filter."""
        conn = self._get_conn()
        query = """
            SELECT * FROM history_events
            WHERE (turbine_id = ? OR turbine_id IS NULL)
        """
        params: list = [turbine_id]

        if turbine_id is None:
            query = "SELECT * FROM history_events WHERE 1=1"
            params = []
        if start:
            query += " AND COALESCE(end_timestamp, timestamp) >= ?"
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
            if d.get("payload_json"):
                try:
                    d["payload"] = json.loads(d["payload_json"])
                except (json.JSONDecodeError, TypeError):
                    pass
            result.append(d)
        return result

    def query_all_latest(self) -> List[dict]:
        """Return the most recent reading for every turbine."""
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

    def query_snapshots(self, turbine_id: str, event_ref: Optional[str] = None,
                        start: Optional[str] = None, end: Optional[str] = None,
                        limit: int = 1000) -> List[dict]:
        """Query high-frequency snapshot readings with optional event and time filter."""
        conn = self._get_conn()
        query = "SELECT * FROM turbine_snapshots WHERE turbine_id = ?"
        params: list = [turbine_id]
        if event_ref:
            query += " AND event_ref = ?"
            params.append(event_ref)
        if start:
            query += " AND timestamp >= ?"
            params.append(start)
        if end:
            query += " AND timestamp <= ?"
            params.append(end)
        query += " ORDER BY timestamp ASC LIMIT ?"
        params.append(limit)
        rows = conn.execute(query, params).fetchall()
        result = []
        for row in rows:
            d = dict(row)
            if d.get('scada_json'):
                try:
                    d['scada'] = json.loads(d['scada_json'])
                except (json.JSONDecodeError, TypeError):
                    pass
            result.append(d)
        return result

    # ══════════════════════════════════════════════════════════════════
    #  Work Orders
    # ══════════════════════════════════════════════════════════════════

    def create_work_order(self, turbine_id: int, turbine_name: str,
                          fault_description: str,
                          technician_id: Optional[int] = None) -> dict:
        """Create a new maintenance work order and return it."""
        conn = self._get_conn()
        wo_id = f"WO-{int(_time.time() * 1000)}"
        now = datetime.now().isoformat()
        status = "IN_PROGRESS" if technician_id else "OPEN"
        conn.execute("""
            INSERT INTO work_orders
            (id, turbine_id, turbine_name, technician_id, status, created_at,
             fault_description, notes, photos_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, '', '[]')
        """, (wo_id, turbine_id, turbine_name, technician_id, status, now,
              fault_description))
        conn.commit()
        return self.get_work_order(wo_id)

    def get_work_order(self, wo_id: str) -> Optional[dict]:
        """Return a single work order by ID, or None."""
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM work_orders WHERE id = ?", (wo_id,)).fetchone()
        if not row:
            return None
        return self._wo_row_to_dict(row)

    def query_work_orders(self, status: Optional[str] = None,
                          turbine_id: Optional[int] = None,
                          limit: int = 100) -> List[dict]:
        """List work orders filtered by status and/or turbine."""
        conn = self._get_conn()
        query = "SELECT * FROM work_orders WHERE 1=1"
        params: list = []
        if status:
            query += " AND status = ?"
            params.append(status)
        if turbine_id is not None:
            query += " AND turbine_id = ?"
            params.append(turbine_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(query, params).fetchall()
        return [self._wo_row_to_dict(r) for r in rows]

    def update_work_order(self, wo_id: str, **kwargs) -> Optional[dict]:
        """Update work order fields (status, notes, photos) and return it."""
        conn = self._get_conn()
        sets = []
        params = []
        if "status" in kwargs:
            sets.append("status = ?")
            params.append(kwargs["status"])
            if kwargs["status"] == "COMPLETED":
                sets.append("completed_at = ?")
                params.append(datetime.now().isoformat())
        if "notes" in kwargs:
            sets.append("notes = ?")
            params.append(kwargs["notes"])
        if "photos" in kwargs:
            sets.append("photos_json = ?")
            params.append(json.dumps(kwargs["photos"]))
        if not sets:
            return self.get_work_order(wo_id)
        params.append(wo_id)
        conn.execute(f"UPDATE work_orders SET {', '.join(sets)} WHERE id = ?", params)
        conn.commit()
        return self.get_work_order(wo_id)

    def _wo_row_to_dict(self, row) -> dict:
        d = dict(row)
        # Map to frontend expected format
        photos = []
        if d.get("photos_json"):
            try:
                photos = json.loads(d["photos_json"])
            except (json.JSONDecodeError, TypeError):
                pass
        return {
            "id": d["id"],
            "turbineId": d["turbine_id"],
            "turbineName": d["turbine_name"],
            "technicianId": d.get("technician_id"),
            "status": d["status"],
            "createdAt": int(datetime.fromisoformat(d["created_at"]).timestamp() * 1000)
                if d.get("created_at") else 0,
            "completedAt": d.get("completed_at"),
            "faultDescription": d["fault_description"],
            "notes": d.get("notes", ""),
            "photos": photos,
        }

    # ══════════════════════════════════════════════════════════════════
    #  Technicians
    # ══════════════════════════════════════════════════════════════════

    def create_technician(self, name: str, status: str = "ON_DUTY") -> dict:
        """Add a technician and return the new record."""
        conn = self._get_conn()
        cursor = conn.execute(
            "INSERT INTO technicians (name, status) VALUES (?, ?)", (name, status)
        )
        conn.commit()
        return {"id": cursor.lastrowid, "name": name, "status": status}

    def query_technicians(self) -> List[dict]:
        """Return all technicians ordered by ID."""
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM technicians ORDER BY id").fetchall()
        return [{"id": r["id"], "name": r["name"], "status": r["status"]} for r in rows]

    def update_technician(self, tech_id: int, status: str) -> Optional[dict]:
        """Update a technician's duty status and return the record."""
        conn = self._get_conn()
        conn.execute("UPDATE technicians SET status = ? WHERE id = ?", (status, tech_id))
        conn.commit()
        row = conn.execute("SELECT * FROM technicians WHERE id = ?", (tech_id,)).fetchone()
        if not row:
            return None
        return {"id": row["id"], "name": row["name"], "status": row["status"]}

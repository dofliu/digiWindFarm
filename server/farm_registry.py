"""
Wind Farm Registry — manages multiple independent wind farm projects.

Each farm has its own SQLite database file under data/farms/{farm_id}/.
A global metadata DB (data/farms.db) tracks all farms and the active farm.
"""

import json
import os
import shutil
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


DATA_DIR = Path(os.environ.get(
    "FARM_DATA_DIR",
    str(Path(__file__).parent.parent / "data"),
))
FARMS_DB = DATA_DIR / "farms.db"
FARMS_DIR = DATA_DIR / "farms"

LEGACY_DB_NAME = "wind_farm_data.db"


@dataclass
class FarmConfig:
    """Serializable wind farm project definition."""
    farm_id: str
    name: str
    turbine_count: int = 14
    turbine_spec: Dict = field(default_factory=dict)
    wind_profile: Dict = field(default_factory=dict)
    grid_profile: Dict = field(default_factory=dict)
    layout: Dict = field(default_factory=dict)
    location: str = ""
    description: str = ""
    created_at: str = ""
    last_active_at: str = ""

    def to_dict(self) -> dict:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "FarmConfig":
        return cls(
            farm_id=row["farm_id"],
            name=row["name"],
            turbine_count=row["turbine_count"],
            turbine_spec=json.loads(row["turbine_spec_json"] or "{}"),
            wind_profile=json.loads(row["wind_profile_json"] or "{}"),
            grid_profile=json.loads(row["grid_profile_json"] or "{}"),
            layout=json.loads(row["layout_json"] or "{}"),
            location=row["location"] or "",
            description=row["description"] or "",
            created_at=row["created_at"] or "",
            last_active_at=row["last_active_at"] or "",
        )


class FarmRegistry:
    """Manages the global farm list and provides paths to per-farm databases."""

    def __init__(self, data_dir: Path = DATA_DIR):
        self._data_dir = data_dir
        self._farms_dir = data_dir / "farms"
        self._farms_db = data_dir / "farms.db"
        self._farms_dir.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._farms_db))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS farms (
                farm_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                turbine_count INTEGER NOT NULL DEFAULT 14,
                turbine_spec_json TEXT,
                wind_profile_json TEXT,
                grid_profile_json TEXT,
                layout_json TEXT,
                location TEXT,
                description TEXT,
                created_at TEXT NOT NULL,
                last_active_at TEXT,
                is_active INTEGER NOT NULL DEFAULT 0
            )
        """)
        conn.commit()
        conn.close()

    # ── CRUD ────────────────────────────────────────────────────────────

    def create_farm(self, farm_id: str, name: str,
                    turbine_count: int = 14,
                    turbine_spec: Optional[Dict] = None,
                    wind_profile: Optional[Dict] = None,
                    grid_profile: Optional[Dict] = None,
                    layout: Optional[Dict] = None,
                    location: str = "",
                    description: str = "") -> FarmConfig:
        """Create a new wind farm project with its own database directory."""
        farm_dir = self._farms_dir / farm_id
        farm_dir.mkdir(parents=True, exist_ok=True)

        now = datetime.now().isoformat()
        conn = self._get_conn()
        conn.execute("""
            INSERT INTO farms (farm_id, name, turbine_count,
                               turbine_spec_json, wind_profile_json,
                               grid_profile_json, layout_json,
                               location, description, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            farm_id, name, turbine_count,
            json.dumps(turbine_spec or {}),
            json.dumps(wind_profile or {}),
            json.dumps(grid_profile or {}),
            json.dumps(layout or {}),
            location, description, now,
        ))
        conn.commit()
        conn.close()

        config_path = farm_dir / "config.json"
        cfg = FarmConfig(
            farm_id=farm_id, name=name, turbine_count=turbine_count,
            turbine_spec=turbine_spec or {}, wind_profile=wind_profile or {},
            grid_profile=grid_profile or {}, layout=layout or {},
            location=location, description=description, created_at=now,
        )
        config_path.write_text(json.dumps(cfg.to_dict(), indent=2, ensure_ascii=False))
        return cfg

    def get_farm(self, farm_id: str) -> Optional[FarmConfig]:
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM farms WHERE farm_id = ?", (farm_id,)).fetchone()
        conn.close()
        return FarmConfig.from_row(row) if row else None

    def list_farms(self) -> List[FarmConfig]:
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM farms ORDER BY last_active_at DESC").fetchall()
        conn.close()
        return [FarmConfig.from_row(r) for r in rows]

    def update_farm(self, farm_id: str, **kwargs) -> Optional[FarmConfig]:
        """Update farm metadata. Accepts: name, location, description, turbine_spec, wind_profile, grid_profile."""
        farm = self.get_farm(farm_id)
        if not farm:
            return None

        conn = self._get_conn()
        field_map = {
            "name": "name",
            "location": "location",
            "description": "description",
            "turbine_spec": "turbine_spec_json",
            "wind_profile": "wind_profile_json",
            "grid_profile": "grid_profile_json",
            "layout": "layout_json",
        }
        for key, val in kwargs.items():
            col = field_map.get(key)
            if col and val is not None:
                db_val = json.dumps(val) if col.endswith("_json") else val
                conn.execute(f"UPDATE farms SET {col} = ? WHERE farm_id = ?", (db_val, farm_id))
        conn.commit()
        conn.close()

        self._save_config_json(farm_id)
        return self.get_farm(farm_id)

    def delete_farm(self, farm_id: str) -> bool:
        """Delete a farm and its data directory."""
        farm = self.get_farm(farm_id)
        if not farm:
            return False
        conn = self._get_conn()
        conn.execute("DELETE FROM farms WHERE farm_id = ?", (farm_id,))
        conn.commit()
        conn.close()

        farm_dir = self._farms_dir / farm_id
        if farm_dir.exists():
            shutil.rmtree(farm_dir)
        return True

    # ── Active farm ─────────────────────────────────────────────────────

    def get_active_farm_id(self) -> Optional[str]:
        conn = self._get_conn()
        row = conn.execute("SELECT farm_id FROM farms WHERE is_active = 1").fetchone()
        conn.close()
        return row["farm_id"] if row else None

    def set_active_farm(self, farm_id: str) -> bool:
        farm = self.get_farm(farm_id)
        if not farm:
            return False
        now = datetime.now().isoformat()
        conn = self._get_conn()
        conn.execute("UPDATE farms SET is_active = 0 WHERE is_active = 1")
        conn.execute(
            "UPDATE farms SET is_active = 1, last_active_at = ? WHERE farm_id = ?",
            (now, farm_id),
        )
        conn.commit()
        conn.close()
        return True

    # ── Paths ───────────────────────────────────────────────────────────

    def get_farm_db_path(self, farm_id: str) -> Path:
        """Return the SQLite database path for a specific farm."""
        return self._farms_dir / farm_id / "wind_farm.db"

    def get_farm_dir(self, farm_id: str) -> Path:
        return self._farms_dir / farm_id

    # ── Clone ───────────────────────────────────────────────────────────

    def clone_farm(self, source_farm_id: str, new_farm_id: str,
                   new_name: str, include_data: bool = False) -> Optional[FarmConfig]:
        """Clone a farm config (and optionally its data) to a new farm."""
        source = self.get_farm(source_farm_id)
        if not source:
            return None

        new_farm = self.create_farm(
            farm_id=new_farm_id, name=new_name,
            turbine_count=source.turbine_count,
            turbine_spec=source.turbine_spec,
            wind_profile=source.wind_profile,
            grid_profile=source.grid_profile,
            layout=source.layout,
            location=source.location,
            description=f"Cloned from {source_farm_id}",
        )

        if include_data:
            src_db = self.get_farm_db_path(source_farm_id)
            dst_db = self.get_farm_db_path(new_farm_id)
            if src_db.exists():
                shutil.copy2(str(src_db), str(dst_db))

        return new_farm

    # ── Migration ───────────────────────────────────────────────────────

    def migrate_legacy_db(self, legacy_db_path: Path) -> Optional[str]:
        """Wrap an existing wind_farm_data.db as the 'legacy' farm.

        Returns the farm_id if migration occurred, None if already done or no legacy DB.
        """
        if not legacy_db_path.exists():
            return None

        farm_id = "legacy"
        if self.get_farm(farm_id):
            return None

        farm_dir = self._farms_dir / farm_id
        farm_dir.mkdir(parents=True, exist_ok=True)

        dst = farm_dir / "wind_farm.db"
        shutil.move(str(legacy_db_path), str(dst))

        self.create_farm(
            farm_id=farm_id,
            name="既有資料（Legacy）",
            turbine_count=14,
            turbine_spec={},
            description="自動遷移自原始 wind_farm_data.db",
        )
        self.set_active_farm(farm_id)
        return farm_id

    # ── Helpers ──────────────────────────────────────────────────────────

    def _save_config_json(self, farm_id: str):
        farm = self.get_farm(farm_id)
        if not farm:
            return
        config_path = self._farms_dir / farm_id / "config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(farm.to_dict(), indent=2, ensure_ascii=False))

    def ensure_default_farm(self) -> str:
        """Ensure at least one farm exists. Returns the active farm_id."""
        active = self.get_active_farm_id()
        if active:
            return active

        farms = self.list_farms()
        if farms:
            self.set_active_farm(farms[0].farm_id)
            return farms[0].farm_id

        from simulator.physics.turbine_physics import TurbineSpec
        default_spec = TurbineSpec()
        farm = self.create_farm(
            farm_id="default_z72_2mw",
            name="Z72-2000-MV 預設風場",
            turbine_count=14,
            turbine_spec=default_spec.to_dict(),
            description="預設 14 台 Z72 直驅 2MW 風機",
        )
        self.set_active_farm(farm.farm_id)
        return farm.farm_id

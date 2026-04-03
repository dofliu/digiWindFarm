"""
Modbus TCP Simulator Server — exposes physics model data via Modbus registers.

Register map aligned to: docs/1040610-Z72_PLC_OPC_TAG_1040510.xlsx
Sheet: "Modbus標籤對應(from Bachmann)"

Each turbine gets its own Modbus slave ID (1-based).
External SCADA software (WinCC, InTouch, Bachmann M-OPC) can connect directly.

Usage:
    server = ModbusSimServer(port=5020)
    server.start()
    server.update_turbine("WT001", scada_dict)  # called by engine each step
    server.stop()
"""

import threading
import logging
from typing import Dict, Optional, List

from pymodbus.server import StartTcpServer, ModbusTcpServer
from pymodbus.datastore import (
    ModbusDeviceContext,
    ModbusServerContext,
    ModbusSequentialDataBlock,
)

logger = logging.getLogger(__name__)


# ─── Register map: SCADA tag → Modbus HoldingRegister address ───────────
# Based on "Modbus標籤對應(from Bachmann)" sheet
# Values are stored as INT16 (×10 or ×100 scaling for decimals)

# Each entry: (register_address, scada_tag_id, scale_factor, description_zh)
REGISTER_MAP: List[tuple] = [
    # ── Control (Coils 1-6, mapped to HR 1-6 as read-only status) ──
    (1, "_coil_start", 1, "遠端起動命令"),
    (2, "_coil_stop", 1, "遠端停車命令"),
    (3, "_coil_reset", 1, "遠端復位命令"),

    # ── Parameters (HR 100-122) ──
    # These are config values, not live data — skip for now

    # ── Live data (HR 200+) ──
    (224, "WTUR_TurSt", 1, "風機當前狀態 (1-9)"),
    (228, "WROT_RotSpd", 100, "輪轂轉速 (×100 RPM)"),
    (229, "_hub_angle", 1, "輪轂角度"),
    (230, "WROT_PtAngValBl1", 10, "葉片1角度 (×10 deg)"),
    (231, "WROT_PtAngValBl2", 10, "葉片2角度 (×10 deg)"),
    (232, "WROT_PtAngValBl3", 10, "葉片3角度 (×10 deg)"),
    (233, "_pitch_motor_cur1", 10, "變槳電機1電流"),
    (234, "_pitch_motor_cur2", 10, "變槳電機2電流"),
    (235, "_pitch_motor_cur3", 10, "變槳電機3電流"),
    (236, "_overspeed_mon", 100, "超速感測器轉速"),
    (241, "_yaw_state", 1, "偏航狀態 (1-6)"),
    (243, "WYAW_YwVn1AlgnAvg5s", 10, "5秒偏航排列平均值 (×10 deg)"),
    (244, "WNAC_VibMsNacXDir", 100, "X方向振動值 (×100 mm/s)"),
    (245, "WNAC_VibMsNacYDir", 100, "Y方向振動值 (×100 mm/s)"),
    (246, "WYAW_CabWup", 10, "扭纜角度 (×10 turns)"),
    (247, "WYAW_YwBrkHyPrs", 10, "液壓制動壓力 (×10 bar)"),
    (248, "WMET_WSpeedNac", 10, "機艙風速 (×10 m/s)"),
    (249, "_vib_abs", 100, "振動絕對值 (×100)"),
    (250, "_atm_pressure", 10, "大氣壓力 (×10 hPa)"),

    # ── Converter (HR 251-292) ──
    (251, "_cnv_ctrl_state", 1, "變頻器控制狀態"),
    (255, "WGEN_GnCurMs", 1, "變頻器電網側電流 (A)"),  # low 16 bits
    (261, "WGEN_GnVtgMs", 1, "變頻器電網側電壓 (V)"),  # low 16 bits
    (267, "WTUR_TotPwrAt", 1, "變頻器電網側有功功率 (kW)"),  # low 16 bits
    (273, "WCNV_CnvGnPwr", 1, "變頻器發電機側功率 (kW)"),
    (274, "WCNV_CnvGnFrq", 100, "發電機運行頻率 (×100 Hz)"),
    (275, "WGEN_GnCurMs", 1, "發電機電流 (A)"),  # duplicate for compat
    (276, "_gen_torque", 10, "發電機轉矩"),
    (277, "WCNV_CnvCabinTmp", 10, "變頻器入口溫度 (×10 °C)"),
    (278, "_cnv_outlet_tmp", 10, "變頻器出口溫度"),
    (279, "WCNV_IGCTWtrPres1", 10, "變頻器入口壓力 (×10 bar)"),
    (280, "WCNV_IGCTWtrPres2", 10, "變頻器出口壓力 (×10 bar)"),
    (290, "_gen_power_limit", 10, "發電機功率限幅值"),
    (291, "_reactive_power_sp", 10, "無功功率設定值"),
    (292, "_hub_rpm_power_calc", 100, "輪轂轉速功率計算值"),

    # ── Status registers (HR 400-411) ──
    (400, "_cooling_status", 1, "水冷系統狀態"),
    (402, "_cnv_status", 1, "變頻器狀態"),
    (404, "_gen_status", 1, "發電機狀態"),
    (405, "_rotor_status1", 1, "葉輪運行狀態1"),
    (406, "_rotor_status2", 1, "葉輪運行狀態2"),
    (410, "_turbine_run_status", 1, "風機運行狀態"),
    (411, "_yaw_status_bits", 1, "偏航狀態"),

    # ── Temperature registers (HR 501-517) ──
    (501, "WGEN_GnStaTmp1", 10, "發電機定子溫度1 (×10 °C)"),
    (502, "_gen_stator_tmp2", 10, "發電機定子溫度2"),
    (503, "_gen_stator_tmp3", 10, "發電機定子溫度3"),
    (504, "_gen_stator_tmp4", 10, "發電機定子溫度4"),
    (505, "_gen_stator_tmp5", 10, "發電機定子溫度5"),
    (506, "_gen_stator_tmp6", 10, "發電機定子溫度6"),
    (507, "WGEN_GnAirTmp1", 10, "發電機空氣溫度1 (×10 °C)"),
    (508, "_gen_air_tmp2", 10, "發電機空氣溫度2"),
    (509, "WGEN_GnBrgTmp1", 10, "主軸承溫度1 (×10 °C)"),
    (510, "_main_brg_tmp2", 10, "主軸承溫度2"),
    (511, "WROT_RotTmp", 10, "輪轂溫度 (×10 °C)"),
    (512, "WROT_RotCabTmp", 10, "輪轂控制櫃溫度 (×10 °C)"),
    (513, "WNAC_NacTmp", 10, "機艙溫度 (×10 °C)"),
    (514, "WNAC_NacCabTmp", 10, "機艙控制櫃溫度 (×10 °C)"),
    (515, "_cnv_inu_tmp", 10, "變頻器INU溫度"),
    (516, "_cnv_isu_tmp", 10, "變頻器ISU溫度"),
    (517, "WCNV_IGCTWtrTmp", 10, "變頻器INU RMIO溫度 (×10 °C)"),

    # ── Counters (HR 550-553) ──
    (550, "_cable_turns", 10, "扭纜圈數"),
    (551, "_pitch_motor_pwr1", 10, "變槳電機1功率估算"),
    (552, "_pitch_motor_pwr2", 10, "變槳電機2功率估算"),
    (553, "_pitch_motor_pwr3", 10, "變槳電機3功率估算"),

    # ── Event registers (HR 600-634) ──
    # EventWord bit fields — skipped for now, driven by fault engine
]

# Build lookup: register_addr → (scada_tag, scale)
_REG_LOOKUP: Dict[int, tuple] = {}
for addr, tag, scale, _ in REGISTER_MAP:
    if not tag.startswith('_'):
        _REG_LOOKUP[addr] = (tag, scale)

# Max register address needed
_MAX_REG = max(addr for addr, _, _, _ in REGISTER_MAP) + 10


class ModbusSimServer:
    """
    Modbus TCP server backed by the physics engine.

    Each turbine = one slave ID (WT001 → slave 1, WT002 → slave 2, ...).
    All data in Holding Registers (function code 3).
    """

    def __init__(self, port: int = 5020, turbine_count: int = 14):
        self.port = port
        self.turbine_count = turbine_count
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._server: Optional[ModbusTcpServer] = None
        self._server_context: Optional[ModbusServerContext] = None

        # Build device contexts (one per turbine = one slave ID)
        slaves: Dict[int, ModbusDeviceContext] = {}
        for i in range(1, turbine_count + 1):
            hr = ModbusSequentialDataBlock(0, [0] * (_MAX_REG + 1))
            slaves[i] = ModbusDeviceContext(
                di=ModbusSequentialDataBlock(0, [0] * 10),
                co=ModbusSequentialDataBlock(0, [0] * 10),
                hr=hr,
                ir=ModbusSequentialDataBlock(0, [0] * 10),
            )
        self._server_context = ModbusServerContext(devices=slaves, single=False)

    def start(self):
        """Start the Modbus TCP server in a background thread."""
        if self._running:
            return
        self._running = True

        self._thread = threading.Thread(
            target=self._run_server, daemon=True
        )
        self._thread.start()
        logger.info(f"[Modbus] TCP server starting on port {self.port} ({self.turbine_count} slaves)")

    def _run_server(self):
        try:
            StartTcpServer(
                context=self._server_context,
                address=("0.0.0.0", self.port),
            )
        except Exception as e:
            logger.error(f"[Modbus] Server error: {e}")
        finally:
            self._running = False

    def stop(self):
        """Stop the Modbus TCP server."""
        if self._running:
            self._running = False
            from pymodbus.server import ServerStop
            try:
                ServerStop()
            except Exception:
                pass
            logger.info("[Modbus] Server stopped")

    def update_turbine(self, turbine_id: str, scada: Dict[str, float]):
        """
        Update Modbus registers for a turbine from SCADA output dict.

        Args:
            turbine_id: e.g. "WT001" → slave ID 1
            scada: flat dict from TurbinePhysicsModel.step()
        """
        if not self._server_context:
            return

        try:
            slave_id = int(turbine_id.replace("WT", ""))
        except ValueError:
            return

        try:
            ctx = self._server_context[slave_id]
        except Exception:
            return

        hr = ctx.store['h']  # holding registers

        for addr, (tag, scale) in _REG_LOOKUP.items():
            val = scada.get(tag)
            if val is not None:
                # Scale and clamp to INT16 range
                scaled = int(round(val * scale))
                scaled = max(-32768, min(32767, scaled))
                # pymodbus uses unsigned, convert signed to unsigned
                if scaled < 0:
                    scaled = scaled + 65536
                try:
                    hr.setValues(addr, [scaled])
                except Exception:
                    pass

        # Also fill in derived values from SCADA data
        # Vibration absolute = sqrt(x² + y²)
        vx = scada.get("WNAC_VibMsNacXDir", 0)
        vy = scada.get("WNAC_VibMsNacYDir", 0)
        vib_abs = (vx**2 + vy**2) ** 0.5
        try:
            hr.setValues(249, [int(round(vib_abs * 100))])
        except Exception:
            pass

    def get_status(self) -> dict:
        return {
            "running": self._running,
            "port": self.port,
            "turbine_count": self.turbine_count,
            "register_count": len(REGISTER_MAP),
        }

    @property
    def is_running(self) -> bool:
        return self._running

    @staticmethod
    def get_register_map() -> List[dict]:
        """Return the register map for documentation/API."""
        return [
            {
                "address": addr,
                "scada_tag": tag if not tag.startswith('_') else None,
                "internal_name": tag if tag.startswith('_') else None,
                "scale": scale,
                "description": desc,
            }
            for addr, tag, scale, desc in REGISTER_MAP
        ]

"""
Fault Simulation Engine — gradual degradation patterns for analyst diagnostics.

Design principles:
1. Faults develop GRADUALLY over hours/days (not sudden jumps)
2. Each fault affects MULTIPLE correlated tags (physically realistic)
3. Severity increases over time → triggers alarm thresholds → trip
4. Historical trend data is analyzable for health assessment

Based on alarm codes from: docs/1040610-Z72_PLC_OPC_TAG_1040510.xlsx
Sheet: "警告訊息列表"

Usage:
    engine = FaultEngine()
    engine.inject("bearing_wear", target_turbine="WT003", severity_rate=0.001)
    # Each physics step:
    modifiers = engine.step(dt=1.0)
    turbine_model.fault_modifiers = modifiers.get("WT003", {})
"""

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime


class FaultPhase(str, Enum):
    """Fault lifecycle phases visible in trend data."""
    INCIPIENT = "incipient"      # Early: subtle changes, hard to detect
    DEVELOPING = "developing"     # Growing: detectable by monitoring
    ADVANCED = "advanced"         # Severe: alarm thresholds exceeded
    CRITICAL = "critical"         # Trip imminent or occurred


@dataclass
class FaultScenario:
    """
    Definition of a fault type and how it affects SCADA tags over time.

    Each fault has:
    - affected_tags: dict mapping tag_id → (max_offset, phase_curve_type)
    - alarm_codes: which Bachmann alarm/trip codes this fault triggers
    - severity: 0.0 (no fault) → 1.0 (full severity, trip condition)
    """
    id: str
    name_en: str
    name_zh: str
    description_en: str
    description_zh: str
    affected_tags: Dict[str, Dict]  # tag_id → {max_offset, curve}
    alarm_codes: List[Dict]         # [{type: "T1"|"T2"|"A", code: int, threshold: float}]
    auto_trip_severity: float = 0.85  # severity at which turbine trips


# ─── Pre-defined fault scenarios ──────────────────────────────────────────

FAULT_SCENARIOS: Dict[str, FaultScenario] = {

    "bearing_wear": FaultScenario(
        id="bearing_wear",
        name_en="Generator Bearing Wear",
        name_zh="發電機軸承磨損",
        description_en="Gradual bearing degradation causing increased temperature and vibration",
        description_zh="軸承逐漸磨損，導致溫度和振動逐步上升",
        affected_tags={
            "WGEN_GnBrgTmp1": {"max_offset": 45.0, "curve": "exponential"},
            "WNAC_VibMsNacXDir": {"max_offset": 8.0, "curve": "exponential"},
            "WNAC_VibMsNacYDir": {"max_offset": 6.0, "curve": "exponential"},
            "WGEN_GnStaTmp1": {"max_offset": 15.0, "curve": "linear"},
            "WGEN_GnAirTmp1": {"max_offset": 10.0, "curve": "linear"},
        },
        alarm_codes=[
            {"type": "A", "code": 300, "threshold": 0.4, "desc": "Generator bearing temp high"},
            {"type": "T2", "code": 301, "threshold": 0.7, "desc": "Generator bearing temp very high"},
            {"type": "T1", "code": 302, "threshold": 0.85, "desc": "Generator bearing failure trip"},
        ],
    ),

    "gearbox_overheat": FaultScenario(
        id="gearbox_overheat",
        name_en="Gearbox Overheating",
        name_zh="齒輪箱過熱",
        description_en="Oil degradation or cooling failure causing gearbox temperature rise",
        description_zh="潤滑油劣化或冷卻系統故障，導致齒輪箱溫度持續上升",
        affected_tags={
            "WNAC_NacTmp": {"max_offset": 20.0, "curve": "logarithmic"},
            "WNAC_VibMsNacXDir": {"max_offset": 5.0, "curve": "linear"},
            "WNAC_VibMsNacYDir": {"max_offset": 4.0, "curve": "linear"},
            "WCNV_CnvCabinTmp": {"max_offset": 8.0, "curve": "linear"},
        },
        alarm_codes=[
            {"type": "A", "code": 270, "desc": "Gearbox temperature high"},
            {"type": "T2", "code": 271, "threshold": 0.6, "desc": "Gearbox oil temp very high"},
            {"type": "T1", "code": 272, "threshold": 0.85, "desc": "Gearbox trip"},
        ],
    ),

    "pitch_motor_fault": FaultScenario(
        id="pitch_motor_fault",
        name_en="Pitch Motor Degradation (Blade 1)",
        name_zh="葉片1變槳馬達劣化",
        description_en="Blade 1 pitch motor losing accuracy, causing asymmetric pitch angles",
        description_zh="1號葉片變槳馬達精度下降，造成三片葉片角度不對稱",
        affected_tags={
            "WROT_PtAngValBl1": {"max_offset": 8.0, "curve": "linear"},
            "WNAC_VibMsNacXDir": {"max_offset": 3.0, "curve": "quadratic"},
            "WNAC_VibMsNacYDir": {"max_offset": 2.0, "curve": "quadratic"},
            "WTUR_TotPwrAt": {"max_offset": -500.0, "curve": "linear"},
        },
        alarm_codes=[
            {"type": "A", "code": 310, "threshold": 0.3, "desc": "Pitch angle deviation blade 1"},
            {"type": "T1", "code": 311, "threshold": 0.7, "desc": "Pitch system fault blade 1"},
        ],
    ),

    "converter_cooling_fault": FaultScenario(
        id="converter_cooling_fault",
        name_en="Converter Cooling System Fault",
        name_zh="變頻器冷卻系統故障",
        description_en="IGCT water cooling degradation causing converter overheating",
        description_zh="IGCT水冷系統劣化，變頻器溫度持續上升",
        affected_tags={
            "WCNV_IGCTWtrTmp": {"max_offset": 30.0, "curve": "exponential"},
            "WCNV_IGCTWtrPres1": {"max_offset": -2.0, "curve": "linear"},
            "WCNV_IGCTWtrPres2": {"max_offset": -2.0, "curve": "linear"},
            "WCNV_CnvCabinTmp": {"max_offset": 25.0, "curve": "exponential"},
            "WCNV_CnvGnPwr": {"max_offset": -300.0, "curve": "linear"},
            "WTUR_TotPwrAt": {"max_offset": -300.0, "curve": "linear"},
        },
        alarm_codes=[
            {"type": "A", "code": 32, "desc": "Converter cooling warning"},
            {"type": "T1", "code": 21, "threshold": 0.8, "desc": "Turbine trip from converter"},
        ],
    ),

    "yaw_misalignment": FaultScenario(
        id="yaw_misalignment",
        name_en="Yaw System Misalignment",
        name_zh="轉向系統偏差",
        description_en="Yaw sensor drift causing persistent wind misalignment and power loss",
        description_zh="轉向感測器漂移，導致持續性風向偏差及功率損失",
        affected_tags={
            "WYAW_YwVn1AlgnAvg5s": {"max_offset": 25.0, "curve": "linear"},
            "WTUR_TotPwrAt": {"max_offset": -800.0, "curve": "quadratic"},
            "WGEN_GnPwrMs": {"max_offset": -800.0, "curve": "quadratic"},
            "WYAW_YwBrkHyPrs": {"max_offset": -40.0, "curve": "linear"},
        },
        alarm_codes=[
            {"type": "A", "code": 400, "threshold": 0.4, "desc": "Yaw alignment warning"},
            {"type": "T2", "code": 401, "threshold": 0.7, "desc": "Yaw system fault"},
        ],
    ),

    "generator_overspeed": FaultScenario(
        id="generator_overspeed",
        name_en="Generator Overspeed",
        name_zh="發電機超速",
        description_en="Control system failure allowing rotor/generator overspeed",
        description_zh="控制系統失效導致發電機超速",
        affected_tags={
            "WROT_RotSpd": {"max_offset": 5.0, "curve": "exponential"},
            "WGEN_GnSpd": {"max_offset": 500.0, "curve": "exponential"},
            "WNAC_VibMsNacXDir": {"max_offset": 12.0, "curve": "exponential"},
            "WNAC_VibMsNacYDir": {"max_offset": 10.0, "curve": "exponential"},
        },
        alarm_codes=[
            {"type": "T1", "code": 27, "threshold": 0.5, "desc": "Generator overspeed"},
        ],
        auto_trip_severity=0.6,
    ),

    "transformer_overheat": FaultScenario(
        id="transformer_overheat",
        name_en="Transformer Overheating",
        name_zh="變壓器過熱",
        description_en="Transformer cooling degradation causing gradual temperature rise",
        description_zh="變壓器冷卻效能下降，溫度逐漸升高",
        affected_tags={
            "WGDC_TrfCoreTmp": {"max_offset": 50.0, "curve": "logarithmic"},
            "WNAC_NacTmp": {"max_offset": 5.0, "curve": "linear"},
        },
        alarm_codes=[
            {"type": "A", "code": 350, "threshold": 0.4, "desc": "Transformer temp high"},
            {"type": "T2", "code": 351, "threshold": 0.75, "desc": "Transformer temp very high"},
        ],
    ),
}


@dataclass
class ActiveFault:
    """An active fault instance on a specific turbine."""
    scenario_id: str
    turbine_id: str
    severity: float = 0.0                # 0.0 → 1.0
    severity_rate: float = 0.0002        # per second (~0.72/hour = ~18 hours to full)
    started_at: Optional[datetime] = None
    tripped: bool = False
    active_alarms: List[Dict] = field(default_factory=list)


class FaultEngine:
    """
    Manages fault injection across all turbines.

    Faults progress gradually:
      severity += severity_rate * dt   (each simulation step)

    Severity curves control how each tag is affected:
      linear:      offset = max_offset * severity
      quadratic:   offset = max_offset * severity²
      exponential: offset = max_offset * (e^(3*severity) - 1) / (e³ - 1)
      logarithmic: offset = max_offset * ln(1 + severity*e) / ln(1+e)
    """

    def __init__(self):
        self._active_faults: List[ActiveFault] = []

    @property
    def active_faults(self) -> List[ActiveFault]:
        return list(self._active_faults)

    def get_scenarios(self) -> Dict[str, FaultScenario]:
        return dict(FAULT_SCENARIOS)

    def inject(self, scenario_id: str, turbine_id: str,
               severity_rate: float = 0.0002,
               initial_severity: float = 0.0) -> bool:
        """
        Inject a fault into a specific turbine.

        Args:
            scenario_id: One of FAULT_SCENARIOS keys
            turbine_id: e.g. "WT003"
            severity_rate: How fast severity grows per second
                          0.0002 = ~18 hours to full (slow, realistic)
                          0.001  = ~3.6 hours to full (fast demo)
                          0.01   = ~20 min to full (very fast demo)
            initial_severity: Start severity (0.0 = beginning, 0.5 = mid-fault)
        """
        if scenario_id not in FAULT_SCENARIOS:
            return False

        # Remove existing fault of same type on same turbine
        self._active_faults = [
            f for f in self._active_faults
            if not (f.scenario_id == scenario_id and f.turbine_id == turbine_id)
        ]

        self._active_faults.append(ActiveFault(
            scenario_id=scenario_id,
            turbine_id=turbine_id,
            severity=initial_severity,
            severity_rate=severity_rate,
            started_at=datetime.now(),
        ))
        return True

    def clear(self, turbine_id: Optional[str] = None,
              scenario_id: Optional[str] = None):
        """Remove active faults. If no args, clears all."""
        if turbine_id is None and scenario_id is None:
            self._active_faults.clear()
            return

        self._active_faults = [
            f for f in self._active_faults
            if not ((turbine_id is None or f.turbine_id == turbine_id) and
                    (scenario_id is None or f.scenario_id == scenario_id))
        ]

    def step(self, dt: float = 1.0) -> Dict[str, Dict[str, float]]:
        """
        Advance all active faults by dt seconds.

        Returns:
            {turbine_id: {tag_id: offset_value}} for all affected turbines.
        """
        result: Dict[str, Dict[str, float]] = {}

        for fault in self._active_faults:
            if fault.tripped:
                continue

            # Progress severity
            fault.severity = min(1.0, fault.severity + fault.severity_rate * dt)

            scenario = FAULT_SCENARIOS.get(fault.scenario_id)
            if not scenario:
                continue

            # Check alarm thresholds
            fault.active_alarms = []
            for alarm in scenario.alarm_codes:
                threshold = alarm.get("threshold", 0.3)
                if fault.severity >= threshold:
                    fault.active_alarms.append(alarm)

            # Auto-trip
            if fault.severity >= scenario.auto_trip_severity:
                fault.tripped = True

            # Calculate tag offsets
            modifiers = result.setdefault(fault.turbine_id, {})
            for tag_id, params in scenario.affected_tags.items():
                max_offset = params["max_offset"]
                curve = params.get("curve", "linear")
                offset = self._apply_curve(fault.severity, max_offset, curve)

                # Accumulate if multiple faults affect the same tag
                modifiers[tag_id] = modifiers.get(tag_id, 0) + offset

        return result

    def get_fault_status(self) -> List[Dict]:
        """Return status of all active faults (for API/frontend)."""
        statuses = []
        for fault in self._active_faults:
            scenario = FAULT_SCENARIOS.get(fault.scenario_id)
            phase = self._severity_to_phase(fault.severity)
            statuses.append({
                "scenario_id": fault.scenario_id,
                "turbine_id": fault.turbine_id,
                "name_en": scenario.name_en if scenario else "",
                "name_zh": scenario.name_zh if scenario else "",
                "severity": round(fault.severity, 4),
                "phase": phase.value,
                "tripped": fault.tripped,
                "active_alarms": fault.active_alarms,
                "started_at": fault.started_at.isoformat() if fault.started_at else None,
            })
        return statuses

    @staticmethod
    def _apply_curve(severity: float, max_offset: float, curve: str) -> float:
        """Map severity (0→1) to offset using the specified curve shape."""
        s = max(0.0, min(1.0, severity))
        if curve == "linear":
            return max_offset * s
        elif curve == "quadratic":
            return max_offset * s * s
        elif curve == "exponential":
            # Slow start, rapid end — mimics real degradation
            return max_offset * (math.exp(3 * s) - 1) / (math.exp(3) - 1)
        elif curve == "logarithmic":
            # Fast start, plateaus — mimics saturation effects
            e = math.e
            return max_offset * math.log(1 + s * e) / math.log(1 + e)
        return max_offset * s

    @staticmethod
    def _severity_to_phase(severity: float) -> FaultPhase:
        if severity < 0.2:
            return FaultPhase.INCIPIENT
        elif severity < 0.5:
            return FaultPhase.DEVELOPING
        elif severity < 0.8:
            return FaultPhase.ADVANCED
        return FaultPhase.CRITICAL

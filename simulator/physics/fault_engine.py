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

    # ══════════════════════════════════════════════════════════════════
    # 1. OBVIOUS FAULTS — clear threshold violations, easy to detect
    # ══════════════════════════════════════════════════════════════════

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
            {"type": "A", "code": 262, "threshold": 0.4, "desc": "Main bearing 1 temperature high (85°C)"},
            {"type": "T1", "code": 240, "threshold": 0.7, "desc": "Bearing 1 temperature very high (95°C)"},
            {"type": "T1", "code": 241, "threshold": 0.85, "desc": "Bearing failure trip"},
        ],
    ),

    "generator_overspeed": FaultScenario(
        id="generator_overspeed",
        name_en="Generator Overspeed",
        name_zh="發電機超速",
        description_en="Control system failure allowing rotor/generator overspeed (Z72 Event 027/041)",
        description_zh="控制系統失效導致發電機超速（Z72事件027/041）",
        affected_tags={
            "WROT_RotSpd": {"max_offset": 5.0, "curve": "exponential"},
            "WGEN_GnSpd": {"max_offset": 5.0, "curve": "exponential"},
            "WNAC_VibMsNacXDir": {"max_offset": 12.0, "curve": "exponential"},
            "WNAC_VibMsNacYDir": {"max_offset": 10.0, "curve": "exponential"},
        },
        alarm_codes=[
            {"type": "T1", "code": 41, "threshold": 0.4, "desc": "Rotor speed very high"},
            {"type": "T1", "code": 27, "threshold": 0.5, "desc": "Generator overspeed (28.5 RPM)"},
        ],
        auto_trip_severity=0.6,
    ),

    "converter_cooling_fault": FaultScenario(
        id="converter_cooling_fault",
        name_en="Converter Cooling System Fault",
        name_zh="變頻器冷卻系統故障",
        description_en="IGCT water cooling degradation causing converter overheating (Z72 Event 021)",
        description_zh="IGCT水冷系統劣化，變頻器溫度持續上升（Z72事件021）",
        affected_tags={
            "WCNV_IGCTWtrTmp": {"max_offset": 30.0, "curve": "exponential"},
            "WCNV_IGCTWtrPres1": {"max_offset": -2.0, "curve": "linear"},
            "WCNV_IGCTWtrPres2": {"max_offset": -2.0, "curve": "linear"},
            "WCNV_CnvCabinTmp": {"max_offset": 25.0, "curve": "exponential"},
            "WCNV_CnvGnPwr": {"max_offset": -300.0, "curve": "linear"},
            "WTUR_TotPwrAt": {"max_offset": -300.0, "curve": "linear"},
        },
        alarm_codes=[
            {"type": "A", "code": 32, "threshold": 0.3, "desc": "Converter cooling warning"},
            {"type": "T1", "code": 21, "threshold": 0.8, "desc": "Turbine trip request from converter"},
        ],
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

    # ══════════════════════════════════════════════════════════════════
    # 2. SUBTLE FAULTS — gradual, cross-correlated, hard to detect
    #    These test whether a diagnosis system can catch early anomalies
    # ══════════════════════════════════════════════════════════════════

    "pitch_imbalance": FaultScenario(
        id="pitch_imbalance",
        name_en="Blade Pitch Imbalance (Subtle)",
        name_zh="葉片旋角不平衡（細微）",
        description_en="Blade 1 pitch motor has slight calibration drift. Causes 1P vibration increase and small power loss. Hard to detect from individual tags — requires cross-correlation analysis.",
        description_zh="1號葉片變槳馬達校準微小偏移。造成1P振動增加和微量功率損失。單一標籤難以偵測，需要交叉關聯分析。",
        affected_tags={
            "WROT_PtAngValBl1": {"max_offset": 3.0, "curve": "logarithmic"},    # small drift
            "WNAC_VibMsNacXDir": {"max_offset": 1.5, "curve": "quadratic"},     # subtle 1P vib
            "WNAC_VibMsNacYDir": {"max_offset": 0.8, "curve": "quadratic"},
            "WTUR_TotPwrAt": {"max_offset": -80.0, "curve": "quadratic"},       # tiny power loss
            "WGEN_GnBrgTmp1": {"max_offset": 3.0, "curve": "linear"},           # slight bearing heat
        },
        alarm_codes=[
            {"type": "A", "code": 43, "threshold": 0.6, "desc": "Pitch angle error blade 1"},
            {"type": "T1", "code": 311, "threshold": 0.85, "desc": "Pitch system fault blade 1"},
        ],
        auto_trip_severity=0.90,  # takes longer to trip
    ),

    "yaw_sensor_drift": FaultScenario(
        id="yaw_sensor_drift",
        name_en="Yaw Sensor Drift (Subtle)",
        name_zh="偏航感測器漂移（細微）",
        description_en="Yaw position sensor slowly drifting. Turbine tracks wind with increasing offset. Power drops subtly relative to wind speed — detectable by comparing power curve to neighbors.",
        description_zh="偏航位置感測器緩慢漂移。風機追風角度逐漸偏移。功率相對風速微量下降 — 可透過與鄰近風機功率曲線比較來發現。",
        affected_tags={
            "WYAW_YwVn1AlgnAvg5s": {"max_offset": 12.0, "curve": "logarithmic"},
            "WTUR_TotPwrAt": {"max_offset": -200.0, "curve": "quadratic"},
            "WGEN_GnPwrMs": {"max_offset": -200.0, "curve": "quadratic"},
        },
        alarm_codes=[
            {"type": "A", "code": 223, "threshold": 0.7, "desc": "Yaw timeout"},
        ],
        auto_trip_severity=0.95,
    ),

    "stator_winding_degradation": FaultScenario(
        id="stator_winding_degradation",
        name_en="Stator Winding Insulation Degradation (Subtle)",
        name_zh="定子繞組絕緣劣化（細微）",
        description_en="Insulation resistance slowly decreasing. Stator temperature rises slightly faster under load. Only visible by comparing temperature-vs-power slopes over weeks. Air gap temp also affected.",
        description_zh="絕緣電阻緩慢下降。定子溫度在負載下升溫稍快。需要比較數週的溫度-功率斜率才能發現。氣隙溫度也受影響。",
        affected_tags={
            "WGEN_GnStaTmp1": {"max_offset": 20.0, "curve": "exponential"},    # key signal
            "WGEN_GnAirTmp1": {"max_offset": 8.0, "curve": "linear"},          # secondary
            "WGEN_GnCurMs": {"max_offset": 15.0, "curve": "linear"},           # slight current increase
        },
        alarm_codes=[
            {"type": "A", "code": 264, "threshold": 0.5, "desc": "Generator stator temperature 1 high (140°C)"},
            {"type": "T1", "code": 244, "threshold": 0.8, "desc": "Generator stator temperature 1 very high (150°C)"},
        ],
        auto_trip_severity=0.85,
    ),

    "hydraulic_leak": FaultScenario(
        id="hydraulic_leak",
        name_en="Yaw Brake Hydraulic Leak (Subtle)",
        name_zh="偏航煞車液壓洩漏（細微）",
        description_en="Slow hydraulic fluid leak in yaw brake system. Pressure drops gradually over days. Causes intermittent yaw slippage under high wind loads — visible as increased yaw error variance.",
        description_zh="偏航煞車系統液壓油緩慢洩漏。壓力在數天內逐漸下降。高風載下偶發偏航滑移 — 表現為偏航誤差變異增大。",
        affected_tags={
            "WYAW_YwBrkHyPrs": {"max_offset": -80.0, "curve": "linear"},       # slow pressure drop
            "WYAW_YwVn1AlgnAvg5s": {"max_offset": 5.0, "curve": "quadratic"},  # increased yaw error
            "WYAW_CabWup": {"max_offset": 0.8, "curve": "linear"},             # slight cable drift
        },
        alarm_codes=[
            {"type": "A", "code": 260, "threshold": 0.3, "desc": "Yaw brake pressure low (170 bar)"},
            {"type": "A", "code": 261, "threshold": 0.5, "desc": "Yaw brake oil leakage detected"},
            {"type": "T1", "code": 228, "threshold": 0.8, "desc": "Yaw brake pressure very low (150 bar)"},
        ],
    ),

    "blade_icing": FaultScenario(
        id="blade_icing",
        name_en="Blade Icing (Environmental)",
        name_zh="葉片結冰（環境因素）",
        description_en="Ice accumulation on blades. Causes aerodynamic imbalance: power drops, vibration increases asymmetrically, rotor speed fluctuates. Self-resolves with temperature rise.",
        description_zh="葉片上冰層累積。造成空氣動力不平衡：功率下降、振動不對稱增加、轉速波動。溫度升高後自行解除。",
        affected_tags={
            "WTUR_TotPwrAt": {"max_offset": -400.0, "curve": "logarithmic"},
            "WROT_RotSpd": {"max_offset": -3.0, "curve": "logarithmic"},
            "WNAC_VibMsNacXDir": {"max_offset": 4.0, "curve": "linear"},
            "WNAC_VibMsNacYDir": {"max_offset": 6.0, "curve": "linear"},      # asymmetric!
            "WROT_PtAngValBl1": {"max_offset": 2.0, "curve": "linear"},        # pitch compensating
            "WROT_PtAngValBl2": {"max_offset": 0.5, "curve": "linear"},
            "WROT_PtAngValBl3": {"max_offset": 0.3, "curve": "linear"},
        },
        alarm_codes=[
            {"type": "A", "code": 42, "threshold": 0.3, "desc": "Pitch control output limited"},
            {"type": "T1", "code": 236, "threshold": 0.8, "desc": "Tower vibration very high"},
        ],
    ),

    "grid_voltage_sag": FaultScenario(
        id="grid_voltage_sag",
        name_en="Grid Voltage Instability (External)",
        name_zh="電網電壓不穩（外部因素）",
        description_en="Grid voltage fluctuations causing converter stress. DC link voltage oscillates, power output limited. Subtle: converter cabinet temp rises due to increased switching losses.",
        description_zh="電網電壓波動造成變頻器壓力。直流電壓振盪，功率輸出受限。細微：變頻器櫃溫因開關損耗增加而升高。",
        affected_tags={
            "WCNV_CnvDClVtg": {"max_offset": -200.0, "curve": "linear"},
            "WCNV_CnvCabinTmp": {"max_offset": 8.0, "curve": "linear"},
            "WTUR_TotPwrAt": {"max_offset": -150.0, "curve": "quadratic"},
            "WCNV_CnvGnFrq": {"max_offset": -0.5, "curve": "linear"},
        },
        alarm_codes=[
            {"type": "A", "code": 30, "threshold": 0.4, "desc": "Grid voltage deviation"},
            {"type": "T1", "code": 24, "threshold": 0.85, "desc": "Grid circuit breaker open"},
        ],
    ),

    # ══════════════════════════════════════════════════════════════════
    # 3. COMPOUND FAULTS — multiple simultaneous issues (hardest to diagnose)
    # ══════════════════════════════════════════════════════════════════

    "nacelle_cooling_failure": FaultScenario(
        id="nacelle_cooling_failure",
        name_en="Nacelle Cooling System Failure (Compound)",
        name_zh="機艙冷卻系統故障（複合型）",
        description_en="Main nacelle ventilation failure. Multiple component temperatures rise together but at different rates. Challenging to isolate root cause from individual component monitoring.",
        description_zh="主要機艙通風失效。多個組件溫度一起上升但速率不同。從個別組件監控難以確定根因。",
        affected_tags={
            "WNAC_NacTmp": {"max_offset": 20.0, "curve": "logarithmic"},
            "WNAC_NacCabTmp": {"max_offset": 18.0, "curve": "logarithmic"},
            "WGEN_GnStaTmp1": {"max_offset": 12.0, "curve": "linear"},
            "WGEN_GnBrgTmp1": {"max_offset": 8.0, "curve": "linear"},
            "WCNV_CnvCabinTmp": {"max_offset": 10.0, "curve": "linear"},
            "WCNV_IGCTWtrTmp": {"max_offset": 5.0, "curve": "linear"},
        },
        alarm_codes=[
            {"type": "A", "code": 256, "threshold": 0.4, "desc": "Nacelle cabinet temperature outside range"},
            {"type": "T1", "code": 273, "threshold": 0.7, "desc": "Nacelle temperature very high (50°C)"},
            {"type": "T1", "code": 258, "threshold": 0.9, "desc": "Nacelle smoke detected"},
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
        """List of currently active fault instances across all turbines."""
        return list(self._active_faults)

    def get_scenarios(self) -> Dict[str, FaultScenario]:
        """Return the full catalog of available fault scenarios."""
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


# ─── Pre-defined Test Plans ──────────────────────────────────────────────
# Each plan is a sequence of fault injections with timing offsets (seconds).
# Used by the API to auto-inject faults during bulk data generation.

@dataclass
class TestPlanStep:
    """One step in a fault injection test plan."""
    offset_seconds: float       # when to inject (relative to plan start)
    scenario_id: str            # which fault
    turbine_id: str             # which turbine
    severity_rate: float        # how fast it develops
    initial_severity: float = 0.0
    description: str = ""


TEST_PLANS: Dict[str, Dict] = {

    "basic_validation": {
        "name_en": "Basic Validation (4 hours)",
        "name_zh": "基本驗證（4小時）",
        "description_en": "One obvious fault per turbine type. Good for quick functional testing.",
        "description_zh": "每種故障各一台。適合快速功能驗證。",
        "duration_hours": 4,
        "steps": [
            TestPlanStep(0,     "bearing_wear",          "WT001", 0.002,  0.0, "Obvious bearing wear on WT001"),
            TestPlanStep(3600,  "converter_cooling_fault","WT003", 0.002,  0.0, "Converter fault on WT003"),
            TestPlanStep(7200,  "generator_overspeed",   "WT005", 0.005,  0.0, "Overspeed on WT005"),
        ],
    },

    "subtle_challenge": {
        "name_en": "Subtle Fault Challenge (24 hours)",
        "name_zh": "細微故障挑戰（24小時）",
        "description_en": "Mix of very slow-developing faults. Tests whether diagnosis can detect incipient failures before alarms trigger.",
        "description_zh": "多種極緩慢發展的故障混合。測試診斷系統能否在警報觸發前偵測初期異常。",
        "duration_hours": 24,
        "steps": [
            TestPlanStep(0,      "stator_winding_degradation", "WT002", 0.00005, 0.0, "Very slow stator degradation"),
            TestPlanStep(7200,   "yaw_sensor_drift",           "WT004", 0.00008, 0.0, "Slow yaw drift"),
            TestPlanStep(14400,  "hydraulic_leak",             "WT006", 0.00006, 0.0, "Very slow hydraulic leak"),
            TestPlanStep(21600,  "pitch_imbalance",            "WT008", 0.00004, 0.0, "Barely detectable pitch drift"),
        ],
    },

    "mixed_difficulty": {
        "name_en": "Mixed Difficulty (48 hours)",
        "name_zh": "混合難度（48小時）",
        "description_en": "Combination of obvious, subtle, and environmental faults across multiple turbines. Realistic scenario for comprehensive diagnosis testing.",
        "description_zh": "明顯、細微和環境故障的組合，分布在多台風機。適合全面性診斷測試的真實場景。",
        "duration_hours": 48,
        "steps": [
            # Hour 0-6: Subtle faults start
            TestPlanStep(0,      "stator_winding_degradation", "WT002", 0.00003, 0.0, "Very slow insulation degradation"),
            TestPlanStep(1800,   "hydraulic_leak",             "WT007", 0.00005, 0.0, "Slow hydraulic leak"),
            # Hour 6-12: Environmental event
            TestPlanStep(21600,  "blade_icing",                "WT001", 0.0004,  0.0, "Icing event (environmental)"),
            TestPlanStep(21600,  "blade_icing",                "WT002", 0.0003,  0.0, "Icing (different rate)"),
            TestPlanStep(21600,  "blade_icing",                "WT003", 0.0005,  0.0, "Icing (worst)"),
            # Hour 12-24: More subtle faults
            TestPlanStep(43200,  "yaw_sensor_drift",           "WT010", 0.00006, 0.0, "Slow yaw drift"),
            TestPlanStep(50400,  "pitch_imbalance",            "WT012", 0.00004, 0.0, "Subtle pitch imbalance"),
            # Hour 24-36: Obvious fault
            TestPlanStep(86400,  "bearing_wear",               "WT005", 0.001,   0.0, "Clear bearing degradation"),
            TestPlanStep(93600,  "converter_cooling_fault",    "WT009", 0.0008,  0.0, "Converter cooling issue"),
            # Hour 36-48: Compound fault
            TestPlanStep(129600, "nacelle_cooling_failure",    "WT003", 0.0006,  0.0, "Nacelle cooling compound"),
            TestPlanStep(136800, "grid_voltage_sag",           "WT011", 0.0005,  0.0, "Grid instability"),
        ],
    },

    "stress_test": {
        "name_en": "Stress Test (72 hours)",
        "name_zh": "壓力測試（72小時）",
        "description_en": "High fault density — multiple simultaneous faults on different turbines with varying speeds. Tests diagnosis system under heavy load.",
        "description_zh": "高故障密度 — 多台風機同時出現不同速率的故障。測試診斷系統在重負載下的表現。",
        "duration_hours": 72,
        "steps": [
            TestPlanStep(0,      "bearing_wear",               "WT001", 0.0003),
            TestPlanStep(0,      "yaw_sensor_drift",           "WT003", 0.0001),
            TestPlanStep(3600,   "pitch_imbalance",            "WT005", 0.00008),
            TestPlanStep(3600,   "stator_winding_degradation", "WT007", 0.00005),
            TestPlanStep(7200,   "hydraulic_leak",             "WT009", 0.0001),
            TestPlanStep(7200,   "converter_cooling_fault",    "WT011", 0.0005),
            TestPlanStep(14400,  "blade_icing",                "WT002", 0.0005),
            TestPlanStep(14400,  "nacelle_cooling_failure",    "WT004", 0.0004),
            TestPlanStep(21600,  "grid_voltage_sag",           "WT006", 0.0003),
            TestPlanStep(21600,  "transformer_overheat",       "WT008", 0.0002),
            TestPlanStep(43200,  "bearing_wear",               "WT010", 0.0005),
            TestPlanStep(43200,  "generator_overspeed",        "WT012", 0.002),
            TestPlanStep(86400,  "converter_cooling_fault",    "WT013", 0.001),
            TestPlanStep(86400,  "nacelle_cooling_failure",    "WT014", 0.0008),
        ],
    },
}

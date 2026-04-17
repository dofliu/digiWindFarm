"""
SCADA Tag Registry — single source of truth for all data point definitions.

Maps internal tag IDs to:
  - OPC DA tag name (Bachmann Z72 format)
  - Modbus register address
  - Data type and unit
  - i18n labels (en / zh-TW)
  - Valid range for simulation

Based on: docs/1040610-Z72_PLC_OPC_TAG_1040510.xlsx
Sheet: "簡化-每部風力機頁面顯示" + "Modbus標籤對應(from Bachmann)"
"""

from dataclasses import dataclass
from typing import Optional, Dict, List


@dataclass(frozen=True)
class ScadaTag:
    """Definition of a single SCADA data point."""
    id: str                    # Internal key, e.g. "WGEN_GnPwrMs"
    opc_tag: str               # Bachmann OPC tag suffix
    subsystem: str             # WCNV, WGDC, WGEN, WMET, WNAC, WROT, WTUR, WYAW, WSRV, MBUS
    data_type: str             # REAL32, SINT16, UINT16, BOOL
    unit: str                  # kW, RPM, °C, m/s, deg, bar, mm/s, V, A, Hz, ...
    label_en: str              # English label
    label_zh: str              # 繁體中文標籤
    sim_min: float = 0.0       # Simulation valid range min
    sim_max: float = 100.0     # Simulation valid range max
    modbus_reg: Optional[str] = None  # e.g. "HldReg[228]"
    is_display: bool = True    # Show on per-turbine dashboard


# ─── Registry ──────────────────────────────────────────────────────────────

_TAGS: List[ScadaTag] = [
    # ══════════════════════════════════════════════════════════════════════
    # WTUR — Wind Turbine (whole machine)
    # ══════════════════════════════════════════════════════════════════════
    ScadaTag("WTUR_TurSt", "WTUR.Z72PLC__UI_Loc_WTUR_State_TurSt",
             "WTUR", "SINT16", "", "Turbine State", "風力機運轉狀態",
             1, 9, "HldReg[224]"),
    ScadaTag("WTUR_TotPwrAt", "WTUR.Z72PLC__UI_Loc_WTUR_Analogue_TotPwrAt",
             "WTUR", "REAL32", "kW", "Total Active Power", "風力機發電量(功率)",
             0, 5500, "HldReg[267]"),

    # ══════════════════════════════════════════════════════════════════════
    # WGEN — Generator
    # ══════════════════════════════════════════════════════════════════════
    ScadaTag("WGEN_GnPwrMs", "WGEN.Z72PLC__UI_Loc_WGEN_Analogue_GnPwrMs",
             "WGEN", "REAL32", "kW", "Generator Power", "發電機發電量(功率)",
             0, 5500),
    ScadaTag("WGEN_GnSpd", "WGEN.Z72PLC__UI_Loc_WGEN_Analogue_GnSpd",
             "WGEN", "REAL32", "RPM", "Generator Speed", "發電機轉速",
             0, 30, "HldReg[274]"),  # Z72 direct-drive: gen speed = rotor speed
    ScadaTag("WGEN_GnVtgMs", "WGEN.Z72PLC__UI_Loc_WGEN_Analogue_GnVtgMs",
             "WGEN", "REAL32", "V", "Generator Voltage", "發電機電壓",
             0, 4500, "HldReg[261]"),  # Z72 MV: 3.5kV nominal
    ScadaTag("WGEN_GnCurMs", "WGEN.Z72PLC__UI_Loc_WGEN_Analogue_GnCurMs",
             "WGEN", "REAL32", "A", "Generator Current", "發電機電流",
             0, 5000, "HldReg[275]"),
    ScadaTag("WGEN_GnStaTmp1", "WGEN.Z72PLC__UI_Loc_WGEN_Analogue_GnStaTmp1",
             "WGEN", "REAL32", "°C", "Generator Stator Temp 1", "發電機定子溫度1",
             20, 160, "HldReg[501]"),
    ScadaTag("WGEN_GnAirTmp1", "WGEN.Z72PLC__UI_Loc_WGEN_Analogue_GnAirTmp1",
             "WGEN", "REAL32", "°C", "Generator Air Gap Temp", "發電機氣隙溫度",
             20, 120, "HldReg[507]"),
    ScadaTag("WGEN_GnBrgTmp1", "WGEN.Z72PLC__UI_Loc_WGEN_Analogue_GnBrgTmp1",
             "WGEN", "REAL32", "°C", "Generator Bearing Temp", "發電機軸承溫度",
             20, 120, "HldReg[509]"),

    # ══════════════════════════════════════════════════════════════════════
    # WROT — Rotor / Pitch
    # ══════════════════════════════════════════════════════════════════════
    ScadaTag("WROT_RotSpd", "WROT.Z72PLC__UI_Loc_WROT_Analogue_RotSpd",
             "WROT", "REAL32", "RPM", "Rotor Speed", "葉輪轉速",
             0, 30, "HldReg[228]"),  # Z72: nominal 22.5, HW overspeed 28.5
    ScadaTag("WROT_PtAngValBl1", "WROT.Z72PLC__UI_Loc_WROT_Analogue_PtAngValBl1",
             "WROT", "REAL32", "deg", "Blade 1 Pitch Angle", "葉片1角度",
             -5, 95, "HldReg[230]"),
    ScadaTag("WROT_PtAngValBl2", "WROT.Z72PLC__UI_Loc_WROT_Analogue_PtAngValBl2",
             "WROT", "REAL32", "deg", "Blade 2 Pitch Angle", "葉片2角度",
             -5, 95, "HldReg[231]"),
    ScadaTag("WROT_PtAngValBl3", "WROT.Z72PLC__UI_Loc_WROT_Analogue_PtAngValBl3",
             "WROT", "REAL32", "deg", "Blade 3 Pitch Angle", "葉片3角度",
             -5, 95, "HldReg[232]"),
    ScadaTag("WROT_RotTmp", "WROT.Z72PLC__UI_Loc_WROT_Analogue_RotTmp",
             "WROT", "REAL32", "°C", "Rotor Temperature", "葉輪轉子溫度",
             -10, 80, "HldReg[511]"),
    ScadaTag("WROT_RotCabTmp", "WROT.Z72PLC__UI_Loc_WROT_Analogue_RotCabTmp",
             "WROT", "REAL32", "°C", "Hub Cabinet Temp", "輪毂控制櫃溫度",
             -10, 60, "HldReg[512]"),
    ScadaTag("WROT_LckngPnPos", "WROT.Z72PLC__UI_Loc_WROT_Analogue_LckngPnPos",
             "WROT", "REAL32", "", "Locking Pin Position", "鎖緊銷位置",
             0, 1),
    ScadaTag("WROT_RotLckd", "WROT.Z72PLC__UI_Loc_WROT_State_RotLckd",
             "WROT", "SINT16", "", "Rotor Locked", "葉輪鎖固狀態",
             0, 1),
    ScadaTag("WROT_SrvcBrkAct", "WROT.Z72PLC__UI_Loc_WROT_State_SrvcBrkAct",
             "WROT", "SINT16", "", "Service Brake Active", "剎車啟動",
             0, 1),

    # ══════════════════════════════════════════════════════════════════════
    # WCNV — Converter
    # ══════════════════════════════════════════════════════════════════════
    ScadaTag("WCNV_CnvCabinTmp", "WCNV.Z72PLC__UI_Loc_WCNV_Analogue_CnvCabinTmp",
             "WCNV", "REAL32", "°C", "Converter Cabinet Temp", "變頻器控制櫃溫度",
             10, 65, "HldReg[277]"),
    ScadaTag("WCNV_CnvDClVtg", "WCNV.Z72PLC__UI_Loc_WCNV_Analogue_CnvDClVtg",
             "WCNV", "REAL32", "V", "Converter DC Link Voltage", "變頻器直流電壓",
             0, 1200),
    ScadaTag("WCNV_CnvGdPwrAt", "WCNV.Z72PLC__UI_Loc_WCNV_Analogue_CnvGdPwrAt",
             "WCNV", "REAL32", "kW", "Converter Grid Active Power", "變頻器電網實功率",
             -500, 5500, "HldReg[267]"),
    ScadaTag("WCNV_CnvGnFrq", "WCNV.Z72PLC__UI_Loc_WCNV_Analogue_CnvGnFrq",
             "WCNV", "REAL32", "Hz", "Converter Generator Freq", "變頻器發電機頻率",
             0, 65, "HldReg[274]"),  # Z72: 60Hz grid
    ScadaTag("WCNV_CnvGnPwr", "WCNV.Z72PLC__UI_Loc_WCNV_Analogue_CnvGnPwr",
             "WCNV", "REAL32", "kW", "Converter Generator Power", "變頻器發電機功率",
             0, 5500, "HldReg[273]"),
    ScadaTag("WCNV_IGCTWtrCond", "WCNV.Z72PLC__UI_Loc_WCNV_Analogue_IGCTWtrCond",
             "WCNV", "REAL32", "", "IGCT Water Condition", "變頻器IGCT水壓狀態",
             0, 5),
    ScadaTag("WCNV_IGCTWtrPres1", "WCNV.Z72PLC__UI_Loc_WCNV_Analogue_IGCTWtrPres1",
             "WCNV", "REAL32", "bar", "IGCT Water Pressure 1", "變頻器IGCT水壓1",
             0, 10, "HldReg[279]"),
    ScadaTag("WCNV_IGCTWtrPres2", "WCNV.Z72PLC__UI_Loc_WCNV_Analogue_IGCTWtrPres2",
             "WCNV", "REAL32", "bar", "IGCT Water Pressure 2", "變頻器IGCT水壓2",
             0, 10, "HldReg[280]"),
    ScadaTag("WCNV_IGCTWtrTmp", "WCNV.Z72PLC__UI_Loc_WCNV_Analogue_IGCTWtrTmp",
             "WCNV", "REAL32", "°C", "IGCT Water Temp", "變頻器IGCT水溫",
             10, 60, "HldReg[277]"),

    # ══════════════════════════════════════════════════════════════════════
    # WGDC — Grid / Transformer
    # ══════════════════════════════════════════════════════════════════════
    ScadaTag("WGDC_TrfCoreTmp", "WGDC.Z72PLC__UI_Loc_WGDC_Analogue_TrfCoreTmp",
             "WGDC", "REAL32", "°C", "Transformer Core Temp", "變壓器溫度",
             10, 120),

    # ══════════════════════════════════════════════════════════════════════
    # WMET — Meteorological
    # ══════════════════════════════════════════════════════════════════════
    ScadaTag("WMET_WSpeedNac", "WMET.Z72PLC__UI_Loc_WMET_Analogue_WSpeedNac",
             "WMET", "REAL32", "m/s", "Nacelle Wind Speed", "機艙風速",
             0, 40, "HldReg[248]"),
    ScadaTag("WMET_WDirAbs", "WMET.Z72PLC__UI_Loc_WMET_Analogue_WDirAbs",
             "WMET", "REAL32", "deg", "Wind Direction (absolute)", "風向(絕對)",
             0, 360),
    ScadaTag("WMET_TmpOutside", "WMET.Z72PLC__UI_Loc_WMET_Analogue_TmpOutside",
             "WMET", "REAL32", "°C", "Outside Temperature", "室外溫度",
             -10, 45),

    # ══════════════════════════════════════════════════════════════════════
    # WNAC — Nacelle
    # ══════════════════════════════════════════════════════════════════════
    ScadaTag("WNAC_NacTmp", "WNAC.Z72PLC__UI_Loc_WNAC_Analogue_NacTmp",
             "WNAC", "REAL32", "°C", "Nacelle Temperature", "機艙溫度",
             -10, 60, "HldReg[513]"),
    ScadaTag("WNAC_NacCabTmp", "WNAC.Z72PLC__UI_Loc_WNAC_Analogue_NacCabTmp",
             "WNAC", "REAL32", "°C", "Nacelle Cabinet Temp", "機艙控制櫃溫度",
             -10, 55, "HldReg[514]"),
    ScadaTag("WNAC_VibMsNacXDir", "WNAC.Z72PLC__UI_Loc_WNAC_Analogue_VibMsNacXDir",
             "WNAC", "REAL32", "mm/s", "Nacelle Vibration X", "機艙X方向振動",
             0, 20, "HldReg[244]"),
    ScadaTag("WNAC_VibMsNacYDir", "WNAC.Z72PLC__UI_Loc_WNAC_Analogue_VibMsNacYDir",
             "WNAC", "REAL32", "mm/s", "Nacelle Vibration Y", "機艙Y方向振動",
             0, 20, "HldReg[245]"),

    # ══════════════════════════════════════════════════════════════════════
    # WYAW — Yaw System
    # ══════════════════════════════════════════════════════════════════════
    ScadaTag("WYAW_YwVn1AlgnAvg5s", "WYAW.Z72PLC__UI_Loc_WYAW_Analogue_YwVn1AlgnAvg5s",
             "WYAW", "REAL32", "deg", "Yaw Alignment Vn1 (5s avg)", "轉向Vn1誤差(5秒平均)",
             -180, 180, "HldReg[243]"),
    ScadaTag("WYAW_YwBrkHyPrs", "WYAW.Z72PLC__UI_Loc_WYAW_Analogue_YwBrkHyPrs",
             "WYAW", "REAL32", "bar", "Yaw Brake Hydraulic Pressure", "轉向剎車液壓壓力",
             0, 250, "HldReg[247]"),
    ScadaTag("WYAW_CabWup", "WYAW.Z72PLC__UI_Loc_WYAW_Analogue_CabWup",
             "WYAW", "REAL32", "turns", "Cable Windup", "纜線防絞(圈數)",
             -5, 5, "HldReg[246]"),

    # ══════════════════════════════════════════════════════════════════════
    # WCNV — Electrical Response (extended)
    # ══════════════════════════════════════════════════════════════════════
    ScadaTag("WCNV_ReactPwr", "WCNV.Z72PLC__UI_Loc_WCNV_Analogue_ReactPwr",
             "WCNV", "REAL32", "kvar", "Reactive Power", "無功功率",
             -1000, 1000),
    ScadaTag("WCNV_PwrFactor", "WCNV.Z72PLC__UI_Loc_WCNV_Analogue_PwrFactor",
             "WCNV", "REAL32", "", "Power Factor", "功率因數",
             -1.0, 1.0),
    ScadaTag("WCNV_AppPwr", "WCNV.Z72PLC__UI_Loc_WCNV_Analogue_AppPwr",
             "WCNV", "REAL32", "kVA", "Apparent Power", "視在功率",
             0, 5500),
    ScadaTag("WCNV_FreqWattDerate", "WCNV.Z72PLC__UI_Loc_WCNV_Analogue_FreqWattDerate",
             "WCNV", "REAL32", "", "Freq-Watt Derate Factor", "頻率-功率降額因子",
             0, 1.0),
    ScadaTag("WCNV_InertiaPwr", "WCNV.Z72PLC__UI_Loc_WCNV_Analogue_InertiaPwr",
             "WCNV", "REAL32", "kW", "Synthetic Inertia Power", "虛擬慣量功率",
             -500, 500),
    ScadaTag("WCNV_CnvMode", "WCNV.Z72PLC__UI_Loc_WCNV_State_CnvMode",
             "WCNV", "SINT16", "", "Converter Mode", "變頻器運行模式",
             0, 5),
    ScadaTag("WCNV_RtBand", "WCNV.Z72PLC__UI_Loc_WCNV_State_RtBand",
             "WCNV", "SINT16", "", "Ride-Through Band", "電壓穿越區間",
             -2, 4),

    # ══════════════════════════════════════════════════════════════════════
    # WVIB — Vibration Spectral Bands
    # ══════════════════════════════════════════════════════════════════════
    ScadaTag("WVIB_Band1pX", "WVIB.Z72PLC__UI_Loc_WVIB_Analogue_Band1pX",
             "WVIB", "REAL32", "mm/s", "Vibration 1P Band X", "振動1P頻帶X",
             0, 10),
    ScadaTag("WVIB_Band1pY", "WVIB.Z72PLC__UI_Loc_WVIB_Analogue_Band1pY",
             "WVIB", "REAL32", "mm/s", "Vibration 1P Band Y", "振動1P頻帶Y",
             0, 10),
    ScadaTag("WVIB_Band3pX", "WVIB.Z72PLC__UI_Loc_WVIB_Analogue_Band3pX",
             "WVIB", "REAL32", "mm/s", "Vibration 3P Band X", "振動3P頻帶X",
             0, 10),
    ScadaTag("WVIB_Band3pY", "WVIB.Z72PLC__UI_Loc_WVIB_Analogue_Band3pY",
             "WVIB", "REAL32", "mm/s", "Vibration 3P Band Y", "振動3P頻帶Y",
             0, 10),
    ScadaTag("WVIB_BandGearX", "WVIB.Z72PLC__UI_Loc_WVIB_Analogue_BandGearX",
             "WVIB", "REAL32", "mm/s", "Vibration Gear Mesh X", "振動齒輪嚙合頻帶X",
             0, 10),
    ScadaTag("WVIB_BandGearY", "WVIB.Z72PLC__UI_Loc_WVIB_Analogue_BandGearY",
             "WVIB", "REAL32", "mm/s", "Vibration Gear Mesh Y", "振動齒輪嚙合頻帶Y",
             0, 10),
    ScadaTag("WVIB_BandHfX", "WVIB.Z72PLC__UI_Loc_WVIB_Analogue_BandHfX",
             "WVIB", "REAL32", "mm/s", "Vibration HF Band X", "振動高頻帶X",
             0, 10),
    ScadaTag("WVIB_BandHfY", "WVIB.Z72PLC__UI_Loc_WVIB_Analogue_BandHfY",
             "WVIB", "REAL32", "mm/s", "Vibration HF Band Y", "振動高頻帶Y",
             0, 10),
    ScadaTag("WVIB_BandBbX", "WVIB.Z72PLC__UI_Loc_WVIB_Analogue_BandBbX",
             "WVIB", "REAL32", "mm/s", "Vibration Broadband X", "振動寬頻帶X",
             0, 10),
    ScadaTag("WVIB_BandBbY", "WVIB.Z72PLC__UI_Loc_WVIB_Analogue_BandBbY",
             "WVIB", "REAL32", "mm/s", "Vibration Broadband Y", "振動寬頻帶Y",
             0, 10),
    ScadaTag("WVIB_CrestFactor", "WVIB.Z72PLC__UI_Loc_WVIB_Analogue_CrestFactor",
             "WVIB", "REAL32", "", "Vibration Crest Factor", "振動峰值因子",
             1, 30),
    ScadaTag("WVIB_Kurtosis", "WVIB.Z72PLC__UI_Loc_WVIB_Analogue_Kurtosis",
             "WVIB", "REAL32", "", "Vibration Kurtosis", "振動峰度",
             1, 50),

    ScadaTag("WVIB_Alarm1p", "WVIB.Z72PLC__UI_Loc_WVIB_State_Alarm1p",
             "WVIB", "SINT16", "", "1P Alarm Level", "1P警報等級",
             0, 2),
    ScadaTag("WVIB_Alarm3p", "WVIB.Z72PLC__UI_Loc_WVIB_State_Alarm3p",
             "WVIB", "SINT16", "", "3P Alarm Level", "3P警報等級",
             0, 2),
    ScadaTag("WVIB_AlarmGear", "WVIB.Z72PLC__UI_Loc_WVIB_State_AlarmGear",
             "WVIB", "SINT16", "", "Gear Mesh Alarm Level", "齒輪嚙合警報等級",
             0, 2),
    ScadaTag("WVIB_AlarmHf", "WVIB.Z72PLC__UI_Loc_WVIB_State_AlarmHf",
             "WVIB", "SINT16", "", "HF Alarm Level", "高頻警報等級",
             0, 2),
    ScadaTag("WVIB_AlarmBb", "WVIB.Z72PLC__UI_Loc_WVIB_State_AlarmBb",
             "WVIB", "SINT16", "", "Broadband Alarm Level", "寬頻警報等級",
             0, 2),
    ScadaTag("WVIB_AlarmCrest", "WVIB.Z72PLC__UI_Loc_WVIB_State_AlarmCrest",
             "WVIB", "SINT16", "", "Crest Factor Alarm Level", "峰值因子警報等級",
             0, 2),
    ScadaTag("WVIB_AlarmKurt", "WVIB.Z72PLC__UI_Loc_WVIB_State_AlarmKurt",
             "WVIB", "SINT16", "", "Kurtosis Alarm Level", "峭度警報等級",
             0, 2),
    ScadaTag("WVIB_AlarmOverall", "WVIB.Z72PLC__UI_Loc_WVIB_State_AlarmOverall",
             "WVIB", "SINT16", "", "Overall Alarm Level", "綜合震動警報等級",
             0, 2),
    ScadaTag("WVIB_Thresh1pWarn", "WVIB.Z72PLC__UI_Loc_WVIB_Analogue_Thresh1pWarn",
             "WVIB", "REAL32", "mm/s", "1P Warning Threshold", "1P警報門檻",
             0, 5),
    ScadaTag("WVIB_Thresh1pAlrm", "WVIB.Z72PLC__UI_Loc_WVIB_Analogue_Thresh1pAlrm",
             "WVIB", "REAL32", "mm/s", "1P Alarm Threshold", "1P危險門檻",
             0, 10),
    ScadaTag("WVIB_BpfoFreq", "WVIB.Z72PLC__UI_Loc_WVIB_Analogue_BpfoFreq",
             "WVIB", "REAL32", "Hz", "BPFO Frequency", "外環缺陷頻率",
             0, 10),
    ScadaTag("WVIB_BpfiFreq", "WVIB.Z72PLC__UI_Loc_WVIB_Analogue_BpfiFreq",
             "WVIB", "REAL32", "Hz", "BPFI Frequency", "內環缺陷頻率",
             0, 10),
    ScadaTag("WVIB_BpfoAmp", "WVIB.Z72PLC__UI_Loc_WVIB_Analogue_BpfoAmp",
             "WVIB", "REAL32", "mm/s", "BPFO Amplitude", "外環缺陷振幅",
             0, 2),
    ScadaTag("WVIB_BpfiAmp", "WVIB.Z72PLC__UI_Loc_WVIB_Analogue_BpfiAmp",
             "WVIB", "REAL32", "mm/s", "BPFI Amplitude", "內環缺陷振幅",
             0, 2),
    ScadaTag("WVIB_GmfFreq", "WVIB.Z72PLC__UI_Loc_WVIB_Analogue_GmfFreq",
             "WVIB", "REAL32", "Hz", "Gear Mesh Frequency", "齒輪嚙合頻率",
             0, 100),
    ScadaTag("WVIB_Sideband1Amp", "WVIB.Z72PLC__UI_Loc_WVIB_Analogue_Sideband1Amp",
             "WVIB", "REAL32", "mm/s", "1st Sideband Amplitude", "一階邊帶振幅",
             0, 2),
    ScadaTag("WVIB_Sideband2Amp", "WVIB.Z72PLC__UI_Loc_WVIB_Analogue_Sideband2Amp",
             "WVIB", "REAL32", "mm/s", "2nd Sideband Amplitude", "二階邊帶振幅",
             0, 2),
    ScadaTag("WVIB_SidebandRatio", "WVIB.Z72PLC__UI_Loc_WVIB_Analogue_SidebandRatio",
             "WVIB", "REAL32", "", "Sideband Energy Ratio", "邊帶能量比",
             0, 1),

    # ══════════════════════════════════════════════════════════════════════
    # WLOD — Structural Load & Fatigue
    # ══════════════════════════════════════════════════════════════════════
    ScadaTag("WLOD_TwrFaMom", "WLOD.Z72PLC__UI_Loc_WLOD_Analogue_TwrFaMom",
             "WLOD", "REAL32", "kNm", "Tower Fore-Aft Moment", "塔架前後彎矩",
             0, 10000),
    ScadaTag("WLOD_TwrSsMom", "WLOD.Z72PLC__UI_Loc_WLOD_Analogue_TwrSsMom",
             "WLOD", "REAL32", "kNm", "Tower Side-Side Moment", "塔架側向彎矩",
             0, 5000),
    ScadaTag("WLOD_BldFlapMom", "WLOD.Z72PLC__UI_Loc_WLOD_Analogue_BldFlapMom",
             "WLOD", "REAL32", "kNm", "Blade Flapwise Moment", "葉片揮舞彎矩",
             0, 5000),
    ScadaTag("WLOD_BldEdgeMom", "WLOD.Z72PLC__UI_Loc_WLOD_Analogue_BldEdgMom",
             "WLOD", "REAL32", "kNm", "Blade Edgewise Moment", "葉片擺振彎矩",
             0, 3000),
    ScadaTag("WLOD_DelTwrFa", "WLOD.Z72PLC__UI_Loc_WLOD_Analogue_DelTwrFa",
             "WLOD", "REAL32", "kNm", "DEL Tower Fore-Aft", "塔架前後等效疲勞載荷",
             0, 5000),
    ScadaTag("WLOD_DelTwrSs", "WLOD.Z72PLC__UI_Loc_WLOD_Analogue_DelTwrSs",
             "WLOD", "REAL32", "kNm", "DEL Tower Side-Side", "塔架側向等效疲勞載荷",
             0, 3000),
    ScadaTag("WLOD_DelBldFlap", "WLOD.Z72PLC__UI_Loc_WLOD_Analogue_DelBldFlap",
             "WLOD", "REAL32", "kNm", "DEL Blade Flapwise", "葉片揮舞等效疲勞載荷",
             0, 3000),
    ScadaTag("WLOD_DelBldEdge", "WLOD.Z72PLC__UI_Loc_WLOD_Analogue_DelBldEdge",
             "WLOD", "REAL32", "kNm", "DEL Blade Edgewise", "葉片擺振等效疲勞載荷",
             0, 2000),
    ScadaTag("WLOD_DmgTwrFa", "WLOD.Z72PLC__UI_Loc_WLOD_Analogue_DmgTwrFa",
             "WLOD", "REAL32", "", "Damage Tower Fore-Aft", "塔架前後累積損傷",
             0, 1),
    ScadaTag("WLOD_DmgTwrSs", "WLOD.Z72PLC__UI_Loc_WLOD_Analogue_DmgTwrSs",
             "WLOD", "REAL32", "", "Damage Tower Side-Side", "塔架側向累積損傷",
             0, 1),
    ScadaTag("WLOD_DmgBldFlap", "WLOD.Z72PLC__UI_Loc_WLOD_Analogue_DmgBldFlap",
             "WLOD", "REAL32", "", "Damage Blade Flapwise", "葉片揮舞累積損傷",
             0, 1),
    ScadaTag("WLOD_DmgBldEdge", "WLOD.Z72PLC__UI_Loc_WLOD_Analogue_DmgBldEdge",
             "WLOD", "REAL32", "", "Damage Blade Edgewise", "葉片擺振累積損傷",
             0, 1),
    ScadaTag("WLOD_ProdHours", "WLOD.Z72PLC__UI_Loc_WLOD_Analogue_ProdHours",
             "WLOD", "REAL32", "h", "Production Hours", "發電運轉時數",
             0, 100000),
    ScadaTag("WLOD_AlmTwr", "WLOD.Z72PLC__UI_Loc_WLOD_Analogue_AlmTwr",
             "WLOD", "SINT16", "", "Tower Fatigue Alarm Level", "塔架疲勞警報等級",
             0, 4),
    ScadaTag("WLOD_AlmBld", "WLOD.Z72PLC__UI_Loc_WLOD_Analogue_AlmBld",
             "WLOD", "SINT16", "", "Blade Fatigue Alarm Level", "葉片疲勞警報等級",
             0, 4),
    ScadaTag("WLOD_RulHours", "WLOD.Z72PLC__UI_Loc_WLOD_Analogue_RulHours",
             "WLOD", "REAL32", "h", "Remaining Useful Life", "剩餘使用壽命",
             -1, 1000000),

    # ══════════════════════════════════════════════════════════════════════
    # WROT — Rotor Imbalance (#72)
    # ══════════════════════════════════════════════════════════════════════
    ScadaTag("WROT_ImbForce", "WROT.Z72PLC__UI_Loc_WROT_Analogue_ImbForce",
             "WROT", "REAL32", "kN", "Rotor Imbalance Force", "轉子不平衡力",
             0, 50),

    # ══════════════════════════════════════════════════════════════════════
    # WSRV / MBUS — Service & Control
    # ══════════════════════════════════════════════════════════════════════
    ScadaTag("WSRV_SrvOn", "WSRV.Z72PLC__UI_Srv_State_SrvOn",
             "WSRV", "SINT16", "", "Service Mode On", "系統服務模式",
             0, 1),
    ScadaTag("MBUS_Contact2", "MBUS.Z72PLC__UI_Mbus_Contact[2]",
             "MBUS", "UINT16", "", "Local/Remote Control", "風機本地/遠端控制",
             0, 1, "Contact[2]"),
]


class ScadaRegistry:
    """Registry providing lookup by tag ID, subsystem, OPC name, or Modbus address."""

    def __init__(self, tags: List[ScadaTag]):
        self._tags = {t.id: t for t in tags}
        self._by_subsystem: Dict[str, List[ScadaTag]] = {}
        self._by_opc: Dict[str, ScadaTag] = {}
        self._by_modbus: Dict[str, ScadaTag] = {}
        for t in tags:
            self._by_subsystem.setdefault(t.subsystem, []).append(t)
            self._by_opc[t.opc_tag] = t
            if t.modbus_reg:
                self._by_modbus[t.modbus_reg] = t

    def __getitem__(self, tag_id: str) -> ScadaTag:
        return self._tags[tag_id]

    def __contains__(self, tag_id: str) -> bool:
        return tag_id in self._tags

    def get(self, tag_id: str) -> Optional[ScadaTag]:
        """Look up a SCADA tag definition by its tag ID."""
        return self._tags.get(tag_id)

    @property
    def all_tags(self) -> List[ScadaTag]:
        """All registered SCADA tag definitions."""
        return list(self._tags.values())

    @property
    def tag_ids(self) -> List[str]:
        """List of all registered tag ID strings."""
        return list(self._tags.keys())

    @property
    def display_tags(self) -> List[ScadaTag]:
        """Tags marked for frontend display."""
        return [t for t in self._tags.values() if t.is_display]

    def by_subsystem(self, subsystem: str) -> List[ScadaTag]:
        """Return tags belonging to a given subsystem (e.g. 'generator', 'grid')."""
        return self._by_subsystem.get(subsystem, [])

    def by_opc_tag(self, opc_tag: str) -> Optional[ScadaTag]:
        """Look up a tag by its OPC UA node path."""
        return self._by_opc.get(opc_tag)

    def by_modbus(self, register: str) -> Optional[ScadaTag]:
        """Look up a tag by its Modbus register address."""
        return self._by_modbus.get(register)

    def labels(self, lang: str = "en") -> Dict[str, str]:
        """Return {tag_id: label} for the given language."""
        if lang == "zh" or lang == "zh-TW":
            return {t.id: t.label_zh for t in self._tags.values()}
        return {t.id: t.label_en for t in self._tags.values()}

    def to_i18n_dict(self) -> Dict[str, Dict[str, str]]:
        """Return full i18n dict: {tag_id: {en: ..., zh: ...}}."""
        return {
            t.id: {"en": t.label_en, "zh": t.label_zh}
            for t in self._tags.values()
        }


# Singleton instance
SCADA_REGISTRY = ScadaRegistry(_TAGS)

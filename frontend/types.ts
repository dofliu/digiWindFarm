export enum TurbineStatus {
  OPERATING = 'OPERATING',
  IDLE = 'IDLE',
  FAULT = 'FAULT',
  OFFLINE = 'OFFLINE',
}

export interface TurbineData {
  id: number;
  name: string;
  status: TurbineStatus;
  turState?: number; // Bachmann TurState 1-9

  // ── Core fields (backward-compatible) ──
  powerOutput: number; // MW (WTUR_TotPwrAt / 1000)
  windSpeed: number; // m/s (WMET_WSpeedNac)
  rotorSpeed: number; // RPM (WROT_RotSpd)
  bladeAngle: number; // deg (WROT_PtAngValBl1)
  temperature: number; // °C (WGEN_GnStaTmp1)
  vibration: number; // mm/s (WNAC_VibMsNacXDir)
  voltage: number; // V (WGEN_GnVtgMs)
  current: number; // A (WGEN_GnCurMs)
  history: { time: number; power: number }[];

  // ── WGEN — Generator (expanded) ──
  genPower?: number; // kW
  genSpeed?: number; // RPM
  genStatorTemp1?: number; // °C
  genAirTemp1?: number; // °C
  genBearingTemp1?: number; // °C

  // ── WROT — Rotor / Pitch (expanded) ──
  bladeAngle1?: number; // deg
  bladeAngle2?: number; // deg
  bladeAngle3?: number; // deg
  rotorTemp?: number; // °C
  hubCabinetTemp?: number; // °C
  rotorLocked?: number; // 0/1
  brakeActive?: number; // 0/1

  // ── WCNV — Converter ──
  cnvCabinetTemp?: number; // °C
  cnvDcVoltage?: number; // V
  cnvGridPower?: number; // kW
  cnvGenFreq?: number; // Hz
  cnvGenPower?: number; // kW
  igctWaterCond?: number;
  igctWaterPres1?: number; // bar
  igctWaterPres2?: number; // bar
  igctWaterTemp?: number; // °C

  // ── WCNV — Electrical Response ──
  reactivePower?: number; // kvar
  powerFactor?: number;
  apparentPower?: number; // kVA
  freqWattDerate?: number;
  inertiaPower?: number; // kW
  converterMode?: number;
  rideThroughBand?: number;

  // ── WVIB — Vibration Spectral Bands ──
  vibBand1pX?: number; // mm/s
  vibBand1pY?: number;
  vibBand3pX?: number;
  vibBand3pY?: number;
  vibBandGearX?: number;
  vibBandGearY?: number;
  vibBandHfX?: number;
  vibBandHfY?: number;
  vibBandBbX?: number;
  vibBandBbY?: number;
  vibCrestFactor?: number;
  vibKurtosis?: number;

  // ── WGDC — Transformer ──
  transformerTemp?: number; // °C

  // ── WMET — Meteorological ──
  windDirection?: number; // deg
  outsideTemp?: number; // °C

  // ── WNAC — Nacelle ──
  nacelleTemp?: number; // °C
  nacelleCabTemp?: number; // °C
  vibrationX?: number; // mm/s
  vibrationY?: number; // mm/s

  // ── WYAW — Yaw ──
  yawError?: number; // deg
  yawBrakePressure?: number; // bar
  cableWindup?: number; // turns

  // ── Fault info ──
  activeFaults?: FaultInfo[];

  // ── Raw SCADA dict (all tags) ──
  scadaTags?: Record<string, number>;
}

export interface FaultInfo {
  scenario_id: string;
  turbine_id: string;
  name_en: string;
  name_zh: string;
  severity: number;
  phase: 'incipient' | 'developing' | 'advanced' | 'critical';
  tripped: boolean;
  active_alarms: { type: string; code: number; desc: string }[];
}

export interface FaultScenario {
  id: string;
  name_en: string;
  name_zh: string;
  description_en: string;
  description_zh: string;
  affected_tags: string[];
  alarm_codes: { type: string; code: number; desc: string }[];
}

export interface ScadaTagLabels {
  [tagId: string]: string;
}

export interface ScadaTagI18n {
  [tagId: string]: { en: string; zh: string };
}

export enum TechnicianStatus {
    ON_DUTY = 'ON DUTY',
    OFF_DUTY = 'OFF DUTY',
    DISPATCHED = 'DISPATCHED',
}

export interface Technician {
    id: number;
    name: string;
    status: TechnicianStatus;
}

export enum WorkOrderStatus {
    OPEN = 'OPEN',
    IN_PROGRESS = 'IN_PROGRESS',
    COMPLETED = 'COMPLETED',
}

export interface WorkOrder {
    id: string;
    turbineId: number;
    turbineName: string;
    technicianId: number | null;
    status: WorkOrderStatus;
    createdAt: number;
    faultDescription: string;
    notes: string;
    photos: string[]; // Array of base64 encoded images
}

// --- App Settings Types ---
export enum DataSourceType {
  MOCK = 'MOCK',
  SIMULATION = 'SIMULATION',
  OPC_DA = 'OPC_DA',
  MODBUS_TCP = 'MODBUS_TCP',
}

export interface OpcDaSettings {
  server: string;
  progId: string;
}

export interface ModbusTcpSettings {
  ip: string;
  port: number;
  slaveId: number;
}

export interface SimulationSettings {
  turbineCount: number;
  baseWindSpeed: number;
  turbulenceIntensity: number;
}

export interface AppSettings {
  dataSource: DataSourceType;
  opcDa: OpcDaSettings;
  modbusTcp: ModbusTcpSettings;
  simulation: SimulationSettings;
}

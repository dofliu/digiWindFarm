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
  powerOutput: number; // in MW
  windSpeed: number; // in m/s
  rotorSpeed: number; // in RPM
  bladeAngle: number; // in degrees
  temperature: number; // in Celsius
  vibration: number; // in mm/s
  voltage: number; // in V
  current: number; // in A
  history: { time: number; power: number }[];
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

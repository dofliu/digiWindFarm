from pydantic import BaseModel
from datetime import datetime
from enum import Enum
from typing import Optional, List


class TurbineStatus(str, Enum):
    OPERATING = "OPERATING"
    IDLE = "IDLE"
    FAULT = "FAULT"
    OFFLINE = "OFFLINE"


class DataSourceMode(str, Enum):
    SIMULATION = "simulation"
    OPC_DA = "opc_da"


class TurbineReading(BaseModel):
    turbineId: str
    name: str
    timestamp: datetime
    status: TurbineStatus
    windSpeed: float          # m/s
    powerOutput: float        # MW
    rotorSpeed: float         # RPM
    bladeAngle: float         # degrees (pitch)
    temperature: float        # generator temp °C
    vibration: float          # gearbox vibration mm/s
    voltage: float            # V
    current: float            # A
    yawAngle: float           # degrees
    gearboxTemp: float        # °C
    frequency: Optional[float] = None       # Hz
    hydraulicPressure: Optional[float] = None  # bar
    history: Optional[List[dict]] = None    # [{time, power}] for frontend chart


class FarmStatus(BaseModel):
    totalTurbines: int
    operatingCount: int
    idleCount: int
    faultCount: int
    offlineCount: int
    totalPowerMW: float
    avgWindSpeed: float
    timestamp: datetime


class DataSourceConfig(BaseModel):
    mode: DataSourceMode
    opcServer: Optional[str] = None
    opcProgId: Optional[str] = None
    opcHost: Optional[str] = "localhost"


class SimulationConfig(BaseModel):
    turbineCount: int = 14
    baseWindSpeed: float = 10.0
    turbulenceIntensity: float = 0.1
    timeStep: float = 1.0


class AppConfig(BaseModel):
    dataSource: DataSourceConfig
    simulation: SimulationConfig

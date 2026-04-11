import { useState, useEffect, useCallback, useRef } from 'react';
import { type TurbineData, TurbineStatus, type FaultInfo } from '../types';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8100';
const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8100/ws/realtime';

interface ApiTurbineReading {
  turbineId: string;
  name: string;
  timestamp: string;
  status: string;
  turState: number;
  windSpeed: number;
  powerOutput: number;
  rotorSpeed: number;
  bladeAngle: number;
  temperature: number;
  vibration: number;
  voltage: number;
  current: number;
  yawAngle: number;
  gearboxTemp: number;
  frequency: number | null;
  hydraulicPressure: number | null;
  history: { time: number; power: number }[] | null;
  // Extended SCADA fields
  genPower?: number;
  genSpeed?: number;
  genStatorTemp1?: number;
  genAirTemp1?: number;
  genBearingTemp1?: number;
  bladeAngle1?: number;
  bladeAngle2?: number;
  bladeAngle3?: number;
  rotorTemp?: number;
  hubCabinetTemp?: number;
  rotorLocked?: number;
  brakeActive?: number;
  cnvCabinetTemp?: number;
  cnvDcVoltage?: number;
  cnvGridPower?: number;
  cnvGenFreq?: number;
  cnvGenPower?: number;
  igctWaterCond?: number;
  igctWaterPres1?: number;
  igctWaterPres2?: number;
  igctWaterTemp?: number;
  transformerTemp?: number;
  windDirection?: number;
  outsideTemp?: number;
  nacelleTemp?: number;
  nacelleCabTemp?: number;
  vibrationX?: number;
  vibrationY?: number;
  yawError?: number;
  yawBrakePressure?: number;
  cableWindup?: number;
  // Electrical response
  reactivePower?: number;
  powerFactor?: number;
  apparentPower?: number;
  freqWattDerate?: number;
  inertiaPower?: number;
  converterMode?: number;
  rideThroughBand?: number;
  // Vibration spectral bands
  vibBand1pX?: number;
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
  // Vibration alarm thresholds
  vibAlarm1p?: number;
  vibAlarm3p?: number;
  vibAlarmGear?: number;
  vibAlarmHf?: number;
  vibAlarmBb?: number;
  vibAlarmOverall?: number;
  vibThresh1pWarn?: number;
  vibThresh1pAlrm?: number;
  // Fatigue / load monitoring
  twrBsMy?: number;
  twrBsMx?: number;
  bldRtMy?: number;
  bldRtMx?: number;
  delTwr?: number;
  delBld?: number;
  dmgAccum?: number;
  activeFaults?: FaultInfo[];
  scadaTags?: Record<string, number>;
}

function mapStatus(status: string): TurbineStatus {
  switch (status) {
    case 'OPERATING': return TurbineStatus.OPERATING;
    case 'IDLE': return TurbineStatus.IDLE;
    case 'FAULT': return TurbineStatus.FAULT;
    case 'OFFLINE': return TurbineStatus.OFFLINE;
    default: return TurbineStatus.IDLE;
  }
}

function apiToTurbineData(api: ApiTurbineReading, index: number): TurbineData {
  return {
    id: index + 1,
    name: api.name,
    status: mapStatus(api.status),
    turState: api.turState,
    powerOutput: api.powerOutput,
    windSpeed: api.windSpeed,
    rotorSpeed: api.rotorSpeed,
    bladeAngle: api.bladeAngle,
    temperature: api.temperature,
    vibration: api.vibration,
    voltage: api.voltage,
    current: api.current,
    history: api.history || [],
    // Extended fields
    genPower: api.genPower,
    genSpeed: api.genSpeed,
    genStatorTemp1: api.genStatorTemp1,
    genAirTemp1: api.genAirTemp1,
    genBearingTemp1: api.genBearingTemp1,
    bladeAngle1: api.bladeAngle1,
    bladeAngle2: api.bladeAngle2,
    bladeAngle3: api.bladeAngle3,
    rotorTemp: api.rotorTemp,
    hubCabinetTemp: api.hubCabinetTemp,
    rotorLocked: api.rotorLocked,
    brakeActive: api.brakeActive,
    cnvCabinetTemp: api.cnvCabinetTemp,
    cnvDcVoltage: api.cnvDcVoltage,
    cnvGridPower: api.cnvGridPower,
    cnvGenFreq: api.cnvGenFreq,
    cnvGenPower: api.cnvGenPower,
    igctWaterCond: api.igctWaterCond,
    igctWaterPres1: api.igctWaterPres1,
    igctWaterPres2: api.igctWaterPres2,
    igctWaterTemp: api.igctWaterTemp,
    transformerTemp: api.transformerTemp,
    windDirection: api.windDirection,
    outsideTemp: api.outsideTemp,
    nacelleTemp: api.nacelleTemp,
    nacelleCabTemp: api.nacelleCabTemp,
    vibrationX: api.vibrationX,
    vibrationY: api.vibrationY,
    yawError: api.yawError,
    yawBrakePressure: api.yawBrakePressure,
    cableWindup: api.cableWindup,
    // Electrical response
    reactivePower: api.reactivePower,
    powerFactor: api.powerFactor,
    apparentPower: api.apparentPower,
    freqWattDerate: api.freqWattDerate,
    inertiaPower: api.inertiaPower,
    converterMode: api.converterMode,
    rideThroughBand: api.rideThroughBand,
    // Vibration spectral bands
    vibBand1pX: api.vibBand1pX,
    vibBand1pY: api.vibBand1pY,
    vibBand3pX: api.vibBand3pX,
    vibBand3pY: api.vibBand3pY,
    vibBandGearX: api.vibBandGearX,
    vibBandGearY: api.vibBandGearY,
    vibBandHfX: api.vibBandHfX,
    vibBandHfY: api.vibBandHfY,
    vibBandBbX: api.vibBandBbX,
    vibBandBbY: api.vibBandBbY,
    vibCrestFactor: api.vibCrestFactor,
    vibKurtosis: api.vibKurtosis,
    // Vibration alarm thresholds
    vibAlarm1p: api.vibAlarm1p,
    vibAlarm3p: api.vibAlarm3p,
    vibAlarmGear: api.vibAlarmGear,
    vibAlarmHf: api.vibAlarmHf,
    vibAlarmBb: api.vibAlarmBb,
    vibAlarmOverall: api.vibAlarmOverall,
    vibThresh1pWarn: api.vibThresh1pWarn,
    vibThresh1pAlrm: api.vibThresh1pAlrm,
    // Fatigue / load monitoring
    twrBsMy: api.twrBsMy,
    twrBsMx: api.twrBsMx,
    bldRtMy: api.bldRtMy,
    bldRtMx: api.bldRtMx,
    delTwr: api.delTwr,
    delBld: api.delBld,
    dmgAccum: api.dmgAccum,
    activeFaults: api.activeFaults,
    scadaTags: api.scadaTags,
  };
}

export const useRealtimeData = () => {
  const [turbines, setTurbines] = useState<TurbineData[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Initial REST fetch
  useEffect(() => {
    fetch(`${API_BASE}/api/turbines`)
      .then(res => res.json())
      .then((data: ApiTurbineReading[]) => {
        setTurbines(data.map(apiToTurbineData));
      })
      .catch(err => {
        console.warn('[useRealtimeData] Initial fetch failed, will retry via WebSocket:', err.message);
      });
  }, []);

  // WebSocket connection
  useEffect(() => {
    function connect() {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('[WS] Connected to', WS_URL);
        ws.send('ping');
      };

      ws.onmessage = (event) => {
        try {
          const data: ApiTurbineReading[] = JSON.parse(event.data);
          setTurbines(data.map(apiToTurbineData));
        } catch (e) {
          // ignore parse errors
        }
      };

      ws.onclose = () => {
        console.log('[WS] Disconnected, reconnecting in 3s...');
        reconnectTimerRef.current = setTimeout(connect, 3000);
      };

      ws.onerror = () => {
        ws.close();
      };
    }

    connect();

    // Also poll REST as fallback every 5s
    const pollInterval = setInterval(() => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        fetch(`${API_BASE}/api/turbines`)
          .then(res => res.json())
          .then((data: ApiTurbineReading[]) => {
            setTurbines(data.map(apiToTurbineData));
          })
          .catch(() => {});
      }
    }, 5000);

    return () => {
      if (wsRef.current) wsRef.current.close();
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      clearInterval(pollInterval);
    };
  }, []);

  const updateTurbineStatus = useCallback((turbineId: number, newStatus: TurbineStatus) => {
    setTurbines(prev => prev.map(t => t.id === turbineId ? { ...t, status: newStatus } : t));
  }, []);

  return { turbines, updateTurbineStatus };
};

import { useState, useEffect, useCallback, useRef } from 'react';
import { type TurbineData, TurbineStatus } from '../types';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';
const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/realtime';

interface ApiTurbineReading {
  turbineId: string;
  name: string;
  timestamp: string;
  status: string;
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
    powerOutput: api.powerOutput,
    windSpeed: api.windSpeed,
    rotorSpeed: api.rotorSpeed,
    bladeAngle: api.bladeAngle,
    temperature: api.temperature,
    vibration: api.vibration,
    voltage: api.voltage,
    current: api.current,
    history: api.history || [],
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
        // Send a ping to keep connection alive
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

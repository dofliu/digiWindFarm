import { useState, useEffect, useCallback } from 'react';
import { type TurbineData, TurbineStatus } from '../types';

const NUM_TURBINES = 14;
const HISTORY_LENGTH = 30;

const createInitialTurbineData = (): TurbineData[] => {
  const turbines: TurbineData[] = [];
  for (let i = 1; i <= NUM_TURBINES; i++) {
    const status = i % 7 === 0 ? TurbineStatus.IDLE : TurbineStatus.OPERATING;
    const powerOutput = status === TurbineStatus.OPERATING ? 2.5 + Math.random() * 1.5 : 0;
    const history = Array.from({ length: HISTORY_LENGTH }, (_, j) => ({
        time: Date.now() - (HISTORY_LENGTH - j) * 2000,
        power: status === TurbineStatus.OPERATING ? 2.5 + Math.random() * 1.5 : 0,
    }));
    turbines.push({
      id: i,
      name: `WTG-${String(i).padStart(2, '0')}`,
      status,
      powerOutput,
      windSpeed: 12 + Math.random() * 5,
      rotorSpeed: 15 + Math.random() * 5,
      bladeAngle: 1.5 + Math.random() * 1,
      temperature: 45 + Math.random() * 10,
      vibration: 0.5 + Math.random() * 0.2,
      voltage: 690 + (Math.random() - 0.5) * 20,
      current: 2500 + (Math.random() - 0.5) * 200,
      history,
    });
  }
  // Force one turbine to start in FAULT state for demonstration
  if (turbines.length > 2) {
      turbines[2].status = TurbineStatus.FAULT;
      turbines[2].powerOutput = 0;
      turbines[2].rotorSpeed = 0;
      turbines[2].vibration = 1.8;
      turbines[2].temperature = 85;
  }
  return turbines;
};

const updateTurbineData = (turbine: TurbineData): TurbineData => {
    let { status, powerOutput, windSpeed, rotorSpeed, bladeAngle, temperature, vibration, voltage, current, history } = turbine;

    // Only introduce new random faults if not already in a fault state
    if (status !== TurbineStatus.FAULT && Math.random() < 0.001) {
       status = TurbineStatus.FAULT;
    } else if (status !== TurbineStatus.FAULT && Math.random() < 0.005) {
       status = TurbineStatus.IDLE;
    } else if (status === TurbineStatus.IDLE && Math.random() < 0.01) {
       status = TurbineStatus.OPERATING;
    }


    switch (status) {
        case TurbineStatus.OPERATING:
            powerOutput = Math.max(0, 2.8 + (Math.random() - 0.5) * 2);
            windSpeed = Math.max(3, 12 + (Math.random() - 0.5) * 8);
            rotorSpeed = Math.max(0, 15 + (Math.random() - 0.5) * 5);
            vibration += (Math.random() - 0.5) * 0.05;
            break;
        case TurbineStatus.IDLE:
            powerOutput = 0;
            rotorSpeed = Math.min(rotorSpeed, 2 + Math.random());
            windSpeed += (Math.random() - 0.5) * 2;
            break;
        case TurbineStatus.FAULT:
            powerOutput = 0;
            rotorSpeed = 0;
            vibration = Math.min(3, vibration + Math.random() * 0.1);
            temperature = Math.min(95, temperature + Math.random() * 0.5);
            break;
        case TurbineStatus.OFFLINE:
            powerOutput = 0;
            rotorSpeed = 0;
            windSpeed = 0;
            vibration = 0;
            break;
    }
    
    // Clamp values to realistic ranges
    const newHistory = [...history.slice(1), { time: Date.now(), power: powerOutput }];

    return {
        ...turbine,
        status,
        powerOutput: parseFloat(powerOutput.toFixed(2)),
        windSpeed: parseFloat(Math.max(0, windSpeed).toFixed(2)),
        rotorSpeed: parseFloat(Math.max(0, rotorSpeed).toFixed(2)),
        bladeAngle: parseFloat(Math.max(0, bladeAngle + (Math.random() - 0.5) * 0.1).toFixed(2)),
        temperature: parseFloat(Math.max(20, Math.min(95, temperature)).toFixed(2)),
        vibration: parseFloat(Math.max(0, Math.min(3, vibration)).toFixed(2)),
        voltage: parseFloat((690 + (Math.random() - 0.5) * 20).toFixed(2)),
        current: parseFloat((status === TurbineStatus.OPERATING ? 2500 + (Math.random() - 0.5) * 200 : 0).toFixed(2)),
        history: newHistory,
    };
};


export const useMockTurbineData = () => {
  const [turbines, setTurbines] = useState<TurbineData[]>(createInitialTurbineData());

  useEffect(() => {
    const interval = setInterval(() => {
      setTurbines(prevTurbines =>
        prevTurbines.map(turbine => updateTurbineData(turbine))
      );
    }, 2000); // Update every 2 seconds

    return () => clearInterval(interval);
  }, []);

  const updateTurbineStatus = useCallback((turbineId: number, newStatus: TurbineStatus) => {
    setTurbines(prev => prev.map(t => t.id === turbineId ? {...t, status: newStatus} : t));
  }, []);

  return { turbines, updateTurbineStatus };
};

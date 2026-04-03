import { useState } from 'react';
import { type AppSettings, DataSourceType } from '../types';

const SETTINGS_KEY = 'windFarmAppSettings_v2';
const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

const defaultSettings: AppSettings = {
    dataSource: DataSourceType.SIMULATION,
    opcDa: { server: 'localhost', progId: 'BACHMANN.OPCEnterpriseServer.2' },
    modbusTcp: { ip: '10.128.0.1', port: 502, slaveId: 1 },
    simulation: { turbineCount: 14, baseWindSpeed: 10.0, turbulenceIntensity: 0.1 },
};

export const useSettings = () => {
    const [settings, setSettings] = useState<AppSettings>(() => {
        try {
            const item = window.localStorage.getItem(SETTINGS_KEY);
            const storedSettings = item ? JSON.parse(item) : {};
            return { ...defaultSettings, ...storedSettings };
        } catch (error) {
            console.error("Error reading settings from localStorage", error);
            return defaultSettings;
        }
    });

    const saveSettings = (newSettings: AppSettings) => {
        try {
            const prevSettings = settings;
            setSettings(newSettings);
            window.localStorage.setItem(SETTINGS_KEY, JSON.stringify(newSettings));

            // Only sync simulation config if params actually changed
            if (newSettings.dataSource === DataSourceType.SIMULATION) {
                const simChanged =
                    prevSettings.simulation.turbineCount !== newSettings.simulation.turbineCount ||
                    prevSettings.simulation.turbulenceIntensity !== newSettings.simulation.turbulenceIntensity;
                if (simChanged) {
                    fetch(`${API_BASE}/api/config/simulation`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            turbineCount: newSettings.simulation.turbineCount,
                            baseWindSpeed: newSettings.simulation.baseWindSpeed,
                            turbulenceIntensity: newSettings.simulation.turbulenceIntensity,
                        }),
                    }).catch(err => console.warn('Failed to sync simulation config:', err.message));
                }
            } else if (newSettings.dataSource === DataSourceType.OPC_DA) {
                fetch(`${API_BASE}/api/config/datasource`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        mode: 'opc_da',
                        opcServer: newSettings.opcDa.server,
                        opcProgId: newSettings.opcDa.progId,
                        opcHost: newSettings.opcDa.server,
                    }),
                }).catch(err => console.warn('Failed to sync OPC config:', err.message));
            }
        } catch (error) {
            console.error('Error saving settings to localStorage', error);
        }
    };

    return { settings, saveSettings };
};

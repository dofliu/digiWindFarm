import { useState } from 'react';
import { type AppSettings, DataSourceType } from '../types';

const SETTINGS_KEY = 'windFarmAppSettings_v1';

const defaultSettings: AppSettings = {
    dataSource: DataSourceType.MOCK,
    opcDa: { server: 'localhost', progId: 'Matrikon.OPC.Simulation.1' },
    modbusTcp: { ip: '10.128.0.1', port: 502, slaveId: 1 },
};

export const useSettings = () => {
    const [settings, setSettings] = useState<AppSettings>(() => {
        try {
            const item = window.localStorage.getItem(SETTINGS_KEY);
            // Merge stored settings with defaults to ensure all keys are present
            const storedSettings = item ? JSON.parse(item) : {};
            return { ...defaultSettings, ...storedSettings };
        } catch (error) {
            console.error("Error reading settings from localStorage", error);
            return defaultSettings;
        }
    });

    const saveSettings = (newSettings: AppSettings) => {
        try {
            setSettings(newSettings);
            window.localStorage.setItem(SETTINGS_KEY, JSON.stringify(newSettings));
        } catch (error) {
            console.error('Error saving settings to localStorage', error);
        }
    };

    return { settings, saveSettings };
};

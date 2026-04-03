import React, { useState, useEffect } from 'react';
import { type AppSettings, DataSourceType } from '../types';

interface SettingsPageProps {
    settings: AppSettings;
    onSave: (settings: AppSettings) => void;
}

const SettingsPage: React.FC<SettingsPageProps> = ({ settings, onSave }) => {
    const [formData, setFormData] = useState<AppSettings>(settings);
    const [saveStatus, setSaveStatus] = useState<'idle' | 'success'>('idle');

    useEffect(() => {
        setFormData(settings);
    }, [settings]);

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        const { name, value, type } = e.target;
        const [section, key] = name.split('.');

        const parsedValue = type === 'number' ? parseFloat(value) || 0 : value;

        if (section === 'dataSource') {
             setFormData(prev => ({ ...prev, dataSource: value as DataSourceType }));
        } else {
             setFormData(prev => ({
                ...prev,
                [section]: {
                    // @ts-ignore
                    ...prev[section],
                    [key]: parsedValue,
                },
            }));
        }
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onSave(formData);
        setSaveStatus('success');
        setTimeout(() => setSaveStatus('idle'), 2000);
    };

    return (
        <div>
            <h2 className="text-3xl font-bold font-orbitron mb-6 text-white">System Settings</h2>
            <div className="max-w-4xl mx-auto bg-gray-800/50 rounded-lg shadow-lg border border-gray-700">
                <form onSubmit={handleSubmit}>
                    <div className="p-6 space-y-6">
                        {/* Data Source Selection */}
                        <div className="bg-gray-900/50 p-4 rounded-md">
                            <label htmlFor="dataSource" className="block text-lg font-medium text-cyan-300 mb-2">
                                Data Source
                            </label>
                            <select
                                id="dataSource"
                                name="dataSource"
                                value={formData.dataSource}
                                onChange={handleInputChange}
                                className="w-full bg-gray-700 border border-gray-600 rounded-md p-2 text-white focus:ring-cyan-500 focus:border-cyan-500"
                            >
                                <option value={DataSourceType.MOCK}>Mock Data (Frontend Only)</option>
                                <option value={DataSourceType.SIMULATION}>Physics Simulation (Backend)</option>
                                <option value={DataSourceType.OPC_DA}>OPC DA Server (Real Wind Farm)</option>
                                <option value={DataSourceType.MODBUS_TCP}>Modbus TCP Gateway</option>
                            </select>
                            <p className="text-xs text-gray-400 mt-2">
                                Mock: frontend random data. Simulation: physics-based model via backend API. OPC DA: real wind farm connection.
                            </p>
                        </div>

                        {/* Simulation Settings */}
                        {(formData.dataSource === DataSourceType.SIMULATION) && (
                            <div className="bg-gray-900/50 p-4 rounded-md border-l-4 border-green-500">
                                <h3 className="text-lg font-semibold text-white mb-3">Simulation Settings</h3>
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                    <div>
                                        <label htmlFor="simTurbineCount" className="block text-sm font-medium text-gray-300">Turbine Count</label>
                                        <input
                                            type="number"
                                            id="simTurbineCount"
                                            name="simulation.turbineCount"
                                            value={formData.simulation.turbineCount}
                                            onChange={handleInputChange}
                                            min={1}
                                            max={100}
                                            className="mt-1 w-full bg-gray-700 border border-gray-600 rounded-md p-2 text-white focus:ring-cyan-500 focus:border-cyan-500"
                                        />
                                    </div>
                                    <div>
                                        <label htmlFor="simBaseWind" className="block text-sm font-medium text-gray-300">Base Wind Speed (m/s)</label>
                                        <input
                                            type="number"
                                            id="simBaseWind"
                                            name="simulation.baseWindSpeed"
                                            value={formData.simulation.baseWindSpeed}
                                            onChange={handleInputChange}
                                            step={0.5}
                                            min={0}
                                            max={30}
                                            className="mt-1 w-full bg-gray-700 border border-gray-600 rounded-md p-2 text-white focus:ring-cyan-500 focus:border-cyan-500"
                                        />
                                    </div>
                                    <div>
                                        <label htmlFor="simTurbulence" className="block text-sm font-medium text-gray-300">Turbulence Intensity</label>
                                        <input
                                            type="number"
                                            id="simTurbulence"
                                            name="simulation.turbulenceIntensity"
                                            value={formData.simulation.turbulenceIntensity}
                                            onChange={handleInputChange}
                                            step={0.01}
                                            min={0}
                                            max={0.5}
                                            className="mt-1 w-full bg-gray-700 border border-gray-600 rounded-md p-2 text-white focus:ring-cyan-500 focus:border-cyan-500"
                                        />
                                    </div>
                                </div>
                                <p className="text-xs text-gray-400 mt-3">
                                    Physics simulation uses wind model with daily patterns, Cp curve, and subsystem models (gearbox, generator, pitch, yaw).
                                    Changing these will restart the simulator.
                                </p>
                            </div>
                        )}

                        {/* OPC DA Settings */}
                        {formData.dataSource === DataSourceType.OPC_DA && (
                            <div className="bg-gray-900/50 p-4 rounded-md border-l-4 border-cyan-500">
                                <h3 className="text-lg font-semibold text-white mb-3">OPC DA Server Settings</h3>
                                <div className="space-y-4">
                                    <div>
                                        <label htmlFor="opcServer" className="block text-sm font-medium text-gray-300">Server Name / IP</label>
                                        <input
                                            type="text"
                                            id="opcServer"
                                            name="opcDa.server"
                                            value={formData.opcDa.server}
                                            onChange={handleInputChange}
                                            className="mt-1 w-full bg-gray-700 border border-gray-600 rounded-md p-2 text-white focus:ring-cyan-500 focus:border-cyan-500"
                                            placeholder="e.g., localhost or 10.128.1.10"
                                        />
                                    </div>
                                    <div>
                                        <label htmlFor="opcProgId" className="block text-sm font-medium text-gray-300">Program ID (ProgID)</label>
                                        <input
                                            type="text"
                                            id="opcProgId"
                                            name="opcDa.progId"
                                            value={formData.opcDa.progId}
                                            onChange={handleInputChange}
                                            className="mt-1 w-full bg-gray-700 border border-gray-600 rounded-md p-2 text-white focus:ring-cyan-500 focus:border-cyan-500"
                                            placeholder="e.g., BACHMANN.OPCEnterpriseServer.2"
                                        />
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Modbus TCP Settings */}
                        {formData.dataSource === DataSourceType.MODBUS_TCP && (
                           <div className="bg-gray-900/50 p-4 rounded-md border-l-4 border-cyan-500">
                                <h3 className="text-lg font-semibold text-white mb-3">Modbus TCP Gateway Settings</h3>
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                    <div>
                                        <label htmlFor="modbusIp" className="block text-sm font-medium text-gray-300">IP Address</label>
                                        <input
                                            type="text"
                                            id="modbusIp"
                                            name="modbusTcp.ip"
                                            value={formData.modbusTcp.ip}
                                            onChange={handleInputChange}
                                            className="mt-1 w-full bg-gray-700 border border-gray-600 rounded-md p-2 text-white focus:ring-cyan-500 focus:border-cyan-500"
                                            placeholder="e.g., 10.128.1.12"
                                        />
                                    </div>
                                    <div>
                                        <label htmlFor="modbusPort" className="block text-sm font-medium text-gray-300">Port</label>
                                        <input
                                            type="number"
                                            id="modbusPort"
                                            name="modbusTcp.port"
                                            value={formData.modbusTcp.port}
                                            onChange={handleInputChange}
                                            className="mt-1 w-full bg-gray-700 border border-gray-600 rounded-md p-2 text-white focus:ring-cyan-500 focus:border-cyan-500"
                                        />
                                    </div>
                                    <div>
                                        <label htmlFor="modbusSlaveId" className="block text-sm font-medium text-gray-300">Slave ID</label>
                                        <input
                                            type="number"
                                            id="modbusSlaveId"
                                            name="modbusTcp.slaveId"
                                            value={formData.modbusTcp.slaveId}
                                            onChange={handleInputChange}
                                            className="mt-1 w-full bg-gray-700 border border-gray-600 rounded-md p-2 text-white focus:ring-cyan-500 focus:border-cyan-500"
                                        />
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* API Info */}
                        <div className="bg-gray-900/50 p-4 rounded-md border-l-4 border-gray-600">
                            <h3 className="text-lg font-semibold text-white mb-2">API Endpoints</h3>
                            <div className="text-sm text-gray-400 space-y-1 font-mono">
                                <p>GET  /api/turbines — All turbines (latest data)</p>
                                <p>GET  /api/turbines/farm-status — Farm KPIs</p>
                                <p>GET  /api/turbines/WT001/history — Historical data</p>
                                <p>GET  /api/export/snapshot — Export current state</p>
                                <p>GET  /api/export/history?turbine_id=WT001&format=csv</p>
                                <p>WS   /ws/realtime — WebSocket real-time stream</p>
                            </div>
                        </div>
                    </div>
                    <div className="p-4 bg-gray-900/50 border-t border-gray-700 flex justify-end items-center">
                        {saveStatus === 'success' && (
                           <span className="text-green-400 mr-4 text-sm transition-opacity">Settings saved!</span>
                        )}
                        <button
                            type="submit"
                            className="bg-cyan-600 hover:bg-cyan-700 text-white font-bold py-2 px-6 rounded-lg transition-all"
                        >
                            Save Settings
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default SettingsPage;

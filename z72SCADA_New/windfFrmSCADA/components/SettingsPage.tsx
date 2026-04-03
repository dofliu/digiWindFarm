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
        
        const parsedValue = type === 'number' ? parseInt(value, 10) || 0 : value;

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
            <h2 className="text-3xl font-bold font-orbitron mb-6 text-white">通訊設定 (Communication Settings)</h2>
            <div className="max-w-4xl mx-auto bg-gray-800/50 rounded-lg shadow-lg border border-gray-700">
                <form onSubmit={handleSubmit}>
                    <div className="p-6 space-y-6">
                        {/* Data Source Selection */}
                        <div className="bg-gray-900/50 p-4 rounded-md">
                            <label htmlFor="dataSource" className="block text-lg font-medium text-cyan-300 mb-2">
                                數據來源 (Data Source)
                            </label>
                            <select
                                id="dataSource"
                                name="dataSource"
                                value={formData.dataSource}
                                onChange={handleInputChange}
                                className="w-full bg-gray-700 border border-gray-600 rounded-md p-2 text-white focus:ring-cyan-500 focus:border-cyan-500"
                            >
                                <option value={DataSourceType.MOCK}>模擬數據 (Mock Data)</option>
                                <option value={DataSourceType.OPC_DA}>OPC DA Server</option>
                                <option value={DataSourceType.MODBUS_TCP}>Modbus TCP Gateway</option>
                            </select>
                            <p className="text-xs text-gray-400 mt-2">
                                當前系統數據來源。選擇 OPC DA 或 Modbus TCP 需要後端服務支援才能實際連線。
                            </p>
                        </div>

                        {/* OPC DA Settings */}
                        {formData.dataSource === DataSourceType.OPC_DA && (
                            <div className="bg-gray-900/50 p-4 rounded-md border-l-4 border-cyan-500">
                                <h3 className="text-lg font-semibold text-white mb-3">OPC DA Server 設定</h3>
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
                                            placeholder="e.g., Matrikon.OPC.Simulation.1"
                                        />
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Modbus TCP Settings */}
                        {formData.dataSource === DataSourceType.MODBUS_TCP && (
                           <div className="bg-gray-900/50 p-4 rounded-md border-l-4 border-cyan-500">
                                <h3 className="text-lg font-semibold text-white mb-3">Modbus TCP Gateway 設定</h3>
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
                    </div>
                    <div className="p-4 bg-gray-900/50 border-t border-gray-700 flex justify-end items-center">
                        {saveStatus === 'success' && (
                           <span className="text-green-400 mr-4 text-sm transition-opacity">Settings saved successfully!</span>
                        )}
                        <button
                            type="submit"
                            className="bg-cyan-600 hover:bg-cyan-700 text-white font-bold py-2 px-6 rounded-lg transition-all"
                        >
                            儲存設定 (Save Settings)
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default SettingsPage;

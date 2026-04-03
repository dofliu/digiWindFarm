import React, { useState, useEffect } from 'react';
import { type AppSettings, DataSourceType } from '../types';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

interface SettingsPageProps {
    settings: AppSettings;
    onSave: (settings: AppSettings) => void;
    lang?: 'en' | 'zh';
}

const WIND_PROFILES = [
    { id: 'auto', en: 'Auto (Daily Pattern)', zh: '自動（日變化模式）' },
    { id: 'calm', en: 'Calm (2 m/s) — Turbines Idle', zh: '平靜 (2 m/s) — 風機待機' },
    { id: 'moderate', en: 'Moderate (8 m/s) — Partial Load', zh: '中等 (8 m/s) — 部分負載' },
    { id: 'rated', en: 'Rated (12 m/s) — Full Power', zh: '額定 (12 m/s) — 滿載發電' },
    { id: 'strong', en: 'Strong (18 m/s) — Pitch Active', zh: '強風 (18 m/s) — 變槳調節' },
    { id: 'storm', en: 'Storm (26 m/s) — Emergency Stop', zh: '暴風 (26 m/s) — 緊急停機' },
    { id: 'gusty', en: 'Gusty (10 m/s, high turbulence)', zh: '陣風 (10 m/s, 高湍流)' },
    { id: 'ramp_up', en: 'Ramp Up (3→15 m/s)', zh: '漸增 (3→15 m/s)' },
    { id: 'ramp_down', en: 'Ramp Down (15→3 m/s)', zh: '漸減 (15→3 m/s)' },
];

const SettingsPage: React.FC<SettingsPageProps> = ({ settings, onSave, lang = 'zh' }) => {
    const [formData, setFormData] = useState<AppSettings>(settings);
    const [saveStatus, setSaveStatus] = useState<'idle' | 'success'>('idle');

    // Wind control state
    const [windStatus, setWindStatus] = useState<any>(null);
    const [windProfile, setWindProfile] = useState('auto');
    const [customWind, setCustomWind] = useState({ speed: '10', direction: '270', temp: '25', turbulence: '0.1' });
    const [windMsg, setWindMsg] = useState('');

    const refreshWindStatus = () => {
        fetch(`${API_BASE}/api/config/wind`).then(r => r.json()).then(setWindStatus).catch(() => {});
    };

    useEffect(() => {
        refreshWindStatus();
        const iv = setInterval(refreshWindStatus, 5000);
        return () => clearInterval(iv);
    }, []);

    const handleSetProfile = async (profile: string) => {
        setWindProfile(profile);
        await fetch(`${API_BASE}/api/config/wind`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ profile }),
        });
        setWindMsg(lang === 'zh' ? `已切換: ${profile}` : `Switched to: ${profile}`);
        refreshWindStatus();
        setTimeout(() => setWindMsg(''), 3000);
    };

    const handleSetCustomWind = async () => {
        await fetch(`${API_BASE}/api/config/wind`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                windSpeed: parseFloat(customWind.speed) || null,
                windDirection: parseFloat(customWind.direction) || null,
                ambientTemp: parseFloat(customWind.temp) || null,
                turbulence: parseFloat(customWind.turbulence) || null,
            }),
        });
        setWindMsg(lang === 'zh' ? '已套用自訂風況' : 'Custom wind applied');
        refreshWindStatus();
        setTimeout(() => setWindMsg(''), 3000);
    };

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

                        {/* Wind Condition Control */}
                        {(formData.dataSource === DataSourceType.SIMULATION) && (
                            <div className="bg-gray-900/50 p-4 rounded-md border-l-4 border-blue-500">
                                <h3 className="text-lg font-semibold text-white mb-3">
                                    {lang === 'zh' ? '風況控制' : 'Wind Condition Control'}
                                </h3>

                                {/* Current status */}
                                {windStatus && (
                                    <div className="mb-3 text-sm text-gray-400">
                                        {lang === 'zh' ? '目前模式' : 'Current mode'}: <span className="text-white font-semibold">{windStatus.mode}</span>
                                        {windStatus.profile && <span className="ml-2">({windStatus.profile})</span>}
                                        {windStatus.override_wind_speed != null && (
                                            <span className="ml-3">{lang === 'zh' ? '風速' : 'Wind'}: <span className="text-cyan-300">{windStatus.override_wind_speed} m/s</span></span>
                                        )}
                                    </div>
                                )}

                                {/* Profile quick buttons */}
                                <div className="mb-4">
                                    <label className="block text-sm text-gray-300 mb-2">{lang === 'zh' ? '快速情境' : 'Quick Profiles'}</label>
                                    <div className="flex flex-wrap gap-2">
                                        {WIND_PROFILES.map(p => (
                                            <button key={p.id} onClick={() => handleSetProfile(p.id)}
                                                className={`text-xs px-3 py-1.5 rounded-md border transition-colors ${
                                                    windProfile === p.id || windStatus?.profile === p.id
                                                    ? 'bg-blue-600 border-blue-500 text-white'
                                                    : 'bg-gray-700 border-gray-600 text-gray-300 hover:border-blue-400'
                                                }`}>
                                                {lang === 'zh' ? p.zh : p.en}
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                {/* Custom values */}
                                <div className="mb-3">
                                    <label className="block text-sm text-gray-300 mb-2">{lang === 'zh' ? '自訂風況' : 'Custom Values'}</label>
                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                                        <div>
                                            <label className="text-xs text-gray-500">{lang === 'zh' ? '風速 (m/s)' : 'Wind Speed (m/s)'}</label>
                                            <input type="number" step="0.5" min="0" max="40" value={customWind.speed}
                                                onChange={e => setCustomWind(p => ({...p, speed: e.target.value}))}
                                                className="mt-1 w-full bg-gray-700 border border-gray-600 rounded px-2 py-1.5 text-sm text-white" />
                                        </div>
                                        <div>
                                            <label className="text-xs text-gray-500">{lang === 'zh' ? '風向 (°)' : 'Direction (°)'}</label>
                                            <input type="number" step="5" min="0" max="360" value={customWind.direction}
                                                onChange={e => setCustomWind(p => ({...p, direction: e.target.value}))}
                                                className="mt-1 w-full bg-gray-700 border border-gray-600 rounded px-2 py-1.5 text-sm text-white" />
                                        </div>
                                        <div>
                                            <label className="text-xs text-gray-500">{lang === 'zh' ? '溫度 (°C)' : 'Temp (°C)'}</label>
                                            <input type="number" step="1" min="-10" max="45" value={customWind.temp}
                                                onChange={e => setCustomWind(p => ({...p, temp: e.target.value}))}
                                                className="mt-1 w-full bg-gray-700 border border-gray-600 rounded px-2 py-1.5 text-sm text-white" />
                                        </div>
                                        <div>
                                            <label className="text-xs text-gray-500">{lang === 'zh' ? '湍流度' : 'Turbulence'}</label>
                                            <input type="number" step="0.05" min="0" max="0.5" value={customWind.turbulence}
                                                onChange={e => setCustomWind(p => ({...p, turbulence: e.target.value}))}
                                                className="mt-1 w-full bg-gray-700 border border-gray-600 rounded px-2 py-1.5 text-sm text-white" />
                                        </div>
                                    </div>
                                    <button onClick={handleSetCustomWind}
                                        className="mt-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold px-4 py-1.5 rounded transition-colors">
                                        {lang === 'zh' ? '套用自訂風況' : 'Apply Custom Wind'}
                                    </button>
                                </div>

                                {windMsg && <div className="text-sm text-cyan-300 bg-cyan-900/30 px-3 py-1 rounded mt-2">{windMsg}</div>}

                                <p className="text-xs text-gray-500 mt-2">
                                    {lang === 'zh'
                                        ? '設定風況後，物理模型會自動計算對應的功率、轉速、溫度、振動等所有 SCADA 數據。選「自動」回到日變化模式。'
                                        : 'After setting wind conditions, the physics model automatically computes all SCADA outputs. Select "Auto" to return to daily pattern.'}
                                </p>
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

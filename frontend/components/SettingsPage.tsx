import React, { useState, useEffect } from 'react';
import { type AppSettings, DataSourceType } from '../types';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8100';

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

const GRID_PROFILES = [
    { id: 'auto', en: 'Auto Grid', zh: '自動電網' },
    { id: 'nominal', en: 'Nominal (50 Hz / 690 V)', zh: '標稱 (50 Hz / 690 V)' },
    { id: 'low_freq', en: 'Low Frequency', zh: '低頻事件' },
    { id: 'high_freq', en: 'High Frequency', zh: '高頻事件' },
    { id: 'undervoltage', en: 'Undervoltage', zh: '欠壓事件' },
    { id: 'overvoltage', en: 'Overvoltage', zh: '過壓事件' },
    { id: 'weak_grid', en: 'Weak Grid', zh: '弱電網' },
    { id: 'recovery', en: 'Recovery Ramp', zh: '電網恢復' },
];

const SettingsPage: React.FC<SettingsPageProps> = ({ settings, onSave, lang = 'zh' }) => {
    const [formData, setFormData] = useState<AppSettings>(settings);
    const [saveStatus, setSaveStatus] = useState<'idle' | 'success'>('idle');

    // Wind control state
    const [windStatus, setWindStatus] = useState<any>(null);
    const [windProfile, setWindProfile] = useState('auto');
    const [customWind, setCustomWind] = useState({ speed: '10', direction: '270', temp: '25', turbulence: '0.1' });
    const [windMsg, setWindMsg] = useState('');
    const [gridStatus, setGridStatus] = useState<any>(null);
    const [gridProfile, setGridProfile] = useState('auto');
    const [customGrid, setCustomGrid] = useState({ frequency: '50.0', voltage: '690' });
    const [gridMsg, setGridMsg] = useState('');

    const [apiConnected, setApiConnected] = useState<boolean | null>(null);

    const refreshWindStatus = () => {
        fetch(`${API_BASE}/api/config/wind`)
            .then(r => { setApiConnected(true); return r.json(); })
            .then(setWindStatus)
            .catch(() => { setApiConnected(false); });
    };
    const refreshGridStatus = () => {
        fetch(`${API_BASE}/api/config/grid`)
            .then(r => r.json()).then(setGridStatus).catch(() => {});
    };

    useEffect(() => {
        refreshWindStatus();
        refreshGridStatus();
        const iv = setInterval(() => {
            refreshWindStatus();
            refreshGridStatus();
        }, 5000);
        return () => clearInterval(iv);
    }, []);

    const handleSetProfile = async (profile: string) => {
        setWindProfile(profile);
        try {
            const res = await fetch(`${API_BASE}/api/config/wind`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ profile }),
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            setWindMsg(lang === 'zh' ? `已切換: ${profile}` : `Switched to: ${profile}`);
            setApiConnected(true);
        } catch (e) {
            setWindMsg(lang === 'zh' ? `無法設定風況 (${API_BASE} 無回應)` : `Failed to set wind (${API_BASE} not responding)`);
            setApiConnected(false);
        }
        refreshWindStatus();
        setTimeout(() => setWindMsg(''), 5000);
    };

    const handleSetCustomWind = async () => {
        try {
            const res = await fetch(`${API_BASE}/api/config/wind`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    windSpeed: parseFloat(customWind.speed) || null,
                    windDirection: parseFloat(customWind.direction) || null,
                    ambientTemp: parseFloat(customWind.temp) || null,
                    turbulence: parseFloat(customWind.turbulence) || null,
                }),
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            setWindMsg(lang === 'zh' ? '已套用自訂風況' : 'Custom wind applied');
            setApiConnected(true);
        } catch (e) {
            setWindMsg(lang === 'zh' ? `無法設定風況 (${API_BASE} 無回應)` : `Failed to set wind (${API_BASE} not responding)`);
            setApiConnected(false);
        }
        refreshWindStatus();
        setTimeout(() => setWindMsg(''), 5000);
    };

    const handleSetGridProfile = async (profile: string) => {
        setGridProfile(profile);
        await fetch(`${API_BASE}/api/config/grid`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ profile }),
        });
        setGridMsg(lang === 'zh' ? `已切換電網: ${profile}` : `Switched grid: ${profile}`);
        refreshGridStatus();
        setTimeout(() => setGridMsg(''), 3000);
    };

    const handleSetCustomGrid = async () => {
        await fetch(`${API_BASE}/api/config/grid`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                frequencyHz: parseFloat(customGrid.frequency) || null,
                voltageV: parseFloat(customGrid.voltage) || null,
            }),
        });
        setGridMsg(lang === 'zh' ? '已套用自訂電網' : 'Custom grid applied');
        refreshGridStatus();
        setTimeout(() => setGridMsg(''), 3000);
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

    // Turbine spec state
    const [turbineSpec, setTurbineSpec] = useState<any>(null);
    const [specPresets, setSpecPresets] = useState<Record<string, any>>({});
    const [specMsg, setSpecMsg] = useState('');
    const [editSpec, setEditSpec] = useState<Record<string, string>>({});

    useEffect(() => {
        fetch(`${API_BASE}/api/config/turbine-spec`).then(r => r.json()).then(spec => {
            setTurbineSpec(spec);
            setEditSpec({
                rated_power_kw: String(spec.rated_power_kw || 5000),
                rotor_diameter: String(spec.rotor_diameter || 126),
                cut_in_speed: String(spec.cut_in_speed || 3),
                rated_speed: String(spec.rated_speed || 12),
                cut_out_speed: String(spec.cut_out_speed || 25),
                gear_ratio: String(spec.gear_ratio || 100),
                max_rotor_rpm: String(spec.max_rotor_rpm || 15),
                nominal_voltage: String(spec.nominal_voltage || 690),
                curtailment_kw: spec.curtailment_kw != null ? String(spec.curtailment_kw) : '',
            });
        }).catch(() => {});
        fetch(`${API_BASE}/api/config/turbine-spec/presets`).then(r => r.json()).then(setSpecPresets).catch(() => {});
    }, []);

    const handleSetPreset = async (preset: string) => {
        const res = await fetch(`${API_BASE}/api/config/turbine-spec`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ preset }),
        });
        if (res.ok) {
            const data = await res.json();
            setTurbineSpec(data.spec);
            setEditSpec({
                rated_power_kw: String(data.spec.rated_power_kw),
                rotor_diameter: String(data.spec.rotor_diameter),
                cut_in_speed: String(data.spec.cut_in_speed),
                rated_speed: String(data.spec.rated_speed),
                cut_out_speed: String(data.spec.cut_out_speed),
                gear_ratio: String(data.spec.gear_ratio),
                max_rotor_rpm: String(data.spec.max_rotor_rpm),
                nominal_voltage: String(data.spec.nominal_voltage),
                curtailment_kw: data.spec.curtailment_kw != null ? String(data.spec.curtailment_kw) : '',
            });
            setSpecMsg(lang === 'zh' ? `已套用: ${preset}` : `Applied: ${preset}`);
            setTimeout(() => setSpecMsg(''), 3000);
        }
    };

    const handleApplySpec = async () => {
        const payload: Record<string, any> = {};
        for (const [k, v] of Object.entries(editSpec)) {
            if (v === '') {
                payload[k] = null;
            } else {
                payload[k] = parseFloat(v);
            }
        }
        const res = await fetch(`${API_BASE}/api/config/turbine-spec`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        if (res.ok) {
            const data = await res.json();
            setTurbineSpec(data.spec);
            setSpecMsg(lang === 'zh' ? '已更新風機規格' : 'Turbine spec updated');
            setTimeout(() => setSpecMsg(''), 3000);
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

                        {/* Turbine Specification */}
                        {(formData.dataSource === DataSourceType.SIMULATION) && (
                            <div className="bg-gray-900/50 p-4 rounded-md border-l-4 border-purple-500">
                                <h3 className="text-lg font-semibold text-white mb-3">
                                    {lang === 'zh' ? '風機規格設定' : 'Turbine Specification'}
                                </h3>

                                {/* Presets */}
                                <div className="mb-4">
                                    <label className="block text-sm text-gray-300 mb-2">{lang === 'zh' ? '預設機型' : 'Presets'}</label>
                                    <div className="flex flex-wrap gap-2">
                                        {Object.entries(specPresets).map(([name, spec]) => (
                                            <button key={name} onClick={() => handleSetPreset(name)}
                                                className="text-xs px-3 py-1.5 rounded-md border bg-gray-700 border-gray-600 text-gray-300 hover:border-purple-400 transition-colors">
                                                {name} ({(spec as any).rated_power_kw}kW)
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                {/* Editable fields */}
                                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 mb-3">
                                    {[
                                        { key: 'rated_power_kw', label_zh: '額定功率 (kW)', label_en: 'Rated Power (kW)' },
                                        { key: 'rotor_diameter', label_zh: '葉輪直徑 (m)', label_en: 'Rotor Diameter (m)' },
                                        { key: 'cut_in_speed', label_zh: '切入風速 (m/s)', label_en: 'Cut-in Speed (m/s)' },
                                        { key: 'rated_speed', label_zh: '額定風速 (m/s)', label_en: 'Rated Speed (m/s)' },
                                        { key: 'cut_out_speed', label_zh: '切出風速 (m/s)', label_en: 'Cut-out Speed (m/s)' },
                                        { key: 'gear_ratio', label_zh: '齒輪比', label_en: 'Gear Ratio' },
                                        { key: 'max_rotor_rpm', label_zh: '最大轉速 (RPM)', label_en: 'Max Rotor RPM' },
                                        { key: 'nominal_voltage', label_zh: '額定電壓 (V)', label_en: 'Nominal Voltage (V)' },
                                    ].map(f => (
                                        <div key={f.key}>
                                            <label className="text-xs text-gray-500">{lang === 'zh' ? f.label_zh : f.label_en}</label>
                                            <input type="number" step="any" value={editSpec[f.key] || ''}
                                                onChange={e => setEditSpec(p => ({...p, [f.key]: e.target.value}))}
                                                className="mt-1 w-full bg-gray-700 border border-gray-600 rounded px-2 py-1.5 text-sm text-white" />
                                        </div>
                                    ))}
                                </div>

                                {/* Curtailment */}
                                <div className="mb-3 p-3 bg-gray-800/80 rounded border border-yellow-500/30">
                                    <label className="text-sm font-semibold text-yellow-300">
                                        {lang === 'zh' ? '功率限載 (kW)' : 'Power Curtailment (kW)'}
                                    </label>
                                    <div className="flex items-center gap-3 mt-1">
                                        <input type="number" step="100" min="0" value={editSpec.curtailment_kw || ''}
                                            onChange={e => setEditSpec(p => ({...p, curtailment_kw: e.target.value}))}
                                            placeholder={lang === 'zh' ? '留空=不限載' : 'Empty=no curtailment'}
                                            className="flex-1 bg-gray-700 border border-gray-600 rounded px-2 py-1.5 text-sm text-white" />
                                        <span className="text-xs text-gray-500">
                                            {lang === 'zh'
                                                ? `額定: ${editSpec.rated_power_kw || '5000'} kW`
                                                : `Rated: ${editSpec.rated_power_kw || '5000'} kW`}
                                        </span>
                                    </div>
                                    <p className="text-xs text-gray-500 mt-1">
                                        {lang === 'zh'
                                            ? '限載後 pitch 角度會自動增加以限制輸出功率'
                                            : 'Curtailment increases pitch angle to limit output power'}
                                    </p>
                                </div>

                                <button onClick={handleApplySpec}
                                    className="bg-purple-600 hover:bg-purple-700 text-white text-sm font-semibold px-4 py-1.5 rounded transition-colors">
                                    {lang === 'zh' ? '套用風機規格' : 'Apply Turbine Spec'}
                                </button>

                                {specMsg && <span className="ml-3 text-sm text-cyan-300">{specMsg}</span>}
                            </div>
                        )}

                        {/* API Connection Warning */}
                        {apiConnected === false && (
                            <div className="bg-red-900/30 border border-red-500/50 rounded-md p-4 mb-4">
                                <div className="text-red-300 font-semibold">
                                    {lang === 'zh' ? '無法連線到後端 API' : 'Cannot connect to backend API'}
                                </div>
                                <div className="text-red-400/80 text-sm mt-1">
                                    {lang === 'zh'
                                        ? `請確認後端伺服器正在運行。目前嘗試連線: ${API_BASE}`
                                        : `Please ensure the backend server is running. Trying: ${API_BASE}`}
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

                        {(formData.dataSource === DataSourceType.SIMULATION) && (
                            <div className="bg-gray-900/50 p-4 rounded-md border-l-4 border-orange-500">
                                <h3 className="text-lg font-semibold text-white mb-3">
                                    {lang === 'zh' ? '電網條件控制' : 'Grid Condition Control'}
                                </h3>

                                {gridStatus && (
                                    <div className="mb-3 text-sm text-gray-400">
                                        {lang === 'zh' ? '目前模式' : 'Current mode'}: <span className="text-white font-semibold">{gridStatus.mode}</span>
                                        {gridStatus.profile && <span className="ml-2">({gridStatus.profile})</span>}
                                        {gridStatus.override_frequency_hz != null && (
                                            <span className="ml-3">{lang === 'zh' ? '頻率' : 'Frequency'}: <span className="text-orange-300">{gridStatus.override_frequency_hz} Hz</span></span>
                                        )}
                                        {gridStatus.override_voltage_v != null && (
                                            <span className="ml-3">{lang === 'zh' ? '電壓' : 'Voltage'}: <span className="text-orange-300">{gridStatus.override_voltage_v} V</span></span>
                                        )}
                                    </div>
                                )}

                                <div className="mb-4">
                                    <label className="block text-sm text-gray-300 mb-2">{lang === 'zh' ? '電網情境' : 'Grid Profiles'}</label>
                                    <div className="flex flex-wrap gap-2">
                                        {GRID_PROFILES.map(p => (
                                            <button key={p.id} onClick={() => handleSetGridProfile(p.id)}
                                                className={`text-xs px-3 py-1.5 rounded-md border transition-colors ${
                                                    gridProfile === p.id || gridStatus?.profile === p.id
                                                    ? 'bg-orange-600 border-orange-500 text-white'
                                                    : 'bg-gray-700 border-gray-600 text-gray-300 hover:border-orange-400'
                                                }`}>
                                                {lang === 'zh' ? p.zh : p.en}
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                <div className="mb-3">
                                    <label className="block text-sm text-gray-300 mb-2">{lang === 'zh' ? '自訂電網' : 'Custom Grid'}</label>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                        <div>
                                            <label className="text-xs text-gray-500">{lang === 'zh' ? '頻率 (Hz)' : 'Frequency (Hz)'}</label>
                                            <input type="number" step="0.05" min="45" max="55" value={customGrid.frequency}
                                                onChange={e => setCustomGrid(p => ({ ...p, frequency: e.target.value }))}
                                                className="mt-1 w-full bg-gray-700 border border-gray-600 rounded px-2 py-1.5 text-sm text-white" />
                                        </div>
                                        <div>
                                            <label className="text-xs text-gray-500">{lang === 'zh' ? '電壓 (V)' : 'Voltage (V)'}</label>
                                            <input type="number" step="1" min="500" max="800" value={customGrid.voltage}
                                                onChange={e => setCustomGrid(p => ({ ...p, voltage: e.target.value }))}
                                                className="mt-1 w-full bg-gray-700 border border-gray-600 rounded px-2 py-1.5 text-sm text-white" />
                                        </div>
                                    </div>
                                    <button onClick={handleSetCustomGrid}
                                        className="mt-2 bg-orange-600 hover:bg-orange-700 text-white text-sm font-semibold px-4 py-1.5 rounded transition-colors">
                                        {lang === 'zh' ? '套用自訂電網' : 'Apply Custom Grid'}
                                    </button>
                                </div>

                                {gridMsg && <div className="text-sm text-orange-300 bg-orange-900/30 px-3 py-1 rounded mt-2">{gridMsg}</div>}

                                <p className="text-xs text-gray-500 mt-2">
                                    {lang === 'zh'
                                        ? '電網事件會影響併網條件、功率降載，以及在偏差過大時觸發正常或緊急停機。'
                                        : 'Grid events affect synchronization, power derating, and can trigger normal or emergency shutdowns under severe deviations.'}
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

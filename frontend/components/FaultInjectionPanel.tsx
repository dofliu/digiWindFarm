import React, { useState, useEffect } from 'react';
import type { FaultScenario } from '../types';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

interface FaultInjectionPanelProps {
  lang?: 'en' | 'zh';
}

const FaultInjectionPanel: React.FC<FaultInjectionPanelProps> = ({ lang = 'zh' }) => {
  const [scenarios, setScenarios] = useState<FaultScenario[]>([]);
  const [selectedScenario, setSelectedScenario] = useState('');
  const [selectedTurbine, setSelectedTurbine] = useState('WT001');
  const [severityRate, setSeverityRate] = useState('0.005');
  const [activeFaults, setActiveFaults] = useState<any[]>([]);
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetch(`${API_BASE}/api/faults/scenarios`)
      .then(r => r.json()).then(setScenarios).catch(() => {});
    refreshActive();
    const iv = setInterval(refreshActive, 3000);
    return () => clearInterval(iv);
  }, []);

  const refreshActive = () => {
    fetch(`${API_BASE}/api/faults/active`)
      .then(r => r.json()).then(setActiveFaults).catch(() => {});
  };

  const handleInject = async () => {
    if (!selectedScenario) return;
    const res = await fetch(`${API_BASE}/api/faults/inject`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        scenarioId: selectedScenario,
        turbineId: selectedTurbine,
        severityRate: parseFloat(severityRate),
      }),
    });
    if (res.ok) {
      setMessage(lang === 'zh' ? `已注入故障到 ${selectedTurbine}` : `Fault injected into ${selectedTurbine}`);
      refreshActive();
    }
    setTimeout(() => setMessage(''), 3000);
  };

  const handleClearAll = async () => {
    await fetch(`${API_BASE}/api/faults/clear`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    });
    setMessage(lang === 'zh' ? '已清除所有故障' : 'All faults cleared');
    refreshActive();
    setTimeout(() => setMessage(''), 3000);
  };

  const phaseColors: Record<string, string> = {
    incipient: 'text-yellow-400',
    developing: 'text-orange-400',
    advanced: 'text-red-400',
    critical: 'text-red-300 font-bold',
  };

  const turbineOptions = Array.from({length: 14}, (_, i) => `WT${String(i+1).padStart(3, '0')}`);

  return (
    <div className="bg-gray-800/50 rounded-lg p-6 border border-gray-700">
      <h3 className="text-xl font-bold text-white mb-4">
        {lang === 'zh' ? '故障模擬控制台' : 'Fault Injection Console'}
      </h3>

      {/* Inject form */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 mb-4">
        <select value={selectedScenario} onChange={e => setSelectedScenario(e.target.value)}
          className="bg-gray-700 text-white rounded px-3 py-2 text-sm">
          <option value="">{lang === 'zh' ? '-- 選擇故障場景 --' : '-- Select Scenario --'}</option>
          {scenarios.map(s => (
            <option key={s.id} value={s.id}>{lang === 'zh' ? s.name_zh : s.name_en}</option>
          ))}
        </select>
        <select value={selectedTurbine} onChange={e => setSelectedTurbine(e.target.value)}
          className="bg-gray-700 text-white rounded px-3 py-2 text-sm">
          {turbineOptions.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
        <div className="flex items-center space-x-2">
          <label className="text-gray-400 text-xs whitespace-nowrap">{lang === 'zh' ? '速率' : 'Rate'}:</label>
          <input type="number" step="0.001" min="0.0001" max="0.1" value={severityRate}
            onChange={e => setSeverityRate(e.target.value)}
            className="bg-gray-700 text-white rounded px-3 py-2 text-sm w-full" />
        </div>
        <button onClick={handleInject} disabled={!selectedScenario}
          className="bg-red-600 hover:bg-red-700 disabled:bg-gray-600 text-white font-bold py-2 px-4 rounded text-sm transition-colors">
          {lang === 'zh' ? '注入故障' : 'Inject Fault'}
        </button>
        <button onClick={handleClearAll}
          className="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded text-sm transition-colors">
          {lang === 'zh' ? '清除全部' : 'Clear All'}
        </button>
      </div>

      {message && (
        <div className="mb-3 text-sm text-cyan-300 bg-cyan-900/30 px-3 py-1 rounded">{message}</div>
      )}

      {/* Active faults table */}
      {activeFaults.length > 0 && (
        <div className="mt-4">
          <h4 className="text-sm text-gray-400 mb-2">{lang === 'zh' ? '活躍故障' : 'Active Faults'} ({activeFaults.length})</h4>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-gray-500 text-xs border-b border-gray-700">
                  <th className="text-left py-1 px-2">{lang === 'zh' ? '風機' : 'Turbine'}</th>
                  <th className="text-left py-1 px-2">{lang === 'zh' ? '故障' : 'Fault'}</th>
                  <th className="text-left py-1 px-2">{lang === 'zh' ? '嚴重度' : 'Severity'}</th>
                  <th className="text-left py-1 px-2">{lang === 'zh' ? '階段' : 'Phase'}</th>
                  <th className="text-left py-1 px-2">{lang === 'zh' ? '告警' : 'Alarms'}</th>
                </tr>
              </thead>
              <tbody>
                {activeFaults.map((f, i) => (
                  <tr key={i} className="border-b border-gray-800">
                    <td className="py-1.5 px-2 text-white font-mono">{f.turbine_id}</td>
                    <td className="py-1.5 px-2 text-gray-300">{lang === 'zh' ? f.name_zh : f.name_en}</td>
                    <td className="py-1.5 px-2">
                      <div className="flex items-center space-x-2">
                        <div className="w-20 h-2 bg-gray-700 rounded-full overflow-hidden">
                          <div className={`h-full rounded-full ${f.severity > 0.7 ? 'bg-red-500' : f.severity > 0.4 ? 'bg-orange-500' : 'bg-yellow-500'}`}
                            style={{width: `${f.severity * 100}%`}} />
                        </div>
                        <span className="text-gray-400 text-xs">{(f.severity * 100).toFixed(0)}%</span>
                      </div>
                    </td>
                    <td className={`py-1.5 px-2 text-xs capitalize ${phaseColors[f.phase] || ''}`}>
                      {f.phase} {f.tripped && '(TRIP)'}
                    </td>
                    <td className="py-1.5 px-2 text-xs text-gray-500">
                      {f.active_alarms?.map((a: any) => `[${a.type}]`).join(' ') || '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default FaultInjectionPanel;

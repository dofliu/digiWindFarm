import React, { useState, useEffect } from 'react';
import type { FaultScenario } from '../types';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

interface TestPlan {
  id: string;
  name_en: string;
  name_zh: string;
  description_en: string;
  description_zh: string;
  duration_hours: number;
  fault_count: number;
  turbines_affected: string[];
  scenarios_used: string[];
}

interface TestPlanResult {
  status: string;
  plan_id: string;
  duration_hours: number;
  total_readings: number;
  faults_injected: number;
  final_fault_status: any[];
  storage_stats: any;
}

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

  // Test plans state
  const [testPlans, setTestPlans] = useState<TestPlan[]>([]);
  const [runningPlan, setRunningPlan] = useState<string | null>(null);
  const [planResult, setPlanResult] = useState<TestPlanResult | null>(null);

  const u = (en: string, zh: string) => lang === 'zh' ? zh : en;

  useEffect(() => {
    fetch(`${API_BASE}/api/faults/scenarios`)
      .then(r => r.json()).then(setScenarios).catch(() => {});
    fetch(`${API_BASE}/api/faults/test-plans`)
      .then(r => r.json()).then(setTestPlans).catch(() => {});
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

  const handleRunPlan = async (planId: string) => {
    setRunningPlan(planId);
    setPlanResult(null);
    setMessage(u(`Running test plan "${planId}"... This may take a moment.`,
                 `正在執行測試計畫「${planId}」... 請稍候。`));
    try {
      const res = await fetch(`${API_BASE}/api/faults/test-plans/${planId}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ time_step: 10 }),
      });
      const data = await res.json();
      setPlanResult(data);
      setMessage(u(`Test plan "${planId}" completed!`, `測試計畫「${planId}」執行完成！`));
      refreshActive();
    } catch {
      setMessage(u('Test plan execution failed', '測試計畫執行失敗'));
    } finally {
      setRunningPlan(null);
      setTimeout(() => setMessage(''), 8000);
    }
  };

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
          <h4 className="text-sm text-gray-400 mb-2">{u('Active Faults', '活躍故障')} ({activeFaults.length})</h4>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-gray-500 text-xs border-b border-gray-700">
                  <th className="text-left py-1 px-2">{u('Turbine', '風機')}</th>
                  <th className="text-left py-1 px-2">{u('Fault', '故障')}</th>
                  <th className="text-left py-1 px-2">{u('Severity', '嚴重度')}</th>
                  <th className="text-left py-1 px-2">{u('Phase', '階段')}</th>
                  <th className="text-left py-1 px-2">{u('Alarms', '告警')}</th>
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

      {/* ════════════════════════════════════════════════════════════════ */}
      {/* Test Plans Section */}
      {/* ════════════════════════════════════════════════════════════════ */}
      <div className="mt-8 border-t border-gray-600 pt-6">
        <h3 className="text-xl font-bold text-white mb-2">
          {u('Diagnostic Test Plans', '故障診斷測試計畫')}
        </h3>
        <p className="text-sm text-gray-400 mb-4">
          {u('Generate simulated historical data with pre-scheduled fault injections for testing external diagnosis systems.',
             '產生含預排程故障注入的模擬歷史資料，用於測試外部故障診斷系統。')}
        </p>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {testPlans.map(plan => {
            const isRunning = runningPlan === plan.id;
            const difficultyColor =
              plan.id === 'basic_validation' ? 'border-green-500/30' :
              plan.id === 'subtle_challenge' ? 'border-yellow-500/30' :
              plan.id === 'mixed_difficulty' ? 'border-orange-500/30' :
              'border-red-500/30';
            const difficultyLabel =
              plan.id === 'basic_validation' ? u('Easy', '簡單') :
              plan.id === 'subtle_challenge' ? u('Hard', '困難') :
              plan.id === 'mixed_difficulty' ? u('Mixed', '混合') :
              u('Extreme', '極限');
            const difficultyBadgeColor =
              plan.id === 'basic_validation' ? 'bg-green-500/20 text-green-300' :
              plan.id === 'subtle_challenge' ? 'bg-yellow-500/20 text-yellow-300' :
              plan.id === 'mixed_difficulty' ? 'bg-orange-500/20 text-orange-300' :
              'bg-red-500/20 text-red-300';

            return (
              <div key={plan.id} className={`bg-gray-800/60 rounded-lg p-4 border ${difficultyColor}`}>
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <h4 className="text-white font-semibold">{lang === 'zh' ? plan.name_zh : plan.name_en}</h4>
                    <span className={`text-xs px-2 py-0.5 rounded ${difficultyBadgeColor}`}>
                      {difficultyLabel}
                    </span>
                  </div>
                  <div className="text-right text-xs text-gray-500">
                    <div>{plan.duration_hours}h</div>
                    <div>{plan.fault_count} {u('faults', '故障')}</div>
                  </div>
                </div>

                <p className="text-xs text-gray-400 mb-3">
                  {lang === 'zh' ? plan.description_zh : plan.description_en}
                </p>

                <div className="flex flex-wrap gap-1 mb-3">
                  {plan.turbines_affected.sort().map(t => (
                    <span key={t} className="text-xs bg-gray-700 text-gray-300 px-1.5 py-0.5 rounded">{t}</span>
                  ))}
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex flex-wrap gap-1">
                    {plan.scenarios_used.map(s => (
                      <span key={s} className="text-xs text-gray-500">{s}</span>
                    ))}
                  </div>
                  <button
                    onClick={() => handleRunPlan(plan.id)}
                    disabled={isRunning || runningPlan !== null}
                    className={`px-4 py-1.5 rounded text-sm font-semibold transition-colors ${
                      isRunning
                        ? 'bg-yellow-600 text-white animate-pulse cursor-wait'
                        : runningPlan !== null
                        ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                        : 'bg-purple-600 hover:bg-purple-700 text-white'
                    }`}>
                    {isRunning
                      ? u('Running...', '執行中...')
                      : u('Run', '執行')}
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {/* Test Plan Result */}
        {planResult && (
          <div className="mt-4 bg-gray-800/60 rounded-lg p-4 border border-purple-500/30">
            <h4 className="text-sm font-semibold text-purple-400 mb-3">
              {u('Test Plan Result', '測試計畫結果')} — {planResult.plan_id}
            </h4>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
              <div className="text-center">
                <div className="text-2xl font-orbitron font-bold text-white">{planResult.duration_hours}h</div>
                <div className="text-xs text-gray-400">{u('Duration', '時長')}</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-orbitron font-bold text-cyan-300">{planResult.total_readings.toLocaleString()}</div>
                <div className="text-xs text-gray-400">{u('Readings', '數據筆數')}</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-orbitron font-bold text-orange-300">{planResult.faults_injected}</div>
                <div className="text-xs text-gray-400">{u('Faults Injected', '注入故障數')}</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-orbitron font-bold text-gray-300">{planResult.storage_stats?.db_size_mb} MB</div>
                <div className="text-xs text-gray-400">{u('DB Size', '資料庫大小')}</div>
              </div>
            </div>

            {planResult.final_fault_status && planResult.final_fault_status.length > 0 && (
              <>
                <h5 className="text-xs text-gray-400 mb-2">{u('Final Fault Status', '最終故障狀態')}</h5>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="text-gray-500 border-b border-gray-700">
                        <th className="text-left py-1 px-2">{u('Turbine', '風機')}</th>
                        <th className="text-left py-1 px-2">{u('Scenario', '場景')}</th>
                        <th className="text-left py-1 px-2">{u('Severity', '嚴重度')}</th>
                        <th className="text-left py-1 px-2">{u('Phase', '階段')}</th>
                        <th className="text-left py-1 px-2">{u('Tripped', '跳脫')}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {planResult.final_fault_status.map((f: any, i: number) => (
                        <tr key={i} className="border-b border-gray-800">
                          <td className="py-1 px-2 text-white font-mono">{f.turbine_id}</td>
                          <td className="py-1 px-2 text-gray-300">{f.scenario_id}</td>
                          <td className="py-1 px-2">
                            <div className="flex items-center space-x-1">
                              <div className="w-16 h-1.5 bg-gray-700 rounded-full overflow-hidden">
                                <div className={`h-full rounded-full ${f.severity > 0.7 ? 'bg-red-500' : f.severity > 0.4 ? 'bg-orange-500' : 'bg-yellow-500'}`}
                                  style={{width: `${f.severity * 100}%`}} />
                              </div>
                              <span className="text-gray-400">{(f.severity * 100).toFixed(0)}%</span>
                            </div>
                          </td>
                          <td className={`py-1 px-2 capitalize ${phaseColors[f.phase] || ''}`}>{f.phase}</td>
                          <td className="py-1 px-2">{f.tripped
                            ? <span className="text-red-400 font-bold">TRIP</span>
                            : <span className="text-green-400">-</span>}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default FaultInjectionPanel;

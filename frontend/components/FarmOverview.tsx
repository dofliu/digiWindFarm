import React, { useState, useMemo } from 'react';
import { type TurbineData, TurbineStatus, type AppSettings, DataSourceType } from '../types';
import StatusIndicator from './StatusIndicator';
import { WindTurbineIcon } from './icons';
import FarmTrendChart from './FarmTrendChart';

/** Format power: show kW when < 1 MW, otherwise MW */
const fmtPower = (mw: number): string => {
  const kw = mw * 1000;
  if (Math.abs(kw) < 1) return '0 kW';
  if (Math.abs(mw) < 1.0) return `${kw.toFixed(0)} kW`;
  return `${mw.toFixed(2)} MW`;
};

interface FarmOverviewProps {
  turbines: TurbineData[];
  onSelectTurbine: (turbine: TurbineData) => void;
  settings: AppSettings;
  lang?: 'en' | 'zh';
}

type ViewMode = 'cards' | 'summary' | 'table';

const TUR_STATE_SHORT: Record<number, string> = {
  1: 'STOP', 2: 'STBY', 3: 'WAIT', 4: 'PREP',
  5: 'START', 6: 'PROD', 7: 'SHTDN', 8: 'RSTR', 9: 'NSTP',
};

// ─── Card View (original) ─────────────────────────────────────────

const TurbineCard: React.FC<{ turbine: TurbineData; onSelect: (t: TurbineData) => void; lang: string }> = ({ turbine, onSelect, lang }) => {
  const getStatusColorClasses = (status: TurbineStatus) => {
    switch (status) {
      case TurbineStatus.OPERATING: return 'border-green-500/50 hover:border-green-500 bg-green-500/10';
      case TurbineStatus.IDLE: return 'border-yellow-500/50 hover:border-yellow-500 bg-yellow-500/10';
      case TurbineStatus.FAULT: return 'border-red-500/50 hover:border-red-500 bg-red-500/10 animate-pulse';
      case TurbineStatus.OFFLINE: return 'border-gray-600/50 hover:border-gray-500 bg-gray-600/10';
    }
  };
  const hasFaults = turbine.activeFaults && turbine.activeFaults.length > 0;

  return (
    <div className={`relative rounded-lg p-4 border transition-all duration-300 cursor-pointer group ${getStatusColorClasses(turbine.status)}`}
      onClick={() => onSelect(turbine)}>
      <div className="flex justify-between items-start">
        <div>
          <h3 className="font-bold text-lg text-white">{turbine.name}</h3>
          {turbine.turState && <span className="text-xs text-gray-500 font-mono">{TUR_STATE_SHORT[turbine.turState] || turbine.turState}</span>}
        </div>
        <StatusIndicator status={turbine.status} />
      </div>
      <div className="mt-3 flex items-end justify-between">
        <div>
          <p className="text-xs text-gray-400">{lang === 'zh' ? '發電功率' : 'Power'}</p>
          <p className="font-orbitron text-2xl font-bold text-white">{fmtPower(turbine.powerOutput)}</p>
        </div>
        <div className="text-right">
          <p className="text-xs text-gray-400">{lang === 'zh' ? '風速' : 'Wind'}</p>
          <p className="text-white">{turbine.windSpeed.toFixed(1)} m/s</p>
        </div>
      </div>
      <div className="mt-2 flex justify-between text-xs text-gray-500">
        <span>{lang === 'zh' ? '轉速' : 'RPM'}: {turbine.rotorSpeed.toFixed(1)}</span>
        <span>{lang === 'zh' ? '溫度' : 'Temp'}: {turbine.temperature.toFixed(0)}°C</span>
        <span>{lang === 'zh' ? '振動' : 'Vib'}: {turbine.vibration.toFixed(1)}</span>
      </div>
      {hasFaults && (
        <div className="mt-2 text-xs">
          {turbine.activeFaults!.map((f, i) => (
            <div key={i} className={`px-2 py-0.5 rounded ${
              f.phase === 'critical' ? 'bg-red-500/30 text-red-300' : f.phase === 'advanced' ? 'bg-orange-500/20 text-orange-300' : 'bg-yellow-500/20 text-yellow-300'
            }`}>{lang === 'zh' ? f.name_zh : f.name_en} ({(f.severity * 100).toFixed(0)}%)</div>
          ))}
        </div>
      )}
      <div className="absolute bottom-4 right-4 text-gray-600 group-hover:text-cyan-400 transition-colors">
        <WindTurbineIcon className="w-10 h-10 opacity-20 group-hover:opacity-40" />
      </div>
    </div>
  );
};

// ─── Summary View (compact cards + stats panel) ───────────────────

const SummaryView: React.FC<{ turbines: TurbineData[]; onSelect: (t: TurbineData) => void; lang: string }> = ({ turbines, onSelect, lang }) => {
  const stats = useMemo(() => {
    const operating = turbines.filter(t => t.status === TurbineStatus.OPERATING);
    const fault = turbines.filter(t => t.status === TurbineStatus.FAULT);
    const idle = turbines.filter(t => t.status === TurbineStatus.IDLE);
    const service = turbines.filter(t => t.turState === 9 || (t.scadaTags && t.scadaTags['WSRV_SrvOn'] === 1));
    const totalPower = turbines.reduce((s, t) => s + t.powerOutput, 0);
    const avgWind = turbines.length > 0 ? turbines.reduce((s, t) => s + t.windSpeed, 0) / turbines.length : 0;
    const avgTemp = turbines.length > 0 ? turbines.reduce((s, t) => s + t.temperature, 0) / turbines.length : 0;
    return { operating, fault, idle, service, totalPower, avgWind, avgTemp };
  }, [turbines]);

  const u = (en: string, zh: string) => lang === 'zh' ? zh : en;

  return (
    <div className="flex flex-col lg:flex-row gap-4">
      {/* Stats panel */}
      <div className="lg:w-80 flex-shrink-0 space-y-3">
        <div className="bg-gray-800/50 rounded-lg p-4 border border-cyan-500/30">
          <h3 className="text-sm text-gray-400 mb-3 uppercase tracking-wider">{u('Farm Statistics', '風場統計')}</h3>
          <div className="space-y-2">
            <StatRow label={u('Total Power', '總發電量')} value={fmtPower(stats.totalPower)} color="text-cyan-300" />
            <StatRow label={u('Avg Wind Speed', '平均風速')} value={`${stats.avgWind.toFixed(1)} m/s`} />
            <StatRow label={u('Avg Temperature', '平均溫度')} value={`${stats.avgTemp.toFixed(1)} °C`} />
            <div className="border-t border-gray-700 my-2" />
            <StatRow label={u('Total Turbines', '風機數量')} value={`${turbines.length}`} />
            <StatRow label={u('Operating', '運轉中')} value={`${stats.operating.length}`} color="text-green-400" />
            <StatRow label={u('Idle / Standby', '待機/停機')} value={`${stats.idle.length}`} color="text-yellow-400" />
            <StatRow label={u('Fault', '故障')} value={`${stats.fault.length}`} color={stats.fault.length > 0 ? 'text-red-400' : ''} />
            <StatRow label={u('Service / Inspection', '定檢中')} value={`${stats.service.length}`} color={stats.service.length > 0 ? 'text-orange-400' : ''} />
            <div className="border-t border-gray-700 my-2" />
            <StatRow label={u('Capacity Factor', '容量因數')} value={`${turbines.length > 0 ? ((stats.totalPower / (turbines.length * 2)) * 100).toFixed(1) : 0}%`} />
          </div>
        </div>
      </div>

      {/* Right column: trend chart + compact grid */}
      <div className="flex-1 space-y-4">
        {/* Farm-wide trend chart */}
        <FarmTrendChart turbines={turbines} lang={lang} />

        {/* Compact turbine grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-7 gap-2">
          {turbines.map(t => (
            <div key={t.id} onClick={() => onSelect(t)}
              className={`rounded-md p-2 border cursor-pointer transition-all hover:scale-105 ${
                t.status === TurbineStatus.FAULT ? 'border-red-500/50 bg-red-500/10' :
                t.status === TurbineStatus.OPERATING ? 'border-green-500/30 bg-gray-800/50' :
                'border-gray-600/30 bg-gray-800/30'
              }`}>
              <div className="flex justify-between items-center mb-1">
                <span className="text-xs font-bold text-white">{t.name}</span>
                <span className={`w-2 h-2 rounded-full ${
                  t.status === TurbineStatus.OPERATING ? 'bg-green-400' :
                  t.status === TurbineStatus.FAULT ? 'bg-red-400 animate-pulse' :
                  'bg-yellow-400'
                }`} />
              </div>
              <div className="text-lg font-orbitron font-bold text-white">{fmtPower(t.powerOutput)}</div>
              <div className="text-xs text-gray-500">{t.windSpeed.toFixed(1)} m/s</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const StatRow: React.FC<{ label: string; value: string; color?: string }> = ({ label, value, color }) => (
  <div className="flex justify-between items-center">
    <span className="text-gray-400 text-sm">{label}</span>
    <span className={`font-mono font-semibold text-sm ${color || 'text-white'}`}>{value}</span>
  </div>
);

// ─── Table View (all turbines, 10 key columns) ───────────────────

const TableView: React.FC<{ turbines: TurbineData[]; onSelect: (t: TurbineData) => void; lang: string }> = ({ turbines, onSelect, lang }) => {
  const u = (en: string, zh: string) => lang === 'zh' ? zh : en;

  const columns = [
    { key: 'name', label: u('Turbine', '風機'), w: 'w-20' },
    { key: 'status', label: u('Status', '狀態'), w: 'w-24' },
    { key: 'powerOutput', label: u('Power (MW)', '功率 MW'), w: 'w-20' },
    { key: 'windSpeed', label: u('Wind (m/s)', '風速'), w: 'w-16' },
    { key: 'rotorSpeed', label: u('RPM', '轉速'), w: 'w-16' },
    { key: 'genStatorTemp1', label: u('Gen Temp °C', '發電機溫度'), w: 'w-20' },
    { key: 'vibrationX', label: u('Vib X', '振動X'), w: 'w-16' },
    { key: 'bladeAngle1', label: u('Blade°', '葉片角'), w: 'w-16' },
    { key: 'cnvGenFreq', label: u('Freq Hz', '頻率'), w: 'w-16' },
    { key: 'yawError', label: u('Yaw Err°', '偏航誤差'), w: 'w-16' },
  ];

  const getCellColor = (key: string, val: number | undefined) => {
    if (val == null) return '';
    if (key === 'genStatorTemp1' && val > 100) return 'text-red-400';
    if (key === 'genStatorTemp1' && val > 80) return 'text-yellow-400';
    if (key === 'vibrationX' && val > 4) return 'text-red-400';
    if (key === 'vibrationX' && val > 2) return 'text-yellow-400';
    if (key === 'yawError' && Math.abs(val) > 10) return 'text-yellow-400';
    return '';
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-700">
            {columns.map(c => (
              <th key={c.key} className={`text-left py-2 px-2 text-xs text-gray-500 uppercase ${c.w}`}>{c.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {turbines.map(t => (
            <tr key={t.id} onClick={() => onSelect(t)}
              className={`border-b border-gray-800 cursor-pointer hover:bg-gray-800/60 transition-colors ${
                t.status === TurbineStatus.FAULT ? 'bg-red-900/20' : ''
              }`}>
              <td className="py-1.5 px-2 text-white font-semibold">{t.name}</td>
              <td className="py-1.5 px-2"><StatusIndicator status={t.status} /></td>
              <td className="py-1.5 px-2 font-mono text-white font-bold">{t.powerOutput.toFixed(2)}</td>
              <td className="py-1.5 px-2 font-mono text-gray-300">{t.windSpeed.toFixed(1)}</td>
              <td className="py-1.5 px-2 font-mono text-gray-300">{t.rotorSpeed.toFixed(1)}</td>
              <td className={`py-1.5 px-2 font-mono ${getCellColor('genStatorTemp1', t.genStatorTemp1)}`}>
                {t.genStatorTemp1?.toFixed(1) ?? '--'}
              </td>
              <td className={`py-1.5 px-2 font-mono ${getCellColor('vibrationX', t.vibrationX)}`}>
                {t.vibrationX?.toFixed(2) ?? '--'}
              </td>
              <td className="py-1.5 px-2 font-mono text-gray-300">{t.bladeAngle1?.toFixed(1) ?? '--'}</td>
              <td className="py-1.5 px-2 font-mono text-gray-300">{t.cnvGenFreq?.toFixed(1) ?? '--'}</td>
              <td className={`py-1.5 px-2 font-mono ${getCellColor('yawError', t.yawError)}`}>
                {t.yawError?.toFixed(1) ?? '--'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

// ─── Main FarmOverview ────────────────────────────────────────────

const FarmOverview: React.FC<FarmOverviewProps> = ({ turbines, onSelectTurbine, settings, lang = 'zh' }) => {
  const [viewMode, setViewMode] = useState<ViewMode>('summary');
  const u = (en: string, zh: string) => lang === 'zh' ? zh : en;

  const viewButtons: { mode: ViewMode; label_en: string; label_zh: string }[] = [
    { mode: 'cards', label_en: 'Cards', label_zh: '卡片' },
    { mode: 'summary', label_en: 'Summary', label_zh: '摘要' },
    { mode: 'table', label_en: 'Table', label_zh: '列表' },
  ];

  return (
    <div>
      <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-6">
        <h2 className="text-3xl font-bold font-orbitron text-white">{u('Farm Overview', '風場總覽')}</h2>
        <div className="flex items-center gap-2 mt-2 md:mt-0">
          {/* View mode toggle */}
          <div className="flex bg-gray-800 rounded-md border border-gray-700 overflow-hidden">
            {viewButtons.map(b => (
              <button key={b.mode} onClick={() => setViewMode(b.mode)}
                className={`px-3 py-1 text-xs font-medium transition-colors ${
                  viewMode === b.mode ? 'bg-cyan-600 text-white' : 'text-gray-400 hover:text-white'
                }`}>
                {lang === 'zh' ? b.label_zh : b.label_en}
              </button>
            ))}
          </div>
          {settings.dataSource === DataSourceType.MOCK && (
            <div className="text-xs text-yellow-300 bg-yellow-900/50 border border-yellow-700 px-2 py-1 rounded-md">MOCK</div>
          )}
        </div>
      </div>

      {viewMode === 'cards' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {turbines.map(t => <TurbineCard key={t.id} turbine={t} onSelect={onSelectTurbine} lang={lang} />)}
        </div>
      )}
      {viewMode === 'summary' && <SummaryView turbines={turbines} onSelect={onSelectTurbine} lang={lang} />}
      {viewMode === 'table' && <TableView turbines={turbines} onSelect={onSelectTurbine} lang={lang} />}
    </div>
  );
};

export default FarmOverview;

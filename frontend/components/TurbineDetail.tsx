import React, { useState, useCallback, useEffect } from 'react';
import { type TurbineData, TurbineStatus, type WorkOrder, WorkOrderStatus, type FaultInfo } from '../types';
import StatusIndicator from './StatusIndicator';

import MiniTrendChart from './MiniTrendChart';
import TrendChartPanel from './TrendChartPanel';
import DataCard from './DataCard';
import { analyzeTurbineFault } from '../services/geminiService';
import { BackIcon, BrainIcon, BoltIcon, WindIcon, TempIcon, VibrationIcon, AngleIcon, SpeedIcon, WrenchScrewdriverIcon } from './icons';

interface TurbineDetailProps {
  turbine: TurbineData;
  onBack: () => void;
  onDispatch: (turbine: TurbineData, faultAnalysis: string) => void;
  activeWorkOrder?: WorkOrder;
  lang?: 'en' | 'zh';
}

const TUR_STATE_LABELS: Record<number, { en: string; zh: string }> = {
  1: { en: 'Shutdown', zh: '自動停機' },
  2: { en: 'Standby', zh: '待機中' },
  3: { en: 'Wait Restart', zh: '等待重啟' },
  4: { en: 'Pre-Production', zh: '發電準備' },
  5: { en: 'Start Production', zh: '啟動發電' },
  6: { en: 'Production', zh: '正常發電' },
  7: { en: 'Emergency Stop', zh: '緊急停機' },
  8: { en: 'Restart', zh: '重新啟動' },
  9: { en: 'Normal Stop', zh: '正常停機' },
};

const fmt = (v: number | undefined | null, digits = 1): string =>
  v != null ? v.toFixed(digits) : '--';

// Subsystem panel component
const SubsystemPanel: React.FC<{ title: string; children: React.ReactNode; color?: string }> = ({ title, children, color = 'cyan' }) => (
  <div className={`bg-gray-800/50 rounded-lg p-4 border border-${color}-500/20`}>
    <h4 className={`text-sm font-semibold text-${color}-400 mb-3 uppercase tracking-wider`}>{title}</h4>
    <div className="space-y-2">
      {children}
    </div>
  </div>
);

const DataRow: React.FC<{ label: string; value: string; warn?: boolean; alert?: boolean }> = ({ label, value, warn, alert }) => (
  <div className="flex justify-between items-center">
    <span className="text-gray-400 text-sm">{label}</span>
    <span className={`font-mono text-sm font-semibold ${alert ? 'text-red-400' : warn ? 'text-yellow-400' : 'text-white'}`}>
      {value}
    </span>
  </div>
);

const FaultBadge: React.FC<{ fault: FaultInfo; lang: string }> = ({ fault, lang }) => {
  const phaseColors: Record<string, string> = {
    incipient: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/50',
    developing: 'bg-orange-500/20 text-orange-300 border-orange-500/50',
    advanced: 'bg-red-500/20 text-red-300 border-red-500/50',
    critical: 'bg-red-600/30 text-red-200 border-red-500 animate-pulse',
  };
  return (
    <div className={`px-3 py-2 rounded-md border text-sm ${phaseColors[fault.phase] || ''}`}>
      <div className="font-bold">{lang === 'zh' ? fault.name_zh : fault.name_en}</div>
      <div className="flex items-center space-x-3 mt-1 text-xs">
        <span>Severity: {(fault.severity * 100).toFixed(1)}%</span>
        <span className="capitalize">{fault.phase}</span>
        {fault.tripped && <span className="text-red-400 font-bold">TRIPPED</span>}
      </div>
      {fault.active_alarms.length > 0 && (
        <div className="mt-1 space-y-0.5">
          {fault.active_alarms.map((a, i) => (
            <div key={i} className="text-xs opacity-80">[{a.type}] {a.desc}</div>
          ))}
        </div>
      )}
    </div>
  );
};

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8100';

const OperatorControlPanel: React.FC<{ turbineId: string; lang: string }> = ({ turbineId, lang }) => {
  const [controlStatus, setControlStatus] = useState<any>(null);
  const [curtailValue, setCurtailValue] = useState('');
  const [msg, setMsg] = useState('');

  const refresh = () => {
    fetch(`${API_BASE}/api/control/${turbineId}/status`).then(r => r.json()).then(setControlStatus).catch(() => {});
  };

  useEffect(() => {
    refresh();
    const iv = setInterval(refresh, 3000);
    return () => clearInterval(iv);
  }, [turbineId]);

  const sendCmd = async (command: string) => {
    await fetch(`${API_BASE}/api/control/command`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ turbineId, command }),
    });
    setMsg(`${command} OK`);
    refresh();
    setTimeout(() => setMsg(''), 2000);
  };

  const setCurtail = async () => {
    const val = curtailValue === '' ? null : parseFloat(curtailValue);
    await fetch(`${API_BASE}/api/control/curtail`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ turbineId, powerLimitKw: val }),
    });
    setMsg(val ? `${lang === 'zh' ? '限載' : 'Curtail'}: ${val} kW` : (lang === 'zh' ? '已解除限載' : 'Curtailment removed'));
    refresh();
    setTimeout(() => setMsg(''), 2000);
  };

  const isServiceMode = controlStatus?.service_mode;
  const isStopped = controlStatus?.operator_stop;
  const curtailKw = controlStatus?.curtailment_kw;
  const stopMode = controlStatus?.stop_mode;
  const shutdownCause = controlStatus?.shutdown_cause;

  return (
    <div className="bg-gray-800/50 rounded-lg p-4 mb-6 border border-gray-700">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-3">
        <h4 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">
          {lang === 'zh' ? '操作控制' : 'Operator Control'}
        </h4>
        <div className="flex items-center space-x-2 mt-2 sm:mt-0 text-xs">
          {isServiceMode && <span className="px-2 py-0.5 rounded bg-orange-500/20 text-orange-300 border border-orange-500/50">
            {lang === 'zh' ? '定檢模式' : 'Service Mode'}
          </span>}
          {isStopped && <span className="px-2 py-0.5 rounded bg-red-500/20 text-red-300 border border-red-500/50">
            {lang === 'zh' ? '手動停機' : 'Manual Stop'}
          </span>}
          {stopMode === 'emergency' && <span className="px-2 py-0.5 rounded bg-red-700/30 text-red-200 border border-red-500/60">
            {lang === 'zh' ? '緊急停機流程' : 'Emergency Stop'}
          </span>}
          {curtailKw != null && <span className="px-2 py-0.5 rounded bg-yellow-500/20 text-yellow-300 border border-yellow-500/50">
            {lang === 'zh' ? `限載 ${curtailKw} kW` : `Curtail ${curtailKw} kW`}
          </span>}
          {shutdownCause && shutdownCause !== 'idle' && (
            <span className="px-2 py-0.5 rounded bg-gray-700 text-gray-200 border border-gray-600">
              {lang === 'zh' ? `原因: ${shutdownCause}` : `Cause: ${shutdownCause}`}
            </span>
          )}
          {msg && <span className="text-cyan-300">{msg}</span>}
        </div>
      </div>
      <div className="flex flex-wrap gap-2 items-end">
        {/* Command buttons */}
        <button onClick={() => sendCmd('stop')}
          className="px-3 py-1.5 text-xs font-semibold rounded bg-red-600 hover:bg-red-700 text-white transition-colors">
          {lang === 'zh' ? '停機' : 'Stop'}
        </button>
        <button onClick={() => sendCmd('emergency_stop')}
          className="px-3 py-1.5 text-xs font-semibold rounded bg-red-800 hover:bg-red-900 text-white transition-colors">
          {lang === 'zh' ? '緊急停機' : 'Emergency Stop'}
        </button>
        <button onClick={() => sendCmd('start')}
          className="px-3 py-1.5 text-xs font-semibold rounded bg-green-600 hover:bg-green-700 text-white transition-colors">
          {lang === 'zh' ? '啟動' : 'Start'}
        </button>
        <button onClick={() => sendCmd('reset')}
          className="px-3 py-1.5 text-xs font-semibold rounded bg-blue-600 hover:bg-blue-700 text-white transition-colors">
          {lang === 'zh' ? '復位' : 'Reset'}
        </button>
        <button onClick={() => sendCmd(isServiceMode ? 'service_off' : 'service_on')}
          className={`px-3 py-1.5 text-xs font-semibold rounded transition-colors ${
            isServiceMode ? 'bg-orange-500 hover:bg-orange-600 text-white' : 'bg-gray-600 hover:bg-gray-500 text-gray-200'}`}>
          {lang === 'zh' ? (isServiceMode ? '結束定檢' : '進入定檢') : (isServiceMode ? 'Exit Service' : 'Service Mode')}
        </button>

        <div className="border-l border-gray-600 h-6 mx-1" />

        {/* Curtailment */}
        <div className="flex items-center gap-1">
          <input type="number" step="100" min="0" value={curtailValue}
            onChange={e => setCurtailValue(e.target.value)}
            placeholder={lang === 'zh' ? '限載 kW' : 'kW limit'}
            className="w-24 bg-gray-700 border border-gray-600 rounded px-2 py-1 text-xs text-white" />
          <button onClick={setCurtail}
            className="px-2 py-1 text-xs rounded bg-yellow-600 hover:bg-yellow-700 text-white transition-colors">
            {lang === 'zh' ? '設定' : 'Set'}
          </button>
          {curtailKw != null && (
            <button onClick={() => { setCurtailValue(''); fetch(`${API_BASE}/api/control/curtail`, {
              method: 'POST', headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ turbineId, powerLimitKw: null }),
            }).then(refresh); setMsg(lang === 'zh' ? '已解除' : 'Cleared'); setTimeout(() => setMsg(''), 2000); }}
              className="px-2 py-1 text-xs rounded bg-gray-600 hover:bg-gray-500 text-gray-200 transition-colors">
              {lang === 'zh' ? '解除' : 'Clear'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

type DetailTab = 'overview' | 'generator' | 'pitch' | 'converter' | 'nacelle' | 'yaw' | 'grid' | 'fatigue';

const DETAIL_TABS: { id: DetailTab; label_en: string; label_zh: string; color: string; preset?: string }[] = [
  { id: 'overview', label_en: 'Overview', label_zh: '總覽', color: 'cyan' },
  { id: 'generator', label_en: 'Generator', label_zh: '發電機', color: 'cyan', preset: 'power' },
  { id: 'pitch', label_en: 'Pitch/Rotor', label_zh: '旋角系統', color: 'green', preset: 'pitch' },
  { id: 'converter', label_en: 'Converter', label_zh: '變頻器', color: 'purple', preset: 'converter' },
  { id: 'nacelle', label_en: 'Nacelle', label_zh: '機艙', color: 'yellow', preset: 'vibration' },
  { id: 'yaw', label_en: 'Yaw', label_zh: '轉向系統', color: 'blue', preset: 'yaw' },
  { id: 'grid', label_en: 'Grid/Met', label_zh: '電網/氣象', color: 'orange', preset: 'temperature' },
  { id: 'fatigue', label_en: 'Load/Fatigue', label_zh: '載荷/疲勞', color: 'red', preset: 'fatigue' },
];

const TurbineDetail: React.FC<TurbineDetailProps> = ({ turbine, onBack, onDispatch, activeWorkOrder, lang = 'zh' }) => {
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [analysisResult, setAnalysisResult] = useState<string | null>(null);
    const [analysisError, setAnalysisError] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState<DetailTab>('overview');

    useEffect(() => {
        if(turbine.status === TurbineStatus.FAULT && !analysisResult && !isAnalyzing) {
            handleAnalyzeFault();
        }
    }, [turbine.status, analysisResult, isAnalyzing]);

    const handleAnalyzeFault = useCallback(async () => {
        setIsAnalyzing(true);
        setAnalysisResult(null);
        setAnalysisError(null);
        try {
            const result = await analyzeTurbineFault(turbine);
            setAnalysisResult(result);
        } catch (error) {
            setAnalysisError('Failed to get analysis. Please try again.');
        } finally {
            setIsAnalyzing(false);
        }
    }, [turbine]);

    const formattedAnalysis = analysisResult?.split('\n').map((line, index) => {
        if (line.startsWith('**') || line.includes('Cause:') || line.includes('Actions:')) {
            return <p key={index} className="font-bold mt-2">{line.replace(/\*\*/g, '')}</p>;
        }
        if (line.match(/^\d+\./)) {
            return <p key={index} className="ml-4">{line}</p>;
        }
        return <p key={index}>{line}</p>;
    });

    const turStateLabel = TUR_STATE_LABELS[turbine.turState || 0];
    const turStateText = turStateLabel ? (lang === 'zh' ? turStateLabel.zh : turStateLabel.en) : `State ${turbine.turState}`;
    const hasFaults = turbine.activeFaults && turbine.activeFaults.length > 0;
    const turbineApiId = `WT${String(turbine.id).padStart(3, '0')}`;
    const u = (en: string, zh: string) => lang === 'zh' ? zh : en;

    const renderTabContent = () => {
      // Compact key metrics bar (replaces 3 large gauges)
      const metricsBar = (
        <div className="bg-gray-800/50 rounded-lg p-3 mb-4 flex flex-wrap items-center gap-4 border border-gray-700">
          <div className="flex items-center gap-2">
            <span className="text-gray-400 text-xs">{u('Power', '功率')}</span>
            <span className="text-cyan-300 font-bold text-lg font-orbitron">
              {turbine.powerOutput >= 1 ? `${fmt(turbine.powerOutput)} MW` : `${fmt(turbine.powerOutput * 1000, 0)} kW`}
            </span>
          </div>
          <div className="w-px h-5 bg-gray-600" />
          <div className="flex items-center gap-2">
            <span className="text-gray-400 text-xs">{u('RPM', '轉速')}</span>
            <span className="text-white font-bold text-lg font-orbitron">{fmt(turbine.rotorSpeed, 1)}</span>
          </div>
          <div className="w-px h-5 bg-gray-600" />
          <div className="flex items-center gap-2">
            <span className="text-gray-400 text-xs">{u('Wind', '風速')}</span>
            <span className="text-green-300 font-bold text-lg font-orbitron">{fmt(turbine.windSpeed, 1)} <span className="text-xs font-normal">m/s</span></span>
          </div>
          <div className="w-px h-5 bg-gray-600" />
          <div className="flex items-center gap-2">
            <span className="text-gray-400 text-xs">{u('Voltage', '電壓')}</span>
            <span className="text-white font-semibold">{fmt(turbine.voltage, 0)} V</span>
          </div>
          <div className="w-px h-5 bg-gray-600" />
          <div className="flex items-center gap-2">
            <span className="text-gray-400 text-xs">{u('Gen Freq', '頻率')}</span>
            <span className="text-white font-semibold">{fmt(turbine.cnvGenFreq, 2)} Hz</span>
          </div>
          <div className="ml-auto flex-shrink-0 w-40 h-10">
            <MiniTrendChart data={turbine.history} />
          </div>
        </div>
      );

      // Subsystem panel for the current tab (left side)
      const subsystemContent = (() => {
        switch (activeTab) {
          case 'overview':
            return (
              <div className="space-y-3">
                <SubsystemPanel title={u('WGEN Generator', 'WGEN 發電機')}>
                  <DataRow label={u('Power', '功率')} value={`${fmt(turbine.genPower)} kW`} />
                  <DataRow label={u('Speed', '轉速')} value={`${fmt(turbine.genSpeed, 0)} RPM`} />
                  <DataRow label={u('Stator Temp', '定子溫度')} value={`${fmt(turbine.genStatorTemp1)}°C`}
                    warn={(turbine.genStatorTemp1 || 0) > 100} alert={(turbine.genStatorTemp1 || 0) > 130} />
                  <DataRow label={u('Bearing Temp', '軸承溫度')} value={`${fmt(turbine.genBearingTemp1)}°C`}
                    warn={(turbine.genBearingTemp1 || 0) > 70} alert={(turbine.genBearingTemp1 || 0) > 90} />
                </SubsystemPanel>
                <SubsystemPanel title={u('WNAC Nacelle', 'WNAC 機艙')} color="yellow">
                  <DataRow label={u('Nacelle Temp', '機艙溫度')} value={`${fmt(turbine.nacelleTemp)}°C`} />
                  <DataRow label={u('Vibration X/Y', '振動 X/Y')} value={`${fmt(turbine.vibrationX, 2)} / ${fmt(turbine.vibrationY, 2)} mm/s`}
                    warn={(turbine.vibrationX || 0) > 4 || (turbine.vibrationY || 0) > 4} />
                </SubsystemPanel>
                <SubsystemPanel title={u('WROT Pitch', 'WROT 旋角')} color="green">
                  <DataRow label={u('Blades', '葉片角度')} value={`${fmt(turbine.bladeAngle1)}° / ${fmt(turbine.bladeAngle2)}° / ${fmt(turbine.bladeAngle3)}°`} />
                  <DataRow label={u('Locked/Brake', '鎖固/剎車')}
                    value={`${turbine.rotorLocked ? 'Locked' : '-'} / ${turbine.brakeActive ? 'Active' : '-'}`} />
                </SubsystemPanel>
              </div>
            );
          case 'generator':
            return (
              <SubsystemPanel title={u('WGEN Generator', 'WGEN 發電機')}>
                <DataRow label={u('Power', '功率')} value={`${fmt(turbine.genPower)} kW`} />
                <DataRow label={u('Speed', '轉速')} value={`${fmt(turbine.genSpeed, 0)} RPM`} />
                <DataRow label={u('Voltage', '電壓')} value={`${fmt(turbine.voltage, 0)} V`} />
                <DataRow label={u('Current', '電流')} value={`${fmt(turbine.current, 0)} A`} />
                <DataRow label={u('Stator Temp', '定子溫度')} value={`${fmt(turbine.genStatorTemp1)}°C`}
                  warn={(turbine.genStatorTemp1 || 0) > 100} alert={(turbine.genStatorTemp1 || 0) > 130} />
                <DataRow label={u('Air Gap Temp', '氣隙溫度')} value={`${fmt(turbine.genAirTemp1)}°C`}
                  warn={(turbine.genAirTemp1 || 0) > 80} />
                <DataRow label={u('Bearing Temp', '軸承溫度')} value={`${fmt(turbine.genBearingTemp1)}°C`}
                  warn={(turbine.genBearingTemp1 || 0) > 70} alert={(turbine.genBearingTemp1 || 0) > 90} />
              </SubsystemPanel>
            );
          case 'pitch':
            return (
              <SubsystemPanel title={u('WROT Rotor/Pitch', 'WROT 葉輪/旋角')} color="green">
                <DataRow label={u('Rotor RPM', '葉輪轉速')} value={`${fmt(turbine.rotorSpeed, 2)} RPM`} />
                <DataRow label={u('Blade 1', '葉片1角度')} value={`${fmt(turbine.bladeAngle1)}°`} />
                <DataRow label={u('Blade 2', '葉片2角度')} value={`${fmt(turbine.bladeAngle2)}°`} />
                <DataRow label={u('Blade 3', '葉片3角度')} value={`${fmt(turbine.bladeAngle3)}°`} />
                <DataRow label={u('Rotor Temp', '轉子溫度')} value={`${fmt(turbine.rotorTemp)}°C`} />
                <DataRow label={u('Hub Cab Temp', '輪毂櫃溫')} value={`${fmt(turbine.hubCabinetTemp)}°C`} />
                <DataRow label={u('Locked/Brake', '鎖固/剎車')}
                  value={`${turbine.rotorLocked ? 'Locked' : '-'} / ${turbine.brakeActive ? 'Active' : '-'}`} />
              </SubsystemPanel>
            );
          case 'converter':
            return (
              <SubsystemPanel title={u('WCNV Converter', 'WCNV 變頻器')} color="purple">
                <DataRow label={u('Gen Power', '發電機功率')} value={`${fmt(turbine.cnvGenPower)} kW`} />
                <DataRow label={u('Grid Power', '電網功率')} value={`${fmt(turbine.cnvGridPower)} kW`} />
                <DataRow label={u('Frequency', '頻率')} value={`${fmt(turbine.cnvGenFreq, 2)} Hz`} />
                <DataRow label={u('DC Voltage', 'DC電壓')} value={`${fmt(turbine.cnvDcVoltage, 0)} V`} />
                <DataRow label={u('Cabinet Temp', '控制櫃溫度')} value={`${fmt(turbine.cnvCabinetTemp)}°C`}
                  warn={(turbine.cnvCabinetTemp || 0) > 45} />
                <DataRow label={u('IGCT Water Temp', 'IGCT水溫')} value={`${fmt(turbine.igctWaterTemp)}°C`}
                  warn={(turbine.igctWaterTemp || 0) > 40} />
                <DataRow label={u('IGCT Pressure', 'IGCT水壓')} value={`${fmt(turbine.igctWaterPres1)} / ${fmt(turbine.igctWaterPres2)} bar`} />
                <div className="border-t border-purple-500/20 my-2 pt-2">
                  <div className="text-xs text-purple-300/60 mb-2">{u('Electrical Response', '電氣響應')}</div>
                  <DataRow label={u('Reactive Power', '無功功率')} value={`${fmt(turbine.reactivePower)} kvar`} />
                  <DataRow label={u('Power Factor', '功率因數')} value={fmt(turbine.powerFactor, 3)} />
                  <DataRow label={u('Apparent Power', '視在功率')} value={`${fmt(turbine.apparentPower)} kVA`} />
                  <DataRow label={u('Freq-Watt Derate', '頻率降額')} value={fmt(turbine.freqWattDerate, 3)}
                    warn={(turbine.freqWattDerate || 1) < 0.95} />
                  <DataRow label={u('Inertia Power', '慣量功率')} value={`${fmt(turbine.inertiaPower)} kW`} />
                  <DataRow label={u('Converter Mode', '變頻器模式')} value={
                    ['Idle', 'Starting', 'Normal', 'Freq Resp', 'V Support', 'Ride-Thru'][turbine.converterMode || 0] || '--'
                  } />
                  <DataRow label={u('Ride-Through', '電壓穿越')} value={`${turbine.rideThroughBand || 0}`}
                    warn={(turbine.rideThroughBand || 0) !== 0} />
                </div>
              </SubsystemPanel>
            );
          case 'nacelle':
            return (
              <SubsystemPanel title={u('WNAC Nacelle', 'WNAC 機艙')} color="yellow">
                <DataRow label={u('Nacelle Temp', '機艙溫度')} value={`${fmt(turbine.nacelleTemp)}°C`} />
                <DataRow label={u('Cabinet Temp', '控制櫃溫度')} value={`${fmt(turbine.nacelleCabTemp)}°C`} />
                <DataRow label={u('Vibration X', 'X方向振動')} value={`${fmt(turbine.vibrationX, 2)} mm/s`}
                  warn={(turbine.vibrationX || 0) > 4} alert={(turbine.vibrationX || 0) > 8} />
                <DataRow label={u('Vibration Y', 'Y方向振動')} value={`${fmt(turbine.vibrationY, 2)} mm/s`}
                  warn={(turbine.vibrationY || 0) > 4} alert={(turbine.vibrationY || 0) > 8} />
                <div className="border-t border-yellow-500/20 my-2 pt-2">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xs text-yellow-300/60">{u('Spectral Bands', '頻帶分析')}</span>
                    {turbine.vibAlarmOverall != null && (
                      <span className={`px-1.5 py-0.5 text-xs rounded font-medium ${
                        turbine.vibAlarmOverall === 2 ? 'bg-red-500/30 text-red-300' :
                        turbine.vibAlarmOverall === 1 ? 'bg-yellow-500/30 text-yellow-300' :
                        'bg-green-500/20 text-green-400'
                      }`}>{turbine.vibAlarmOverall === 2 ? 'ALARM' : turbine.vibAlarmOverall === 1 ? 'WARN' : 'OK'}</span>
                    )}
                  </div>
                  <DataRow label={u('1P Band X/Y', '1P頻帶X/Y')} value={`${fmt(turbine.vibBand1pX, 3)} / ${fmt(turbine.vibBand1pY, 3)}`}
                    warn={turbine.vibAlarm1p === 1} alert={turbine.vibAlarm1p === 2} />
                  <DataRow label={u('3P Band X/Y', '3P頻帶X/Y')} value={`${fmt(turbine.vibBand3pX, 3)} / ${fmt(turbine.vibBand3pY, 3)}`}
                    warn={turbine.vibAlarm3p === 1} alert={turbine.vibAlarm3p === 2} />
                  <DataRow label={u('Gear Mesh X/Y', '齒輪嚙合X/Y')} value={`${fmt(turbine.vibBandGearX, 3)} / ${fmt(turbine.vibBandGearY, 3)}`}
                    warn={turbine.vibAlarmGear === 1} alert={turbine.vibAlarmGear === 2} />
                  <DataRow label={u('HF Band X/Y', '高頻帶X/Y')} value={`${fmt(turbine.vibBandHfX, 3)} / ${fmt(turbine.vibBandHfY, 3)}`}
                    warn={turbine.vibAlarmHf === 1} alert={turbine.vibAlarmHf === 2} />
                  <DataRow label={u('Broadband X/Y', '寬頻帶X/Y')} value={`${fmt(turbine.vibBandBbX, 3)} / ${fmt(turbine.vibBandBbY, 3)}`}
                    warn={turbine.vibAlarmBb === 1} alert={turbine.vibAlarmBb === 2} />
                  <DataRow label={u('Crest Factor', '峰值因子')} value={fmt(turbine.vibCrestFactor, 2)}
                    warn={(turbine.vibCrestFactor || 3) > 5} alert={(turbine.vibCrestFactor || 3) > 8} />
                  <DataRow label={u('Kurtosis', '峰度')} value={fmt(turbine.vibKurtosis, 2)}
                    warn={(turbine.vibKurtosis || 3) > 5} alert={(turbine.vibKurtosis || 3) > 10} />
                  {turbine.vibThresh1pWarn != null && (
                    <DataRow label={u('1P Threshold W/A', '1P門檻 警告/警報')}
                      value={`${fmt(turbine.vibThresh1pWarn, 3)} / ${fmt(turbine.vibThresh1pAlrm, 3)} mm/s`} />
                  )}
                </div>
              </SubsystemPanel>
            );
          case 'yaw':
            return (
              <SubsystemPanel title={u('WYAW Yaw System', 'WYAW 轉向系統')} color="blue">
                <DataRow label={u('Yaw Error (5s)', '風向誤差(5s)')} value={`${fmt(turbine.yawError)}°`}
                  warn={Math.abs(turbine.yawError || 0) > 10} />
                <DataRow label={u('Brake Pressure', '剎車液壓')} value={`${fmt(turbine.yawBrakePressure, 0)} bar`} />
                <DataRow label={u('Cable Windup', '纜線圈數')} value={`${fmt(turbine.cableWindup, 2)} turns`}
                  warn={Math.abs(turbine.cableWindup || 0) > 3} />
              </SubsystemPanel>
            );
          case 'grid':
            return (
              <SubsystemPanel title={u('WGDC/WMET Grid/Met', 'WGDC/WMET 電網/氣象')} color="orange">
                <DataRow label={u('Transformer Temp', '變壓器溫度')} value={`${fmt(turbine.transformerTemp)}°C`}
                  warn={(turbine.transformerTemp || 0) > 80} />
                <DataRow label={u('Wind Speed', '風速')} value={`${fmt(turbine.windSpeed)} m/s`} />
                <DataRow label={u('Wind Dir', '風向')} value={`${fmt(turbine.windDirection, 0)}°`} />
                <DataRow label={u('Outside Temp', '室外溫度')} value={`${fmt(turbine.outsideTemp)}°C`} />
              </SubsystemPanel>
            );
          case 'fatigue':
            return (
              <SubsystemPanel title={u('WLOD Structural Load & Fatigue', 'WLOD 結構載荷與疲勞')} color="red">
                <div className="text-xs text-red-300/60 mb-2">{u('Tower Moments', '塔架彎矩')}</div>
                <DataRow label={u('Fore-Aft FA', '前後彎矩 FA')} value={`${fmt(turbine.towerFaMoment, 1)} kNm`} />
                <DataRow label={u('Side-Side SS', '側面彎矩 SS')} value={`${fmt(turbine.towerSsMoment, 1)} kNm`} />
                
                <div className="border-t border-red-500/20 my-2 pt-2">
                  <div className="text-xs text-red-300/60 mb-2">{u('Blade Moments', '葉片彎矩')}</div>
                  <DataRow label={u('Flapwise My', '揮舞彎矩 Flap')} value={`${fmt(turbine.bladeFlapMoment, 1)} kNm`} />
                  <DataRow label={u('Edgewise Mx', '擺振彎矩 Edge')} value={`${fmt(turbine.bladeEdgeMoment, 1)} kNm`} />
                </div>

                <div className="border-t border-red-500/20 my-2 pt-2">
                  <div className="text-xs text-red-300/60 mb-2">{u('DEL Indicators (kNm)', 'DEL 等效疲勞指標')}</div>
                  <DataRow label={u('Tower FA', '塔架前後')} value={fmt(turbine.delTowerFa, 1)}
                    warn={(turbine.delTowerFa || 0) > 4000} alert={(turbine.delTowerFa || 0) > 6000} />
                  <DataRow label={u('Blade Flap', '葉片揮舞')} value={fmt(turbine.delBladeFlap, 1)}
                    warn={(turbine.delBladeFlap || 0) > 2000} alert={(turbine.delBladeFlap || 0) > 3000} />
                </div>

                <div className="border-t border-red-500/20 my-2 pt-2">
                  <div className="text-xs text-red-300/60 mb-2">{u('Cumulative Damage', '累積損傷')}</div>
                  <DataRow label={u('Tower FA', '塔架前後')} value={`${((turbine.damageTowerFa || 0) * 100).toFixed(6)}%`}
                    warn={(turbine.damageTowerFa || 0) > 0.5} alert={(turbine.damageTowerFa || 0) > 0.8} />
                  <DataRow label={u('Blade Flap', '葉片揮舞')} value={`${((turbine.damageBladeFlap || 0) * 100).toFixed(6)}%`}
                    warn={(turbine.damageBladeFlap || 0) > 0.5} alert={(turbine.damageBladeFlap || 0) > 0.8} />
                </div>

                <div className="border-t border-red-500/20 my-2 pt-2">
                  <DataRow label={u('Production Hours', '發電時數')} value={`${fmt(turbine.productionHours, 1)} h`} />
                </div>
              </SubsystemPanel>
            );
          default:
            return null;
        }
      })();

      return (
        <>
          {metricsBar}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
            {/* Left: Subsystem data (compact) */}
            <div className="lg:col-span-4">
              {subsystemContent}
            </div>
            {/* Right: Trend chart (always visible) */}
            <div className="lg:col-span-8">
              <TrendChartPanel turbineId={turbineApiId} lang={lang} />
            </div>
          </div>
        </>
      );
    };

  return (
    <div>
        <button onClick={onBack} className="flex items-center space-x-2 text-cyan-400 hover:text-cyan-300 mb-6 transition-colors">
            <BackIcon />
            <span>{u('Back to Farm Overview', '返回風場總覽')}</span>
        </button>

      {/* Header */}
      <div className="bg-gray-800/50 rounded-lg p-6 mb-4">
        <div className="flex flex-col sm:flex-row justify-between sm:items-center">
            <div>
              <h2 className="text-4xl font-bold font-orbitron text-white">{turbine.name}</h2>
              <div className="flex items-center space-x-3 mt-2 text-sm">
                <span className="text-gray-400">TurState: <span className="text-white font-semibold">{turbine.turState} - {turStateText}</span></span>
                {turbine.outsideTemp != null && (
                  <span className="text-gray-400">{u('Outdoor', '室外')}: <span className="text-white">{fmt(turbine.outsideTemp)}°C</span></span>
                )}
                {turbine.windDirection != null && (
                  <span className="text-gray-400">{u('Wind Dir', '風向')}: <span className="text-white">{fmt(turbine.windDirection, 0)}°</span></span>
                )}
              </div>
            </div>
            <div className="mt-2 sm:mt-0"><StatusIndicator status={turbine.status} large /></div>
        </div>
      </div>

      {/* Fault alerts */}
      {hasFaults && (
        <div className="mb-4 space-y-2">
          {turbine.activeFaults!.map((f, i) => (
            <FaultBadge key={i} fault={f} lang={lang} />
          ))}
        </div>
      )}

      {/* Operator Control Panel */}
      <OperatorControlPanel turbineId={turbineApiId} lang={lang} />

      {/* Tab Navigation */}
      <div className="flex overflow-x-auto gap-1 mb-6 bg-gray-800/50 rounded-lg p-1 border border-gray-700">
        {DETAIL_TABS.map(tab => {
          const activeStyles: Record<string, string> = {
            cyan:   'bg-cyan-600/30 text-cyan-300 border-cyan-500/50',
            green:  'bg-green-600/30 text-green-300 border-green-500/50',
            purple: 'bg-purple-600/30 text-purple-300 border-purple-500/50',
            yellow: 'bg-yellow-600/30 text-yellow-300 border-yellow-500/50',
            blue:   'bg-blue-600/30 text-blue-300 border-blue-500/50',
            orange: 'bg-orange-600/30 text-orange-300 border-orange-500/50',
            red:    'bg-red-600/30 text-red-300 border-red-500/50',
          };
          return (
            <button key={tab.id} onClick={() => setActiveTab(tab.id)}
              className={`flex-shrink-0 px-4 py-2 text-sm font-medium rounded-md transition-colors border ${
                activeTab === tab.id
                  ? activeStyles[tab.color] || activeStyles.cyan
                  : 'text-gray-400 hover:text-white hover:bg-gray-700/50 border-transparent'
              }`}>
              {lang === 'zh' ? tab.label_zh : tab.label_en}
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      {renderTabContent()}

      {/* AI Fault Diagnosis - always visible when in fault */}
      {turbine.status === TurbineStatus.FAULT && (
         <div className="mt-6 bg-red-900/30 border border-red-500/50 rounded-lg p-6">
            <div className="flex flex-col md:flex-row md:items-start justify-between">
                <div>
                    <h3 className="text-xl font-bold text-red-300">{u('AI Fault Diagnosis', 'AI 故障診斷')}</h3>
                    <p className="text-red-400 mt-1">{u('Experimental AI analysis to help diagnose the issue.', '實驗性 AI 分析協助故障診斷')}</p>
                </div>
                <div className="flex space-x-2 mt-4 md:mt-0">
                    <button
                        onClick={handleAnalyzeFault}
                        disabled={isAnalyzing}
                        className="flex items-center justify-center space-x-2 bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded-lg transition-all disabled:bg-gray-800 disabled:cursor-not-allowed"
                    >
                        <BrainIcon />
                        <span>{isAnalyzing ? u('Analyzing...', '分析中...') : u('Re-Analyze', '重新分析')}</span>
                    </button>
                    {activeWorkOrder ? (
                        <div className="text-center py-2 px-4 rounded-lg bg-yellow-500/20 text-yellow-300 border border-yellow-500/50">
                            <p className="font-bold">{u('WO', '工單')} #{activeWorkOrder.id.slice(-4)} {u('In Progress', '處理中')}</p>
                        </div>
                    ) : (
                        <button
                            onClick={() => onDispatch(turbine, analysisResult || "Awaiting analysis...")}
                            disabled={isAnalyzing || !analysisResult}
                            className="flex items-center justify-center space-x-2 bg-yellow-500 hover:bg-yellow-600 text-white font-bold py-2 px-4 rounded-lg transition-all disabled:bg-yellow-800 disabled:cursor-not-allowed w-full md:w-auto"
                        >
                            <WrenchScrewdriverIcon />
                            <span>{u('Dispatch Technician', '派遣技術員')}</span>
                        </button>
                    )}
                </div>
            </div>
            {isAnalyzing && <div className="mt-4 text-center text-red-300 animate-pulse">{u('Contacting maintenance AI...', '正在聯繫維護 AI...')}</div>}
            {analysisError && <div className="mt-4 text-center font-bold text-red-200 bg-red-500/30 p-3 rounded">{analysisError}</div>}
            {analysisResult && (
                <div className="mt-4 bg-gray-900/50 p-4 rounded-md text-gray-300 font-mono text-sm leading-relaxed">
                    {formattedAnalysis}
                </div>
            )}
        </div>
      )}
    </div>
  );
};

export default TurbineDetail;

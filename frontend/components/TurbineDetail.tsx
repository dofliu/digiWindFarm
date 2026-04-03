import React, { useState, useCallback, useEffect } from 'react';
import { type TurbineData, TurbineStatus, type WorkOrder, WorkOrderStatus, type FaultInfo } from '../types';
import StatusIndicator from './StatusIndicator';
import Gauge from './Gauge';
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
  7: { en: 'Shutting Down', zh: '停機中' },
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

const TurbineDetail: React.FC<TurbineDetailProps> = ({ turbine, onBack, onDispatch, activeWorkOrder, lang = 'zh' }) => {
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [analysisResult, setAnalysisResult] = useState<string | null>(null);
    const [analysisError, setAnalysisError] = useState<string | null>(null);

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

  return (
    <div>
        <button onClick={onBack} className="flex items-center space-x-2 text-cyan-400 hover:text-cyan-300 mb-6 transition-colors">
            <BackIcon />
            <span>{lang === 'zh' ? '返回風場總覽' : 'Back to Farm Overview'}</span>
        </button>

      {/* Header */}
      <div className="bg-gray-800/50 rounded-lg p-6 mb-6">
        <div className="flex flex-col sm:flex-row justify-between sm:items-center">
            <div>
              <h2 className="text-4xl font-bold font-orbitron text-white">{turbine.name}</h2>
              <div className="flex items-center space-x-3 mt-2 text-sm">
                <span className="text-gray-400">TurState: <span className="text-white font-semibold">{turbine.turState} - {turStateText}</span></span>
                {turbine.outsideTemp != null && (
                  <span className="text-gray-400">{lang === 'zh' ? '室外' : 'Outdoor'}: <span className="text-white">{fmt(turbine.outsideTemp)}°C</span></span>
                )}
                {turbine.windDirection != null && (
                  <span className="text-gray-400">{lang === 'zh' ? '風向' : 'Wind Dir'}: <span className="text-white">{fmt(turbine.windDirection, 0)}°</span></span>
                )}
              </div>
            </div>
            <div className="mt-2 sm:mt-0"><StatusIndicator status={turbine.status} large /></div>
        </div>
      </div>

      {/* Fault alerts */}
      {hasFaults && (
        <div className="mb-6 space-y-2">
          {turbine.activeFaults!.map((f, i) => (
            <FaultBadge key={i} fault={f} lang={lang} />
          ))}
        </div>
      )}

      {/* Gauges row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        <Gauge value={turbine.powerOutput} maxValue={5} label={lang === 'zh' ? '發電功率' : 'Power Output'} unit="MW" />
        <Gauge value={turbine.rotorSpeed} maxValue={15} label={lang === 'zh' ? '葉輪轉速' : 'Rotor Speed'} unit="RPM" />
        <Gauge value={turbine.windSpeed} maxValue={25} label={lang === 'zh' ? '風速' : 'Wind Speed'} unit="m/s" />
        <div className="bg-gray-800/50 p-4 rounded-lg flex flex-col justify-center">
           <h3 className="text-gray-400 text-sm mb-2 text-center">{lang === 'zh' ? '功率趨勢' : 'Power Trend'}</h3>
           <MiniTrendChart data={turbine.history} />
        </div>
      </div>

      {/* SCADA subsystem panels */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        {/* Generator */}
        <SubsystemPanel title={lang === 'zh' ? 'WGEN 發電機' : 'WGEN Generator'}>
          <DataRow label={lang === 'zh' ? '功率' : 'Power'} value={`${fmt(turbine.genPower)} kW`} />
          <DataRow label={lang === 'zh' ? '轉速' : 'Speed'} value={`${fmt(turbine.genSpeed, 0)} RPM`} />
          <DataRow label={lang === 'zh' ? '電壓' : 'Voltage'} value={`${fmt(turbine.voltage, 0)} V`} />
          <DataRow label={lang === 'zh' ? '電流' : 'Current'} value={`${fmt(turbine.current, 0)} A`} />
          <DataRow label={lang === 'zh' ? '定子溫度' : 'Stator Temp'} value={`${fmt(turbine.genStatorTemp1)}°C`}
            warn={(turbine.genStatorTemp1 || 0) > 100} alert={(turbine.genStatorTemp1 || 0) > 130} />
          <DataRow label={lang === 'zh' ? '氣隙溫度' : 'Air Gap Temp'} value={`${fmt(turbine.genAirTemp1)}°C`}
            warn={(turbine.genAirTemp1 || 0) > 80} />
          <DataRow label={lang === 'zh' ? '軸承溫度' : 'Bearing Temp'} value={`${fmt(turbine.genBearingTemp1)}°C`}
            warn={(turbine.genBearingTemp1 || 0) > 70} alert={(turbine.genBearingTemp1 || 0) > 90} />
        </SubsystemPanel>

        {/* Rotor / Pitch */}
        <SubsystemPanel title={lang === 'zh' ? 'WROT 葉輪/旋角' : 'WROT Rotor/Pitch'} color="green">
          <DataRow label={lang === 'zh' ? '葉輪轉速' : 'Rotor RPM'} value={`${fmt(turbine.rotorSpeed, 2)} RPM`} />
          <DataRow label={lang === 'zh' ? '葉片1角度' : 'Blade 1'} value={`${fmt(turbine.bladeAngle1)}°`} />
          <DataRow label={lang === 'zh' ? '葉片2角度' : 'Blade 2'} value={`${fmt(turbine.bladeAngle2)}°`} />
          <DataRow label={lang === 'zh' ? '葉片3角度' : 'Blade 3'} value={`${fmt(turbine.bladeAngle3)}°`} />
          <DataRow label={lang === 'zh' ? '轉子溫度' : 'Rotor Temp'} value={`${fmt(turbine.rotorTemp)}°C`} />
          <DataRow label={lang === 'zh' ? '輪毂櫃溫' : 'Hub Cab Temp'} value={`${fmt(turbine.hubCabinetTemp)}°C`} />
          <DataRow label={lang === 'zh' ? '鎖固/剎車' : 'Locked/Brake'}
            value={`${turbine.rotorLocked ? 'Locked' : '-'} / ${turbine.brakeActive ? 'Active' : '-'}`} />
        </SubsystemPanel>

        {/* Converter */}
        <SubsystemPanel title={lang === 'zh' ? 'WCNV 變頻器' : 'WCNV Converter'} color="purple">
          <DataRow label={lang === 'zh' ? '發電機功率' : 'Gen Power'} value={`${fmt(turbine.cnvGenPower)} kW`} />
          <DataRow label={lang === 'zh' ? '電網功率' : 'Grid Power'} value={`${fmt(turbine.cnvGridPower)} kW`} />
          <DataRow label={lang === 'zh' ? '頻率' : 'Frequency'} value={`${fmt(turbine.cnvGenFreq, 2)} Hz`} />
          <DataRow label={lang === 'zh' ? 'DC電壓' : 'DC Voltage'} value={`${fmt(turbine.cnvDcVoltage, 0)} V`} />
          <DataRow label={lang === 'zh' ? '控制櫃溫度' : 'Cabinet Temp'} value={`${fmt(turbine.cnvCabinetTemp)}°C`}
            warn={(turbine.cnvCabinetTemp || 0) > 45} />
          <DataRow label={lang === 'zh' ? 'IGCT水溫' : 'IGCT Water Temp'} value={`${fmt(turbine.igctWaterTemp)}°C`}
            warn={(turbine.igctWaterTemp || 0) > 40} />
          <DataRow label={lang === 'zh' ? 'IGCT水壓' : 'IGCT Pressure'} value={`${fmt(turbine.igctWaterPres1)} / ${fmt(turbine.igctWaterPres2)} bar`} />
        </SubsystemPanel>

        {/* Nacelle */}
        <SubsystemPanel title={lang === 'zh' ? 'WNAC 機艙' : 'WNAC Nacelle'} color="yellow">
          <DataRow label={lang === 'zh' ? '機艙溫度' : 'Nacelle Temp'} value={`${fmt(turbine.nacelleTemp)}°C`} />
          <DataRow label={lang === 'zh' ? '控制櫃溫度' : 'Cabinet Temp'} value={`${fmt(turbine.nacelleCabTemp)}°C`} />
          <DataRow label={lang === 'zh' ? 'X方向振動' : 'Vibration X'} value={`${fmt(turbine.vibrationX, 2)} mm/s`}
            warn={(turbine.vibrationX || 0) > 4} alert={(turbine.vibrationX || 0) > 8} />
          <DataRow label={lang === 'zh' ? 'Y方向振動' : 'Vibration Y'} value={`${fmt(turbine.vibrationY, 2)} mm/s`}
            warn={(turbine.vibrationY || 0) > 4} alert={(turbine.vibrationY || 0) > 8} />
        </SubsystemPanel>

        {/* Yaw */}
        <SubsystemPanel title={lang === 'zh' ? 'WYAW 轉向系統' : 'WYAW Yaw System'} color="blue">
          <DataRow label={lang === 'zh' ? '風向誤差(5s)' : 'Yaw Error (5s)'} value={`${fmt(turbine.yawError)}°`}
            warn={Math.abs(turbine.yawError || 0) > 10} />
          <DataRow label={lang === 'zh' ? '剎車液壓' : 'Brake Pressure'} value={`${fmt(turbine.yawBrakePressure, 0)} bar`} />
          <DataRow label={lang === 'zh' ? '纜線圈數' : 'Cable Windup'} value={`${fmt(turbine.cableWindup, 2)} turns`}
            warn={Math.abs(turbine.cableWindup || 0) > 3} />
        </SubsystemPanel>

        {/* Grid / Transformer + Met */}
        <SubsystemPanel title={lang === 'zh' ? 'WGDC/WMET 電網/氣象' : 'WGDC/WMET Grid/Met'} color="orange">
          <DataRow label={lang === 'zh' ? '變壓器溫度' : 'Transformer Temp'} value={`${fmt(turbine.transformerTemp)}°C`}
            warn={(turbine.transformerTemp || 0) > 80} />
          <DataRow label={lang === 'zh' ? '風速' : 'Wind Speed'} value={`${fmt(turbine.windSpeed)} m/s`} />
          <DataRow label={lang === 'zh' ? '風向' : 'Wind Dir'} value={`${fmt(turbine.windDirection, 0)}°`} />
          <DataRow label={lang === 'zh' ? '室外溫度' : 'Outside Temp'} value={`${fmt(turbine.outsideTemp)}°C`} />
        </SubsystemPanel>
      </div>

      {/* Trend Chart */}
      <div className="mb-6">
        <TrendChartPanel turbineId={`WT${String(turbine.id).padStart(3, '0')}`} lang={lang} />
      </div>

      {/* AI Fault Diagnosis */}
      {turbine.status === TurbineStatus.FAULT && (
         <div className="mt-6 bg-red-900/30 border border-red-500/50 rounded-lg p-6">
            <div className="flex flex-col md:flex-row md:items-start justify-between">
                <div>
                    <h3 className="text-xl font-bold text-red-300">{lang === 'zh' ? 'AI 故障診斷' : 'AI Fault Diagnosis'}</h3>
                    <p className="text-red-400 mt-1">{lang === 'zh' ? '實驗性 AI 分析協助故障診斷' : 'Experimental AI analysis to help diagnose the issue.'}</p>
                </div>
                <div className="flex space-x-2 mt-4 md:mt-0">
                    <button
                        onClick={handleAnalyzeFault}
                        disabled={isAnalyzing}
                        className="flex items-center justify-center space-x-2 bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded-lg transition-all disabled:bg-gray-800 disabled:cursor-not-allowed"
                    >
                        <BrainIcon />
                        <span>{isAnalyzing ? (lang === 'zh' ? '分析中...' : 'Analyzing...') : (lang === 'zh' ? '重新分析' : 'Re-Analyze')}</span>
                    </button>
                    {activeWorkOrder ? (
                        <div className="text-center py-2 px-4 rounded-lg bg-yellow-500/20 text-yellow-300 border border-yellow-500/50">
                            <p className="font-bold">{lang === 'zh' ? '工單' : 'WO'} #{activeWorkOrder.id.slice(-4)} {lang === 'zh' ? '處理中' : 'In Progress'}</p>
                        </div>
                    ) : (
                        <button
                            onClick={() => onDispatch(turbine, analysisResult || "Awaiting analysis...")}
                            disabled={isAnalyzing || !analysisResult}
                            className="flex items-center justify-center space-x-2 bg-yellow-500 hover:bg-yellow-600 text-white font-bold py-2 px-4 rounded-lg transition-all disabled:bg-yellow-800 disabled:cursor-not-allowed w-full md:w-auto"
                        >
                            <WrenchScrewdriverIcon />
                            <span>{lang === 'zh' ? '派遣技術員' : 'Dispatch Technician'}</span>
                        </button>
                    )}
                </div>
            </div>
            {isAnalyzing && <div className="mt-4 text-center text-red-300 animate-pulse">{lang === 'zh' ? '正在聯繫維護 AI...' : 'Contacting maintenance AI...'}</div>}
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

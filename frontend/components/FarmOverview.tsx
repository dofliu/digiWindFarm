import React from 'react';
import { type TurbineData, TurbineStatus, type AppSettings, DataSourceType } from '../types';
import StatusIndicator from './StatusIndicator';
import { WindTurbineIcon } from './icons';

interface FarmOverviewProps {
  turbines: TurbineData[];
  onSelectTurbine: (turbine: TurbineData) => void;
  settings: AppSettings;
  lang?: 'en' | 'zh';
}

const TUR_STATE_SHORT: Record<number, string> = {
  1: 'STOP', 2: 'STBY', 3: 'WAIT', 4: 'PREP',
  5: 'START', 6: 'PROD', 7: 'SHTDN', 8: 'RSTR', 9: 'NSTP',
};

const TurbineCard: React.FC<{ turbine: TurbineData; onSelect: (turbine: TurbineData) => void; lang: string }> = ({ turbine, onSelect, lang }) => {
  const getStatusColorClasses = (status: TurbineStatus) => {
    switch (status) {
      case TurbineStatus.OPERATING:
        return 'border-green-500/50 hover:border-green-500 bg-green-500/10';
      case TurbineStatus.IDLE:
        return 'border-yellow-500/50 hover:border-yellow-500 bg-yellow-500/10';
      case TurbineStatus.FAULT:
        return 'border-red-500/50 hover:border-red-500 bg-red-500/10 animate-pulse';
      case TurbineStatus.OFFLINE:
        return 'border-gray-600/50 hover:border-gray-500 bg-gray-600/10';
    }
  };

  const hasFaults = turbine.activeFaults && turbine.activeFaults.length > 0;

  return (
    <div
      className={`relative rounded-lg p-4 border transition-all duration-300 cursor-pointer group ${getStatusColorClasses(turbine.status)}`}
      onClick={() => onSelect(turbine)}
    >
      <div className="flex justify-between items-start">
        <div>
          <h3 className="font-bold text-lg text-white">{turbine.name}</h3>
          {turbine.turState && (
            <span className="text-xs text-gray-500 font-mono">{TUR_STATE_SHORT[turbine.turState] || turbine.turState}</span>
          )}
        </div>
        <StatusIndicator status={turbine.status} />
      </div>
      <div className="mt-3 flex items-end justify-between">
        <div>
          <p className="text-xs text-gray-400">{lang === 'zh' ? '發電功率' : 'Power'}</p>
          <p className="font-orbitron text-2xl font-bold text-white">{turbine.powerOutput.toFixed(2)} <span className="text-lg">MW</span></p>
        </div>
        <div className="text-right">
          <p className="text-xs text-gray-400">{lang === 'zh' ? '風速' : 'Wind'}</p>
          <p className="text-white">{turbine.windSpeed.toFixed(1)} m/s</p>
        </div>
      </div>
      {/* Extra SCADA info row */}
      <div className="mt-2 flex justify-between text-xs text-gray-500">
        <span>{lang === 'zh' ? '轉速' : 'RPM'}: {turbine.rotorSpeed.toFixed(1)}</span>
        <span>{lang === 'zh' ? '溫度' : 'Temp'}: {turbine.temperature.toFixed(0)}°C</span>
        <span>{lang === 'zh' ? '振動' : 'Vib'}: {turbine.vibration.toFixed(1)}</span>
      </div>
      {/* Fault indicator */}
      {hasFaults && (
        <div className="mt-2 text-xs">
          {turbine.activeFaults!.map((f, i) => (
            <div key={i} className={`px-2 py-0.5 rounded text-xs ${
              f.phase === 'critical' ? 'bg-red-500/30 text-red-300' :
              f.phase === 'advanced' ? 'bg-orange-500/20 text-orange-300' :
              'bg-yellow-500/20 text-yellow-300'
            }`}>
              {lang === 'zh' ? f.name_zh : f.name_en} ({(f.severity * 100).toFixed(0)}%)
            </div>
          ))}
        </div>
      )}
       <div className="absolute bottom-4 right-4 text-gray-600 group-hover:text-cyan-400 transition-colors">
          <WindTurbineIcon className="w-10 h-10 opacity-20 group-hover:opacity-40" />
       </div>
    </div>
  );
};


const FarmOverview: React.FC<FarmOverviewProps> = ({ turbines, onSelectTurbine, settings, lang = 'zh' }) => {
  return (
    <div>
      <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-6">
        <h2 className="text-3xl font-bold font-orbitron text-white">{lang === 'zh' ? '風場總覽' : 'Farm Overview'}</h2>
        {settings.dataSource === DataSourceType.MOCK && (
          <div className="mt-2 md:mt-0 text-xs text-yellow-300 bg-yellow-900/50 border border-yellow-700 px-3 py-1 rounded-md">
            {lang === 'zh' ? '注意: 使用前端模擬數據。請到設定頁面切換為「Physics Simulation」以使用後端模擬器。' : 'Using MOCK data. Switch to "Physics Simulation" in Settings for backend simulator.'}
          </div>
        )}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {turbines.map(turbine => (
          <TurbineCard key={turbine.id} turbine={turbine} onSelect={onSelectTurbine} lang={lang} />
        ))}
      </div>
    </div>
  );
};

export default FarmOverview;

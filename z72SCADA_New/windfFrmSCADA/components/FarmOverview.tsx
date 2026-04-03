import React from 'react';
import { type TurbineData, TurbineStatus, type AppSettings, DataSourceType } from '../types';
import StatusIndicator from './StatusIndicator';
import { WindTurbineIcon } from './icons';

interface FarmOverviewProps {
  turbines: TurbineData[];
  onSelectTurbine: (turbine: TurbineData) => void;
  settings: AppSettings;
}

const TurbineCard: React.FC<{ turbine: TurbineData; onSelect: (turbine: TurbineData) => void }> = ({ turbine, onSelect }) => {
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

  return (
    <div
      className={`relative rounded-lg p-4 border transition-all duration-300 cursor-pointer group ${getStatusColorClasses(turbine.status)}`}
      onClick={() => onSelect(turbine)}
    >
      <div className="flex justify-between items-start">
        <h3 className="font-bold text-lg text-white">{turbine.name}</h3>
        <StatusIndicator status={turbine.status} />
      </div>
      <div className="mt-4 flex items-end justify-between">
        <div>
          <p className="text-xs text-gray-400">Power Output</p>
          <p className="font-orbitron text-2xl font-bold text-white">{turbine.powerOutput.toFixed(2)} <span className="text-lg">MW</span></p>
        </div>
        <div className="text-right">
          <p className="text-xs text-gray-400">Wind Speed</p>
          <p className="text-white">{turbine.windSpeed.toFixed(1)} m/s</p>
        </div>
      </div>
       <div className="absolute bottom-4 right-4 text-gray-600 group-hover:text-cyan-400 transition-colors">
          <WindTurbineIcon className="w-10 h-10 opacity-20 group-hover:opacity-40" />
       </div>
    </div>
  );
};


const FarmOverview: React.FC<FarmOverviewProps> = ({ turbines, onSelectTurbine, settings }) => {
  return (
    <div>
      <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-6">
        <h2 className="text-3xl font-bold font-orbitron text-white">Farm Overview</h2>
        {settings.dataSource !== DataSourceType.MOCK && (
          <div className="mt-2 md:mt-0 text-xs text-yellow-300 bg-yellow-900/50 border border-yellow-700 px-3 py-1 rounded-md">
            Note: Data source is set to "{settings.dataSource}". Displaying MOCK DATA as a backend connection is not yet implemented.
          </div>
        )}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {turbines.map(turbine => (
          <TurbineCard key={turbine.id} turbine={turbine} onSelect={onSelectTurbine} />
        ))}
      </div>
    </div>
  );
};

export default FarmOverview;

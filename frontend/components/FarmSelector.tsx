import React, { useState, useEffect, useRef } from 'react';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8100';

interface Farm {
  farm_id: string;
  name: string;
  turbine_count: number;
  is_active: boolean;
  location: string;
  description: string;
  created_at: string;
  turbine_spec: Record<string, unknown>;
}

interface Props {
  lang: string;
}

const FarmSelector: React.FC<Props> = ({ lang }) => {
  const [farms, setFarms] = useState<Farm[]>([]);
  const [activeFarmId, setActiveFarmId] = useState<string | null>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [switching, setSwitching] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const ui = (en: string, zh: string) => lang === 'zh' ? zh : en;

  useEffect(() => {
    fetchFarms();
  }, []);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchFarms = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/farms`);
      if (!res.ok) return;
      const data = await res.json();
      setFarms(data.farms || []);
      setActiveFarmId(data.active_farm_id);
    } catch {
      // Farm API not available yet — silently ignore
    }
  };

  const switchFarm = async (farmId: string) => {
    if (farmId === activeFarmId || switching) return;
    setSwitching(true);
    try {
      const res = await fetch(`${API_BASE}/api/farms/${farmId}/activate`, { method: 'POST' });
      if (res.ok) {
        setActiveFarmId(farmId);
        setIsOpen(false);
        window.location.reload();
      }
    } catch {
      // ignore
    } finally {
      setSwitching(false);
    }
  };

  const activeFarm = farms.find(f => f.farm_id === activeFarmId);

  if (farms.length === 0) return null;

  const ratedPower = activeFarm?.turbine_spec?.rated_power_kw as number | undefined;
  const label = activeFarm
    ? `${activeFarm.name}${ratedPower ? ` (${(ratedPower / 1000).toFixed(1)}MW)` : ''}`
    : ui('Select Farm', '選擇風場');

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-1.5 px-2.5 py-1.5 rounded-md text-xs font-medium border border-gray-600 text-gray-300 hover:text-white hover:border-gray-400 transition-colors bg-gray-800/60"
        title={ui('Switch Wind Farm', '切換風場')}
      >
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
          <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 0h.008v.008h-.008v-.008zm0 3h.008v.008h-.008v-.008zm0 3h.008v.008h-.008v-.008z" />
        </svg>
        <span className="hidden lg:inline max-w-[140px] truncate">{label}</span>
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-3 h-3">
          <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute top-full right-0 mt-1 w-72 bg-gray-800 border border-gray-600 rounded-lg shadow-xl z-[100] overflow-hidden">
          <div className="px-3 py-2 border-b border-gray-700 text-xs text-gray-400 font-medium">
            {ui('Wind Farms', '風場專案')}
          </div>
          <div className="max-h-64 overflow-y-auto">
            {farms.map(farm => {
              const power = farm.turbine_spec?.rated_power_kw as number | undefined;
              return (
                <button
                  key={farm.farm_id}
                  onClick={() => switchFarm(farm.farm_id)}
                  disabled={switching}
                  className={`w-full text-left px-3 py-2.5 flex items-center justify-between hover:bg-gray-700/50 transition-colors ${
                    farm.farm_id === activeFarmId ? 'bg-cyan-500/10 border-l-2 border-cyan-400' : 'border-l-2 border-transparent'
                  }`}
                >
                  <div>
                    <div className="text-sm text-white font-medium">{farm.name}</div>
                    <div className="text-xs text-gray-400">
                      {farm.turbine_count} {ui('turbines', '台風機')}
                      {power ? ` | ${(power / 1000).toFixed(1)} MW` : ''}
                      {farm.location ? ` | ${farm.location}` : ''}
                    </div>
                  </div>
                  {farm.farm_id === activeFarmId && (
                    <span className="text-cyan-400 text-xs font-medium">{ui('Active', '使用中')}</span>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default FarmSelector;

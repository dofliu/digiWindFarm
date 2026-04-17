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

interface Preset {
  key: string;
  label: string;
}

const PRESETS: Preset[] = [
  { key: 'z72_2mw', label: 'Z72 2MW (Direct Drive)' },
  { key: 'vestas_v90_3mw', label: 'Vestas V90 3MW' },
  { key: 'sg_8mw', label: 'SG 8MW (Offshore)' },
  { key: 'goldwind_2.5mw', label: 'Goldwind 2.5MW' },
];

interface Props {
  lang: string;
}

const FarmSelector: React.FC<Props> = ({ lang }) => {
  const [farms, setFarms] = useState<Farm[]>([]);
  const [activeFarmId, setActiveFarmId] = useState<string | null>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [switching, setSwitching] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const ui = (en: string, zh: string) => lang === 'zh' ? zh : en;

  useEffect(() => { fetchFarms(); }, []);

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
    } catch { /* Farm API not available yet */ }
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
    } catch { /* ignore */ }
    finally { setSwitching(false); }
  };

  const activeFarm = farms.find(f => f.farm_id === activeFarmId);
  const ratedPower = activeFarm?.turbine_spec?.rated_power_kw as number | undefined;
  const label = activeFarm
    ? `${activeFarm.name}${ratedPower ? ` (${(ratedPower / 1000).toFixed(1)}MW)` : ''}`
    : ui('Select Farm', '選擇風場');

  return (
    <>
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
          <div className="absolute top-full right-0 mt-1 w-80 bg-gray-800 border border-gray-600 rounded-lg shadow-xl z-[100] overflow-hidden">
            <div className="px-3 py-2 border-b border-gray-700 flex items-center justify-between">
              <span className="text-xs text-gray-400 font-medium">{ui('Wind Farms', '風場專案')}</span>
              <button
                onClick={() => { setIsOpen(false); setShowCreate(true); }}
                className="flex items-center space-x-1 text-xs text-cyan-400 hover:text-cyan-300 transition-colors"
              >
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-3.5 h-3.5">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                </svg>
                <span>{ui('New Farm', '新增風場')}</span>
              </button>
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

      {showCreate && (
        <CreateFarmModal
          lang={lang}
          onClose={() => setShowCreate(false)}
          onCreated={(farmId) => {
            setShowCreate(false);
            fetchFarms();
            switchFarm(farmId);
          }}
        />
      )}
    </>
  );
};


// ── Create Farm Modal ──────────────────────────────────────────────────

interface CreateModalProps {
  lang: string;
  onClose: () => void;
  onCreated: (farmId: string) => void;
}

const CreateFarmModal: React.FC<CreateModalProps> = ({ lang, onClose, onCreated }) => {
  const ui = (en: string, zh: string) => lang === 'zh' ? zh : en;
  const [name, setName] = useState('');
  const [preset, setPreset] = useState('z72_2mw');
  const [turbineCount, setTurbineCount] = useState(14);
  const [location, setLocation] = useState('');
  const [description, setDescription] = useState('');
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState('');

  const handleCreate = async () => {
    if (!name.trim()) {
      setError(ui('Farm name is required', '請輸入風場名稱'));
      return;
    }
    setCreating(true);
    setError('');
    try {
      const res = await fetch(`${API_BASE}/api/farms`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: name.trim(),
          preset,
          turbine_count: turbineCount,
          location: location.trim(),
          description: description.trim(),
        }),
      });
      if (!res.ok) {
        const data = await res.json();
        setError(data.detail || 'Failed to create farm');
        return;
      }
      const data = await res.json();
      onCreated(data.farm.farm_id);
    } catch {
      setError(ui('Network error', '網路錯誤'));
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[200] overflow-y-auto" onClick={onClose}>
      <div className="min-h-full flex items-center justify-center p-4">
        <div className="bg-gray-800 border border-gray-600 rounded-xl shadow-2xl w-full max-w-md" onClick={e => e.stopPropagation()}>
          <div className="px-5 py-4 border-b border-gray-700 flex items-center justify-between">
            <h2 className="text-lg font-bold text-white">{ui('Create Wind Farm', '建立新風場')}</h2>
            <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div className="px-5 py-4 space-y-4">
          {/* Farm Name */}
          <div>
            <label className="block text-sm text-gray-300 mb-1">{ui('Farm Name', '風場名稱')} *</label>
            <input
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder={ui('e.g. Changhua Offshore 8MW', '例：彰化離岸 8MW 風場')}
              className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500"
              autoFocus
            />
          </div>

          {/* Turbine Preset */}
          <div>
            <label className="block text-sm text-gray-300 mb-1">{ui('Turbine Model', '風機機型')}</label>
            <div className="grid grid-cols-2 gap-2">
              {PRESETS.map(p => (
                <button
                  key={p.key}
                  onClick={() => setPreset(p.key)}
                  className={`px-3 py-2 rounded-md text-xs font-medium transition-colors border ${
                    preset === p.key
                      ? 'bg-cyan-500/20 border-cyan-500 text-cyan-300'
                      : 'bg-gray-700 border-gray-600 text-gray-300 hover:border-gray-400'
                  }`}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>

          {/* Turbine Count */}
          <div>
            <label className="block text-sm text-gray-300 mb-1">{ui('Number of Turbines', '風機數量')}</label>
            <input
              type="number"
              value={turbineCount}
              onChange={e => setTurbineCount(Math.max(1, Math.min(50, parseInt(e.target.value) || 1)))}
              min={1}
              max={50}
              className="w-24 bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500"
            />
          </div>

          {/* Location */}
          <div>
            <label className="block text-sm text-gray-300 mb-1">{ui('Location', '地點')} <span className="text-gray-500">({ui('optional', '選填')})</span></label>
            <input
              type="text"
              value={location}
              onChange={e => setLocation(e.target.value)}
              placeholder={ui('e.g. Taiwan Strait', '例：台灣海峽')}
              className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500"
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm text-gray-300 mb-1">{ui('Description', '說明')} <span className="text-gray-500">({ui('optional', '選填')})</span></label>
            <textarea
              value={description}
              onChange={e => setDescription(e.target.value)}
              rows={2}
              placeholder={ui('Notes about this farm project...', '關於此風場專案的備註...')}
              className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500 resize-none"
            />
          </div>

          {error && (
            <div className="text-red-400 text-sm bg-red-500/10 border border-red-500/30 rounded-md px-3 py-2">
              {error}
            </div>
          )}
        </div>

          <div className="px-5 py-3 border-t border-gray-700 flex justify-end space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm text-gray-300 hover:text-white transition-colors"
            >
              {ui('Cancel', '取消')}
            </button>
            <button
              onClick={handleCreate}
              disabled={creating || !name.trim()}
              className="px-4 py-2 text-sm font-medium bg-cyan-600 hover:bg-cyan-500 text-white rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {creating ? ui('Creating...', '建立中...') : ui('Create & Activate', '建立並啟用')}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FarmSelector;

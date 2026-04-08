import React, { useEffect, useMemo, useState } from 'react';
import type { TurbineData } from '../types';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8100';

const EVENT_COLORS: Record<string, string> = {
  grid: '#f59e0b',
  fault: '#ef4444',
  fault_lifecycle: '#fb923c',
  operator: '#22c55e',
  wind: '#38bdf8',
  state: '#a78bfa',
};

const SEVERITY_COLORS: Record<string, string> = {
  critical: 'bg-red-500/20 text-red-300 border-red-500/50',
  warning: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/50',
  info: 'bg-gray-500/20 text-gray-300 border-gray-500/50',
};

interface ComparisonEvent {
  id: number;
  timestamp: string;
  end_timestamp?: string | null;
  turbine_id?: string | null;
  event_type: string;
  source: string;
  title: string;
  detail?: string | null;
  severity?: string;
  _turbine_id?: string;
}

interface EventComparisonViewProps {
  turbines: TurbineData[];
  lang?: 'en' | 'zh';
}

const toDateTimeLocal = (value: Date) => {
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${value.getFullYear()}-${pad(value.getMonth() + 1)}-${pad(value.getDate())}T${pad(value.getHours())}:${pad(value.getMinutes())}`;
};

const EventComparisonView: React.FC<EventComparisonViewProps> = ({ turbines, lang = 'zh' }) => {
  const u = (en: string, zh: string) => lang === 'zh' ? zh : en;

  const allTurbineIds = useMemo(
    () => turbines.map(t => `WT${String(t.id).padStart(3, '0')}`),
    [turbines],
  );

  const [selectedIds, setSelectedIds] = useState<string[]>(() => allTurbineIds.slice(0, 4));
  const [rangeStart, setRangeStart] = useState(() => toDateTimeLocal(new Date(Date.now() - 2 * 60 * 60 * 1000)));
  const [rangeEnd, setRangeEnd] = useState(() => toDateTimeLocal(new Date()));
  const [eventTypeFilter, setEventTypeFilter] = useState('');
  const [loading, setLoading] = useState(false);
  const [perTurbine, setPerTurbine] = useState<Record<string, ComparisonEvent[]>>({});
  const [timeline, setTimeline] = useState<ComparisonEvent[]>([]);
  const [summary, setSummary] = useState<Record<string, { total: number; by_type: Record<string, number> }>>({});
  const [farmEvents, setFarmEvents] = useState<ComparisonEvent[]>([]);

  const fetchComparison = async () => {
    if (selectedIds.length === 0) return;
    setLoading(true);
    try {
      const params = new URLSearchParams({
        turbine_ids: selectedIds.join(','),
        limit: '500',
      });
      if (rangeStart) params.set('start', new Date(rangeStart).toISOString());
      if (rangeEnd) params.set('end', new Date(rangeEnd).toISOString());
      if (eventTypeFilter) params.set('event_type', eventTypeFilter);

      const res = await fetch(`${API_BASE}/api/maintenance/events/compare?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setPerTurbine(data.per_turbine || {});
        setTimeline(data.timeline || []);
        setSummary(data.summary || {});
        setFarmEvents(data.farm_events || []);
      }
    } catch (e) {
      console.warn('[EventComparison] fetch failed:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchComparison();
  }, [selectedIds, rangeStart, rangeEnd, eventTypeFilter]);

  const toggleTurbine = (tid: string) => {
    setSelectedIds(prev =>
      prev.includes(tid) ? prev.filter(id => id !== tid) : [...prev, tid]
    );
  };

  const selectAll = () => setSelectedIds([...allTurbineIds]);
  const selectNone = () => setSelectedIds([]);

  const exportEvents = () => {
    const params = new URLSearchParams({ format: 'csv', limit: '5000' });
    if (rangeStart) params.set('start', new Date(rangeStart).toISOString());
    if (rangeEnd) params.set('end', new Date(rangeEnd).toISOString());
    if (eventTypeFilter) params.set('event_type', eventTypeFilter);
    window.open(`${API_BASE}/api/export/events?${params.toString()}`, '_blank');
  };

  return (
    <div className="space-y-4">
      {/* Turbine selector */}
      <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-gray-300">{u('Select Turbines', '選擇風機')}</h3>
          <div className="flex gap-2">
            <button onClick={selectAll} className="text-xs px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded text-gray-300">
              {u('All', '全選')}
            </button>
            <button onClick={selectNone} className="text-xs px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded text-gray-300">
              {u('None', '清除')}
            </button>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          {allTurbineIds.map(tid => (
            <button
              key={tid}
              onClick={() => toggleTurbine(tid)}
              className={`px-3 py-1.5 rounded text-xs font-mono transition-colors ${
                selectedIds.includes(tid)
                  ? 'bg-cyan-600 text-white'
                  : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
              }`}
            >
              {tid}
            </button>
          ))}
        </div>
      </div>

      {/* Filters */}
      <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <div>
            <label className="block text-xs text-gray-400 mb-1">{u('Start', '開始時間')}</label>
            <input type="datetime-local" value={rangeStart} onChange={e => setRangeStart(e.target.value)}
              className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-sm text-white" />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">{u('End', '結束時間')}</label>
            <input type="datetime-local" value={rangeEnd} onChange={e => setRangeEnd(e.target.value)}
              className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-sm text-white" />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">{u('Event Type', '事件類型')}</label>
            <select value={eventTypeFilter} onChange={e => setEventTypeFilter(e.target.value)}
              className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-sm text-white">
              <option value="">{u('All Types', '全部類型')}</option>
              <option value="fault">{u('Fault', '故障')}</option>
              <option value="fault_lifecycle">{u('Fault Lifecycle', '故障生命週期')}</option>
              <option value="grid">{u('Grid', '電網')}</option>
              <option value="state">{u('State', '狀態')}</option>
              <option value="operator">{u('Operator', '操作')}</option>
              <option value="wind">{u('Wind', '風況')}</option>
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">{u('Export', '匯出')}</label>
            <button onClick={exportEvents} className="w-full bg-cyan-600 hover:bg-cyan-500 text-white rounded px-3 py-2 text-sm transition-colors">
              {u('Export Events CSV', '匯出事件 CSV')}
            </button>
          </div>
        </div>
        <div className="mt-2 text-sm text-gray-400">
          {loading ? u('Loading...', '載入中...') : `${timeline.length} ${u('events', '筆事件')} | ${selectedIds.length} ${u('turbines', '台風機')}`}
        </div>
      </div>

      {/* Summary grid */}
      {selectedIds.length > 0 && (
        <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-gray-300 mb-3">{u('Summary', '摘要')}</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
            {selectedIds.map(tid => {
              const s = summary[tid] || { total: 0, by_type: {} };
              return (
                <div key={tid} className="bg-gray-900/50 rounded-lg p-3 border border-gray-700">
                  <div className="font-mono text-sm text-cyan-400 mb-2">{tid}</div>
                  <div className="text-2xl font-bold text-white">{s.total}</div>
                  <div className="text-xs text-gray-400 mt-1">{u('events', '事件')}</div>
                  <div className="flex flex-wrap gap-1 mt-2">
                    {Object.entries(s.by_type).map(([type, count]) => (
                      <span key={type} className="text-xs px-1.5 py-0.5 rounded" style={{
                        backgroundColor: (EVENT_COLORS[type] || '#64748b') + '20',
                        color: EVENT_COLORS[type] || '#94a3b8',
                      }}>
                        {type}: {count as number}
                      </span>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Farm-wide events */}
      {farmEvents.length > 0 && (
        <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-yellow-400 mb-3">{u('Farm-Wide Events', '全場事件')}</h3>
          <div className="space-y-1 max-h-40 overflow-y-auto">
            {farmEvents.slice(0, 20).map((ev, i) => (
              <div key={i} className="flex items-center gap-3 text-sm py-1 border-b border-gray-700/50">
                <span className="text-xs text-gray-500 font-mono w-40 flex-shrink-0">
                  {new Date(ev.timestamp).toLocaleString()}
                </span>
                <span className="px-1.5 py-0.5 rounded text-xs" style={{
                  backgroundColor: (EVENT_COLORS[ev.event_type] || '#64748b') + '20',
                  color: EVENT_COLORS[ev.event_type] || '#94a3b8',
                }}>
                  {ev.event_type}
                </span>
                <span className="text-gray-300 truncate">{ev.title}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Per-turbine timeline */}
      <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-gray-300 mb-3">{u('Event Timeline', '事件時間線')}</h3>
        <div className="space-y-1 max-h-[500px] overflow-y-auto">
          {timeline.length === 0 && !loading && (
            <div className="text-gray-500 text-sm text-center py-8">{u('No events found', '未找到事件')}</div>
          )}
          {timeline.map((ev, i) => {
            const sevClass = SEVERITY_COLORS[ev.severity || 'info'] || SEVERITY_COLORS.info;
            return (
              <div key={i} className="flex items-start gap-3 text-sm py-2 border-b border-gray-700/50">
                <span className="text-xs text-gray-500 font-mono w-40 flex-shrink-0">
                  {new Date(ev.timestamp).toLocaleString()}
                </span>
                <span className="font-mono text-cyan-400 text-xs w-14 flex-shrink-0">{ev._turbine_id || ev.turbine_id || '—'}</span>
                <span className="px-1.5 py-0.5 rounded text-xs flex-shrink-0" style={{
                  backgroundColor: (EVENT_COLORS[ev.event_type] || '#64748b') + '20',
                  color: EVENT_COLORS[ev.event_type] || '#94a3b8',
                }}>
                  {ev.event_type}
                </span>
                {ev.severity && (
                  <span className={`px-1.5 py-0.5 rounded text-xs border flex-shrink-0 ${sevClass}`}>
                    {ev.severity}
                  </span>
                )}
                <div className="min-w-0">
                  <span className="text-gray-200">{ev.title}</span>
                  {ev.detail && <span className="text-gray-500 ml-2 text-xs">{ev.detail}</span>}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default EventComparisonView;

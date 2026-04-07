import React, { useEffect, useMemo, useState } from 'react';
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceArea,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { TurbineData } from '../types';
import EventComparisonView from './EventComparisonView';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';
const LINE_COLORS = ['#22d3ee', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16'];

const TAG_PRESETS: Record<string, string[]> = {
  startup: ['WTUR_TurSt', 'WROT_RotSpd', 'WTUR_TotPwrAt', 'WGEN_GnVtgMs', 'WCNV_CnvGnFrq'],
  thermal: ['WGEN_GnStaTmp1', 'WGEN_GnBrgTmp1', 'WCNV_CnvCabinTmp', 'WGDC_TrfCoreTmp'],
  vibration: ['WNAC_VibMsNacXDir', 'WNAC_VibMsNacYDir', 'WYAW_YwBrkHyPrs', 'WROT_RotSpd'],
  pitch: ['WROT_PtAngValBl1', 'WROT_PtAngValBl2', 'WROT_PtAngValBl3', 'WTUR_TotPwrAt'],
};

const EVENT_COLORS: Record<string, string> = {
  grid: '#f59e0b',
  fault: '#ef4444',
  operator: '#22c55e',
  wind: '#38bdf8',
  state: '#a78bfa',
};

const EVENT_TYPES = ['grid', 'fault', 'operator', 'wind', 'state'] as const;
type EventType = typeof EVENT_TYPES[number];

interface HistoryPageProps {
  turbines: TurbineData[];
  lang?: 'en' | 'zh';
}

interface HistoryRow {
  timestamp: string;
  scada?: Record<string, number>;
  scada_json?: string;
}

interface HistoryEvent {
  id: number;
  timestamp: string;
  end_timestamp?: string | null;
  turbine_id?: string | null;
  event_type: string;
  source: string;
  title: string;
  detail?: string | null;
  payload?: Record<string, unknown>;
  _time?: number;
  _endTime?: number;
}

const toDateTimeLocal = (value: Date) => {
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${value.getFullYear()}-${pad(value.getMonth() + 1)}-${pad(value.getDate())}T${pad(value.getHours())}:${pad(value.getMinutes())}`;
};

const HistoryPage: React.FC<HistoryPageProps> = ({ turbines, lang = 'zh' }) => {
  const [historyTab, setHistoryTab] = useState<'single' | 'compare'>('single');
  const [selectedTurbineId, setSelectedTurbineId] = useState('WT001');
  const [activeTags, setActiveTags] = useState<string[]>(TAG_PRESETS.startup);
  const [limit, setLimit] = useState(300);
  const [chartData, setChartData] = useState<Record<string, number | string | null>[]>([]);
  const [events, setEvents] = useState<HistoryEvent[]>([]);
  const [selectedEventId, setSelectedEventId] = useState<number | null>(null);
  const [focusWindowSec, setFocusWindowSec] = useState<number>(0);
  const [eventSearch, setEventSearch] = useState('');
  const [rangeStart, setRangeStart] = useState(() => toDateTimeLocal(new Date(Date.now() - 2 * 60 * 60 * 1000)));
  const [rangeEnd, setRangeEnd] = useState(() => toDateTimeLocal(new Date()));
  const [enabledEventTypes, setEnabledEventTypes] = useState<Record<EventType, boolean>>({
    grid: true,
    fault: true,
    operator: true,
    wind: true,
    state: true,
  });
  const [tagLabels, setTagLabels] = useState<Record<string, string>>({});
  const [customTags, setCustomTags] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!turbines.length) return;
    setSelectedTurbineId(prev => prev || `WT${String(turbines[0].id).padStart(3, '0')}`);
  }, [turbines]);

  useEffect(() => {
    fetch(`${API_BASE}/api/i18n/tags?lang=${lang}`)
      .then(res => res.json())
      .then(setTagLabels)
      .catch(() => {});
  }, [lang]);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    const params = new URLSearchParams({ limit: String(limit) });
    if (rangeStart) params.set('start', new Date(rangeStart).toISOString());
    if (rangeEnd) params.set('end', new Date(rangeEnd).toISOString());

    fetch(`${API_BASE}/api/turbines/${selectedTurbineId}/history?${params.toString()}`, { signal: controller.signal })
      .then(res => res.json())
      .then(res => {
        const rows: HistoryRow[] = Array.isArray(res.data) ? [...res.data].reverse() : [];
        const eventRows: HistoryEvent[] = Array.isArray(res.events) ? [...res.events].reverse() : [];
        const mapped = rows.map(row => {
          let scada = row.scada || {};
          if (!row.scada && row.scada_json) {
            try {
              scada = JSON.parse(row.scada_json);
            } catch {
              scada = {};
            }
          }
          const point: Record<string, number | string | null> = {
            timestamp: row.timestamp,
            _time: row.timestamp ? new Date(row.timestamp).getTime() : 0,
          };
          for (const tag of activeTags) {
            point[tag] = scada?.[tag] ?? null;
          }
          return point;
        });

        setChartData(mapped);
        setEvents(eventRows);
        setSelectedEventId(prev => (eventRows.some(event => event.id === prev) ? prev : eventRows[0]?.id ?? null));
      })
      .catch(() => {})
      .finally(() => setLoading(false));

    return () => controller.abort();
  }, [selectedTurbineId, activeTags, limit, rangeStart, rangeEnd]);

  const allVisibleEvents = useMemo(
    () => events
      .filter(event => enabledEventTypes[(event.event_type as EventType)] ?? false)
      .map(event => ({
        ...event,
        _time: event.timestamp ? new Date(event.timestamp).getTime() : 0,
        _endTime: event.end_timestamp ? new Date(event.end_timestamp).getTime() : undefined,
      }))
      .filter(event => (event._time ?? 0) > 0)
      .filter(event => {
        const q = eventSearch.trim().toLowerCase();
        if (!q) return true;
        const blob = `${event.title} ${event.detail ?? ''} ${event.source} ${event.event_type} ${event.turbine_id ?? ''}`.toLowerCase();
        return blob.includes(q);
      }),
    [events, enabledEventTypes, eventSearch],
  );

  const selectedEvent = useMemo(
    () => allVisibleEvents.find(event => event.id === selectedEventId) || allVisibleEvents[0] || null,
    [allVisibleEvents, selectedEventId],
  );

  const focusedChartData = useMemo(() => {
    if (!selectedEvent || focusWindowSec <= 0) return chartData;
    const center = selectedEvent._time ?? 0;
    const halfWindowMs = focusWindowSec * 1000;
    return chartData.filter(point => {
      const time = Number(point._time ?? 0);
      return time >= center - halfWindowMs && time <= center + halfWindowMs;
    });
  }, [chartData, selectedEvent, focusWindowSec]);

  const focusedEvents = useMemo(() => {
    if (!selectedEvent || focusWindowSec <= 0) return allVisibleEvents;
    const center = selectedEvent._time ?? 0;
    const halfWindowMs = focusWindowSec * 1000;
    return allVisibleEvents.filter(event => {
      const start = event._time ?? 0;
      const end = event._endTime ?? start;
      return end >= center - halfWindowMs && start <= center + halfWindowMs;
    });
  }, [allVisibleEvents, selectedEvent, focusWindowSec]);

  const previewRows = useMemo(() => focusedChartData.slice(-20).reverse(), [focusedChartData]);

  const applyPreset = (presetId: keyof typeof TAG_PRESETS) => setActiveTags(TAG_PRESETS[presetId]);
  const applyCustomTags = () => {
    const tags = customTags.split(',').map(tag => tag.trim()).filter(Boolean);
    if (tags.length) setActiveTags(tags);
  };

  const exportCsv = (focusedOnly: boolean) => {
    const params = new URLSearchParams({
      turbine_id: selectedTurbineId,
      limit: String(limit),
      format: 'csv',
    });
    const focusCenter = selectedEvent?._time ?? 0;
    if (focusedOnly && selectedEvent && focusWindowSec > 0) {
      params.set('start', new Date(focusCenter - focusWindowSec * 1000).toISOString());
      params.set('end', new Date(focusCenter + focusWindowSec * 1000).toISOString());
    } else {
      if (rangeStart) params.set('start', new Date(rangeStart).toISOString());
      if (rangeEnd) params.set('end', new Date(rangeEnd).toISOString());
    }
    window.open(`${API_BASE}/api/export/history?${params.toString()}`, '_blank');
  };

  const toggleEventType = (eventType: EventType) => {
    setEnabledEventTypes(prev => ({ ...prev, [eventType]: !prev[eventType] }));
  };

  const getLabel = (tag: string) => tagLabels[tag] || tag;
  const getEventColor = (eventType: string) => EVENT_COLORS[eventType] || '#94a3b8';
  const getEventTypeLabel = (eventType: string) => {
    if (lang === 'zh') {
      if (eventType === 'grid') return '電網';
      if (eventType === 'fault') return '故障';
      if (eventType === 'operator') return '操作';
      if (eventType === 'wind') return '風況';
      if (eventType === 'state') return '狀態';
    }
    return eventType;
  };

  return (
    <div className="space-y-6">
      {/* Tab selector: Single Turbine vs Multi-Turbine Comparison */}
      <div className="flex gap-2">
        <button
          onClick={() => setHistoryTab('single')}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            historyTab === 'single' ? 'bg-cyan-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
          }`}
        >
          {lang === 'zh' ? '單機歷史' : 'Single Turbine'}
        </button>
        <button
          onClick={() => setHistoryTab('compare')}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            historyTab === 'compare' ? 'bg-cyan-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
          }`}
        >
          {lang === 'zh' ? '多機事件比較' : 'Multi-Turbine Comparison'}
        </button>
      </div>

      {historyTab === 'compare' ? (
        <EventComparisonView turbines={turbines} lang={lang} />
      ) : (<>
      <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-5">
        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-1 md:grid-cols-3 xl:grid-cols-6 gap-3">
            <div>
              <label className="block text-xs text-gray-400 mb-1">{lang === 'zh' ? '風機' : 'Turbine'}</label>
              <select value={selectedTurbineId} onChange={e => setSelectedTurbineId(e.target.value)} className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-sm text-white">
                {turbines.map(t => {
                  const tid = `WT${String(t.id).padStart(3, '0')}`;
                  return <option key={tid} value={tid}>{tid} / {t.name}</option>;
                })}
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">{lang === 'zh' ? '筆數' : 'Samples'}</label>
              <select value={limit} onChange={e => setLimit(Number(e.target.value))} className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-sm text-white">
                {[120, 300, 600, 1200, 3600].map(value => <option key={value} value={value}>{value}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">{lang === 'zh' ? '開始時間' : 'Start'}</label>
              <input type="datetime-local" value={rangeStart} onChange={e => setRangeStart(e.target.value)} className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-sm text-white" />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">{lang === 'zh' ? '結束時間' : 'End'}</label>
              <input type="datetime-local" value={rangeEnd} onChange={e => setRangeEnd(e.target.value)} className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-sm text-white" />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">{lang === 'zh' ? '匯出目前區間' : 'Export Range'}</label>
              <button onClick={() => exportCsv(false)} className="w-full bg-cyan-600 hover:bg-cyan-500 text-white rounded px-3 py-2 text-sm transition-colors">
                {lang === 'zh' ? '下載目前區間' : 'Download Range'}
              </button>
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">{lang === 'zh' ? '匯出聚焦視窗' : 'Export Focus'}</label>
              <button onClick={() => exportCsv(true)} className="w-full bg-gray-700 hover:bg-gray-600 text-white rounded px-3 py-2 text-sm transition-colors">
                {lang === 'zh' ? '下載聚焦區段' : 'Download Focus'}
              </button>
            </div>
          </div>
          <div className="text-sm text-gray-400">
            {loading ? (lang === 'zh' ? '載入中...' : 'Loading...') : `${focusedChartData.length} ${lang === 'zh' ? '筆資料' : 'rows'}`}
          </div>
        </div>
      </div>

      <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-5">
        <h2 className="text-xl font-bold text-white mb-4">{lang === 'zh' ? '歷史資料檢視' : 'Historical Data Viewer'}</h2>

        <div className="flex flex-wrap gap-2 mb-4">
          {Object.keys(TAG_PRESETS).map(key => (
            <button key={key} onClick={() => applyPreset(key as keyof typeof TAG_PRESETS)} className="px-3 py-1.5 text-xs rounded border border-gray-600 bg-gray-900 text-gray-300 hover:border-cyan-400 hover:text-white transition-colors">
              {key}
            </button>
          ))}
        </div>

        <div className="flex gap-2 mb-4">
          <input type="text" value={customTags} onChange={e => setCustomTags(e.target.value)} placeholder={lang === 'zh' ? '自訂 Tag，以逗號分隔' : 'Custom tags, comma separated'} className="flex-1 bg-gray-900 border border-gray-600 rounded px-3 py-2 text-sm text-white" />
          <button onClick={applyCustomTags} className="bg-gray-700 hover:bg-gray-600 text-white rounded px-3 py-2 text-sm transition-colors">
            {lang === 'zh' ? '套用' : 'Apply'}
          </button>
        </div>

        <div className="mb-4 grid grid-cols-1 xl:grid-cols-[1fr_auto_auto] gap-4 xl:items-end">
          <div>
            <div className="text-xs text-gray-400 mb-2">{lang === 'zh' ? '事件篩選' : 'Event Filters'}</div>
            <div className="flex flex-wrap gap-2">
              {EVENT_TYPES.map(eventType => (
                <button
                  key={eventType}
                  onClick={() => toggleEventType(eventType)}
                  className={`px-3 py-1.5 text-xs rounded border transition-colors ${enabledEventTypes[eventType] ? 'text-white' : 'border-gray-700 bg-gray-900 text-gray-500'}`}
                  style={enabledEventTypes[eventType] ? { borderColor: getEventColor(eventType), backgroundColor: `${getEventColor(eventType)}22` } : undefined}
                >
                  {getEventTypeLabel(eventType)}
                </button>
              ))}
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-400 mb-2">{lang === 'zh' ? '事件搜尋' : 'Event Search'}</div>
            <input type="text" value={eventSearch} onChange={e => setEventSearch(e.target.value)} placeholder={lang === 'zh' ? '搜尋標題、內容、類型' : 'Search title, detail, type'} className="w-full xl:w-72 bg-gray-900 border border-gray-600 rounded px-3 py-2 text-sm text-white" />
          </div>
          <div>
            <div className="text-xs text-gray-400 mb-2">{lang === 'zh' ? '聚焦視窗' : 'Focus Window'}</div>
            <div className="flex flex-wrap gap-2">
              {[0, 30, 120].map(value => (
                <button key={value} onClick={() => setFocusWindowSec(value)} className={`px-3 py-1.5 text-xs rounded border transition-colors ${focusWindowSec === value ? 'border-cyan-500 bg-cyan-500/15 text-white' : 'border-gray-700 bg-gray-900 text-gray-400'}`}>
                  {value === 0 ? (lang === 'zh' ? '全部' : 'All') : `${value}s`}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="bg-gray-900/60 rounded-lg p-3">
          <ResponsiveContainer width="100%" height={420}>
            <LineChart data={focusedChartData}>
              <CartesianGrid stroke="#1f2937" strokeDasharray="3 3" />
              <XAxis dataKey="_time" tickFormatter={value => new Date(value).toLocaleTimeString()} stroke="#9ca3af" fontSize={11} />
              <YAxis stroke="#9ca3af" fontSize={11} />
              <Tooltip
                contentStyle={{ backgroundColor: '#111827', border: '1px solid #374151', borderRadius: '0.5rem' }}
                labelFormatter={value => new Date(value).toLocaleString()}
                formatter={(value: number, name: string) => [value != null ? Number(value).toFixed(2) : '--', getLabel(name)]}
              />
              <Legend formatter={value => getLabel(value)} />
              {focusedEvents.filter(event => (event._endTime ?? 0) > (event._time ?? 0) && (event.event_type === 'grid' || event.event_type === 'wind')).map(event => (
                <ReferenceArea
                  key={`band-${event.id}`}
                  x1={event._time}
                  x2={event._endTime}
                  fill={getEventColor(event.event_type)}
                  fillOpacity={selectedEvent?.id === event.id ? 0.16 : 0.08}
                  strokeOpacity={0}
                />
              ))}
              {focusedEvents.map((event, index) => (
                <ReferenceLine
                  key={`${event.id}-${event.timestamp}`}
                  x={event._time}
                  stroke={getEventColor(event.event_type)}
                  strokeDasharray="4 4"
                  strokeOpacity={selectedEvent?.id === event.id ? 1 : 0.75}
                  strokeWidth={selectedEvent?.id === event.id ? 3 : 1.5}
                  ifOverflow="extendDomain"
                  label={{ value: index % 2 === 0 ? getEventTypeLabel(event.event_type).toUpperCase() : '', position: 'top', fill: '#d1d5db', fontSize: 10 }}
                />
              ))}
              {activeTags.map((tag, index) => (
                <Line key={tag} type="monotone" dataKey={tag} stroke={LINE_COLORS[index % LINE_COLORS.length]} strokeWidth={1.8} dot={false} isAnimationActive={false} connectNulls />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="mt-3 text-xs text-gray-500">
          {(lang === 'zh' ? '目前顯示' : 'Showing')}: {activeTags.map(getLabel).join(' | ')}
        </div>

        <div className="mt-4 grid grid-cols-1 xl:grid-cols-[1.2fr_0.8fr] gap-4 border-t border-gray-700 pt-4">
          <div>
            <h4 className="text-sm font-semibold text-white mb-2">{lang === 'zh' ? '事件標記' : 'Event Markers'}</h4>
            {focusedEvents.length ? (
              <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                {focusedEvents.slice().reverse().map(event => (
                  <button
                    key={`event-${event.id}`}
                    type="button"
                    onClick={() => setSelectedEventId(event.id)}
                    className={`w-full text-left rounded border px-3 py-2 text-xs transition-colors ${selectedEvent?.id === event.id ? 'border-cyan-500 bg-gray-800 text-white' : 'border-gray-700 bg-gray-900/60 text-gray-200 hover:border-gray-500'}`}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <span className="font-medium">{event.title}</span>
                      <span className="text-gray-500">{new Date(event.timestamp).toLocaleString()}</span>
                    </div>
                    <div className="mt-1 text-gray-400">
                      {[getEventTypeLabel(event.event_type), event.turbine_id || 'FARM', event.detail || ''].filter(Boolean).join(' | ')}
                    </div>
                  </button>
                ))}
              </div>
            ) : (
              <div className="text-xs text-gray-500">{lang === 'zh' ? '目前區間沒有事件' : 'No events in current range'}</div>
            )}
          </div>

          <div>
            <h4 className="text-sm font-semibold text-white mb-2">{lang === 'zh' ? '事件詳情' : 'Event Details'}</h4>
            {selectedEvent ? (
              <div className="rounded border border-gray-700 bg-gray-900/60 p-4 space-y-3">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="text-white font-medium">{selectedEvent.title}</div>
                    <div className="text-xs text-gray-400 mt-1">
                      {[getEventTypeLabel(selectedEvent.event_type), selectedEvent.source, selectedEvent.turbine_id || 'FARM'].join(' | ')}
                    </div>
                  </div>
                  <span className="inline-flex rounded px-2 py-1 text-[11px] font-medium" style={{ color: getEventColor(selectedEvent.event_type), backgroundColor: `${getEventColor(selectedEvent.event_type)}22` }}>
                    {getEventTypeLabel(selectedEvent.event_type)}
                  </span>
                </div>
                <div className="text-xs text-gray-400">
                  {new Date(selectedEvent.timestamp).toLocaleString()}
                  {selectedEvent.end_timestamp ? ` -> ${new Date(selectedEvent.end_timestamp).toLocaleString()}` : ''}
                </div>
                <div className="text-sm text-gray-200">{selectedEvent.detail || (lang === 'zh' ? '沒有額外描述' : 'No additional detail')}</div>
                <div className="flex flex-wrap gap-2">
                  {[30, 120].map(value => (
                    <button key={value} onClick={() => setFocusWindowSec(value)} className="rounded border border-gray-600 bg-gray-800 px-3 py-1.5 text-xs text-white hover:border-cyan-400">
                      {lang === 'zh' ? `聚焦前後 ${value} 秒` : `Focus ±${value}s`}
                    </button>
                  ))}
                  <button onClick={() => setFocusWindowSec(0)} className="rounded border border-gray-600 bg-gray-800 px-3 py-1.5 text-xs text-white hover:border-cyan-400">
                    {lang === 'zh' ? '顯示全部' : 'Show All'}
                  </button>
                </div>
                <div>
                  <div className="text-xs text-gray-400 mb-2">Payload</div>
                  <pre className="overflow-auto rounded bg-black/30 p-3 text-xs text-gray-300 whitespace-pre-wrap break-all">
                    {JSON.stringify(selectedEvent.payload ?? {}, null, 2)}
                  </pre>
                </div>
              </div>
            ) : (
              <div className="text-xs text-gray-500">{lang === 'zh' ? '請從左側選擇事件' : 'Select an event from the list'}</div>
            )}
          </div>
        </div>
      </div>

      <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-5">
        <h3 className="text-lg font-semibold text-white mb-4">{lang === 'zh' ? '最近 20 筆' : 'Latest 20 Rows'}</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="border-b border-gray-700 text-gray-400">
                <th className="text-left py-2 pr-4">{lang === 'zh' ? '時間' : 'Timestamp'}</th>
                {activeTags.map(tag => (
                  <th key={tag} className="text-left py-2 pr-4">{getLabel(tag)}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {previewRows.map((row, index) => (
                <tr key={`${row.timestamp}-${index}`} className="border-b border-gray-800 text-gray-200">
                  <td className="py-2 pr-4 whitespace-nowrap">{String(row.timestamp)}</td>
                  {activeTags.map(tag => (
                    <td key={tag} className="py-2 pr-4 whitespace-nowrap">
                      {row[tag] != null ? Number(row[tag]).toFixed(2) : '--'}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      </>)}
    </div>
  );
};

export default HistoryPage;

import React, { useRef, useEffect, useState, useCallback } from 'react';
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { type TurbineData } from '../types';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

interface FarmTrendChartProps {
  turbines: TurbineData[];
  lang?: 'en' | 'zh';
}

interface FarmDataPoint {
  time: number;
  totalPower: number;
  avgWindSpeed: number;
}

type TimeRange = '5m' | '1h' | '12h' | '1d';

const TIME_RANGES: { id: TimeRange; label_en: string; label_zh: string; refreshMs: number }[] = [
  { id: '5m',  label_en: '5 Min',   label_zh: '5分鐘',  refreshMs: 2000 },
  { id: '1h',  label_en: '1 Hour',  label_zh: '1小時',  refreshMs: 5000 },
  { id: '12h', label_en: '12 Hours', label_zh: '12小時', refreshMs: 30000 },
  { id: '1d',  label_en: '1 Day',   label_zh: '1天',    refreshMs: 60000 },
];

const MAX_LIVE_POINTS = 150;

const FarmTrendChart: React.FC<FarmTrendChartProps> = ({ turbines, lang = 'zh' }) => {
  const [range, setRange] = useState<TimeRange>('5m');
  const [liveData, setLiveData] = useState<FarmDataPoint[]>([]);
  const [apiData, setApiData] = useState<FarmDataPoint[]>([]);
  const [loading, setLoading] = useState(false);
  const lastLiveUpdate = useRef(0);

  // Live accumulation for 5m mode
  useEffect(() => {
    if (range !== '5m' || !turbines.length) return;
    const now = Date.now();
    if (now - lastLiveUpdate.current < 1800) return;
    lastLiveUpdate.current = now;

    const totalPower = turbines.reduce((s, t) => s + t.powerOutput, 0);
    const avgWindSpeed = turbines.reduce((s, t) => s + t.windSpeed, 0) / turbines.length;

    setLiveData(prev => {
      const next = [...prev, { time: now, totalPower: +totalPower.toFixed(2), avgWindSpeed: +avgWindSpeed.toFixed(1) }];
      return next.length > MAX_LIVE_POINTS ? next.slice(-MAX_LIVE_POINTS) : next;
    });
  }, [turbines, range]);

  // API fetch for longer ranges
  const fetchApiData = useCallback(() => {
    if (range === '5m') return;
    setLoading(true);
    fetch(`${API_BASE}/api/turbines/farm-trend?range=${range}&points=150`)
      .then(r => r.json())
      .then(res => {
        if (res.data) {
          setApiData(res.data.map((d: any) => ({
            time: d.timestamp ? new Date(d.timestamp).getTime() : 0,
            totalPower: d.totalPower,
            avgWindSpeed: d.avgWindSpeed,
          })));
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [range]);

  useEffect(() => {
    if (range === '5m') return;
    fetchApiData();
    const refreshMs = TIME_RANGES.find(r => r.id === range)?.refreshMs || 30000;
    const iv = setInterval(fetchApiData, refreshMs);
    return () => clearInterval(iv);
  }, [fetchApiData, range]);

  const chartData = range === '5m' ? liveData : apiData;
  const u = (en: string, zh: string) => lang === 'zh' ? zh : en;

  const formatTime = (t: number) => {
    if (!t) return '';
    const d = new Date(t);
    if (range === '5m' || range === '1h') {
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    }
    return d.toLocaleTimeString([], { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' } as any);
  };

  return (
    <div className="bg-gray-800/50 rounded-lg p-4 border border-cyan-500/20">
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-semibold text-cyan-400 uppercase tracking-wider">
          {u('Farm Power & Wind Trend', '全風場發電量與風速趨勢')}
        </h4>
        <div className="flex gap-1">
          {TIME_RANGES.map(r => (
            <button key={r.id} onClick={() => setRange(r.id)}
              className={`px-2 py-0.5 text-xs rounded transition-colors ${
                range === r.id
                  ? 'bg-cyan-600 text-white'
                  : 'bg-gray-700 text-gray-400 hover:text-white'
              }`}>
              {lang === 'zh' ? r.label_zh : r.label_en}
            </button>
          ))}
        </div>
      </div>
      <div className="bg-gray-900/50 rounded p-2 relative">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-900/50 z-10 rounded">
            <span className="text-xs text-cyan-400 animate-pulse">{u('Loading...', '載入中...')}</span>
          </div>
        )}
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
            <XAxis
              dataKey="time"
              tickFormatter={formatTime}
              stroke="#6b7280"
              fontSize={10}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              yAxisId="power"
              stroke="#22d3ee"
              fontSize={10}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v) => `${v}`}
              label={{ value: 'MW', angle: -90, position: 'insideLeft', style: { fill: '#22d3ee', fontSize: 10 } }}
            />
            <YAxis
              yAxisId="wind"
              orientation="right"
              stroke="#f59e0b"
              fontSize={10}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v) => `${v}`}
              label={{ value: 'm/s', angle: 90, position: 'insideRight', style: { fill: '#f59e0b', fontSize: 10 } }}
            />
            <Tooltip
              contentStyle={{ backgroundColor: 'rgba(17,24,39,0.95)', border: '1px solid #374151', borderRadius: '0.5rem', color: '#e5e7eb' }}
              labelFormatter={(t) => t ? new Date(t).toLocaleString() : ''}
              formatter={(value: number, name: string) => {
                if (name === 'totalPower') return [`${value.toFixed(2)} MW`, u('Total Power', '總發電量')];
                return [`${value.toFixed(1)} m/s`, u('Avg Wind Speed', '平均風速')];
              }}
            />
            <Legend
              formatter={(value) => {
                if (value === 'totalPower') return u('Total Power (MW)', '總發電量 (MW)');
                return u('Avg Wind Speed (m/s)', '平均風速 (m/s)');
              }}
              wrapperStyle={{ fontSize: '11px' }}
            />
            <Line
              yAxisId="power"
              type="monotone"
              dataKey="totalPower"
              stroke="#22d3ee"
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
            <Line
              yAxisId="wind"
              type="monotone"
              dataKey="avgWindSpeed"
              stroke="#f59e0b"
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default FarmTrendChart;

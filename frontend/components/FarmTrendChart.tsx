import React, { useRef, useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { type TurbineData } from '../types';

interface FarmTrendChartProps {
  turbines: TurbineData[];
  lang?: 'en' | 'zh';
}

interface FarmDataPoint {
  time: number;
  totalPower: number;
  avgWindSpeed: number;
}

const MAX_POINTS = 120; // ~4 minutes at 2s intervals

const FarmTrendChart: React.FC<FarmTrendChartProps> = ({ turbines, lang = 'zh' }) => {
  const [data, setData] = useState<FarmDataPoint[]>([]);
  const lastUpdate = useRef(0);

  useEffect(() => {
    if (!turbines.length) return;
    const now = Date.now();
    // Throttle to ~2s intervals to match WS refresh
    if (now - lastUpdate.current < 1800) return;
    lastUpdate.current = now;

    const totalPower = turbines.reduce((s, t) => s + t.powerOutput, 0);
    const avgWindSpeed = turbines.reduce((s, t) => s + t.windSpeed, 0) / turbines.length;

    setData(prev => {
      const next = [...prev, { time: now, totalPower: +totalPower.toFixed(2), avgWindSpeed: +avgWindSpeed.toFixed(1) }];
      return next.length > MAX_POINTS ? next.slice(-MAX_POINTS) : next;
    });
  }, [turbines]);

  const u = (en: string, zh: string) => lang === 'zh' ? zh : en;

  return (
    <div className="bg-gray-800/50 rounded-lg p-4 border border-cyan-500/20">
      <h4 className="text-sm font-semibold text-cyan-400 mb-3 uppercase tracking-wider">
        {u('Farm Power & Wind Trend', '全風場發電量與風速趨勢')}
      </h4>
      <div className="bg-gray-900/50 rounded p-2">
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
            <XAxis
              dataKey="time"
              tickFormatter={(t) => t ? new Date(t).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : ''}
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
              labelFormatter={(t) => t ? new Date(t).toLocaleTimeString() : ''}
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

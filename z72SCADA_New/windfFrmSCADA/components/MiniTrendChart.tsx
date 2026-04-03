
import React from 'react';
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip } from 'recharts';

interface MiniTrendChartProps {
  data: { time: number; power: number }[];
}

const MiniTrendChart: React.FC<MiniTrendChartProps> = ({ data }) => {
  return (
    <ResponsiveContainer width="100%" height={150}>
      <LineChart data={data} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}>
        <XAxis 
            dataKey="time" 
            tickFormatter={(unixTime) => new Date(unixTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            stroke="#9ca3af"
            fontSize={10}
            axisLine={false}
            tickLine={false}
        />
        <YAxis 
            stroke="#9ca3af" 
            fontSize={10}
            domain={['dataMin - 0.5', 'dataMax + 0.5']}
            axisLine={false}
            tickLine={false}
        />
        <Tooltip
            contentStyle={{
                backgroundColor: 'rgba(31, 41, 55, 0.8)',
                border: '1px solid #4b5563',
                borderRadius: '0.5rem',
                color: '#e5e7eb',
            }}
            labelStyle={{ color: '#9ca3af' }}
            formatter={(value: number) => [`${value.toFixed(2)} MW`, 'Power']}
            labelFormatter={(label) => new Date(label).toLocaleTimeString()}
        />
        <Line 
            type="monotone" 
            dataKey="power" 
            stroke="#22d3ee" 
            strokeWidth={2} 
            dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
};

export default MiniTrendChart;

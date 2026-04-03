
import React from 'react';

interface GaugeProps {
  value: number;
  maxValue: number;
  label: string;
  unit: string;
}

const Gauge: React.FC<GaugeProps> = ({ value, maxValue, label, unit }) => {
  const percentage = Math.min(Math.max(value / maxValue, 0), 1);
  const angle = percentage * 270 - 135; // from -135 to 135 degrees
  const strokeWidth = 12;
  const radius = 60;
  const circumference = 2 * Math.PI * radius;
  const arcLength = circumference * 0.75; // 270 degrees arc
  const strokeDashoffset = arcLength * (1 - percentage);

  return (
    <div className="bg-gray-800/50 p-4 rounded-lg flex flex-col items-center justify-center aspect-square">
      <svg viewBox="0 0 160 120" className="w-full h-auto">
        {/* Background Arc */}
        <path
          d="M 20 100 A 60 60 0 1 1 140 100"
          fill="none"
          stroke="currentColor"
          className="text-gray-700"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        />
        {/* Value Arc */}
        <path
          d="M 20 100 A 60 60 0 1 1 140 100"
          fill="none"
          stroke="currentColor"
          className="text-cyan-400"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={arcLength}
          strokeDashoffset={strokeDashoffset}
          style={{ transition: 'stroke-dashoffset 0.5s ease-out' }}
        />
        {/* Value Text */}
        <text
          x="80"
          y="80"
          textAnchor="middle"
          className="font-orbitron font-bold text-4xl fill-current text-white"
        >
          {value.toFixed(1)}
        </text>
        <text
          x="80"
          y="100"
          textAnchor="middle"
          className="text-lg fill-current text-gray-400"
        >
          {unit}
        </text>
      </svg>
      <p className="text-center mt-2 text-sm text-gray-300">{label}</p>
    </div>
  );
};

export default Gauge;

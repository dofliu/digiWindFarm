
import React from 'react';

interface DataCardProps {
  icon: React.ReactNode;
  label: string;
  value: string;
}

const DataCard: React.FC<DataCardProps> = ({ icon, label, value }) => {
  return (
    <div className="bg-gray-800/50 p-4 rounded-lg flex items-center space-x-4">
      <div className="flex-shrink-0 text-cyan-400 bg-gray-700/50 p-3 rounded-lg">
        {icon}
      </div>
      <div>
        <p className="text-sm text-gray-400">{label}</p>
        <p className="text-xl font-bold font-orbitron text-white">{value}</p>
      </div>
    </div>
  );
};

export default DataCard;

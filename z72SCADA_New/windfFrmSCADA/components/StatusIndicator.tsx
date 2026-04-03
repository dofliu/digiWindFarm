
import React from 'react';
import { TurbineStatus } from '../types';

interface StatusIndicatorProps {
  status: TurbineStatus;
  large?: boolean;
}

const StatusIndicator: React.FC<StatusIndicatorProps> = ({ status, large = false }) => {
  const getStatusClasses = (s: TurbineStatus) => {
    switch (s) {
      case TurbineStatus.OPERATING:
        return {
          dot: 'bg-green-500',
          text: 'text-green-400',
        };
      case TurbineStatus.IDLE:
        return {
          dot: 'bg-yellow-500',
          text: 'text-yellow-400',
        };
      case TurbineStatus.FAULT:
        return {
          dot: 'bg-red-500 animate-pulse',
          text: 'text-red-400',
        };
      case TurbineStatus.OFFLINE:
        return {
          dot: 'bg-gray-500',
          text: 'text-gray-500',
        };
    }
  };

  const classes = getStatusClasses(status);
  const sizeClass = large ? 'h-4 w-4' : 'h-3 w-3';
  const textSizeClass = large ? 'text-lg' : 'text-sm';

  return (
    <div className="flex items-center space-x-2">
      <div className={`rounded-full ${sizeClass} ${classes.dot}`}></div>
      <span className={`font-semibold ${textSizeClass} ${classes.text}`}>{status}</span>
    </div>
  );
};

export default StatusIndicator;

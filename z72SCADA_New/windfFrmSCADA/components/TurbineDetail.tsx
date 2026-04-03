import React, { useState, useCallback, useEffect } from 'react';
import { type TurbineData, TurbineStatus, type WorkOrder, WorkOrderStatus, TechnicianStatus } from '../types';
import StatusIndicator from './StatusIndicator';
import Gauge from './Gauge';
import MiniTrendChart from './MiniTrendChart';
import DataCard from './DataCard';
import { analyzeTurbineFault } from '../services/geminiService';
import { BackIcon, BrainIcon, BoltIcon, WindIcon, TempIcon, VibrationIcon, AngleIcon, SpeedIcon, WrenchScrewdriverIcon } from './icons';

interface TurbineDetailProps {
  turbine: TurbineData;
  onBack: () => void;
  onDispatch: (turbine: TurbineData, faultAnalysis: string) => void;
  activeWorkOrder?: WorkOrder;
}

const TurbineDetail: React.FC<TurbineDetailProps> = ({ turbine, onBack, onDispatch, activeWorkOrder }) => {
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [analysisResult, setAnalysisResult] = useState<string | null>(null);
    const [analysisError, setAnalysisError] = useState<string | null>(null);
    
    // Auto-run analysis when viewing a faulted turbine if no analysis has been run yet.
    useEffect(() => {
        if(turbine.status === TurbineStatus.FAULT && !analysisResult && !isAnalyzing) {
            handleAnalyzeFault();
        }
    }, [turbine.status, analysisResult, isAnalyzing]);


    const handleAnalyzeFault = useCallback(async () => {
        setIsAnalyzing(true);
        setAnalysisResult(null);
        setAnalysisError(null);
        try {
            const result = await analyzeTurbineFault(turbine);
            setAnalysisResult(result);
        } catch (error) {
            setAnalysisError('Failed to get analysis. Please try again.');
        } finally {
            setIsAnalyzing(false);
        }
    }, [turbine]);

    const formattedAnalysis = analysisResult?.split('\n').map((line, index) => {
        if (line.startsWith('**') || line.includes('Cause:') || line.includes('Actions:')) {
            return <p key={index} className="font-bold mt-2">{line.replace(/\*\*/g, '')}</p>;
        }
        if (line.match(/^\d+\./)) {
            return <p key={index} className="ml-4">{line}</p>;
        }
        return <p key={index}>{line}</p>;
    });

  return (
    <div>
        <button onClick={onBack} className="flex items-center space-x-2 text-cyan-400 hover:text-cyan-300 mb-6 transition-colors">
            <BackIcon />
            <span>Back to Farm Overview</span>
        </button>

      <div className="bg-gray-800/50 rounded-lg p-6 mb-6">
        <div className="flex flex-col sm:flex-row justify-between sm:items-center">
            <h2 className="text-4xl font-bold font-orbitron text-white">{turbine.name}</h2>
            <div className="mt-2 sm:mt-0"><StatusIndicator status={turbine.status} large /></div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Gauges */}
        <Gauge value={turbine.powerOutput} maxValue={5} label="Power Output" unit="MW" />
        <Gauge value={turbine.rotorSpeed} maxValue={25} label="Rotor Speed" unit="RPM" />
        <Gauge value={turbine.windSpeed} maxValue={25} label="Wind Speed" unit="m/s" />

        {/* Trend Chart */}
        <div className="md:col-span-2 lg:col-span-1 bg-gray-800/50 p-4 rounded-lg flex flex-col justify-center">
           <h3 className="text-gray-400 text-sm mb-2 text-center">Power Trend (Last Minute)</h3>
           <MiniTrendChart data={turbine.history} />
        </div>

        {/* Data Cards */}
        <DataCard icon={<BoltIcon />} label="Voltage / Current" value={`${turbine.voltage.toFixed(0)} V / ${turbine.current.toFixed(0)} A`} />
        <DataCard icon={<TempIcon />} label="Nacelle Temperature" value={`${turbine.temperature.toFixed(1)} °C`} />
        <DataCard icon={<VibrationIcon />} label="Vibration" value={`${turbine.vibration.toFixed(2)} mm/s`} />
        <DataCard icon={<AngleIcon />} label="Blade Angle" value={`${turbine.bladeAngle.toFixed(1)} °`} />
      </div>

      {turbine.status === TurbineStatus.FAULT && (
         <div className="mt-6 bg-red-900/30 border border-red-500/50 rounded-lg p-6">
            <div className="flex flex-col md:flex-row md:items-start justify-between">
                <div>
                    <h3 className="text-xl font-bold text-red-300">AI Fault Diagnosis</h3>
                    <p className="text-red-400 mt-1">Experimental AI analysis to help diagnose the issue.</p>
                </div>
                <div className="flex space-x-2 mt-4 md:mt-0">
                    <button 
                        onClick={handleAnalyzeFault} 
                        disabled={isAnalyzing}
                        className="flex items-center justify-center space-x-2 bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded-lg transition-all disabled:bg-gray-800 disabled:cursor-not-allowed"
                    >
                        <BrainIcon />
                        <span>{isAnalyzing ? 'Analyzing...' : 'Re-Analyze'}</span>
                    </button>

                    {activeWorkOrder ? (
                        <div className="text-center py-2 px-4 rounded-lg bg-yellow-500/20 text-yellow-300 border border-yellow-500/50">
                            <p className="font-bold">Work Order #{activeWorkOrder.id.slice(-4)} In Progress</p>
                        </div>
                    ) : (
                        <button 
                            onClick={() => onDispatch(turbine, analysisResult || "Awaiting analysis...")} 
                            disabled={isAnalyzing || !analysisResult}
                            className="flex items-center justify-center space-x-2 bg-yellow-500 hover:bg-yellow-600 text-white font-bold py-2 px-4 rounded-lg transition-all disabled:bg-yellow-800 disabled:cursor-not-allowed w-full md:w-auto"
                        >
                            <WrenchScrewdriverIcon />
                            <span>Dispatch Technician</span>
                        </button>
                    )}
                </div>
            </div>
            {isAnalyzing && <div className="mt-4 text-center text-red-300 animate-pulse">Contacting maintenance AI, please wait...</div>}
            {analysisError && <div className="mt-4 text-center font-bold text-red-200 bg-red-500/30 p-3 rounded">{analysisError}</div>}
            {analysisResult && (
                <div className="mt-4 bg-gray-900/50 p-4 rounded-md text-gray-300 font-mono text-sm leading-relaxed">
                    {formattedAnalysis}
                </div>
            )}
        </div>
      )}
    </div>
  );
};

export default TurbineDetail;

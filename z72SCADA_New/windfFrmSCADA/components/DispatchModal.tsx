import React, { useState } from 'react';
import { type TurbineData, type Technician, TechnicianStatus } from '../types';
import { XMarkIcon, WrenchScrewdriverIcon } from './icons';

interface DispatchModalProps {
    turbine: TurbineData;
    technicians: Technician[];
    faultAnalysis: string;
    onClose: () => void;
    onConfirm: (turbineId: number, technicianId: number, faultDescription: string) => void;
}

const DispatchModal: React.FC<DispatchModalProps> = ({ turbine, technicians, faultAnalysis, onClose, onConfirm }) => {
    const [selectedTechnicianId, setSelectedTechnicianId] = useState<number | null>(null);
    const availableTechnicians = technicians.filter(t => t.status === TechnicianStatus.ON_DUTY);

    const handleConfirm = () => {
        if (selectedTechnicianId) {
            onConfirm(turbine.id, selectedTechnicianId, faultAnalysis);
        }
    };

    return (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
            <div className="bg-gray-800 rounded-lg shadow-xl w-full max-w-2xl border border-gray-700">
                <div className="flex justify-between items-center p-4 border-b border-gray-700">
                    <h2 className="text-2xl font-bold font-orbitron text-white">Dispatch Technician</h2>
                    <button onClick={onClose} className="text-gray-400 hover:text-white">
                        <XMarkIcon className="w-6 h-6" />
                    </button>
                </div>
                
                <div className="p-6 space-y-6">
                    <div>
                        <h3 className="text-lg font-bold text-cyan-400">Target Turbine: {turbine.name}</h3>
                        <p className="text-sm text-gray-400">Current Status: <span className="text-red-400 font-semibold">{turbine.status}</span></p>
                    </div>

                    <div className="bg-gray-900/50 p-3 rounded-md">
                        <h4 className="font-semibold text-gray-300">AI Fault Analysis Summary:</h4>
                        <p className="text-sm text-gray-400 mt-2 font-mono whitespace-pre-wrap">{faultAnalysis}</p>
                    </div>

                    <div>
                        <h4 className="font-semibold text-gray-300 mb-2">Select Available Technician:</h4>
                        {availableTechnicians.length > 0 ? (
                             <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                                {availableTechnicians.map(tech => (
                                    <button
                                        key={tech.id}
                                        onClick={() => setSelectedTechnicianId(tech.id)}
                                        className={`p-3 rounded-md text-left transition-colors border-2 ${selectedTechnicianId === tech.id ? 'bg-cyan-500/30 border-cyan-500' : 'bg-gray-700/50 border-transparent hover:bg-gray-700'}`}
                                    >
                                        <p className="font-bold text-white">{tech.name}</p>
                                        <p className="text-xs text-green-400">{tech.status}</p>
                                    </button>
                                ))}
                            </div>
                        ) : (
                            <p className="text-yellow-400 bg-yellow-900/50 p-3 rounded-md">No technicians are currently available (On Duty).</p>
                        )}
                    </div>
                </div>

                <div className="p-4 bg-gray-800/50 border-t border-gray-700 flex justify-end">
                     <button
                        onClick={handleConfirm}
                        disabled={!selectedTechnicianId}
                        className="flex items-center justify-center space-x-2 bg-cyan-600 hover:bg-cyan-700 text-white font-bold py-2 px-6 rounded-lg transition-all disabled:bg-gray-600 disabled:cursor-not-allowed"
                    >
                        <WrenchScrewdriverIcon />
                        <span>Confirm Dispatch</span>
                    </button>
                </div>
            </div>
        </div>
    );
};

export default DispatchModal;

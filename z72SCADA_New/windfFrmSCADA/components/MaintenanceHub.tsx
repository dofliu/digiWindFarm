
import React, { useState } from 'react';
import { type useMockMaintenanceData } from '../hooks/useMockMaintenanceData';
import { type WorkOrder, WorkOrderStatus, TechnicianStatus, type Technician } from '../types';
import { WrenchScrewdriverIcon, UserGroupIcon, ClipboardDocumentListIcon } from './icons';

type MaintenanceData = ReturnType<typeof useMockMaintenanceData>;

interface MaintenanceHubProps {
  maintenanceData: MaintenanceData;
  onSelectWorkOrder: (workOrder: WorkOrder) => void;
}

// FIX: Moved TabButton component outside of the MaintenanceHub component to avoid re-creation on render and fix typing errors.
const TabButton = ({ isActive, onClick, children, count }: {isActive: boolean, onClick:()=>void, children: React.ReactNode, count: number}) => (
    <button onClick={onClick} className={`flex items-center space-x-2 px-4 py-2 text-sm font-medium rounded-t-lg border-b-2 transition-colors ${
        isActive ? 'border-cyan-400 text-cyan-300' : 'border-transparent text-gray-400 hover:text-white'
    }`}>
        {children}
        <span className={`px-2 py-0.5 rounded-full text-xs ${isActive ? 'bg-cyan-400/20 text-cyan-200' : 'bg-gray-700 text-gray-300'}`}>{count}</span>
    </button>
);

const MaintenanceHub: React.FC<MaintenanceHubProps> = ({ maintenanceData, onSelectWorkOrder }) => {
    const [activeTab, setActiveTab] = useState<'workOrders' | 'technicians'>('workOrders');
    const { technicians, workOrders, toggleTechnicianStatus } = maintenanceData;

    const getWorkOrderStatusClasses = (status: WorkOrderStatus) => {
        switch (status) {
            case WorkOrderStatus.IN_PROGRESS: return 'bg-yellow-500/20 text-yellow-300';
            case WorkOrderStatus.COMPLETED: return 'bg-green-500/20 text-green-400';
            default: return 'bg-gray-500/20 text-gray-300';
        }
    };

    const getTechnicianStatusClasses = (status: TechnicianStatus) => {
        switch (status) {
            case TechnicianStatus.ON_DUTY: return 'bg-green-500/20 text-green-400';
            case TechnicianStatus.OFF_DUTY: return 'bg-gray-500/20 text-gray-400';
            case TechnicianStatus.DISPATCHED: return 'bg-cyan-500/20 text-cyan-300 animate-pulse';
        }
    };


    return (
        <div>
            <div className="flex items-center justify-between mb-6">
                <h2 className="text-3xl font-bold font-orbitron text-white">Maintenance Hub</h2>
            </div>
            
            <div className="border-b border-gray-700">
                <nav className="-mb-px flex space-x-4">
                    <TabButton isActive={activeTab === 'workOrders'} onClick={() => setActiveTab('workOrders')} count={workOrders.length}>
                        <ClipboardDocumentListIcon className='w-5 h-5'/>
                        <span>Work Orders</span>
                    </TabButton>
                    <TabButton isActive={activeTab === 'technicians'} onClick={() => setActiveTab('technicians')} count={technicians.length}>
                        <UserGroupIcon className='w-5 h-5'/>
                        <span>Technician Roster</span>
                    </TabButton>
                </nav>
            </div>

            <div className="mt-6">
                {activeTab === 'workOrders' && (
                    <div className="bg-gray-800/50 rounded-lg p-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {workOrders.map(wo => (
                                <div key={wo.id} onClick={() => onSelectWorkOrder(wo)} className="bg-gray-800 rounded-lg p-4 border border-gray-700 hover:border-cyan-500 cursor-pointer transition-colors">
                                    <div className="flex justify-between items-start">
                                        <div>
                                            <p className="text-sm text-gray-400">Work Order</p>
                                            <p className="font-bold text-white font-mono">#{wo.id.slice(-6)}</p>
                                        </div>
                                        <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getWorkOrderStatusClasses(wo.status)}`}>{wo.status}</span>
                                    </div>
                                    <div className="mt-4">
                                        <p className="text-sm text-gray-400">Turbine</p>
                                        <p className="font-semibold text-white">{wo.turbineName}</p>
                                    </div>
                                    <div className="mt-2">
                                        <p className="text-sm text-gray-400">Assigned To</p>
                                        <p className="font-semibold text-white">{technicians.find(t=>t.id === wo.technicianId)?.name || 'Unassigned'}</p>
                                    </div>
                                    <div className="mt-2 text-xs text-gray-500">
                                        Created: {new Date(wo.createdAt).toLocaleString()}
                                    </div>
                                </div>
                            ))}
                        </div>
                         {workOrders.length === 0 && <p className='text-center text-gray-500 py-8'>No work orders found.</p>}
                    </div>
                )}
                {activeTab === 'technicians' && (
                     <div className="bg-gray-800/50 rounded-lg p-4">
                        <div className="overflow-x-auto">
                            <table className="min-w-full">
                                <thead>
                                    <tr>
                                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Name</th>
                                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Status</th>
                                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Action</th>
                                    </tr>
                                </thead>
                                <tbody className="bg-gray-800">
                                    {technicians.map(tech => (
                                        <tr key={tech.id} className="border-b border-gray-700">
                                            <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-white">{tech.name}</td>
                                            <td className="px-4 py-3 whitespace-nowrap text-sm">
                                                <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getTechnicianStatusClasses(tech.status)}`}>{tech.status}</span>
                                            </td>
                                            <td className="px-4 py-3 whitespace-nowrap text-sm">
                                                 <button
                                                    onClick={() => toggleTechnicianStatus(tech.id)}
                                                    disabled={tech.status === TechnicianStatus.DISPATCHED}
                                                    className={`px-3 py-1 text-xs rounded-md font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
                                                        tech.status === TechnicianStatus.ON_DUTY
                                                        ? 'bg-red-600/50 hover:bg-red-500/50 text-red-300'
                                                        : 'bg-green-600/50 hover:bg-green-500/50 text-green-300'
                                                    }`}
                                                >
                                                   {tech.status === TechnicianStatus.ON_DUTY ? 'Clock Out' : 'Clock In'}
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default MaintenanceHub;

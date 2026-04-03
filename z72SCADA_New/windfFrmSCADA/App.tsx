import React, { useState, useCallback, useMemo } from 'react';
import { useMockTurbineData } from './hooks/useMockTurbineData';
import { useMockMaintenanceData } from './hooks/useMockMaintenanceData';
import { type TurbineData, TurbineStatus, type WorkOrder, type Technician, WorkOrderStatus } from './types';
import FarmOverview from './components/FarmOverview';
import TurbineDetail from './components/TurbineDetail';
import MaintenanceHub from './components/MaintenanceHub';
import { HeaderIcon, WrenchScrewdriverIcon, ChartBarIcon, CogIcon } from './components/icons';
import DispatchModal from './components/DispatchModal';
import WorkOrderDetailModal from './components/WorkOrderDetailModal';
import SettingsPage from './components/SettingsPage';
import { useSettings } from './hooks/useSettings';

const NavButton = ({ isActive, onClick, children }: {isActive: boolean, onClick: ()=>void, children: React.ReactNode}) => (
    <button 
        onClick={onClick}
        className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
            isActive 
            ? 'bg-cyan-500/20 text-cyan-300' 
            : 'text-gray-300 hover:bg-gray-700 hover:text-white'
        }`}
    >
        {children}
    </button>
);

const App: React.FC = () => {
  const { turbines, updateTurbineStatus } = useMockTurbineData();
  const maintenance = useMockMaintenanceData();
  const { workOrders } = maintenance;
  const { settings, saveSettings } = useSettings();

  const [selectedTurbine, setSelectedTurbine] = useState<TurbineData | null>(null);
  const [view, setView] = useState<'dashboard' | 'maintenance' | 'settings'>('dashboard');

  const [isDispatchModalOpen, setIsDispatchModalOpen] = useState(false);
  const [turbineToDispatch, setTurbineToDispatch] = useState<TurbineData | null>(null);
  const [faultAnalysisForDispatch, setFaultAnalysisForDispatch] = useState('');

  const [selectedWorkOrder, setSelectedWorkOrder] = useState<WorkOrder | null>(null);


  const handleSelectTurbine = useCallback((turbine: TurbineData) => {
    setSelectedTurbine(turbine);
  }, []);

  const handleBackToOverview = useCallback(() => {
    setSelectedTurbine(null);
  }, []);

  const handleOpenDispatchModal = useCallback((turbine: TurbineData, faultAnalysis: string) => {
    setTurbineToDispatch(turbine);
    setFaultAnalysisForDispatch(faultAnalysis);
    setIsDispatchModalOpen(true);
  }, []);

  const handleCloseDispatchModal = useCallback(() => {
    setIsDispatchModalOpen(false);
    setTurbineToDispatch(null);
    setFaultAnalysisForDispatch('');
  }, []);
  
  const handleConfirmDispatch = useCallback((turbineId: number, technicianId: number, faultDescription: string) => {
    maintenance.createWorkOrder(turbineId, turbines.find(t=>t.id === turbineId)?.name || '', faultDescription, technicianId);
    handleCloseDispatchModal();
  }, [maintenance, turbines, handleCloseDispatchModal]);

  const handleCompleteWorkOrder = useCallback((workOrder: WorkOrder) => {
    maintenance.updateWorkOrder(workOrder.id, {
      status: WorkOrderStatus.COMPLETED,
      notes: workOrder.notes,
      photos: workOrder.photos,
    });
    updateTurbineStatus(workOrder.turbineId, TurbineStatus.IDLE);
    setSelectedWorkOrder(null);
  },[maintenance, updateTurbineStatus]);


  const activeWorkOrders = useMemo(() => workOrders.filter(wo => wo.status !== WorkOrderStatus.COMPLETED), [workOrders]);
  
  const farmStatus = turbines.some(t => t.status === TurbineStatus.FAULT) 
    ? TurbineStatus.FAULT 
    : turbines.every(t => t.status === TurbineStatus.OPERATING)
    ? TurbineStatus.OPERATING
    : TurbineStatus.IDLE;

  const totalPower = turbines.reduce((sum, turbine) => sum + turbine.powerOutput, 0);

  const getStatusColorClass = (status: TurbineStatus) => {
    switch (status) {
      case TurbineStatus.OPERATING: return 'text-green-400';
      case TurbineStatus.IDLE: return 'text-yellow-400';
      case TurbineStatus.FAULT: return 'text-red-500';
      case TurbineStatus.OFFLINE: return 'text-gray-500';
    }
  };
  
  const renderContent = () => {
    switch (view) {
        case 'dashboard':
            return selectedTurbine ? (
              <TurbineDetail 
                turbine={selectedTurbine} 
                onBack={handleBackToOverview}
                onDispatch={handleOpenDispatchModal}
                activeWorkOrder={activeWorkOrders.find(wo => wo.turbineId === selectedTurbine.id)}
              />
            ) : (
              <FarmOverview turbines={turbines} onSelectTurbine={handleSelectTurbine} settings={settings} />
            );
        case 'maintenance':
            return <MaintenanceHub 
                maintenanceData={maintenance}
                onSelectWorkOrder={(wo) => setSelectedWorkOrder(wo)}
            />;
        case 'settings':
            return <SettingsPage settings={settings} onSave={saveSettings} />;
        default:
            return null;
    }
  };

  return (
    <div className="bg-gray-900 text-gray-200 min-h-screen">
      <header className="bg-gray-800/50 backdrop-blur-sm border-b border-gray-700 p-4 flex justify-between items-center sticky top-0 z-50">
        <div className="flex items-center space-x-3">
          <HeaderIcon />
          <h1 className="text-xl md:text-2xl font-bold font-orbitron text-white">Wind Farm SCADA</h1>
        </div>
        <div className='flex items-center space-x-2'>
            <NavButton isActive={view === 'dashboard'} onClick={() => setView('dashboard')}>
                <ChartBarIcon />
                <span>Dashboard</span>
            </NavButton>
            <NavButton isActive={view === 'maintenance'} onClick={() => setView('maintenance')}>
                <WrenchScrewdriverIcon />
                <span>Maintenance Hub</span>
            </NavButton>
        </div>
        <div className="flex items-center space-x-4">
            <div className="hidden md:flex items-center space-x-6 text-sm">
              <div>
                <span className="text-gray-400">Total Power: </span>
                <span className="font-bold font-orbitron text-white">{totalPower.toFixed(2)} MW</span>
              </div>
              <div>
                <span className="text-gray-400">Farm Status: </span>
                <span className={`font-bold ${getStatusColorClass(farmStatus)}`}>{farmStatus}</span>
              </div>
            </div>
             <button onClick={() => setView('settings')} title="Settings" className={`p-2 rounded-md transition-colors ${view === 'settings' ? 'bg-cyan-500/20 text-cyan-300' : 'text-gray-300 hover:bg-gray-700 hover:text-white'}`}>
                <CogIcon />
            </button>
        </div>
      </header>
      <main className="p-4 sm:p-6 lg:p-8">
        {renderContent()}
      </main>
       <footer className="text-center p-4 text-xs text-gray-500 border-t border-gray-800">
        Wind Farm SCADA System &copy; 2024. For demonstration purposes only.
      </footer>

      {isDispatchModalOpen && turbineToDispatch && (
        <DispatchModal
            turbine={turbineToDispatch}
            technicians={maintenance.technicians}
            faultAnalysis={faultAnalysisForDispatch}
            onClose={handleCloseDispatchModal}
            onConfirm={handleConfirmDispatch}
        />
      )}

      {selectedWorkOrder && (
        <WorkOrderDetailModal
            workOrder={selectedWorkOrder}
            technicians={maintenance.technicians}
            onClose={() => setSelectedWorkOrder(null)}
            onUpdate={maintenance.updateWorkOrder}
            onComplete={handleCompleteWorkOrder}
        />
      )}
    </div>
  );
};

export default App;

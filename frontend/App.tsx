import React, { useState, useCallback, useMemo } from 'react';
import { useMockTurbineData } from './hooks/useMockTurbineData';
import { useRealtimeData } from './hooks/useRealtimeData';
import { useMockMaintenanceData } from './hooks/useMockMaintenanceData';
import { useI18n } from './hooks/useI18n';
import { type TurbineData, TurbineStatus, DataSourceType, type WorkOrder, type Technician, WorkOrderStatus } from './types';
import FarmOverview from './components/FarmOverview';
import TurbineDetail from './components/TurbineDetail';
import MaintenanceHub from './components/MaintenanceHub';
import FaultInjectionPanel from './components/FaultInjectionPanel';
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
  const { settings, saveSettings } = useSettings();
  const { lang, setLang, ui } = useI18n();

  // Use mock data for MOCK mode, real API data for SIMULATION / OPC_DA
  const mockData = useMockTurbineData();
  const realtimeData = useRealtimeData();

  const useMock = settings.dataSource === DataSourceType.MOCK;
  const { turbines, updateTurbineStatus } = useMock ? mockData : realtimeData;
  const maintenance = useMockMaintenanceData();
  const { workOrders } = maintenance;

  const [selectedTurbine, setSelectedTurbine] = useState<TurbineData | null>(null);
  const [view, setView] = useState<'dashboard' | 'maintenance' | 'faults' | 'settings'>('dashboard');

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

  const faultCount = turbines.filter(t => t.status === TurbineStatus.FAULT).length;
  const farmStatus = faultCount > 0
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
                lang={lang}
              />
            ) : (
              <FarmOverview turbines={turbines} onSelectTurbine={handleSelectTurbine} settings={settings} lang={lang} />
            );
        case 'maintenance':
            return <MaintenanceHub
                maintenanceData={maintenance}
                onSelectWorkOrder={(wo) => setSelectedWorkOrder(wo)}
            />;
        case 'faults':
            return <FaultInjectionPanel lang={lang} />;
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
        <div className='flex items-center space-x-1'>
            <NavButton isActive={view === 'dashboard'} onClick={() => { setView('dashboard'); setSelectedTurbine(null); }}>
                <ChartBarIcon />
                <span className="hidden sm:inline">{ui('Dashboard', '儀表板')}</span>
            </NavButton>
            <NavButton isActive={view === 'maintenance'} onClick={() => setView('maintenance')}>
                <WrenchScrewdriverIcon />
                <span className="hidden sm:inline">{ui('Maintenance', '維護中心')}</span>
            </NavButton>
            <NavButton isActive={view === 'faults'} onClick={() => setView('faults')}>
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
                </svg>
                <span className="hidden sm:inline">{ui('Faults', '故障模擬')}</span>
                {faultCount > 0 && (
                  <span className="ml-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">{faultCount}</span>
                )}
            </NavButton>
        </div>
        <div className="flex items-center space-x-3">
            <div className="hidden md:flex items-center space-x-6 text-sm">
              <div>
                <span className="text-gray-400">{ui('Total Power', '總功率')}: </span>
                <span className="font-bold font-orbitron text-white">{totalPower.toFixed(2)} MW</span>
              </div>
              <div>
                <span className="text-gray-400">{ui('Status', '狀態')}: </span>
                <span className={`font-bold ${getStatusColorClass(farmStatus)}`}>{farmStatus}</span>
              </div>
            </div>
            {/* Language toggle */}
            <button onClick={() => setLang(lang === 'zh' ? 'en' : 'zh')}
              className="text-xs px-2 py-1 rounded border border-gray-600 text-gray-400 hover:text-white hover:border-gray-400 transition-colors"
              title="Toggle language">
              {lang === 'zh' ? 'EN' : '中文'}
            </button>
             <button onClick={() => setView('settings')} title="Settings" className={`p-2 rounded-md transition-colors ${view === 'settings' ? 'bg-cyan-500/20 text-cyan-300' : 'text-gray-300 hover:bg-gray-700 hover:text-white'}`}>
                <CogIcon />
            </button>
        </div>
      </header>
      <main className="p-4 sm:p-6 lg:p-8">
        {renderContent()}
      </main>
       <footer className="text-center p-4 text-xs text-gray-500 border-t border-gray-800">
        Wind Farm SCADA System &copy; 2024. {ui('For demonstration purposes only.', '僅供展示使用。')}
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

import { useState, useCallback } from 'react';
import { 
    type Technician, 
    TechnicianStatus, 
    type WorkOrder, 
    WorkOrderStatus 
} from '../types';

const initialTechnicians: Technician[] = [
    { id: 1, name: 'Alice Johnson', status: TechnicianStatus.ON_DUTY },
    { id: 2, name: 'Bob Williams', status: TechnicianStatus.ON_DUTY },
    { id: 3, name: 'Charlie Brown', status: TechnicianStatus.OFF_DUTY },
    { id: 4, name: 'Diana Miller', status: TechnicianStatus.ON_DUTY },
];

export const useMockMaintenanceData = () => {
    const [technicians, setTechnicians] = useState<Technician[]>(initialTechnicians);
    const [workOrders, setWorkOrders] = useState<WorkOrder[]>([]);

    const toggleTechnicianStatus = useCallback((technicianId: number) => {
        setTechnicians(prev => prev.map(tech => {
            if (tech.id === technicianId && tech.status !== TechnicianStatus.DISPATCHED) {
                return { ...tech, status: tech.status === TechnicianStatus.ON_DUTY ? TechnicianStatus.OFF_DUTY : TechnicianStatus.ON_DUTY };
            }
            return tech;
        }));
    }, []);

    const createWorkOrder = useCallback((turbineId: number, turbineName: string, faultDescription: string, technicianId: number) => {
        const newWorkOrder: WorkOrder = {
            id: `WO-${Date.now()}`,
            turbineId,
            turbineName,
            technicianId,
            status: WorkOrderStatus.IN_PROGRESS,
            createdAt: Date.now(),
            faultDescription,
            notes: '',
            photos: [],
        };
        setWorkOrders(prev => [newWorkOrder, ...prev]);
        setTechnicians(prev => prev.map(t => t.id === technicianId ? { ...t, status: TechnicianStatus.DISPATCHED } : t));
    }, []);

    const updateWorkOrder = useCallback((workOrderId: string, updates: Partial<Pick<WorkOrder, 'notes' | 'photos' | 'status'>>) => {
        setWorkOrders(prev => prev.map(wo => {
            if (wo.id === workOrderId) {
                const updatedWo = { ...wo, ...updates };
                // If work order is completed, free up the technician
                if (updates.status === WorkOrderStatus.COMPLETED && wo.technicianId) {
                     setTechnicians(prevTechs => prevTechs.map(t => t.id === wo.technicianId ? { ...t, status: TechnicianStatus.ON_DUTY } : t));
                }
                return updatedWo;
            }
            return wo;
        }));
    }, []);

    return {
        technicians,
        workOrders,
        toggleTechnicianStatus,
        createWorkOrder,
        updateWorkOrder,
    };
};

import { useState, useCallback, useEffect } from 'react';
import {
    type Technician,
    TechnicianStatus,
    type WorkOrder,
    WorkOrderStatus,
} from '../types';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

/** Map backend status string to TechnicianStatus enum */
function mapTechStatus(s: string): TechnicianStatus {
  if (s === 'ON_DUTY' || s === 'ON DUTY') return TechnicianStatus.ON_DUTY;
  if (s === 'OFF_DUTY' || s === 'OFF DUTY') return TechnicianStatus.OFF_DUTY;
  if (s === 'DISPATCHED') return TechnicianStatus.DISPATCHED;
  return TechnicianStatus.OFF_DUTY;
}

function mapWoStatus(s: string): WorkOrderStatus {
  if (s === 'IN_PROGRESS') return WorkOrderStatus.IN_PROGRESS;
  if (s === 'COMPLETED') return WorkOrderStatus.COMPLETED;
  return WorkOrderStatus.OPEN;
}

interface ApiWorkOrder {
  id: string;
  turbineId: number;
  turbineName: string;
  technicianId: number | null;
  status: string;
  createdAt: number;
  faultDescription: string;
  notes: string;
  photos: string[];
}

interface ApiTechnician {
  id: number;
  name: string;
  status: string;
}

function apiToWorkOrder(api: ApiWorkOrder): WorkOrder {
  return {
    id: api.id,
    turbineId: api.turbineId,
    turbineName: api.turbineName,
    technicianId: api.technicianId,
    status: mapWoStatus(api.status),
    createdAt: api.createdAt,
    faultDescription: api.faultDescription,
    notes: api.notes || '',
    photos: api.photos || [],
  };
}

function apiToTechnician(api: ApiTechnician): Technician {
  return {
    id: api.id,
    name: api.name,
    status: mapTechStatus(api.status),
  };
}

export const useMaintenanceData = () => {
  const [technicians, setTechnicians] = useState<Technician[]>([]);
  const [workOrders, setWorkOrders] = useState<WorkOrder[]>([]);

  // Fetch initial data
  const refresh = useCallback(async () => {
    try {
      const [techRes, woRes] = await Promise.all([
        fetch(`${API_BASE}/api/maintenance/technicians`),
        fetch(`${API_BASE}/api/maintenance/work-orders`),
      ]);
      if (techRes.ok) {
        const techData = await techRes.json();
        setTechnicians((techData.data || []).map(apiToTechnician));
      }
      if (woRes.ok) {
        const woData = await woRes.json();
        setWorkOrders((woData.data || []).map(apiToWorkOrder));
      }
    } catch (e) {
      console.warn('[useMaintenanceData] fetch failed:', e);
    }
  }, []);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 10000); // poll every 10s
    return () => clearInterval(interval);
  }, [refresh]);

  const toggleTechnicianStatus = useCallback(async (technicianId: number) => {
    const tech = technicians.find(t => t.id === technicianId);
    if (!tech || tech.status === TechnicianStatus.DISPATCHED) return;
    const newStatus = tech.status === TechnicianStatus.ON_DUTY ? 'OFF_DUTY' : 'ON_DUTY';
    try {
      const res = await fetch(`${API_BASE}/api/maintenance/technicians/${technicianId}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus }),
      });
      if (res.ok) {
        const updated = await res.json();
        setTechnicians(prev =>
          prev.map(t => t.id === technicianId ? apiToTechnician(updated) : t)
        );
      }
    } catch (e) {
      console.warn('[useMaintenanceData] toggle technician failed:', e);
    }
  }, [technicians]);

  const createWorkOrder = useCallback(async (
    turbineId: number, turbineName: string, faultDescription: string, technicianId: number
  ) => {
    try {
      const res = await fetch(`${API_BASE}/api/maintenance/work-orders`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ turbineId, turbineName, faultDescription, technicianId }),
      });
      if (res.ok) {
        const wo = await res.json();
        setWorkOrders(prev => [apiToWorkOrder(wo), ...prev]);
        // Refresh technicians to pick up DISPATCHED status
        const techRes = await fetch(`${API_BASE}/api/maintenance/technicians`);
        if (techRes.ok) {
          const techData = await techRes.json();
          setTechnicians((techData.data || []).map(apiToTechnician));
        }
      }
    } catch (e) {
      console.warn('[useMaintenanceData] create WO failed:', e);
    }
  }, []);

  const updateWorkOrder = useCallback(async (
    workOrderId: string, updates: Partial<Pick<WorkOrder, 'notes' | 'photos' | 'status'>>
  ) => {
    try {
      const body: Record<string, unknown> = {};
      if (updates.status !== undefined) body.status = updates.status;
      if (updates.notes !== undefined) body.notes = updates.notes;
      if (updates.photos !== undefined) body.photos = updates.photos;

      const res = await fetch(`${API_BASE}/api/maintenance/work-orders/${workOrderId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (res.ok) {
        const updated = await res.json();
        setWorkOrders(prev =>
          prev.map(wo => wo.id === workOrderId ? apiToWorkOrder(updated) : wo)
        );
        // Refresh technicians if completed (tech released)
        if (updates.status === WorkOrderStatus.COMPLETED) {
          const techRes = await fetch(`${API_BASE}/api/maintenance/technicians`);
          if (techRes.ok) {
            const techData = await techRes.json();
            setTechnicians((techData.data || []).map(apiToTechnician));
          }
        }
      }
    } catch (e) {
      console.warn('[useMaintenanceData] update WO failed:', e);
    }
  }, []);

  return {
    technicians,
    workOrders,
    toggleTechnicianStatus,
    createWorkOrder,
    updateWorkOrder,
  };
};

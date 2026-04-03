
import React, { useState } from 'react';
import { type WorkOrder, type Technician, WorkOrderStatus } from '../types';
import { XMarkIcon, CameraIcon } from './icons';

interface WorkOrderDetailModalProps {
    workOrder: WorkOrder;
    technicians: Technician[];
    onClose: () => void;
    onUpdate: (workOrderId: string, updates: Partial<Pick<WorkOrder, 'notes' | 'photos'>>) => void;
    onComplete: (workOrder: WorkOrder) => void;
}

const WorkOrderDetailModal: React.FC<WorkOrderDetailModalProps> = ({ workOrder, technicians, onClose, onUpdate, onComplete }) => {
    const [notes, setNotes] = useState(workOrder.notes);
    const [photos, setPhotos] = useState<string[]>(workOrder.photos);

    const getTechnicianName = (id: number | null) => {
        return technicians.find(t => t.id === id)?.name || 'N/A';
    };

    const handlePhotoUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
        if (event.target.files) {
            const files = Array.from(event.target.files);
            files.forEach(file => {
                const reader = new FileReader();
                reader.onloadend = () => {
                    // FIX: TypeScript was not correctly narrowing the type of `reader.result`
                    // inside the `setPhotos` callback. Assigning the result to a new const
                    // after the type check ensures the correct type is inferred.
                    if (typeof reader.result === 'string') {
                        const newPhoto = reader.result;
                        setPhotos(prev => [...prev, newPhoto]);
                    }
                };
                reader.readAsDataURL(file);
            });
        }
    };
    
    const removePhoto = (index: number) => {
        setPhotos(prev => prev.filter((_, i) => i !== index));
    };
    
    const handleUpdate = () => {
        onUpdate(workOrder.id, { notes, photos });
    };

    const handleComplete = () => {
        if (photos.length > 0) {
            onComplete({
                ...workOrder,
                notes,
                photos,
                status: WorkOrderStatus.COMPLETED
            });
        }
    };

    const isCompleted = workOrder.status === WorkOrderStatus.COMPLETED;

    return (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
            <div className="bg-gray-800 rounded-lg shadow-xl w-full max-w-4xl border border-gray-700 flex flex-col max-h-[90vh]">
                <div className="flex justify-between items-center p-4 border-b border-gray-700 flex-shrink-0">
                    <h2 className="text-2xl font-bold font-orbitron text-white">Work Order Details <span className="text-cyan-400">#{workOrder.id.slice(-6)}</span></h2>
                    <button onClick={onClose} className="text-gray-400 hover:text-white">
                        <XMarkIcon className="w-6 h-6" />
                    </button>
                </div>
                
                <div className="p-6 space-y-4 overflow-y-auto">
                    {/* Details Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                        <div className="bg-gray-900/50 p-3 rounded-md">
                            <p className="text-gray-400">Turbine</p>
                            <p className="font-bold text-white text-base">{workOrder.turbineName}</p>
                        </div>
                        <div className="bg-gray-900/50 p-3 rounded-md">
                            <p className="text-gray-400">Assigned Technician</p>
                            <p className="font-bold text-white text-base">{getTechnicianName(workOrder.technicianId)}</p>
                        </div>
                        <div className="bg-gray-900/50 p-3 rounded-md">
                            <p className="text-gray-400">Status</p>
                            <p className={`font-bold text-base ${workOrder.status === WorkOrderStatus.COMPLETED ? 'text-green-400' : 'text-yellow-400'}`}>{workOrder.status}</p>
                        </div>
                    </div>

                    {/* Fault Description */}
                    <div className="bg-gray-900/50 p-3 rounded-md">
                        <h4 className="font-semibold text-gray-300">AI Fault Analysis / Description:</h4>
                        <p className="text-sm text-gray-400 mt-2 font-mono whitespace-pre-wrap">{workOrder.faultDescription}</p>
                    </div>

                    {/* Maintenance Notes */}
                    <div>
                        <label htmlFor="notes" className="font-semibold text-gray-300 mb-2 block">Maintenance Notes</label>
                        <textarea
                            id="notes"
                            value={notes}
                            onChange={e => setNotes(e.target.value)}
                            rows={5}
                            className="w-full bg-gray-900/70 border border-gray-600 rounded-md p-2 text-gray-300 focus:ring-cyan-500 focus:border-cyan-500 transition"
                            placeholder="Add maintenance notes here..."
                            disabled={isCompleted}
                        />
                    </div>

                    {/* Photo Upload */}
                    <div>
                        <h4 className="font-semibold text-gray-300 mb-2">现场照片 (Site Photos)</h4>
                        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                            {photos.map((photo, index) => (
                                <div key={index} className="relative group">
                                    <img src={photo} alt={`Maintenance photo ${index + 1}`} className="rounded-md w-full h-32 object-cover" />
                                    {!isCompleted && (
                                        <button onClick={() => removePhoto(index)} className="absolute top-1 right-1 bg-red-600/80 text-white rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                            <XMarkIcon className="w-4 h-4" />
                                        </button>
                                    )}
                                </div>
                            ))}
                            {!isCompleted && (
                                <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-gray-600 border-dashed rounded-lg cursor-pointer bg-gray-700/50 hover:bg-gray-700 transition">
                                    <div className="flex flex-col items-center justify-center pt-5 pb-6">
                                        <CameraIcon className="w-8 h-8 text-gray-400" />
                                        <p className="mb-2 text-sm text-gray-400 text-center">Click to upload</p>
                                    </div>
                                    <input type="file" className="hidden" accept="image/*" multiple onChange={handlePhotoUpload} />
                                </label>
                            )}
                        </div>
                        {isCompleted && photos.length === 0 && <p className="text-gray-500 text-sm">No photos were uploaded for this work order.</p>}
                         <p className="text-xs text-gray-500 mt-2">Completion requires at least one photo to be uploaded.</p>
                    </div>
                </div>

                {!isCompleted && (
                    <div className="p-4 bg-gray-800/50 border-t border-gray-700 flex justify-end space-x-3 flex-shrink-0">
                        <button
                            onClick={handleUpdate}
                            className="bg-gray-600 hover:bg-gray-500 text-white font-bold py-2 px-4 rounded-lg transition-colors"
                        >
                            Update Notes/Photos
                        </button>
                         <button
                            onClick={handleComplete}
                            disabled={photos.length === 0}
                            className="flex items-center justify-center space-x-2 bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-6 rounded-lg transition-all disabled:bg-gray-600/50 disabled:text-gray-400 disabled:cursor-not-allowed"
                        >
                            <span>Complete Work Order</span>
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};

export default WorkOrderDetailModal;

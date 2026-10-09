import React from 'react';
import { InventoryManager } from '../features/inventory/InventoryManager';

export const InventoryPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <div>
          <h1 className="text-xl font-bold text-slate-100 tracking-tight">AI Provider & Endpoint Inventory</h1>
          <p className="text-xs text-slate-400">Catalog of identified AI vendors, models, and endpoints.</p>
        </div>
      </div>
      <InventoryManager />
    </div>
  );
};

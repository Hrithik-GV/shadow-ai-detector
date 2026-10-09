import React from 'react';
import { RiskAssessment } from '../features/risk/RiskAssessment';

export const RiskPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <div>
          <h1 className="text-xl font-bold text-slate-100 tracking-tight">Risk Classifications</h1>
          <p className="text-xs text-slate-400">Security risk evaluation and policy violations for AI usage.</p>
        </div>
      </div>
      <RiskAssessment />
    </div>
  );
};

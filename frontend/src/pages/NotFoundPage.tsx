import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldAlert, ArrowLeft } from 'lucide-react';

export const NotFoundPage: React.FC = () => {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <div className="p-3 bg-rose-500/10 text-rose-400 border border-rose-500/20 rounded-full mb-4">
        <ShieldAlert className="w-8 h-8" />
      </div>
      <h1 className="text-2xl font-bold text-slate-100">404 - Page Not Found</h1>
      <p className="mt-2 text-sm text-slate-400 max-w-md">
        The requested security console route does not exist.
      </p>
      <Link
        to="/"
        className="mt-6 inline-flex items-center space-x-2 text-xs font-semibold px-4 py-2 rounded-lg bg-indigo-600 text-white hover:bg-indigo-500 transition-colors"
      >
        <ArrowLeft className="w-3.5 h-3.5" />
        <span>Return to Overview</span>
      </Link>
    </div>
  );
};

import React from 'react';

export interface PageContainerProps {
  title: string;
  description?: string;
  badge?: React.ReactNode;
  actions?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export const PageContainer: React.FC<PageContainerProps> = ({
  title,
  description,
  badge,
  actions,
  children,
  className = '',
}) => {
  return (
    <div className={`space-y-6 max-w-7xl mx-auto ${className}`}>
      {/* Page Header */}
      <div className="border-b-2 border-[#333330] pb-5 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="font-mono text-xl sm:text-2xl font-bold uppercase tracking-wide text-[#F4F4F0]">
              {title}
            </h1>
            {badge && <div>{badge}</div>}
          </div>
          {description && (
            <p className="font-mono text-xs sm:text-sm text-[#9A9A91] mt-1.5 leading-relaxed max-w-3xl">
              {description}
            </p>
          )}
        </div>
        {actions && <div className="flex items-center gap-3 shrink-0">{actions}</div>}
      </div>

      {/* Main Content Area */}
      <div className="space-y-6">{children}</div>
    </div>
  );
};

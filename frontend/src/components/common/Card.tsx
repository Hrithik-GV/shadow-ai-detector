import React from 'react';

export interface CardProps {
  children: React.ReactNode;
  title?: React.ReactNode;
  subtitle?: React.ReactNode;
  action?: React.ReactNode;
  headerIcon?: React.ReactNode;
  className?: string;
  variant?: 'surface' | 'charcoal' | 'accent';
  hoverable?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  title,
  subtitle,
  action,
  headerIcon,
  className = '',
  variant = 'surface',
  hoverable = false,
}) => {
  const bgStyles = {
    surface: 'bg-[#171716] border-[#333330]',
    charcoal: 'bg-[#181818] border-[#333330]',
    accent: 'bg-[#181818] border-[#FFCC00]/50 shadow-[4px_4px_0_#735C00]',
  };

  const shadowStyle = variant === 'accent' ? '' : 'shadow-[4px_4px_0_#000000]';
  const hoverStyle = hoverable
    ? 'transition-all duration-150 hover:-translate-y-0.5 hover:border-[#FFCC00] hover:shadow-[5px_5px_0_#000000]'
    : '';

  return (
    <div
      className={`border ${bgStyles[variant]} ${shadowStyle} ${hoverStyle} p-5 sm:p-6 text-[#F4F4F0] ${className}`}
    >
      {(title || subtitle || action || headerIcon) && (
        <div className="flex items-start justify-between gap-4 pb-4 mb-4 border-b border-[#333330]">
          <div className="flex items-start gap-3">
            {headerIcon && <div className="mt-0.5 text-[#FFCC00] shrink-0">{headerIcon}</div>}
            <div>
              {title && (
                <h3 className="font-mono text-sm sm:text-base font-bold text-[#F4F4F0] tracking-wide">
                  {title}
                </h3>
              )}
              {subtitle && (
                <p className="font-mono text-xs text-[#9A9A91] mt-1 leading-relaxed">
                  {subtitle}
                </p>
              )}
            </div>
          </div>
          {action && <div className="shrink-0">{action}</div>}
        </div>
      )}
      {children}
    </div>
  );
};

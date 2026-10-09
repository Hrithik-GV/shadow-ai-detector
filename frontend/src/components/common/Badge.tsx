import React from 'react';

export interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'accent' | 'warning' | 'danger' | 'success' | 'muted';
  size?: 'sm' | 'md';
  icon?: React.ReactNode;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'default',
  size = 'md',
  icon,
  className = '',
}) => {
  const sizeStyles = {
    sm: 'text-[10px] px-1.5 py-0.5 gap-1',
    md: 'text-xs px-2.5 py-1 gap-1.5',
  };

  const variantStyles = {
    default: 'bg-[#181818] text-[#F4F4F0] border-[#333330]',
    accent: 'bg-[#FFCC00]/15 text-[#FFCC00] border-[#FFCC00]',
    warning: 'bg-[#FFCC00]/10 text-[#FFCC00] border-[#997A00]',
    danger: 'bg-[#FF4D4D]/10 text-[#FF6B6B] border-[#8C2323]',
    success: 'bg-[#00E575]/10 text-[#00E575] border-[#006633]',
    muted: 'bg-[#171716] text-[#9A9A91] border-[#2A2A2A]',
  };

  return (
    <span
      className={`inline-flex items-center font-mono font-medium tracking-wide border uppercase select-none ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
    >
      {icon && <span className="shrink-0">{icon}</span>}
      <span>{children}</span>
    </span>
  );
};

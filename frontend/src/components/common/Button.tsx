import React from 'react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  icon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  icon,
  className = '',
  disabled,
  ...props
}) => {
  const baseStyles =
    'inline-flex items-center justify-center font-mono font-medium tracking-wider uppercase transition-all duration-120 cursor-pointer disabled:cursor-not-allowed disabled:opacity-50 select-none focus:outline-none focus-visible:outline-2 focus-visible:outline-[#F4F4F0] focus-visible:outline-offset-2';

  const sizeStyles = {
    sm: 'text-xs px-2.5 py-1.5 gap-1.5 border',
    md: 'text-xs px-4 py-2 gap-2 border-2',
    lg: 'text-sm px-5 py-2.5 gap-2.5 border-2',
  };

  const variantStyles = {
    primary:
      'bg-[#FFCC00] hover:bg-[#FFDB4D] text-[#0D0D0D] border-[#FFCC00] shadow-[3px_3px_0_#735C00] active:translate-x-[2px] active:translate-y-[2px] active:shadow-[1px_1px_0_#735C00]',
    secondary:
      'bg-[#181818] hover:bg-[#222222] text-[#F4F4F0] border-[#333330] hover:border-[#FFCC00] shadow-[3px_3px_0_#000000] active:translate-x-[2px] active:translate-y-[2px] active:shadow-[1px_1px_0_#000000]',
    outline:
      'bg-transparent hover:bg-[#181818] text-[#F4F4F0] border-[#333330] hover:border-[#F4F4F0] shadow-[2px_2px_0_#000000] active:translate-x-[1px] active:translate-y-[1px] active:shadow-none',
    danger:
      'bg-[#2A1616] hover:bg-[#3D1E1E] text-[#FF6B6B] border-[#732626] shadow-[3px_3px_0_#000000] active:translate-x-[2px] active:translate-y-[2px] active:shadow-[1px_1px_0_#000000]',
  };

  return (
    <button
      className={`${baseStyles} ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
      disabled={disabled}
      {...props}
    >
      {icon && <span className="shrink-0">{icon}</span>}
      {children}
    </button>
  );
};

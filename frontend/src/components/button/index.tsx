import clsx from 'clsx';
import { ComponentProps } from 'react';

type ButtonProps = {
  children: React.ReactNode;
  variant?: 'contained' | 'outlined' | 'text';
  color?: 'primary' | 'danger' | 'success' | 'warning' | 'info';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
} & ComponentProps<'button'>;

export const Button = ({
  variant = 'contained',
  color = 'primary',
  size = 'md',
  children,
  className,
  ...props
}: ButtonProps) => {
  const variantClasses = {
    contained: '',
    outlined: 'border border-solid',
    text: 'bg-none border-none',
  };

  const colorClasses = {
    contained: {
      primary: 'bg-white/90 text-black/75 enabled:hover:bg-white enabled:hover:text-black/90',
      danger: 'bg-red-700 text-white enabled:hover:bg-red-400',
      success: 'bg-green-700 text-white enabled:hover:bg-green-400',
      warning: 'bg-amber-700 text-white enabled:hover:bg-amber-400',
      info: 'bg-indigo-700 text-white enabled:hover:bg-indigo-400',
    },
    outlined: {
      primary:
        'border-white/40 text-white/80 enabled:hover:border-white/80 enabled:hover:text-white',
      danger: 'border-red-700 text-red-700 enabled:hover:border-red-400 enabled:hover:text-red-400',
      success:
        'border-green-700 text-green-700 enabled:hover:border-green-400 enabled:hover:text-green-400',
      warning:
        'border-amber-700 text-amber-700 enabled:hover:border-amber-400 enabled:hover:text-amber-400',
      info: 'border-indigo-700 text-indigo-700 enabled:hover:border-indigo-400 enabled:hover:text-indigo-400',
    },
    text: {
      primary: 'text-white/80 enabled:hover:text-white enabled:hover:underline',
      danger: 'text-red-700/80 enabled:hover:text-red-400 enabled:hover:underline',
      success: 'text-green-700/80 enabled:hover:text-green-400 enabled:hover:underline',
      warning: 'text-amber-700/80 enabled:hover:text-amber-400 enabled:hover:underline',
      info: 'text-blue-700/80 enabled:hover:text-blue-400 enabled:hover:underline',
    },
  };

  const sizeClasses = {
    sm: 'h-8 px-2',
    md: 'h-10 px-4',
    lg: 'h-12 px-6',
  };
  return (
    <button
      className={clsx(
        props.disabled ? 'opacity-60 cursor-not-allowed' : 'cursor-pointer',
        'flex items-center justify-center gap-2 w-full sm:w-auto rounded-sm transition-colors font-medium sm:text-base',
        variantClasses[variant],
        colorClasses[variant][color],
        sizeClasses[size],
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
};

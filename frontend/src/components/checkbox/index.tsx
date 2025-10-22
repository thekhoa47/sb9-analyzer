import clsx from 'clsx';
import { forwardRef } from 'react';

type CheckboxProps = React.ComponentProps<'input'> & {
  label: string;
};

export const Checkbox = forwardRef<HTMLInputElement, CheckboxProps>(
  ({ id, label, className, ...inputProps }, ref) => {
    return (
      <label
        htmlFor={id}
        className={clsx(
          'inline-flex items-center gap-2 select-none ',
          inputProps.disabled ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'
        )}
      >
        <input
          ref={ref}
          id={id}
          type="checkbox"
          className={clsx(
            'h-4 w-4 rounded accent-amber-500',
            inputProps.disabled && 'pointer-events-none',
            className
          )}
          {...inputProps}
        />
        <span className="text-sm">{label}</span>
      </label>
    );
  }
);

Checkbox.displayName = 'Checkbox';

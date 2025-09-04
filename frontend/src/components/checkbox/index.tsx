import clsx from 'clsx';
import { forwardRef } from 'react';

type CheckboxProps = React.ComponentProps<'input'> & {
  label: string;
};

export const Checkbox = forwardRef<HTMLInputElement, CheckboxProps>(
  ({ id, label, className, ...inputProps }, ref) => {
    return (
      <label htmlFor={id} className="inline-flex items-center gap-2 cursor-pointer select-none">
        <input
          ref={ref}
          id={id}
          type="checkbox"
          className={clsx("h-4 w-4 rounded border-gray-400 text-blue-600 focus:ring-blue-500", className)}
          {...inputProps}
        />
        <span className="text-sm">{label}</span>
      </label>
    );
  }
);

Checkbox.displayName = 'Checkbox';

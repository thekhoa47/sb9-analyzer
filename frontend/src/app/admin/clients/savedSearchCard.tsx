import React, { useState } from 'react';
import { z } from 'zod';
import {
  useFieldArray,
  type Control,
  type UseFormRegister,
  type FieldErrors,
} from 'react-hook-form';
import { formSchema, savedSearchFieldSchema } from './formSchema';
import { Button } from '@/components/button';
import { FaTrash, FaX } from 'react-icons/fa6';

// ----------------- types from zod -----------------
type Schema = typeof formSchema;
type FormInput = z.input<Schema>;
type SavedSearchField = z.infer<typeof savedSearchFieldSchema>;

// ----------------- constants -----------------
const FIELD_OPTIONS = [
  { value: 'city', label: 'City', placeholder: 'e.g. San Francisco' },
  { value: 'zip', label: 'ZIP', placeholder: 'e.g. 94107' },
  {
    value: 'property_sub_type',
    label: 'Property Sub Type',
    placeholder: 'e.g. Single Family, Condo, Townhouse...',
  },
  { value: 'lot_size', label: 'Lot Size', placeholder: 'e.g. 10,000' },
  { value: 'living_area', label: 'Living Area', placeholder: 'e.g. 2,000' },
  { value: 'garage_spaces', label: 'Garage Spaces', placeholder: 'e.g. 3' },
] as const;

type SavedSearchCardProps = {
  index: number;
  control: Control<FormInput>; // note the ", any" to avoid resolver mismatch
  register: UseFormRegister<FormInput>;
  errors: FieldErrors<FormInput>;
  onRemove: () => void;
  canRemove: boolean;
};

export function SavedSearchCard({
  index,
  control,
  register,
  errors,
  onRemove,
  canRemove,
}: SavedSearchCardProps) {
  // name is a literal so TS can narrow
  const name = `saved_searches.${index}.fields` as const;

  const { fields, append, remove, update } = useFieldArray<FormInput, typeof name, 'id'>({
    control,
    name,
  });

  // local "add criterion" state
  const [selKey, setSelKey] = useState<(typeof FIELD_OPTIONS)[number]['value']>(
    FIELD_OPTIONS[0].value
  );
  const [val, setVal] = useState('');

  const addCriterion = () => {
    const trimmed = val.trim();
    if (!trimmed) return;

    const idx = fields.findIndex((f) => f.search_field === selKey);
    if (idx >= 0) {
      update(idx, { ...fields[idx], value: trimmed });
    } else {
      append({ search_field: selKey, value: trimmed });
    }
    setVal('');
  };

  return (
    <fieldset className="rounded-2xl border p-5 space-y-4 shadow-sm ">
      <legend className="px-2 font-semibold flex gap-x-2 items-baseline">
        Saved Search #{index + 1}
        <Button variant="text" size="sm" onClick={onRemove} disabled={!canRemove}>
          <FaTrash />
        </Button>
      </legend>

      <label className="flex flex-col gap-1 text-sm font-medium">
        Name
        <input
          {...register(`saved_searches.${index}.name`)}
          className="w-full rounded border px-3 py-2 outline-none focus:ring"
          placeholder='e.g. "2 bed in SF"'
        />
        {errors.saved_searches?.[index]?.name && (
          <span className="text-sm text-red-600">
            {errors.saved_searches[index]?.name?.message as string}
          </span>
        )}
      </label>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <label className="flex flex-col gap-1 text-sm font-medium">
          Beds (min)
          <input
            type="number"
            {...register(`saved_searches.${index}.beds_min`, { valueAsNumber: true })}
            className="w-full rounded border px-3 py-2 outline-none focus:ring"
          />
          {errors.saved_searches?.[index]?.beds_min && (
            <span className="text-sm text-red-600">
              {errors.saved_searches[index]?.beds_min?.message as string}
            </span>
          )}
        </label>

        <label className="flex flex-col gap-1 text-sm font-medium">
          Baths (min)
          <input
            type="number"
            {...register(`saved_searches.${index}.baths_min`, { valueAsNumber: true })}
            className="w-full rounded border px-3 py-2 outline-none focus:ring"
          />
          {errors.saved_searches?.[index]?.baths_min && (
            <span className="text-sm text-red-600">
              {errors.saved_searches[index]?.baths_min?.message as string}
            </span>
          )}
        </label>
      </div>

      <label className="flex flex-col gap-1 text-sm font-medium">
        Max price
        {/* Let Zod coerce; do NOT use valueAsNumber to avoid NaN on empty */}
        <input
          type="number"
          inputMode="numeric"
          {...register(`saved_searches.${index}.max_price`)}
          className="w-full rounded border px-3 py-2 outline-none focus:ring"
          placeholder="1,000,000"
        />
        {errors.saved_searches?.[index]?.max_price && (
          <span className="text-sm text-red-600">
            {errors.saved_searches[index]?.max_price?.message as string}
          </span>
        )}
      </label>

      <label className="flex flex-col gap-1 text-sm font-medium">
        Analysis note
        <textarea
          {...register(`saved_searches.${index}.analysis_note`)}
          className="w-full rounded border px-3 py-2 outline-none focus:ring"
          placeholder="Potential for ADU or perfect for SB9"
          rows={2}
        />
        {errors.saved_searches?.[index]?.analysis_note && (
          <span className="text-sm text-red-600">
            {errors.saved_searches[index]?.analysis_note?.message as string}
          </span>
        )}
      </label>

      {/* criteria editor */}
      <div className="space-y-2">
        <h4 className="text-sm font-semibold">Add criteria</h4>
        <div className="grid grid-cols-1 md:grid-cols-[200px_1fr_auto] gap-2">
          <select
            value={selKey}
            onChange={(e) => setSelKey(e.target.value as (typeof FIELD_OPTIONS)[number]['value'])}
            className="rounded border px-3 py-2 outline-none focus:ring"
          >
            {FIELD_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
          <input
            value={val}
            onChange={(e) => setVal(e.target.value)}
            placeholder={FIELD_OPTIONS.find((o) => o.value === selKey)?.placeholder ?? ''}
            className="rounded border px-3 py-2 outline-none focus:ring"
          />
          <Button onClick={addCriterion}>
            Add criteria
          </Button>
        </div>

        {fields.length > 0 && (
          <ul className="mt-2 grid grid-cols-1 md:grid-cols-2 gap-2">
            {fields.map((c, j) => (
              <li
                key={c.id}
                className="flex items-center justify-between rounded border px-3 py-2 text-sm"
              >
                <span className="truncate">
                  <span className="font-semibold">{c.search_field}</span>: {c.value}
                </span>
                <Button onClick={() => remove(j)} variant="outlined" color="danger" size="sm">
                  <FaX />
                </Button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </fieldset>
  );
}

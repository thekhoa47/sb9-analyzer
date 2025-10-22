import React, { useEffect } from 'react';
import { z } from 'zod';
import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { formSchema, emailRequiredValid, phoneRequiredValid, type FormValues } from './formSchema';
import { SavedSearchCard } from './savedSearchCard';
import { Checkbox } from '@/components/checkbox';
import { Button } from '@/components/button';

// ----------------- types from zod -----------------
type Schema = typeof formSchema;
type FormInput = z.input<Schema>;
type FormOutput = z.infer<Schema>;

// ----------------- main form -----------------
export function NewClientForm({
  onSubmit,
  onCancel,
}: {
  onSubmit: (data: FormValues) => void;
  onCancel: () => void;
}) {
  const {
    control,
    register,
    handleSubmit,
    watch,
    reset,
    formState: { errors },
  } = useForm<FormInput, undefined, FormOutput>({
    resolver: zodResolver(formSchema),
    mode: 'onChange',
    defaultValues: {
      name: '',
      email: '',
      phone: '',
      address: '',
      is_active: true,
      // one default saved search (min=1)
      saved_searches: [
        {
          name: '',
          beds_min: 1,
          baths_min: 1,
          max_price: 2000000,
          analysis_note: undefined,
          fields: [],
        },
      ],
      notification_preferences: [],
    },
  });

  // top-level arrays
  const {
    fields: ssFields,
    append: ssAppend,
    remove: ssRemove,
  } = useFieldArray<FormInput, 'saved_searches'>({
    control,
    name: 'saved_searches',
  });

  const {
    fields: npFields,
    append: npAppend,
    remove: npRemove,
    update: npUpdate,
  } = useFieldArray<FormInput, 'notification_preferences'>({
    control,
    name: 'notification_preferences',
  });

  // email/phone opt-in logic
  const emailVal = watch('email');
  const phoneVal = watch('phone');
  const emailValid = emailRequiredValid.safeParse(emailVal ?? '').success;
  const phoneValid = phoneRequiredValid.safeParse(phoneVal ?? '').success;

  const hasPref = (channel: 'EMAIL' | 'SMS') => npFields.some((p) => p.channel === channel);

  const ensurePrefOn = (channel: 'EMAIL' | 'SMS') => {
    const idx = npFields.findIndex((p) => p.channel === channel);
    if (idx === -1) npAppend({ channel, enabled: true });
    else if (!npFields[idx].enabled) npUpdate(idx, { ...npFields[idx], enabled: true });
  };

  const ensurePrefOff = (channel: 'EMAIL' | 'SMS') => {
    const idx = npFields.findIndex((p) => p.channel === channel);
    if (idx !== -1) npRemove(idx);
  };

  // auto-sync preferences based on validity
  useEffect(() => {
    if (emailValid) ensurePrefOn('EMAIL');
    else ensurePrefOff('EMAIL');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [emailValid]);

  useEffect(() => {
    if (phoneValid) ensurePrefOn('SMS');
    else ensurePrefOff('SMS');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phoneValid]);

  const submitHandler = async (data: FormOutput) => {
    try {
      console.log(data);
      await onSubmit(data);
      // reset(); // resets to defaults (1 saved search, prefs follow validators)
    } catch (err) {
      console.log(err);
    }
  };
  const cancelHandler = () => {
    reset();
    onCancel();
  };

  return (
    <form
      noValidate
      onSubmit={handleSubmit(submitHandler, (errs) => console.error('Form invalid:', errs))}
      className="mx-auto flex flex-col gap-8"
    >
      {/* Client info */}
      <section className="rounded-2xl border  p-6 shadow-sm">
        <h2 className="mb-4 text-lg font-semibold">Client</h2>
        <div className="grid grid-cols-1 gap-4">
          <label className=" full flex flex-col gap-1 text-sm font-medium">
            Name*
            <input
              {...register('name', { required: true })}
              className="w-full rounded border px-3 py-2 outline-none focus:ring"
              placeholder="Your name"
            />
            {errors.name && <p className="text-sm text-red-600">{errors.name.message}</p>}
            <Checkbox label="Active" {...register('is_active')} />
          </label>

          <label className="flex flex-col gap-1 text-sm font-medium">
            Email
            <input
              type="email"
              {...register('email', {
                setValueAs: (v) => (typeof v === 'string' && v.trim() === '' ? undefined : v),
              })}
              className="w-full rounded border px-3 py-2 outline-none focus:ring"
              placeholder="you@example.com"
            />
            {errors.email && <p className="text-sm text-red-600 mt-1">{errors.email.message}</p>}
            <Checkbox
              label="Receive email updates"
              disabled={!emailValid}
              checked={hasPref('EMAIL')}
              onChange={(e) => (e.target.checked ? ensurePrefOn('EMAIL') : ensurePrefOff('EMAIL'))}
            />
          </label>

          <label className="flex flex-col gap-1 text-sm font-medium">
            Phone
            <input
              type="tel"
              {...register('phone', {
                setValueAs: (v) => (typeof v === 'string' && v.trim() === '' ? undefined : v),
              })}
              className="w-full rounded border px-3 py-2 outline-none focus:ring"
              placeholder="+14085551234"
            />
            {errors.phone && <p className="text-sm text-red-600 mt-1">{errors.phone.message}</p>}
            <Checkbox
              label="Receive email updates"
              disabled={!phoneValid}
              checked={hasPref('SMS')}
              onChange={(e) => (e.target.checked ? ensurePrefOn('SMS') : ensurePrefOff('SMS'))}
            />
          </label>

          <label className="flex flex-col gap-1 text-sm font-medium">
            Address
            <input
              {...register('address')}
              className="w-full rounded border px-3 py-2 outline-none focus:ring"
              placeholder="123 Main St"
            />
            {errors.address && <p className="text-sm text-red-600">{errors.address.message}</p>}
          </label>
        </div>
      </section>

      {/* Saved searches */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Saved Searches</h2>
          <Button
            onClick={() =>
              ssAppend({
                name: '',
                beds_min: 1,
                baths_min: 1,
                max_price: undefined,
                analysis_note: undefined,
                fields: [],
              })
            }
          >
            + Add search
          </Button>
        </div>

        {errors.saved_searches?.message && (
          <p className="text-sm text-red-600">{errors.saved_searches.message as string}</p>
        )}

        <div className="space-y-6">
          {ssFields.map((f, i) => (
            <SavedSearchCard
              key={f.id}
              index={i}
              control={control}
              register={register}
              errors={errors}
              onRemove={() => ssRemove(i)}
              canRemove={ssFields.length > 1}
            />
          ))}
        </div>
      </section>

      {/* Actions */}
      <div className="mt-6 flex justify-end gap-3">
        <Button variant="text" onClick={cancelHandler}>
          Cancel
        </Button>
        <Button type="submit" color='warning'>Submit</Button>
      </div>
    </form>
  );
}

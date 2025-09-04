import { z } from 'zod';
import { Checkbox } from '@/components/checkbox';
import { useFieldArray, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { FormValues, formSchema, emailRequiredValid, phoneRequiredValid } from './formSchema';

type ContactFormProps = {
  onSubmit: (data: FormValues) => void;
  onCancel: () => void;
};

type Schema = typeof formSchema;
type FormInput = z.input<Schema>; // before preprocess/coerce
type FormOutput = z.infer<Schema>; // after resolver

export function NewClientForm({ onSubmit, onCancel }: ContactFormProps) {
  const {
    control,
    register,
    handleSubmit,
    watch,
    reset,
    formState: { errors },
  } = useForm<FormInput, undefined, FormOutput>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: '',
      email: '',
      phone: '',
      messenger_psid: '',
      email_opt_in: false,
      sms_opt_in: false,
      messenger_opt_in: false,
      listing_preferences: [
        {
          name: '',
          city: '',
          radius_miles: 50,
          beds_min: 2,
          baths_min: 2,
          max_price: 1000000,
        },
      ],
    },
    mode: 'onChange',
  });

  const { fields, append, remove } = useFieldArray<FormInput>({
    control,
    name: 'listing_preferences',
  });

  const emailVal = watch('email');
  const phoneVal = watch('phone');
  const messengerVal = watch('messenger_psid');

  // enable only if strict validators pass
  const emailEnabled = emailRequiredValid.safeParse(emailVal ?? '').success;
  const phoneEnabled = phoneRequiredValid.safeParse(phoneVal ?? '').success;
  const messengerNonEmpty = z
    .string()
    .trim()
    .min(1)
    .safeParse(messengerVal ?? '').success;

  const submitHandler = (data: FormOutput) => {
    onSubmit(data);
    reset();
  };

  const cancelHandler = () => {
    reset();
    onCancel();
  };

  return (
    <form
      noValidate
      onSubmit={handleSubmit(submitHandler, (errs) => {
        console.error('Form invalid:', errs);
      })}
      className="flex flex-col gap-6"
    >
      <label htmlFor="new-client-name" className="flex flex-col gap-1 text-sm font-medium">
        Name*
        <input
          {...register('name', { required: true })}
          className="w-full rounded border px-3 py-2 outline-none focus:ring"
          placeholder="Your name"
          id="new-client-name"
        />
        {errors.name && <p className="text-sm text-red-600">{errors.name.message}</p>}
      </label>

      <div className="flex flex-col gap-2">
        <label htmlFor="new-client-email" className="flex flex-col gap-1 text-sm font-medium">
          Email
          <input
            type="email"
            {...register('email', {
              setValueAs: (v) => {
                if (typeof v === 'string') {
                  const t = v.trim();
                  return t === '' ? undefined : t;
                }
                return v;
              },
            })}
            className="w-full rounded border px-3 py-2 outline-none focus:ring"
            placeholder="you@example.com"
            id="new-client-email"
          />
        </label>
        {errors.email && <p className="text-sm text-red-600 mt-1">{errors.email.message}</p>}
        <Checkbox
          disabled={!emailEnabled}
          id="email-opt-in"
          label="Receive email update"
          {...register('email_opt_in')}
        />
      </div>

      <div className="flex flex-col gap-2">
        <label htmlFor="new-client-phone" className="flex flex-col gap-1 text-sm font-medium">
          Phone
          <input
            type="tel"
            {...register('phone', {
              setValueAs: (v) => {
                if (typeof v === 'string') {
                  const t = v.trim();
                  return t === '' ? undefined : t; // matches your Zod preprocess
                }
                return v;
              },
            })}
            className="w-full rounded border px-3 py-2 outline-none focus:ring"
            placeholder="+14085551234"
            id="new-client-phone"
          />
        </label>
        {errors.phone && <p className="text-sm text-red-600 mt-1">{errors.phone.message}</p>}
        <Checkbox
          disabled={!phoneEnabled}
          id="sms-opt-in"
          label="Receive SMS update"
          {...register('sms_opt_in')}
        />
      </div>

      <div className="flex flex-col gap-2">
        <label htmlFor="new-client-messenger" className="flex flex-col gap-1 text-sm font-medium">
          Messenger PSID
          <input
            {...register('messenger_psid')}
            className="w-full rounded border px-3 py-2 outline-none focus:ring"
            placeholder="you@example.com"
            id="new-client-messenger"
          />
        </label>
        {errors.messenger_psid && (
          <p className="text-sm text-red-600 mt-1">{errors.messenger_psid.message}</p>
        )}
        <Checkbox
          disabled={!messengerNonEmpty}
          id="messenger-opt-in"
          label="Receive Messenger update"
          {...register('messenger_opt_in')}
        />
      </div>

      {/* Saved searches */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Saved Searches</h2>
          <button
            type="button"
            onClick={() =>
              append({
                name: '',
                city: '',
                radius_miles: 50,
                beds_min: 2,
                baths_min: 2,
                max_price: 1000000,
              })
            }
            className="rounded bg-black px-3 py-2 text-white hover:bg-black/90"
          >
            + Add search
          </button>
        </div>

        {errors.listing_preferences?.message && (
          <p className="text-sm text-red-600">{errors.listing_preferences.message as string}</p>
        )}

        <div className="space-y-6">
          {fields.map((field, i) => (
            <fieldset key={field.id} className="rounded border p-4 space-y-4">
              <legend className="px-2 text-sm font-medium text-gray-300">Search #{i + 1}</legend>

              {/* Row 1: Name (full row) */}
              <label
                htmlFor={`listing-${i}-name`}
                className="flex flex-col gap-1 text-sm font-medium"
              >
                Name
                <input
                  id={`listing-${i}-name`}
                  {...register(`listing_preferences.${i}.name`)}
                  className="w-full rounded border px-3 py-2 outline-none focus:ring"
                  placeholder='e.g. "2 bed in SF"'
                />
                {errors.listing_preferences?.[i]?.name && (
                  <span className="text-sm text-red-600">
                    {errors.listing_preferences[i]?.name?.message as string}
                  </span>
                )}
              </label>

              {/* Row 2: City (large) + Radius (small) */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <label
                  htmlFor={`listing-${i}-city`}
                  className="flex flex-col gap-1 text-sm font-medium md:col-span-2"
                >
                  City
                  <input
                    id={`listing-${i}-city`}
                    {...register(`listing_preferences.${i}.city`)}
                    className="w-full rounded border px-3 py-2 outline-none focus:ring"
                  />
                  {errors.listing_preferences?.[i]?.city && (
                    <span className="text-sm text-red-600">
                      {errors.listing_preferences[i]?.city?.message as string}
                    </span>
                  )}
                </label>

                <label
                  htmlFor={`listing-${i}-radius`}
                  className="flex flex-col gap-1 text-sm font-medium"
                >
                  Radius (miles)
                  <input
                    id={`listing-${i}-radius`}
                    type="number"
                    {...register(`listing_preferences.${i}.radius_miles`)}
                    className="w-full rounded border px-3 py-2 outline-none focus:ring"
                  />
                  {errors.listing_preferences?.[i]?.radius_miles && (
                    <span className="text-sm text-red-600">
                      {errors.listing_preferences[i]?.radius_miles?.message as string}
                    </span>
                  )}
                </label>
              </div>

              {/* Row 3: Beds + Baths */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <label
                  htmlFor={`listing-${i}-beds`}
                  className="flex flex-col gap-1 text-sm font-medium"
                >
                  Beds (min)
                  <input
                    id={`listing-${i}-beds`}
                    type="number"
                    {...register(`listing_preferences.${i}.beds_min`)}
                    className="w-full rounded border px-3 py-2 outline-none focus:ring"
                  />
                  {errors.listing_preferences?.[i]?.beds_min && (
                    <span className="text-sm text-red-600">
                      {errors.listing_preferences[i]?.beds_min?.message as string}
                    </span>
                  )}
                </label>

                <label
                  htmlFor={`listing-${i}-baths`}
                  className="flex flex-col gap-1 text-sm font-medium"
                >
                  Baths (min)
                  <input
                    id={`listing-${i}-baths`}
                    type="number"
                    {...register(`listing_preferences.${i}.baths_min`)}
                    className="w-full rounded border px-3 py-2 outline-none focus:ring"
                  />
                  {errors.listing_preferences?.[i]?.baths_min && (
                    <span className="text-sm text-red-600">
                      {errors.listing_preferences[i]?.baths_min?.message as string}
                    </span>
                  )}
                </label>
              </div>

              {/* Row 4: Max price with commas */}
              <label
                htmlFor={`listing-${i}-maxprice`}
                className="flex flex-col gap-1 text-sm font-medium"
              >
                Max price
                {(() => {
                  const reg = register(`listing_preferences.${i}.max_price`, {
                    setValueAs: (v) => {
                      const raw = String(v ?? '').replace(/,/g, '');
                      if (raw === '') return undefined as unknown as number;
                      const n = Number(raw);
                      return Number.isNaN(n) ? (undefined as unknown as number) : n;
                    },
                  });

                  const formatWithCommas = (raw: string) =>
                    raw.replace(/[^\d]/g, '').replace(/\B(?=(\d{3})+(?!\d))/g, ',');

                  return (
                    <input
                      id={`listing-${i}-maxprice`}
                      type="text"
                      inputMode="numeric"
                      {...reg}
                      onChange={(e) => {
                        const formatted = formatWithCommas(e.target.value);
                        e.target.value = formatted;
                        reg.onChange(e);
                      }}
                      className="w-full rounded border px-3 py-2 outline-none focus:ring"
                      placeholder="1,000,000"
                    />
                  );
                })()}
                {errors.listing_preferences?.[i]?.max_price && (
                  <span className="text-sm text-red-600">
                    {errors.listing_preferences[i]?.max_price?.message as string}
                  </span>
                )}
              </label>

              {/* Remove button */}
              <div className="flex justify-end">
                <button
                  type="button"
                  onClick={() => remove(i)}
                  className="rounded border px-3 py-2 hover:bg-gray-50"
                  disabled={fields.length === 1}
                  title={fields.length === 1 ? 'Keep at least one search' : 'Remove'}
                >
                  Remove
                </button>
              </div>
            </fieldset>
          ))}
        </div>
      </section>

      <div className="mt-6 flex justify-end gap-3">
        <button
          type="button"
          onClick={cancelHandler}
          className="rounded border px-4 py-2 hover:bg-gray-50"
        >
          Cancel
        </button>
        <button type="submit" className="rounded bg-black px-4 py-2 text-white hover:bg-black/90">
          Submit
        </button>
      </div>
    </form>
  );
}

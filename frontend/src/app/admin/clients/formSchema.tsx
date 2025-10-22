import { z } from 'zod';

export const emailSchema = z
  .preprocess(
    (v) => (typeof v === 'string' && v.trim() === '' ? undefined : v),
    z.email('Invalid email')
  )
  .optional();

const phoneRegex = /^\+?[1-9]\d{7,14}$/; // tweak to your needs

export const phoneSchema = z
  .preprocess(
    (v) => (typeof v === 'string' && v.trim() === '' ? undefined : v),
    z.string().trim().regex(phoneRegex, 'Invalid phone number')
  )
  .optional();

export const maxPriceSchema = z.preprocess(
  (v) => {
    if (v === '' || v == null) return undefined;
    if (typeof v === 'number') return Number.isNaN(v) ? undefined : v;
    if (typeof v === 'string') {
      const n = Number(v.replace(/,/g, ''));
      return Number.isNaN(n) ? undefined : n;
    }
    return v;
  },
  z.union([z.number().int().min(0, 'Max price must be ≥ 0'), z.undefined()])
);

export const savedSearchFieldSchema = z.object({
  search_field: z.string(),
  value: z.string(),
});

export const clientSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  email: emailSchema,
  phone: phoneSchema,
  address: z.string().optional(),
  is_active: z.boolean().default(true),
});

export const savedSearchSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  beds_min: z.coerce.number().int().min(0, 'Beds must be ≥ 0'),
  baths_min: z.coerce.number().int().min(0, 'Baths must be ≥ 0'),
  max_price: maxPriceSchema,
  analysis_note: z.string().optional(),
  fields: z.array(savedSearchFieldSchema).optional(),
});

export const clientNotificationPreferenceSchema = z.object({
  channel: z.string(),
  enabled: z.boolean(),
});

export const formSchema = clientSchema.extend({
  saved_searches: z.array(savedSearchSchema).min(1, 'At least one search required'),
  notification_preferences: z.array(clientNotificationPreferenceSchema),
});

export type FormValues = z.infer<typeof formSchema>;

// -------- Strict validators for enabling checkboxes --------
export const emailRequiredValid = z.string().trim().min(1).email();
export const phoneRequiredValid = z.string().trim().regex(phoneRegex);

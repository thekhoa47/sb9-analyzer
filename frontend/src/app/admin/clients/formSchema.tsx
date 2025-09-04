import { z } from 'zod';

// -------- Validators --------

// Optional email field: "" → undefined
export const emailSchema = z
  .preprocess(
    (v) => (typeof v === 'string' && v.trim() === '' ? undefined : v),
    z.email('Invalid email')
  )
  .optional();

// Optional phone field: "" → undefined
const phoneRegex = /^\+?[1-9]\d{7,14}$/; // tweak to your needs
export const phoneSchema = z
  .preprocess(
    (v) => (typeof v === 'string' && v.trim() === '' ? undefined : v),
    z.string().trim().regex(phoneRegex, 'Invalid phone number')
  )
  .optional();

// Messenger PSID (optional, no strict validation)
export const messengerSchema = z
  .preprocess((v) => (typeof v === 'string' && v.trim() === '' ? undefined : v), z.string())
  .optional();

// Saved search schema
export const savedSearchSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  city: z.string().min(1, 'City is required'),
  radius_miles: z.coerce.number().min(0, 'Radius must be ≥ 0'),
  beds_min: z.coerce.number().int().min(0, 'Beds must be ≥ 0'),
  baths_min: z.coerce.number().int().min(0, 'Baths must be ≥ 0'),
  max_price: z
    .preprocess(
      (v) => (v === '' ? undefined : v),
      z.coerce.number().min(0, 'Max price must be ≥ 0')
    )
    .optional(),
});

// Main form schema
export const formSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  email: emailSchema,
  phone: phoneSchema,
  messenger_psid: messengerSchema,
  email_opt_in: z.boolean().optional(),
  sms_opt_in: z.boolean().optional(),
  messenger_opt_in: z.boolean().optional(),
  listing_preferences: z.array(savedSearchSchema).min(1, 'At least one search required'),
});

export type FormValues = z.infer<typeof formSchema>;

// -------- Strict validators for enabling checkboxes --------
export const emailRequiredValid = z.string().trim().min(1).email();
export const phoneRequiredValid = z.string().trim().regex(phoneRegex);

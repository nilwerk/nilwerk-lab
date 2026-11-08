// Client-side validation for the auth forms (FR-A01). The server (Supabase Auth) stays the authority; this gives early, plain feedback.
// Every returned value is a string-catalogue key + params, never user-facing text.

export const PASSWORD_MIN = 8;
export const DISPLAY_NAME_MAX = 60;

export interface FieldError { key: string; params?: Record<string, string | number> }
export type FieldResult = FieldError | null;

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

export function validateEmail(value: string): FieldResult {
  const v = value.trim();
  if (!v) return { key: 'validation.email.required' };
  if (v.length > 254 || !EMAIL_RE.test(v)) return { key: 'validation.email.invalid' };
  return null;
}

export function validatePassword(value: string): FieldResult {
  if (!value) return { key: 'validation.password.required' };
  if (value.length < PASSWORD_MIN) return { key: 'validation.password.short', params: { min: PASSWORD_MIN } };
  return null;
}

export function validateDisplayName(value: string): FieldResult {
  if (value.trim().length > DISPLAY_NAME_MAX) return { key: 'validation.displayName.long', params: { max: DISPLAY_NAME_MAX } };
  return null;
}

/** Account deletion needs the exact word DELETE (OpenAPI /account: confirm enum [DELETE]). */
export function validateDeleteConfirm(value: string): FieldResult {
  return value.trim() === 'DELETE' ? null : { key: 'validation.delete.mismatch' };
}

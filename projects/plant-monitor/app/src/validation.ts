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

// ---- device setup (4.A3, FR-A03 / FR-A04). Limits from ble-provisioning.md (name 1-80) and db-schema.sql plants.* ----
export const DEVICE_NAME_MAX = 80;
export const PLANT_NAME_MAX = 80;
export const AREA_MAX = 80;
export const SPECIES_MAX = 120;
export const CITY_MAX = 120;

const required = (v: string, key: string): FieldResult => (v.trim() ? null : { key });
const tooLong = (v: string, max: number): FieldResult => (v.trim().length > max ? { key: 'validation.tooLong', params: { max } } : null);

export const validateDeviceName = (v: string): FieldResult => required(v, 'validation.deviceName.required') ?? tooLong(v, DEVICE_NAME_MAX);
export const validateSsid = (v: string): FieldResult => required(v, 'validation.ssid.required') ?? (new TextEncoder().encode(v).length > 32 ? { key: 'validation.ssid.long' } : null);
export const validateWifiPassword = (v: string): FieldResult => required(v, 'validation.wifiPassword.required');
export const validatePlantName = (v: string): FieldResult => required(v, 'validation.plantName.required') ?? tooLong(v, PLANT_NAME_MAX);
export const validateArea = (v: string): FieldResult => required(v, 'validation.area.required') ?? tooLong(v, AREA_MAX);
export const validateCity = (v: string): FieldResult => required(v, 'validation.city.required') ?? tooLong(v, CITY_MAX);
export const validateSpecies = (v: string): FieldResult => tooLong(v, SPECIES_MAX);

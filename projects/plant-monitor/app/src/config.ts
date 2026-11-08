// Runtime config. Values are injected at build time by app.config.ts from SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, CONTACT_EMAIL (default nilwerk.team@gmail.com; an explicitly empty value hides the Premium contact link).
// The publishable key is public by design (RLS protects data, NFR-06). Never put a secret / service-role key in the app.
import Constants from 'expo-constants';

// Nilwerk's one shared mailbox for now (A-048, Arsany 2026-11-08: only this one until there are more customers). Public contact address, not a secret.
export const DEFAULT_CONTACT_EMAIL = 'nilwerk.team@gmail.com';

// The address shown in the legal line (A-052): the configured contact, or the default when the Premium link is hidden (the Impressum contact must never be empty).
export const legalContact = (configured: string): string => configured || DEFAULT_CONTACT_EMAIL;

export interface AppConfig { supabaseUrl: string; supabasePublishableKey: string; contactEmail: string }

export function readConfig(extra: Record<string, unknown> | undefined = Constants.expoConfig?.extra): AppConfig {
  const s = (k: string) => (typeof extra?.[k] === 'string' ? (extra[k] as string).trim() : '');
  return { supabaseUrl: s('supabaseUrl'), supabasePublishableKey: s('supabasePublishableKey'), contactEmail: typeof extra?.contactEmail === 'string' ? s('contactEmail') : DEFAULT_CONTACT_EMAIL };
}

export function isConfigured(c: AppConfig): boolean {
  return /^https:\/\/|^http:\/\/(localhost|127\.0\.0\.1|10\.0\.2\.2)/.test(c.supabaseUrl) && c.supabasePublishableKey.length > 0;
}

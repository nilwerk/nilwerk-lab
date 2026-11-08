// Runtime config. Values are injected at build time by app.config.ts from SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, CONTACT_EMAIL.
// The publishable key is public by design (RLS protects data, NFR-06). Never put a secret / service-role key in the app.
import Constants from 'expo-constants';

export interface AppConfig { supabaseUrl: string; supabasePublishableKey: string; contactEmail: string }

export function readConfig(extra: Record<string, unknown> | undefined = Constants.expoConfig?.extra): AppConfig {
  const s = (k: string) => (typeof extra?.[k] === 'string' ? (extra[k] as string).trim() : '');
  return { supabaseUrl: s('supabaseUrl'), supabasePublishableKey: s('supabasePublishableKey'), contactEmail: s('contactEmail') };
}

export function isConfigured(c: AppConfig): boolean {
  return /^https:\/\/|^http:\/\/(localhost|127\.0\.0\.1|10\.0\.2\.2)/.test(c.supabaseUrl) && c.supabasePublishableKey.length > 0;
}

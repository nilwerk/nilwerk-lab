// Expo config. Brand wiring per showcase/brand/app/README.md (A-040): icon, adaptive icon, splash light/dark.
// Supabase settings come from the environment at build time (names only, never values in the repo):
//   SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY (the NEW publishable key, not the legacy anon key), CONTACT_EMAIL (Premium contact link).
import type { ExpoConfig } from 'expo/config';

const config: ExpoConfig = {
  name: 'Plant Monitor',
  slug: 'plant-monitor',
  version: '0.1.0',
  scheme: 'plantmonitor',
  orientation: 'portrait',
  icon: './assets/icon-1024.png',
  userInterfaceStyle: 'automatic',
  ios: { bundleIdentifier: 'de.nilwerk.plantmonitor', supportsTablet: false },
  android: {
    package: 'de.nilwerk.plantmonitor',
    adaptiveIcon: { foregroundImage: './assets/adaptive-icon-foreground-1024.png', backgroundColor: '#15181d' },
  },
  web: { favicon: './assets/favicon-48.png', bundler: 'metro' },
  plugins: [
    'expo-font',
    'expo-secure-store',
    [
      'expo-splash-screen',
      {
        image: './assets/splash-light-1284x2778.png',
        backgroundColor: '#f6f4ef',
        imageWidth: 200,
        dark: { image: './assets/splash-dark-1284x2778.png', backgroundColor: '#101317' },
      },
    ],
  ],
  extra: {
    supabaseUrl: process.env.SUPABASE_URL ?? '',
    supabasePublishableKey: process.env.SUPABASE_PUBLISHABLE_KEY ?? '',
    // Default is Nilwerk's shared mailbox (A-048); CONTACT_EMAIL overrides it, CONTACT_EMAIL= (empty) hides the link.
    contactEmail: process.env.CONTACT_EMAIL ?? 'nilwerk.team@gmail.com',
  },
};

export default config;

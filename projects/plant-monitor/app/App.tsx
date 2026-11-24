// App shell. Requirements: FR-P03 (profile -> connect your AI), FR-A01 (signed-out: welcome -> sign up / sign in; signed-in: profile -> delete account / premium), FR-A06 (plants tab: list -> detail),
// FR-A05 (detail -> photo gallery), FR-A08 + A-022 (detail -> export -> remove plant -> keep/release sensor), 4.A3 device setup (profile -> setup; fake service in the mock build, real BLE in a dev build, 4.A3b). Alerts (4.A5, FR-A07): plant list -> alerts list, rules from src/plants/alerts.ts; push delivery is not built.
import React, { useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, Platform, View } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import { useFonts } from 'expo-font';
import { SpaceGrotesk_500Medium, SpaceGrotesk_700Bold } from '@expo-google-fonts/space-grotesk';
import { Inter_400Regular, Inter_600SemiBold } from '@expo-google-fonts/inter';
import { JetBrainsMono_400Regular, JetBrainsMono_600SemiBold } from '@expo-google-fonts/jetbrains-mono';
import { AuthProvider, useAuth } from './src/auth/AuthContext';
import { createSupabaseAuth } from './src/auth/supabaseAuth';
import { createFakeAuth } from './src/auth/fakeAuth';
import { AuthError, type AuthService } from './src/auth/types';
import { isConfigured, readConfig } from './src/config';
import { useTheme } from './src/ui/useTheme';
import { Notice } from './src/ui/primitives';
import { t } from './src/i18n';
import { WelcomeScreen } from './src/screens/WelcomeScreen';
import { AuthFormScreen, type AuthMode } from './src/screens/AuthFormScreen';
import { ProfileScreen } from './src/screens/ProfileScreen';
import { DeleteAccountScreen } from './src/screens/DeleteAccountScreen';
import { PremiumScreen } from './src/screens/PremiumScreen';
import { PlantsScreen } from './src/screens/PlantsScreen';
import { PlantDetailScreen } from './src/screens/PlantDetailScreen';
import { PlantRemovedScreen, RemovePlantScreen, type RemoveOutcome } from './src/screens/RemovePlantScreen';
import { PlantGalleryScreen } from './src/screens/PlantGalleryScreen';
import { AlertsScreen } from './src/screens/AlertsScreen';
import { PremiumDashboardScreen } from './src/screens/PremiumDashboardScreen';
import { ConnectAiScreen } from './src/screens/ConnectAiScreen';
import { createApiKeysClient, unconfiguredApiKeys, type ApiKeysService } from './src/mcp/apiKeysApi';
import { createAnalyticsClient, unconfiguredAnalytics, type AnalyticsService } from './src/analytics/analyticsApi';
import { PlantsProvider } from './src/plants/PlantsContext';
import { createFakePlants } from './src/plants/fakePlants';
import { unconfiguredPlants } from './src/plants/unconfiguredPlants';
import { createRealPlants } from './src/plants/realPlants';
import { createFileHandOff } from './src/export/fileHandOff';
import { platformHandOffDeps } from './src/export/handOffDeps';
import type { PlantDetail, PlantSummary, PlantsService } from './src/plants/types';
import { TabBar, type Tab } from './src/ui/TabBar';
import { SetupFlow } from './src/screens/setup/SetupFlow';
import { createFakeSetup, unavailableProvisioning } from './src/provisioning/fakeProvisioning';
import { createRealPlantSetup, noPhotoSource, unconfiguredPlantSetup } from './src/provisioning/realPlantSetup';
import { createBleProvisioning } from './src/provisioning/bleProvisioning';
import { createEspAdapter } from './src/provisioning/espAdapter';
import { createFetchClaimApi } from './src/provisioning/claimApi';
import type { SetupServices } from './src/provisioning/types';

type Route = 'welcome' | AuthMode | 'plants' | 'alerts' | 'setup' | 'plant' | 'gallery' | 'remove' | 'removed' | 'profile' | 'delete' | 'premium' | 'dashboard' | 'connectAi';
type Removed = RemoveOutcome;

/** Service used when no Supabase config is present: every call reports "not configured" instead of crashing. */
function unconfiguredAuth(): AuthService {
  const no = async (): Promise<never> => { throw new AuthError('not_configured'); };
  return { getSession: async () => null, onChange: () => () => undefined, signUp: no, signIn: no, signOut: no, getProfile: no, updateDisplayName: no, deleteAccount: no, getAccessToken: async () => null };
}

export function Root({ contactEmail, banner, setup, analytics = unconfiguredAnalytics, apiKeys = unconfiguredApiKeys }: { contactEmail: string; banner?: string; setup: SetupServices; analytics?: AnalyticsService; apiKeys?: ApiKeysService }) {
  const { state } = useAuth();
  const th = useTheme();
  const [route, setRoute] = useState<Route>('welcome');
  const [plantId, setPlantId] = useState<string | null>(null);
  const [toRemove, setToRemove] = useState<PlantDetail | null>(null);
  const [gallery, setGallery] = useState<PlantSummary | null>(null);
  const [removed, setRemoved] = useState<Removed | null>(null);
  const signedOut = state.status === 'signedOut';
  // a signed-out user starts again at the welcome screen, so the next sign-in lands on the plants tab
  useEffect(() => { if (signedOut) { setRoute('welcome'); setPlantId(null); setToRemove(null); setGallery(null); setRemoved(null); } }, [signedOut]);

  if (state.status === 'loading') {
    return <View style={{ flex: 1, justifyContent: 'center', backgroundColor: th.color.bg }}><ActivityIndicator accessibilityLabel={t('common.loading')} color={th.color.accent} /></View>;
  }
  const signedIn = state.status === 'signedIn';
  let screen: React.ReactNode;
  if (!signedIn) {
    // a signed-out user can never be on a signed-in route
    const r: Route = route === 'signUp' || route === 'signIn' ? route : 'welcome';
    screen = r === 'welcome'
      ? <WelcomeScreen contactEmail={contactEmail} onCreate={() => setRoute('signUp')} onSignIn={() => setRoute('signIn')} />
      : <AuthFormScreen mode={r} onSwitch={() => setRoute(r === 'signUp' ? 'signIn' : 'signUp')} onBack={() => setRoute('welcome')} />;
  } else if (route === 'delete') {
    screen = <DeleteAccountScreen onCancel={() => setRoute('profile')} />;
  } else if (route === 'setup') {
    screen = <SetupFlow services={setup} onExit={() => setRoute('profile')} />;
  } else if (route === 'dashboard') {
    screen = <PremiumDashboardScreen analytics={analytics} onBack={() => setRoute('profile')} onPremium={() => setRoute('premium')} />;
  } else if (route === 'connectAi') {
    screen = <ConnectAiScreen apiKeys={apiKeys} onBack={() => setRoute('profile')} onPremium={() => setRoute('premium')} />;
  } else if (route === 'premium') {
    screen = <PremiumScreen contactEmail={contactEmail} onBack={() => setRoute('profile')} />;
  } else if (route === 'plant' && plantId) {
    screen = <PlantDetailScreen plantId={plantId} onBack={() => setRoute('plants')} onRemove={(d) => { setToRemove(d); setRoute('remove'); }}
      onGallery={(p) => { setGallery(p); setRoute('gallery'); }} />;
  } else if (route === 'gallery' && gallery) {
    screen = <PlantGalleryScreen plant={gallery} onBack={() => setRoute('plant')} />;
  } else if (route === 'remove' && toRemove) {
    screen = <RemovePlantScreen plant={toRemove.plant} onCancel={() => setRoute('plant')}
      onRemoved={(r) => { setRemoved(r); setToRemove(null); setPlantId(null); setRoute('removed'); }} />;
  } else if (route === 'removed' && removed) {
    screen = <PlantRemovedScreen {...removed} onDone={() => { setRemoved(null); setRoute('plants'); }} />;
  } else if (route === 'profile') {
    screen = <ProfileScreen contactEmail={contactEmail} onPremium={() => setRoute('premium')} onDelete={() => setRoute('delete')} onAddSensor={() => setRoute('setup')} onDashboard={() => setRoute('dashboard')} onConnectAi={() => setRoute('connectAi')} />;
  } else if (route === 'alerts') {
    screen = <AlertsScreen onBack={() => setRoute('plants')} />;
  } else {
    screen = <PlantsScreen onOpen={(id) => { setPlantId(id); setRoute('plant'); }} onAlerts={() => setRoute('alerts')} />;
  }
  const tab: Tab | null = !signedIn ? null : route === 'profile' ? 'profile' : route === 'plants' || route === 'alerts' || route === 'welcome' || route === 'signUp' || route === 'signIn' ? 'plants' : null;
  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: th.color.bg }}>
      {banner ? <Notice kind="info" text={banner} /> : null}
      {screen}
      {tab ? <TabBar active={tab} onSelect={setRoute} /> : null}
    </SafeAreaView>
  );
}

export default function App() {
  const cfg = useMemo(() => readConfig(), []);
  const mock = process.env.EXPO_PUBLIC_MOCK_AUTH === '1';
  const service = useMemo(() => (mock ? createFakeAuth() : isConfigured(cfg) ? createSupabaseAuth(cfg) : unconfiguredAuth()), [cfg, mock]);
  const plants = useMemo<PlantsService>(() => (mock ? createFakePlants() : isConfigured(cfg)
    ? createRealPlants({ baseUrl: cfg.supabaseUrl, publishableKey: cfg.supabasePublishableKey, getAccessToken: () => service.getAccessToken(), handOff: createFileHandOff(platformHandOffDeps) })
    : unconfiguredPlants()), [cfg, mock, service]);
  // Mock build: fake sensor and fake plant save. Real build on a phone (iOS/Android, Supabase configured): real BLE (4.A3b slice 1, needs the dev build; in Expo Go the native
  // library is missing and the first step says so). Web or unconfigured: "not available". The plant itself is saved for real (4.A4c, plants row + devices.plant_id);
  // photos are not in this slice (the photo step offers only Skip).
  const setup = useMemo<SetupServices>(() => {
    const fake = createFakeSetup().services;
    if (mock) return fake;
    const plantSetup = isConfigured(cfg)
      ? createRealPlantSetup({ baseUrl: cfg.supabaseUrl, publishableKey: cfg.supabasePublishableKey, getAccessToken: () => service.getAccessToken(), getUserId: async () => (await service.getSession())?.id ?? null })
      : unconfiguredPlantSetup;
    const base = { ...fake, plants: plantSetup, photos: noPhotoSource };
    if (Platform.OS === 'web' || !isConfigured(cfg)) return { ...base, provisioning: unavailableProvisioning() };
    const claim = createFetchClaimApi({ baseUrl: cfg.supabaseUrl, publishableKey: cfg.supabasePublishableKey, getAccessToken: () => service.getAccessToken() });
    return { ...base, provisioning: createBleProvisioning({ adapter: createEspAdapter(), claim }) };
  }, [mock, cfg, service]);
  // 4.A6: premium analytics client (proposed endpoint, not deployed); mock build and unconfigured builds report not_configured and fetch nothing.
  const analytics = useMemo<AnalyticsService>(() => (!mock && isConfigured(cfg)
    ? createAnalyticsClient({ baseUrl: cfg.supabaseUrl, publishableKey: cfg.supabasePublishableKey, getAccessToken: () => service.getAccessToken() })
    : unconfiguredAnalytics), [cfg, mock, service]);
  // 4.A8: MCP key client (FR-P03). The /api-keys edge function is not built yet (proposed route); mock and unconfigured builds report not_configured and fetch nothing.
  const apiKeys = useMemo<ApiKeysService>(() => (!mock && isConfigured(cfg)
    ? createApiKeysClient({ baseUrl: cfg.supabaseUrl, publishableKey: cfg.supabasePublishableKey, getAccessToken: () => service.getAccessToken() })
    : unconfiguredApiKeys), [cfg, mock, service]);
  const [fonts] = useFonts({ SpaceGrotesk_500Medium, SpaceGrotesk_700Bold, Inter_400Regular, Inter_600SemiBold, JetBrainsMono_400Regular, JetBrainsMono_600SemiBold });
  if (!fonts) return null;
  return (
    <SafeAreaProvider>
    <AuthProvider service={service}>
      <PlantsProvider service={plants}>
        <StatusBar style="auto" />
        <Root contactEmail={cfg.contactEmail} banner={mock ? t('app.mockBanner') : undefined} setup={setup} analytics={analytics} apiKeys={apiKeys} />
      </PlantsProvider>
    </AuthProvider>
    </SafeAreaProvider>
  );
}

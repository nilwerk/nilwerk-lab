// App shell. Requirements: FR-A01 (signed-out: welcome -> sign up / sign in; signed-in: profile -> delete account / premium), FR-A06 (plants tab: list -> detail),
// FR-A08 + A-022 (detail -> remove plant -> keep/release sensor), 4.A3 device setup (profile -> setup, fake service; real BLE is a later slice). gallery (FR-A05) and alerts (4.A5) are not part of this shell yet.
import React, { useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, View } from 'react-native';
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
import { PlantRemovedScreen, RemovePlantScreen } from './src/screens/RemovePlantScreen';
import { PlantsProvider } from './src/plants/PlantsContext';
import { createFakePlants } from './src/plants/fakePlants';
import { unconfiguredPlants } from './src/plants/unconfiguredPlants';
import type { PlantDetail, PlantsService } from './src/plants/types';
import { TabBar, type Tab } from './src/ui/TabBar';
import { SetupFlow } from './src/screens/setup/SetupFlow';
import { createFakeSetup, unavailableProvisioning } from './src/provisioning/fakeProvisioning';
import type { SetupServices } from './src/provisioning/types';

type Route = 'welcome' | AuthMode | 'plants' | 'setup' | 'plant' | 'remove' | 'removed' | 'profile' | 'delete' | 'premium';
interface Removed { plantName: string; deviceId: string | null; sensorName: string | null }

/** Service used when no Supabase config is present: every call reports "not configured" instead of crashing. */
function unconfiguredAuth(): AuthService {
  const no = async (): Promise<never> => { throw new AuthError('not_configured'); };
  return { getSession: async () => null, onChange: () => () => undefined, signUp: no, signIn: no, signOut: no, getProfile: no, updateDisplayName: no, deleteAccount: no };
}

export function Root({ contactEmail, banner, setup }: { contactEmail: string; banner?: string; setup: SetupServices }) {
  const { state } = useAuth();
  const th = useTheme();
  const [route, setRoute] = useState<Route>('welcome');
  const [plantId, setPlantId] = useState<string | null>(null);
  const [toRemove, setToRemove] = useState<PlantDetail | null>(null);
  const [removed, setRemoved] = useState<Removed | null>(null);
  const signedOut = state.status === 'signedOut';
  // a signed-out user starts again at the welcome screen, so the next sign-in lands on the plants tab
  useEffect(() => { if (signedOut) { setRoute('welcome'); setPlantId(null); setToRemove(null); setRemoved(null); } }, [signedOut]);

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
  } else if (route === 'premium') {
    screen = <PremiumScreen contactEmail={contactEmail} onBack={() => setRoute('profile')} />;
  } else if (route === 'plant' && plantId) {
    screen = <PlantDetailScreen plantId={plantId} onBack={() => setRoute('plants')} onRemove={(d) => { setToRemove(d); setRoute('remove'); }} />;
  } else if (route === 'remove' && toRemove) {
    screen = <RemovePlantScreen plant={toRemove.plant} onCancel={() => setRoute('plant')}
      onRemoved={() => { setRemoved({ plantName: toRemove.plant.name, deviceId: toRemove.plant.deviceId, sensorName: toRemove.plant.deviceName }); setToRemove(null); setPlantId(null); setRoute('removed'); }} />;
  } else if (route === 'removed' && removed) {
    screen = <PlantRemovedScreen {...removed} onDone={() => { setRemoved(null); setRoute('plants'); }} />;
  } else if (route === 'profile') {
    screen = <ProfileScreen contactEmail={contactEmail} onPremium={() => setRoute('premium')} onDelete={() => setRoute('delete')} onAddSensor={() => setRoute('setup')} />;
  } else {
    screen = <PlantsScreen onOpen={(id) => { setPlantId(id); setRoute('plant'); }} />;
  }
  const tab: Tab | null = !signedIn ? null : route === 'profile' ? 'profile' : route === 'plants' || route === 'welcome' || route === 'signUp' || route === 'signIn' ? 'plants' : null;
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
  const plants = useMemo<PlantsService>(() => (mock ? createFakePlants() : unconfiguredPlants()), [mock]);
  // Real BLE provisioning (dev build, @orbital-systems/react-native-esp-idf-provisioning) is a later slice: until then only the mock build can run setup.
  const setup = useMemo<SetupServices>(() => (mock ? createFakeSetup().services : { ...createFakeSetup().services, provisioning: unavailableProvisioning() }), [mock]);
  const [fonts] = useFonts({ SpaceGrotesk_500Medium, SpaceGrotesk_700Bold, Inter_400Regular, Inter_600SemiBold, JetBrainsMono_400Regular, JetBrainsMono_600SemiBold });
  if (!fonts) return null;
  return (
    <SafeAreaProvider>
    <AuthProvider service={service}>
      <PlantsProvider service={plants}>
        <StatusBar style="auto" />
        <Root contactEmail={cfg.contactEmail} banner={mock ? t('app.mockBanner') : undefined} setup={setup} />
      </PlantsProvider>
    </AuthProvider>
    </SafeAreaProvider>
  );
}

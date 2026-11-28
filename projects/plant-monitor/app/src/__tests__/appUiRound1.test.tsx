// App UI round 1 (owner feedback, 28 Nov): plant detail chips wrap inside the card (FR-A06, FR-A04); plant list refreshes on pull-down, no Refresh button (FR-A06);
// Profile shows only the current plan tier and its price, the full comparison is on the Premium screen (FR-P04); display name read-only until the edit icon (NFR-06).
// Mocked backend only: fake auth, fake plants, no network, no device. Layout is checked through styles, not on a phone (not run on a device).
import React from 'react';
import { act, render, screen, fireEvent, waitFor } from '@testing-library/react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { Root } from '../../App';
import { AuthProvider } from '../auth/AuthContext';
import { createFakeAuth } from '../auth/fakeAuth';
import { PlantsProvider } from '../plants/PlantsContext';
import { createFakePlants, sampleFixture } from '../plants/fakePlants';
import { createFakeSetup } from '../provisioning/fakeProvisioning';
import { PlantDetailScreen } from '../screens/PlantDetailScreen';
import { PlantsScreen } from '../screens/PlantsScreen';
import { t } from '../i18n';
import type { PlantSummary } from '../plants/types';

const frame = { frame: { x: 0, y: 0, width: 390, height: 844 }, insets: { top: 0, left: 0, right: 0, bottom: 0 } };
const svcWith = (isPremium: boolean) => ({
  ...createFakeAuth(),
  getSession: async () => ({ id: 'user-test', email: 'test@example.invalid' }),
  getProfile: async () => ({ displayName: 'Sam', isPremium }),
});
const mountRoot = async (isPremium: boolean, plants = createFakePlants()) => {
  await render(<SafeAreaProvider initialMetrics={frame}><AuthProvider service={svcWith(isPremium)}><PlantsProvider service={plants}>
    <Root contactEmail="hello@example.invalid" setup={createFakeSetup().services} />
  </PlantsProvider></AuthProvider></SafeAreaProvider>);
  return plants;
};

describe('plant list (FR-A06)', () => {
  test('no Refresh button and no View alerts button; the list renders', async () => {
    const plants = createFakePlants();
    await render(<SafeAreaProvider initialMetrics={frame}><PlantsProvider service={plants}><PlantsScreen onOpen={() => undefined} /></PlantsProvider></SafeAreaProvider>);
    expect(await screen.findByText('Basil')).toBeTruthy();
    expect(screen.queryByRole('button', { name: t('plants.refresh') })).toBeNull();
    expect(screen.queryByRole('button', { name: 'View alerts' })).toBeNull();
  });

  test('pull down at the top reloads the plant list', async () => {
    const plants = createFakePlants();
    const list = jest.spyOn(plants, 'listPlants');
    await render(<SafeAreaProvider initialMetrics={frame}><PlantsProvider service={plants}><PlantsScreen onOpen={() => undefined} /></PlantsProvider></SafeAreaProvider>);
    await screen.findByText('Basil');
    expect(list).toHaveBeenCalledTimes(1);
    const scroll = screen.getByTestId('screen-scroll');
    await act(async () => { scroll.props.refreshControl.props.onRefresh(); });
    await waitFor(() => expect(list).toHaveBeenCalledTimes(2));
  });
});

describe('plant detail chips (FR-A06, FR-A04)', () => {
  test('the status chips sit in a row that wraps inside the card, so a long chip set is not clipped at 390 px', async () => {
    const now = new Date('2026-11-28T12:00:00Z');
    const noSensor: PlantSummary = { ...sampleFixture(now).plants[0], id: 'p-nosensor', name: 'Ficus', deviceId: null, deviceName: null, lastSeenAt: null, latest: null, openAlerts: [] };
    const svc = createFakePlants({ plants: [noSensor] });
    await render(<SafeAreaProvider initialMetrics={frame}><PlantsProvider service={svc}><PlantDetailScreen plantId="p-nosensor" onBack={() => undefined} onRemove={() => undefined} onGallery={() => undefined} now={() => now} /></PlantsProvider></SafeAreaProvider>);
    expect(await screen.findByLabelText(t('a11y.chip', { status: t('status.noSensor') }))).toBeTruthy();
    const chips = screen.getByTestId('plant-chips');
    expect(chips.props.style.flexWrap).toBe('wrap');
  });
});

describe('profile plan box (FR-P04)', () => {
  test('free account: only the Free tier and its price; the Premium price is not on Profile', async () => {
    await mountRoot(false);
    await fireEvent.press(await screen.findByRole('tab', { name: t('nav.profile') }));
    expect(await screen.findByText(t('profile.price.free'))).toBeTruthy();
    expect(screen.queryByText(t('profile.price.premium'))).toBeNull();
    expect(screen.getByRole('button', { name: t('profile.whatIsPremium') })).toBeTruthy();
  });

  test('premium account: only the Premium tier and its price', async () => {
    await mountRoot(true);
    await fireEvent.press(await screen.findByRole('tab', { name: t('nav.profile') }));
    expect(await screen.findByText(t('profile.price.premium'))).toBeTruthy();
    expect(screen.queryByText(t('profile.price.free'))).toBeNull();
  });

  test('What is Premium? opens the Premium screen with the full comparison (both prices)', async () => {
    await mountRoot(false);
    await fireEvent.press(await screen.findByRole('tab', { name: t('nav.profile') }));
    await fireEvent.press(await screen.findByRole('button', { name: t('profile.whatIsPremium') }));
    expect(await screen.findByText(t('profile.price.free'))).toBeTruthy();
    expect(screen.getByText(t('profile.price.premium'))).toBeTruthy();
  });
});

describe('display name (NFR-06)', () => {
  const openProfile = async () => {
    await mountRoot(false);
    await fireEvent.press(await screen.findByRole('tab', { name: t('nav.profile') }));
    await screen.findByText('Sam');
  };

  test('read-only by default: no field, no Save or Cancel; the edit icon is shown', async () => {
    await openProfile();
    expect(screen.queryByLabelText(t('profile.displayName'))).toBeNull();
    expect(screen.queryByRole('button', { name: t('profile.displayName.save') })).toBeNull();
    expect(screen.queryByRole('button', { name: t('common.cancel') })).toBeNull();
    expect(screen.getByRole('button', { name: t('profile.displayName.edit') })).toBeTruthy();
  });

  test('edit icon opens the field with Save and Cancel; Cancel reverts and closes without saving', async () => {
    await openProfile();
    await fireEvent.press(await screen.findByRole('button', { name: t('profile.displayName.edit') }));
    await fireEvent.changeText(await screen.findByLabelText(t('profile.displayName')), 'Changed');
    await fireEvent.press(screen.getByRole('button', { name: t('common.cancel') }));
    expect(screen.queryByLabelText(t('profile.displayName'))).toBeNull();
    expect(screen.getByText('Sam')).toBeTruthy();
    expect(screen.queryByText('Changed')).toBeNull();
  });
});

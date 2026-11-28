// Care tips entry point on the plant detail screen (task 4.A7): the entry renders, opens the tips screen, and the free-account path never reads tips (FR-P02, FR-P04, NFR-06).
// Mocked backend only: fake auth, fake plants, and a stub tips service passed into Root. No Supabase call, no network, no device.
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { Root } from '../../App';
import { AuthProvider } from '../auth/AuthContext';
import { createFakeAuth } from '../auth/fakeAuth';
import { PlantsProvider } from '../plants/PlantsContext';
import { createFakePlants } from '../plants/fakePlants';
import { createFakeSetup } from '../provisioning/fakeProvisioning';
import type { TipsService } from '../tips/tipsApi';
import type { PlantTips } from '../tips/tipsModel';
import { t } from '../i18n';

// Fixture texts stand in for what the server stored (not app data). 'p-basil' is the fake plant the detail opens.
const PLANT_ID = 'p-basil';
const tipsFixture: PlantTips = {
  plantId: PLANT_ID,
  generatedAt: '2026-11-24T06:00:00Z',
  items: [{ id: 'w-1', category: 'watering', text: 'Water when the top 2 cm of soil is dry.' }],
};

const frame = { frame: { x: 0, y: 0, width: 390, height: 844 }, insets: { top: 0, left: 0, right: 0, bottom: 0 } };
const svcWith = (isPremium: boolean) => ({
  ...createFakeAuth(),
  getSession: async () => ({ id: 'user-test', email: 'test@example.invalid' }),
  getProfile: async () => ({ displayName: null, isPremium }),
});
const tipsStub = () => ({ fetchPlantTips: jest.fn(async () => tipsFixture) }) as unknown as TipsService & { fetchPlantTips: jest.Mock };

const mountRoot = async (isPremium: boolean, tips: TipsService) => {
  await render(<SafeAreaProvider initialMetrics={frame}><AuthProvider service={svcWith(isPremium)}><PlantsProvider service={createFakePlants()}>
    <Root contactEmail="hello@example.invalid" setup={createFakeSetup().services} tips={tips} />
  </PlantsProvider></AuthProvider></SafeAreaProvider>);
};

// Plants tab -> plant detail (Basil) -> care tips entry.
const openDetail = async () => {
  fireEvent.press(await screen.findByText('Basil'));
  return screen.findByRole('button', { name: t('plant.tips.button') });
};

describe('care tips entry on plant detail (FR-P02, FR-P04)', () => {
  test('the entry renders on plant detail for every account', async () => {
    await mountRoot(false, tipsStub());
    const entry = await openDetail();
    expect(entry).toBeTruthy();
    expect(screen.getByRole('button', { name: t('plant.photos.button') })).toBeTruthy();
  });

  test('free account: the entry opens the tips screen, shows the upgrade notice, and no tips are read', async () => {
    const tips = tipsStub();
    await mountRoot(false, tips);
    fireEvent.press(await openDetail());
    expect(await screen.findByRole('header', { name: t('tips.title') })).toBeTruthy();
    expect(await screen.findByText(t('tips.upgrade.title'))).toBeTruthy();
    expect(screen.getByText(t('tips.upgrade.body'))).toBeTruthy();
    expect(screen.queryByText(tipsFixture.items[0].text)).toBeNull();
    expect(tips.fetchPlantTips).not.toHaveBeenCalled();
  });

  test('free account: Go back returns to plant detail with the entry still there, and still no tips are read', async () => {
    const tips = tipsStub();
    await mountRoot(false, tips);
    fireEvent.press(await openDetail());
    await screen.findByText(t('tips.upgrade.title'));
    fireEvent.press(screen.getByRole('button', { name: t('a11y.back') }));
    expect(await screen.findByRole('button', { name: t('plant.tips.button') })).toBeTruthy();
    expect(tips.fetchPlantTips).not.toHaveBeenCalled();
  });

  test('premium account: the entry opens the tips screen and shows the stored tip for this plant', async () => {
    const tips = tipsStub();
    await mountRoot(true, tips);
    fireEvent.press(await openDetail());
    expect(await screen.findByText(tipsFixture.items[0].text)).toBeTruthy();
    expect(screen.queryByText(t('tips.upgrade.title'))).toBeNull();
    await waitFor(() => expect(tips.fetchPlantTips).toHaveBeenCalledWith(PLANT_ID));
    expect(tips.fetchPlantTips).toHaveBeenCalledTimes(1);
  });
});

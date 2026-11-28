// Care tips screen (task 4.A7): entitlement gate (FR-P04), loading / empty / error / ready states, tip text exactly as stored (FR-P02, NFR-06).
// Uses an in-memory auth service and a fake tips service. No Supabase call, no network, no device.
import React from 'react';
import { act, render, screen, fireEvent, waitFor } from '@testing-library/react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { AuthProvider } from '../auth/AuthContext';
import { createFakeAuth } from '../auth/fakeAuth';
import { PlantTipsScreen } from '../screens/PlantTipsScreen';
import { TipsError, type TipsService } from '../tips/tipsApi';
import type { PlantTips } from '../tips/tipsModel';
import { t } from '../i18n';

// Test fixtures (not app data): the texts below stand in for what the server stored.
const PLANT_ID = '6f1c2a3e-0000-4000-8000-000000000001';
const tipsFixture: PlantTips = {
  plantId: PLANT_ID,
  generatedAt: '2026-11-24T06:00:00Z',
  items: [
    { id: 'w-1', category: 'watering', text: 'Water when the top 2 cm of soil is dry.' },
    { id: 'l-1', category: 'light', text: 'Bright indirect light suits this plant.' },
    { id: 's-1', category: 'safety', text: 'Keep out of reach of pets.' },
  ],
};

const svcWith = (isPremium: boolean | 'error') => ({
  ...createFakeAuth(),
  getSession: async () => ({ id: 'user-test', email: 'test@example.invalid' }),
  getProfile: async () => { if (isPremium === 'error') throw new Error('boom'); return { displayName: null, isPremium }; },
});
const tipsStub = (fetchPlantTips: TipsService['fetchPlantTips']) => ({ fetchPlantTips: jest.fn(fetchPlantTips) }) as unknown as TipsService & { fetchPlantTips: jest.Mock };

const frame = { frame: { x: 0, y: 0, width: 390, height: 844 }, insets: { top: 0, left: 0, right: 0, bottom: 0 } };
const mountScreen = async (auth: ReturnType<typeof svcWith>, tips: TipsService) => {
  const onPremium = jest.fn();
  await render(<SafeAreaProvider initialMetrics={frame}><AuthProvider service={auth}><PlantTipsScreen tips={tips} plantId={PLANT_ID} plantName="Basil" onBack={() => undefined} onPremium={onPremium} /></AuthProvider></SafeAreaProvider>);
  return { onPremium };
};

describe('care tips: entitlement gate (FR-P04)', () => {
  test('free account sees the upgrade message and no tips are read; no tip text is shown', async () => {
    const tips = tipsStub(async () => tipsFixture);
    const { onPremium } = await mountScreen(svcWith(false), tips);
    expect(await screen.findByText(t('tips.upgrade.title'))).toBeTruthy();
    expect(screen.getByText(t('tips.upgrade.body'))).toBeTruthy();
    expect(tips.fetchPlantTips).not.toHaveBeenCalled();
    expect(screen.queryByText(tipsFixture.items[0].text)).toBeNull();
    expect(screen.queryByText(t('tips.empty'))).toBeNull();
    fireEvent.press(screen.getByRole('button', { name: t('profile.whatIsPremium') }));
    expect(onPremium).toHaveBeenCalled();
  });

  test('premium with zero rows (RLS returns nothing, no tips stored): empty state shown, no error, no upgrade notice', async () => {
    const tips = tipsStub(async () => null);
    await mountScreen(svcWith(true), tips);
    expect(await screen.findByText(t('tips.empty'))).toBeTruthy();
    expect(tips.fetchPlantTips).toHaveBeenCalledWith(PLANT_ID);
    expect(screen.queryByText(t('tips.error'))).toBeNull();
    expect(screen.queryByText(t('tips.upgrade.title'))).toBeNull();
    expect(screen.queryByText(t('tips.profileError'))).toBeNull();
  });

  test('plan cannot be read: error message and nothing is read (fails closed)', async () => {
    const tips = tipsStub(async () => tipsFixture);
    await mountScreen(svcWith('error'), tips);
    expect(await screen.findByText(t('tips.profileError'))).toBeTruthy();
    expect(tips.fetchPlantTips).not.toHaveBeenCalled();
    expect(screen.queryByText(t('tips.upgrade.title'))).toBeNull();
    expect(screen.queryByText(tipsFixture.items[0].text)).toBeNull();
  });
});

describe('care tips: states (FR-P02)', () => {
  test('loading: shows the loading line until the read answers; no tip before that', async () => {
    const tips = tipsStub(() => new Promise<PlantTips | null>(() => undefined));
    await mountScreen(svcWith(true), tips);
    expect(await screen.findByText(t('tips.loading'))).toBeTruthy();
    expect(tips.fetchPlantTips).toHaveBeenCalledWith(PLANT_ID);
    expect(screen.queryByText(tipsFixture.items[0].text)).toBeNull();
    expect(screen.queryByText(t('tips.empty'))).toBeNull();
  });

  test('empty: no stored tips says "No tips yet for this plant." and lists nothing', async () => {
    await mountScreen(svcWith(true), tipsStub(async () => null));
    expect(await screen.findByText(t('tips.empty'))).toBeTruthy();
    expect(screen.queryByText(t('tips.loading'))).toBeNull();
    expect(screen.queryByText(t('tips.error'))).toBeNull();
    expect(screen.queryByText(/Generated /)).toBeNull();
  });

  test('empty: a stored row with no items is shown as the same empty state', async () => {
    await mountScreen(svcWith(true), tipsStub(async () => ({ ...tipsFixture, items: [] })));
    expect(await screen.findByText(t('tips.empty'))).toBeTruthy();
    expect(screen.queryByText(/Generated /)).toBeNull();
  });

  test('error: shows the honest error copy (no cause named) and no tips; Try again reads again and then shows them', async () => {
    let fail = true;
    const tips = tipsStub(async () => { if (fail) throw new TipsError('network'); return tipsFixture; });
    await mountScreen(svcWith(true), tips);
    expect(await screen.findByText(t('tips.error'))).toBeTruthy();
    expect(screen.queryByText(tipsFixture.items[0].text)).toBeNull();
    expect(screen.queryByText(t('tips.empty'))).toBeNull();
    fail = false;
    await act(async () => { fireEvent.press(screen.getByRole('button', { name: t('common.tryAgain') })); });
    await waitFor(() => expect(screen.getByText(tipsFixture.items[0].text)).toBeTruthy());
    expect(screen.queryByText(t('tips.error'))).toBeNull();
    expect(tips.fetchPlantTips).toHaveBeenCalledTimes(2);
  });

  test('ready: shows each stored tip text and its category label, the plant name and the generated date', async () => {
    await mountScreen(svcWith(true), tipsStub(async () => tipsFixture));
    expect(await screen.findByText(tipsFixture.items[0].text)).toBeTruthy();
    expect(screen.getByText(tipsFixture.items[1].text)).toBeTruthy();
    expect(screen.getByText(tipsFixture.items[2].text)).toBeTruthy();
    expect(screen.getByText(t('tips.category.watering'))).toBeTruthy();
    expect(screen.getByText(t('tips.category.light'))).toBeTruthy();
    expect(screen.getByText(t('tips.category.safety'))).toBeTruthy();
    expect(screen.getByText(t('tips.intro', { plantName: 'Basil' }))).toBeTruthy();
    expect(screen.getByText(t('tips.generated', { date: '2026-11-24' }))).toBeTruthy();
    expect(screen.queryByText(t('tips.empty'))).toBeNull();
    expect(screen.queryByText(t('tips.error'))).toBeNull();
  });
});

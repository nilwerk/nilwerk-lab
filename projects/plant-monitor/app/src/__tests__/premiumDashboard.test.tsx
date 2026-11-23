// Premium dashboard screen (4.A6, S41): entitlement gate, loading / empty / error / ready states (FR-P01, FR-P04, NFR-06).
// Uses an in-memory auth service and a fake analytics service. No Supabase call, no network.
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { AuthProvider } from '../auth/AuthContext';
import { createFakeAuth } from '../auth/fakeAuth';
import { PremiumDashboardScreen } from '../screens/PremiumDashboardScreen';
import { AnalyticsError, type AnalyticsService } from '../analytics/analyticsApi';
import type { AnalyticsResponse, AnalyticsWindow, PlantAnalytics } from '../analytics/analyticsModel';
import { t } from '../i18n';

// Test fixtures (not app data).
const basil: PlantAnalytics = { plantId: 'p-basil', name: 'Basil', readingCount: 12, soilPct: { mean: 42.5, min: 20, max: 60 }, batteryMv: { mean: 3800, min: 3700, max: 3900 }, wateringEvents: 3, trend: { soilChangePct: 5, firstWeekMean: 40, lastWeekMean: 45 } };
const fixture = (windowDays: AnalyticsWindow, plants: PlantAnalytics[] = [basil]): AnalyticsResponse => ({ windowDays, plants });
const emptyPlant: PlantAnalytics = { ...basil, readingCount: 0, soilPct: null, batteryMv: null, wateringEvents: 0, trend: { soilChangePct: null, firstWeekMean: null, lastWeekMean: null } };

const svcWith = (isPremium: boolean | 'error') => ({
  ...createFakeAuth(),
  getSession: async () => ({ id: 'user-test', email: 'test@example.invalid' }),
  getProfile: async () => { if (isPremium === 'error') throw new Error('boom'); return { displayName: null, isPremium }; },
});
const analyticsStub = (fetchWindow: AnalyticsService['fetchWindow']) => ({ fetchWindow: jest.fn(fetchWindow) }) as unknown as AnalyticsService & { fetchWindow: jest.Mock };

const frame = { frame: { x: 0, y: 0, width: 390, height: 844 }, insets: { top: 0, left: 0, right: 0, bottom: 0 } };
const mountScreen = async (auth: ReturnType<typeof svcWith>, analytics: AnalyticsService) => {
  const onPremium = jest.fn();
  await render(<SafeAreaProvider initialMetrics={frame}><AuthProvider service={auth}><PremiumDashboardScreen analytics={analytics} onBack={() => undefined} onPremium={onPremium} /></AuthProvider></SafeAreaProvider>);
  return { onPremium };
};

describe('premium dashboard: entitlement gate (FR-P04)', () => {
  test('free account sees the upgrade message and the analytics endpoint is never called', async () => {
    const a = analyticsStub(async (w) => fixture(w));
    const { onPremium } = await mountScreen(svcWith(false), a);
    expect(await screen.findByText(t('dashboard.upgrade.title'))).toBeTruthy();
    expect(screen.getByText(t('dashboard.upgrade.body'))).toBeTruthy();
    expect(a.fetchWindow).not.toHaveBeenCalled();
    expect(screen.queryByText('Basil')).toBeNull();
    fireEvent.press(screen.getByRole('button', { name: t('profile.whatIsPremium') }));
    expect(onPremium).toHaveBeenCalled();
  });

  test('plan cannot be read: error message, nothing loaded (fails closed)', async () => {
    const a = analyticsStub(async (w) => fixture(w));
    await mountScreen(svcWith('error'), a);
    expect(await screen.findByText(t('dashboard.profileError'))).toBeTruthy();
    expect(a.fetchWindow).not.toHaveBeenCalled();
    expect(screen.queryByText(t('dashboard.upgrade.title'))).toBeNull();
  });

  test('server answers premium_required although the app thought premium: shows the upgrade state, no data', async () => {
    const a = analyticsStub(async () => { throw new AnalyticsError('premium_required'); });
    await mountScreen(svcWith(true), a);
    expect(await screen.findByText(t('dashboard.upgrade.title'))).toBeTruthy();
    expect(screen.queryByText(/Soil moisture/)).toBeNull();
  });

});

describe('premium dashboard: states (FR-P01)', () => {
  test('loading: shows the loading line until both windows answer', async () => {
    const a = analyticsStub(() => new Promise<AnalyticsResponse>(() => undefined));
    await mountScreen(svcWith(true), a);
    expect(await screen.findByText(t('dashboard.loading'))).toBeTruthy();
    expect(a.fetchWindow).toHaveBeenCalledWith(30);
    expect(a.fetchWindow).toHaveBeenCalledWith(90);
    expect(screen.queryByText(/Soil moisture/)).toBeNull();
  });

  test('ready: renders the 30- and 90-day values exactly as the response has them', async () => {
    const a = analyticsStub(async (w) => fixture(w));
    await mountScreen(svcWith(true), a);
    expect(await screen.findByText(t('dashboard.window.title', { days: 30 }))).toBeTruthy();
    expect(screen.getByText(t('dashboard.window.title', { days: 90 }))).toBeTruthy();
    expect(screen.getAllByText('Basil')).toHaveLength(2);
    expect(screen.getAllByText('Soil moisture: mean 42.5 %, min 20.0 %, max 60.0 %')).toHaveLength(2);
    expect(screen.getAllByText('Battery: mean 3.80 V, min 3.70 V, max 3.90 V')).toHaveLength(2);
    expect(screen.getAllByText('Watering events: 3')).toHaveLength(2);
    expect(screen.getAllByText('Trend: soil +5.0 points (first week 40.0 %, last week 45.0 %)')).toHaveLength(2);
    expect(screen.getAllByText('12 readings')).toHaveLength(2);
  });

  test('empty: no plants says so for both windows', async () => {
    await mountScreen(svcWith(true), analyticsStub(async (w) => fixture(w, [])));
    expect(await screen.findAllByText(t('dashboard.noPlants'))).toHaveLength(2);
  });

  test('empty: plants without any reading say so for both windows and list no values', async () => {
    await mountScreen(svcWith(true), analyticsStub(async (w) => fixture(w, [emptyPlant])));
    expect(await screen.findAllByText(t('dashboard.noReadings'))).toHaveLength(2);
    expect(screen.queryByText('Basil')).toBeNull();
  });

  test('error: shows the error message; Try again fetches again and then shows the data', async () => {
    let fail = true;
    const a = analyticsStub(async (w) => { if (fail) throw new AnalyticsError('network'); return fixture(w); });
    await mountScreen(svcWith(true), a);
    expect(await screen.findByText(t('dashboard.error'))).toBeTruthy();
    expect(screen.queryByText(/Soil moisture/)).toBeNull();
    fail = false;
    fireEvent.press(screen.getByRole('button', { name: t('common.tryAgain') }));
    await waitFor(() => expect(screen.getAllByText('Basil').length).toBeGreaterThan(0));
    expect(screen.queryByText(t('dashboard.error'))).toBeNull();
  });
});

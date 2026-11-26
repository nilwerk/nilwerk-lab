// Premium dashboard screen (4.A6 states and gate; 4.A6b daily line chart, FR-P01 with ADR-018 daily series): entitlement gate, loading / empty / error / ready states,
// 30- and 90-day line chart with gaps (FR-P01, FR-P04, NFR-06). Uses an in-memory auth service and a fake analytics service. No Supabase call, no network.
import React from 'react';
import { act, render, screen, fireEvent, waitFor } from '@testing-library/react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { AuthProvider } from '../auth/AuthContext';
import { createFakeAuth } from '../auth/fakeAuth';
import { PremiumDashboardScreen } from '../screens/PremiumDashboardScreen';
import { AnalyticsError, type AnalyticsService } from '../analytics/analyticsApi';
import type { AnalyticsResponse, AnalyticsWindow, DailyPoint, PlantAnalytics } from '../analytics/analyticsModel';
import { t } from '../i18n';

// Test fixtures (not app data).
type Base = Omit<PlantAnalytics, 'daily'>;
const basil: Base = { plantId: 'p-basil', name: 'Basil', readingCount: 12, soilPct: { mean: 42.5, min: 20, max: 60 }, batteryMv: { mean: 3800, min: 3700, max: 3900 }, wateringEvents: 3, trend: { soilChangePct: 5, firstWeekMean: 40, lastWeekMean: 45 } };
const END_MS = Date.parse('2026-11-24T00:00:00Z');   // fixed "today" of the fixtures (UTC)
const DAY_MS = 86_400_000;
const dayAt = (windowDays: number, i: number): string => new Date(END_MS - (windowDays - 1 - i) * DAY_MS).toISOString().slice(0, 10);
/** Daily series of windowDays items with one soil mean and count on every day (null soil = no value). */
const series = (windowDays: AnalyticsWindow, soil: number | null = 42.5, count = 1): DailyPoint[] =>
  Array.from({ length: windowDays }, (_, i) => ({ date: dayAt(windowDays, i), soilPctMean: soil, batteryMvMean: 3800, readingCount: count }));
/** Days 10, 11 and 12 are gaps: an empty day, a day with readings but no soil value, and a real zero. Other days 40 %. */
const gapSeries = (windowDays: AnalyticsWindow): DailyPoint[] => series(windowDays, 40).map((d, i) => {
  if (i === 10) return { ...d, soilPctMean: null, readingCount: 0 };
  if (i === 11) return { ...d, soilPctMean: null, readingCount: 5 };
  if (i === 12) return { ...d, soilPctMean: 0, readingCount: 13 };
  return d;
});
const fixture = (windowDays: AnalyticsWindow, plants: Array<Base & { daily?: DailyPoint[] }> = [basil]): AnalyticsResponse => ({
  windowDays,
  plants: plants.map(({ daily, ...p }) => ({ ...p, daily: daily ?? series(windowDays, p.soilPct ? p.soilPct.mean : null) })),
});
const emptyPlant: Base = { ...basil, readingCount: 0, soilPct: null, batteryMv: null, wateringEvents: 0, trend: { soilChangePct: null, firstWeekMean: null, lastWeekMean: null } };

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
/** The chart is measured by onLayout (no layout pass runs in jest): the test calls the handler with a 300 px width, inside act. */
const measure = async (el: { props: { onLayout?: (e: unknown) => void } }) => {
  await act(async () => { el.props.onLayout?.({ nativeEvent: { layout: { x: 0, y: 0, width: 300, height: 160 } } }); });
};

describe('premium dashboard: entitlement gate (FR-P04)', () => {
  test('free account sees the upgrade message and the analytics endpoint is never called; no chart is shown', async () => {
    const a = analyticsStub(async (w) => fixture(w));
    const { onPremium } = await mountScreen(svcWith(false), a);
    expect(await screen.findByText(t('dashboard.upgrade.title'))).toBeTruthy();
    expect(screen.getByText(t('dashboard.upgrade.body'))).toBeTruthy();
    expect(a.fetchWindow).not.toHaveBeenCalled();
    expect(screen.queryByText('Basil')).toBeNull();
    expect(screen.queryByText(t('dashboard.daily.title'))).toBeNull();
    expect(screen.queryByTestId('daily-chart')).toBeNull();
    fireEvent.press(screen.getByRole('button', { name: t('profile.whatIsPremium') }));
    expect(onPremium).toHaveBeenCalled();
  });

  test('plan cannot be read: error message, nothing loaded (fails closed)', async () => {
    const a = analyticsStub(async (w) => fixture(w));
    await mountScreen(svcWith('error'), a);
    expect(await screen.findByText(t('dashboard.profileError'))).toBeTruthy();
    expect(a.fetchWindow).not.toHaveBeenCalled();
    expect(screen.queryByText(t('dashboard.upgrade.title'))).toBeNull();
    expect(screen.queryByTestId('daily-chart')).toBeNull();
  });

  test('server answers premium_required although the app thought premium: shows the upgrade state, no data and no chart', async () => {
    const a = analyticsStub(async () => { throw new AnalyticsError('premium_required'); });
    await mountScreen(svcWith(true), a);
    expect(await screen.findByText(t('dashboard.upgrade.title'))).toBeTruthy();
    expect(screen.queryByText(/Soil moisture/)).toBeNull();
    expect(screen.queryByTestId('daily-chart')).toBeNull();
  });

});

describe('premium dashboard: states (FR-P01)', () => {
  test('loading: shows the loading line until both windows answer; no chart before that', async () => {
    const a = analyticsStub(() => new Promise<AnalyticsResponse>(() => undefined));
    await mountScreen(svcWith(true), a);
    expect(await screen.findByText(t('dashboard.loading'))).toBeTruthy();
    expect(a.fetchWindow).toHaveBeenCalledWith(30);
    expect(a.fetchWindow).toHaveBeenCalledWith(90);
    expect(screen.queryByText(/Soil moisture/)).toBeNull();
    expect(screen.queryByText(t('dashboard.daily.title'))).toBeNull();
  });

  test('ready: renders the 30- and 90-day values exactly as the response has them', async () => {
    const a = analyticsStub(async (w) => fixture(w));
    await mountScreen(svcWith(true), a);
    expect(await screen.findByText(t('dashboard.window.title', { days: 30 }))).toBeTruthy();
    expect(screen.getByText(t('dashboard.window.title', { days: 90 }))).toBeTruthy();
    expect(screen.getAllByText('Basil')).toHaveLength(3);   // daily section header + the two window sections
    expect(screen.getAllByText('Soil moisture: mean 42.5 %, min 20.0 %, max 60.0 %')).toHaveLength(2);
    expect(screen.getAllByText('Battery: mean 3.80 V, min 3.70 V, max 3.90 V')).toHaveLength(2);
    expect(screen.getAllByText('Watering events: 3')).toHaveLength(2);
    expect(screen.getAllByText('Trend: soil +5.0 points (first week 40.0 %, last week 45.0 %)')).toHaveLength(2);
    expect(screen.getAllByText('12 readings')).toHaveLength(2);
  });

  test('empty: no plants says so for the chart section and both windows', async () => {
    await mountScreen(svcWith(true), analyticsStub(async (w) => fixture(w, [])));
    expect(await screen.findAllByText(t('dashboard.noPlants'))).toHaveLength(3);
    expect(screen.queryByTestId('daily-chart')).toBeNull();
  });

  test('empty: plants without any reading say so and list no values or chart', async () => {
    await mountScreen(svcWith(true), analyticsStub(async (w) => fixture(w, [emptyPlant])));
    expect(await screen.findAllByText(t('dashboard.noReadings'))).toHaveLength(3);
    expect(screen.queryByText('Basil')).toBeNull();
    expect(screen.queryByTestId('daily-chart')).toBeNull();
  });

  test('error: shows the error message and no chart; Try again fetches again and then shows the data', async () => {
    let fail = true;
    const a = analyticsStub(async (w) => { if (fail) throw new AnalyticsError('network'); return fixture(w); });
    await mountScreen(svcWith(true), a);
    expect(await screen.findByText(t('dashboard.error'))).toBeTruthy();
    expect(screen.queryByText(/Soil moisture/)).toBeNull();
    expect(screen.queryByTestId('daily-chart')).toBeNull();
    fail = false;
    fireEvent.press(screen.getByRole('button', { name: t('common.tryAgain') }));
    await waitFor(() => expect(screen.getAllByText('Basil').length).toBeGreaterThan(0));
    expect(screen.queryByText(t('dashboard.error'))).toBeNull();
    expect(screen.getByTestId('daily-chart')).toBeTruthy();
  });
});

describe('premium dashboard: daily line chart (FR-P01, 4.A6b)', () => {
  test('30 and 90 windows: the 30-day chart is shown first, the switch shows the 90-day chart from the 90 daily items', async () => {
    const a = analyticsStub(async (w) => fixture(w));
    await mountScreen(svcWith(true), a);
    const chart30 = await screen.findByTestId('daily-chart');
    expect(chart30.props.accessibilityLabel).toBe(`Daily soil moisture line, 30 days from ${dayAt(30, 0)} to 2026-11-24: 30 days with a mean value, 0 days without a soil reading (shown as gaps).`);
    expect(dayAt(30, 0)).toBe('2026-10-26');
    fireEvent.press(screen.getByRole('button', { name: t('dashboard.daily.switch', { days: 90 }) }));
    const chart90 = await screen.findByTestId('daily-chart');
    expect(chart90.props.accessibilityLabel).toContain('90 days from 2026-08-27 to 2026-11-24: 90 days with a mean value');
    expect(dayAt(90, 0)).toBe('2026-08-27');
  });

  test('gap days: no dot and no line across them; a real 0 is drawn; the line breaks at the gap', async () => {
    const a = analyticsStub(async (w) => fixture(w, [{ ...basil, daily: gapSeries(w) }]));
    await mountScreen(svcWith(true), a);
    const chart = await screen.findByTestId('daily-chart');
    await measure(chart);
    expect(chart.props.accessibilityLabel).toContain('28 days with a mean value, 2 days without a soil reading');
    expect(screen.getAllByTestId('daily-dot')).toHaveLength(28);      // 30 days minus the 2 null soil days; the 0 % day has a dot
    expect(screen.getAllByTestId('daily-segment')).toHaveLength(26);  // 29 neighbour pairs minus the 3 that touch a gap
  });

  test('reading counts are not drawn as values: a day with 13 readings adds no label and no point of its own', async () => {
    const a = analyticsStub(async (w) => fixture(w, [{ ...basil, daily: gapSeries(w) }]));
    await mountScreen(svcWith(true), a);
    await measure(await screen.findByTestId('daily-chart'));
    expect(screen.queryByText('13')).toBeNull();
    expect(screen.queryByText('5')).toBeNull();
    expect(screen.queryByText('13 readings')).toBeNull();
    expect(screen.getAllByTestId('daily-dot')).toHaveLength(28);      // dots come from soil means only, not from counts
  });

  test('all-null window: says there are no soil values in that window, with no chart; the other window still draws', async () => {
    const a = analyticsStub(async (w) => fixture(w, [{ ...basil, daily: w === 30 ? series(30, null, 2) : series(90, 40) }]));
    await mountScreen(svcWith(true), a);
    expect(await screen.findByText(t('dashboard.daily.noValues', { days: 30 }))).toBeTruthy();
    expect(screen.queryByTestId('daily-chart')).toBeNull();
    fireEvent.press(screen.getByRole('button', { name: t('dashboard.daily.switch', { days: 90 }) }));
    expect(await screen.findByTestId('daily-chart')).toBeTruthy();
    expect(screen.queryByText(t('dashboard.daily.noValues', { days: 30 }))).toBeNull();
  });

  test('a plant with no readings at all in the window is listed as "no readings", not as an empty chart', async () => {
    await mountScreen(svcWith(true), analyticsStub(async (w) => fixture(w, [emptyPlant])));
    expect(await screen.findByText(t('dashboard.daily.title'))).toBeTruthy();
    expect(screen.queryByTestId('daily-chart')).toBeNull();
  });
});

describe('premium dashboard: graphs and gaps (FR-P01)', () => {
  const rangeLabel = 'Soil moisture range from 20.0 % to 60.0 %, mean 42.5 %';
  const trendLabel = 'Soil moisture trend graph: first week mean 40.0 %, last week mean 45.0 %';

  test('ready: a range graph and a first-week / last-week trend graph per plant and window, from the response values', async () => {
    await mountScreen(svcWith(true), analyticsStub(async (w) => fixture(w)));
    expect(await screen.findAllByLabelText(rangeLabel)).toHaveLength(2);
    expect(screen.getAllByLabelText(trendLabel)).toHaveLength(2);
    expect(screen.getAllByText(t('dashboard.trend.first'))).toHaveLength(2);
    expect(screen.getAllByText(t('dashboard.trend.last'))).toHaveLength(2);
    expect(screen.getAllByText('40.0 %')).toHaveLength(2);
    expect(screen.getAllByText('45.0 %')).toHaveLength(2);
  });

  test('gaps: soil present but no trend (a week is empty) shows the soil graph and "not enough readings", no trend graph', async () => {
    const gap: Base = { ...basil, trend: { soilChangePct: null, firstWeekMean: 40, lastWeekMean: null } };
    await mountScreen(svcWith(true), analyticsStub(async (w) => fixture(w, [gap])));
    expect(await screen.findAllByLabelText(rangeLabel)).toHaveLength(2);
    expect(screen.getAllByText(t('dashboard.plant.noTrend'))).toHaveLength(2);
    expect(screen.queryByLabelText(trendLabel)).toBeNull();
  });

  test('gaps: no soil sample and no battery sample shows the notice and no range graph, without crashing', async () => {
    const noSoil: Base = { ...basil, readingCount: 1, soilPct: null, batteryMv: null, trend: { soilChangePct: null, firstWeekMean: null, lastWeekMean: null } };
    await mountScreen(svcWith(true), analyticsStub(async (w) => fixture(w, [noSoil])));
    expect(await screen.findAllByText(t('dashboard.plant.noSoil'))).toHaveLength(2);
    expect(screen.queryByLabelText(/Soil moisture range/)).toBeNull();
    expect(screen.queryByLabelText(/Soil moisture trend graph/)).toBeNull();
    expect(screen.getAllByText(t('dashboard.plant.noTrend'))).toHaveLength(2);
  });

  test('gaps: a plant with no soil readings gets no range graph and the rest still renders', async () => {
    const mixed: Base[] = [{ ...basil, plantId: 'p-a', name: 'Aloe', soilPct: null }, { ...basil, plantId: 'p-b', name: 'Mint' }];
    await mountScreen(svcWith(true), analyticsStub(async (w) => fixture(w, mixed)));
    expect(await screen.findAllByText('Mint')).toHaveLength(3);
    expect(screen.getAllByText('Aloe')).toHaveLength(3);
    expect(screen.getAllByLabelText(rangeLabel)).toHaveLength(2);
    expect(screen.getAllByLabelText(trendLabel)).toHaveLength(4);
  });
});

// Premium analytics client and response parser (4.A6 consumes 4.B4; 4.A6b consumes the daily series, ADR-018; FR-P01, FR-P04, NFR-06).
// Fake fetch only: no live Supabase or edge call. Wire fixtures are hand-written literals or a fixed-date builder (the parser is never used to make its own expectations).
import { createAnalyticsClient, analyticsUrl, AnalyticsError } from '../analytics/analyticsApi';
import { parseAnalyticsResponse } from '../analytics/analyticsModel';

// Fixed end day (UTC), so every date in the fixtures is a literal in the expectations below.
const END_DAY_MS = Date.parse('2026-11-24T00:00:00Z');
const DAY_MS = 86_400_000;
/** Wire daily series of n days, oldest first, ending 2026-11-24 (UTC). Each item gets the given soil mean and count. */
type WireDay = { date: string; soil_pct_mean: number | null; battery_mv_mean: number | null; reading_count: number };
const wireDaily = (n: number, soil: number | null = 42.5, count = 1): WireDay[] =>
  Array.from({ length: n }, (_, i) => ({
    date: new Date(END_DAY_MS - (n - 1 - i) * DAY_MS).toISOString().slice(0, 10),
    soil_pct_mean: soil, battery_mv_mean: 3800, reading_count: count,
  }));

const plantOk = {
  plant_id: '11111111-1111-4111-8111-111111111111', name: 'Basil', reading_count: 12,
  soil_pct: { mean: 42.5, min: 20, max: 60 }, battery_mv: { mean: 3800, min: 3700, max: 3900 },
  watering_events: 3, trend: { soil_change_pct: 5, first_week_mean: 40, last_week_mean: 45 },
  daily: wireDaily(30),
};
const body30 = { window_days: 30, plants: [plantOk] };
const reply = (status: number, json: unknown = null) => ({ status, json: async () => json }) as unknown as Response;
const deps = (fetchImpl: jest.Mock, token: string | null = 'jwt-test') => ({
  baseUrl: 'https://example.invalid/', publishableKey: 'pk-test', getAccessToken: async () => token, fetchImpl: fetchImpl as unknown as typeof fetch,
});

describe('analytics client', () => {
  test('builds the window URL on the functions path and sends the user JWT and publishable key', async () => {
    const f = jest.fn(async () => reply(200, body30));
    const r = await createAnalyticsClient(deps(f)).fetchWindow(30);
    expect(analyticsUrl('https://example.invalid/', 30)).toBe('https://example.invalid/functions/v1/analytics?window=30');
    expect(f).toHaveBeenCalledWith('https://example.invalid/functions/v1/analytics?window=30', expect.objectContaining({
      method: 'GET', headers: expect.objectContaining({ Authorization: 'Bearer jwt-test', apikey: 'pk-test' }),
    }));
    expect(r.windowDays).toBe(30);
    expect(r.plants[0]).toEqual({
      plantId: plantOk.plant_id, name: 'Basil', readingCount: 12, soilPct: { mean: 42.5, min: 20, max: 60 },
      batteryMv: { mean: 3800, min: 3700, max: 3900 }, wateringEvents: 3, trend: { soilChangePct: 5, firstWeekMean: 40, lastWeekMean: 45 },
      daily: r.plants[0].daily,
    });
    expect(r.plants[0].daily).toHaveLength(30);
    expect(r.plants[0].daily?.[0]).toEqual({ date: '2026-10-26', soilPctMean: 42.5, batteryMvMean: 3800, readingCount: 1 });
    expect(r.plants[0].daily?.[29]).toEqual({ date: '2026-11-24', soilPctMean: 42.5, batteryMvMean: 3800, readingCount: 1 });
  });

  test('no session: rejects as unauthorized and never calls the network', async () => {
    const f = jest.fn();
    await expect(createAnalyticsClient(deps(f, null)).fetchWindow(90)).rejects.toMatchObject({ code: 'unauthorized' });
    expect(f).not.toHaveBeenCalled();
  });

  test.each([
    [403, 'premium_required'], [401, 'unauthorized'], [500, 'server'], [503, 'server'], [404, 'unknown'],
  ])('HTTP %i maps to %s', async (status, code) => {
    await expect(createAnalyticsClient(deps(jest.fn(async () => reply(status, {})))).fetchWindow(30)).rejects.toMatchObject({ code });
  });

  test('fetch failure maps to network', async () => {
    await expect(createAnalyticsClient(deps(jest.fn(async () => { throw new Error('offline'); }))).fetchWindow(30)).rejects.toBeInstanceOf(AnalyticsError);
    await expect(createAnalyticsClient(deps(jest.fn(async () => { throw new Error('offline'); }))).fetchWindow(30)).rejects.toMatchObject({ code: 'network' });
  });

  test('a 200 body that does not match the contract is bad_response, never a partial result', async () => {
    const wrongWindow = jest.fn(async () => reply(200, { window_days: 90, plants: [] }));
    await expect(createAnalyticsClient(deps(wrongWindow)).fetchWindow(30)).rejects.toMatchObject({ code: 'bad_response' });
    const missingTrend = jest.fn(async () => reply(200, { window_days: 30, plants: [{ ...plantOk, trend: undefined }] }));
    await expect(createAnalyticsClient(deps(missingTrend)).fetchWindow(30)).rejects.toMatchObject({ code: 'bad_response' });
  });
});

describe('analytics response parser', () => {
  test('accepts null soil, battery and trend values and an empty plant list', () => {
    const r = parseAnalyticsResponse({ window_days: 90, plants: [{ ...plantOk, reading_count: 0, soil_pct: null, battery_mv: null, watering_events: 0, trend: { soil_change_pct: null, first_week_mean: null, last_week_mean: null }, daily: wireDaily(90, null, 0) }] }, 90);
    expect(r?.plants[0]).toMatchObject({ readingCount: 0, soilPct: null, batteryMv: null, trend: { soilChangePct: null } });
    expect(parseAnalyticsResponse({ window_days: 30, plants: [] }, 30)).toEqual({ windowDays: 30, plants: [] });
  });

  test('daily series: null day stays null (a gap), a real 0 stays 0, and the 90-day window needs 90 items', () => {
    const daily = wireDaily(90, 40);
    daily[10] = { ...daily[10], soil_pct_mean: null, battery_mv_mean: null, reading_count: 0 };   // empty day
    daily[11] = { ...daily[11], soil_pct_mean: 0, reading_count: 2 };                            // real zero, not a gap
    daily[12] = { ...daily[12], soil_pct_mean: null, reading_count: 3 };                         // readings but no soil value
    const r = parseAnalyticsResponse({ window_days: 90, plants: [{ ...plantOk, daily }] }, 90);
    expect(r?.plants[0].daily).toHaveLength(90);
    expect(r?.plants[0].daily?.[10]).toEqual({ date: daily[10].date, soilPctMean: null, batteryMvMean: null, readingCount: 0 });
    expect(r?.plants[0].daily?.[11]).toEqual({ date: daily[11].date, soilPctMean: 0, batteryMvMean: 3800, readingCount: 2 });
    expect(r?.plants[0].daily?.[12]).toEqual({ date: daily[12].date, soilPctMean: null, batteryMvMean: 3800, readingCount: 3 });
    expect(parseAnalyticsResponse({ window_days: 90, plants: [{ ...plantOk, daily: wireDaily(30) }] }, 90)).toBeNull();
  });

  test('daily series: a series that is the wrong length, not consecutive, or has a bad value is rejected (whole response)', () => {
    const ok = wireDaily(30);
    const wrap = (daily: unknown) => parseAnalyticsResponse({ window_days: 30, plants: [{ ...plantOk, daily }] }, 30);
    expect(wrap(ok)).not.toBeNull();
    expect(wrap(ok.slice(1))).toBeNull();                                                     // 29 items
    expect(wrap([...ok, ok[0]])).toBeNull();                                                  // 31 items
    expect(wrap(ok.map((d, i) => (i === 5 ? { ...d, date: '2026-11-02' } : d)))).toBeNull();  // gap in the dates (skips Oct 31)
    expect(wrap(ok.map((d, i) => (i === 5 ? { ...d, date: '2026-10-30' } : d)))).toBeNull();  // repeated date
    expect(wrap(ok.map((d, i) => (i === 3 ? { ...d, date: '2026-02-30' } : d)))).toBeNull();  // not a real day
    expect(wrap(ok.map((d, i) => (i === 3 ? { ...d, date: '26-10-29' } : d)))).toBeNull();    // wrong format
    expect(wrap(ok.map((d, i) => (i === 3 ? { ...d, reading_count: -1 } : d)))).toBeNull();
    expect(wrap(ok.map((d, i) => (i === 3 ? { ...d, reading_count: 1.5 } : d)))).toBeNull();
    expect(wrap(ok.map((d, i) => (i === 3 ? { ...d, soil_pct_mean: NaN } : d)))).toBeNull();
    expect(wrap(ok.map((d, i) => (i === 3 ? { date: d.date, soil_pct_mean: 1 } : d)))).toBeNull();  // missing fields
    expect(wrap(null)).toBeNull();                                                            // present but not an array: malformed, whole response rejected
  });

  test('daily key absent (older backend): the response is accepted, aggregates intact, daily is null (not available yet)', () => {
    const { daily: _absent, ...noDaily } = plantOk;
    const r = parseAnalyticsResponse({ window_days: 30, plants: [noDaily] }, 30);
    expect(r?.plants[0]).toMatchObject({ readingCount: 12, soilPct: { mean: 42.5, min: 20, max: 60 }, batteryMv: { mean: 3800, min: 3700, max: 3900 }, wateringEvents: 3, daily: null });
    expect(r?.plants[0].trend).toEqual({ soilChangePct: 5, firstWeekMean: 40, lastWeekMean: 45 });
  });

  test('daily key absent through the client: resolves with the aggregates (no bad_response, no error state)', async () => {
    const { daily: _absent, ...noDaily } = plantOk;
    const r = await createAnalyticsClient(deps(jest.fn(async () => reply(200, { window_days: 30, plants: [noDaily] })))).fetchWindow(30);
    expect(r.plants[0]).toMatchObject({ name: 'Basil', soilPct: { mean: 42.5 }, daily: null });
  });

  test('rejects non-finite numbers, negative counts and a missing plant id', () => {
    expect(parseAnalyticsResponse({ window_days: 30, plants: [{ ...plantOk, reading_count: -1 }] }, 30)).toBeNull();
    expect(parseAnalyticsResponse({ window_days: 30, plants: [{ ...plantOk, soil_pct: { mean: NaN, min: 1, max: 2 } }] }, 30)).toBeNull();
    expect(parseAnalyticsResponse({ window_days: 30, plants: [{ ...plantOk, plant_id: undefined }] }, 30)).toBeNull();
    expect(parseAnalyticsResponse('nope', 30)).toBeNull();
  });
});

// Premium analytics client and response parser (4.A6, consumes 4.B4; FR-P01, FR-P04, NFR-06). Fake fetch only: no live Supabase or edge call.
import { createAnalyticsClient, analyticsUrl, AnalyticsError } from '../analytics/analyticsApi';
import { parseAnalyticsResponse } from '../analytics/analyticsModel';

const plantOk = {
  plant_id: '11111111-1111-4111-8111-111111111111', name: 'Basil', reading_count: 12,
  soil_pct: { mean: 42.5, min: 20, max: 60 }, battery_mv: { mean: 3800, min: 3700, max: 3900 },
  watering_events: 3, trend: { soil_change_pct: 5, first_week_mean: 40, last_week_mean: 45 },
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
    });
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
    const r = parseAnalyticsResponse({ window_days: 90, plants: [{ ...plantOk, reading_count: 0, soil_pct: null, battery_mv: null, watering_events: 0, trend: { soil_change_pct: null, first_week_mean: null, last_week_mean: null } }] }, 90);
    expect(r?.plants[0]).toMatchObject({ readingCount: 0, soilPct: null, batteryMv: null, trend: { soilChangePct: null } });
    expect(parseAnalyticsResponse({ window_days: 30, plants: [] }, 30)).toEqual({ windowDays: 30, plants: [] });
  });

  test('rejects non-finite numbers, negative counts and a missing plant id', () => {
    expect(parseAnalyticsResponse({ window_days: 30, plants: [{ ...plantOk, reading_count: -1 }] }, 30)).toBeNull();
    expect(parseAnalyticsResponse({ window_days: 30, plants: [{ ...plantOk, soil_pct: { mean: NaN, min: 1, max: 2 } }] }, 30)).toBeNull();
    expect(parseAnalyticsResponse({ window_days: 30, plants: [{ ...plantOk, plant_id: undefined }] }, 30)).toBeNull();
    expect(parseAnalyticsResponse('nope', 30)).toBeNull();
  });
});

// Mock build only (EXPO_PUBLIC_MOCK_AUTH=1): premium dashboard data from a fixed, hand-written pattern. Not a real measurement.
// The values are generated from the day index so every run is the same; the window ends today (UTC), as the real endpoint does.
import type { AnalyticsService } from './analyticsApi';
import type { AnalyticsResponse, AnalyticsWindow, DailyPoint, PlantAnalytics } from './analyticsModel';

const DAY_MS = 24 * 3600_000;

/** window days ending today (UTC), oldest first; every 9th day has no reading (a gap, never zero). */
export function fakeDaily(windowDays: AnalyticsWindow, now: Date): DailyPoint[] {
  const end = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate());
  const out: DailyPoint[] = [];
  for (let i = windowDays - 1; i >= 0; i--) {
    const d = new Date(end - i * DAY_MS);
    const gap = i % 9 === 0;
    out.push({
      date: d.toISOString().slice(0, 10),
      soilPctMean: gap ? null : 30 + ((windowDays - 1 - i) * 7) % 40,
      batteryMvMean: gap ? null : 3800 - ((windowDays - 1 - i) % 5) * 10,
      readingCount: gap ? 0 : 24,
    });
  }
  return out;
}

export function fakeAnalyticsResponse(windowDays: AnalyticsWindow, now: Date): AnalyticsResponse {
  const daily = fakeDaily(windowDays, now);
  const soil = daily.map((d) => d.soilPctMean).filter((v): v is number => v !== null);
  const bat = daily.map((d) => d.batteryMvMean).filter((v): v is number => v !== null);
  const mean = (xs: number[]) => xs.reduce((a, b) => a + b, 0) / xs.length;
  const plant: PlantAnalytics = {
    plantId: 'p-basil',
    name: 'Basil',
    readingCount: daily.reduce((a, d) => a + d.readingCount, 0),
    soilPct: { mean: mean(soil), min: Math.min(...soil), max: Math.max(...soil) },
    batteryMv: { mean: mean(bat), min: Math.min(...bat), max: Math.max(...bat) },
    wateringEvents: 3,
    trend: { soilChangePct: 2.5, firstWeekMean: 41, lastWeekMean: 43.5 },
    daily,
  };
  return { windowDays, plants: [plant] };
}

/** Analytics service for the mock build. */
export function createFakeAnalytics(now: () => Date = () => new Date()): AnalyticsService {
  return { fetchWindow: async (windowDays) => fakeAnalyticsResponse(windowDays, now()) };
}

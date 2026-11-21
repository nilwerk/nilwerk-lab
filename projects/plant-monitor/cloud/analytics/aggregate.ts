// Analytics (task 4.B4): 30/90-day aggregates, trend, watering events and plant comparison.
// Requirements: FR-P01 (30/90-day history, trends, watering events, comparison), FR-P04 (premium only, ADR-008).
// Pure TypeScript: no database, no network, no clock (the caller passes `nowMs`). Runs in Deno and Node 22.6+.
// The HTTP endpoint (not built in 4.B4 yet) calls public.is_premium() first and maps readings rows to AnalyticsReading.

export const DAY_MS = 86_400_000;
const WEEK_MS = 7 * DAY_MS;

/** TO CONFIRM (open decision A-115): soil percent points one sample step must rise to count as a watering event. Strictly above. */
export const WATERING_RISE_PCT = 10;
/** TO CONFIRM (open decision A-115): two consecutive samples further apart than this are not compared (a rise across a long gap is not a watering). */
export const MAX_EVENT_GAP_MS = 2 * 3_600_000;

export const ANALYTICS_WINDOWS_DAYS = [30, 90] as const;
export type AnalyticsWindow = (typeof ANALYTICS_WINDOWS_DAYS)[number];

/** One row of `readings`, camelCased. Only `plausible` rows are used (db-schema: implausible samples are kept but excluded). */
export interface AnalyticsReading {
  ts: string;              // ISO 8601, readings.ts
  plantId: string | null;  // readings.plant_id (null = not assigned to a plant)
  moisturePct: number | null; // readings.moisture_pct, relative 0-100
  vbatMv: number | null;   // readings.vbat_mv
  plausible: boolean;      // readings.plausible
}
export interface AnalyticsPlant { id: string; name: string }

export interface Stat { mean: number; min: number; max: number }
export interface PlantAnalytics {
  plantId: string;
  name: string;
  windowDays: number;
  readingCount: number;        // plausible readings inside the window (0 = no data)
  soilPct: Stat | null;        // null when no usable soil reading
  batteryMv: Stat | null;      // null when no usable battery reading
  wateringEvents: number;
  trend: {
    soilChangePct: number | null;  // lastWeekMean - firstWeekMean, in soil percent points; null if either week is empty
    firstWeekMean: number | null;
    lastWeekMean: number | null;
  };
}

function stat(values: number[]): Stat | null {
  if (values.length === 0) return null;
  let sum = 0, min = Infinity, max = -Infinity;
  for (const v of values) { sum += v; if (v < min) min = v; if (v > max) max = v; }
  return { mean: sum / values.length, min, max };
}

function mean(values: number[]): number | null {
  return values.length === 0 ? null : values.reduce((a, b) => a + b, 0) / values.length;
}

interface Sample { t: number; moisturePct: number | null; vbatMv: number | null }

/** Plausible readings of one plant with a parseable time in [startMs, nowMs], sorted by time. Anything else is dropped. */
function samplesInWindow(readings: AnalyticsReading[], plantId: string, startMs: number, nowMs: number): Sample[] {
  const out: Sample[] = [];
  for (const r of readings) {
    if (r.plantId !== plantId || !r.plausible) continue;
    const t = Date.parse(r.ts);
    if (Number.isNaN(t) || t < startMs || t > nowMs) continue;
    out.push({ t, moisturePct: r.moisturePct, vbatMv: r.vbatMv });
  }
  return out.sort((a, b) => a.t - b.t);
}

/** Count consecutive soil samples whose rise is strictly above WATERING_RISE_PCT and whose gap is at most MAX_EVENT_GAP_MS. */
function countWateringEvents(samples: Sample[]): number {
  let events = 0;
  for (let i = 1; i < samples.length; i++) {
    const prev = samples[i - 1], cur = samples[i];
    if (prev.moisturePct === null || cur.moisturePct === null) continue;
    const gap = cur.t - prev.t;
    if (gap <= 0 || gap > MAX_EVENT_GAP_MS) continue;
    if (cur.moisturePct - prev.moisturePct > WATERING_RISE_PCT) events++;
  }
  return events;
}

/** Aggregates for one plant over the last `windowDays` days ending at `nowMs`. No readings gives explicit nulls and zeros. */
export function aggregatePlant(plant: AnalyticsPlant, readings: AnalyticsReading[], nowMs: number, windowDays: number): PlantAnalytics {
  const startMs = nowMs - windowDays * DAY_MS;
  const samples = samplesInWindow(readings, plant.id, startMs, nowMs);
  const soil = samples.filter((s) => s.moisturePct !== null).map((s) => s.moisturePct as number);
  const battery = samples.filter((s) => s.vbatMv !== null).map((s) => s.vbatMv as number);

  const firstWeek = samples.filter((s) => s.t < startMs + WEEK_MS && s.moisturePct !== null).map((s) => s.moisturePct as number);
  const lastWeek = samples.filter((s) => s.t >= nowMs - WEEK_MS && s.moisturePct !== null).map((s) => s.moisturePct as number);
  const firstWeekMean = mean(firstWeek);
  const lastWeekMean = mean(lastWeek);

  return {
    plantId: plant.id,
    name: plant.name,
    windowDays,
    readingCount: samples.length,
    soilPct: stat(soil),
    batteryMv: stat(battery),
    wateringEvents: countWateringEvents(samples),
    trend: {
      soilChangePct: firstWeekMean === null || lastWeekMean === null ? null : lastWeekMean - firstWeekMean,
      firstWeekMean,
      lastWeekMean,
    },
  };
}

/** Same aggregates for every plant in the list, sorted by name (code-point order, then id). Readings of unknown plants are ignored. */
export function comparePlants(plants: AnalyticsPlant[], readings: AnalyticsReading[], nowMs: number, windowDays: number): PlantAnalytics[] {
  return plants
    .map((p) => aggregatePlant(p, readings, nowMs, windowDays))
    .sort((a, b) => (a.name < b.name ? -1 : a.name > b.name ? 1 : a.plantId < b.plantId ? -1 : a.plantId > b.plantId ? 1 : 0));
}

export type AnalyticsResult =
  | { ok: true; windowDays: AnalyticsWindow; plants: PlantAnalytics[] }
  | { ok: false; error: "invalid_window" | "premium_required" };

/** Entry point. The premium flag is passed in by the caller (FR-P04); this module does not check entitlement itself (the entitlement rule is 4.B7). The flag is checked before any data is read. */
export function analyticsForPlants(input: {
  isPremium: boolean;
  windowDays: number;
  plants: AnalyticsPlant[];
  readings: AnalyticsReading[];
  nowMs: number;
}): AnalyticsResult {
  const window = ANALYTICS_WINDOWS_DAYS.find((w) => w === input.windowDays);
  if (window === undefined) return { ok: false, error: "invalid_window" };
  if (!input.isPremium) return { ok: false, error: "premium_required" };
  return { ok: true, windowDays: window, plants: comparePlants(input.plants, input.readings, input.nowMs, window) };
}

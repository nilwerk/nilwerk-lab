// Premium analytics response (task 4.A6, consumes the 4.B4 contract). Requirements: FR-P01 (30/90-day aggregates, trends, watering events, comparison),
// FR-P04 (premium only; the server decides, the app only shows or hides UI), NFR-06 (the response holds only the caller's own plants).
// Shape: docs/interfaces/openapi.yaml /analytics (snake_case on the wire). Pure TypeScript, no network, so it is unit-tested directly.
// Every value shown comes from the response: nothing is estimated or filled in here.

export const ANALYTICS_WINDOWS = [30, 90] as const;
export type AnalyticsWindow = (typeof ANALYTICS_WINDOWS)[number];

export interface Stat { mean: number; min: number; max: number }

export interface PlantTrend {
  /** last-week mean minus first-week mean, soil percent points; null when either week has no sample */
  soilChangePct: number | null;
  firstWeekMean: number | null;
  lastWeekMean: number | null;
}

export interface PlantAnalytics {
  plantId: string;
  name: string;
  readingCount: number;
  soilPct: Stat | null;
  batteryMv: Stat | null;
  wateringEvents: number;
  trend: PlantTrend;
}

export interface AnalyticsResponse {
  windowDays: AnalyticsWindow;
  plants: PlantAnalytics[];
}

const isNum = (v: unknown): v is number => typeof v === 'number' && Number.isFinite(v);
const isObj = (v: unknown): v is Record<string, unknown> => typeof v === 'object' && v !== null && !Array.isArray(v);
const nullableNum = (v: unknown): number | null | undefined => (v === null ? null : isNum(v) ? v : undefined);

function parseStat(v: unknown): Stat | null | undefined {
  if (v === null) return null;
  if (!isObj(v) || !isNum(v.mean) || !isNum(v.min) || !isNum(v.max)) return undefined;
  return { mean: v.mean, min: v.min, max: v.max };
}

function parseTrend(v: unknown): PlantTrend | undefined {
  if (!isObj(v)) return undefined;
  const soil = nullableNum(v.soil_change_pct), first = nullableNum(v.first_week_mean), last = nullableNum(v.last_week_mean);
  if (soil === undefined || first === undefined || last === undefined) return undefined;
  return { soilChangePct: soil, firstWeekMean: first, lastWeekMean: last };
}

function parsePlant(v: unknown): PlantAnalytics | undefined {
  if (!isObj(v)) return undefined;
  if (typeof v.plant_id !== 'string' || typeof v.name !== 'string') return undefined;
  if (!isNum(v.reading_count) || v.reading_count < 0 || !isNum(v.watering_events) || v.watering_events < 0) return undefined;
  const soil = parseStat(v.soil_pct), battery = parseStat(v.battery_mv), trend = parseTrend(v.trend);
  if (soil === undefined || battery === undefined || trend === undefined) return undefined;
  return { plantId: v.plant_id, name: v.name, readingCount: v.reading_count, soilPct: soil, batteryMv: battery, wateringEvents: v.watering_events, trend };
}

/** Parses a 200 body. Returns null for anything that does not match the contract (the caller shows the error state, never a partial dashboard). */
export function parseAnalyticsResponse(json: unknown, expectedWindow: AnalyticsWindow): AnalyticsResponse | null {
  if (!isObj(json) || json.window_days !== expectedWindow || !Array.isArray(json.plants)) return null;
  const plants: PlantAnalytics[] = [];
  for (const p of json.plants) {
    const parsed = parsePlant(p);
    if (!parsed) return null;
    plants.push(parsed);
  }
  return { windowDays: expectedWindow, plants };
}

/** True when the window has no readings at all (no plants, or every plant has zero plausible samples). */
export const windowIsEmpty = (r: AnalyticsResponse): boolean => r.plants.every((p) => p.readingCount === 0);

/** Display helpers: fixed decimals from the response values, no rounding beyond display. */
export const fmtPct = (n: number): string => n.toFixed(1);
export const fmtVolt = (mv: number): string => (mv / 1000).toFixed(2);
export const fmtSigned = (n: number): string => (n > 0 ? `+${n.toFixed(1)}` : n.toFixed(1));

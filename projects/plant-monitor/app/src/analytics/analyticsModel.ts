// Premium analytics response (task 4.A6 aggregates, 4.A6b daily series). Requirements: FR-P01 (30/90-day line chart from the daily series,
// aggregates, trends, watering events, comparison), FR-P04 (premium only; the server decides, the app only shows or hides UI), NFR-06 (the response
// holds only the caller's own plants). Shape: docs/interfaces/openapi.yaml /analytics and docs/adr/ADR-018 (snake_case on the wire).
// Pure TypeScript, no network, so it is unit-tested directly. Every value shown comes from the response: nothing is estimated or filled in here.

export const ANALYTICS_WINDOWS = [30, 90] as const;
export type AnalyticsWindow = (typeof ANALYTICS_WINDOWS)[number];

export interface Stat { mean: number; min: number; max: number }

export interface PlantTrend {
  /** last-week mean minus first-week mean, soil percent points; null when either week has no sample */
  soilChangePct: number | null;
  firstWeekMean: number | null;
  lastWeekMean: number | null;
}

/** One UTC calendar day of the daily series (ADR-018, FR-P01). Null means "no value that day": a gap, never 0. readingCount is not a chart value. */
export interface DailyPoint {
  date: string;                 // YYYY-MM-DD, UTC calendar day
  soilPctMean: number | null;
  batteryMvMean: number | null;
  readingCount: number;
}

export interface PlantAnalytics {
  plantId: string;
  name: string;
  readingCount: number;
  soilPct: Stat | null;
  batteryMv: Stat | null;
  wateringEvents: number;
  trend: PlantTrend;
  /** exactly windowDays items, oldest first, ending with today (UTC), empty days included (ADR-018).
   *  null when the response has no `daily` key at all (an older backend): the chart says "not available yet", the aggregates still show.
   *  A `daily` value that is present but malformed rejects the whole response (ADR-018 Consequences). */
  daily: DailyPoint[] | null;
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

const DAY_MS = 86_400_000;
const ISO_DAY = /^\d{4}-\d{2}-\d{2}$/;

/** Parses one day of the daily series. Null stays null (a gap), a real 0 stays 0. */
function parseDailyPoint(v: unknown): DailyPoint | undefined {
  if (!isObj(v) || typeof v.date !== 'string' || !ISO_DAY.test(v.date)) return undefined;
  const ms = Date.parse(`${v.date}T00:00:00Z`);
  if (!Number.isFinite(ms) || new Date(ms).toISOString().slice(0, 10) !== v.date) return undefined;
  const soil = nullableNum(v.soil_pct_mean), battery = nullableNum(v.battery_mv_mean);
  if (soil === undefined || battery === undefined) return undefined;
  if (!isNum(v.reading_count) || !Number.isInteger(v.reading_count) || v.reading_count < 0) return undefined;
  return { date: v.date, soilPctMean: soil, batteryMvMean: battery, readingCount: v.reading_count };
}

/** The series must hold exactly windowDays items, each the UTC day after the previous one (ADR-018 client rule). */
function parseDaily(v: unknown, windowDays: AnalyticsWindow): DailyPoint[] | undefined {
  if (!Array.isArray(v) || v.length !== windowDays) return undefined;
  const out: DailyPoint[] = [];
  for (const item of v) {
    const d = parseDailyPoint(item);
    if (!d) return undefined;
    if (out.length > 0 && Date.parse(`${d.date}T00:00:00Z`) - Date.parse(`${out[out.length - 1].date}T00:00:00Z`) !== DAY_MS) return undefined;
    out.push(d);
  }
  return out;
}

function parsePlant(v: unknown, windowDays: AnalyticsWindow): PlantAnalytics | undefined {
  if (!isObj(v)) return undefined;
  if (typeof v.plant_id !== 'string' || typeof v.name !== 'string') return undefined;
  if (!isNum(v.reading_count) || v.reading_count < 0 || !isNum(v.watering_events) || v.watering_events < 0) return undefined;
  const soil = parseStat(v.soil_pct), battery = parseStat(v.battery_mv), trend = parseTrend(v.trend);
  const daily = v.daily === undefined ? null : parseDaily(v.daily, windowDays);   // absent key: null; present but malformed: undefined
  if (soil === undefined || battery === undefined || trend === undefined || daily === undefined) return undefined;
  return { plantId: v.plant_id, name: v.name, readingCount: v.reading_count, soilPct: soil, batteryMv: battery, wateringEvents: v.watering_events, trend, daily };
}

/** Parses a 200 body. Returns null for anything that does not match the contract (the caller shows the error state, never a partial dashboard). */
export function parseAnalyticsResponse(json: unknown, expectedWindow: AnalyticsWindow): AnalyticsResponse | null {
  if (!isObj(json) || json.window_days !== expectedWindow || !Array.isArray(json.plants)) return null;
  const plants: PlantAnalytics[] = [];
  for (const p of json.plants) {
    const parsed = parsePlant(p, expectedWindow);
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

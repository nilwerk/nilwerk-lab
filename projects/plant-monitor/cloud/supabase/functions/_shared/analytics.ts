// GET /analytics (app, user JWT): task 4.B4 slice 2. Requirements: FR-P01 (30/90-day aggregates, trend, watering events, comparison),
// FR-P04 (premium only, checked by public.is_premium() BEFORE any reading is read, ADR-008), NFR-06 (the caller's own rows only).
// Contract: docs/interfaces/openapi.yaml /analytics. Aggregates: ../../../analytics/aggregate.ts (pure, tested without a database).
// Plain TypeScript, no dependencies: runs in Deno (Supabase) and Node 22.6+ (tests).
//
// No service role here. Every database call runs AS THE USER (their JWT), so RLS decides which rows exist: plants_all_own,
// readings_select_own. No SQL function, migration or new column is needed (4.B4 scope: no migration).
//
// Cost (per premium user per month, estimate, no LLM call on this path): reads are plain row selects paged 1000 at a time. A user with
// 3 plants at one sample per 15 min, opening the 90-day view 30 times a month, reads about 3 x 8,640 x 30 = 0.78 M rows. At roughly
// 100 bytes of JSON per row that is ~78 MB of database egress per month, well under 0.01 EUR at list egress prices. Assumptions, not measured.
import { DAY_MS, analyticsForPlants, type AnalyticsPlant, type AnalyticsReading, type AnalyticsWindow } from "../../../analytics/aggregate.ts";
import { bearer, err, json } from "./lib.ts";

/** Rows per PostgREST page. The loop advances by the number of rows actually returned, so a server-side row cap cannot skip rows. */
export const READINGS_PAGE_SIZE = 1000;

/** Database access for the analytics function. Every method takes the user's JWT; a null result is a database or Auth failure. */
export interface AnalyticsDeps {
  /** Verifies a user JWT and returns the user id, or null (401). */
  getUserId(jwt: string): Promise<string | null>;
  /** public.is_premium() called as the user (FR-P04). Null = the call failed. */
  isPremium(jwt: string): Promise<boolean | null>;
  /** The caller's plants (RLS plants_all_own). Null = the call failed. */
  plants(jwt: string): Promise<AnalyticsPlant[] | null>;
  /** One page of the caller's plausible readings with ts >= sinceIso, ordered by (ts, device_id) (RLS readings_select_own). Null = failed. */
  readingsPage(jwt: string, sinceIso: string, offset: number, limit: number): Promise<ReadingRow[] | null>;
}

/** One row of `readings` as PostgREST returns it (snake_case, only the columns the aggregates use). */
export interface ReadingRow { ts: string; plant_id: string | null; moisture_pct: number | null; vbat_mv: number | null; plausible: boolean }
export const readingFromRow = (r: ReadingRow): AnalyticsReading =>
  ({ ts: r.ts, plantId: r.plant_id, moisturePct: r.moisture_pct, vbatMv: r.vbat_mv, plausible: r.plausible });

/** Wire shape of one plant, exactly openapi /analytics 200. */
export interface AnalyticsPlantWire {
  plant_id: string; name: string; reading_count: number;
  soil_pct: { mean: number; min: number; max: number } | null;
  battery_mv: { mean: number; min: number; max: number } | null;
  watering_events: number;
  /** ADR-018 (4.B4b): one item per UTC day of the window, oldest first, empty days included; null = gap, never 0. At most 90 x 4 values. */
  daily: { date: string; soil_pct_mean: number | null; battery_mv_mean: number | null; reading_count: number }[];
  trend: { soil_change_pct: number | null; first_week_mean: number | null; last_week_mean: number | null };
}

/**
 * GET /analytics?window=30|90. Order of checks: method (405) -> token (401) -> premium (403 premium_required, public.is_premium() called
 * as the user before ANY reading; FR-P04) -> window (400; checked after the premium gate so a free user learns nothing about it) ->
 * plants and readings (500 on any failure, no detail). Openapi /analytics: "call public.is_premium() first".
 * `nowMs` is injected so tests use fixed fixtures; production passes Date.now().
 */
export async function handleAnalytics(req: Request, deps: AnalyticsDeps, nowMs: number = Date.now()): Promise<Response> {
  if (req.method !== "GET") return err(405, "method_not_allowed");
  const jwt = bearer(req);
  const uid = jwt ? await deps.getUserId(jwt) : null;
  if (!jwt || !uid) return err(401, "unauthorized", "missing or invalid user JWT");
  const premium = await deps.isPremium(jwt);
  if (premium === null) return err(500, "internal");
  if (!premium) return err(403, "premium_required", "analytics is a premium feature (FR-P04)");

  const raw = new URL(req.url).searchParams.get("window");
  const windowDays = raw === "30" ? 30 : raw === "90" ? 90 : null;
  if (windowDays === null) return err(400, "bad_request", "window must be 30 or 90");

  const plants = await deps.plants(jwt);
  if (plants === null) return err(500, "internal");
  const sinceIso = new Date(nowMs - windowDays * DAY_MS).toISOString();
  const readings: AnalyticsReading[] = [];
  for (let offset = 0; ;) {
    const page = await deps.readingsPage(jwt, sinceIso, offset, READINGS_PAGE_SIZE);
    if (page === null) return err(500, "internal");
    if (page.length === 0) break;
    for (const r of page) readings.push(readingFromRow(r));
    offset += page.length;
  }

  // isPremium is true here (the 403 above), so analyticsForPlants only computes; it cannot refuse.
  const result = analyticsForPlants({ isPremium: true, windowDays, plants, readings, nowMs });
  if (!result.ok) return err(500, "internal");
  const body = {
    window_days: result.windowDays as AnalyticsWindow,
    plants: result.plants.map((p): AnalyticsPlantWire => ({
      plant_id: p.plantId, name: p.name, reading_count: p.readingCount,
      // watering_events thresholds (WATERING_RISE_PCT = 10 points or more, MAX_EVENT_GAP_MS = 2 h) are decided, A-115.
      soil_pct: p.soilPct, battery_mv: p.batteryMv, watering_events: p.wateringEvents,
      daily: p.daily.map((d) => ({ date: d.date, soil_pct_mean: d.soilPctMean, battery_mv_mean: d.batteryMvMean, reading_count: d.readingCount })),
      trend: { soil_change_pct: p.trend.soilChangePct, first_week_mean: p.trend.firstWeekMean, last_week_mean: p.trend.lastWeekMean },
    })),
  };
  return json(200, body, { "cache-control": "no-store" });   // personal plant data: never cached
}

// 4.B4 slice 2: GET /analytics tests. Unit (fake deps, no database) + integration (local PostgreSQL, NW_TEST_DB_URL, set by cloud/test.sh).
// Requirements: FR-P01 (30/90-day aggregates, trend, watering events, comparison), FR-P04 (premium only, checked before any reading),
// NFR-06 (the caller's own rows only, RLS). Expected numbers are hand-computed in the comments, not produced by the code under test.
import { test } from "node:test";
import assert from "node:assert/strict";
import { handleAnalytics, READINGS_PAGE_SIZE, type AnalyticsDeps, type ReadingRow } from "../../supabase/functions/_shared/analytics.ts";
import { psql } from "./psql_deps.ts";

const NOW_ISO = "2026-11-20T00:00:00Z";
const NOW_MS = Date.parse(NOW_ISO);
const P = "00000000-0000-0000-0000-0000000000a0", E = "00000000-0000-0000-0000-0000000000e0", F = "00000000-0000-0000-0000-0000000000f0";
const JWT: Record<string, string> = { "jwt-p": P, "jwt-e": E, "jwt-f": F };

const req = (qs: string, auth?: string, method = "GET") =>
  new Request(`http://x/analytics${qs}`, { method, headers: auth ? { authorization: `Bearer ${auth}` } : {} });

/** Deps that fail loudly if anything reads data: used to prove the premium check runs before any reading. */
const spyDeps = (over: Partial<AnalyticsDeps> = {}) => {
  const calls: string[] = [];
  const deps: AnalyticsDeps = {
    getUserId: async (j) => { calls.push("getUserId"); return JWT[j] ?? null; },
    isPremium: async () => { calls.push("isPremium"); return true; },
    plants: async () => { calls.push("plants"); return []; },
    readingsPage: async () => { calls.push("readingsPage"); return []; },
    ...over,
  };
  return { deps, calls };
};

// ---------------------------------------------------------------- unit tests (no database)
test("FR-P04: wrong method -> 405 and nothing is read", async () => {
  const { deps, calls } = spyDeps();
  for (const m of ["POST", "PUT", "DELETE", "PATCH"]) assert.equal((await handleAnalytics(req("?window=30", "jwt-p", m), deps, NOW_MS)).status, 405, m);
  assert.deepEqual(calls, []);
});

test("NFR-06: missing or forged token -> 401 before any data access", async () => {
  const { deps, calls } = spyDeps();
  const none = await handleAnalytics(req("?window=30"), deps, NOW_MS);
  assert.equal(none.status, 401); assert.equal((await none.json() as { error: string }).error, "unauthorized");
  assert.equal((await handleAnalytics(req("?window=30", "forged"), deps, NOW_MS)).status, 401);
  assert.deepEqual(calls, ["getUserId"]);
});

test("window must be exactly 30 or 90 -> 400 bad_request, no data access", async () => {
  const { deps, calls } = spyDeps();
  const bad = ["", "?window=", "?window=7", "?window=031", "?window=30.0", "?window=30%20", "?window=60", "?days=30"];
  for (const qs of bad) {
    const r = await handleAnalytics(req(qs, "jwt-p"), deps, NOW_MS);
    assert.equal(r.status, 400, qs); assert.equal((await r.json() as { error: string }).error, "bad_request", qs);
  }
  assert.deepEqual(calls, bad.flatMap(() => ["getUserId", "isPremium"]), "token, then premium, then the 400: no plant or reading is read");
  assert.ok(!calls.includes("plants") && !calls.includes("readingsPage"));
  const free = spyDeps({ isPremium: async () => false });
  assert.equal((await handleAnalytics(req("?window=7", "jwt-e"), free.deps, NOW_MS)).status, 403, "a free user gets 403 before the window is looked at");
});

test("FR-P04: a free user gets 403 premium_required and NO plant or reading is read", async () => {
  const { deps, calls } = spyDeps({ isPremium: async () => false });
  for (const w of ["30", "90"]) {
    const r = await handleAnalytics(req(`?window=${w}`, "jwt-e"), deps, NOW_MS);
    assert.equal(r.status, 403); assert.equal((await r.json() as { error: string }).error, "premium_required");
  }
  assert.ok(!calls.includes("plants") && !calls.includes("readingsPage"), "the premium check comes before any read");
});

test("500: a failed premium check, plant read or reading read -> 'internal', no database detail in the body", async () => {
  const leak = "SELECT secret_table failed";
  const cases: Partial<AnalyticsDeps>[] = [
    { isPremium: async () => null },
    { plants: async () => null },
    { readingsPage: async () => null },
  ];
  for (const over of cases) {
    const { deps } = spyDeps({ isPremium: async () => true, ...over });
    const r = await handleAnalytics(req("?window=30", "jwt-p"), deps, NOW_MS);
    const text = await r.text();
    assert.equal(r.status, 500); assert.deepEqual(JSON.parse(text), { error: "internal" }); assert.ok(!text.includes(leak));
  }
});

test("NFR-07-style paging: reads every page until an empty one; the offset advances by the rows actually returned (a server row cap cannot skip rows)", async () => {
  const offsets: number[] = [];
  // a server that caps pages at 500 rows (not the 1000 requested): 1,203 readings in total
  const all: ReadingRow[] = Array.from({ length: 1203 }, (_, i) => ({ ts: new Date(NOW_MS - (1203 - i) * 60000).toISOString(), plant_id: null, moisture_pct: 40, vbat_mv: 3900, plausible: true }));
  const { deps } = spyDeps({
    plants: async () => [{ id: "x", name: "X" }],
    isPremium: async () => true,
    readingsPage: async (_j, _since, offset, limit) => {
      offsets.push(offset); assert.equal(limit, READINGS_PAGE_SIZE);
      return all.slice(offset, offset + Math.min(limit, 500));
    },
  });
  const r = await handleAnalytics(req("?window=90", "jwt-p"), deps, NOW_MS);
  assert.equal(r.status, 200);
  assert.deepEqual(offsets, [0, 500, 1000, 1203], "pages at 0, 500, 1000, then the empty page at the end");
});

// ---------------------------------------------------------------- integration tests (local PostgreSQL, RLS as the user)
const url = process.env.NW_TEST_DB_URL;
const db = url ? { skip: false } : { skip: "NW_TEST_DB_URL not set (run via cloud/test.sh)" };
const q = (sql: string, vars?: Record<string, string>) => { const r = psql(url!, sql, vars); assert.ok(r.ok, r.err); return r.out; };
/** Runs as the authenticated role with auth.uid() = uid, the way PostgREST runs a user request. */
const asUser = (uid: string, sql: string, vars: Record<string, string> = {}) =>
  q(`set role authenticated; set request.uid = :'uid'; ${sql}`, { ...vars, uid });

const PLANT_BASIL = "10000000-0000-0000-0000-00000000a0b1", PLANT_ALOE = "10000000-0000-0000-0000-00000000a0b2", PLANT_FERN = "10000000-0000-0000-0000-0000000000f1";
const DEV_P = "20000000-0000-0000-0000-0000000000a1", DEV_F = "20000000-0000-0000-0000-0000000000f1";
const T0 = "2026-10-26T00:00:00Z";   // NOW - 25 days

function seed() {
  for (const [u, tag] of [[P, "p"], [E, "e"], [F, "f"]] as const) q(`insert into auth.users(id,email) values (:'u', :'e')`, { u, e: `${tag}@example.test` });
  q(`update public.profiles set is_premium = true where id in (:'p', :'f'); update public.profiles set is_premium = false where id = :'e';`, { p: P, f: F, e: E });
  q(`insert into public.plants(id,owner_id,name,location_type,soil_type) values
       (:'pb', :'p', 'Basil', 'house', 'potting'), (:'pa', :'p', 'Aloe', 'house', 'potting'), (:'pf', :'f', 'Fern', 'house', 'potting');
     insert into public.devices(id,hw_id,owner_id,plant_id,claimed_at) values
       (:'dp', 'nw-0000000000a1', :'p', :'pb', now()), (:'df', 'nw-0000000000f1', :'f', :'pf', now());
     -- 2,400 plausible samples, 15 min apart, from NOW-25 d to NOW-15 min: moisture 40 for the first 2,000, then 60; battery 3,900 mV
     insert into public.readings(device_id,ts,owner_id,plant_id,moisture_pct,vbat_mv,plausible)
       select :'dp', timestamptz :'t0' + g * interval '15 minutes', :'p', :'pb', case when g < 2000 then 40 else 60 end, 3900, true
       from generate_series(0, 2399) g;
     -- must NOT count: implausible (19 Nov 23:07, off the 15-min grid so no key clash, moisture 99), and a plausible sample in the future (NOW + 1 h)
     insert into public.readings(device_id,ts,owner_id,plant_id,moisture_pct,vbat_mv,plausible) values
       (:'dp', timestamptz '2026-11-19T23:07:00Z', :'p', :'pb', 99, 3900, false),
       (:'dp', timestamptz '2026-11-20T01:00:00Z', :'p', :'pb', 99, 3900, true);
     -- F's own data: must never appear in P's answer
     insert into public.readings(device_id,ts,owner_id,plant_id,moisture_pct,vbat_mv,plausible)
       select :'df', timestamptz '2026-11-18T00:00:00Z' + g * interval '1 hour', :'f', :'pf', 5, 3000, true from generate_series(0, 9) g;`,
    { p: P, e: E, f: F, pb: PLANT_BASIL, pa: PLANT_ALOE, pf: PLANT_FERN, dp: DEV_P, df: DEV_F, t0: T0 });
}

/** Deps as the app would use them: every call runs as the user, through RLS and public.is_premium(). */
function dbDeps(calls: string[] = []): AnalyticsDeps {
  return {
    async getUserId(jwt) { calls.push("getUserId"); return JWT[jwt] ?? null; },
    async isPremium(jwt) {
      calls.push("isPremium");
      const r = psql(url!, `set role authenticated; set request.uid = :'uid'; select public.is_premium();`, { uid: JWT[jwt] ?? "" });
      return r.ok ? r.out === "t" : null;
    },
    async plants(jwt) {
      calls.push("plants");
      const r = psql(url!, `set role authenticated; set request.uid = :'uid'; select coalesce(json_agg(json_build_object('id', id, 'name', name)), '[]'::json) from public.plants;`, { uid: JWT[jwt] ?? "" });
      return r.ok ? JSON.parse(r.out) : null;
    },
    async readingsPage(jwt, sinceIso, offset, limit) {
      calls.push(`readingsPage@${offset}`);
      const r = psql(url!, `set role authenticated; set request.uid = :'uid';
        select coalesce(json_agg(x), '[]'::json) from (select ts, plant_id, moisture_pct, vbat_mv, plausible from public.readings
          where plausible and ts >= :'since'::timestamptz order by ts, device_id offset :off limit :lim) x;`,
        { uid: JWT[jwt] ?? "", since: sinceIso, off: String(offset), lim: String(limit) });
      return r.ok ? JSON.parse(r.out) : null;
    },
  };
}

const WIRE_PLANT_KEYS = ["battery_mv", "plant_id", "name", "reading_count", "soil_pct", "trend", "watering_events"].sort();
const WIRE_TREND_KEYS = ["first_week_mean", "last_week_mean", "soil_change_pct"].sort();

test("setup: three users, two premium and one free; each has its own plants and readings", db, () => {
  seed();
  assert.equal(asUser(P, `select count(*) from public.readings;`), "2402", "P sees its 2,402 rows (2,400 + one future + one implausible), never F's");
  assert.equal(asUser(F, `select count(*) from public.plants;`), "1");
  assert.equal(q(`select is_premium from public.profiles where id = :'e'`, { e: E }), "f");
});

test("FR-P04: the free user is refused 403 premium_required (integration, real is_premium())", db, async () => {
  const calls: string[] = [];
  const r = await handleAnalytics(req("?window=30", "jwt-e"), dbDeps(calls), NOW_MS);
  assert.equal(r.status, 403);
  assert.deepEqual(await r.json(), { error: "premium_required", message: "analytics is a premium feature (FR-P04)" });
  assert.ok(!calls.some((c) => c.startsWith("readingsPage") || c === "plants"), "no reading or plant is read for a free user");
});

test("FR-P01: premium user, window=30 -> 200 with the contract shape, hand-computed aggregates for Basil and zeros for Aloe", db, async () => {
  const r = await handleAnalytics(req("?window=30", "jwt-p"), dbDeps(), NOW_MS);
  assert.equal(r.status, 200);
  assert.equal(r.headers.get("cache-control"), "no-store");
  const body = await r.json() as { window_days: number; plants: any[] };
  assert.deepEqual(Object.keys(body).sort(), ["plants", "window_days"]);
  assert.equal(body.window_days, 30);
  assert.deepEqual(body.plants.map((p) => p.name), ["Aloe", "Basil"], "sorted by name");
  const [aloe, basil] = body.plants;
  // Aloe: no readings -> explicit zeros and nulls
  assert.deepEqual(aloe, {
    plant_id: PLANT_ALOE, name: "Aloe", reading_count: 0, soil_pct: null, battery_mv: null, watering_events: 0,
    trend: { soil_change_pct: null, first_week_mean: null, last_week_mean: null },
  });
  // Basil, 30 days: 2,400 samples. soil sum 2,000*40 + 400*60 = 104,000 -> mean 43.333..., min 40, max 60 (the future and implausible rows are out)
  // first week (Oct 21-27 window start, t < Oct 28): 192 samples, all 40 -> 40.
  // last week (t >= Nov 13): 672 samples = 272 x 40 + 400 x 60 = 34,880 -> 34,880 / 672 = 51.9047619...; trend = 11.9047619...
  // watering: one rise 40 -> 60 within 15 min (> 10, gap <= 2 h) -> 1 event.
  assert.equal(basil.plant_id, PLANT_BASIL);
  assert.equal(basil.reading_count, 2400);
  assert.deepEqual(Object.keys(basil).sort(), WIRE_PLANT_KEYS);
  assert.deepEqual(Object.keys(basil.trend).sort(), WIRE_TREND_KEYS);
  assert.deepEqual(basil.soil_pct, { mean: 104000 / 2400, min: 40, max: 60 });
  assert.deepEqual(basil.battery_mv, { mean: 3900, min: 3900, max: 3900 });
  assert.equal(basil.watering_events, 1);
  assert.equal(basil.trend.first_week_mean, 40);
  assert.ok(Math.abs(basil.trend.last_week_mean - 34880 / 672) < 1e-9);
  assert.ok(Math.abs(basil.trend.soil_change_pct - (34880 / 672 - 40)) < 1e-9);
});

test("FR-P01: window=90 -> the same readings; the first week is empty so the trend is null", db, async () => {
  const body = await (await handleAnalytics(req("?window=90", "jwt-p"), dbDeps(), NOW_MS)).json() as { window_days: number; plants: any[] };
  assert.equal(body.window_days, 90);
  const basil = body.plants.find((p) => p.name === "Basil");
  assert.equal(basil.reading_count, 2400);
  assert.equal(basil.watering_events, 1);
  assert.equal(basil.trend.first_week_mean, null);
  assert.equal(basil.trend.soil_change_pct, null);
  assert.ok(Math.abs(basil.trend.last_week_mean - 34880 / 672) < 1e-9);
});

test("NFR-06: the answer names only the caller's plants; F's plant and readings never appear", db, async () => {
  const text = await (await handleAnalytics(req("?window=90", "jwt-p"), dbDeps(), NOW_MS)).text();
  assert.ok(!text.includes(PLANT_FERN) && !text.includes("Fern") && !text.includes(DEV_F));
  const fern = await (await handleAnalytics(req("?window=30", "jwt-f"), dbDeps(), NOW_MS)).json() as { plants: any[] };
  assert.deepEqual(fern.plants.map((p) => p.name), ["Fern"]);
  assert.equal(fern.plants[0].reading_count, 10, "F sees only F's 10 readings");
  assert.equal(fern.plants[0].soil_pct.mean, 5);
});

test("paging over the real database: 2,401 rows in three pages (1000, 1000, 401) and one empty page", db, async () => {
  const calls: string[] = [];
  const r = await handleAnalytics(req("?window=90", "jwt-p"), dbDeps(calls), NOW_MS);
  assert.equal(r.status, 200);
  assert.deepEqual(calls.filter((c) => c.startsWith("readingsPage")), ["readingsPage@0", "readingsPage@1000", "readingsPage@2000", "readingsPage@2401"]);
  assert.equal(READINGS_PAGE_SIZE, 1000);
});

test("500 on a database failure as the user (a table that does not exist), no database text in the body", db, async () => {
  const broken: AnalyticsDeps = { ...dbDeps(), readingsPage: async () => { const r = psql(url!, `select * from public.no_such_table`); return r.ok ? [] : null; } };
  const r = await handleAnalytics(req("?window=30", "jwt-p"), broken, NOW_MS);
  const text = await r.text();
  assert.equal(r.status, 500); assert.deepEqual(JSON.parse(text), { error: "internal" }); assert.ok(!text.includes("no_such_table"));
});

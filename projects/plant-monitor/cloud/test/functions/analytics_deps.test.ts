// 4.B4 slice 3: the database adapter of GET /analytics (buildAnalyticsDeps, used by makeAnalyticsDeps) against a FAKE PostgREST client that
// records every call. No database, no network. NOT a real PostgREST check: the filter strings are asserted, not executed against PostgREST.
// Requirements: FR-P04 (is_premium as the user, before any read), NFR-06 (every call carries the user's JWT), FR-P01 (paging).
import { test } from "node:test";
import assert from "node:assert/strict";
import { buildAnalyticsDeps, type AnalyticsClient, type AnalyticsQuery } from "../../supabase/functions/_shared/analytics_deps.ts";
import { handleAnalytics, type ReadingRow } from "../../supabase/functions/_shared/analytics.ts";

const NOW_MS = Date.parse("2026-11-20T00:00:00Z");
const U = "00000000-0000-0000-0000-0000000000a0";

interface Fake { log: string[]; jwts: string[]; clients: string[]; asUser: (jwt: string) => AnalyticsClient }
/** Fake client factory. `pageRows` is how many rows the "server" returns per range call (a row cap); `total` rows exist. */
function fake(opts: { premium?: unknown; rpcError?: boolean; total?: number; pageRows?: number; readError?: boolean } = {}): Fake {
  const log: string[] = [], jwts: string[] = [], clients: string[] = [];
  const total = opts.total ?? 0, cap = opts.pageRows ?? 1000;
  const row = (i: number): ReadingRow => ({ ts: new Date(NOW_MS - 3_600_000 * (total - i)).toISOString(), plant_id: "p1", moisture_pct: 40, vbat_mv: 3900, plausible: true });
  const asUser = (jwt: string): AnalyticsClient => {
    jwts.push(jwt); clients.push(jwt);
    const q = (table: string): AnalyticsQuery => {
      const steps: string[] = [];
      const self: AnalyticsQuery = {
        select: (c) => { steps.push(`select(${c})`); return self; },
        eq: (c, v) => { steps.push(`eq(${c},${String(v)})`); return self; },
        gte: (c, v) => { steps.push(`gte(${c},${String(v)})`); return self; },
        order: (c, o) => { steps.push(`order(${c},${o.ascending})`); return self; },
        range: (a, b) => {
          log.push(`from(${table}).${steps.join(".")}.range(${a},${b})`);
          if (opts.readError) return Promise.resolve({ data: null, error: { message: "boom" } });
          const n = Math.max(0, Math.min(cap, b - a + 1, total - a));
          return Promise.resolve({ data: Array.from({ length: n }, (_, k) => row(a + k)), error: null });
        },
        then: ((f: never, r: never) => { log.push(`from(${table}).${steps.join(".")}`); return Promise.resolve({ data: [{ id: "p1", name: "Basil" }], error: null }).then(f, r); }) as AnalyticsQuery["then"],
      };
      return self;
    };
    return {
      auth: { getUser: async (j) => { log.push(`getUser(${j})`); return { data: { user: j === "jwt-ok" ? { id: U } : null }, error: j === "jwt-ok" ? null : { message: "bad" } }; } },
      rpc: (name) => { log.push(`rpc(${name})`); return Promise.resolve({ data: "premium" in opts ? opts.premium : true, error: opts.rpcError ? { message: "x" } : null }); },
      from: q,
    };
  };
  return { log, jwts, clients, asUser };
}
const get = (qs = "?window=30") => new Request(`http://x/analytics${qs}`, { headers: { authorization: "Bearer jwt-ok" } });

test("FR-P04: is_premium is an RPC named is_premium, called as the user (their JWT), before any table read", async () => {
  const f = fake({ total: 3 });
  const res = await handleAnalytics(get(), buildAnalyticsDeps(f.asUser), NOW_MS);
  assert.equal(res.status, 200);
  const iRpc = f.log.indexOf("rpc(is_premium)");
  const iFirstRead = f.log.findIndex((l) => l.startsWith("from("));
  assert.ok(iRpc >= 0 && iFirstRead > iRpc, `rpc must precede reads: ${JSON.stringify(f.log)}`);
  assert.equal(f.log.filter((l) => l.startsWith("rpc(")).length, 1);
  assert.ok(f.jwts.length > 0 && f.jwts.every((j) => j === "jwt-ok"), "every client is built from the caller's JWT only");
});

test("FR-P04: free user -> 403 and NO table read happened (only getUser and the RPC)", async () => {
  const f = fake({ premium: false, total: 5 });
  const res = await handleAnalytics(get(), buildAnalyticsDeps(f.asUser), NOW_MS);
  assert.equal(res.status, 403);
  assert.deepEqual(f.log, ["getUser(jwt-ok)", "rpc(is_premium)"]);
});

test("FR-P04: RPC error or non-boolean result -> 500 (fail closed), no table read", async () => {
  for (const f of [fake({ rpcError: true }), fake({ premium: "true" }), fake({ premium: null })]) {
    const res = await handleAnalytics(get(), buildAnalyticsDeps(f.asUser), NOW_MS);
    assert.equal(res.status, 500);
    assert.ok(!f.log.some((l) => l.startsWith("from(")));
  }
});

test("getUserId: valid JWT -> user id, invalid JWT -> null (401) and nothing else is called", async () => {
  const f = fake();
  const deps = buildAnalyticsDeps(f.asUser);
  assert.equal(await deps.getUserId("jwt-ok"), U);
  assert.equal(await deps.getUserId("jwt-bad"), null);
  const res = await handleAnalytics(new Request("http://x/analytics?window=30", { headers: { authorization: "Bearer jwt-bad" } }), buildAnalyticsDeps(fake().asUser), NOW_MS);
  assert.equal(res.status, 401);
});

test("readings query: plausible only, since the window start, ordered by ts then device_id, range(offset, offset+limit-1)", async () => {
  const f = fake({ total: 1 });
  await handleAnalytics(get("?window=90"), buildAnalyticsDeps(f.asUser), NOW_MS);
  const since = new Date(NOW_MS - 90 * 86_400_000).toISOString();   // 2026-08-22T00:00:00.000Z
  assert.equal(since, "2026-08-22T00:00:00.000Z");
  assert.ok(f.log.includes(`from(readings).select(ts,plant_id,moisture_pct,vbat_mv,plausible).eq(plausible,true).gte(ts,${since}).order(ts,true).order(device_id,true).range(0,999)`), JSON.stringify(f.log));
  assert.ok(f.log.includes("from(plants).select(id,name)"));
});

test("paging advances by the rows actually returned: a server cap of 250 rows per page over 600 rows reads offsets 0, 250, 500, 600", async () => {
  const f = fake({ total: 600, pageRows: 250 });
  const res = await handleAnalytics(get(), buildAnalyticsDeps(f.asUser), NOW_MS);
  assert.equal(res.status, 200);
  const ranges = f.log.filter((l) => l.includes(".range(")).map((l) => l.slice(l.indexOf(".range(")));
  // hand count: pages of 250, 250, 100, then an empty page at offset 600
  assert.deepEqual(ranges, [".range(0,999)", ".range(250,1249)", ".range(500,1499)", ".range(600,1599)"]);
  const body = await res.json() as { plants: { reading_count: number }[] };
  assert.equal(body.plants[0].reading_count, 600);   // none skipped, none doubled
});

test("a read error in a page -> 500 with no detail", async () => {
  const f = fake({ total: 5, readError: true });
  const res = await handleAnalytics(get(), buildAnalyticsDeps(f.asUser), NOW_MS);
  assert.equal(res.status, 500);
  assert.ok(!JSON.stringify(await res.json()).includes("boom"));
});

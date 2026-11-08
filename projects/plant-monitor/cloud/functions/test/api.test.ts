// 4.B2 tests: unit tests (no database) and integration tests against a local PostgreSQL (NW_TEST_DB_URL, set by cloud/test.sh).
// Requirements: FR-D01, FR-D02, FR-D03, FR-D04, FR-A02, FR-A03, FR-A07, FR-A08, FR-E03, NFR-04, NFR-06.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { handleClaimToken, handleDeviceClaim, handleIngest } from "../_shared/handlers.ts";
import { sha256Hex, validateReport, type Deps } from "../_shared/lib.ts";
import { psql, psqlDeps } from "./psql_deps.ts";

const here = dirname(fileURLToPath(import.meta.url));
const fx = join(here, "../../../docs/interfaces/fixtures");
const A = "00000000-0000-0000-0000-00000000000a", B = "00000000-0000-0000-0000-00000000000b";
const T0 = 1767225600;   // fixture sent_at

// ---------------------------------------------------------------- unit tests (no database)
test("NFR-06: sha256Hex is the real SHA-256 (known vector) and never the identity", async () => {
  assert.equal(await sha256Hex("abc"), "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");
  assert.notEqual(await sha256Hex("tok"), "tok");
  assert.match(await sha256Hex("tok"), /^[0-9a-f]{64}$/);
});

test("FR-D04: validateReport agrees with device-report.schema.json fixtures (valid accepted, invalid rejected, 193 samples -> 413)", () => {
  const valid = JSON.parse(readFileSync(join(fx, "device-report.valid.json"), "utf8"));
  assert.equal(validateReport(valid), null);
  for (const f of readdirSync(join(fx, "invalid"))) {
    const v = validateReport(JSON.parse(readFileSync(join(fx, "invalid", f), "utf8")));
    assert.ok(v, `${f} must be rejected`);
    assert.equal(v.status, f.includes("193") ? 413 : 400, f);
  }
  const mk = (n: number) => ({ ...valid, samples: Array.from({ length: n }, (_, i) => ({ ts: T0 - 900 * i })) });
  assert.equal(validateReport(mk(96)), null, "96 samples (24 h offline buffer) accepted");
  assert.equal(validateReport(mk(192)), null);
  assert.equal(validateReport(mk(193))?.status, 413);
  assert.ok(validateReport({ ...valid, device_id: "x" }), "a caller cannot name a device");
  assert.equal(validateReport({ ...valid, samples: [{ ts: T0, temp_c: 999, vbat_mv: 1 }] }), null, "implausible values are stored, not rejected (FR-D01)");
});

test("NFR-06: handlers send only SHA-256 digests to the database, never plaintext tokens; 401/405 shortcuts", async () => {
  const seen: Record<string, unknown>[] = [];
  const deps: Deps = {
    rpc: async (_n, a) => { seen.push(a); return { data: { error: "token_invalid" }, error: null }; },
    getUserId: async () => null, randomBytes: (n) => new Uint8Array(n).fill(7),
  };
  const valid = readFileSync(join(fx, "device-report.valid.json"), "utf8");
  const r = await handleIngest(new Request("http://x/ingest", { method: "POST", headers: { authorization: "Bearer SECRET-TOKEN" }, body: valid }), deps);
  assert.equal(r.status, 401);
  assert.equal(seen[0].p_token_hash, await sha256Hex("SECRET-TOKEN"));
  assert.ok(!JSON.stringify(seen).includes("SECRET-TOKEN"));
  assert.equal((await handleIngest(new Request("http://x/ingest", { method: "POST", body: valid }), deps)).status, 401);
  assert.equal((await handleIngest(new Request("http://x/ingest", { method: "GET" }), deps)).status, 405);
  assert.equal(seen.length, 1, "no database call without a token");
  const big = await handleIngest(new Request("http://x/ingest", { method: "POST", headers: { authorization: "Bearer t" }, body: " ".repeat(65 * 1024) }), deps);
  assert.equal(big.status, 413);
  assert.equal((await handleClaimToken(new Request("http://x/claim-token", { method: "POST" }), deps)).status, 401);
});

// ---------------------------------------------------------------- integration tests (local PostgreSQL)
const url = process.env.NW_TEST_DB_URL;
const db = url ? { skip: false } : { skip: "NW_TEST_DB_URL not set (run via cloud/test.sh)" };
const deps = url ? psqlDeps(url, { "jwt-a": A, "jwt-b": B }) : (undefined as unknown as Deps);
const q = (sql: string, vars?: Record<string, string>) => { const r = psql(url!, sql, vars); assert.ok(r.ok, r.err); return r.out; };
const post = (fn: typeof handleIngest, path: string, body: unknown, auth?: string) =>
  fn(new Request(`http://x/${path}`, { method: "POST", headers: auth ? { authorization: `Bearer ${auth}` } : {}, body: JSON.stringify(body) }), deps);
async function claimToken(jwt: string) {
  const r = await handleClaimToken(new Request("http://x/claim-token", { method: "POST", headers: { authorization: `Bearer ${jwt}` } }), deps);
  return { status: r.status, body: await r.json() as Record<string, string> };
}
async function claim(jwt: string, hw: string, extra: Record<string, unknown> = {}) {
  const ct = await claimToken(jwt);
  assert.equal(ct.status, 201);
  const r = await post(handleDeviceClaim, "device-claim", { hw_id: hw, claim_token: ct.body.claim_token, fw: "0.1.0", ...extra });
  return { status: r.status, body: await r.json() as Record<string, any>, claim_token: ct.body.claim_token };
}
const samples = (n: number, from = T0, extra: Record<string, unknown> = {}) =>
  Array.from({ length: n }, (_, i) => ({ ts: from - 900 * i, moisture_pct: 40 + (i % 5), moisture_raw: 1900, temp_c: 21, rh_pct: 50, lux: 300, vbat_mv: 3900, ...extra }));
const report = (s: unknown[], extra: Record<string, unknown> = {}) => ({ v: 1, sent_at: Math.floor(Date.now() / 1000), trigger: "scheduled", fw: "0.1.0", samples: s, ...extra });
const ingest = async (tok: string, body: unknown) => { const r = await post(handleIngest, "ingest", body, tok); return { status: r.status, body: await r.json() as Record<string, any> }; };
const count = (table: string, dev: string) => Number(q(`select count(*) from public.${table} where device_id = :'d'`, { d: dev }));

let devA = "", devB = "", tokA = "", tokB = "";

test("FR-D03, FR-A03, NFR-06: claim token -> device token, hash only stored, single use", db, async () => {
  const a = await claim("jwt-a", "nw-aaaaaaaaaaaa", { name: "Basil" });
  assert.equal(a.status, 200);
  assert.match(a.body.device_token, /^[0-9a-f]{64}$/);
  assert.deepEqual(a.body.config, { sample_interval_s: 900, report_interval_s: 3600, dry_pct: 25, wet_pct: 85, low_battery_mv: 3400 });
  devA = a.body.device_id; tokA = a.body.device_token;
  assert.equal(q(`select encode(token_hash,'hex') from public.device_credentials where device_id = :'d'`, { d: devA }),
    createHash("sha256").update(tokA).digest("hex"), "stored value is SHA-256(token)");
  assert.equal(q(`select count(*) from public.device_credentials where encode(token_hash,'hex') = :'t'`, { t: tokA }), "0", "plaintext token is not stored");
  assert.equal(q(`select count(*) from public.claim_tokens where encode(token_hash,'hex') = :'t' or convert_from(token_hash,'LATIN1') = :'t'`, { t: a.claim_token }), "0", "plaintext claim token is not stored");
  assert.equal(q(`select owner_id from public.devices where id = :'d'`, { d: devA }), A);
  const again = await post(handleDeviceClaim, "device-claim", { hw_id: "nw-aaaaaaaaaaaa", claim_token: a.claim_token, fw: "0.1.0" });
  assert.equal(again.status, 401, "claim token is single use");
  assert.equal((await again.json() as any).error, "claim_token_invalid");
  const b = await claim("jwt-b", "nw-bbbbbbbbbbbb");
  assert.equal(b.status, 200); devB = b.body.device_id; tokB = b.body.device_token;
  assert.notEqual(tokA, tokB);
});

test("FR-D03: expired and unknown claim tokens are refused; hw_id of another user -> 409 and token stays usable", db, async () => {
  const ct = await claimToken("jwt-a");
  q(`update public.claim_tokens set expires_at = now() - interval '1 second' where used_at is null and encode(token_hash,'hex') = :'h'`, { h: await sha256Hex(ct.body.claim_token) });
  const exp = await post(handleDeviceClaim, "device-claim", { hw_id: "nw-cccccccccccc", claim_token: ct.body.claim_token, fw: "1" });
  assert.equal(exp.status, 401);
  const unk = await post(handleDeviceClaim, "device-claim", { hw_id: "nw-cccccccccccc", claim_token: "nope", fw: "1" });
  assert.equal(unk.status, 401);
  const stolen = await claimToken("jwt-b");
  const r = await post(handleDeviceClaim, "device-claim", { hw_id: "nw-aaaaaaaaaaaa", claim_token: stolen.body.claim_token, fw: "1" });
  assert.equal(r.status, 409);
  assert.equal((await r.json() as any).error, "device_owned");
  assert.equal(q(`select owner_id from public.devices where id = :'d'`, { d: devA }), A, "owner unchanged");
  assert.equal(q(`select used_at is null from public.claim_tokens where encode(token_hash,'hex') = :'h'`, { h: await sha256Hex(stolen.body.claim_token) }), "t");
  assert.equal((await claimToken("bad-jwt")).status, 401);
});

test("FR-A02: unlimited devices per user (7+ devices for one user), but at most 10 open claim tokens", db, async () => {
  const owned = () => Number(q(`select count(*) from public.devices where owner_id = :'u'`, { u: A }));
  const n0 = owned();
  for (let i = 0; i < 6; i++) assert.equal((await claim("jwt-a", `nw-a0000000000${i}`)).status, 200);
  assert.equal(owned(), n0 + 6, "no cap on devices per user");
  assert.ok(owned() >= 7);
  q(`delete from public.claim_tokens where user_id = :'u'`, { u: A });
  for (let i = 0; i < 10; i++) assert.equal((await claimToken("jwt-a")).status, 201);
  const r = await handleClaimToken(new Request("http://x/claim-token", { method: "POST", headers: { authorization: "Bearer jwt-a" } }), deps);
  assert.equal(r.status, 429);
  assert.ok(r.headers.get("retry-after"));
  q(`delete from public.claim_tokens where user_id = :'u' and used_at is null`, { u: A });
});

test("FR-D04, FR-D02: 96 buffered samples in one batch are stored; replay is idempotent on (device, ts)", db, async () => {
  const first = await ingest(tokA, report(samples(96)));
  assert.equal(first.status, 200);
  assert.equal(first.body.accepted, 96); assert.equal(first.body.duplicates, 0); assert.equal(first.body.implausible, 0);
  assert.equal(first.body.fw_target, null);
  assert.equal(count("readings", devA), 96);
  const replay = await ingest(tokA, report(samples(96)));
  assert.equal(replay.status, 200, "all-duplicate batch is still 2xx so the device can clear its buffer");
  assert.equal(replay.body.accepted, 0); assert.equal(replay.body.duplicates, 96);
  assert.equal(count("readings", devA), 96);
  const overlap = await ingest(tokA, report(samples(100, T0 + 4 * 900)));   // 4 new + 96 already known
  assert.equal(overlap.body.accepted, 4); assert.equal(overlap.body.duplicates, 96);
  assert.equal(count("readings", devA), 100);
  const same = await ingest(tokA, report([{ ts: T0 + 99999, moisture_pct: 1 }, { ts: T0 + 99999, moisture_pct: 2 }]));
  assert.equal(same.body.accepted, 1, "duplicate ts inside one batch counts once");
  assert.equal(q(`select owner_id from public.readings where device_id = :'d' limit 1`, { d: devA }), A);
});

test("FR-D01: out-of-range samples are stored with plausible=false, not rejected; ts is shifted when the device clock is off", db, async () => {
  const r = await ingest(tokA, report([{ ts: T0 + 200000, temp_c: 99, moisture_pct: 50 }, { ts: T0 + 200900, temp_c: 20, moisture_pct: 50 }]));
  assert.equal(r.body.accepted, 2); assert.equal(r.body.implausible, 1);
  assert.equal(q(`select plausible from public.readings where device_id = :'d' and ts = to_timestamp(:'t')`, { d: devA, t: String(T0 + 200000) }), "f");
  // device clock 1000 s behind the server: ts shifted by +1000 s (skew > 120 s)
  const skew = await ingest(tokB, report([{ ts: T0 + 500000 }], { sent_at: Math.floor(Date.now() / 1000) - 1000 }));
  assert.equal(skew.status, 200);
  const shifted = Number(q(`select extract(epoch from ts)::bigint - :'t' from public.readings where device_id = :'d' and ts > to_timestamp(:'t' + 900)`, { d: devB, t: String(T0 + 500000) }));
  assert.ok(Math.abs(shifted - 1000) <= 5, `ts shifted by about 1000 s, got ${shifted}`);
});

test("FR-E03, FR-A07: events stored idempotently; critical ones set critical=true and raise an alert; hourly config/forecast/cal update the device", db, async () => {
  const body = report(samples(1, T0 + 300000), { forecast_h: 36.5, cal: { dry_raw: 3000, wet_raw: 1200 }, model: "m0", events: [{ ts: T0 + 300000, type: "waterlogged" }, { ts: T0 + 300001, type: "wetting" }] });
  const r = await ingest(tokA, body);
  assert.equal(r.status, 200);
  assert.equal(q(`select string_agg(type || ':' || critical, ',' order by type) from public.events where device_id = :'d'`, { d: devA }), "waterlogged:true,wetting:false");
  await ingest(tokA, body);
  assert.equal(count("events", devA), 2, "event replay does not duplicate");
  assert.equal(q(`select string_agg(type || ':' || critical, ',' order by type) from public.events where device_id = :'d'`, { d: devA }), "waterlogged:true,wetting:false", "replay leaves rows unchanged");
  assert.equal(q(`select count(*) from public.alerts where device_id = :'d' and kind = 'waterlogged' and resolved_at is null`, { d: devA }), "1");
  assert.equal(q(`select forecast_h || '/' || cal_dry_raw || '/' || cal_wet_raw || '/' || model_version || '/' || (last_seen_at is not null) from public.devices where id = :'d'`, { d: devA }), "36.5/3000/1200/m0/true");
});

test("NFR-06: device A's token cannot write device B; the body cannot name a device; B's rows are untouched", db, async () => {
  const before = { rb: count("readings", devB), eb: count("events", devB) };
  const r = await ingest(tokA, { ...report(samples(3, T0 + 700000)), device_id: devB });
  assert.equal(r.status, 400, "device_id in the body is an unknown property");
  const ok = await ingest(tokA, report(samples(3, T0 + 700000), { events: [{ ts: T0 + 700000, type: "sensor_fault" }] }));
  assert.equal(ok.status, 200);
  assert.deepEqual({ rb: count("readings", devB), eb: count("events", devB) }, before, "nothing landed on B");
  assert.equal(q(`select count(*) from public.readings where ts = to_timestamp(:'t') and device_id = :'b'`, { t: String(T0 + 700000), b: devB }), "0");
  // same timestamps from B land on B (the idempotency key is per device, no cross-device collision)
  const rb = await ingest(tokB, report(samples(3, T0 + 700000)));
  assert.equal(rb.body.accepted, 3);
  assert.equal(q(`select count(*) from public.readings where ts = to_timestamp(:'t') and owner_id = :'u'`, { t: String(T0 + 700000), u: B }), "1");
  assert.equal(q(`select count(distinct owner_id) from public.readings where device_id = :'d'`, { d: devB }), "1");
});

test("NFR-06: unknown, malformed, revoked and released tokens get 401 and write nothing", db, async () => {
  const n = count("readings", devA);
  assert.equal((await ingest("0".repeat(64), report(samples(1, T0 + 900000)))).body.error, "token_invalid");
  assert.equal((await ingest(tokA.toUpperCase(), report(samples(1, T0 + 900000)))).status, 401, "token compare is on the exact string");
  q(`update public.device_credentials set revoked_at = now() where device_id = :'d'`, { d: devA });
  const rev = await ingest(tokA, report(samples(1, T0 + 900000)));
  assert.equal(rev.status, 401); assert.equal(rev.body.error, "token_revoked");
  q(`update public.device_credentials set revoked_at = null where device_id = :'d'`, { d: devA });
  q(`update public.devices set owner_id = null where id = :'d'`, { d: devA });   // released (FR-A08)
  assert.equal((await ingest(tokA, report(samples(1, T0 + 900000)))).body.error, "token_revoked");
  q(`update public.devices set owner_id = :'u' where id = :'d'`, { u: A, d: devA });
  assert.equal(count("readings", devA), n);
});

test("FR-D03, FR-A08: re-claiming by the same user rotates the token (old one dies); a released device can be claimed by another user", db, async () => {
  const re = await claim("jwt-a", "nw-aaaaaaaaaaaa");
  assert.equal(re.status, 200); assert.equal(re.body.device_id, devA);
  assert.equal((await ingest(tokA, report(samples(1, T0 + 950000)))).body.error, "token_invalid", "old token replaced");
  tokA = re.body.device_token;
  assert.equal((await ingest(tokA, report(samples(1, T0 + 950000)))).status, 200);
  // release (FR-A08): owner cleared, plant link deliberately LEFT in place; the next claim by another user must drop it
  const plantA = q(`insert into public.plants(owner_id,name,location_type,soil_type) values (:'u','P','house','potting') returning id`, { u: A }).split("\n")[0];
  q(`update public.devices set owner_id = null, plant_id = :'p' where id = :'d'`, { d: devA, p: plantA });
  q(`update public.device_credentials set revoked_at = now() where device_id = :'d'`, { d: devA });
  const moved = await claim("jwt-b", "nw-aaaaaaaaaaaa");
  assert.equal(moved.status, 200);
  assert.equal(q(`select owner_id from public.devices where id = :'d'`, { d: devA }), B);
  assert.equal(q(`select plant_id is null from public.devices where id = :'d'`, { d: devA }), "t", "new owner does not inherit the previous owner's plant");
  assert.equal((await ingest(tokA, report(samples(1, T0 + 960000)))).body.error, "token_invalid", "previous owner's token is dead");
  assert.equal((await ingest(moved.body.device_token, report(samples(1, T0 + 960000)))).status, 200);
  assert.equal(q(`select count(distinct owner_id) from public.readings where device_id = :'d'`, { d: devA }), "2", "history stays with the owner at recording time (FR-A08)");
});

test("NFR-06, RLS: API roles cannot call the functions or read credentials/claim tokens", db, async () => {
  for (const role of ["anon", "authenticated"]) {
    for (const sql of [
      `select public.ingest_batch('00', '{}')`, `select public.device_claim('00','00','nw-aaaaaaaaaaaa',null,'1')`,
      `select public.issue_claim_token('${A}', '00')`]) {
      const r = psql(url!, `set role ${role}; ${sql};`);
      assert.ok(!r.ok && /permission denied/.test(r.err), `${role}: ${sql} -> ${r.err}`);
    }
    for (const t of ["device_credentials", "claim_tokens"]) {   // RLS on, no policy: zero rows even where the role has table grants
      assert.equal(psql(url!, `set role ${role}; select count(*) from public.${t}`).out, role === "anon" ? "" : "0", `${role} ${t}`);
    }
  }
  assert.ok(Number(q(`select count(*) from public.device_credentials`)) >= 2, "rows exist for the superuser");
  assert.ok(psql(url!, `set role service_role; select public.device_config('${devB}')`).ok, "service_role may call them");
});

// ---------------------------------------------------------------- boundary tests (QA gaps from the PR #45 review)
test("FR-D03: a claim token lives 15 minutes (not 14, not 150)", db, async () => {
  const ct = await claimToken("jwt-a");
  const secs = Number(q(`select extract(epoch from expires_at - now())::int from public.claim_tokens where encode(token_hash,'hex') = :'h'`, { h: await sha256Hex(ct.body.claim_token) }));
  assert.ok(secs >= 15 * 60 - 5 && secs <= 15 * 60, `lifetime ${secs} s, expected 900 s`);
  const api = (Date.parse(ct.body.expires_at) - Date.now()) / 1000;
  assert.ok(api > 15 * 60 - 10 && api <= 15 * 60 + 1, `expires_at in the response is ${api} s ahead`);
  q(`delete from public.claim_tokens where user_id = :'u' and used_at is null`, { u: A });
});

test("device-report.schema.json: sent_at skew tolerance is exactly 120 s (ts shifted only beyond it)", db, async () => {
  const recv = T0 + 5_000_000;   // fixed server receive time, passed explicitly so the boundary is exact
  const dev = await claim("jwt-a", "nw-5ce000000001");   // fresh device: tokA/devA were released and re-claimed by earlier tests
  const hash = await sha256Hex(dev.body.device_token);
  const ts = (k: number) => T0 + 6_000_000 + k;
  const run = (k: number, skew: number) => {
    const rep = { v: 1, sent_at: recv - skew, trigger: "scheduled", fw: "0.1.0", samples: [{ ts: ts(k), moisture_pct: 40 }] };
    q(`select public.ingest_batch(:'h', :'r'::jsonb, to_timestamp(:'t'))`, { h: hash, r: JSON.stringify(rep), t: String(recv) });
    return Number(q(`select count(*) from public.readings where device_id = :'d' and ts = to_timestamp(:'t')`, { d: dev.body.device_id, t: String(ts(k) + (Math.abs(skew) <= 120 ? 0 : skew)) }));
  };
  assert.equal(run(1, 120), 1, "device 120 s behind: not shifted");
  assert.equal(run(2, -120), 1, "device 120 s ahead: not shifted");
  assert.equal(run(3, 121), 1, "device 121 s behind: shifted by +121 s");
  assert.equal(run(4, -121), 1, "device 121 s ahead: shifted by -121 s");
  // the unshifted rows really are at the original ts, the shifted ones are not
  assert.equal(Number(q(`select count(*) from public.readings where device_id = :'d' and ts in (to_timestamp(:'a'), to_timestamp(:'b'))`, { d: dev.body.device_id, a: String(ts(3)), b: String(ts(4)) })), 0);
});

test("FR-D04, FR-E03: events are capped at 32 per report, samples/events/sent_at need ts >= 1700000000", () => {
  const valid = JSON.parse(readFileSync(join(fx, "device-report.valid.json"), "utf8"));
  const evs = (n: number) => Array.from({ length: n }, (_, i) => ({ ts: T0 - 60 * i, type: "wetting" }));
  assert.equal(validateReport({ ...valid, events: evs(32) }), null, "32 events accepted");
  assert.equal(validateReport({ ...valid, events: evs(33) })?.status, 400, "33 events rejected");
  assert.equal(validateReport({ ...valid, events: evs(31) }), null);
  const MIN = 1700000000;
  assert.equal(validateReport({ ...valid, sent_at: MIN }), null, "sent_at = MIN_TS accepted");
  assert.equal(validateReport({ ...valid, sent_at: MIN - 1 })?.status, 400, "sent_at = MIN_TS - 1 rejected");
  assert.equal(validateReport({ ...valid, samples: [{ ts: MIN }] }), null, "sample ts = MIN_TS accepted");
  assert.equal(validateReport({ ...valid, samples: [{ ts: MIN - 1 }] })?.status, 400, "sample ts = MIN_TS - 1 rejected");
  assert.equal(validateReport({ ...valid, events: [{ ts: MIN, type: "wetting" }] }), null, "event ts = MIN_TS accepted");
  assert.equal(validateReport({ ...valid, events: [{ ts: MIN - 1, type: "wetting" }] })?.status, 400, "event ts = MIN_TS - 1 rejected");
});

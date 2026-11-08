// Unit tests for the device API handlers with a MOCK database layer (no Supabase, no network).
// Run: node --test supabase/functions/_shared/   (Node >= 22.18 strips TypeScript types natively; no dependencies)
// The SQL behaviour (idempotency, plausibility, alerts) is tested against real Postgres in test/device_api.sql.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { type Db, DbError, handleClaim, handleIngest, type IngestResult } from "./handlers.ts";
import { sha256ByteaHex } from "./crypto.ts";

const GOOD = "ab".repeat(32);                       // a valid-looking 256-bit hex device token
const fixture = readFileSync(new URL("../../../../docs/interfaces/fixtures/device-report.valid.json", import.meta.url), "utf8");
const okResult: IngestResult = { server_time: 1, accepted: 4, duplicates: 0, implausible: 0, config: { dry_pct: 25 }, fw_target: null, model_target: null };

/** Mock DB: knows exactly one token (GOOD -> device d1), optionally revoked. Records calls. */
function mockDb(opts: { revoked?: boolean; claim?: () => Promise<any>; ingest?: () => Promise<IngestResult> } = {}) {
  const calls = { auth: [] as string[], ingest: 0, claim: [] as any[] };
  const db: Db = {
    async authenticate(h) {
      calls.auth.push(h);
      if (h !== (await sha256ByteaHex(GOOD))) return { device_id: null, status: "invalid" };
      return { device_id: "d1", status: opts.revoked ? "revoked" : "ok" };
    },
    async claim(a) { calls.claim.push(a); return opts.claim ? opts.claim() : { device_id: "d1", server_time: 5, config: {} }; },
    async ingest() { calls.ingest++; return opts.ingest ? opts.ingest() : okResult; },
  };
  return { db, calls };
}

// ---- /ingest authentication (FR-D03, NFR-06)
test("ingest: missing / malformed bearer -> 401 token_invalid, DB never touched", async () => {
  const { db, calls } = mockDb();
  for (const h of [null, "", "Bearer", "Bearer xyz", `Basic ${GOOD}`, `Bearer ${GOOD.toUpperCase()}`, `Bearer ${GOOD}00`]) {
    const r = await handleIngest(h, fixture, db);
    assert.equal(r.status, 401); assert.deepEqual(r.body, { error: "token_invalid" });
  }
  assert.equal(calls.auth.length, 0); assert.equal(calls.ingest, 0);
});
test("ingest: unknown token -> 401 token_invalid and nothing is written", async () => {
  const { db, calls } = mockDb();
  const r = await handleIngest("Bearer " + "cd".repeat(32), fixture, db);
  assert.equal(r.status, 401); assert.deepEqual(r.body, { error: "token_invalid" }); assert.equal(calls.ingest, 0);
});
test("ingest: revoked token -> 401 token_revoked and nothing is written", async () => {
  const { db, calls } = mockDb({ revoked: true });
  const r = await handleIngest(`Bearer ${GOOD}`, fixture, db);
  assert.equal(r.status, 401); assert.deepEqual(r.body, { error: "token_revoked" }); assert.equal(calls.ingest, 0);
});
test("ingest: only the SHA-256 of the token reaches the DB layer, never the token (ADR-004)", async () => {
  const { db, calls } = mockDb();
  await handleIngest(`Bearer ${GOOD}`, fixture, db);
  assert.equal(calls.auth.length, 1); assert.match(calls.auth[0], /^\\x[0-9a-f]{64}$/); assert.ok(!calls.auth[0].includes(GOOD));
});

// ---- /ingest validation + happy path
test("ingest: valid fixture -> 200 with counts, config and OTA fields", async () => {
  const { db, calls } = mockDb();
  const r = await handleIngest(`Bearer ${GOOD}`, fixture, db);
  assert.equal(r.status, 200); assert.equal(calls.ingest, 1);
  assert.deepEqual(Object.keys(r.body as object).sort(), ["accepted", "config", "duplicates", "fw_target", "implausible", "model_target", "server_time"]);
});
test("ingest: schema violations -> 400 bad_request, nothing written", async () => {
  const { db, calls } = mockDb();
  const base = JSON.parse(fixture);
  const bad: unknown[] = [
    "not json", { ...base, v: 2 }, { ...base, trigger: "now" }, { ...base, samples: [] }, { ...base, extra: 1 },
    { ...base, samples: [{ ts: 5, moisture_pct: 1 }] }, { ...base, samples: [{ ts: 1799000000, temp_c: "hot" }] },
    { ...base, events: [{ ts: 1799000000, type: "flood" }] }, { ...base, sent_at: 1.5 },
  ];
  for (const b of bad) {
    const r = await handleIngest(`Bearer ${GOOD}`, typeof b === "string" ? b : JSON.stringify(b), db);
    assert.equal(r.status, 400, JSON.stringify(b)); assert.equal((r.body as any).error, "bad_request");
  }
  assert.equal(calls.ingest, 0);
});
test("ingest: implausible values are NOT rejected by the function (FR-D01: stored flagged by SQL)", async () => {
  const { db, calls } = mockDb();
  const b = JSON.parse(fixture); b.samples[0].temp_c = 99; b.samples[0].vbat_mv = 2000;
  const r = await handleIngest(`Bearer ${GOOD}`, JSON.stringify(b), db);
  assert.equal(r.status, 200); assert.equal(calls.ingest, 1);
});
test("ingest: 96 samples (24 h buffer, FR-D04) accepted, 192 accepted, 193 -> 413", async () => {
  const { db } = mockDb();
  const mk = (n: number) => JSON.stringify({ ...JSON.parse(fixture), samples: Array.from({ length: n }, (_, i) => ({ ts: 1798000000 + i * 900, moisture_pct: 40 })) });
  assert.equal((await handleIngest(`Bearer ${GOOD}`, mk(96), db)).status, 200);
  assert.equal((await handleIngest(`Bearer ${GOOD}`, mk(192), db)).status, 200);
  assert.equal((await handleIngest(`Bearer ${GOOD}`, mk(193), db)).status, 413);
});
test("ingest: body over 64 KiB -> 413", async () => {
  const { db } = mockDb();
  assert.equal((await handleIngest(`Bearer ${GOOD}`, " ".repeat(70000), db)).status, 413);
});
test("ingest: replay is passed straight to the idempotent SQL; duplicates come back as 200 (openapi)", async () => {
  const { db } = mockDb({ ingest: async () => ({ ...okResult, accepted: 0, duplicates: 4 }) });
  const r = await handleIngest(`Bearer ${GOOD}`, fixture, db);
  assert.equal(r.status, 200); assert.equal((r.body as any).duplicates, 4);
});
test("ingest: device released between auth and insert (NW403) -> 401 token_revoked", async () => {
  const { db } = mockDb({ ingest: async () => { throw new DbError("NW403"); } });
  assert.deepEqual((await handleIngest(`Bearer ${GOOD}`, fixture, db)).body, { error: "token_revoked" });
});
test("ingest: OTA artefact gets a signed URL (FR-D05)", async () => {
  const art = { version: "0.3.0", storage_path: "fw/0.3.0.bin", sha256: "0".repeat(64), size_bytes: 10, min_battery_mv: 3700 };
  const { db } = mockDb({ ingest: async () => ({ ...okResult, fw_target: art }) });
  db.signUrl = async (p) => `https://signed.example/${p}?t=1`;
  const r = await handleIngest(`Bearer ${GOOD}`, fixture, db);
  assert.equal((r.body as any).fw_target.url, "https://signed.example/fw/0.3.0.bin?t=1");
});

// ---- /device-claim (FR-D03, FR-A08)
const claimBody = { hw_id: "nw-a1b2c3d4e5f6", claim_token: "tok", fw: "0.1.0" };
test("claim: success returns a fresh 64-hex token; DB receives hashes only", async () => {
  const { db, calls } = mockDb();
  const r = await handleClaim(JSON.stringify(claimBody), db);
  const b = r.body as any;
  assert.equal(r.status, 200); assert.match(b.device_token, /^[0-9a-f]{64}$/);
  assert.equal(calls.claim[0].token_hash, await sha256ByteaHex(b.device_token));
  assert.equal(calls.claim[0].claim_hash, await sha256ByteaHex("tok"));
  assert.ok(!JSON.stringify(calls.claim[0]).includes(b.device_token)); assert.ok(!JSON.stringify(calls.claim[0]).includes('"tok"'));
  const r2 = await handleClaim(JSON.stringify(claimBody), db);
  assert.notEqual((r2.body as any).device_token, b.device_token);          // never reused
});
test("claim: NW401 -> 401 claim_token_invalid; NW409 -> 409 device_owned; other errors propagate", async () => {
  assert.deepEqual((await handleClaim(JSON.stringify(claimBody), mockDb({ claim: async () => { throw new DbError("NW401"); } }).db)).body, { error: "claim_token_invalid" });
  const r = await handleClaim(JSON.stringify(claimBody), mockDb({ claim: async () => { throw new DbError("NW409"); } }).db);
  assert.equal(r.status, 409); assert.equal((r.body as any).error, "device_owned");
  await assert.rejects(handleClaim(JSON.stringify(claimBody), mockDb({ claim: async () => { throw new DbError("XX000"); } }).db));
});
test("claim: bad bodies -> 400 and the DB is not called", async () => {
  const { db, calls } = mockDb();
  for (const b of [{ ...claimBody, hw_id: "NW-A1B2C3D4E5F6" }, { ...claimBody, hw_id: "nw-123" }, { hw_id: claimBody.hw_id, fw: "1" },
                   { ...claimBody, extra: true }, { ...claimBody, name: "x".repeat(81) }, "nope"]) {
    const r = await handleClaim(typeof b === "string" ? b : JSON.stringify(b), db);
    assert.equal(r.status, 400, JSON.stringify(b));
  }
  assert.equal(calls.claim.length, 0);
});

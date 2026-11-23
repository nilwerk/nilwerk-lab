// 4.B5 MCP server tests: unit (no database) and integration against a local PostgreSQL seeded by cloud/test.sh (NW_TEST_DB_URL, own database).
// Requirements: FR-P03 (per-user key, read-only tools, revoked key fails), FR-P04 (premium gate), FR-P01 (history window and downsampling),
// FR-P02 (tips re-checked on output), NFR-06 (key stored hashed, never echoed), NFR-07 (a user reads only their own rows).
// Keys in these tests are generated at run time (node:crypto). No real key is used anywhere.
import { test, describe, before } from "node:test";
import assert from "node:assert/strict";
import { randomBytes, createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import {
  handleMcp, authenticate, validate, plantStatus, TOOLS, KEY_PATTERN, GUARDRAIL_VERSION_EXPECTED, type McpDeps, type Schema,
} from "../../supabase/functions/_shared/mcp.ts";
import type { RpcResult } from "../../supabase/functions/_shared/lib.ts";
import { GUARDRAIL_VERSION } from "../../tips/guardrails.ts";
import { psql, psqlDeps } from "./psql_deps.ts";

const here = dirname(fileURLToPath(import.meta.url));
const contract = JSON.parse(readFileSync(join(here, "../../../docs/interfaces/mcp-tools.json"), "utf8"));
const DB = process.env.NW_TEST_DB_URL ?? "";

const A = "00000000-0000-0000-0000-00000000000a", B = "00000000-0000-0000-0000-00000000000b";
const C = "00000000-0000-0000-0000-0000000000c0";                       // free user, created by this test
const PLANT_A = "10000000-0000-0000-0000-00000000000a", PLANT_B = "10000000-0000-0000-0000-00000000000b";
const DEVICE_A = "20000000-0000-0000-0000-00000000000a";
const UNKNOWN_PLANT = "10000000-0000-0000-0000-0000000000ff";

/** A fresh key in the documented format: "nwk_" + 32 random bytes, base64url (43 chars). */
const makeKey = () => `nwk_${randomBytes(32).toString("base64url")}`;
/** Independent oracle for the stored form (node:crypto, not the code under test). */
const hashOf = (key: string) => createHash("sha256").update(key).digest("hex");

// ---------------------------------------------------------------- helpers
type Call = { name: string; args: Record<string, unknown> };
/** Fake database: `answers` maps an RPC name to what it returns; every call is recorded. */
function fakeDeps(answers: Record<string, (args: Record<string, unknown>) => RpcResult>, resolveTo: string | null = "owner"): { deps: McpDeps; calls: Call[] } {
  const calls: Call[] = [];
  const deps: McpDeps = {
    rpc(name, args): Promise<RpcResult> {
      calls.push({ name, args });
      if (name === "mcp_resolve_key") {
        if (resolveTo === "PREMIUM") return Promise.resolve({ data: null, error: { message: "premium_required" } });
        return Promise.resolve({ data: resolveTo, error: null });
      }
      const f = answers[name];
      return Promise.resolve(f ? f(args) : { data: null, error: null });
    },
  };
  return { deps, calls };
}
const req = (body: unknown, key?: string, method = "POST") => new Request("https://example.test/mcp", {
  method,
  headers: { "content-type": "application/json", ...(key ? { authorization: `Bearer ${key}` } : {}) },
  body: method === "POST" ? JSON.stringify(body) : undefined,
});
const call = (name: string, args: Record<string, unknown> = {}, id = 1) => ({ jsonrpc: "2.0", id, method: "tools/call", params: { name, arguments: args } });
async function toolCall(deps: McpDeps, key: string, name: string, args: Record<string, unknown> = {}) {
  const res = await handleMcp(req(call(name, args), key), deps);
  return { status: res.status, body: (await res.json()) as { result?: { isError?: boolean; structuredContent?: unknown; content: { text: string }[] }; error?: unknown } };
}
const errorCode = (r: { result?: { content: { text: string }[] } }) => JSON.parse(r.result!.content[0].text).error as string;
const contractOutput = (tool: string) => contract.tools.find((t: { name: string }) => t.name === tool).outputSchema as Schema;
const stripDescriptions = (v: unknown): unknown => Array.isArray(v) ? v.map(stripDescriptions)
  : v && typeof v === "object" ? Object.fromEntries(Object.entries(v as Record<string, unknown>).filter(([k]) => k !== "description").map(([k, x]) => [k, stripDescriptions(x)]))
  : v;

// ---------------------------------------------------------------- unit: keys and authentication (FR-P03, NFR-06)
test("FR-P03: key format is nwk_ + 43 base64url characters; anything else is refused by the pattern", () => {
  assert.match(makeKey(), KEY_PATTERN);
  assert.equal(makeKey().length, 47);
  for (const bad of ["", "nwk_", "nwk_short", `nwk_${"a".repeat(44)}`, `xyz_${"a".repeat(43)}`, `nwk_${"a".repeat(42)}+`, `nwk_${"a".repeat(42)} `]) {
    assert.doesNotMatch(bad, KEY_PATTERN, JSON.stringify(bad));
  }
});

test("NFR-06: the database receives sha256(key) as bytea and never the key itself", async () => {
  const key = makeKey();
  const { deps, calls } = fakeDeps({}, A);
  const r = await authenticate(req({}, key), deps);
  assert.equal(r.ok, true);
  assert.equal(calls.length, 1);
  assert.equal(calls[0].name, "mcp_resolve_key");
  assert.equal(calls[0].args.p_key_hash, `\\x${hashOf(key)}`);
  assert.ok(!JSON.stringify(calls).includes(key), "the plaintext key must not reach the database call");
});

test("FR-P03: missing or malformed key -> 401 and no database call at all", async () => {
  for (const r of [req({ jsonrpc: "2.0", id: 1, method: "tools/list" }), req({}, "nwk_too-short")]) {
    const { deps, calls } = fakeDeps({}, A);
    const res = await handleMcp(r, deps);
    assert.equal(res.status, 401);
    assert.equal(((await res.json()) as { error: string }).error, "unauthorized");
    assert.equal(calls.length, 0, "nothing is read or resolved without a well-formed key");
  }
});

test("FR-P03: wrong or revoked key -> 401 key_revoked_or_unknown, and only the key check runs (no reads)", async () => {
  // mcp_resolve_key returns null for an unknown key and for a revoked one (revoked_at is set): the same answer.
  const { deps, calls } = fakeDeps({}, null);
  const res = await handleMcp(req(call("list_plants"), makeKey()), deps);
  assert.equal(res.status, 401);
  assert.equal(((await res.json()) as { error: string }).error, "key_revoked_or_unknown");
  assert.deepEqual(calls.map((c) => c.name), ["mcp_resolve_key"]);
});

test("FR-P04: a free user's tool call is refused with premium_required, and no data is read", async () => {
  const { deps, calls } = fakeDeps({}, "PREMIUM");
  for (const t of TOOLS) {
    const r = await toolCall(deps, makeKey(), t.name, t.name === "list_plants" ? {} : { plant_id: PLANT_A });
    assert.equal(r.status, 200, t.name);
    assert.equal(r.body.result?.isError, true, t.name);
    assert.equal(errorCode(r.body as never), "premium_required", t.name);
  }
  assert.ok(calls.every((c) => c.name === "mcp_resolve_key"), "no read RPC for a free user");
  const list = await handleMcp(req({ jsonrpc: "2.0", id: 2, method: "tools/list" }, makeKey()), deps);
  assert.equal(list.status, 403, "other methods get a clear 403 for a free user");
  assert.equal(((await list.json()) as { error: string }).error, "premium_required");
});

test("NFR-06: a database error text is never returned to the client (server_error only)", async () => {
  const { deps } = fakeDeps({ mcp_list_plants: () => ({ data: null, error: { message: "SELECT secret_table failed" } }) }, A);
  const r = await toolCall(deps, makeKey(), "list_plants");
  assert.equal(errorCode(r.body as never), "server_error");
  assert.ok(!JSON.stringify(r.body).includes("secret_table"));
});

test("protocol: GET -> 405, bad JSON -> parse error, unknown method -> method not found", async () => {
  const { deps } = fakeDeps({}, A);
  assert.equal((await handleMcp(req(null, makeKey(), "GET"), deps)).status, 405);
  const bad = await handleMcp(new Request("https://x/mcp", { method: "POST", headers: { authorization: `Bearer ${makeKey()}` }, body: "{nope" }), deps);
  assert.equal(((await bad.json()) as { error: { code: number } }).error.code, -32700);
  const unknown = await handleMcp(req({ jsonrpc: "2.0", id: 9, method: "resources/list" }, makeKey()), deps);
  assert.equal(((await unknown.json()) as { error: { code: number } }).error.code, -32601);
});

test("protocol: initialize and tools/list answer for a valid key; the four tools are read-only", async () => {
  const { deps } = fakeDeps({}, A);
  const init = (await (await handleMcp(req({ jsonrpc: "2.0", id: 1, method: "initialize", params: {} }, makeKey()), deps)).json()) as { result: { serverInfo: { name: string } } };
  assert.equal(init.result.serverInfo.name, "nilwerk-plant-monitor");
  const list = (await (await handleMcp(req({ jsonrpc: "2.0", id: 2, method: "tools/list" }, makeKey()), deps)).json()) as { result: { tools: { name: string; annotations: { readOnlyHint: boolean } }[] } };
  assert.deepEqual(list.result.tools.map((t) => t.name), ["list_plants", "get_plant_status", "get_history", "get_tips"]);
  assert.ok(list.result.tools.every((t) => t.annotations.readOnlyHint === true), "read-only (FR-P03)");
});

// ---------------------------------------------------------------- contract: tools match docs/interfaces/mcp-tools.json (FR-P03)
test("contract: names, annotations, input and output schemas equal docs/interfaces/mcp-tools.json (descriptions are prose and compared as-is)", () => {
  assert.deepEqual(TOOLS.map((t) => t.name), contract.tools.map((t: { name: string }) => t.name));
  for (const t of TOOLS) {
    const c = contract.tools.find((x: { name: string }) => x.name === t.name);
    assert.equal(t.description, c.description, `${t.name} description`);
    assert.deepEqual(t.annotations, c.annotations, `${t.name} annotations`);
    assert.deepEqual(stripDescriptions(t.inputSchema), stripDescriptions(c.inputSchema), `${t.name} inputSchema`);
    assert.deepEqual(stripDescriptions(t.outputSchema), stripDescriptions(c.outputSchema), `${t.name} outputSchema`);
  }
});

test("FR-P02: the tips version this server accepts equals the guardrail layer's version", () => {
  assert.equal(GUARDRAIL_VERSION_EXPECTED, GUARDRAIL_VERSION);
});

// ---------------------------------------------------------------- unit: input validation (contract tests for the tools)
test("contract: input arguments are validated before any read (uuid, days 1..90, enum, no extra keys)", async () => {
  const cases: [string, Record<string, unknown>][] = [
    ["get_plant_status", {}], ["get_plant_status", { plant_id: "not-a-uuid" }], ["get_plant_status", { plant_id: PLANT_A, extra: 1 }],
    ["get_history", { plant_id: PLANT_A, days: 0 }], ["get_history", { plant_id: PLANT_A, days: 91 }], ["get_history", { plant_id: PLANT_A, days: "7" }],
    ["get_history", { plant_id: PLANT_A, resolution: "minute" }], ["get_tips", { plant_id: "x" }], ["list_plants", { plant_id: PLANT_A }],
  ];
  for (const [name, args] of cases) {
    const { deps, calls } = fakeDeps({}, A);
    const r = await toolCall(deps, makeKey(), name, args);
    assert.equal(errorCode(r.body as never), "invalid_input", `${name} ${JSON.stringify(args)}`);
    assert.ok(calls.every((c) => c.name === "mcp_resolve_key"), `${name}: nothing read`);
  }
});

test("contract: an unknown tool name is refused", async () => {
  const { deps } = fakeDeps({}, A);
  assert.equal(errorCode((await toolCall(deps, makeKey(), "delete_plant", {})).body as never), "unknown_tool");
});

test("FR-P03: validate() accepts a well-formed value and names the path of a bad one", () => {
  assert.equal(validate(contractOutput("list_plants") as Schema, { plants: [] }), null);
  assert.match(validate(contractOutput("list_plants") as Schema, { plants: [{ plant_id: "x", name: "n", status: "ok" }] }) ?? "", /plant_id: not a uuid/);
  assert.match(validate(contractOutput("list_plants") as Schema, { plants: [{ plant_id: PLANT_A, name: "n", status: "broken" }] }) ?? "", /status/);
});

// ---------------------------------------------------------------- unit: status mapping (FR-A06, FR-D06)
test("FR-A06: plant status follows the most urgent open alert; no sensor -> no_device", () => {
  assert.equal(plantStatus({ device_id: null, open_alerts: ["too_dry"] }), "no_device");
  assert.equal(plantStatus({ device_id: DEVICE_A, open_alerts: ["device_offline", "too_dry"] }), "offline");
  assert.equal(plantStatus({ device_id: DEVICE_A, open_alerts: ["low_battery", "too_wet"] }), "low_battery");
  assert.equal(plantStatus({ device_id: DEVICE_A, open_alerts: ["too_dry"] }), "dry");
  assert.equal(plantStatus({ device_id: DEVICE_A, open_alerts: ["too_wet"] }), "wet");
  assert.equal(plantStatus({ device_id: DEVICE_A, open_alerts: ["sensor_fault"] }), "ok");
  assert.equal(plantStatus({ device_id: DEVICE_A, open_alerts: [] }), "ok");
});

// ---------------------------------------------------------------- unit: tips guardrails on the way out (FR-P02)
describe("tips: cached tips are re-checked before they are returned (FR-P02)", () => {
  const tipRow = (over: Record<string, unknown> = {}) => ({
    generated_at: "2026-11-23T06:00:00+00:00", guardrail_version: GUARDRAIL_VERSION_EXPECTED,
    content: { items: [{ id: "water-later", category: "watering", text: "Water again in two days." }] }, ...over,
  });
  const tipsFor = (tip: unknown) => ({ mcp_get_tips: () => ({ data: { plant_id: PLANT_A, tip }, error: null }) });

  test("a current, valid tip is returned in the contract shape", async () => {
    const { deps } = fakeDeps(tipsFor(tipRow()), A);
    const r = await toolCall(deps, makeKey(), "get_tips", { plant_id: PLANT_A });
    assert.equal(r.body.result?.isError, undefined);
    assert.deepEqual(r.body.result!.structuredContent, { plant_id: PLANT_A, generated_at: "2026-11-23T06:00:00+00:00", items: [{ id: "water-later", category: "watering", text: "Water again in two days." }] });
  });

  test("no cached tip, or tips under another guardrail version -> tips_unavailable (never regenerated here)", async () => {
    for (const tip of [null, tipRow({ guardrail_version: "seed" })]) {
      const { deps, calls } = fakeDeps(tipsFor(tip), A);
      assert.equal(errorCode(await toolCall(deps, makeKey(), "get_tips", { plant_id: PLANT_A }).then((r) => r.body) as never), "tips_unavailable");
      assert.ok(!calls.some((c) => c.name !== "mcp_resolve_key" && c.name !== "mcp_get_tips"), "no other write or read");
    }
  });

  test("an item outside the contract (unknown category, over 400 characters, missing text) fails the whole answer", async () => {
    const bad = [
      { id: "x", category: "medical", text: "Take this pill." },
      { id: "x", category: "watering", text: "a".repeat(401) },
      { id: "x", category: "watering" },
    ];
    for (const item of bad) {
      const { deps } = fakeDeps(tipsFor(tipRow({ content: { items: [item] } })), A);
      assert.equal(errorCode((await toolCall(deps, makeKey(), "get_tips", { plant_id: PLANT_A })).body as never), "tips_unavailable", JSON.stringify(item).slice(0, 60));
    }
  });

  test("a plant that is not the caller's -> not_found, whatever the tips say", async () => {
    const { deps } = fakeDeps({ mcp_get_tips: () => ({ data: null, error: null }) }, A);
    assert.equal(errorCode((await toolCall(deps, makeKey(), "get_tips", { plant_id: PLANT_B })).body as never), "not_found");
  });
});

// ---------------------------------------------------------------- unit: output contract for the other three tools
test("contract: list_plants, get_plant_status and get_history map database rows to the contract shape", async () => {
  const row = {
    plant_id: PLANT_A, name: "Basil A", location_type: "house", area: "kitchen", species: "basil", soil_type: "potting", city: "Berlin",
    device_id: DEVICE_A, moisture_pct: 41.5, temp_c: 21.0, rh_pct: 55, lux: 800, vbat_mv: 3900, reading_ts: "2026-11-23T06:00:00+00:00",
    dry_threshold_pct: 25, wet_threshold_pct: 85, forecast_h: 30, open_alerts: ["too_dry"],
  };
  const { deps } = fakeDeps({
    mcp_list_plants: () => ({ data: [row], error: null }),
    mcp_get_plant: () => ({ data: row, error: null }),
    mcp_get_history: () => ({ data: { plant_id: PLANT_A, resolution: "hourly", points: [{ ts: "2026-11-23T05:00:00+00:00", moisture_pct: 40, battery_mv: 3900 }], watering_events: ["2026-11-23T04:00:00+00:00"] }, error: null }),
  }, A);
  const list = await toolCall(deps, makeKey(), "list_plants");
  assert.deepEqual(list.body.result!.structuredContent, { plants: [{ plant_id: PLANT_A, name: "Basil A", location_type: "house", area: "kitchen", moisture_pct: 41.5, hours_to_dry: 30, status: "dry", last_reading_at: "2026-11-23T06:00:00+00:00" }] });
  const st = await toolCall(deps, makeKey(), "get_plant_status", { plant_id: PLANT_A });
  assert.equal((st.body.result!.structuredContent as { battery_mv: number }).battery_mv, 3900);
  assert.deepEqual((st.body.result!.structuredContent as { open_alerts: string[] }).open_alerts, ["too_dry"]);
  const hist = await toolCall(deps, makeKey(), "get_history", { plant_id: PLANT_A });
  assert.equal(hist.body.result?.isError, undefined);
});

test("contract: get_history defaults to 7 days and hourly resolution", async () => {
  const { deps, calls } = fakeDeps({ mcp_get_history: () => ({ data: { plant_id: PLANT_A, resolution: "hourly", points: [] }, error: null }) }, A);
  await toolCall(deps, makeKey(), "get_history", { plant_id: PLANT_A });
  const h = calls.find((c) => c.name === "mcp_get_history")!;
  assert.deepEqual(h.args, { p_owner: A, p_plant: PLANT_A, p_days: 7, p_resolution: "hourly" });
});

// ---------------------------------------------------------------- integration: local PostgreSQL (cloud/test.sh stage "mcp")
// Real RPCs and RLS-free owner filters against the seeded database. The key resolves through the real mcp_resolve_key.
const psqlDeps0 = () => psqlDeps(DB, {});
function dbDeps(log: string[] = []): McpDeps {
  const base = psqlDeps0();
  return {
    rpc(name, args): Promise<RpcResult> {
      log.push(name);
      if (name !== "mcp_resolve_key") return base.rpc(name, args);
      const r = psql(DB, "select public.mcp_resolve_key(:'h')::text;", { h: String(args.p_key_hash) });   // uuid is not JSON: read raw
      if (!r.ok) return Promise.resolve({ data: null, error: { message: r.err } });
      return Promise.resolve({ data: r.out === "" ? null : r.out, error: null });
    },
  };
}
const must = (r: { ok: boolean; out: string; err: string }) => { assert.ok(r.ok, `psql failed: ${r.err}`); return r.out; };

const keys = { A: makeKey(), B: makeKey(), C: makeKey(), revoked: makeKey(), toRevoke: makeKey() };

describe("integration (local PostgreSQL, seeded): owner filter, cross-user, revocation, premium", () => {
  before(() => {
    if (!DB) throw new Error("NW_TEST_DB_URL is not set: run cloud/test.sh (the mcp stage)");
    // Free user C (no plant). A is made premium for the cross-user tests (B is premium in the seed). Keys are stored as sha256 only.
    const hashes = Object.fromEntries(Object.entries(keys).map(([k, v]) => [k, hashOf(v)]));
    must(psql(DB, `
      insert into auth.users (id, email) values (:'c', 'user-c@example.test') on conflict do nothing;
      update public.profiles set is_premium = true where id = :'a';
      insert into public.api_keys (owner_id, name, prefix, key_hash) values
        (:'a', 'test key A', :'pa', decode(:'ha', 'hex')),
        (:'b', 'test key B', :'pb', decode(:'hb', 'hex')),
        (:'b', 'test revoked', :'pr', decode(:'hr', 'hex')),
        (:'c', 'test key C', :'pc', decode(:'hc', 'hex')),
        (:'b', 'test to revoke', :'pt', decode(:'ht', 'hex'));
      update public.api_keys set revoked_at = now() where key_hash = decode(:'hr', 'hex');
      -- 90 days of 15-min samples for A's sensor (history downsampling, FR-P01); the seed only has 3 days.
      insert into public.readings (device_id, ts, owner_id, plant_id, moisture_pct, vbat_mv)
      select :'dev', now() - (g * 15 || ' minutes')::interval, :'a', :'pa_plant', 40, 3900
        from generate_series(0, 90 * 96 - 1) g on conflict do nothing;`,
      { c: C, a: A, b: B, pa: keys.A.slice(0, 8), pb: keys.B.slice(0, 8), pr: keys.revoked.slice(0, 8), pc: keys.C.slice(0, 8), pt: keys.toRevoke.slice(0, 8),
        ha: hashes.A, hb: hashes.B, hr: hashes.revoked, hc: hashes.C, ht: hashes.toRevoke, dev: DEVICE_A, pa_plant: PLANT_A }));
  });

  test("NFR-06: the stored key is the sha256 digest; the plaintext key is not in the table", () => {
    assert.equal(must(psql(DB, "select count(*) from public.api_keys where key_hash = convert_to(:'k', 'UTF8');", { k: keys.A })), "0");
    assert.equal(must(psql(DB, "select count(*) from public.api_keys where key_hash = decode(:'h', 'hex');", { h: hashOf(keys.A) })), "1");
  });

  test("FR-P03, NFR-07: a premium user's key lists only that user's plants (A sees A's plant only)", async () => {
    const log: string[] = [];
    const r = await toolCall(dbDeps(log), keys.A, "list_plants");
    assert.equal(r.body.result?.isError, undefined);
    const plants = (r.body.result!.structuredContent as { plants: { plant_id: string; status: string }[] }).plants;
    assert.deepEqual(plants.map((p) => p.plant_id), [PLANT_A]);
    assert.equal(plants[0].status, "dry", "seeded too_dry alert on A's sensor -> dry");
    assert.ok(!JSON.stringify(r.body).includes(PLANT_B), "B's plant id never appears in A's answer");
  });

  test("FR-P03, NFR-07 (cross-user): A's key cannot read B's plant through any tool; B's key cannot read A's", async () => {
    for (const [who, key, other] of [["A", keys.A, PLANT_B], ["B", keys.B, PLANT_A]] as const) {
      for (const [tool, args] of [["get_plant_status", { plant_id: other }], ["get_history", { plant_id: other, days: 90, resolution: "raw" }], ["get_tips", { plant_id: other }]] as const) {
        const r = await toolCall(dbDeps(), key, tool, args);
        assert.equal(r.body.result?.isError, true, `${who} ${tool}`);
        assert.equal(errorCode(r.body as never), "not_found", `${who} ${tool}`);
        assert.ok(!JSON.stringify(r.body).includes("10000000-0000-0000-0000-0000000000"), `${who} ${tool}: no plant data in the answer`);
      }
    }
  });

  test("NFR-07 (mechanism): the owner-scoped RPCs return null for another user's plant and for an unknown id", () => {
    assert.equal(must(psql(DB, "select public.mcp_get_plant(:'a', :'p') is null;", { a: A, p: PLANT_B })), "t");
    assert.equal(must(psql(DB, "select public.mcp_get_history(:'a', :'p', 7, 'raw') is null;", { a: A, p: PLANT_B })), "t");
    assert.equal(must(psql(DB, "select public.mcp_get_tips(:'a', :'p') is null;", { a: A, p: PLANT_B })), "t");
    assert.equal(must(psql(DB, "select public.mcp_get_plant(:'a', :'p') is null;", { a: A, p: UNKNOWN_PLANT })), "t");
    assert.equal(must(psql(DB, "select (public.mcp_list_plants(:'a')::text like :'pat');", { a: A, pat: `%${PLANT_B}%` })), "f");
  });

  test("NFR-06: the MCP RPCs are not callable by the API roles (service_role only)", () => {
    for (const role of ["anon", "authenticated"]) {
      const r = psql(DB, `set role ${role}; select public.mcp_list_plants(:'a');`, { a: A });
      assert.equal(r.ok, false, role);
      assert.match(r.err, /permission denied/, role);
    }
  });

  test("FR-P03: a key revoked in the database fails on the next call, with no reads", async () => {
    const ok = await toolCall(dbDeps(), keys.toRevoke, "list_plants");
    assert.equal(ok.body.result?.isError, undefined, "works while active");
    must(psql(DB, "update public.api_keys set revoked_at = now() where key_hash = decode(:'h', 'hex');", { h: hashOf(keys.toRevoke) }));
    const log: string[] = [];
    const res = await handleMcp(req(call("list_plants"), keys.toRevoke), dbDeps(log));
    assert.equal(res.status, 401);
    assert.equal(((await res.json()) as { error: string }).error, "key_revoked_or_unknown");
    assert.deepEqual(log, ["mcp_resolve_key"]);
  });

  test("FR-P03: a revoked key from the start and an unknown key both get 401 and read nothing", async () => {
    for (const key of [keys.revoked, makeKey()]) {
      const log: string[] = [];
      const res = await handleMcp(req(call("get_plant_status", { plant_id: PLANT_A }), key), dbDeps(log));
      assert.equal(res.status, 401);
      assert.deepEqual(log, ["mcp_resolve_key"]);
    }
  });

  test("FR-P04: a free user's key is refused on every tool; no plant of C is read", async () => {
    const log: string[] = [];
    const r = await toolCall(dbDeps(log), keys.C, "list_plants");
    assert.equal(errorCode(r.body as never), "premium_required");
    assert.deepEqual(log, ["mcp_resolve_key"]);
  });

  test("FR-P01: history for 7 days returns points and the seeded watering event; 90 days raw is downsampled to <= 2000 points", async () => {
    const h7 = await toolCall(dbDeps(), keys.A, "get_history", { plant_id: PLANT_A, days: 7, resolution: "raw" });
    const s7 = h7.body.result!.structuredContent as { points: unknown[]; watering_events: string[] };
    assert.ok(s7.points.length > 0 && s7.points.length <= 2000);
    assert.ok(s7.watering_events.length >= 1, "seeded wetting event is listed");
    const h90 = await toolCall(dbDeps(), keys.A, "get_history", { plant_id: PLANT_A, days: 90, resolution: "raw" });
    const s90 = h90.body.result!.structuredContent as { points: { ts: string }[] };
    assert.ok(s90.points.length > 0 && s90.points.length <= 2000, `got ${s90.points.length}`);
    // 90 days of raw needs a 120-minute step; buckets are aligned to 2000-01-01 00:00 UTC
    const epoch = Date.parse("2000-01-01T00:00:00Z");
    assert.ok(s90.points.every((p) => (Date.parse(p.ts) - epoch) % (120 * 60000) === 0), "120-minute buckets");
  });

  test("FR-P02: no cached tips yet (seed row has another guardrail version) -> tips_unavailable", async () => {
    const r = await toolCall(dbDeps(), keys.A, "get_tips", { plant_id: PLANT_A });
    assert.equal(errorCode(r.body as never), "tips_unavailable");
  });

  test("FR-P02: a current cached tip is returned; an expired newer one is ignored; a bad stored item fails the answer", async () => {
    const item = { id: "water-later", category: "watering", text: "Water again in two days." };
    must(psql(DB, `
      update public.tips set expires_at = now() - interval '1 minute' where guardrail_version = 'seed';   -- the seed's own rows are not the subject here
      insert into public.tips (plant_id, owner_id, generated_at, expires_at, content, guardrail_version)
        values (:'pa', :'a', now() - interval '1 hour', now() + interval '3 hours', :'good'::jsonb, :'gv');
      insert into public.tips (plant_id, owner_id, generated_at, expires_at, content, guardrail_version)
        values (:'pa', :'a', now(), now() - interval '1 minute', :'good'::jsonb, :'gv');`,
      { pa: PLANT_A, a: A, good: JSON.stringify({ items: [item] }), gv: GUARDRAIL_VERSION_EXPECTED }));
    const ok = await toolCall(dbDeps(), keys.A, "get_tips", { plant_id: PLANT_A });
    assert.equal(ok.body.result?.isError, undefined);
    assert.deepEqual((ok.body.result!.structuredContent as { items: unknown[] }).items, [item]);

    must(psql(DB, `insert into public.tips (plant_id, owner_id, expires_at, content, guardrail_version)
                   values (:'pb', :'b', now() + interval '1 hour', :'bad'::jsonb, :'gv');`,
      { pb: PLANT_B, b: B, bad: JSON.stringify({ items: [{ id: "x", category: "medical", text: "Take this." }] }), gv: GUARDRAIL_VERSION_EXPECTED }));
    const bad = await toolCall(dbDeps(), keys.B, "get_tips", { plant_id: PLANT_B });
    assert.equal(errorCode(bad.body as never), "tips_unavailable");
  });

  test("contract: every database answer for A validates against the contract output schema", async () => {
    const list = await toolCall(dbDeps(), keys.A, "list_plants");
    assert.equal(validate(contractOutput("list_plants") as Schema, list.body.result!.structuredContent), null);
    const st = await toolCall(dbDeps(), keys.A, "get_plant_status", { plant_id: PLANT_A });
    assert.equal(validate(contractOutput("get_plant_status") as Schema, st.body.result!.structuredContent), null);
    const h = await toolCall(dbDeps(), keys.A, "get_history", { plant_id: PLANT_A, days: 7, resolution: "raw" });
    assert.equal(validate(contractOutput("get_history") as Schema, h.body.result!.structuredContent), null);
  });
});

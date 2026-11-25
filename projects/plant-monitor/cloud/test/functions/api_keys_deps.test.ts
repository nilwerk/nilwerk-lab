// 4.B2d: the PostgREST adapter of /api-keys (buildApiKeysDeps, used by makeApiKeysDeps) against a FAKE client that records every call. No database,
// no network. NOT a real PostgREST check: the filters are asserted, not executed. Requirements: FR-P04 (is_premium as the user, before any write),
// NFR-06 (the user's JWT on user calls; the service client only for the two writes, each filtered by owner), FR-P03.
import { test } from "node:test";
import assert from "node:assert/strict";
import { buildApiKeysDeps, type KeysClient, type KeysQuery } from "../../supabase/functions/_shared/api_keys_deps.ts";
import { handleApiKeys } from "../../supabase/functions/_shared/api_keys.ts";

const U = "00000000-0000-0000-0000-0000000000b0", ID = "30000000-0000-0000-0000-000000000001";
interface Fake { log: string[]; asUser: (jwt: string) => KeysClient; admin: () => KeysClient }
function fake(opts: { premium?: unknown; rpcError?: boolean; rows?: unknown; writeError?: boolean } = {}): Fake {
  const log: string[] = [];
  const client = (who: string): KeysClient => ({
    auth: { getUser: async (j) => { log.push(`${who}.getUser(${j})`); return { data: { user: j === "jwt-ok" ? { id: U } : null }, error: j === "jwt-ok" ? null : { message: "bad" } }; } },
    rpc: (name) => { log.push(`${who}.rpc(${name})`); return Promise.resolve({ data: "premium" in opts ? opts.premium : true, error: opts.rpcError ? { message: "x" } : null }); },
    from: (table) => {
      const steps: string[] = [];
      const self: KeysQuery = {
        select: (c) => { steps.push(`select(${c})`); return self; },
        insert: (r) => { steps.push(`insert(${JSON.stringify(r)})`); return self; },
        update: (r) => { steps.push(`update(${Object.keys(r).join(",")})`); return self; },
        eq: (c, v) => { steps.push(`eq(${c},${String(v)})`); return self; },
        is: (c, v) => { steps.push(`is(${c},${String(v)})`); return self; },
        then: ((f: never, r: never) => {
          log.push(`${who}.from(${table}).${steps.join(".")}`);
          const insert = steps.some((s) => s.startsWith("insert"));
          const data = opts.rows !== undefined ? opts.rows : insert ? [{ id: ID }] : [];
          return Promise.resolve({ data, error: opts.writeError ? { message: "boom" } : null }).then(f, r);
        }) as KeysQuery["then"],
      };
      return self;
    },
  });
  return { log, asUser: (jwt) => client(`user[${jwt}]`), admin: () => client("service") };
}
const deps = (f: Fake) => buildApiKeysDeps(f.asUser, f.admin, (n) => new Uint8Array(n).fill(1));
const req = (m: string, p = "api-keys") => new Request(`http://x/functions/v1/${p}`, { method: m, headers: { authorization: "Bearer jwt-ok" }, body: m === "POST" ? JSON.stringify({ name: "n" }) : undefined });

test("FR-P04: is_premium is an RPC called as the user (their JWT) BEFORE the service client is touched; a free user never reaches the service client", async () => {
  const f = fake({ premium: false });
  const r = await handleApiKeys(req("POST"), deps(f));
  assert.equal(r.status, 403);
  assert.ok(f.log.includes("user[jwt-ok].rpc(is_premium)"));
  assert.ok(!f.log.some((l) => l.startsWith("service")), "no service-role call");
});

test("create: the service insert carries the verified owner id, a '\\x' hash, the prefix and name, and selects only the id", async () => {
  const f = fake();
  const r = await handleApiKeys(req("POST"), deps(f));
  assert.equal(r.status, 201);
  const ins = f.log.find((l) => l.startsWith("service.from(api_keys)"))!;
  assert.match(ins, /insert\(\{"owner_id":"0{8}-0{4}-0{4}-0{4}-0{10}b0","name":"n","prefix":"nwk_[A-Za-z0-9_-]{4}","key_hash":"\\\\x[0-9a-f]{64}"\}\)\.select\(id\)$/);
  const { key } = await r.json() as { key: string };
  assert.ok(!f.log.some((l) => l.includes(key)), "the key is never sent to the database");
  assert.ok(f.log.indexOf("user[jwt-ok].rpc(is_premium)") < f.log.indexOf(ins), "premium check before the write");
});

test("revoke: ownership is read as the user, the service update is filtered by id AND owner AND not-yet-revoked", async () => {
  const f = fake({ rows: [{ revoked_at: null }] });
  const r = await handleApiKeys(req("DELETE", `api-keys/${ID}`), deps(f));
  assert.equal(r.status, 204);
  assert.ok(f.log.includes(`user[jwt-ok].from(api_keys).select(id,revoked_at).eq(id,${ID})`));
  assert.ok(f.log.includes(`service.from(api_keys).update(revoked_at).eq(id,${ID}).eq(owner_id,${U}).is(revoked_at,null)`));
});

test("revoke: no row for the user (foreign or unknown) -> 404 and no service call; already revoked -> 204 and no service call", async () => {
  const none = fake({ rows: [] });
  assert.equal((await handleApiKeys(req("DELETE", `api-keys/${ID}`), deps(none))).status, 404);
  assert.ok(!none.log.some((l) => l.startsWith("service")));
  const done = fake({ rows: [{ revoked_at: "2026-11-20T00:00:00Z" }] });
  assert.equal((await handleApiKeys(req("DELETE", `api-keys/${ID}`), deps(done))).status, 204);
  assert.ok(!done.log.some((l) => l.startsWith("service")));
});

test("failures map to 500: rpc error, non-boolean premium, write error, read error", async () => {
  assert.equal((await handleApiKeys(req("POST"), deps(fake({ rpcError: true })))).status, 500);
  assert.equal((await handleApiKeys(req("POST"), deps(fake({ premium: "yes" })))).status, 500);
  assert.equal((await handleApiKeys(req("POST"), deps(fake({ writeError: true })))).status, 500);
  assert.equal((await handleApiKeys(req("POST"), deps(fake({ rows: [] })))).status, 500, "an insert that returns no id is a failure");
  assert.equal((await handleApiKeys(req("DELETE", `api-keys/${ID}`), deps(fake({ writeError: true })))).status, 500);
  assert.equal((await handleApiKeys(req("DELETE", `api-keys/${ID}`), deps(fake({ rows: { not: "array" } })))).status, 500);
});

test("401 for a bad JWT, no data call", async () => {
  const f = fake();
  const r = await handleApiKeys(new Request("http://x/api-keys", { method: "POST", headers: { authorization: "Bearer nope" }, body: "{}" }), deps(f));
  assert.equal(r.status, 401); assert.deepEqual(f.log, ["user[nope].getUser(nope)"]);
});

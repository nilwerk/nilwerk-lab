// 4.B2d: POST /api-keys and DELETE /api-keys/{id} tests. Unit (fake deps, no database) + integration (local PostgreSQL, NW_TEST_DB_URL, set by cloud/test.sh).
// Requirements: FR-P03 (create/revoke a personal key, revoked key fails at the MCP server), FR-P04 (premium checked before any write), NFR-06 (only the hash
// and prefix are stored, the key never leaves the response). Fixtures use the nwk_TESTONLY marker, never a real key.
import { test } from "node:test";
import assert from "node:assert/strict";
import { createHash, randomBytes } from "node:crypto";
import { Buffer } from "node:buffer";
import { handleApiKeys, NAME_MAX, type ApiKeysDeps } from "../../supabase/functions/_shared/api_keys.ts";
import { authenticate, KEY_PATTERN } from "../../supabase/functions/_shared/mcp.ts";
import { psql, psqlDeps } from "./psql_deps.ts";

const P = "00000000-0000-0000-0000-0000000000b0", E = "00000000-0000-0000-0000-0000000000b1", F = "00000000-0000-0000-0000-0000000000b2";
const JWT: Record<string, string> = { "jwt-p": P, "jwt-e": E, "jwt-f": F };
const ID1 = "30000000-0000-0000-0000-000000000001";

const post = (body: unknown, auth?: string, method = "POST") =>
  new Request("http://x/functions/v1/api-keys", { method, headers: auth ? { authorization: `Bearer ${auth}` } : {}, body: method === "POST" ? (typeof body === "string" ? body : JSON.stringify(body)) : undefined });
const del = (id: string, auth?: string, method = "DELETE") =>
  new Request(`http://x/functions/v1/api-keys/${id}`, { method, headers: auth ? { authorization: `Bearer ${auth}` } : {} });

/** Fake deps that record every call, so a test can prove nothing was written. */
const spyDeps = (over: Partial<ApiKeysDeps> = {}) => {
  const calls: string[] = [];
  const stored: { ownerId: string; name: string; prefix: string; keyHashHex: string }[] = [];
  const deps: ApiKeysDeps = {
    getUserId: async (j) => { calls.push("getUserId"); return JWT[j] ?? null; },
    isPremium: async () => { calls.push("isPremium"); return true; },
    randomBytes: (n) => new Uint8Array(randomBytes(n)),
    insertKey: async (ownerId, row) => { calls.push("insertKey"); stored.push({ ownerId, ...row }); return { id: ID1 }; },
    findOwnKey: async () => { calls.push("findOwnKey"); return { found: true, revoked: false }; },
    revokeKey: async () => { calls.push("revokeKey"); return true; },
    ...over,
  };
  return { deps, calls, stored };
};
const errOf = async (r: Response) => (await r.json() as { error: string }).error;

// ---------------------------------------------------------------- unit tests (no database)
test("405: wrong method on either route, nothing is read or written", async () => {
  const { deps, calls } = spyDeps();
  for (const m of ["GET", "PUT", "DELETE", "PATCH"]) assert.equal((await handleApiKeys(post({}, "jwt-p", m), deps)).status, 405, `collection ${m}`);
  for (const m of ["GET", "POST", "PUT", "PATCH"]) assert.equal((await handleApiKeys(del(ID1, "jwt-p", m), deps)).status, 405, `item ${m}`);
  assert.deepEqual(calls, []);
});

test("404: a path that is not /api-keys or /api-keys/{id}", async () => {
  const { deps, calls } = spyDeps();
  for (const u of ["http://x/other", "http://x/functions/v1/api-keys/a/b"]) assert.equal((await handleApiKeys(new Request(u, { method: "POST", headers: { authorization: "Bearer jwt-p" } }), deps)).status, 404, u);
  assert.deepEqual(calls, []);
});

test("NFR-06: missing or forged token -> 401 before any data access, on both routes", async () => {
  const { deps, calls } = spyDeps();
  const none = await handleApiKeys(post({ name: "n" }), deps);
  assert.equal(none.status, 401); assert.equal(await errOf(none), "unauthorized");
  assert.equal((await handleApiKeys(post({ name: "n" }, "forged"), deps)).status, 401);
  assert.equal((await handleApiKeys(del(ID1), deps)).status, 401);
  assert.equal((await handleApiKeys(del(ID1, "forged"), deps)).status, 401);
  assert.deepEqual(calls, ["getUserId", "getUserId"]);
});

test("FR-P04: a free user gets 403 premium_required and NOTHING is written (premium is checked before the body and before any write)", async () => {
  const { deps, calls, stored } = spyDeps({ isPremium: async () => { return false; } });
  for (const body of [{ name: "My AI" }, {}, "not json"]) {   // even a bad body: the free user learns nothing but 403
    const r = await handleApiKeys(post(body, "jwt-e"), deps);
    assert.equal(r.status, 403); assert.equal(await errOf(r), "premium_required");
  }
  assert.ok(!calls.includes("insertKey") && !calls.includes("revokeKey")); assert.equal(stored.length, 0);
});

test("500 without detail: a failed premium check, insert, ownership read or revoke", async () => {
  const leak = "relation api_keys secret failure";
  const cases: [() => Request, Partial<ApiKeysDeps>][] = [
    [() => post({ name: "n" }, "jwt-p"), { isPremium: async () => null }],
    [() => post({ name: "n" }, "jwt-p"), { insertKey: async () => null }],
    [() => del(ID1, "jwt-p"), { findOwnKey: async () => null }],
    [() => del(ID1, "jwt-p"), { revokeKey: async () => false }],
  ];
  for (const [mk, over] of cases) {
    const r = await handleApiKeys(mk(), spyDeps(over).deps);
    const text = await r.text();
    assert.equal(r.status, 500); assert.deepEqual(JSON.parse(text), { error: "internal" }); assert.ok(!text.includes(leak));
  }
});

test("400: name is required, a string of 1..60 characters; a premium user's bad body writes nothing", async () => {
  const { deps, calls, stored } = spyDeps();
  const bad: unknown[] = [{}, { name: "" }, { name: "   " }, { name: 5 }, { name: null }, { name: "x".repeat(NAME_MAX + 1) }, [], "null", "not json", "{", { name: "x", pad: "y".repeat(3000) }];
  for (const b of bad) { const r = await handleApiKeys(post(b, "jwt-p"), deps); assert.equal(r.status, 400, JSON.stringify(b).slice(0, 40)); assert.equal(await errOf(r), "bad_request"); }
  assert.ok(!calls.includes("insertKey")); assert.equal(stored.length, 0);
  assert.equal((await handleApiKeys(post({ name: "x".repeat(NAME_MAX) }, "jwt-p"), deps)).status, 201, "exactly 60 is allowed");
});

test("400: a malformed id on DELETE, after 401 and before any database access", async () => {
  const { deps, calls } = spyDeps();
  for (const id of ["1", "not-a-uuid", "30000000-0000-0000-0000-00000000000g", "30000000-0000-0000-0000-0000000000011", "%20"]) {
    const r = await handleApiKeys(del(id, "jwt-p"), deps); assert.equal(r.status, 400, id); assert.equal(await errOf(r), "bad_request");
  }
  assert.ok(!calls.includes("findOwnKey") && !calls.includes("revokeKey"));
});

test("FR-P03/NFR-06: 201 returns the key once; only its sha256 and 8-char prefix reach the store; the key is not in the store call, headers or logs", async () => {
  const logs: string[] = [];
  const orig = { log: console.log, error: console.error, warn: console.warn, info: console.info };
  console.log = console.error = console.warn = console.info = (...a: unknown[]) => { logs.push(a.join(" ")); };
  const { deps, stored } = spyDeps({ randomBytes: () => new Uint8Array(32).fill(7) });
  let r: Response;
  try { r = await handleApiKeys(post({ name: "  Claude  " }, "jwt-p"), deps); } finally { Object.assign(console, orig); }
  assert.equal(r.status, 201); assert.equal(r.headers.get("cache-control"), "no-store");
  const body = await r.json() as { id: string; key: string; prefix: string };
  assert.deepEqual(Object.keys(body).sort(), ["id", "key", "prefix"]);
  assert.equal(body.id, ID1);
  assert.match(body.key, KEY_PATTERN, "nwk_ + 43 base64url characters");
  assert.equal(body.key, "nwk_" + Buffer.alloc(32, 7).toString("base64url"));
  assert.equal(body.prefix, body.key.slice(0, 8)); assert.equal(body.prefix.length, 8);
  assert.equal(stored.length, 1);
  assert.deepEqual(stored[0], { ownerId: P, name: "Claude", prefix: body.prefix, keyHashHex: createHash("sha256").update(body.key).digest("hex") });
  assert.ok(!JSON.stringify(stored).includes(body.key), "the key itself is never handed to storage");
  assert.deepEqual(logs, [], "nothing is logged");
});

test("FR-P03: two creations give two different keys", async () => {
  const { deps } = spyDeps();
  const a = await (await handleApiKeys(post({ name: "a" }, "jwt-p"), deps)).json() as { key: string };
  const b = await (await handleApiKeys(post({ name: "b" }, "jwt-p"), deps)).json() as { key: string };
  assert.notEqual(a.key, b.key);
});

test("DELETE: own key -> 204 and revoked once; unknown or foreign -> 404 and no write; already revoked -> 204 and no second write", async () => {
  const own = spyDeps();
  const r = await handleApiKeys(del(ID1, "jwt-p"), own.deps);
  assert.equal(r.status, 204); assert.equal(await r.text(), "");
  assert.deepEqual(own.calls, ["getUserId", "findOwnKey", "revokeKey"]);
  const none = spyDeps({ findOwnKey: async () => ({ found: false }) });
  const n = await handleApiKeys(del(ID1, "jwt-p"), none.deps);
  assert.equal(n.status, 404); assert.equal(await errOf(n), "not_found"); assert.ok(!none.calls.includes("revokeKey"));
  const again = spyDeps({ findOwnKey: async () => ({ found: true, revoked: true }) });
  assert.equal((await handleApiKeys(del(ID1, "jwt-p"), again.deps)).status, 204); assert.ok(!again.calls.includes("revokeKey"));
});

test("DELETE needs no premium check: a lapsed user can still revoke", async () => {
  const { deps, calls } = spyDeps({ isPremium: async () => false });
  assert.equal((await handleApiKeys(del(ID1, "jwt-e"), deps)).status, 204);
  assert.ok(!calls.includes("isPremium"));
});

// ---------------------------------------------------------------- integration tests (local PostgreSQL; user calls under RLS, writes as service_role)
const url = process.env.NW_TEST_DB_URL;
const db = url ? { skip: false } : { skip: "NW_TEST_DB_URL not set (run via cloud/test.sh)" };
const q = (sql: string, vars?: Record<string, string>) => { const r = psql(url!, sql, vars); assert.ok(r.ok, r.err); return r.out; };
const asUser = (uid: string, sql: string, vars: Record<string, string> = {}) => q(`set role authenticated; set request.uid = :'uid'; ${sql}`, { ...vars, uid });
const asService = (sql: string, vars: Record<string, string> = {}) => psql(url!, `set role service_role; ${sql}`, vars);

/** Deps shaped like production: premium and ownership reads as the user (authenticated role, RLS), the two writes as service_role. */
function dbDeps(calls: string[] = []): ApiKeysDeps {
  return {
    async getUserId(jwt) { calls.push("getUserId"); return JWT[jwt] ?? null; },
    async isPremium(jwt) {
      calls.push("isPremium");
      const r = psql(url!, `set role authenticated; set request.uid = :'uid'; select public.is_premium();`, { uid: JWT[jwt] ?? "" });
      return r.ok ? r.out === "t" : null;
    },
    randomBytes: (n) => new Uint8Array(randomBytes(n)),
    async insertKey(ownerId, row) {
      calls.push("insertKey");
      const r = asService(`insert into public.api_keys(owner_id,name,prefix,key_hash) values (:'o',:'n',:'p',decode(:'h','hex')) returning id;`, { o: ownerId, n: row.name, p: row.prefix, h: row.keyHashHex });
      return r.ok ? { id: r.out.split("\n")[0] } : null;
    },
    async findOwnKey(jwt, id) {
      calls.push("findOwnKey");
      const r = psql(url!, `set role authenticated; set request.uid = :'uid'; select revoked_at is not null from public.api_keys where id = :'id';`, { uid: JWT[jwt] ?? "", id });
      if (!r.ok) return null;
      const last = r.out.split("\n").pop() ?? "";
      return last === "" || last === "SET" ? { found: false } : { found: true, revoked: last === "t" };
    },
    async revokeKey(ownerId, id) {
      calls.push("revokeKey");
      return asService(`update public.api_keys set revoked_at = now() where id = :'id' and owner_id = :'o' and revoked_at is null;`, { id, o: ownerId }).ok;
    },
  };
}
const rowCount = (owner: string) => asService(`select count(*) from public.api_keys where owner_id = :'o'`, { o: owner }).out.split("\n").pop();
const hashOf = (k: string) => createHash("sha256").update(k).digest("hex");

test("setup: P and F premium, E free", db, () => {
  for (const [u, tag] of [[P, "p"], [E, "e"], [F, "f"]] as const) q(`insert into auth.users(id,email) values (:'u', :'e')`, { u, e: `k${tag}@example.test` });
  q(`update public.profiles set is_premium = true where id in (:'p', :'f')`, { p: P, f: F });
  assert.equal(q(`select is_premium from public.profiles where id = :'e'`, { e: E }), "f");
});

test("FR-P04 (integration, real is_premium()): a free user gets 403 and NO row is written", db, async () => {
  const calls: string[] = [];
  const r = await handleApiKeys(post({ name: "free try" }, "jwt-e"), dbDeps(calls));
  assert.equal(r.status, 403); assert.equal(await errOf(r), "premium_required");
  assert.ok(!calls.includes("insertKey")); assert.equal(rowCount(E), "0"); assert.equal(q(`select count(*) from public.api_keys where name = 'free try'`), "0");
});

let keyP1 = "", idP1 = "";
test("FR-P03/NFR-06: premium create -> 201, the DB row has the hash and the 8-char prefix, never the key", db, async () => {
  const r = await handleApiKeys(post({ name: "Claude Desktop" }, "jwt-p"), dbDeps());
  assert.equal(r.status, 201);
  const b = await r.json() as { id: string; key: string; prefix: string };
  keyP1 = b.key; idP1 = b.id;
  assert.match(b.key, KEY_PATTERN);
  const row = q(`select owner_id, name, prefix, encode(key_hash,'hex'), revoked_at is null from public.api_keys where id = :'id'`, { id: b.id });
  assert.equal(row, [P, "Claude Desktop", b.prefix, hashOf(b.key), "t"].join("|"));
  assert.equal(b.prefix, b.key.slice(0, 8), "prefix = first 8 characters of the key");
  assert.equal(q(`select count(*) from public.api_keys where convert_from(key_hash, 'UTF8') = :'k' or prefix = :'k' or name = :'k'`.replace(/convert_from\(key_hash, 'UTF8'\)/, "encode(key_hash,'escape')"), { k: b.key }), "0", "the key is nowhere in the row");
  assert.equal(rowCount(P), "1");
});

test("FR-P03: a key created by the function authenticates against the MCP server's check (mcp_resolve_key); once revoked it fails", db, async () => {
  const mcp = psqlDeps(url!, {});
  const resolve = (key: string) => authenticate(new Request("http://x/mcp", { method: "POST", headers: { authorization: `Bearer ${key}` } }), {
    rpc: (name, args) => {
      assert.equal(name, "mcp_resolve_key");
      const r = psql(url!, "select public.mcp_resolve_key(:'h')::text;", { h: String(args.p_key_hash) });
      return Promise.resolve(r.ok ? { data: r.out === "" ? null : r.out, error: null } : { data: null, error: { message: r.err } });
    },
  });
  void mcp;
  const before = await resolve(keyP1);
  assert.deepEqual(before, { ok: true, owner: P }, "the created key verifies and resolves to its owner");
  assert.equal(q(`select last_used_at is not null from public.api_keys where id = :'id'`, { id: idP1 }), "t");
  const del1 = await handleApiKeys(del(idP1, "jwt-p"), dbDeps());
  assert.equal(del1.status, 204);
  const after = await resolve(keyP1);
  assert.equal(after.ok, false, "the revoked key fails the MCP check");
  if (!after.ok) assert.equal(after.response.status, 401);
});

/** The MCP server's key check (mcp.ts authenticate) against the real mcp_resolve_key function. */
const mcpAccepts = (key: string) => authenticate(new Request("http://x/mcp", { method: "POST", headers: { authorization: `Bearer ${key}` } }), {
  rpc: (name, args) => {
    assert.equal(name, "mcp_resolve_key");
    const r = psql(url!, "select public.mcp_resolve_key(:'h')::text;", { h: String(args.p_key_hash) });
    return Promise.resolve(r.ok ? { data: r.out === "" ? null : r.out, error: null } : { data: null, error: { message: r.err } });
  },
});

test("revoke twice: both 204, and the first revoked_at is kept", db, async () => {
  const first = q(`select revoked_at::text from public.api_keys where id = :'id'`, { id: idP1 });
  assert.notEqual(first, "");
  const calls: string[] = [];
  assert.equal((await handleApiKeys(del(idP1, "jwt-p"), dbDeps(calls))).status, 204);
  assert.ok(!calls.includes("revokeKey"), "no second write");
  assert.equal(q(`select revoked_at::text from public.api_keys where id = :'id'`, { id: idP1 }), first);
});

test("NFR-06: revoking another user's key -> 404, the key stays valid; an unknown id -> the same 404", db, async () => {
  const c = await handleApiKeys(post({ name: "F key" }, "jwt-f"), dbDeps());
  const fk = await c.json() as { id: string; key: string };
  const calls: string[] = [];
  const r = await handleApiKeys(del(fk.id, "jwt-p"), dbDeps(calls));
  assert.equal(r.status, 404); assert.equal(await errOf(r), "not_found"); assert.ok(!calls.includes("revokeKey"));
  assert.equal(q(`select revoked_at is null from public.api_keys where id = :'id'`, { id: fk.id }), "t", "F's key is untouched");
  const unknown = await handleApiKeys(del("30000000-0000-0000-0000-0000000000ff", "jwt-p"), dbDeps());
  assert.equal(unknown.status, 404);
  assert.equal(q(`select count(*) from public.api_keys where owner_id = :'p' and revoked_at is null`, { p: P }), "0");
});

test("the service-role revoke is filtered by owner as well: even a wrong id/owner pair changes no row", db, () => {
  const fkId = q(`select id from public.api_keys where owner_id = :'f' limit 1`, { f: F });
  assert.ok(asService(`update public.api_keys set revoked_at = now() where id = :'id' and owner_id = :'o' and revoked_at is null;`, { id: fkId, o: P }).ok);
  assert.equal(q(`select revoked_at is null from public.api_keys where id = :'id'`, { id: fkId }), "t");
});

test("FR-P03: the list is a select under RLS: each user sees only their own keys, never the hash; authenticated cannot insert or update", db, async () => {
  await handleApiKeys(post({ name: "P second" }, "jwt-p"), dbDeps());
  assert.equal(asUser(P, `select string_agg(name, ',' order by name) from public.api_keys;`).split("\n").pop(), "Claude Desktop,P second");
  assert.equal(asUser(F, `select string_agg(name, ',') from public.api_keys;`).split("\n").pop(), "F key");
  assert.equal(asUser(E, `select count(*) from public.api_keys;`).split("\n").pop(), "0");
  const hash = psql(url!, `set role authenticated; set request.uid = '${P}'; select key_hash from public.api_keys;`);
  assert.ok(!hash.ok, "key_hash is not selectable by the owner");
  assert.ok(!psql(url!, `set role authenticated; set request.uid = '${P}'; insert into public.api_keys(owner_id,name,prefix,key_hash) values ('${P}','x','nwk_xxxx','\\x00');`).ok, "no insert as the user: the function (service role) is the only writer");
  assert.ok(!psql(url!, `set role authenticated; set request.uid = '${P}'; update public.api_keys set revoked_at = null;`).ok);
});

test("500 on a database failure (no database text in the body)", db, async () => {
  const broken: ApiKeysDeps = { ...dbDeps(), insertKey: async () => { const r = psql(url!, `insert into public.no_such_table values (1)`); return r.ok ? { id: ID1 } : null; } };
  const r = await handleApiKeys(post({ name: "n" }, "jwt-p"), broken);
  const text = await r.text();
  assert.equal(r.status, 500); assert.deepEqual(JSON.parse(text), { error: "internal" }); assert.ok(!text.includes("no_such_table"));
});

// Last on purpose: it creates a key for P, and the list test above asserts P's exact key names.
test("FR-P03 (F-06): DELETE /api-keys/{id} revokes the key in the database; the first and the second use after it are refused with 401", db, async () => {
  const made = await handleApiKeys(post({ name: "Revoke me" }, "jwt-p"), dbDeps());
  assert.equal(made.status, 201);
  const { id, key } = await made.json() as { id: string; key: string };
  assert.equal((await mcpAccepts(key)).ok, true, "before the DELETE the key is accepted (the test is not vacuous)");
  const r = await handleApiKeys(del(id, "jwt-p"), dbDeps());
  assert.equal(r.status, 204);
  assert.equal(q(`select revoked_at is not null from public.api_keys where id = :'id'`, { id }), "t", "the row is revoked, not only the response");
  for (const use of ["first", "second"]) {
    const after = await mcpAccepts(key);
    assert.equal(after.ok, false, `${use} use after the revoke must be refused`);
    if (!after.ok) assert.equal(after.response.status, 401, `${use} use after the revoke`);
  }
});

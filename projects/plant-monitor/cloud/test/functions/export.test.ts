// 4.B2c GET /export tests: unit (no database) + integration against a local PostgreSQL (NW_TEST_DB_URL, own database, set by cloud/test.sh).
// Requirements: NFR-07 (export before delete), FR-A01 (account data), NFR-06 (only the caller's rows), FR-A06 (export is not limited to the 7-day free window).
import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { crc32 as zlibCrc32 } from "node:zlib";
import { handleExport, CSV_COLUMNS, PHOTO_URL_TTL_SECONDS, csvCell, toCsv, zipStore, crc32 } from "../../supabase/functions/_shared/export.ts";
import type { Deps } from "../../supabase/functions/_shared/lib.ts";
import { psql, psqlDeps, signCtl, signed } from "./psql_deps.ts";

const E = "00000000-0000-0000-0000-0000000000e0", F = "00000000-0000-0000-0000-0000000000f0", G = "00000000-0000-0000-0000-000000000090";
const DAY = 86400000;

// ---------------------------------------------------------------- unit tests (no database)
const spy = (over: Partial<Deps> = {}) => {
  const calls: string[] = [];
  const deps: Deps = {
    rpc: async (n) => { calls.push(`rpc:${n}`); return { data: null, error: { message: "SELECT secret_table failed" } }; },
    getUserId: async (j) => { calls.push("getUserId"); return j === "good" ? E : null; },
    randomBytes: (n) => new Uint8Array(n), deleteUserPhotos: async () => null, deleteAuthUser: async () => null,
    signPhotoUrls: async () => { calls.push("sign"); return { urls: {} }; }, ...over,
  };
  return { deps, calls };
};
const get = (deps: Deps, qs = "?format=json", auth?: string, method = "GET") =>
  handleExport(new Request(`http://x/export${qs}`, { method, headers: auth ? { authorization: `Bearer ${auth}` } : {} }), deps);

test("NFR-07, NFR-06: wrong method -> 405, missing/invalid token -> 401; nothing is read or signed before the token is verified", async () => {
  const { deps, calls } = spy();
  for (const m of ["POST", "PUT", "DELETE", "PATCH"]) assert.equal((await get(deps, "?format=json", "good", m)).status, 405, m);
  assert.equal(calls.length, 0, "405 before anything else");
  const none = await get(deps); assert.equal(none.status, 401); assert.equal((await none.json() as any).error, "unauthorized");
  assert.equal((await get(deps, "?format=json", "forged")).status, 401);
  assert.equal((await get(deps, "", "forged")).status, 401, "401 wins over a missing format (an unauthenticated caller learns nothing)");
  assert.ok(!calls.includes("rpc:export_account") && !calls.includes("sign"), "no data access without a verified user");
});

test("NFR-07: format must be json or csv (missing, other case, list, empty -> 400); no data access for a bad format", async () => {
  const { deps, calls } = spy();
  for (const qs of ["", "?format=", "?format=JSON", "?format=xml", "?format=json,csv", "?formats=json"]) {
    const r = await get(deps, qs, "good"); assert.equal(r.status, 400, qs); assert.equal((await r.json() as any).error, "bad_request");
  }
  assert.ok(!calls.includes("rpc:export_account"));
});

test("NFR-07: a database failure or a malformed database answer -> 500 'internal' without leaking the database message; the user is the verified one", async () => {
  let seen: Record<string, unknown> = {};
  for (const data of [null, "x", { plants: [] }, { photo_rows: [] }]) {
    const { deps } = spy({ rpc: async (_n, a) => { seen = a; return { data, error: data === null ? { message: "SELECT secret_table failed" } : null }; } });
    const r = await get(deps, "?format=json", "good"); assert.equal(r.status, 500);
    const t = await r.text(); assert.ok(!t.includes("secret_table")); assert.deepEqual(JSON.parse(t), { error: "internal" });
  }
  assert.deepEqual(seen, { p_user: E });
});

test("csvCell: RFC 4180 quoting and formula-injection guard for strings only (numbers keep their sign)", () => {
  assert.equal(csvCell(null), ""); assert.equal(csvCell(undefined), ""); assert.equal(csvCell(true), "true"); assert.equal(csvCell(-3.5), "-3.5"); assert.equal(csvCell(0), "0");
  assert.equal(csvCell("a,b"), '"a,b"'); assert.equal(csvCell('say "hi"'), '"say ""hi"""'); assert.equal(csvCell("l1\nl2"), '"l1\nl2"'); assert.equal(csvCell("ä€"), "ä€");
  for (const f of ["=1+1", "+1", "-1", "@SUM(A1)", "\tx", "\rx"]) assert.ok(csvCell(f).replace(/^"/, "").startsWith("'"), JSON.stringify(f));
  assert.equal(csvCell({ a: 1 }), '"{""a"":1}"');
  assert.equal(toCsv(["a", "b"], []), "a,b\r\n", "empty table: header row only");
});

test("zipStore + crc32: crc32 known vector; empty file list is a valid (22-byte) zip", () => {
  assert.equal(crc32(new TextEncoder().encode("123456789")), 0xcbf43926);
  assert.equal(zipStore([], new Date(0)).length, 22);
});

test("zipStore: local header and central directory agree with each other and with node:zlib's crc32 (streaming readers use the local header)", () => {
  const files = [{ name: "a.csv", data: new TextEncoder().encode("x,y\r\n1,2\r\n") }, { name: "bä.csv", data: new TextEncoder().encode("é".repeat(1000)) }];
  const z = zipStore(files, new Date("2026-11-17T10:00:00Z")); const v = new DataView(z.buffer);
  const eocd = z.length - 22; assert.equal(v.getUint32(eocd, true), 0x06054b50); assert.equal(v.getUint16(eocd + 10, true), 2);
  let c = v.getUint32(eocd + 16, true), l = 0;
  for (const f of files) {
    assert.equal(v.getUint32(l, true), 0x04034b50); assert.equal(v.getUint32(c, true), 0x02014b50);
    const want = zlibCrc32(f.data);
    assert.equal(v.getUint32(l + 14, true), want, `${f.name}: local header crc`); assert.equal(v.getUint32(c + 16, true), want, `${f.name}: central directory crc`);
    assert.equal(v.getUint32(l + 18, true), f.data.length); assert.equal(v.getUint32(l + 22, true), f.data.length);
    assert.equal(v.getUint32(c + 42, true), l, "central directory points at the local header");
    const n = v.getUint16(l + 26, true); assert.equal(new TextDecoder().decode(z.subarray(l + 30, l + 30 + n)), f.name);
    assert.deepEqual(z.subarray(l + 30 + n, l + 30 + n + f.data.length), f.data);
    l += 30 + n + f.data.length; c += 46 + n;
  }
});

// ---------------------------------------------------------------- integration tests (local PostgreSQL)
const url = process.env.NW_TEST_DB_URL;
const db = url ? { skip: false } : { skip: "NW_TEST_DB_URL not set (run via cloud/test.sh)" };
const deps = url ? psqlDeps(url, { "jwt-e": E, "jwt-f": F, "jwt-g": G }) : (undefined as unknown as Deps);
const q = (sql: string, vars?: Record<string, string>) => { const r = psql(url!, sql, vars); assert.ok(r.ok, r.err); return r.out; };
const exp = (auth: string | undefined, format = "json", qs = "") => get(deps, `?format=${format}${qs}`, auth);

const PE = "10000000-0000-0000-0000-0000000000e1", PF = "10000000-0000-0000-0000-0000000000f1", DE = "20000000-0000-0000-0000-0000000000e1", DF = "20000000-0000-0000-0000-0000000000f1";
const PHOTO_E1 = `${E}/${PE}/11111111-1111-1111-1111-111111111111.jpg`, PHOTO_E2 = `${E}/${PE}/22222222-2222-2222-2222-222222222222.jpg`, PHOTO_F = `${F}/${PF}/33333333-3333-3333-3333-333333333333.jpg`;
const NASTY = '=HYPERLINK("http://evil.test","x"), "Ficus"\nline2';

function seed() {
  for (const [u, tag] of [[E, "e"], [F, "f"], [G, "9"]]) q(`insert into auth.users(id,email) values (:'u', :'e')`, { u, e: `${tag}@example.test` });
  q(`update public.profiles set display_name = 'Eve', is_premium = false where id = :'u'`, { u: E });   // FREE user: RLS shows only 7 days of readings
  for (const [u, p, d, tag, name] of [[E, PE, DE, "e", NASTY], [F, PF, DF, "f", "Fern of F"]]) {
    q(`insert into public.plants(id,owner_id,name,location_type,soil_type,city) values (:'p', :'u', :'n', 'house', 'potting', 'Köln');
       insert into public.devices(id,hw_id,owner_id,plant_id,claimed_at) values (:'d', 'nw-0000000000${tag}1', :'u', :'p', now());
       insert into public.device_credentials(device_id,token_hash) values (:'d', decode(repeat('${tag}${tag}', 32), 'hex'));
       -- 0, 3, 30, 100 days old: raw readings 0/3/30 and one very old (the roll-up keeps 12 months)
       insert into public.readings(device_id,ts,owner_id,plant_id,moisture_pct,temp_c) select :'d', now() - g * interval '1 day', :'u', :'p', 40, -3.5 from unnest(array[0,3,30,100]) g;
       insert into public.readings_hourly(device_id,hour,owner_id,plant_id,n,moisture_avg) select :'d', date_trunc('hour', now() - g * interval '1 day'), :'u', :'p', 4, 41 from unnest(array[0,200]) g;
       insert into public.events(device_id,owner_id,plant_id,ts,type,critical) values (:'d', :'u', :'p', now() - interval '40 days', 'wetting', false);
       insert into public.alerts(owner_id,device_id,plant_id,kind,detail) values (:'u', :'d', :'p', 'too_dry', '{"event_ts":1}');
       insert into public.tips(plant_id,owner_id,expires_at,content,guardrail_version) values (:'p', :'u', now() - interval '60 days', '{"items":[{"id":"t1"}]}', 'g1.1');
       insert into public.api_keys(owner_id,name,prefix,key_hash) values (:'u', 'k', 'nwk_x', decode(repeat('${tag}${tag}', 32), 'hex'));
       insert into public.push_tokens(owner_id,expo_token) values (:'u', 'ExponentPushToken[${tag}]');`, { u, p, d, n: name });
  }
  q(`insert into public.plant_images(plant_id,owner_id,storage_path,taken_at) values (:'p', :'u', :'a', '2026-01-02T03:04:05Z'), (:'p', :'u', :'b', '2026-02-02T03:04:05Z');
     insert into public.plant_images(plant_id,owner_id,storage_path) values (:'pf', :'f', :'c')`, { p: PE, u: E, a: PHOTO_E1, b: PHOTO_E2, pf: PF, f: F, c: PHOTO_F });
}
const TABLES = ["plants", "devices", "readings", "readings_hourly", "events", "alerts", "tips"];

test("setup: two users with data in every table, E is a free user (RLS hides E's readings older than 7 days)", db, () => {
  seed();
  assert.equal(q(`set role authenticated; set request.uid = '${E}'; select count(*) from public.readings`), "2", "the RLS view of a free user: only 0 and 3 days");
  assert.equal(q(`select count(*) from public.readings where owner_id = :'u'`, { u: E }), "4");
});

test("NFR-07, FR-A01, FR-A06: JSON export has the top-level plants array, ALL of E's retained data (older than the 7-day RLS window too) and nothing of F", db, async () => {
  signed.length = 0;
  const r = await exp("jwt-e");
  assert.equal(r.status, 200);
  assert.match(r.headers.get("content-type")!, /^application\/json/);
  assert.equal(r.headers.get("cache-control"), "no-store");
  assert.match(r.headers.get("content-disposition")!, /^attachment; filename="nilwerk-export-\d{4}-\d\d-\d\d\.json"$/);
  const raw = await r.text(); const doc = JSON.parse(raw);
  assert.ok(Array.isArray(doc.plants), "the app client rejects anything without a plants array");
  assert.deepEqual(Object.keys(doc), ["exported_at", "profile", ...TABLES, "photos"]);
  assert.match(doc.exported_at, /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$/);
  assert.equal(doc.profile.id, E); assert.equal(doc.profile.display_name, "Eve");
  assert.deepEqual(Object.fromEntries(TABLES.map((t) => [t, doc[t].length])), { plants: 1, devices: 1, readings: 4, readings_hourly: 2, events: 1, alerts: 1, tips: 1 });
  assert.equal(doc.plants[0].name, NASTY, "JSON carries values verbatim (no CSV guard applied)");
  assert.equal(doc.readings.at(-1).temp_c, -3.5);
  assert.ok(doc.readings.every((x: any) => x.owner_id === E) && doc.plants.every((x: any) => x.owner_id === E));
  assert.equal(doc.tips[0].content.items[0].id, "t1", "expired and free-user tips are still exported (premium RLS does not apply to the owner's own data)");
  // isolation (NFR-06): no id, name or path of user F anywhere, a query parameter cannot name another user
  for (const needle of [F, PF, DF, "Fern of F", PHOTO_F, "ExponentPushToken", "token_hash", "key_hash", "nwk_x"]) assert.ok(!raw.includes(needle), `export must not contain ${needle}`);
  const other = JSON.parse(await (await exp("jwt-e", "json", `&user_id=${F}&owner_id=${F}`)).text());
  assert.equal(other.profile.id, E, "an extra parameter is ignored: the user is the token's user");
  // ISO-8601 UTC timestamps
  for (const t of [doc.readings[0].ts, doc.plants[0].created_at, doc.events[0].ts, doc.profile.created_at]) assert.match(t, /^\d{4}-\d\d-\d\dT[\d:.]+(Z|\+00:00)$/, t);
});

test("NFR-07, A-107(b): photos are 7-day signed URLs with an absolute expires_at, only E's paths are signed, once", db, async () => {
  signed.length = 0;
  const r = await exp("jwt-e"); const doc = await r.json() as any;
  assert.equal(PHOTO_URL_TTL_SECONDS, 604800);
  assert.equal(signed.length, 1, "one signing call");
  assert.equal(signed[0].ttl, 604800, "7 days");
  assert.deepEqual([...signed[0].paths].sort(), [PHOTO_E1, PHOTO_E2].sort());
  assert.equal(doc.photos.length, 2);
  for (const p of doc.photos) {
    assert.deepEqual(Object.keys(p), ["id", "plant_id", "taken_at", "url", "expires_at", "file"]);
    assert.equal(p.plant_id, PE); assert.match(p.url, /^https:\/\/storage\.test\/sign\/plant-photos\/.*ttl=604800$/);
    assert.equal(Date.parse(p.expires_at) - Date.parse(doc.exported_at), 7 * DAY, "expires_at = exported_at + 7 days");
    assert.match(p.file, /^[0-9a-f-]{36}\/[0-9a-f-]{36}\.jpg$/, "plant_id/uuid.jpg so the app can store the file without parsing the URL");
  }
  assert.deepEqual(doc.photos.map((p: any) => p.taken_at), ["2026-01-02T03:04:05+00:00", "2026-02-02T03:04:05+00:00"], "ordered by taken_at");
});

test("NFR-07: a photo whose Storage object is missing gets url null (export still works); a failing signing call fails the WHOLE export with 500", db, async () => {
  signCtl.missing = new Set([PHOTO_E2]);
  const ok = await (await exp("jwt-e")).json() as any;
  assert.equal(ok.photos.find((p: any) => p.file.startsWith(`${PE}/2222`)).url, null);
  assert.equal(ok.photos.find((p: any) => p.file.startsWith(`${PE}/2222`)).expires_at, null);
  assert.ok(ok.photos.find((p: any) => p.file.startsWith(`${PE}/1111`)).url);
  signCtl.missing = new Set(); signCtl.fail = true;
  const bad = await exp("jwt-e"); assert.equal(bad.status, 500); assert.deepEqual(await bad.json(), { error: "internal" });
  assert.equal((await exp("jwt-e", "csv")).status, 500);
  signCtl.fail = false;
});

test("NFR-06: a photo row whose path is not under the caller's folder is never signed (defence in depth)", db, async () => {
  const foreign = `${F}/${PF}/44444444-4444-4444-4444-444444444444.jpg`;
  q(`insert into public.plant_images(plant_id,owner_id,storage_path) values (:'p', :'u', :'a')`, { p: PE, u: E, a: foreign });
  signed.length = 0;
  const doc = await (await exp("jwt-e")).json() as any;
  assert.ok(!signed[0].paths.includes(foreign));
  assert.equal(doc.photos.length, 3); assert.equal(doc.photos.filter((p: any) => p.url === null).length, 1);
  q(`delete from public.plant_images where storage_path = :'a'`, { a: foreign });
});

test("NFR-06: user F gets only F's data with F's token (and E's token never yields F)", db, async () => {
  const f = await (await exp("jwt-f")).json() as any;
  assert.equal(f.plants.length, 1); assert.equal(f.plants[0].id, PF); assert.equal(f.photos.length, 1);
  assert.ok(!JSON.stringify(f).includes(E));
});

test("NFR-07: empty account (profile only) -> 200 with empty arrays, header-only CSVs; an app can tell it from a failure", db, async () => {
  const doc = await (await exp("jwt-g")).json() as any;
  assert.equal(doc.profile.id, G);
  for (const t of [...TABLES, "photos"]) assert.deepEqual(doc[t], [], t);
  const z = unzip(new Uint8Array(await (await exp("jwt-g", "csv")).arrayBuffer()));
  for (const [name, cols] of Object.entries(CSV_COLUMNS)) { assert.equal(z.files[`${name}.csv`].length, 1, name); assert.equal(z.files[`${name}.csv`][0].join(","), cols.join(",")); }
});

test("export_account rows have exactly the columns of CSV_COLUMNS (schema drift fails here), and no secret column", db, async () => {
  const doc = await (await exp("jwt-e")).json() as any;
  for (const t of TABLES) assert.deepEqual(Object.keys(doc[t][0]).sort(), [...CSV_COLUMNS[t]].sort(), t);
  assert.deepEqual(Object.keys(doc.profile).sort(), ["created_at", "display_name", "id", "is_premium"]);
});

/** Independent check of the ZIP: Python's zipfile (CRC-verified) + csv module. */
function unzip(bytes: Uint8Array): { names: string[]; files: Record<string, string[][]> } {
  const py = `import sys,io,zipfile,csv,json
z=zipfile.ZipFile(io.BytesIO(sys.stdin.buffer.read()))
bad=z.testzip()
if bad: sys.exit("bad crc: "+bad)
out={n:list(csv.reader(io.StringIO(z.read(n).decode("utf-8"),newline=""))) for n in z.namelist()}
print(json.dumps({"names":z.namelist(),"files":out}))`;
  const r = spawnSync("python3", ["-I", "-c", py], { input: bytes, maxBuffer: 1 << 26 });
  assert.equal(r.status, 0, String(r.stderr));
  return JSON.parse(String(r.stdout));
}

test("NFR-07: CSV export is application/zip with one CSV per table, UTF-8, header row, one row per record, valid CRCs", db, async () => {
  const r = await exp("jwt-e", "csv");
  assert.equal(r.status, 200); assert.equal(r.headers.get("content-type"), "application/zip"); assert.equal(r.headers.get("cache-control"), "no-store");
  assert.match(r.headers.get("content-disposition")!, /\.zip"$/);
  const z = unzip(new Uint8Array(await r.arrayBuffer()));
  assert.deepEqual(z.names, [...Object.keys(CSV_COLUMNS)].map((t) => `${t}.csv`));
  assert.deepEqual(Object.fromEntries(Object.entries(z.files).map(([n, rows]) => [n, rows.length - 1])),
    { "plants.csv": 1, "devices.csv": 1, "readings.csv": 4, "readings_hourly.csv": 2, "events.csv": 1, "alerts.csv": 1, "tips.csv": 1, "photos.csv": 2 });
  for (const [n, cols] of Object.entries(CSV_COLUMNS)) assert.deepEqual(z.files[`${n}.csv`][0], cols, n);
  const plant = Object.fromEntries(z.files["plants.csv"][0].map((c, i) => [c, z.files["plants.csv"][1][i]]));
  assert.equal(plant.name, `'${NASTY}`, "formula guard applied, commas/quotes/newline round-trip through a real CSV parser");
  assert.equal(plant.city, "Köln", "UTF-8");
  const rd = z.files["readings.csv"]; const t = rd[0].indexOf("temp_c"); assert.ok(rd.slice(1).every((row) => row[t] === "-3.5"), "negative numbers are not mangled");
  const ph = z.files["photos.csv"]; assert.ok(ph.slice(1).every((row) => /^https:\/\/storage\.test\//.test(row[ph[0].indexOf("url")]) && row[ph[0].indexOf("expires_at")] !== ""), "photo links are in the CSV export too");
  assert.ok(!z.files["tips.csv"].flat().join("").includes(F));
});

test("NFR-06: the SQL function is service_role only (API roles get permission denied), and only returns the id it is given", db, () => {
  for (const role of ["anon", "authenticated"]) {
    const r = psql(url!, `set role ${role}; select public.export_account('${E}');`);
    assert.ok(!r.ok && /permission denied/.test(r.err), `${role}: ${r.err}`);
  }
  const f = JSON.parse(q(`select public.export_account(:'u')::text`, { u: F }));
  assert.ok(!JSON.stringify(f).includes(E)); assert.equal(f.plants.length, 1);
  assert.equal(psql(url!, `select public.export_account(null)`).ok, false);
});

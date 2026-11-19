// GET /export (app, user JWT): NFR-07 (data export before deletion), FR-A01 (account data), NFR-06 (only the caller's rows).
// Plain TypeScript, no dependencies (Deno on Supabase, Node 22+ in tests). Contract: docs/interfaces/openapi.yaml /export.
import { bearer, type Deps, err } from "./lib.ts";

/** Photo links live 7 days (openapi /export). The app downloads the photos from these URLs BEFORE the delete screen unlocks (A-107 option b). */
export const PHOTO_URL_TTL_SECONDS = 7 * 24 * 3600;

type Row = Record<string, unknown>;
/** Column order of the CSV files (header row). Must equal the keys of the rows export_account() returns (checked by a test, so schema drift fails CI). */
export const CSV_COLUMNS: Record<string, string[]> = {
  plants: ["id", "owner_id", "name", "location_type", "area", "soil_type", "species", "city", "dry_threshold_pct", "wet_threshold_pct", "created_at", "updated_at"],
  devices: ["id", "hw_id", "owner_id", "plant_id", "name", "claimed_at", "last_seen_at", "fw_version", "model_version", "fw_target", "model_target", "low_battery_mv",
    "forecast_h", "forecast_at", "cal_dry_raw", "cal_wet_raw", "cal_at", "created_at"],
  readings: ["device_id", "ts", "owner_id", "plant_id", "moisture_pct", "moisture_raw", "temp_c", "rh_pct", "lux", "vbat_mv", "plausible", "received_at"],
  readings_hourly: ["device_id", "hour", "owner_id", "plant_id", "n", "moisture_avg", "moisture_min", "moisture_max", "temp_avg", "rh_avg", "lux_avg", "vbat_min_mv"],
  events: ["id", "device_id", "owner_id", "plant_id", "ts", "type", "critical", "received_at"],
  alerts: ["id", "owner_id", "device_id", "plant_id", "kind", "opened_at", "resolved_at", "notified_at", "detail"],
  tips: ["id", "plant_id", "owner_id", "generated_at", "expires_at", "content", "weather", "model", "guardrail_version"],
  photos: ["id", "plant_id", "taken_at", "url", "expires_at", "file"],
};
const TABLES = Object.keys(CSV_COLUMNS).filter((t) => t !== "photos");

/** One CSV cell (RFC 4180). Strings that a spreadsheet would run as a formula (= + - @ tab CR first) get a leading ' (CSV injection); numbers are never touched, so -3.5 stays -3.5. */
export function csvCell(v: unknown): string {
  if (v === null || v === undefined) return "";
  let s = typeof v === "object" ? JSON.stringify(v) : String(v);
  if (typeof v === "string" && /^[=+\-@\t\r]/.test(s)) s = `'${s}`;
  return /[",\r\n]/.test(s) ? `"${s.replaceAll('"', '""')}"` : s;
}
export function toCsv(columns: string[], rows: Row[]): string {
  return [columns.join(","), ...rows.map((r) => columns.map((c) => csvCell(r[c])).join(","))].map((l) => l + "\r\n").join("");
}

const CRC = (() => { const t = new Uint32Array(256); for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; t[n] = c >>> 0; } return t; })();
export function crc32(b: Uint8Array): number { let c = 0xffffffff; for (const x of b) c = CRC[(c ^ x) & 0xff] ^ (c >>> 8); return (c ^ 0xffffffff) >>> 0; }

/** Minimal ZIP writer, method 0 (stored), UTF-8 names, no ZIP64 (an export of one user stays far below 4 GiB / 65535 files). */
export function zipStore(files: { name: string; data: Uint8Array }[], when: Date): Uint8Array {
  const enc = new TextEncoder();
  const dosTime = (when.getUTCHours() << 11) | (when.getUTCMinutes() << 5) | (when.getUTCSeconds() >> 1);
  const dosDate = ((Math.max(when.getUTCFullYear(), 1980) - 1980) << 9) | ((when.getUTCMonth() + 1) << 5) | when.getUTCDate();
  const chunks: Uint8Array[] = []; const central: Uint8Array[] = []; let offset = 0;
  const hdr = (n: number) => { const a = new Uint8Array(n); return [a, new DataView(a.buffer)] as const; };
  for (const f of files) {
    const name = enc.encode(f.name), crc = crc32(f.data);
    const [l, lv] = hdr(30);
    lv.setUint32(0, 0x04034b50, true); lv.setUint16(4, 20, true); lv.setUint16(6, 0x0800, true); lv.setUint16(8, 0, true);
    lv.setUint16(10, dosTime, true); lv.setUint16(12, dosDate, true); lv.setUint32(14, crc, true);
    lv.setUint32(18, f.data.length, true); lv.setUint32(22, f.data.length, true); lv.setUint16(26, name.length, true);
    const [c, cv] = hdr(46);
    cv.setUint32(0, 0x02014b50, true); cv.setUint16(4, 20, true); cv.setUint16(6, 20, true); cv.setUint16(8, 0x0800, true); cv.setUint16(10, 0, true);
    cv.setUint16(12, dosTime, true); cv.setUint16(14, dosDate, true); cv.setUint32(16, crc, true);
    cv.setUint32(20, f.data.length, true); cv.setUint32(24, f.data.length, true); cv.setUint16(28, name.length, true); cv.setUint32(42, offset, true);
    chunks.push(l, name, f.data); central.push(c, name);
    offset += 30 + name.length + f.data.length;
  }
  const cdSize = central.reduce((n, a) => n + a.length, 0);
  const [e, ev] = hdr(22);
  ev.setUint32(0, 0x06054b50, true); ev.setUint16(8, files.length, true); ev.setUint16(10, files.length, true); ev.setUint32(12, cdSize, true); ev.setUint32(16, offset, true);
  const all = [...chunks, ...central, e]; const out = new Uint8Array(all.reduce((n, a) => n + a.length, 0));
  let p = 0; for (const a of all) { out.set(a, p); p += a.length; }
  return out;
}

/**
 * GET /export?format=json|csv (app, user JWT): NFR-07, FR-A01, NFR-06. The user is ONLY the one the token verifies (auth.getUser); there is no
 * parameter that names a user. Order of checks: method (405) -> token (401, before anything is read) -> format (400) -> data (500 on any failure).
 * Data comes from the service_role-only SQL function export_account(p_user), which filters every table on owner_id and covers all retained data
 * for free and premium users alike. Photos are LINKED as signed Storage URLs valid 7 days (PHOTO_URL_TTL_SECONDS), each with its absolute
 * expires_at, so the app can download them before it unlocks "delete account". If signing fails as a whole the export fails (500) instead of
 * silently returning a document without photo links: the app deletes after exporting. A photo whose Storage object is missing gets url null.
 */
export async function handleExport(req: Request, deps: Deps): Promise<Response> {
  if (req.method !== "GET") return err(405, "method_not_allowed");
  const jwt = bearer(req);
  const uid = jwt ? await deps.getUserId(jwt) : null;
  if (!uid) return err(401, "unauthorized", "missing or invalid user JWT");
  const format = new URL(req.url).searchParams.get("format");
  if (format !== "json" && format !== "csv") return err(400, "bad_request", "format must be json or csv");
  const { data, error } = await deps.rpc("export_account", { p_user: uid });
  if (error || typeof data !== "object" || data === null) return err(500, "internal");
  const d = data as Record<string, unknown>;
  if (!TABLES.every((t) => Array.isArray(d[t])) || !Array.isArray(d.photo_rows)) return err(500, "internal");
  const now = new Date();   // taken BEFORE signing: the real link lifetime is >= the stated one
  const rows = d.photo_rows as { id: string; plant_id: string; taken_at: string; storage_path: string }[];
  const own = rows.filter((p) => typeof p.storage_path === "string" && p.storage_path.startsWith(`${uid}/`));   // defence in depth: never sign a foreign path
  let urls: Record<string, string | null> = {};
  if (own.length > 0) {
    const s = await deps.signPhotoUrls(own.map((p) => p.storage_path), PHOTO_URL_TTL_SECONDS);
    if ("error" in s) return err(500, "internal");
    urls = s.urls;
  }
  const expiresAt = new Date(now.getTime() + PHOTO_URL_TTL_SECONDS * 1000).toISOString();
  const photos = rows.map((p) => {
    const url = own.includes(p) ? urls[p.storage_path] ?? null : null;
    return { id: p.id, plant_id: p.plant_id, taken_at: p.taken_at, url, expires_at: url ? expiresAt : null, file: p.storage_path.split("/").slice(1).join("/") };
  });
  const stamp = now.toISOString().slice(0, 10);
  const common = { "cache-control": "no-store" };   // personal data and bearer-like URLs: never cached
  if (format === "json") {
    const doc: Row = { exported_at: now.toISOString(), profile: d.profile ?? null };
    for (const t of TABLES) doc[t] = d[t];
    doc.photos = photos;
    return new Response(JSON.stringify(doc), { status: 200, headers: { ...common, "content-type": "application/json", "content-disposition": `attachment; filename="nilwerk-export-${stamp}.json"` } });
  }
  const enc = new TextEncoder();
  const all: Record<string, Row[]> = { ...Object.fromEntries(TABLES.map((t) => [t, d[t] as Row[]])), photos };
  const zip = zipStore(Object.keys(CSV_COLUMNS).map((t) => ({ name: `${t}.csv`, data: enc.encode(toCsv(CSV_COLUMNS[t], all[t])) })), now);
  return new Response(zip, { status: 200, headers: { ...common, "content-type": "application/zip", "content-disposition": `attachment; filename="nilwerk-export-${stamp}.zip"` } });
}

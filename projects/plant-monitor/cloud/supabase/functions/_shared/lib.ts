// Shared helpers for the 4.B2 edge functions. Plain TypeScript, no dependencies: runs in Deno (Supabase) and Node 22+ (tests).
// Requirements: FR-D01, FR-D03, FR-D04, FR-A02, NFR-06 (per-device tokens, stored hashed, ADR-004).

export interface RpcResult { data: unknown; error: { message: string } | null }
export interface Deps {
  /** Calls a service_role-only SQL function (migration 20261108000004_device_api.sql). */
  rpc(name: string, args: Record<string, unknown>): Promise<RpcResult>;
  /** Verifies a Supabase user JWT, returns the user id or null (only used by /claim-token). */
  getUserId(jwt: string): Promise<string | null>;
  randomBytes(n: number): Uint8Array;
  /** Deletes every Storage object under '<userId>/' in the private bucket plant-photos (only used by DELETE /account). */
  deleteUserPhotos(userId: string, knownPaths: string[]): Promise<{ message: string } | null>;
  /** Deletes the auth.users row (FK cascade removes the user's data). A user that does not exist anymore is NOT an error (idempotent). */
  deleteAuthUser(userId: string): Promise<{ message: string } | null>;
  /**
   * Signs Storage paths of the private bucket plant-photos for `expiresInSeconds` (only used by GET /export). A whole-call failure is `{error}`;
   * a single object that cannot be signed (missing in Storage) is `null` in `urls`.
   */
  signPhotoUrls(paths: string[], expiresInSeconds: number): Promise<{ urls: Record<string, string | null> } | { error: { message: string } }>;
}

export const MAX_BODY_BYTES = 64 * 1024;   // openapi /ingest 413
export const MAX_SAMPLES = 192;            // device-report.schema.json maxItems (>= 96 = 24 h of buffer, FR-D04)

/** Lower-case hex SHA-256 of the UTF-8 token string. Only this digest is ever stored or sent to the database (ADR-004, NFR-06). */
export async function sha256Hex(s: string): Promise<string> {
  const d = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s));
  return [...new Uint8Array(d)].map((b) => b.toString(16).padStart(2, "0")).join("");
}
export const toHex = (b: Uint8Array) => [...b].map((x) => x.toString(16).padStart(2, "0")).join("");
export function toBase64Url(b: Uint8Array): string {
  let s = ""; for (const x of b) s += String.fromCharCode(x);
  return btoa(s).replaceAll("+", "-").replaceAll("/", "_").replaceAll("=", "");
}

export function json(status: number, body: unknown, headers: Record<string, string> = {}): Response {
  return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json", ...headers } });
}
export const err = (status: number, error: string, message?: string) => json(status, message ? { error, message } : { error });

export function bearer(req: Request): string | null {
  const m = /^Bearer ([^\s]+)$/.exec(req.headers.get("authorization") ?? "");
  return m ? m[1] : null;
}

/** Reads a JSON body with the 64 KiB cap. Returns a Response on failure. */
export async function readJson(req: Request): Promise<{ body: unknown } | { fail: Response }> {
  const text = await req.text();
  if (new TextEncoder().encode(text).length > MAX_BODY_BYTES) return { fail: err(413, "payload_too_large", "body > 64 KiB") };
  try { return { body: JSON.parse(text) }; } catch { return { fail: err(400, "bad_request", "body is not valid JSON") }; }
}

type Obj = Record<string, unknown>;
const isObj = (v: unknown): v is Obj => typeof v === "object" && v !== null && !Array.isArray(v);
const isInt = (v: unknown): v is number => typeof v === "number" && Number.isInteger(v);
const isNum = (v: unknown): v is number => typeof v === "number" && Number.isFinite(v);
const noExtra = (o: Obj, allowed: string[], where: string): string | null => {
  const x = Object.keys(o).find((k) => !allowed.includes(k)); return x ? `${where}: unknown property '${x}'` : null;
};
const EVENT_TYPES = ["wetting", "wetting_unexpected", "fast_drying", "waterlogged", "sensor_out_of_soil", "sensor_fault"];
const MIN_TS = 1700000000;

/**
 * Validates a /ingest body against docs/interfaces/device-report.schema.json (hand-written, no dependency; the fixtures test
 * checks it against the schema's valid and invalid fixtures). Returns null if valid, else the HTTP status and message.
 * Plausible ranges are NOT enforced here: out-of-range samples are stored with plausible=false (FR-D01, ADR-013).
 */
export function validateReport(r: unknown): { status: 400 | 413; message: string } | null {
  const bad = (message: string) => ({ status: 400 as const, message });
  if (!isObj(r)) return bad("body must be an object");
  if (Array.isArray(r.samples) && r.samples.length > MAX_SAMPLES) return { status: 413, message: `more than ${MAX_SAMPLES} samples` };
  let e = noExtra(r, ["v", "sent_at", "trigger", "fw", "model", "forecast_h", "cal", "ota", "samples", "events"], "report");
  if (e) return bad(e);
  for (const k of ["v", "sent_at", "trigger", "fw", "samples"]) if (!(k in r)) return bad(`missing field '${k}'`);
  if (r.v !== 1) return bad("v must be 1");
  if (!isInt(r.sent_at) || r.sent_at < MIN_TS) return bad("sent_at must be unix seconds >= 1700000000");
  if (!["scheduled", "critical", "reconnect"].includes(r.trigger as string)) return bad("trigger must be scheduled|critical|reconnect");
  if (typeof r.fw !== "string" || r.fw.length > 32) return bad("fw must be a string of at most 32 chars");
  if ("model" in r && (typeof r.model !== "string" || r.model.length > 32)) return bad("model must be a string of at most 32 chars");
  if ("forecast_h" in r && r.forecast_h !== null && (!isNum(r.forecast_h) || r.forecast_h < 0 || r.forecast_h > 72)) return bad("forecast_h must be null or 0..72");
  if ("cal" in r) {
    const c = r.cal;
    if (!isObj(c)) return bad("cal must be an object");
    if ((e = noExtra(c, ["dry_raw", "wet_raw", "at"], "cal"))) return bad(e);
    for (const k of ["dry_raw", "wet_raw"]) if (!isInt(c[k]) || (c[k] as number) < 0 || (c[k] as number) > 4095) return bad(`cal.${k} must be an integer 0..4095`);
    if ("at" in c && !isInt(c.at)) return bad("cal.at must be an integer");
  }
  if ("ota" in r) {
    const o = r.ota;
    if (!isObj(o)) return bad("ota must be an object");
    if ((e = noExtra(o, ["version", "kind", "status"], "ota"))) return bad(e);
    if (typeof o.version !== "string" || o.version.length > 32) return bad("ota.version must be a string of at most 32 chars");
    if ("kind" in o && !["fw", "model"].includes(o.kind as string)) return bad("ota.kind must be fw|model");
    if (!["ok", "rolled_back", "hash_mismatch", "download_failed", "battery_low"].includes(o.status as string)) return bad("ota.status invalid");
  }
  if (!Array.isArray(r.samples) || r.samples.length < 1) return bad("samples must be a non-empty array");
  for (const [i, s] of r.samples.entries()) {
    if (!isObj(s)) return bad(`samples[${i}] must be an object`);
    if ((e = noExtra(s, ["ts", "moisture_pct", "moisture_raw", "temp_c", "rh_pct", "lux", "vbat_mv"], `samples[${i}]`))) return bad(e);
    if (!isInt(s.ts) || s.ts < MIN_TS) return bad(`samples[${i}].ts must be unix seconds >= 1700000000`);
    for (const k of ["moisture_pct", "temp_c", "rh_pct", "lux"]) if (k in s && s[k] !== null && !isNum(s[k])) return bad(`samples[${i}].${k} must be a number or null`);
    if ("moisture_raw" in s && s.moisture_raw !== null && (!isInt(s.moisture_raw) || s.moisture_raw < 0 || s.moisture_raw > 4095)) return bad(`samples[${i}].moisture_raw must be an integer 0..4095 or null`);
    if ("vbat_mv" in s && s.vbat_mv !== null && !isInt(s.vbat_mv)) return bad(`samples[${i}].vbat_mv must be an integer or null`);
  }
  if ("events" in r) {
    if (!Array.isArray(r.events) || r.events.length > 32) return bad("events must be an array of at most 32");
    for (const [i, ev] of r.events.entries()) {
      if (!isObj(ev)) return bad(`events[${i}] must be an object`);
      if ((e = noExtra(ev, ["ts", "type"], `events[${i}]`))) return bad(e);
      if (!isInt(ev.ts) || ev.ts < MIN_TS) return bad(`events[${i}].ts must be unix seconds >= 1700000000`);
      if (!EVENT_TYPES.includes(ev.type as string)) return bad(`events[${i}].type invalid`);
    }
  }
  return null;
}

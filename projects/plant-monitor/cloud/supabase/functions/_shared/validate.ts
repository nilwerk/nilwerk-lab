// Request validation for the device API. Mirrors docs/interfaces/device-report.schema.json and the openapi.yaml
// /device-claim body (source of truth: those files). Hand-written (no dependency, zero cost); handlers.test.ts feeds the
// committed valid fixture through this code. Plausible ranges (FR-D01) are NOT enforced here on purpose:
// out-of-range samples are stored with plausible=false in SQL (schema description), so one bad value never loses a batch.

export type Result<T> = { ok: true; value: T } | { ok: false; message: string };
const isObj = (x: unknown): x is Record<string, unknown> => typeof x === "object" && x !== null && !Array.isArray(x);
const isInt = (x: unknown): x is number => typeof x === "number" && Number.isInteger(x);
const numOrNull = (x: unknown) => x === null || (typeof x === "number" && Number.isFinite(x));
const MIN_TS = 1700000000;
export const MAX_SAMPLES = 192;          // schema maxItems; FR-D04 needs 96 (24 h of 15-min samples)
export const MAX_EVENTS = 32;
const EVENT_TYPES = ["wetting", "wetting_unexpected", "fast_drying", "waterlogged", "sensor_out_of_soil", "sensor_fault"];

function noExtra(o: Record<string, unknown>, allowed: string[], where: string): string | null {
  for (const k of Object.keys(o)) if (!allowed.includes(k)) return `${where}: unexpected field '${k}'`;
  return null;
}

export interface ClaimBody { hw_id: string; claim_token: string; name?: string; fw: string }
export function validateClaim(b: unknown): Result<ClaimBody> {
  if (!isObj(b)) return { ok: false, message: "body must be an object" };
  const extra = noExtra(b, ["hw_id", "claim_token", "name", "fw"], "body");
  if (extra) return { ok: false, message: extra };
  if (typeof b.hw_id !== "string" || !/^nw-[0-9a-f]{12}$/.test(b.hw_id)) return { ok: false, message: "hw_id: must match ^nw-[0-9a-f]{12}$" };
  if (typeof b.claim_token !== "string" || b.claim_token.length < 1 || b.claim_token.length > 256) return { ok: false, message: "claim_token: required string" };
  if (b.name !== undefined && (typeof b.name !== "string" || b.name.length > 80)) return { ok: false, message: "name: string, max 80" };
  if (typeof b.fw !== "string" || b.fw.length < 1 || b.fw.length > 32) return { ok: false, message: "fw: required string, max 32" };
  return { ok: true, value: b as unknown as ClaimBody };
}

export interface Report { v: 1; sent_at: number; trigger: string; fw: string; samples: Record<string, unknown>[]; [k: string]: unknown }
export function validateReport(b: unknown): Result<Report> {
  if (!isObj(b)) return { ok: false, message: "body must be an object" };
  const extra = noExtra(b, ["v", "sent_at", "trigger", "fw", "model", "forecast_h", "cal", "ota", "samples", "events"], "body");
  if (extra) return { ok: false, message: extra };
  if (b.v !== 1) return { ok: false, message: "v: must be 1" };
  if (!isInt(b.sent_at) || b.sent_at < MIN_TS) return { ok: false, message: "sent_at: unix seconds >= 1700000000" };
  if (!["scheduled", "critical", "reconnect"].includes(b.trigger as string)) return { ok: false, message: "trigger: scheduled | critical | reconnect" };
  if (typeof b.fw !== "string" || b.fw.length > 32) return { ok: false, message: "fw: string, max 32" };
  if (b.model !== undefined && (typeof b.model !== "string" || b.model.length > 32)) return { ok: false, message: "model: string, max 32" };
  if (b.forecast_h !== undefined && !(b.forecast_h === null || (typeof b.forecast_h === "number" && b.forecast_h >= 0 && b.forecast_h <= 72)))
    return { ok: false, message: "forecast_h: number 0..72 or null" };
  if (b.cal !== undefined) {
    const c = b.cal;
    if (!isObj(c) || noExtra(c, ["dry_raw", "wet_raw", "at"], "cal") || !isInt(c.dry_raw) || !isInt(c.wet_raw) ||
        c.dry_raw < 0 || c.dry_raw > 4095 || c.wet_raw < 0 || c.wet_raw > 4095 || (c.at !== undefined && !isInt(c.at)))
      return { ok: false, message: "cal: {dry_raw, wet_raw} integers 0..4095" };
  }
  if (!Array.isArray(b.samples) || b.samples.length < 1) return { ok: false, message: "samples: non-empty array" };
  if (b.samples.length > MAX_SAMPLES) return { ok: false, message: `samples: max ${MAX_SAMPLES}` };
  for (const [i, s] of b.samples.entries()) {
    const w = `samples[${i}]`;
    if (!isObj(s)) return { ok: false, message: `${w}: object` };
    const e = noExtra(s, ["ts", "moisture_pct", "moisture_raw", "temp_c", "rh_pct", "lux", "vbat_mv"], w);
    if (e) return { ok: false, message: e };
    if (!isInt(s.ts) || s.ts < MIN_TS) return { ok: false, message: `${w}.ts: unix seconds >= 1700000000` };
    for (const k of ["moisture_pct", "temp_c", "rh_pct", "lux"]) if (s[k] !== undefined && !numOrNull(s[k])) return { ok: false, message: `${w}.${k}: number or null` };
    if (s.moisture_raw !== undefined && !(s.moisture_raw === null || (isInt(s.moisture_raw) && s.moisture_raw >= 0 && s.moisture_raw <= 4095))) return { ok: false, message: `${w}.moisture_raw: integer 0..4095 or null` };
    if (s.vbat_mv !== undefined && !(s.vbat_mv === null || isInt(s.vbat_mv))) return { ok: false, message: `${w}.vbat_mv: integer or null` };
  }
  if (b.events !== undefined) {
    if (!Array.isArray(b.events) || b.events.length > MAX_EVENTS) return { ok: false, message: `events: array, max ${MAX_EVENTS}` };
    for (const [i, ev] of b.events.entries()) {
      if (!isObj(ev) || noExtra(ev, ["ts", "type"], `events[${i}]`) || !isInt(ev.ts) || ev.ts < MIN_TS || !EVENT_TYPES.includes(ev.type as string))
        return { ok: false, message: `events[${i}]: {ts, type} with a known type` };
    }
  }
  return { ok: true, value: b as unknown as Report };
}

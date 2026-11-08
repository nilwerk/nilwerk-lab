// Request handlers for POST /device-claim and POST /ingest (docs/interfaces/openapi.yaml). Pure functions over a small
// `Db` interface, so tests run with a mock (no Supabase, no network). The Deno entry points wire `Db` to supabase-js.
// Requirements: FR-D01 (plausible ranges -> flagged in SQL), FR-D02/FR-D04 (hourly + 24 h buffer, idempotent),
// FR-D03/FR-A03/FR-A08 (claim, release), FR-E03/FR-A07 (events -> alerts), FR-D05 (OTA manifest), NFR-04, NFR-06 (hash-only tokens).
import { newDeviceToken, sha256ByteaHex } from "./crypto.ts";
import { type Report, validateClaim, validateReport } from "./validate.ts";

export interface Db {
  /** SQL authenticate_device(): status for a token hash. */
  authenticate(tokenHashHex: string): Promise<{ device_id: string | null; status: "ok" | "revoked" | "invalid" }>;
  /** SQL claim_device(): throws DbError with code NW401 / NW409 per the openapi rules. */
  claim(a: { hw_id: string; claim_hash: string; name: string | null; fw: string; token_hash: string }): Promise<{ device_id: string; server_time: number; config: unknown }>;
  /** SQL ingest_report(): one transaction, idempotent on (device, ts). */
  ingest(deviceId: string, report: Report, receivedAtIso: string): Promise<IngestResult>;
  /** Signed Storage URL for an OTA artefact (FR-D05); absent in tests that do not need it. */
  signUrl?(storagePath: string): Promise<string>;
}
export interface Artifact { version: string; storage_path: string; sha256: string; size_bytes: number; min_battery_mv: number }
export interface IngestResult { server_time: number; accepted: number; duplicates: number; implausible: number; config: unknown; fw_target: Artifact | null; model_target: Artifact | null }
export class DbError extends Error {
  code: string;   // no parameter property: Node's type stripping (tests) rejects it
  constructor(code: string, msg = code) { super(msg); this.code = code; }
}

export interface Out { status: number; body: unknown }
export const MAX_BODY_BYTES = 64 * 1024;           // openapi /ingest 413
const err = (status: number, error: string, message?: string): Out => ({ status, body: message ? { error, message } : { error } });

function parseJson(raw: string): { ok: true; v: unknown } | { ok: false } {
  try { return { ok: true, v: JSON.parse(raw) }; } catch { return { ok: false }; }
}

export async function handleClaim(rawBody: string, db: Db): Promise<Out> {
  if (rawBody.length > MAX_BODY_BYTES) return err(413, "payload_too_large");
  const j = parseJson(rawBody);
  if (!j.ok) return err(400, "bad_request", "body is not JSON");
  const v = validateClaim(j.v);
  if (!v.ok) return err(400, "bad_request", v.message);
  const token = newDeviceToken();                                   // shown once, only its hash is stored (ADR-004)
  try {
    const r = await db.claim({
      hw_id: v.value.hw_id, claim_hash: await sha256ByteaHex(v.value.claim_token),
      name: v.value.name ?? null, fw: v.value.fw, token_hash: await sha256ByteaHex(token),
    });
    return { status: 200, body: { device_id: r.device_id, device_token: token, server_time: r.server_time, config: r.config } };
  } catch (e) {
    if (e instanceof DbError && e.code === "NW401") return err(401, "claim_token_invalid");
    if (e instanceof DbError && e.code === "NW409") return err(409, "device_owned", "release the device in the app first (FR-A08)");
    throw e;
  }
}

export async function handleIngest(authHeader: string | null, rawBody: string, db: Db, now: Date = new Date()): Promise<Out> {
  // 1. authenticate (NFR-06): bearer 256-bit hex token, looked up by SHA-256 hash
  const m = /^Bearer ([0-9a-f]{64})$/.exec(authHeader ?? "");
  if (!m) return err(401, "token_invalid");
  const auth = await db.authenticate(await sha256ByteaHex(m[1]));
  if (auth.status === "invalid" || !auth.device_id) return err(401, "token_invalid");
  if (auth.status === "revoked") return err(401, "token_revoked");        // device stops uploading, re-enters setup (openapi)
  // 2. size + schema
  if (rawBody.length > MAX_BODY_BYTES) return err(413, "payload_too_large");
  const j = parseJson(rawBody);
  if (!j.ok) return err(400, "bad_request", "body is not JSON");
  const peek = j.v as { samples?: unknown[] } | null;
  if (peek && Array.isArray(peek.samples) && peek.samples.length > 192) return err(413, "payload_too_large", "max 192 samples per request");
  const v = validateReport(j.v);
  if (!v.ok) return err(400, "bad_request", v.message);
  // 3. one SQL transaction: samples (idempotent, plausible flag), events, device row, evaluate_alerts()
  let r: IngestResult;
  try { r = await db.ingest(auth.device_id, v.value, now.toISOString()); }
  catch (e) {
    if (e instanceof DbError && e.code === "NW403") return err(401, "token_revoked");   // released between auth and insert
    throw e;
  }
  // 4. response: config + OTA manifest with signed URLs (FR-D05)
  const art = async (a: Artifact | null) => !a ? null : { version: a.version, url: db.signUrl ? await db.signUrl(a.storage_path) : a.storage_path,
    sha256: a.sha256, size_bytes: a.size_bytes, min_battery_mv: a.min_battery_mv };
  return { status: 200, body: { server_time: r.server_time, accepted: r.accepted, duplicates: r.duplicates, implausible: r.implausible,
    config: r.config, fw_target: await art(r.fw_target), model_target: await art(r.model_target) } };
}

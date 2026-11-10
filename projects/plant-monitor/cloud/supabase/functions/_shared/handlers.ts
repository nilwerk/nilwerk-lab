// Request handlers for the three 4.B2 edge functions. Pure functions of (Request, Deps): the Deno entry points in
// ../<name>/index.ts wire Deps to supabase-js; the tests wire it to a local PostgreSQL. Contract: docs/interfaces/openapi.yaml.
import { bearer, type Deps, err, json, readJson, sha256Hex, toBase64Url, toHex, validateReport } from "./lib.ts";

const methodNotAllowed = () => err(405, "method_not_allowed");
const internal = () => err(500, "internal");   // never leak database messages

/** POST /claim-token (app, user JWT): FR-D03, FR-A03, FR-A02, NFR-06. 16 random bytes base64url, 15 min, single use, SHA-256 stored. */
export async function handleClaimToken(req: Request, deps: Deps): Promise<Response> {
  if (req.method !== "POST") return methodNotAllowed();
  const jwt = bearer(req);
  const uid = jwt ? await deps.getUserId(jwt) : null;
  if (!uid) return err(401, "unauthorized", "missing or invalid user JWT");
  const token = toBase64Url(deps.randomBytes(16));
  const { data, error } = await deps.rpc("issue_claim_token", { p_user: uid, p_token_hash: await sha256Hex(token) });
  if (error || !data) return internal();
  const d = data as { error?: string; expires_at?: string };
  if (d.error === "rate_limited") return json(429, { error: "rate_limited", message: "at most 10 open claim tokens" }, { "retry-after": "900" });
  if (d.error) return internal();
  return json(201, { claim_token: token, expires_at: d.expires_at });
}

/** POST /device-claim (device, claim token in body): FR-D03, FR-A03, FR-A08, NFR-06. Device token = 32 random bytes hex, shown once. */
export async function handleDeviceClaim(req: Request, deps: Deps): Promise<Response> {
  if (req.method !== "POST") return methodNotAllowed();
  const r = await readJson(req);
  if ("fail" in r) return r.fail;
  const b = r.body as Record<string, unknown>;
  const bad = (m: string) => err(400, "bad_request", m);
  if (typeof b !== "object" || b === null || Array.isArray(b)) return bad("body must be an object");
  const extra = Object.keys(b).find((k) => !["hw_id", "claim_token", "name", "fw"].includes(k));
  if (extra) return bad(`unknown property '${extra}'`);
  if (typeof b.hw_id !== "string" || !/^nw-[0-9a-f]{12}$/.test(b.hw_id)) return bad("hw_id must match ^nw-[0-9a-f]{12}$");
  if (typeof b.claim_token !== "string" || b.claim_token.length < 1 || b.claim_token.length > 128) return bad("claim_token is required");
  if (typeof b.fw !== "string" || b.fw.length > 32) return bad("fw must be a string of at most 32 chars");
  if ("name" in b && (typeof b.name !== "string" || b.name.length > 80)) return bad("name must be a string of at most 80 chars");
  const token = toHex(deps.randomBytes(32));
  const { data, error } = await deps.rpc("device_claim", {
    p_claim_hash: await sha256Hex(b.claim_token), p_token_hash: await sha256Hex(token),
    p_hw_id: b.hw_id, p_name: (b.name as string | undefined) ?? null, p_fw: b.fw,
  });
  if (error || !data) return internal();
  const d = data as { error?: string; device_id?: string; server_time?: number; config?: unknown };
  if (d.error === "claim_token_invalid") return err(401, "claim_token_invalid", "claim token unknown, expired or already used");
  if (d.error === "device_owned") return err(409, "device_owned", "release the device in its current account first");
  if (d.error || !d.device_id) return internal();
  return json(200, { device_id: d.device_id, device_token: token, server_time: d.server_time, config: d.config });
}

/**
 * POST /ingest (device bearer token): FR-D01, FR-D02, FR-D04, FR-A07, FR-E03, NFR-04, NFR-06.
 * Missing Authorization -> 401 before the body is read; a syntactically bad body is rejected with 400/413 before the token is
 * checked against the database (the token check and the inserts run in ONE database call, so a stolen-token replay cannot
 * learn anything from a 400). Unknown/revoked tokens -> 401 and nothing is written.
 */
export async function handleIngest(req: Request, deps: Deps): Promise<Response> {
  if (req.method !== "POST") return methodNotAllowed();
  const token = bearer(req);
  if (!token) return err(401, "token_invalid", "missing bearer token");
  const r = await readJson(req);
  if ("fail" in r) return r.fail;
  const v = validateReport(r.body);
  if (v) return err(v.status, v.status === 413 ? "payload_too_large" : "bad_request", v.message);
  const { data, error } = await deps.rpc("ingest_batch", { p_token_hash: await sha256Hex(token), p_report: r.body });
  if (error || !data) return internal();
  const d = data as Record<string, unknown>;
  if (d.error === "token_invalid" || d.error === "token_revoked") return err(401, d.error as string);
  if (d.error) return internal();
  return json(200, d);
}

/**
 * DELETE /account (app, user JWT): FR-A01, FR-A08, NFR-07 (GDPR erasure), NFR-06. The user is ONLY the one the token verifies
 * (auth.getUser); the body cannot name another user. Body {"confirm":"DELETE"} is required. Order (openapi /account):
 * release + revoke devices -> delete Storage photos -> delete the auth user (FK cascade removes the rest). Every step is
 * idempotent and a failure returns 500 before the auth user is deleted, so the client can simply retry. 204 = erased.
 */
export async function handleDeleteAccount(req: Request, deps: Deps): Promise<Response> {
  if (req.method !== "DELETE") return methodNotAllowed();
  const jwt = bearer(req);
  const uid = jwt ? await deps.getUserId(jwt) : null;
  if (!uid) return err(401, "unauthorized", "missing or invalid user JWT");
  const r = await readJson(req);
  if ("fail" in r) return r.fail;
  const b = r.body as Record<string, unknown>;
  if (typeof b !== "object" || b === null || Array.isArray(b) || Object.keys(b).some((k) => k !== "confirm") || b.confirm !== "DELETE") {
    return err(400, "bad_request", 'body must be {"confirm":"DELETE"}');
  }
  const { data, error } = await deps.rpc("release_account_devices", { p_user: uid });
  if (error || !data) return internal();
  const paths = (data as { photo_paths?: unknown }).photo_paths;
  if (!Array.isArray(paths)) return internal();
  if (await deps.deleteUserPhotos(uid, paths as string[])) return internal();
  if (await deps.deleteAuthUser(uid)) return internal();
  return new Response(null, { status: 204 });
}

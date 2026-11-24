// POST /api-keys and DELETE /api-keys/{id} (app, user JWT): task 4.B2d. Requirements: FR-P03 (personal key for the user's AI, revocable),
// FR-P04 (premium only, public.is_premium() called as the user BEFORE any write), NFR-06 (only sha256 and the 8-char prefix are stored; the key
// is returned once and never logged). Contract: docs/interfaces/openapi.yaml /api-keys, docs/interfaces/db-schema.sql public.api_keys.
// Plain TypeScript, no dependencies: runs in Deno (Supabase) and Node 22.6+ (tests).
//
// Service role: db-schema.sql grants `authenticated` only a column SELECT on api_keys ("create / revoke only through the /api-keys edge function
// (service role)"), so the two writes cannot run as the user. They are the ONLY service-role calls: an insert whose owner_id is the verified
// caller, and one update filtered by id AND owner_id. Everything else (premium check, ownership check, the list) runs as the user under RLS.
import { bearer, err, json, sha256Hex, toBase64Url } from "./lib.ts";

export const NAME_MAX = 60;           // openapi maxLength, db check length(name) between 1 and 60
const BODY_MAX_BYTES = 2 * 1024;      // a name of 60 chars needs far less
const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export interface ApiKeysDeps {
  /** Verifies a user JWT and returns the user id, or null (401). */
  getUserId(jwt: string): Promise<string | null>;
  /** public.is_premium() called as the user (FR-P04). Null = the call failed. */
  isPremium(jwt: string): Promise<boolean | null>;
  randomBytes(n: number): Uint8Array;
  /** SERVICE ROLE. Inserts one key row for `ownerId` (the verified caller). `keyHashHex` is sha256(key) in hex. Null = failed. */
  insertKey(ownerId: string, row: { name: string; prefix: string; keyHashHex: string }): Promise<{ id: string } | null>;
  /** AS THE USER (RLS api_keys_select_own): does the caller own this key, and is it already revoked? Null = the call failed. */
  findOwnKey(jwt: string, id: string): Promise<{ found: false } | { found: true; revoked: boolean } | null>;
  /** SERVICE ROLE. Sets revoked_at on the row with this id AND this owner that is not revoked yet. False = the call failed. */
  revokeKey(ownerId: string, id: string): Promise<boolean>;
}

/** The part of the path after `api-keys`: [] for the collection, [id] for one key. Works behind /functions/v1/ and without it. */
function tail(url: string): string[] | null {
  const segs = new URL(url).pathname.split("/").filter((s) => s !== "");
  const i = segs.lastIndexOf("api-keys");
  return i < 0 ? null : segs.slice(i + 1);
}

/** A name per openapi: required string, 1..60 chars after trimming (the db check). Returns null when invalid. */
async function readName(req: Request): Promise<string | null> {
  const text = await req.text();
  if (new TextEncoder().encode(text).length > BODY_MAX_BYTES) return null;
  let body: unknown;
  try { body = JSON.parse(text); } catch { return null; }
  if (typeof body !== "object" || body === null || Array.isArray(body)) return null;
  const name = (body as Record<string, unknown>).name;
  if (typeof name !== "string") return null;
  const t = name.trim();
  return t.length >= 1 && t.length <= NAME_MAX ? t : null;
}

/**
 * Order of checks. POST: method (405) -> token (401) -> premium (403 premium_required, is_premium() as the user before ANY write; FR-P04) ->
 * body (400) -> insert (500, no detail). DELETE /{id}: method (405) -> token (401) -> id format (400) -> own key (404, indistinguishable from an
 * unknown id) -> revoke (204; an already revoked own key is 204 again and keeps its first revoked_at) -> 500 on any failure. Revoking needs no
 * premium: a lapsed user must still be able to switch their keys off (FR-P03). The list is a select under RLS in the app, no function.
 */
export async function handleApiKeys(req: Request, deps: ApiKeysDeps): Promise<Response> {
  const rest = tail(req.url);
  const isItem = rest !== null && rest.length === 1;
  if (rest === null || rest.length > 1) return err(404, "not_found");
  if (req.method !== (isItem ? "DELETE" : "POST")) return err(405, "method_not_allowed");
  const jwt = bearer(req);
  const uid = jwt ? await deps.getUserId(jwt) : null;
  if (!jwt || !uid) return err(401, "unauthorized", "missing or invalid user JWT");

  if (!isItem) {
    const premium = await deps.isPremium(jwt);
    if (premium === null) return err(500, "internal");
    if (!premium) return err(403, "premium_required", "API keys are a premium feature (FR-P04)");
    const name = await readName(req);
    if (name === null) return err(400, "bad_request", `name is required, a string of 1 to ${NAME_MAX} characters`);
    // Key = "nwk_" + 32 random bytes base64url (43 chars). Stored: sha256 and the first 8 characters only (NFR-06).
    const key = `nwk_${toBase64Url(deps.randomBytes(32))}`;
    const row = await deps.insertKey(uid, { name, prefix: key.slice(0, 8), keyHashHex: await sha256Hex(key) });
    if (!row) return err(500, "internal");
    return json(201, { id: row.id, key, prefix: key.slice(0, 8) }, { "cache-control": "no-store" });   // the only time the key leaves the server
  }

  const id = rest[0];
  if (!UUID_RE.test(id)) return err(400, "bad_request", "id must be a uuid");
  const own = await deps.findOwnKey(jwt, id);
  if (own === null) return err(500, "internal");
  if (!own.found) return err(404, "not_found");
  if (!own.revoked && !(await deps.revokeKey(uid, id))) return err(500, "internal");
  return new Response(null, { status: 204 });
}

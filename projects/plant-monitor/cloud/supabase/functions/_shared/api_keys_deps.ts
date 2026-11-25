// PostgREST calls of /api-keys (task 4.B2d; FR-P03, FR-P04, NFR-06). Split out of supabase.ts so tests can inject a fake client: no npm: import,
// no Deno API. `asUser` builds a client from the caller's JWT (premium check, ownership read: RLS applies); `admin` is the service-role client,
// used ONLY by insertKey and revokeKey because the table grants authenticated no insert or update (db-schema.sql).
import type { ApiKeysDeps } from "./api_keys.ts";

type Res = { data: unknown; error: unknown };
/** The slice of a supabase-js client that /api-keys uses. The query builder is thenable, like the real one. */
export interface KeysQuery {
  select(cols: string): KeysQuery;
  insert(row: Record<string, unknown>): KeysQuery;
  update(row: Record<string, unknown>): KeysQuery;
  eq(col: string, v: unknown): KeysQuery;
  is(col: string, v: null): KeysQuery;
  then: PromiseLike<Res>["then"];
}
export interface KeysClient {
  auth: { getUser(jwt: string): Promise<{ data: { user: { id: string } | null }; error: unknown }> };
  rpc(name: string): PromiseLike<Res>;
  from(table: string): KeysQuery;
}

export function buildApiKeysDeps(
  asUser: (jwt: string) => KeysClient, admin: () => KeysClient, randomBytes: (n: number) => Uint8Array,
): ApiKeysDeps {
  return {
    async getUserId(jwt) {
      const { data, error } = await asUser(jwt).auth.getUser(jwt);
      return error || !data.user ? null : data.user.id;
    },
    async isPremium(jwt) {
      const { data, error } = await asUser(jwt).rpc("is_premium");
      return error || typeof data !== "boolean" ? null : data;
    },
    randomBytes,
    async insertKey(ownerId, row) {
      // bytea travels as a '\x<hex>' string. returning only the id: the hash never comes back.
      const { data, error } = await admin().from("api_keys")
        .insert({ owner_id: ownerId, name: row.name, prefix: row.prefix, key_hash: `\\x${row.keyHashHex}` })
        .select("id") as unknown as Res;
      const first = Array.isArray(data) ? data[0] as { id?: unknown } | undefined : undefined;
      return error || !first || typeof first.id !== "string" ? null : { id: first.id };
    },
    async findOwnKey(jwt, id) {
      const { data, error } = await asUser(jwt).from("api_keys").select("id,revoked_at").eq("id", id) as unknown as Res;
      if (error || !Array.isArray(data)) return null;
      const row = data[0] as { revoked_at?: string | null } | undefined;
      return row ? { found: true, revoked: row.revoked_at != null } : { found: false };
    },
    async revokeKey(ownerId, id) {
      const { error } = await admin().from("api_keys")
        .update({ revoked_at: new Date().toISOString() }).eq("id", id).eq("owner_id", ownerId).is("revoked_at", null) as unknown as Res;
      return !error;
    },
  };
}

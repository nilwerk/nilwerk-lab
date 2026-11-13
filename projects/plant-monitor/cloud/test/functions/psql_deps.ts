// Test-only Deps: calls the SQL functions on a local PostgreSQL through psql (no npm dependencies, no Supabase, no secrets).
import { spawnSync } from "node:child_process";
import { randomBytes } from "node:crypto";
import type { Deps, RpcResult } from "../../supabase/functions/_shared/lib.ts";

export function psql(url: string, sql: string, vars: Record<string, string> = {}): { ok: boolean; out: string; err: string } {
  const a = ["-X", "-q", "-At", "-v", "ON_ERROR_STOP=1", url, ...Object.entries(vars).flatMap(([k, v]) => ["-v", `${k}=${v}`])];
  const r = spawnSync("psql", a, { input: sql, encoding: "utf8" });   // stdin so :'var' is interpolated
  return { ok: r.status === 0, out: r.stdout.trim(), err: r.stderr.trim() };
}

export const storage: { userId: string; knownPaths: string[] }[] = [];
let failPhotos = false;
export const setFailPhotos = (v: boolean) => { failPhotos = v; };

export function psqlDeps(url: string, users: Record<string, string>): Deps {
  return {
    async rpc(name, args): Promise<RpcResult> {
      const vars: Record<string, string> = {};
      const parts = Object.entries(args).map(([k, v]) => {
        vars[k] = typeof v === "string" ? v : JSON.stringify(v);
        return `${k} => :'${k}'`;
      });
      const r = psql(url, `select public.${name}(${parts.join(", ")})::text;`, vars);
      if (!r.ok) return { data: null, error: { message: r.err } };
      return { data: r.out === "" ? null : JSON.parse(r.out), error: null };
    },
    async getUserId(jwt) { return users[jwt] ?? null; },
    randomBytes: (n) => new Uint8Array(randomBytes(n)),
    // Storage is not available in plain Postgres: the test records which prefixes the handler asked to delete.
    async deleteUserPhotos(userId, knownPaths) { storage.push({ userId, knownPaths }); return failPhotos ? { message: "storage down" } : null; },
    async deleteAuthUser(userId) {
      const r = psql(url, `delete from auth.users where id = :'u'`, { u: userId });   // not-found deletes 0 rows: idempotent
      return r.ok ? null : { message: r.err };
    },
  };
}

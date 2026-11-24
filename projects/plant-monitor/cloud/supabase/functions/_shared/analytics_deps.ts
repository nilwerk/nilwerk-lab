// PostgREST calls of GET /analytics (task 4.B4 slice 3; FR-P01, FR-P04, NFR-06). Split out of supabase.ts so tests can inject a fake client:
// this file has no npm: import and no Deno API. Every call is made through a client built per request from the USER's JWT (never the service key),
// so public.is_premium() and RLS see auth.uid() = the caller.
import type { AnalyticsDeps, ReadingRow } from "./analytics.ts";
import type { AnalyticsPlant } from "../../../analytics/aggregate.ts";

type Res = { data: unknown; error: unknown };
/** The slice of a supabase-js client that analytics uses. The query builder is thenable, like the real one. */
export interface AnalyticsQuery {
  select(cols: string): AnalyticsQuery;
  eq(col: string, v: unknown): AnalyticsQuery;
  gte(col: string, v: unknown): AnalyticsQuery;
  order(col: string, o: { ascending: boolean }): AnalyticsQuery;
  range(from: number, to: number): PromiseLike<Res>;
  then: PromiseLike<Res>["then"];
}
export interface AnalyticsClient {
  auth: { getUser(jwt: string): Promise<{ data: { user: { id: string } | null }; error: unknown }> };
  rpc(name: string): PromiseLike<Res>;
  from(table: string): AnalyticsQuery;
}

export function buildAnalyticsDeps(asUser: (jwt: string) => AnalyticsClient): AnalyticsDeps {
  return {
    async getUserId(jwt) {
      const { data, error } = await asUser(jwt).auth.getUser(jwt);
      return error || !data.user ? null : data.user.id;
    },
    async isPremium(jwt) {
      const { data, error } = await asUser(jwt).rpc("is_premium");
      return error || typeof data !== "boolean" ? null : data;
    },
    async plants(jwt) {
      const { data, error } = await asUser(jwt).from("plants").select("id,name") as unknown as Res;
      return error || !Array.isArray(data) ? null : (data as AnalyticsPlant[]);
    },
    async readingsPage(jwt, sinceIso, offset, limit) {
      const { data, error } = await asUser(jwt).from("readings")
        .select("ts,plant_id,moisture_pct,vbat_mv,plausible")
        .eq("plausible", true).gte("ts", sinceIso)
        .order("ts", { ascending: true }).order("device_id", { ascending: true })   // (ts, device_id) is unique: stable paging
        .range(offset, offset + limit - 1);
      return error || !Array.isArray(data) ? null : (data as ReadingRow[]);
    },
  };
}

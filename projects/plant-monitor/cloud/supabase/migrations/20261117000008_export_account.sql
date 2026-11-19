-- 4.B2c GET /export: the data behind the edge function `export` (FR-A01, NFR-07, NFR-06).
-- No table changes (db-schema.sql stays the contract). service_role ONLY: the edge function calls it after it verified the user JWT itself
-- (auth.getUser); the user id is never taken from the request. Every query filters on owner_id = p_user explicitly: service_role bypasses RLS,
-- so the owner filter IS the isolation here (tested: a second user's rows never appear).
-- Why not the user's own session + RLS: readings/readings_hourly policies hide everything older than 7 days from free users, but the export
-- covers all retained data for free and premium users alike (openapi /export), and tips are premium-gated by policy.
-- Left out on purpose: device_credentials and api_keys (secrets/hashes), push_tokens and claim_tokens (technical, short-lived).
-- Timestamps render as ISO-8601 UTC (function-level timezone UTC). Photo rows carry storage_path; the function turns them into signed URLs.
create or replace function public.export_account(p_user uuid) returns jsonb
language plpgsql stable security definer set search_path = public set timezone = 'UTC' as $$
declare r jsonb;
begin
  if p_user is null then raise exception 'p_user required'; end if;
  select jsonb_build_object(
    'profile',         (select to_jsonb(p) from public.profiles p where p.id = p_user),
    'plants',          coalesce((select jsonb_agg(to_jsonb(x) order by x.created_at, x.id) from public.plants x where x.owner_id = p_user), '[]'),
    'devices',         coalesce((select jsonb_agg(to_jsonb(x) order by x.created_at, x.id) from public.devices x where x.owner_id = p_user), '[]'),
    'readings',        coalesce((select jsonb_agg(to_jsonb(x) order by x.ts, x.device_id) from public.readings x where x.owner_id = p_user), '[]'),
    'readings_hourly', coalesce((select jsonb_agg(to_jsonb(x) order by x.hour, x.device_id) from public.readings_hourly x where x.owner_id = p_user), '[]'),
    'events',          coalesce((select jsonb_agg(to_jsonb(x) order by x.ts, x.id) from public.events x where x.owner_id = p_user), '[]'),
    'alerts',          coalesce((select jsonb_agg(to_jsonb(x) order by x.opened_at, x.id) from public.alerts x where x.owner_id = p_user), '[]'),
    'tips',            coalesce((select jsonb_agg(to_jsonb(x) order by x.generated_at, x.id) from public.tips x where x.owner_id = p_user), '[]'),
    'photo_rows',      coalesce((select jsonb_agg(jsonb_build_object('id', x.id, 'plant_id', x.plant_id, 'taken_at', x.taken_at, 'storage_path', x.storage_path)
                                                  order by x.taken_at, x.id) from public.plant_images x where x.owner_id = p_user), '[]')
  ) into r;
  return r;
end $$;

revoke all on function public.export_account(uuid) from public, anon, authenticated;
grant execute on function public.export_account(uuid) to service_role;

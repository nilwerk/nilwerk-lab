-- 4.B5 MCP server (FR-P03, FR-P01, FR-P02, FR-P04, FR-A06, NFR-06, NFR-07). Read-only RPCs for the MCP edge function.
-- Migration 1 is frozen, so this is a new file. Contract: docs/interfaces/mcp-tools.json; key resolution is
-- public.mcp_resolve_key() in migration 1 (sha256 of the key -> owner, premium gate, revoked keys fail).
--
-- Isolation mechanism (AC 2): the edge function runs with the service role, which bypasses RLS, so RLS cannot
-- protect these reads. Every function therefore takes p_owner (the owner that mcp_resolve_key returned for the
-- key) and filters on owner_id = p_owner in the SQL itself, and filters the plant on the same owner. A plant that
-- is not the caller's gives null (mapped to not_found), the same as an unknown id. Callable by service_role only.
-- No function here writes; the MCP server is read-only (role file rule, FR-P03).

-- ---------------------------------------------------------------- plants: list and single (plant_status view, migration 1)
create or replace function public.mcp_list_plants(p_owner uuid) returns jsonb
language sql stable security definer set search_path = public as $$
  select coalesce(jsonb_agg(to_jsonb(s) - 'owner_id' order by s.name), '[]'::jsonb)
    from public.plant_status s
   where s.owner_id = p_owner and p_owner is not null;
$$;

create or replace function public.mcp_get_plant(p_owner uuid, p_plant uuid) returns jsonb
language sql stable security definer set search_path = public as $$
  select to_jsonb(s) - 'owner_id'
    from public.plant_status s
   where s.owner_id = p_owner and s.plant_id = p_plant and p_owner is not null and p_plant is not null;
$$;

-- ---------------------------------------------------------------- history (FR-P01): raw 15-min samples or roll-ups
-- Returns null when the plant is not the owner's (-> not_found). The window is `p_days` (1..90). The server downsamples
-- so that at most 2000 points come back: the step is the smallest of the candidates that is a multiple of the native
-- resolution (raw 15 min, hourly 60 min, daily 1440 min) and gives <= 2000 points. Raw comes from readings (kept 3 months,
-- NFR-13), hourly/daily from readings_hourly (kept 12 months). Watering events are the device's 'wetting' events in the window.
create or replace function public.mcp_get_history(p_owner uuid, p_plant uuid, p_days int, p_resolution text) returns jsonb
language plpgsql stable security definer set search_path = public as $$
declare
  v_native int; v_step int; v_from timestamptz; v_points jsonb; v_events jsonb;
begin
  if p_owner is null or p_plant is null or p_days is null or p_days < 1 or p_days > 90
     or p_resolution not in ('raw', 'hourly', 'daily') then
    raise exception 'invalid_input' using errcode = '22023';
  end if;
  if not exists (select 1 from public.plants p where p.id = p_plant and p.owner_id = p_owner) then
    return null;                                                     -- not the caller's plant: not_found
  end if;
  v_native := case p_resolution when 'raw' then 15 when 'hourly' then 60 else 1440 end;
  select min(c) into v_step from unnest(array[15, 30, 60, 120, 180, 240, 360, 720, 1440]) as c
   where c >= v_native and (p_days * 1440.0) / c <= 2000;
  if v_step is null then raise exception 'invalid_input' using errcode = '22023'; end if;
  v_from := now() - make_interval(days => p_days);

  if p_resolution = 'raw' then
    select coalesce(jsonb_agg(jsonb_build_object('ts', b.ts, 'moisture_pct', b.m, 'temp_c', b.t,
                                                  'rh_pct', b.h, 'lux', b.l, 'battery_mv', b.v) order by b.ts), '[]'::jsonb)
      into v_points
      from (select date_bin(make_interval(mins => v_step), r.ts, timestamptz '2000-01-01 00:00:00+00') as ts,
                   avg(r.moisture_pct) as m, avg(r.temp_c) as t, avg(r.rh_pct) as h, avg(r.lux) as l,
                   round(avg(r.vbat_mv))::int as v
              from public.readings r
             where r.owner_id = p_owner and r.plant_id = p_plant and r.plausible and r.ts > v_from
             group by 1) b;
  else
    -- mean of the hourly means (equal weight per hour); battery is the lowest hourly minimum in the bucket
    select coalesce(jsonb_agg(jsonb_build_object('ts', b.ts, 'moisture_pct', b.m, 'temp_c', b.t,
                                                  'rh_pct', b.h, 'lux', b.l, 'battery_mv', b.v) order by b.ts), '[]'::jsonb)
      into v_points
      from (select date_bin(make_interval(mins => v_step), h.hour, timestamptz '2000-01-01 00:00:00+00') as ts,
                   avg(h.moisture_avg) as m, avg(h.temp_avg) as t, avg(h.rh_avg) as h, avg(h.lux_avg) as l,
                   min(h.vbat_min_mv) as v
              from public.readings_hourly h
             where h.owner_id = p_owner and h.plant_id = p_plant and h.hour > v_from
             group by 1) b;
  end if;

  select coalesce(jsonb_agg(e.ts order by e.ts), '[]'::jsonb) into v_events
    from public.events e
   where e.owner_id = p_owner and e.plant_id = p_plant and e.type = 'wetting' and e.ts > v_from;

  return jsonb_build_object('plant_id', p_plant, 'resolution', p_resolution,
                            'points', v_points, 'watering_events', v_events);
end $$;

-- ---------------------------------------------------------------- tips (FR-P02, FR-P04): cached tips only, never generated here
-- Null when the plant is not the owner's. Otherwise {plant_id, tip} where tip is the newest unexpired row or null.
-- The edge function re-checks guardrail_version and every item before it returns anything (guardrails, FR-P02).
create or replace function public.mcp_get_tips(p_owner uuid, p_plant uuid) returns jsonb
language plpgsql stable security definer set search_path = public as $$
declare v_tip jsonb;
begin
  if p_owner is null or p_plant is null then raise exception 'invalid_input' using errcode = '22023'; end if;
  if not exists (select 1 from public.plants p where p.id = p_plant and p.owner_id = p_owner) then
    return null;
  end if;
  select jsonb_build_object('generated_at', t.generated_at, 'content', t.content,
                            'guardrail_version', t.guardrail_version)
    into v_tip
    from public.tips t
   where t.owner_id = p_owner and t.plant_id = p_plant and t.expires_at > now()
   order by t.generated_at desc limit 1;
  return jsonb_build_object('plant_id', p_plant, 'tip', v_tip);
end $$;

-- ---------------------------------------------------------------- privileges: service_role only (as mcp_resolve_key)
revoke all on function public.mcp_list_plants(uuid) from public, anon, authenticated;
revoke all on function public.mcp_get_plant(uuid, uuid) from public, anon, authenticated;
revoke all on function public.mcp_get_history(uuid, uuid, int, text) from public, anon, authenticated;
revoke all on function public.mcp_get_tips(uuid, uuid) from public, anon, authenticated;
grant execute on function public.mcp_list_plants(uuid) to service_role;
grant execute on function public.mcp_get_plant(uuid, uuid) to service_role;
grant execute on function public.mcp_get_history(uuid, uuid, int, text) to service_role;
grant execute on function public.mcp_get_tips(uuid, uuid) to service_role;

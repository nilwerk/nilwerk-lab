-- 4.B2 migration 4: SQL side of the device API (docs/interfaces/openapi.yaml: POST /device-claim, POST /ingest).
-- Migration 1 is frozen (merged); this is a NEW migration, as the README rules require. Schema tables are unchanged.
-- The Edge Functions (functions/device-claim, functions/ingest) are thin: they hash tokens, validate the body and call
-- these functions with the service role. All state changes happen here, in ONE transaction per call, so a failed
-- request never leaves a half-written batch (FR-D04: the device resends the whole batch until it gets a 2xx).
-- Tokens: only SHA-256 hashes ever reach the database (ADR-004, NFR-06). Hash input = the token string as UTF-8.
-- Custom SQLSTATEs (mapped to HTTP by the functions): NW401 claim_token_invalid, NW409 device_owned, NW403 device_not_owned.

-- Config pushed to the device with every response (openapi DeviceConfig; G1 defaults 25 / 85 / 3400 mV, FR-D06).
create or replace function public.device_config(p_device uuid) returns jsonb
language sql stable security definer set search_path = public as $$
  select jsonb_build_object(
    'sample_interval_s', 900,                                   -- 15 min (FR-D04 unit of record)
    'report_interval_s', 3600,                                  -- FR-D02
    'dry_pct', coalesce(p.dry_threshold_pct, 25),
    'wet_pct', coalesce(p.wet_threshold_pct, 85),
    'low_battery_mv', d.low_battery_mv)
  from public.devices d left join public.plants p on p.id = d.plant_id
  where d.id = p_device
$$;

-- Token check for /ingest (FR-D03, NFR-06, ADR-004). 'ok' | 'revoked' (released/rotated away, openapi 401 token_revoked)
-- | 'invalid' (unknown hash). Lookup is by the unique hash, so no secret is compared in application code.
create or replace function public.authenticate_device(p_token_hash bytea) returns table (device_id uuid, status text)
language sql stable security definer set search_path = public as $$
  select c.device_id,
         case when c.revoked_at is not null or d.owner_id is null then 'revoked' else 'ok' end
    from public.device_credentials c join public.devices d on d.id = c.device_id
   where c.token_hash = p_token_hash
  union all
  select null::uuid, 'invalid' where not exists (select 1 from public.device_credentials where token_hash = p_token_hash)
$$;

-- POST /device-claim (FR-D03, FR-A03, FR-A08, NFR-06). Rules are the ones in openapi.yaml.
create or replace function public.claim_device(p_hw_id text, p_claim_hash bytea, p_name text, p_fw text, p_token_hash bytea)
returns jsonb language plpgsql security definer set search_path = public as $$
declare ct public.claim_tokens; d public.devices;
begin
  select * into ct from public.claim_tokens where token_hash = p_claim_hash for update;
  if not found or ct.used_at is not null or ct.expires_at <= now() then
    raise exception 'claim_token_invalid' using errcode = 'NW401';
  end if;
  select * into d from public.devices where hw_id = p_hw_id for update;
  if not found then
    insert into public.devices (hw_id, owner_id, name, claimed_at, last_seen_at, fw_version)
    values (p_hw_id, ct.user_id, p_name, now(), now(), p_fw) returning * into d;
  elsif d.owner_id is not null and d.owner_id <> ct.user_id then
    raise exception 'device_owned' using errcode = 'NW409';                      -- owner must release first (FR-A08)
  else
    -- unowned (released) or same owner (factory reset, FR-D07): (re)claim. A new owner never inherits the old plant link.
    update public.devices set owner_id = ct.user_id, claimed_at = now(), last_seen_at = now(), fw_version = p_fw,
           name = coalesce(p_name, name), plant_id = case when d.owner_id = ct.user_id then plant_id else null end
     where id = d.id returning * into d;
  end if;
  -- one credential row per device: insert or rotate (old token stops working at once)
  insert into public.device_credentials (device_id, token_hash) values (d.id, p_token_hash)
  on conflict (device_id) do update set token_hash = excluded.token_hash, created_at = now(), revoked_at = null;
  update public.claim_tokens set used_at = now(), device_id = d.id where token_hash = p_claim_hash;
  return jsonb_build_object('device_id', d.id, 'server_time', extract(epoch from now())::bigint, 'config', public.device_config(d.id));
end $$;

-- POST /ingest (FR-D01, FR-D02, FR-D04, FR-D06, FR-E01, FR-E03, FR-A07, NFR-04). Body already schema-validated by the function.
-- Idempotent on (device_id, ts) (FR-D04): replays count as duplicates. Out-of-range samples are STORED with plausible=false
-- (FR-D01, device-report.schema.json): one bad value never loses the batch; alerts/charts ignore them.
-- Clock skew: if |received_at - sent_at| > 120 s every ts is shifted by the skew (device-report.schema.json, sent_at).
create or replace function public.ingest_report(p_device uuid, p_report jsonb, p_received timestamptz default now())
returns jsonb language plpgsql security definer set search_path = public as $$
declare
  d public.devices; v_skew interval; v_total int; v_acc int; v_imp int; v_fw jsonb; v_model jsonb;
begin
  select * into d from public.devices where id = p_device for update;
  if not found or d.owner_id is null then raise exception 'device_not_owned' using errcode = 'NW403'; end if;
  v_skew := p_received - to_timestamp((p_report->>'sent_at')::bigint);
  v_skew := make_interval(secs => round(extract(epoch from v_skew)));              -- whole seconds: sent_at is an integer
  if abs(extract(epoch from v_skew)) <= 120 then v_skew := interval '0'; end if;

  select jsonb_array_length(p_report->'samples') into v_total;
  with s as (
    select to_timestamp((x->>'ts')::bigint) + v_skew as ts,
           (x->>'moisture_pct')::real as moisture_pct, (x->>'moisture_raw')::int as moisture_raw,
           (x->>'temp_c')::real as temp_c, (x->>'rh_pct')::real as rh_pct, (x->>'lux')::real as lux, (x->>'vbat_mv')::int as vbat_mv
      from jsonb_array_elements(p_report->'samples') x
  ), ins as (
    insert into public.readings (device_id, ts, owner_id, plant_id, moisture_pct, moisture_raw, temp_c, rh_pct, lux, vbat_mv, plausible, received_at)
    select p_device, s.ts, d.owner_id, d.plant_id, s.moisture_pct, s.moisture_raw, s.temp_c, s.rh_pct, s.lux, s.vbat_mv,
           public.reading_is_plausible(s.temp_c, s.rh_pct, s.lux, s.vbat_mv, s.moisture_pct), p_received
      from s
    on conflict (device_id, ts) do nothing                                        -- idempotency key (FR-D04)
    returning plausible)
  select count(*), count(*) filter (where not plausible) into v_acc, v_imp from ins;

  insert into public.events (device_id, owner_id, plant_id, ts, type, critical, received_at)
  select p_device, d.owner_id, d.plant_id, to_timestamp((e->>'ts')::bigint) + v_skew, e->>'type',
         (e->>'type') in ('wetting_unexpected', 'waterlogged', 'sensor_out_of_soil', 'sensor_fault'),   -- FR-E03, FR-A07
         p_received
    from jsonb_array_elements(coalesce(p_report->'events', '[]'::jsonb)) e
  on conflict (device_id, ts, type) do nothing;

  update public.devices set
    last_seen_at = p_received, fw_version = p_report->>'fw',
    model_version = coalesce(p_report->>'model', model_version),
    forecast_h  = case when p_report ? 'forecast_h' then (p_report->>'forecast_h')::numeric else forecast_h end,
    forecast_at = case when p_report ? 'forecast_h' then p_received else forecast_at end,
    cal_dry_raw = coalesce((p_report#>>'{cal,dry_raw}')::int, cal_dry_raw),
    cal_wet_raw = coalesce((p_report#>>'{cal,wet_raw}')::int, cal_wet_raw),
    cal_at      = case when p_report ? 'cal' then p_received else cal_at end
   where id = p_device;

  perform public.evaluate_alerts(p_device, p_received);                          -- FR-A07, FR-D06 (via existing 2.4 function)

  select to_jsonb(r) into v_fw from (select f.version, f.storage_path, f.sha256, f.size_bytes, f.min_battery_mv
    from public.firmware_releases f where f.kind = 'fw' and f.version = d.fw_target and d.fw_target is distinct from p_report->>'fw') r;
  select to_jsonb(r) into v_model from (select f.version, f.storage_path, f.sha256, f.size_bytes, f.min_battery_mv
    from public.firmware_releases f where f.kind = 'model' and f.version = d.model_target and d.model_target is distinct from p_report->>'model') r;

  return jsonb_build_object('server_time', extract(epoch from p_received)::bigint, 'accepted', v_acc,
    'duplicates', v_total - v_acc, 'implausible', v_imp, 'config', public.device_config(p_device),
    'fw_target', v_fw, 'model_target', v_model);       -- artefact rows; the function turns storage_path into a signed URL (FR-D05)
end $$;

revoke all on function public.device_config(uuid) from public, anon, authenticated;
revoke all on function public.authenticate_device(bytea) from public, anon, authenticated;
revoke all on function public.claim_device(text, bytea, text, text, bytea) from public, anon, authenticated;
revoke all on function public.ingest_report(uuid, jsonb, timestamptz) from public, anon, authenticated;
grant execute on function public.device_config(uuid), public.authenticate_device(bytea),
  public.claim_device(text, bytea, text, text, bytea), public.ingest_report(uuid, jsonb, timestamptz) to service_role;

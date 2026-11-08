-- 4.B2 device claim + ingest API: server-side logic behind the edge functions (docs/interfaces/openapi.yaml).
-- No table changes (db-schema.sql stays the contract). Functions are callable by service_role ONLY (the edge functions
-- use SUPABASE_SECRET_KEY); anon/authenticated cannot call them (NFR-06). Plain tokens never reach the database:
-- the edge function sends SHA-256 hex digests (ADR-004). Requirements: FR-D01, FR-D02, FR-D03, FR-D04, FR-A02, FR-A03,
-- FR-A07, FR-E03, NFR-04, NFR-06.

-- ------------------------------------------------------------------ POST /claim-token (FR-D03, FR-A03, FR-A02)
-- At most 10 open (unused, unexpired) tokens per user; no cap on devices per user (FR-A02).
create or replace function public.issue_claim_token(p_user uuid, p_token_hash text) returns jsonb
language plpgsql security definer set search_path = public as $$
declare v_exp timestamptz := now() + interval '15 minutes';
begin
  if (select count(*) from public.claim_tokens where user_id = p_user and used_at is null and expires_at > now()) >= 10 then
    return jsonb_build_object('error', 'rate_limited');
  end if;
  insert into public.claim_tokens(token_hash, user_id, expires_at) values (decode(p_token_hash, 'hex'), p_user, v_exp);
  return jsonb_build_object('expires_at', v_exp);
end $$;

-- Per-device config pushed with every response (architecture D-5; G1 defaults 25 / 85 / 900 s / 3600 s / 3400 mV).
create or replace function public.device_config(p_device uuid) returns jsonb
language sql stable security definer set search_path = public as $$
  select jsonb_build_object('sample_interval_s', 900, 'report_interval_s', 3600,
           'dry_pct', coalesce(pl.dry_threshold_pct, 25), 'wet_pct', coalesce(pl.wet_threshold_pct, 85), 'low_battery_mv', d.low_battery_mv)
  from public.devices d left join public.plants pl on pl.id = d.plant_id where d.id = p_device
$$;

-- ------------------------------------------------------------------ POST /device-claim (FR-D03, FR-A03, FR-A08, NFR-06)
-- p_claim_hash / p_token_hash: lower-case hex SHA-256. The new device token hash replaces any old credential (rotation / re-claim).
create or replace function public.device_claim(p_claim_hash text, p_token_hash text, p_hw_id text, p_name text, p_fw text) returns jsonb
language plpgsql security definer set search_path = public as $$
declare ct public.claim_tokens; d public.devices;
begin
  select * into ct from public.claim_tokens where token_hash = decode(p_claim_hash, 'hex') for update;
  if not found or ct.used_at is not null or ct.expires_at <= now() then
    return jsonb_build_object('error', 'claim_token_invalid');
  end if;
  select * into d from public.devices where hw_id = p_hw_id for update;
  if found and d.owner_id is not null and d.owner_id <> ct.user_id then
    return jsonb_build_object('error', 'device_owned');          -- token stays unused
  end if;
  if not found then
    insert into public.devices(hw_id, owner_id, name, claimed_at, fw_version)
      values (p_hw_id, ct.user_id, p_name, now(), p_fw) returning * into d;
  else
    update public.devices set owner_id = ct.user_id, claimed_at = now(), name = coalesce(p_name, name), fw_version = p_fw,
           plant_id = case when d.owner_id = ct.user_id then plant_id else null end   -- a new owner never inherits the old plant link
      where id = d.id returning * into d;
  end if;
  insert into public.device_credentials(device_id, token_hash) values (d.id, decode(p_token_hash, 'hex'))
    on conflict (device_id) do update set token_hash = excluded.token_hash, created_at = now(), revoked_at = null;
  update public.claim_tokens set used_at = now(), device_id = d.id where token_hash = ct.token_hash;
  return jsonb_build_object('device_id', d.id, 'server_time', extract(epoch from now())::bigint, 'config', public.device_config(d.id));
end $$;

-- ------------------------------------------------------------------ POST /ingest (FR-D01, FR-D02, FR-D04, FR-A07, FR-E03, NFR-04)
-- Authenticates by token hash; the device is ALWAYS the one owning the token, never named by the caller, so one device cannot
-- write another's rows (NFR-06). Idempotent on (device_id, ts) (FR-D04). Shifts ts by the clock skew if |skew| > 120 s.
-- Stores the latest forecast (FR-E01) and calibration; evaluate_alerts() turns low battery (FR-D06) and critical events into alerts.
-- FR-D05 (OTA manifest) is NOT built here: fw_target / model_target are returned as null.
create or replace function public.ingest_batch(p_token_hash text, p_report jsonb, p_received_at timestamptz default now()) returns jsonb
language plpgsql security definer set search_path = public as $$
declare
  c public.device_credentials; d public.devices;
  v_skew bigint; v_total int; v_acc int; v_imp int;
begin
  select * into c from public.device_credentials where token_hash = decode(p_token_hash, 'hex');
  if not found then return jsonb_build_object('error', 'token_invalid'); end if;
  select * into d from public.devices where id = c.device_id for update;
  if c.revoked_at is not null or d.owner_id is null then return jsonb_build_object('error', 'token_revoked'); end if;

  v_skew := extract(epoch from p_received_at)::bigint - (p_report->>'sent_at')::bigint;
  if abs(v_skew) <= 120 then v_skew := 0; end if;
  v_total := jsonb_array_length(p_report->'samples');

  with s as (
    select to_timestamp((x->>'ts')::bigint + v_skew) ts,
           (x->>'moisture_pct')::real m, (x->>'moisture_raw')::int mr, (x->>'temp_c')::real t,
           (x->>'rh_pct')::real rh, (x->>'lux')::real lx, (x->>'vbat_mv')::int vb
    from jsonb_array_elements(p_report->'samples') x
  ), ins as (
    insert into public.readings(device_id, ts, owner_id, plant_id, moisture_pct, moisture_raw, temp_c, rh_pct, lux, vbat_mv, plausible, received_at)
    select d.id, ts, d.owner_id, d.plant_id, m, mr, t, rh, lx, vb, public.reading_is_plausible(t, rh, lx, vb, m), p_received_at from s
    on conflict (device_id, ts) do nothing
    returning plausible
  ) select count(*), count(*) filter (where not plausible) into v_acc, v_imp from ins;

  insert into public.events(device_id, owner_id, plant_id, ts, type, critical, received_at)
  select d.id, d.owner_id, d.plant_id, to_timestamp((e->>'ts')::bigint + v_skew), e->>'type',
         (e->>'type') in ('wetting_unexpected', 'waterlogged', 'sensor_out_of_soil', 'sensor_fault'), p_received_at
  from jsonb_array_elements(coalesce(p_report->'events', '[]'::jsonb)) e
  on conflict (device_id, ts, type) do nothing;

  update public.devices set last_seen_at = p_received_at, fw_version = p_report->>'fw',
    model_version = coalesce(p_report->>'model', model_version),
    forecast_h = case when p_report ? 'forecast_h' then (p_report->>'forecast_h')::numeric(5,1) else forecast_h end,
    forecast_at = case when p_report ? 'forecast_h' then p_received_at else forecast_at end,
    cal_dry_raw = coalesce((p_report#>>'{cal,dry_raw}')::int, cal_dry_raw),
    cal_wet_raw = coalesce((p_report#>>'{cal,wet_raw}')::int, cal_wet_raw),
    cal_at = case when p_report ? 'cal' then coalesce(to_timestamp((p_report#>>'{cal,at}')::bigint), p_received_at) else cal_at end
  where id = d.id;

  perform public.evaluate_alerts(d.id, p_received_at);
  return jsonb_build_object('server_time', extract(epoch from p_received_at)::bigint, 'accepted', v_acc,
    'duplicates', v_total - v_acc, 'implausible', v_imp, 'config', public.device_config(d.id),
    'fw_target', null, 'model_target', null);      -- OTA manifest (FR-D05) is a later task
end $$;

do $$ declare f text; begin
  foreach f in array array['issue_claim_token(uuid,text)', 'device_config(uuid)', 'device_claim(text,text,text,text,text)',
                           'ingest_batch(text,jsonb,timestamptz)'] loop
    execute format('revoke all on function public.%s from public, anon, authenticated', f);
    execute format('grant execute on function public.%s to service_role', f);
  end loop;
end $$;

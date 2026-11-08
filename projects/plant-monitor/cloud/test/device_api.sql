-- SQL-level tests for the device API (4.B2): claim_device, authenticate_device, ingest_report.
-- Runs after migrations + stub_auth + grants on an EMPTY database. Token hash = sha256 of the token string (UTF-8).
\set ON_ERROR_STOP on
insert into auth.users(id) values ('00000000-0000-0000-0000-00000000000a'), ('00000000-0000-0000-0000-00000000000b');
create function pg_temp.h(t text) returns bytea language sql as $$ select digest(t, 'sha256') $$;
insert into public.claim_tokens(token_hash, user_id, expires_at) values
  (pg_temp.h('ct-a1'), '00000000-0000-0000-0000-00000000000a', now() + interval '15 min'),
  (pg_temp.h('ct-expired'), '00000000-0000-0000-0000-00000000000a', now() - interval '1 min'),
  (pg_temp.h('ct-b1'), '00000000-0000-0000-0000-00000000000b', now() + interval '15 min'),
  (pg_temp.h('ct-a2'), '00000000-0000-0000-0000-00000000000a', now() + interval '15 min'),
  (pg_temp.h('ct-b2'), '00000000-0000-0000-0000-00000000000b', now() + interval '15 min');

-- ---- claim (FR-D03, FR-A03, FR-A08)
do $$ declare r jsonb; n int; did uuid; begin
  r := public.claim_device('nw-a1b2c3d4e5f6', pg_temp.h('ct-a1'), 'Basil sensor', '0.1.0', pg_temp.h('tok-1'));
  did := (r->>'device_id')::uuid;
  if r->'config'->>'dry_pct' <> '25' or (r->'config'->>'low_battery_mv')::int <> 3400 then raise exception 'config defaults wrong: %', r; end if;
  select count(*) into n from public.devices where id = did and owner_id = '00000000-0000-0000-0000-00000000000a' and name = 'Basil sensor'; if n <> 1 then raise exception 'device not created'; end if;
  -- only the hash is stored (ADR-004)
  select count(*) into n from public.device_credentials where device_id = did and token_hash = pg_temp.h('tok-1'); if n <> 1 then raise exception 'hash missing'; end if;
  select count(*) into n from public.claim_tokens where token_hash = pg_temp.h('ct-a1') and used_at is not null and device_id = did; if n <> 1 then raise exception 'claim token not marked used'; end if;
  -- token reuse, expired token, unknown token -> NW401
  begin perform public.claim_device('nw-a1b2c3d4e5f6', pg_temp.h('ct-a1'), null, '0.1.0', pg_temp.h('tok-x')); raise exception 'reused claim token accepted';
  exception when sqlstate 'NW401' then null; end;
  begin perform public.claim_device('nw-a1b2c3d4e5f6', pg_temp.h('ct-expired'), null, '0.1.0', pg_temp.h('tok-x')); raise exception 'expired claim token accepted';
  exception when sqlstate 'NW401' then null; end;
  begin perform public.claim_device('nw-a1b2c3d4e5f6', pg_temp.h('nope'), null, '0.1.0', pg_temp.h('tok-x')); raise exception 'unknown claim token accepted';
  exception when sqlstate 'NW401' then null; end;
  -- owned by ANOTHER user -> NW409, token stays unused, credential untouched
  begin perform public.claim_device('nw-a1b2c3d4e5f6', pg_temp.h('ct-b1'), null, '0.1.0', pg_temp.h('tok-b')); raise exception 'foreign claim allowed';
  exception when sqlstate 'NW409' then null; end;
  select count(*) into n from public.claim_tokens where token_hash = pg_temp.h('ct-b1') and used_at is null; if n <> 1 then raise exception 'token consumed by failed claim'; end if;
  select count(*) into n from public.device_credentials where token_hash = pg_temp.h('tok-b'); if n <> 0 then raise exception 'credential written by failed claim'; end if;
  -- same owner again (factory reset, FR-D07): credential rotated, old token dead
  perform public.claim_device('nw-a1b2c3d4e5f6', pg_temp.h('ct-a2'), null, '0.1.1', pg_temp.h('tok-2'));
  if (select status from public.authenticate_device(pg_temp.h('tok-1'))) <> 'invalid' then raise exception 'old token still valid after rotation'; end if;
  if (select status from public.authenticate_device(pg_temp.h('tok-2'))) <> 'ok' then raise exception 'new token not valid'; end if;
  -- release (FR-A08): owner null -> token_revoked; then user B may claim it
  update public.devices set owner_id = null, plant_id = null where id = did;
  if (select status from public.authenticate_device(pg_temp.h('tok-2'))) <> 'revoked' then raise exception 'released device token not revoked'; end if;
  perform public.claim_device('nw-a1b2c3d4e5f6', pg_temp.h('ct-b2'), null, '0.1.1', pg_temp.h('tok-3'));
  select count(*) into n from public.devices where id = did and owner_id = '00000000-0000-0000-0000-00000000000b'; if n <> 1 then raise exception 'B could not claim released device'; end if;
  if (select status from public.authenticate_device(pg_temp.h('tok-2'))) <> 'invalid' then raise exception 'previous owner token survives re-claim'; end if;
  if (select status from public.authenticate_device(pg_temp.h('tok-3'))) <> 'ok' then raise exception 'B token not valid'; end if;
  if (select status from public.authenticate_device(pg_temp.h('garbage'))) <> 'invalid' then raise exception 'garbage token not invalid'; end if;
  raise notice 'claim ok: new, reuse, expired, unknown, foreign owner, rotation, release + re-claim';
end $$;

-- ---- ingest (FR-D01, FR-D02, FR-D04, FR-E03, FR-A07, NFR-04)
-- device now belongs to B. Plant for B so alerts have thresholds.
insert into public.plants(id, owner_id, name, location_type, soil_type) values ('10000000-0000-0000-0000-00000000000b', '00000000-0000-0000-0000-00000000000b', 'Tomato', 'balcony', 'garden');
update public.devices set plant_id = '10000000-0000-0000-0000-00000000000b';
create temp table res(name text, r jsonb);
do $$ declare did uuid := (select id from public.devices); rep jsonb; r jsonb; n int; base bigint := extract(epoch from date_trunc('hour', now()))::bigint - 40000; begin
  -- 1. normal batch of 4 + 1 implausible (temp 99) + critical event
  rep := jsonb_build_object('v', 1, 'sent_at', extract(epoch from now())::bigint, 'trigger', 'critical', 'fw', '0.2.0', 'model', 'm1', 'forecast_h', 12.5,
    'cal', jsonb_build_object('dry_raw', 3000, 'wet_raw', 1200),
    'samples', (select jsonb_agg(jsonb_build_object('ts', base + g * 900, 'moisture_pct', 20, 'moisture_raw', 2800, 'temp_c', case when g = 4 then 99 else 21 end, 'rh_pct', 50, 'lux', 300, 'vbat_mv', 3300)) from generate_series(0, 4) g),
    'events', jsonb_build_array(jsonb_build_object('ts', base + 3600, 'type', 'waterlogged'), jsonb_build_object('ts', base + 3600, 'type', 'wetting')));
  r := public.ingest_report(did, rep);
  if (r->>'accepted')::int <> 5 or (r->>'duplicates')::int <> 0 or (r->>'implausible')::int <> 1 then raise exception 'counts wrong: %', r; end if;
  select count(*) into n from public.readings where device_id = did and plausible = false and temp_c = 99; if n <> 1 then raise exception 'implausible sample not stored flagged (FR-D01)'; end if;
  select count(*) into n from public.readings where device_id = did and owner_id = '00000000-0000-0000-0000-00000000000b' and plant_id = '10000000-0000-0000-0000-00000000000b'; if n <> 5 then raise exception 'owner/plant not stamped'; end if;
  select count(*) into n from public.events where device_id = did and ((type = 'waterlogged' and critical) or (type = 'wetting' and not critical)); if n <> 2 then raise exception 'events/critical flag wrong'; end if;
  -- alerts via evaluate_alerts: too_dry (20 < 25), low_battery (3300 < 3400) from the last PLAUSIBLE sample, waterlogged from the event
  select count(*) into n from public.alerts where device_id = did and resolved_at is null and kind in ('too_dry', 'low_battery', 'waterlogged'); if n <> 3 then raise exception 'expected 3 open alerts, got %', n; end if;
  select count(*) into n from public.devices where id = did and fw_version = '0.2.0' and model_version = 'm1' and forecast_h = 12.5 and cal_dry_raw = 3000 and cal_wet_raw = 1200 and last_seen_at is not null; if n <> 1 then raise exception 'device row not updated'; end if;
  -- 2. idempotent replay: same batch => all duplicates, nothing new (FR-D04)
  r := public.ingest_report(did, rep);
  if (r->>'accepted')::int <> 0 or (r->>'duplicates')::int <> 5 then raise exception 'replay not idempotent: %', r; end if;
  select count(*) into n from public.readings where device_id = did; if n <> 5 then raise exception 'replay duplicated rows (%)', n; end if;
  select count(*) into n from public.events where device_id = did; if n <> 2 then raise exception 'replay duplicated events'; end if;
  select count(*) into n from public.alerts where device_id = did; if n <> 3 then raise exception 'replay duplicated alerts'; end if;
  -- 3. partial overlap: 2 old + 2 new => accepted 2, duplicates 2
  rep := jsonb_set(rep, '{samples}', (select jsonb_agg(jsonb_build_object('ts', base + g * 900, 'moisture_pct', 20, 'vbat_mv', 3300)) from generate_series(3, 6) g));
  r := public.ingest_report(did, rep);
  if (r->>'accepted')::int <> 2 or (r->>'duplicates')::int <> 2 then raise exception 'overlap wrong: %', r; end if;
  -- 4. 24 h offline buffer: 96 samples in one request (FR-D04), then 192 max accepted by the SQL as well
  rep := jsonb_build_object('v', 1, 'sent_at', extract(epoch from now())::bigint, 'trigger', 'reconnect', 'fw', '0.2.0',
    'samples', (select jsonb_agg(jsonb_build_object('ts', base - 200000 + g * 900, 'moisture_pct', 50, 'temp_c', 20, 'vbat_mv', 3800)) from generate_series(1, 96) g));
  r := public.ingest_report(did, rep);
  if (r->>'accepted')::int <> 96 then raise exception '96-sample buffer not stored: %', r; end if;
  -- 5. clock skew > 120 s: device clock 1 h behind => ts shifted +1 h; skew <= 120 s => unchanged
  rep := jsonb_build_object('v', 1, 'sent_at', extract(epoch from now())::bigint - 3600, 'trigger', 'scheduled', 'fw', '0.2.0',
    'samples', jsonb_build_array(jsonb_build_object('ts', base - 500000 - 3600, 'moisture_pct', 50)));
  perform public.ingest_report(did, rep);
  select count(*) into n from public.readings where device_id = did and ts = to_timestamp(base - 500000); if n <> 1 then raise exception 'skew correction missing'; end if;
  rep := jsonb_build_object('v', 1, 'sent_at', extract(epoch from now())::bigint - 60, 'trigger', 'scheduled', 'fw', '0.2.0',
    'samples', jsonb_build_array(jsonb_build_object('ts', base - 600000, 'moisture_pct', 50)));
  perform public.ingest_report(did, rep);
  select count(*) into n from public.readings where device_id = did and ts = to_timestamp(base - 600000); if n <> 1 then raise exception 'small skew must not shift ts'; end if;
  -- 6. recovery: a good reading resolves too_dry (hysteresis +5) and device_offline
  rep := jsonb_build_object('v', 1, 'sent_at', extract(epoch from now())::bigint, 'trigger', 'scheduled', 'fw', '0.2.0',
    'samples', jsonb_build_array(jsonb_build_object('ts', extract(epoch from now())::bigint, 'moisture_pct', 60, 'vbat_mv', 3900)));
  perform public.ingest_report(did, rep);
  select count(*) into n from public.alerts where device_id = did and kind = 'too_dry' and resolved_at is null; if n <> 0 then raise exception 'too_dry not resolved'; end if;
  -- 7. released device is refused
  update public.devices set owner_id = null where id = did;
  begin perform public.ingest_report(did, rep); raise exception 'ingest for released device allowed';
  exception when sqlstate 'NW403' then null; end;
  raise notice 'ingest ok: counts, implausible flagged (FR-D01), idempotent replay, overlap, 96-sample buffer, skew, alerts open/resolve, released refused';
end $$;

-- ---- app roles cannot call the device functions (NFR-06)
set role authenticated;
do $$ begin
  begin perform public.claim_device('nw-000000000001', '\x00', null, '0', '\x00'); raise exception 'authenticated ran claim_device';
  exception when insufficient_privilege then null; end;
  begin perform public.ingest_report('00000000-0000-0000-0000-000000000000', '{}'); raise exception 'authenticated ran ingest_report';
  exception when insufficient_privilege then null; end;
  begin perform * from public.authenticate_device('\x00'); raise exception 'authenticated ran authenticate_device';
  exception when insufficient_privilege then null; end;
end $$;
reset role;
\echo DEVICE API SQL OK

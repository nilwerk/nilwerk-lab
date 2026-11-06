-- Smoke test for db-schema.sql (task 2.4). Run on a scratch PostgreSQL 15+ AFTER db-schema.sql, with a
-- stub `auth` schema (auth.users, auth.uid() reading setting 'request.uid') and roles anon, authenticated,
-- service_role. Supabase grants table access to these roles by default; the prelude mimics that.
-- Each check raises an exception on failure; the script ends with 'ALL OK'.
\set ON_ERROR_STOP on
do $$ declare t text; begin
  for t in select tablename from pg_tables where schemaname='public' loop
    if t <> 'api_keys' then execute format('grant all on public.%I to authenticated, service_role', t); end if;
  end loop;
  grant usage on schema public to anon, authenticated, service_role;
  grant select on public.plant_status to authenticated;
  grant select (id, owner_id, name, prefix, created_at, last_used_at, revoked_at) on public.api_keys to authenticated;
  grant all on public.api_keys to service_role;
end $$;

-- every public table has RLS enabled (NFR-06)
do $$ declare t text; begin
  for t in select c.relname from pg_class c join pg_namespace n on n.oid=c.relnamespace
           where n.nspname='public' and c.relkind='r' and not c.relrowsecurity loop
    raise exception 'RLS missing on %', t; end loop; end $$;

insert into auth.users(id) values ('00000000-0000-0000-0000-00000000000a'),('00000000-0000-0000-0000-00000000000b');
insert into public.plants(id,owner_id,name,location_type,soil_type) values
  ('10000000-0000-0000-0000-00000000000a','00000000-0000-0000-0000-00000000000a','Basil','house','potting');
insert into public.devices(id,hw_id,owner_id,plant_id,claimed_at,last_seen_at) values
  ('20000000-0000-0000-0000-00000000000a','nw-a1b2c3d4e5f6','00000000-0000-0000-0000-00000000000a','10000000-0000-0000-0000-00000000000a',now(), now() - interval '4 hours');
insert into public.readings(device_id,ts,owner_id,plant_id,moisture_pct,vbat_mv)
select '20000000-0000-0000-0000-00000000000a', now() - (g || ' days')::interval, '00000000-0000-0000-0000-00000000000a',
       '10000000-0000-0000-0000-00000000000a', 20, 3300 from generate_series(0,30) g;

-- idempotent ingest: same (device, ts) twice is a no-op with ON CONFLICT DO NOTHING (FR-D04)
insert into public.readings(device_id,ts,owner_id,moisture_pct)
select device_id, ts, owner_id, 1 from public.readings limit 1 on conflict do nothing;

-- user A: sees own, free = 7 days only (FR-A06 vs FR-P01)
set role authenticated; set request.uid = '00000000-0000-0000-0000-00000000000a';
do $$ declare n int; begin
  select count(*) into n from public.readings; if n <> 7 then raise exception 'free user expected 7 rows, got %', n; end if;
  select count(*) into n from public.plants; if n <> 1 then raise exception 'plants own'; end if;
end $$;
-- user A cannot grant premium (FR-P04)
do $$ begin
  begin update public.profiles set is_premium = true where id = auth.uid();
        raise exception 'premium self-grant allowed';
  exception when insufficient_privilege then null; end;
end $$;
-- user A cannot move a device to someone else or change server-managed columns
do $$ begin
  begin update public.devices set owner_id = '00000000-0000-0000-0000-00000000000b';
        raise exception 'owner change allowed';
  exception when insufficient_privilege then null; end;
end $$;
-- user B sees nothing of A (NFR-06)
set request.uid = '00000000-0000-0000-0000-00000000000b';
do $$ declare n int; begin
  select count(*) into n from public.readings; if n <> 0 then raise exception 'B sees A readings'; end if;
  select count(*) into n from public.plants;   if n <> 0 then raise exception 'B sees A plants'; end if;
  select count(*) into n from public.devices;  if n <> 0 then raise exception 'B sees A devices'; end if;
  select count(*) into n from public.device_credentials; -- RLS without policy => 0 rows, no error
  if n <> 0 then raise exception 'credentials visible'; end if;
end $$;
-- api_keys: key_hash column is not selectable by users
set request.uid = '00000000-0000-0000-0000-00000000000a';
do $$ begin
  begin perform key_hash from public.api_keys; raise exception 'key_hash readable';
  exception when insufficient_privilege then null; end;
end $$;
reset role;

-- premium via service side: A now sees 31 days (FR-P01)
update public.profiles set is_premium = true where id = '00000000-0000-0000-0000-00000000000a';
set role authenticated; set request.uid = '00000000-0000-0000-0000-00000000000a';
do $$ declare n int; begin select count(*) into n from public.readings; if n <> 31 then raise exception 'premium expected 31, got %', n; end if; end $$;
reset role;

-- alerts: too_dry + low_battery open once (dedupe), offline opens at 3 h 10 min, clears on report (FR-A07, G1)
select public.evaluate_alerts('20000000-0000-0000-0000-00000000000a', now() - interval '1 minute');
select public.evaluate_alerts('20000000-0000-0000-0000-00000000000a', now() - interval '1 minute');
do $$ declare n int; begin
  select count(*) into n from public.alerts where resolved_at is null and kind in ('too_dry','low_battery');
  if n <> 2 then raise exception 'expected 2 open alerts, got %', n; end if; end $$;
select public.scan_offline();
select public.scan_offline();
do $$ declare n int; begin
  select count(*) into n from public.alerts where kind='device_offline' and resolved_at is null;
  if n <> 1 then raise exception 'offline alert expected once, got %', n; end if; end $$;
update public.devices set last_seen_at = now();
select public.evaluate_alerts('20000000-0000-0000-0000-00000000000a', now());
do $$ declare n int; begin
  select count(*) into n from public.alerts where kind='device_offline' and resolved_at is null;
  if n <> 0 then raise exception 'offline alert not resolved'; end if; end $$;

-- offline boundary (G1: 3 missed reports = 3 h + 10 min grace): 3 h 05 min -> no alert, 3 h 15 min -> alert
update public.devices set last_seen_at = now() - interval '2 hours 50 minutes';
select public.scan_offline();
do $$ declare n int; begin
  select count(*) into n from public.alerts where kind='device_offline' and resolved_at is null;
  if n <> 0 then raise exception 'offline alert at 2 h 50 min (too early), got %', n; end if; end $$;
update public.devices set last_seen_at = now() - interval '3 hours 5 minutes';
select public.scan_offline();
do $$ declare n int; begin
  select count(*) into n from public.alerts where kind='device_offline' and resolved_at is null;
  if n <> 0 then raise exception 'offline alert at 3 h 05 min (inside grace), got %', n; end if; end $$;
update public.devices set last_seen_at = now() - interval '3 hours 15 minutes';
select public.scan_offline();
do $$ declare n int; begin
  select count(*) into n from public.alerts where kind='device_offline' and resolved_at is null;
  if n <> 1 then raise exception 'no offline alert at 3 h 15 min, got %', n; end if; end $$;
update public.devices set last_seen_at = now();
select public.evaluate_alerts('20000000-0000-0000-0000-00000000000a', now());

-- low-battery hysteresis (G1 3.4 V, resolve at +100 mV [proposed]): 3399 opens, 3450 stays open, 3500 resolves
update public.alerts set resolved_at = now() where kind='low_battery' and resolved_at is null;
insert into public.readings(device_id,ts,owner_id,vbat_mv) values
 ('20000000-0000-0000-0000-00000000000a', now() + interval '1 second','00000000-0000-0000-0000-00000000000a', 3399);
select public.evaluate_alerts('20000000-0000-0000-0000-00000000000a', now());
do $$ declare n int; begin
  select count(*) into n from public.alerts where kind='low_battery' and resolved_at is null;
  if n <> 1 then raise exception 'low_battery not opened at 3399 mV, got %', n; end if; end $$;
insert into public.readings(device_id,ts,owner_id,vbat_mv) values
 ('20000000-0000-0000-0000-00000000000a', now() + interval '2 seconds','00000000-0000-0000-0000-00000000000a', 3450);
select public.evaluate_alerts('20000000-0000-0000-0000-00000000000a', now());
do $$ declare n int; begin
  select count(*) into n from public.alerts where kind='low_battery' and resolved_at is null;
  if n <> 1 then raise exception 'low_battery resolved at 3450 mV (hysteresis broken), got %', n; end if; end $$;
insert into public.readings(device_id,ts,owner_id,vbat_mv) values
 ('20000000-0000-0000-0000-00000000000a', now() + interval '3 seconds','00000000-0000-0000-0000-00000000000a', 3500);
select public.evaluate_alerts('20000000-0000-0000-0000-00000000000a', now());
do $$ declare n int; begin
  select count(*) into n from public.alerts where kind='low_battery' and resolved_at is null;
  if n <> 0 then raise exception 'low_battery not resolved at 3500 mV, got %', n; end if; end $$;

-- plausibility (G1 ranges)
do $$ begin
  if not public.reading_is_plausible(21.5, 55, 1200, 3900, 40) then raise exception 'normal flagged'; end if;
  if public.reading_is_plausible(61, 55, 1200, 3900, 40) then raise exception 'temp 61 accepted'; end if;
  if public.reading_is_plausible(21, 101, 1200, 3900, 40) then raise exception 'rh 101 accepted'; end if;
  if public.reading_is_plausible(21, 55, 100001, 3900, 40) then raise exception 'lux accepted'; end if;
  if public.reading_is_plausible(21, 55, 1200, 4300, 40) then raise exception 'vbat 4300 accepted'; end if;
  if public.reading_is_plausible(21, 55, 1200, 2900, 40) then raise exception 'vbat 2900 accepted'; end if;
end $$;

-- retention: 13-month-old row is purged, 11-month-old stays (G1)
insert into public.readings(device_id,ts,owner_id) values
 ('20000000-0000-0000-0000-00000000000a', now() - interval '13 months','00000000-0000-0000-0000-00000000000a'),
 ('20000000-0000-0000-0000-00000000000a', now() - interval '11 months','00000000-0000-0000-0000-00000000000a');
do $$ declare n bigint; begin n := public.purge_old_readings(); if n <> 1 then raise exception 'purge expected 1, got %', n; end if; end $$;

-- delete_plant (FR-A08, NFR-07, A-022): photos + readings go, sensor stays claimed, foreign plant refused
reset role;
insert into public.plants(id,owner_id,name,location_type,soil_type) values
  ('10000000-0000-0000-0000-0000000000a2','00000000-0000-0000-0000-00000000000a','Mint','house','potting');
insert into public.plant_images(plant_id,owner_id,storage_path) values
  ('10000000-0000-0000-0000-0000000000a2','00000000-0000-0000-0000-00000000000a','a/mint/1.jpg'),
  ('10000000-0000-0000-0000-0000000000a2','00000000-0000-0000-0000-00000000000a','a/mint/2.jpg');
insert into public.devices(id,hw_id,owner_id,plant_id,claimed_at,last_seen_at) values
  ('20000000-0000-0000-0000-0000000000a2','nw-a1b2c3d4e5f7','00000000-0000-0000-0000-00000000000a','10000000-0000-0000-0000-0000000000a2',now(),now());
insert into public.readings(device_id,ts,owner_id,plant_id,moisture_pct) values
  ('20000000-0000-0000-0000-0000000000a2', now() - interval '1 hour','00000000-0000-0000-0000-00000000000a','10000000-0000-0000-0000-0000000000a2', 40),
  ('20000000-0000-0000-0000-0000000000a2', now() - interval '2 hours','00000000-0000-0000-0000-00000000000a','10000000-0000-0000-0000-0000000000a2', 41),
  ('20000000-0000-0000-0000-0000000000a2', now() - interval '3 hours','00000000-0000-0000-0000-00000000000a',null, 42);  -- before assignment: kept
set role authenticated;
-- user B cannot delete A's plant, and nothing changes
set request.uid = '00000000-0000-0000-0000-00000000000b';
do $$ begin
  begin perform public.delete_plant('10000000-0000-0000-0000-0000000000a2');
        raise exception 'foreign delete_plant allowed';
  exception when sqlstate 'P0002' then null; end;
end $$;
-- anon cannot call it at all
reset role; set role anon;
do $$ begin
  begin perform public.delete_plant('10000000-0000-0000-0000-0000000000a2');
        raise exception 'anon delete_plant allowed';
  exception when insufficient_privilege then null; end;
end $$;
reset role; set role authenticated; set request.uid = '00000000-0000-0000-0000-00000000000a';
do $$ declare r jsonb; n int; begin
  r := public.delete_plant('10000000-0000-0000-0000-0000000000a2');
  if (r->'deleted'->>'readings')::int <> 2 then raise exception 'expected 2 readings deleted, got %', r; end if;
  if (r->'deleted'->>'photos')::int <> 2 or jsonb_array_length(r->'photo_paths') <> 2 then raise exception 'photo paths %', r; end if;
  select count(*) into n from public.plants where id = '10000000-0000-0000-0000-0000000000a2'; if n <> 0 then raise exception 'plant survives'; end if;
  select count(*) into n from public.plant_images where plant_id = '10000000-0000-0000-0000-0000000000a2'; if n <> 0 then raise exception 'photos survive'; end if;
  select count(*) into n from public.readings where device_id = '20000000-0000-0000-0000-0000000000a2' and plant_id is not null; if n <> 0 then raise exception 'plant readings survive'; end if;
  select count(*) into n from public.readings where device_id = '20000000-0000-0000-0000-0000000000a2'; if n <> 1 then raise exception 'unassigned reading must stay, got %', n; end if;
  -- sensor stays claimed, only the plant link is gone
  select count(*) into n from public.devices where id = '20000000-0000-0000-0000-0000000000a2'
     and owner_id = '00000000-0000-0000-0000-00000000000a' and plant_id is null;
  if n <> 1 then raise exception 'device must stay claimed with plant_id null'; end if;
  -- the other plant (Basil) is untouched
  select count(*) into n from public.plants; if n <> 1 then raise exception 'other plant affected'; end if;
end $$;
reset role;

-- account deletion cascades (FR-A01, NFR-07)
delete from auth.users where id = '00000000-0000-0000-0000-00000000000a';
do $$ declare n int; begin
  select count(*) into n from public.readings; if n <> 0 then raise exception 'readings survive account delete'; end if;
  select count(*) into n from public.plants;   if n <> 0 then raise exception 'plants survive'; end if;
  select count(*) into n from public.devices where owner_id is not null; if n <> 0 then raise exception 'device still owned'; end if;
end $$;
\echo ALL OK

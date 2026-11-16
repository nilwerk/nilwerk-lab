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
  grant select on public.plant_status, public.readings_daily to authenticated;
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

-- C10 (4.F3 review, Theo): battery alerts use the LOWEST vbat of the batch received since p_since, not the newest row.
-- Own plant + device C (one plant per device), removed again at the end of this section.
insert into public.plants(id,owner_id,name,location_type,soil_type) values
  ('10000000-0000-0000-0000-00000000000c','00000000-0000-0000-0000-00000000000a','Mint','house','potting');
insert into public.devices(id,hw_id,owner_id,plant_id,claimed_at,last_seen_at) values
  ('20000000-0000-0000-0000-00000000000c','nw-c10c10c10c10','00000000-0000-0000-0000-00000000000a','10000000-0000-0000-0000-00000000000c',now(), now());

-- (a) a dip inside the batch: 3600 mV, 3300 mV (dip), 3600 mV newest => low_battery must open
insert into public.readings(device_id,ts,owner_id,plant_id,moisture_pct,vbat_mv) values
 ('20000000-0000-0000-0000-00000000000c', now() - interval '3 minutes', '00000000-0000-0000-0000-00000000000a', '10000000-0000-0000-0000-00000000000c', 50, 3600),
 ('20000000-0000-0000-0000-00000000000c', now() - interval '2 minutes', '00000000-0000-0000-0000-00000000000a', '10000000-0000-0000-0000-00000000000c', 50, 3300),
 ('20000000-0000-0000-0000-00000000000c', now() - interval '1 minute',  '00000000-0000-0000-0000-00000000000a', '10000000-0000-0000-0000-00000000000c', 50, 3600);
select public.evaluate_alerts('20000000-0000-0000-0000-00000000000c', now() - interval '1 hour');
do $$ declare n int; begin
  select count(*) into n from public.alerts where device_id='20000000-0000-0000-0000-00000000000c' and kind='low_battery' and resolved_at is null;
  if n <> 1 then raise exception 'C10: dip inside batch missed (newest row 3600 hid vbat 3300), low_battery open = %', n; end if; end $$;
update public.alerts set resolved_at = now() where device_id='20000000-0000-0000-0000-00000000000c' and resolved_at is null;

-- (b) a bad moisture value next to a low battery: the newest row (250 moisture, plausible=false, 3300 mV) must not hide
-- its battery; the plausible row before it (60 moisture, 3600 mV) keeps moisture alerts off. The batch is the rows
-- received after the time captured here.
select now() as c10_since \gset
insert into public.readings(device_id,ts,owner_id,plant_id,moisture_pct,vbat_mv,plausible) values
 ('20000000-0000-0000-0000-00000000000c', now() - interval '2 minutes', '00000000-0000-0000-0000-00000000000a', '10000000-0000-0000-0000-00000000000c', 60, 3600, true),
 ('20000000-0000-0000-0000-00000000000c', now() - interval '1 minute',  '00000000-0000-0000-0000-00000000000a', '10000000-0000-0000-0000-00000000000c', 250, 3300, false);
select public.evaluate_alerts('20000000-0000-0000-0000-00000000000c', :'c10_since'::timestamptz);
do $$ declare n int; begin
  select count(*) into n from public.alerts where device_id='20000000-0000-0000-0000-00000000000c' and kind='low_battery' and resolved_at is null;
  if n <> 1 then raise exception 'C10: bad moisture row hid the low battery (3300 mV), low_battery open = %', n; end if;
  select count(*) into n from public.alerts where device_id='20000000-0000-0000-0000-00000000000c' and kind in ('too_wet','too_dry') and resolved_at is null;
  if n <> 0 then raise exception 'C10: moisture alert raised from the implausible row or from the plausible 60 row, open = %', n; end if;
end $$;

-- clean up device C and its plant (later sections count devices and alerts of user A)
delete from public.alerts where device_id='20000000-0000-0000-0000-00000000000c';
delete from public.readings where device_id='20000000-0000-0000-0000-00000000000c';
delete from public.devices where id='20000000-0000-0000-0000-00000000000c';
delete from public.plants where id='10000000-0000-0000-0000-00000000000c';

-- retention (NFR-13, A-028): raw 3 months, hourly roll-up 12 months. Fixture, all for device A:
--  * 4 plausible samples 100 days ago in one hour (20,30,40,50 %) + 1 implausible (moisture 99, vbat 2900 -> excluded)
--  * 1 raw sample 5 days ago (stays raw; rolled up only once its hour is complete, which it is)
--  * 1 raw sample 11 months ago directly in readings_hourly (kept) and 13 months ago (deleted)
reset role;
insert into public.readings(device_id,ts,owner_id,plant_id,moisture_pct,temp_c,vbat_mv,plausible)
select '20000000-0000-0000-0000-00000000000a', date_trunc('hour', now() - interval '100 days') + (g*15 || ' minutes')::interval,
       '00000000-0000-0000-0000-00000000000a', '10000000-0000-0000-0000-00000000000a', 20 + 10*g, 20 + g, 3800, true from generate_series(0,3) g;
insert into public.readings(device_id,ts,owner_id,plant_id,moisture_pct,vbat_mv,plausible) values
 ('20000000-0000-0000-0000-00000000000a', date_trunc('hour', now() - interval '100 days') + interval '50 minutes',
  '00000000-0000-0000-0000-00000000000a','10000000-0000-0000-0000-00000000000a', 99, 2900, false),
 ('20000000-0000-0000-0000-00000000000a', now() - interval '5 days','00000000-0000-0000-0000-00000000000a',null,10,3700,true);
insert into public.readings_hourly(device_id,hour,owner_id,n,moisture_avg) values
 ('20000000-0000-0000-0000-00000000000a', date_trunc('hour', now() - interval '11 months'),'00000000-0000-0000-0000-00000000000a',4,33),
 ('20000000-0000-0000-0000-00000000000a', date_trunc('hour', now() - interval '13 months'),'00000000-0000-0000-0000-00000000000a',4,33);
do $$ declare r jsonb; n int; h record; begin
  -- the 31 fixture rows from day 0..30 are younger than 3 months; apply_retention must delete exactly the 5 old raw rows
  r := public.apply_retention();
  if (r->>'raw_deleted')::int <> 5 then raise exception 'raw_deleted expected 5, got %', r; end if;
  if (r->>'hourly_deleted')::int <> 1 then raise exception 'hourly_deleted expected 1 (13 months), got %', r; end if;
  select count(*) into n from public.readings where ts < now() - interval '3 months'; if n <> 0 then raise exception 'raw older than 3 months survives'; end if;
  select count(*) into n from public.readings where ts > now() - interval '3 months'; if n < 31 then raise exception 'young raw rows lost, got %', n; end if;
  -- the 100-day-old hour is in the roll-up: 4 plausible samples, avg 35, min 20, max 50, vbat min 3800 (implausible row excluded)
  select * into h from public.readings_hourly where device_id='20000000-0000-0000-0000-00000000000a'
     and hour = date_trunc('hour', now() - interval '100 days');
  if h.n is distinct from 4 or h.moisture_avg is distinct from 35::real or h.moisture_min <> 20 or h.moisture_max <> 50 or h.vbat_min_mv <> 3800
     then raise exception 'roll-up wrong: %', h; end if;
  select count(*) into n from public.readings_hourly where hour < now() - interval '12 months'; if n <> 0 then raise exception '13-month roll-up survives'; end if;
  select count(*) into n from public.readings_hourly where hour = date_trunc('hour', now() - interval '11 months'); if n <> 1 then raise exception '11-month roll-up lost'; end if;
  -- idempotent: second run changes nothing and a re-roll over the same hour never lowers n
  r := public.apply_retention();
  if (r->>'raw_deleted')::int <> 0 or (r->>'hourly_deleted')::int <> 0 then raise exception 'second run not a no-op: %', r; end if;
  select hr.n into n from public.readings_hourly hr where hour = date_trunc('hour', now() - interval '100 days'); if n <> 4 then raise exception 'roll-up n lowered to %', n; end if;
  -- daily view: one day row for the 100-day-old day, weighted average 35
  select * into h from public.readings_daily where day = (date_trunc('hour', now() - interval '100 days') at time zone 'UTC')::date;
  if h.n <> 4 or h.moisture_avg <> 35 then raise exception 'daily view wrong: %', h; end if;
  -- a roll-up hour is never shrunk when part of its raw rows are gone: delete one of the 2 raw rows of a kept hour and re-roll
  perform public.rollup_readings(now() - interval '6 days');
  delete from public.readings where ts > now() - interval '5 days 1 hour' and ts < now() - interval '4 days 23 hours' and plant_id is null;   -- half of that hour
  perform public.rollup_readings(now() - interval '6 days');
  select hr.n into n from public.readings_hourly hr where hour = date_trunc('hour', now() - interval '5 days'); if n <> 2 then raise exception 'roll-up shrunk after raw delete, n=%', n; end if;  -- 2 = fixture day-5 row + the extra one (one raw row is left, a naive upsert would write 1)
end $$;
-- roll-up is owner-scoped by RLS: user B sees none, user A (free) sees only the last 7 days of it
set role authenticated; set request.uid = '00000000-0000-0000-0000-00000000000b';
do $$ declare n int; begin select count(*) into n from public.readings_hourly; if n <> 0 then raise exception 'B sees A roll-up (%)', n; end if;
  select count(*) into n from public.readings_daily; if n <> 0 then raise exception 'B sees A daily'; end if; end $$;
reset role; update public.profiles set is_premium = false where id = '00000000-0000-0000-0000-00000000000a';   -- A is premium from the earlier block
set role authenticated; set request.uid = '00000000-0000-0000-0000-00000000000a';
do $$ declare n int; begin select count(*) into n from public.readings_hourly where hour < now() - interval '7 days';
  if n <> 0 then raise exception 'free user sees roll-up older than 7 days'; end if; end $$;
reset role; update public.profiles set is_premium = true where id = '00000000-0000-0000-0000-00000000000a'; set role authenticated;
-- users cannot call the retention functions or write the roll-up
do $$ begin
  begin perform public.apply_retention(); raise exception 'user ran apply_retention';
  exception when insufficient_privilege then null; end;
  begin insert into public.readings_hourly(device_id,hour,owner_id,n) values ('20000000-0000-0000-0000-00000000000a', date_trunc('hour',now()),'00000000-0000-0000-0000-00000000000a',1);
        raise exception 'user wrote roll-up';
  exception when insufficient_privilege or sqlstate '42501' then null; end;
end $$;
reset role;

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
insert into public.readings_hourly(device_id,hour,owner_id,plant_id,n) values
  ('20000000-0000-0000-0000-0000000000a2', date_trunc('hour', now() - interval '30 days'),'00000000-0000-0000-0000-00000000000a','10000000-0000-0000-0000-0000000000a2',4);
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
  select count(*) into n from public.readings_hourly where device_id = '20000000-0000-0000-0000-0000000000a2'; if n <> 0 then raise exception 'plant roll-up survives'; end if;
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

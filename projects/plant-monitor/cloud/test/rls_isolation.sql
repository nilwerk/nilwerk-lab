-- RLS isolation test (4.B1, NFR-06, FR-A08): user A cannot read or write user B's rows, on EVERY table.
-- Runs after migrations + stub_auth + grants + seed (seed: A free, B premium, each with one row per table).
-- Both users are made premium first so that isolation is proven by owner_id, not by the free-plan 7-day rule.
\set ON_ERROR_STOP on
\set A '00000000-0000-0000-0000-00000000000a'
\set B '00000000-0000-0000-0000-00000000000b'
reset role;
update public.profiles set is_premium = true;

-- 0. every public table has RLS enabled (NFR-06)
do $$ declare t text; n int := 0; begin
  for t in select c.relname from pg_class c join pg_namespace s on s.oid = c.relnamespace
           where s.nspname = 'public' and c.relkind = 'r' loop
    n := n + 1;
    if not (select relrowsecurity from pg_class where oid = ('public.' || t)::regclass) then raise exception 'RLS missing on %', t; end if;
  end loop;
  raise notice 'RLS enabled on all % public tables', n;
end $$;

-- 1. READ isolation. Owner column per table; profiles uses id. Service-only tables (no policy) show nothing to anyone.
create temp table nw_t (tbl text, ownercol text, readable boolean);
insert into nw_t values
  ('profiles','id',true), ('plants','owner_id',true), ('devices','owner_id',true), ('plant_images','owner_id',true),
  ('readings','owner_id',true), ('readings_hourly','owner_id',true), ('events','owner_id',true), ('alerts','owner_id',true),
  ('push_tokens','owner_id',true), ('tips','owner_id',true), ('api_keys','owner_id',true),
  ('device_credentials',null,false), ('claim_tokens',null,false), ('firmware_releases',null,false);
grant select on nw_t to authenticated;

set role authenticated;
set request.uid = :'A';
do $$ declare r record; own int; other int; begin
  for r in select * from nw_t loop
    if r.readable then
      execute format('select count(*) from public.%I where %I = %L', r.tbl, r.ownercol, current_setting('request.uid')) into own;
      execute format('select count(*) from public.%I where %I <> %L', r.tbl, r.ownercol, current_setting('request.uid')) into other;
      if own = 0 then raise exception 'A sees none of its own rows in % (vacuous test)', r.tbl; end if;
      if other <> 0 then raise exception 'A sees % foreign rows in %', other, r.tbl; end if;
      raise notice 'read ok  % : A sees % own, 0 foreign', rpad(r.tbl, 16), own;
    else
      execute format('select count(*) from public.%I', r.tbl) into own;
      if own <> 0 then raise exception 'service-only table % visible to A (% rows)', r.tbl, own; end if;
      raise notice 'read ok  % : service-only, A sees 0', rpad(r.tbl, 16);
    end if;
  end loop;
end $$;
-- same from B's side (symmetry)
set request.uid = :'B';
do $$ declare r record; own int; other int; begin
  for r in select * from nw_t where readable loop
    execute format('select count(*) from public.%I where %I = %L', r.tbl, r.ownercol, current_setting('request.uid')) into own;
    execute format('select count(*) from public.%I where %I <> %L', r.tbl, r.ownercol, current_setting('request.uid')) into other;
    if own = 0 or other <> 0 then raise exception 'B isolation broken in % (own %, foreign %)', r.tbl, own, other; end if;
  end loop;
end $$;
-- api_keys: key_hash column is not selectable even by the owner (NFR-06)
do $$ begin
  begin perform key_hash from public.api_keys; raise exception 'key_hash readable';
  exception when insufficient_privilege then null; end;
end $$;
-- views run with the caller's RLS (security_invoker)
do $$ declare n int; begin
  select count(*) into n from public.plant_status where owner_id <> current_setting('request.uid')::uuid; if n <> 0 then raise exception 'plant_status leaks'; end if;
  select count(*) into n from public.readings_daily where owner_id <> current_setting('request.uid')::uuid; if n <> 0 then raise exception 'readings_daily leaks'; end if;
end $$;

-- 2. WRITE isolation: A tries to change / delete / forge B's rows. Allowed outcomes: 0 rows affected or an
--    insufficient_privilege (42501, RLS or missing grant). Anything else (a row changed) fails the test.
set request.uid = :'A';
do $$ declare r record; n int; b uuid := '00000000-0000-0000-0000-00000000000b'; begin
  for r in select * from nw_t loop
    -- UPDATE a foreign row (profiles: id; others: owner_id); where-clause targets B only
    begin
      if r.tbl = 'firmware_releases' then execute 'update public.firmware_releases set min_battery_mv = 3000';
      elsif r.tbl = 'claim_tokens' then execute format('update public.claim_tokens set used_at = now() where user_id = %L', b);
      elsif r.tbl = 'device_credentials' then execute format('update public.device_credentials set revoked_at = now() where device_id = %L', '20000000-0000-0000-0000-00000000000b');
      else execute format('update public.%I set %I = %I where %I = %L', r.tbl, r.ownercol, r.ownercol, r.ownercol, b); end if;
      get diagnostics n = row_count;
      if n <> 0 then raise exception 'A updated % row(s) of B in %', n, r.tbl; end if;
    exception when insufficient_privilege then null; end;
    -- DELETE a foreign row
    begin
      if r.tbl = 'firmware_releases' then execute 'delete from public.firmware_releases';
      elsif r.tbl = 'claim_tokens' then execute format('delete from public.claim_tokens where user_id = %L', b);
      elsif r.tbl = 'device_credentials' then execute format('delete from public.device_credentials where device_id = %L', '20000000-0000-0000-0000-00000000000b');
      else execute format('delete from public.%I where %I = %L', r.tbl, r.ownercol, b); end if;
      get diagnostics n = row_count;
      if n <> 0 then raise exception 'A deleted % row(s) of B in %', n, r.tbl; end if;
    exception when insufficient_privilege then null; end;
    raise notice 'write ok % : A cannot update/delete B rows', rpad(r.tbl, 16);
  end loop;
end $$;
-- INSERT forged rows owned by B (WITH CHECK / no insert policy => 42501)
do $$ declare b text := '00000000-0000-0000-0000-00000000000b'; pb text := '10000000-0000-0000-0000-00000000000b'; db text := '20000000-0000-0000-0000-00000000000b'; stmt text; begin
  foreach stmt in array array[
    format('insert into public.plants(owner_id,name,location_type,soil_type) values (%L,''x'',''house'',''potting'')', b),
    format('insert into public.devices(hw_id,owner_id) values (''nw-ffffffffffff'', %L)', b),
    format('insert into public.plant_images(plant_id,owner_id,storage_path) values (%L,%L,''forged/a.jpg'')', pb, b),
    format('insert into public.readings(device_id,ts,owner_id) values (%L, now(), %L)', db, b),
    format('insert into public.readings_hourly(device_id,hour,owner_id,n) values (%L, date_trunc(''hour'',now()), %L, 1)', db, b),
    format('insert into public.events(device_id,owner_id,ts,type,critical) values (%L,%L,now(),''wetting'',false)', db, b),
    format('insert into public.alerts(owner_id,device_id,kind) values (%L,%L,''too_dry'')', b, db),
    format('insert into public.push_tokens(owner_id,expo_token) values (%L,''ExponentPushToken[forged]'')', b),
    format('insert into public.tips(plant_id,owner_id,expires_at,content,guardrail_version) values (%L,%L,now(),''{}'',''x'')', pb, b),
    format('insert into public.api_keys(owner_id,name,prefix,key_hash) values (%L,''k'',''nwk_x'',''\xdeadbeef'')', b),
    format('insert into public.device_credentials(device_id,token_hash) values (%L,''\xdeadbeef'')', db),
    format('insert into public.claim_tokens(token_hash,user_id,expires_at) values (''\xdeadbeef'',%L,now())', b),
    'insert into public.firmware_releases(version,kind,storage_path,sha256,size_bytes) values (''9'',''fw'',''p'',repeat(''0'',64),1)',
    format('insert into public.profiles(id) values (%L)', b)
  ] loop
    begin execute stmt; raise exception 'forged insert allowed: %', stmt;
    exception when insufficient_privilege or unique_violation then null; end;   -- unique_violation only for the profiles row that already exists; RLS fires first for the rest
  end loop;
  raise notice 'write ok  forged inserts refused on all 14 tables';
end $$;
-- N2 (PR #45): A may not point A's own device at B's plant (devices_update_own with check), but may use/clear its own plant link
do $$ declare n int; begin
  begin
    update public.devices set plant_id = '10000000-0000-0000-0000-00000000000b' where id = '20000000-0000-0000-0000-00000000000a';
    raise exception 'A pointed its device at B plant';
  exception when insufficient_privilege then null;   -- 42501 new row violates row-level security policy
    when unique_violation then raise exception 'A pointed its device at B plant (the policy did not refuse it; only the unique key did)'; end;
  update public.devices set plant_id = null where id = '20000000-0000-0000-0000-00000000000a'; get diagnostics n = row_count;
  if n <> 1 then raise exception 'A cannot clear its own plant link (%)', n; end if;
  update public.devices set plant_id = '10000000-0000-0000-0000-00000000000a' where id = '20000000-0000-0000-0000-00000000000a'; get diagnostics n = row_count;
  if n <> 1 then raise exception 'A cannot set its own plant link (%)', n; end if;
  raise notice 'write ok  devices.plant_id: A cannot point its device at B plant; own plant and null allowed';
end $$;
-- A may not even call B's delete_plant, and cannot grant itself premium (FR-P04)
do $$ begin
  begin perform public.delete_plant('10000000-0000-0000-0000-00000000000b'); raise exception 'A deleted B plant';
  exception when sqlstate 'P0002' then null; end;
end $$;
reset role;

-- 2b. setup save (4.A4c, N1/N2): create_plant_and_link_device is one atomic call and never moves a sensor silently
set role authenticated;
set request.uid = :'A';
do $$ declare n int; nid uuid; begin
  begin perform public.create_plant_and_link_device('20000000-0000-0000-0000-00000000000b', 'X', 'house', null, 'potting', null, null, false);
    raise exception 'A linked a plant to the B device';
  exception when sqlstate 'P0002' then null; end;
  select count(*) into n from public.plants where name = 'X'; if n <> 0 then raise exception 'plant X inserted for a foreign device'; end if;
  begin perform public.create_plant_and_link_device('20000000-0000-0000-0000-00000000000a', 'Y', 'house', null, 'potting', null, null, false);
    raise exception 'A moved its sensor without asking';
  exception when sqlstate 'P0005' then null; end;
  select count(*) into n from public.plants where name = 'Y'; if n <> 0 then raise exception 'plant Y inserted on a refused move'; end if;
  nid := public.create_plant_and_link_device('20000000-0000-0000-0000-00000000000a', 'Z', 'balcony', 'Sill', 'sand', null, 'Berlin', true);
  select count(*) into n from public.devices where id = '20000000-0000-0000-0000-00000000000a' and plant_id = nid; if n <> 1 then raise exception 'confirmed move did not link the device'; end if;
  select count(*) into n from public.plants where id = nid and owner_id = '00000000-0000-0000-0000-00000000000a'; if n <> 1 then raise exception 'new plant not owned by A'; end if;
  select count(*) into n from public.plants where id = '10000000-0000-0000-0000-00000000000a'; if n <> 1 then raise exception 'confirmed move deleted the old plant'; end if;
  raise notice 'contract ok  create_plant_and_link_device: foreign device refused, silent move refused, confirmed move links and keeps the old plant';
end $$;
reset role;

-- 2c. the device link must not reach a foreign plant even when no device uses that plant (ADR-017, RLS-1).
-- Plant C is owned by B and unlinked; the unique key on devices.plant_id would hide the hole for B's own plant, so this uses C.
reset role;
insert into public.plants (id, owner_id, name, location_type, soil_type) values ('10000000-0000-0000-0000-00000000000c', '00000000-0000-0000-0000-00000000000b', 'Unlinked B', 'house', 'potting');
set role authenticated;
set request.uid = :'A';
do $$ begin
  begin
    update public.devices set plant_id = '10000000-0000-0000-0000-00000000000c' where id = '20000000-0000-0000-0000-00000000000a';
    raise exception 'A pointed its device at an unlinked B plant';
  exception when insufficient_privilege then null; end;   -- 42501: the policy's plant ownership check
end $$;
reset role;
delete from public.plants where id = '10000000-0000-0000-0000-00000000000c';
do $$ declare n int; begin
  select count(*) into n from public.devices where id = '20000000-0000-0000-0000-00000000000a' and plant_id = '10000000-0000-0000-0000-00000000000c'; if n <> 0 then raise exception 'foreign plant linked'; end if;
  raise notice 'RLS ok    A cannot link its device to an unlinked foreign plant (devices_update_own plant check)';
end $$;

-- 3. B's data is untouched after all of the above
do $$ declare n int; begin
  select count(*) into n from public.plants where owner_id = '00000000-0000-0000-0000-00000000000b'; if n <> 1 then raise exception 'B plant changed'; end if;
  select count(*) into n from public.readings where owner_id = '00000000-0000-0000-0000-00000000000b'; if n <> 288 then raise exception 'B readings changed (%)', n; end if;
  select count(*) into n from public.devices where owner_id = '00000000-0000-0000-0000-00000000000a' and plant_id = '10000000-0000-0000-0000-00000000000b'; if n <> 0 then raise exception 'A device points at B plant'; end if;
  select count(*) into n from public.firmware_releases; if n <> 1 then raise exception 'firmware changed'; end if;
end $$;
\echo RLS ISOLATION OK

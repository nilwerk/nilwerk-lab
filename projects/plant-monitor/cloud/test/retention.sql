-- Retention / roll-up test (4.B1, NFR-13, A-028): raw readings ~3 months, hourly roll-up 12 months.
-- Runs after migrations + stub_auth + grants on an EMPTY database (own fixtures; no seed).
\set ON_ERROR_STOP on
insert into auth.users(id) values ('00000000-0000-0000-0000-00000000000a');
insert into public.devices(id, hw_id, owner_id, claimed_at) values
  ('20000000-0000-0000-0000-00000000000a', 'nw-a1b2c3d4e5f6', '00000000-0000-0000-0000-00000000000a', now());
-- fixture: 4 plausible samples 100 days ago in one hour (20,30,40,50) + 1 implausible (excluded),
--          1 sample 5 days ago, 1 sample 10 days ago; roll-up rows 11 months (kept) and 13 months (deleted) old.
insert into public.readings(device_id, ts, owner_id, moisture_pct, vbat_mv, plausible)
select '20000000-0000-0000-0000-00000000000a', date_trunc('hour', now() - interval '100 days') + (g * 15 || ' minutes')::interval,
       '00000000-0000-0000-0000-00000000000a', 20 + 10 * g, 3800, true from generate_series(0, 3) g;
insert into public.readings(device_id, ts, owner_id, moisture_pct, vbat_mv, plausible) values
  ('20000000-0000-0000-0000-00000000000a', date_trunc('hour', now() - interval '100 days') + interval '50 minutes', '00000000-0000-0000-0000-00000000000a', 99, 2900, false),
  ('20000000-0000-0000-0000-00000000000a', now() - interval '5 days',  '00000000-0000-0000-0000-00000000000a', 10, 3700, true),
  ('20000000-0000-0000-0000-00000000000a', now() - interval '10 days', '00000000-0000-0000-0000-00000000000a', 11, 3700, true);
insert into public.readings_hourly(device_id, hour, owner_id, n, moisture_avg) values
  ('20000000-0000-0000-0000-00000000000a', date_trunc('hour', now() - interval '11 months'), '00000000-0000-0000-0000-00000000000a', 4, 33),
  ('20000000-0000-0000-0000-00000000000a', date_trunc('hour', now() - interval '13 months'), '00000000-0000-0000-0000-00000000000a', 4, 33);

do $$ declare r jsonb; n int; h record; begin
  r := public.apply_retention();
  raise notice 'apply_retention #1 -> %', r;
  if (r->>'raw_deleted')::int <> 5 then raise exception 'raw_deleted expected 5 (4 plausible + 1 implausible old rows), got %', r; end if;
  if (r->>'hourly_deleted')::int <> 1 then raise exception 'hourly_deleted expected 1 (13 months), got %', r; end if;
  select count(*) into n from public.readings where ts < now() - interval '3 months'; if n <> 0 then raise exception 'raw older than 3 months survives'; end if;
  select count(*) into n from public.readings; if n <> 2 then raise exception 'young raw rows must stay (2), got %', n; end if;
  -- the expired hour survives as a roll-up: n=4, avg 35, min 20, max 50, vbat min 3800 (implausible row excluded)
  select * into h from public.readings_hourly where device_id = '20000000-0000-0000-0000-00000000000a' and hour = date_trunc('hour', now() - interval '100 days');
  if h.n is distinct from 4 or h.moisture_avg is distinct from 35::real or h.moisture_min <> 20 or h.moisture_max <> 50 or h.vbat_min_mv <> 3800
    then raise exception 'roll-up wrong: %', h; end if;
  select count(*) into n from public.readings_hourly where hour < now() - interval '12 months'; if n <> 0 then raise exception '13-month roll-up survives'; end if;
  select count(*) into n from public.readings_hourly where hour = date_trunc('hour', now() - interval '11 months'); if n <> 1 then raise exception '11-month roll-up lost'; end if;
  -- idempotent
  r := public.apply_retention();
  raise notice 'apply_retention #2 -> %', r;
  if (r->>'raw_deleted')::int <> 0 or (r->>'hourly_deleted')::int <> 0 then raise exception 'second run not a no-op: %', r; end if;
  select hr.n into n from public.readings_hourly hr where hour = date_trunc('hour', now() - interval '100 days'); if n <> 4 then raise exception 'roll-up n lowered to %', n; end if;
  -- configurable window (raw_months knob): 1 month removes the 5- and 10-day-old rows? no: they are < 1 month, so they stay
  r := public.apply_retention(1, 12);
  if (r->>'raw_deleted')::int <> 0 then raise exception 'raw_months=1 must keep 10-day-old rows, got %', r; end if;
end $$;
\echo RETENTION OK

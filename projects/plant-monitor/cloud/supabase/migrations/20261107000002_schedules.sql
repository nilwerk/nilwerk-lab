-- 4.B1 migration 2/3: pg_cron schedules from the footer of docs/interfaces/db-schema.sql.
-- A-028 / NFR-13: raw readings ~3 months, hourly roll-up 12 months. FR-A07/FR-D06: offline scan.
-- Fails LOUDLY (exception) when pg_cron is missing, so a deploy never silently lacks retention (NFR-13, A-028).
-- Only an explicit opt-out skips it: `set nilwerk.allow_no_cron = on` (cloud/test.sh sets it for plain local Postgres).
do $$
begin
  if exists (select 1 from pg_available_extensions where name = 'pg_cron') then
    create extension if not exists pg_cron;
    perform cron.schedule('nw-offline-scan', '*/5 * * * *', 'select public.scan_offline()');
    perform cron.schedule('nw-rollup',       '5 * * * *',   'select public.rollup_readings()');
    perform cron.schedule('nw-retention',    '17 3 * * *',  'select public.apply_retention()');
  else
    if coalesce(current_setting('nilwerk.allow_no_cron', true), 'off') = 'on' then
      raise notice 'pg_cron not available: schedules skipped (nilwerk.allow_no_cron=on, test/local only)';
    else
      raise exception 'pg_cron is not available: enable it (Supabase Dashboard > Database > Extensions) and re-run. Retention would not run otherwise (NFR-13).';
    end if;
  end if;
end $$;

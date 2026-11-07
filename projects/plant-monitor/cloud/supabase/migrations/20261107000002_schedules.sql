-- 4.B1 migration 2/3: pg_cron schedules from the footer of docs/interfaces/db-schema.sql.
-- A-028 / NFR-13: raw readings ~3 months, hourly roll-up 12 months. FR-A07/FR-D06: offline scan.
-- Guarded: runs only where pg_cron is available (Supabase yes; plain Postgres in CI/test.sh no -> skipped).
do $$
begin
  if exists (select 1 from pg_available_extensions where name = 'pg_cron') then
    create extension if not exists pg_cron;
    perform cron.schedule('nw-offline-scan', '*/5 * * * *', 'select public.scan_offline()');
    perform cron.schedule('nw-rollup',       '5 * * * *',   'select public.rollup_readings()');
    perform cron.schedule('nw-retention',    '17 3 * * *',  'select public.apply_retention()');
  else
    raise notice 'pg_cron not available: schedules skipped (enable pg_cron on Supabase and re-run this file)';
  end if;
end $$;

-- Mimics Supabase default privileges (table access for API roles; RLS + column grants do the restricting).
-- Same prelude as docs/interfaces/db-schema.test.sql.
do $$ declare t text; begin
  for t in select tablename from pg_tables where schemaname='public' loop
    if t <> 'api_keys' then execute format('grant all on public.%I to authenticated, service_role', t); end if;
  end loop;
  grant usage on schema public to anon, authenticated, service_role;
  grant select on public.plant_status, public.readings_daily to authenticated;
  grant select (id, owner_id, name, prefix, created_at, last_used_at, revoked_at) on public.api_keys to authenticated;
  grant all on public.api_keys to service_role;
end $$;

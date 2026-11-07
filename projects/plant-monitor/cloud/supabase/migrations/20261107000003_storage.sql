-- 4.B1 migration 3/3: private Storage buckets + owner-folder policy (FR-A05, NFR-06), from db-schema.sql comments.
-- Guarded: runs only where the Supabase `storage` schema exists.
do $$
begin
  if to_regclass('storage.buckets') is not null and to_regclass('storage.objects') is not null then
    insert into storage.buckets (id, name, public) values ('plant-photos', 'plant-photos', false) on conflict (id) do nothing;
    insert into storage.buckets (id, name, public) values ('firmware', 'firmware', false) on conflict (id) do nothing;
    -- 'firmware' has no policy: service role only (signed URLs issued by ingest, FR-D05).
    if not exists (select 1 from pg_policies where schemaname = 'storage' and tablename = 'objects' and policyname = 'photos_own') then
      create policy photos_own on storage.objects for all
        using (bucket_id = 'plant-photos' and (storage.foldername(name))[1] = auth.uid()::text)
        with check (bucket_id = 'plant-photos' and (storage.foldername(name))[1] = auth.uid()::text);
    end if;
  else
    raise notice 'storage schema not present: buckets skipped';
  end if;
end $$;

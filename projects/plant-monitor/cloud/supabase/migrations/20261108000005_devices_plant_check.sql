-- 4.B2 security fix (Theo's review N2 of PR #45; NFR-06, NFR-07, FR-A08): a user may only point THEIR device at THEIR plant.
-- Before: devices_update_own checked only owner_id = auth.uid(), so user B could set devices.plant_id to user A's plant id
-- (needs the uuid; `unique` would leak its existence, and ingest_batch would stamp A's plant_id on B-owned readings/events).
-- The policy is replaced here (migration 1 stays byte-identical to docs/interfaces/db-schema.sql, which is the Architect's contract;
-- the same clause belongs into that file in his contract PR). Service role / postgres are not subject to RLS, so claim and ingest are unaffected.
drop policy if exists devices_update_own on public.devices;
create policy devices_update_own on public.devices for update
  using (owner_id = auth.uid())
  with check (owner_id = auth.uid()
    and (plant_id is null or exists (select 1 from public.plants p where p.id = plant_id and p.owner_id = auth.uid())));

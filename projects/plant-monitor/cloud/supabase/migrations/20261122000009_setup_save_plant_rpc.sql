-- 4.A4c (ADR-017): setup "save plant" RPC and the plant check in devices_update_own.
-- Moved here per owner decision C6 (option B). Migration 20261107000001_core_schema.sql is frozen (cloud/README.md
-- "Migration rules"; pushed to nilwerk-cloud, see cloud/README.md), so it is NOT edited: this file carries the change.
-- The devices_update_own text is the same clause as 20261108000005_devices_plant_check.sql; this file restates it so the
-- policy is defined here too. drop + create replaces the policy with that same definition (no behaviour change).
-- docs/interfaces/db-schema.sql carries the same two blocks (the contract, kept equal to the cumulative 2.4 state).

drop policy if exists devices_update_own on public.devices;
create policy devices_update_own on public.devices for update
  using (owner_id = auth.uid())
  with check (owner_id = auth.uid()
    and (plant_id is null or exists (select 1 from public.plants p where p.id = plant_id and p.owner_id = auth.uid())));

-- Setup "save plant" (4.A4c, FR-A03, FR-A04, NFR-06; ADR-017): one call inserts the plant AND points the device at it, or does neither.
-- Runs as one transaction: if the device link fails, the plant insert is rolled back too (no orphan plant).
-- A device that already has a plant is NOT moved unless p_move is true (no silent move; P0005 otherwise).
-- security definer: RLS does not apply inside, so the owner checks are explicit (device owned by auth.uid(); the new plant is the caller's).
create or replace function public.create_plant_and_link_device(
  p_device uuid, p_name text, p_location_type text, p_area text, p_soil_type text, p_species text, p_city text, p_move boolean default false
) returns uuid
language plpgsql security definer set search_path = public as $$
declare v_uid uuid := auth.uid(); v_current uuid; v_plant uuid;
begin
  if v_uid is null then raise exception 'not authenticated' using errcode = '28000'; end if;
  select plant_id into v_current from public.devices where id = p_device and owner_id = v_uid for update;
  if not found then raise exception 'device not found' using errcode = 'P0002'; end if;   -- same answer for unknown and foreign devices
  if v_current is not null and not p_move then raise exception 'device already has a plant' using errcode = 'P0005'; end if;
  insert into public.plants (owner_id, name, location_type, area, soil_type, species, city)
    values (v_uid, p_name, p_location_type, p_area, p_soil_type, p_species, p_city) returning id into v_plant;
  update public.devices set plant_id = v_plant where id = p_device and owner_id = v_uid;
  return v_plant;
end $$;
revoke all on function public.create_plant_and_link_device(uuid, text, text, text, text, text, text, boolean) from public, anon;
grant execute on function public.create_plant_and_link_device(uuid, text, text, text, text, text, text, boolean) to authenticated;

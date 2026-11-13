-- 4.B2b DELETE /account: server-side step 1 (release devices) behind the edge function `delete-account`.
-- Requirements: FR-A01, FR-A08, NFR-07 (GDPR erasure), NFR-06. No table changes (db-schema.sql stays the contract).
-- service_role ONLY (the edge function calls it with SUPABASE_SECRET_KEY after it verified the user JWT itself); the user id is
-- never taken from the request body. Idempotent: a second call for the same user finds nothing and returns zeros.
-- Order of the whole operation (openapi /account): this function -> delete Storage objects under '<owner_id>/' in plant-photos
-- -> delete the auth.users row (FK cascade removes profiles, plants, plant_images, readings, readings_hourly, events, alerts,
-- tips, api_keys, push_tokens, claim_tokens).
create or replace function public.release_account_devices(p_user uuid) returns jsonb
language plpgsql security definer set search_path = public as $$
declare v_released int; v_paths text[];
begin
  if p_user is null then raise exception 'p_user required'; end if;
  -- photo paths known to the database (the function also lists the Storage folder, in case a row is missing)
  select coalesce(array_agg(storage_path), '{}') into v_paths from public.plant_images where owner_id = p_user;
  -- revoke every device token of this user (FR-A08), then release the devices; the device rows stay (hardware), unowned
  update public.device_credentials set revoked_at = coalesce(revoked_at, now())
    where device_id in (select id from public.devices where owner_id = p_user);
  update public.devices set owner_id = null, plant_id = null where owner_id = p_user;
  get diagnostics v_released = row_count;
  -- unused claim tokens of this user must not be redeemable after deletion
  delete from public.claim_tokens where user_id = p_user;
  return jsonb_build_object('released', v_released, 'photo_paths', to_jsonb(v_paths));
end $$;

revoke all on function public.release_account_devices(uuid) from public, anon, authenticated;
grant execute on function public.release_account_devices(uuid) to service_role;

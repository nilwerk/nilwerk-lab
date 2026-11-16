-- C10 (firmware review, Theo, 4.F3): evaluate_alerts looked only at the newest plausible reading.
-- Two misses: (1) a battery dip inside a batch was hidden when a later row in the same batch was higher;
-- (2) a reading with a bad moisture value (plausible=false) was skipped, so its low vbat was hidden too.
-- Fix: battery = MIN vbat_mv over the batch received since p_since, with NO plausible filter (a low battery is a
-- real-world fact the sensor reports, FR-D06). Only physically impossible values are ignored (vbat_mv <= 0 or
-- > 5000 mV: a corrupt ADC read, Ines QA note 1), so one bad sample cannot open a false low_battery; real low
-- readings such as 2900 mV still count. If the call has no batch rows (manual re-evaluation), fall back to the
-- newest reading's vbat (same ignore rule). Moisture keeps the plausible filter: newest plausible reading (FR-A07).
-- Migration 1 stays byte-identical to docs/interfaces/db-schema.sql (drift guard); this is a new migration, as the
-- README's migration rules require. The same body belongs into db-schema.sql in the Architect's contract PR.
create or replace function public.evaluate_alerts(p_device uuid, p_since timestamptz) returns void
language plpgsql security definer set search_path = public as $$
declare d public.devices; pl public.plants; r public.readings; v_min integer;
begin
  select * into d from public.devices where id = p_device;
  if d.owner_id is null then return; end if;
  select * into pl from public.plants where id = d.plant_id;
  -- moisture: newest plausible reading
  select * into r from public.readings where device_id = p_device and plausible order by ts desc limit 1;
  -- battery: lowest vbat in the batch (received since p_since), plausible or not; impossible values ignored
  if exists (select 1 from public.readings where device_id = p_device and received_at >= p_since) then
    select min(vbat_mv) into v_min from public.readings
     where device_id = p_device and received_at >= p_since and vbat_mv > 0 and vbat_mv <= 5000;
  else
    select x.vbat_mv into v_min from public.readings x
     where x.device_id = p_device and x.vbat_mv > 0 and x.vbat_mv <= 5000 order by x.ts desc limit 1;
  end if;
  if r.ts is null and v_min is null then return; end if;

  -- helper pattern: open if condition, resolve if clearly cleared
  if pl.id is not null and r.moisture_pct is not null then
    if r.moisture_pct < pl.dry_threshold_pct then
      insert into public.alerts (owner_id, device_id, plant_id, kind, detail)
      values (d.owner_id, d.id, pl.id, 'too_dry', jsonb_build_object('moisture_pct', r.moisture_pct, 'threshold', pl.dry_threshold_pct))
      on conflict (device_id, kind) where resolved_at is null do nothing;
    elsif r.moisture_pct >= pl.dry_threshold_pct + 5 then
      update public.alerts set resolved_at = now() where device_id = d.id and kind = 'too_dry' and resolved_at is null;
    end if;
    if r.moisture_pct > pl.wet_threshold_pct then
      insert into public.alerts (owner_id, device_id, plant_id, kind, detail)
      values (d.owner_id, d.id, pl.id, 'too_wet', jsonb_build_object('moisture_pct', r.moisture_pct, 'threshold', pl.wet_threshold_pct))
      on conflict (device_id, kind) where resolved_at is null do nothing;
    elsif r.moisture_pct <= pl.wet_threshold_pct - 5 then
      update public.alerts set resolved_at = now() where device_id = d.id and kind = 'too_wet' and resolved_at is null;
    end if;
  end if;

  if v_min is not null then
    if v_min < d.low_battery_mv then
      insert into public.alerts (owner_id, device_id, plant_id, kind, detail)
      values (d.owner_id, d.id, d.plant_id, 'low_battery', jsonb_build_object('vbat_mv', v_min, 'threshold', d.low_battery_mv))
      on conflict (device_id, kind) where resolved_at is null do nothing;
    elsif v_min >= d.low_battery_mv + 100 then
      update public.alerts set resolved_at = now() where device_id = d.id and kind = 'low_battery' and resolved_at is null;
    end if;
  end if;

  -- a report arrived => the device is online again
  update public.alerts set resolved_at = now() where device_id = d.id and kind = 'device_offline' and resolved_at is null;

  -- critical device events become alerts (names are identical by design)
  insert into public.alerts (owner_id, device_id, plant_id, kind, detail)
  select d.owner_id, d.id, d.plant_id, e.type, jsonb_build_object('event_ts', e.ts)
    from public.events e
   where e.device_id = d.id and e.critical and e.received_at >= p_since
  on conflict (device_id, kind) where resolved_at is null do nothing;
end $$;
revoke all on function public.evaluate_alerts(uuid, timestamptz) from public, anon, authenticated;
grant execute on function public.evaluate_alerts(uuid, timestamptz) to service_role;

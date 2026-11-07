-- Local seed (4.B1). Fake data only, fixed UUIDs, relative timestamps. Runs after migrations on `supabase db reset`
-- and in cloud/test.sh. User A = free plan, user B = premium (FR-A06 vs FR-P01). No real people, no secrets.
insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-00000000000a', 'user-a@example.test'),
  ('00000000-0000-0000-0000-00000000000b', 'user-b@example.test');   -- profiles rows come from the on_auth_user_created trigger
update public.profiles set is_premium = true, display_name = 'User B' where id = '00000000-0000-0000-0000-00000000000b';
update public.profiles set display_name = 'User A' where id = '00000000-0000-0000-0000-00000000000a';

insert into public.plants (id, owner_id, name, location_type, soil_type, city) values
  ('10000000-0000-0000-0000-00000000000a', '00000000-0000-0000-0000-00000000000a', 'Basil A', 'house', 'potting', 'Berlin'),
  ('10000000-0000-0000-0000-00000000000b', '00000000-0000-0000-0000-00000000000b', 'Tomato B', 'balcony', 'garden', 'Hamburg');
insert into public.devices (id, hw_id, owner_id, plant_id, claimed_at, last_seen_at) values
  ('20000000-0000-0000-0000-00000000000a', 'nw-a1b2c3d4e5f6', '00000000-0000-0000-0000-00000000000a', '10000000-0000-0000-0000-00000000000a', now(), now()),
  ('20000000-0000-0000-0000-00000000000b', 'nw-b1b2c3d4e5f6', '00000000-0000-0000-0000-00000000000b', '10000000-0000-0000-0000-00000000000b', now(), now());
-- 3 days of 15-minute samples per device (96/day, decision 2.4)
insert into public.readings (device_id, ts, owner_id, plant_id, moisture_pct, moisture_raw, temp_c, rh_pct, lux, vbat_mv)
select d.id, date_trunc('minute', now()) - (g * 15 || ' minutes')::interval, d.owner_id, d.plant_id,
       40 + 10 * sin(g / 12.0), 1800 + g, 21, 55, 800, 3900
from public.devices d, generate_series(0, 287) g;
select public.rollup_readings(now() - interval '4 days');   -- fills readings_hourly for the seed
insert into public.events (device_id, owner_id, plant_id, ts, type, critical) values
  ('20000000-0000-0000-0000-00000000000a', '00000000-0000-0000-0000-00000000000a', '10000000-0000-0000-0000-00000000000a', now() - interval '2 hours', 'wetting', false),
  ('20000000-0000-0000-0000-00000000000b', '00000000-0000-0000-0000-00000000000b', '10000000-0000-0000-0000-00000000000b', now() - interval '2 hours', 'wetting', false);
insert into public.alerts (owner_id, device_id, plant_id, kind) values
  ('00000000-0000-0000-0000-00000000000a', '20000000-0000-0000-0000-00000000000a', '10000000-0000-0000-0000-00000000000a', 'too_dry'),
  ('00000000-0000-0000-0000-00000000000b', '20000000-0000-0000-0000-00000000000b', '10000000-0000-0000-0000-00000000000b', 'too_wet');
insert into public.push_tokens (owner_id, expo_token) values
  ('00000000-0000-0000-0000-00000000000a', 'ExponentPushToken[fake-a]'),
  ('00000000-0000-0000-0000-00000000000b', 'ExponentPushToken[fake-b]');
insert into public.plant_images (plant_id, owner_id, storage_path) values
  ('10000000-0000-0000-0000-00000000000a', '00000000-0000-0000-0000-00000000000a', '00000000-0000-0000-0000-00000000000a/10000000-0000-0000-0000-00000000000a/seed.jpg'),
  ('10000000-0000-0000-0000-00000000000b', '00000000-0000-0000-0000-00000000000b', '00000000-0000-0000-0000-00000000000b/10000000-0000-0000-0000-00000000000b/seed.jpg');
insert into public.tips (plant_id, owner_id, expires_at, content, guardrail_version) values
  ('10000000-0000-0000-0000-00000000000a', '00000000-0000-0000-0000-00000000000a', now() + interval '4 hours', '{"items":[]}', 'seed'),
  ('10000000-0000-0000-0000-00000000000b', '00000000-0000-0000-0000-00000000000b', now() + interval '4 hours', '{"items":[]}', 'seed');
insert into public.api_keys (owner_id, name, prefix, key_hash) values
  ('00000000-0000-0000-0000-00000000000a', 'seed key A', 'nwk_seeA', decode(repeat('aa', 32), 'hex')),
  ('00000000-0000-0000-0000-00000000000b', 'seed key B', 'nwk_seeB', decode(repeat('bb', 32), 'hex'));
insert into public.device_credentials (device_id, token_hash) values
  ('20000000-0000-0000-0000-00000000000a', decode(repeat('a1', 32), 'hex')),
  ('20000000-0000-0000-0000-00000000000b', decode(repeat('b1', 32), 'hex'));
insert into public.claim_tokens (token_hash, user_id, expires_at) values
  (decode(repeat('c1', 16), 'hex'), '00000000-0000-0000-0000-00000000000a', now() + interval '15 minutes'),
  (decode(repeat('c2', 16), 'hex'), '00000000-0000-0000-0000-00000000000b', now() + interval '15 minutes');
insert into public.firmware_releases (version, kind, storage_path, sha256, size_bytes) values
  ('0.0.0-seed', 'fw', 'fw/0.0.0-seed.bin', repeat('0', 64), 1024);

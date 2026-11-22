-- 4.B1 migration 1/3: core schema. VERBATIM COPY of docs/interfaces/db-schema.sql (task 2.4, source of truth).
-- Do NOT edit below the marker; change the source file and re-copy (cloud/test.sh fails on drift).
-- ======== BEGIN db-schema.sql ========
-- Plant Monitor - database schema, DRAFT v0.1 (task 2.4)
-- Target: Supabase Postgres 15+ (EU). Author: Theo (System Architect), 2026-11-04.
-- Status: contract draft for G2. Syntax-checked on a local PostgreSQL 16 with a stubbed
-- `auth` schema (see docs/interfaces/README.md "Verification"). NOT run on Supabase.
-- Builders (Leo, 4.B1) copy this to cloud/supabase/migrations/ when 4.B1 starts; the cloud/
-- scaffold is empty today, so the file lives here and docs/interfaces/ stays the source of truth.
--
-- Requirement citations are in comments: FR-xx / NFR-xx are from Requirements v0.1.
-- Rule (TEAM.md section 6, NFR-06): RLS is enabled on EVERY table. Devices never touch tables;
-- the ingest/claim edge functions use the service role (bypasses RLS) and are the only writers
-- of readings, events, alerts, tips, device_credentials, claim_tokens.
-- "users" in the Plan = Supabase auth.users (identity) + public.profiles (our data).

-- ---------------------------------------------------------------- helpers
create extension if not exists pgcrypto;

create or replace function public.set_updated_at() returns trigger
language plpgsql as $$ begin new.updated_at = now(); return new; end $$;

-- ---------------------------------------------------------------- profiles (FR-A01, FR-P04)
create table public.profiles (
  id           uuid primary key references auth.users(id) on delete cascade,  -- FR-A01 delete account
  display_name text,
  is_premium   boolean not null default false,                                -- FR-P04, ADR-008
  created_at   timestamptz not null default now()
);
alter table public.profiles enable row level security;
create policy profiles_select_own on public.profiles for select using (id = auth.uid());
create policy profiles_update_own on public.profiles for update using (id = auth.uid()) with check (id = auth.uid());
-- no insert policy: row is created by the trigger below. no delete policy: delete via /account.

-- Users may edit their profile but never the premium flag (FR-P04). RLS has no column level,
-- so a trigger guards it; only service role / dashboard (postgres) may change it.
create or replace function public.profiles_guard() returns trigger
language plpgsql as $$
begin
  if new.is_premium is distinct from old.is_premium
     and current_user not in ('postgres', 'service_role', 'supabase_admin') then
    raise exception 'is_premium can only be changed by service role' using errcode = '42501';
  end if;
  return new;
end $$;
create trigger profiles_guard before update on public.profiles
  for each row execute function public.profiles_guard();

create or replace function public.handle_new_user() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  insert into public.profiles (id) values (new.id);
  return new;
end $$;
create trigger on_auth_user_created after insert on auth.users
  for each row execute function public.handle_new_user();

-- true if the calling user has the premium flag (FR-P04, ADR-008). SECURITY DEFINER so that
-- policies on other tables can call it without granting access to profiles internals.
create or replace function public.is_premium() returns boolean
language sql stable security definer set search_path = public as $$
  select coalesce((select p.is_premium from public.profiles p where p.id = auth.uid()), false)
$$;

-- ---------------------------------------------------------------- plants (FR-A04, FR-A06)
create table public.plants (
  id                 uuid primary key default gen_random_uuid(),
  owner_id           uuid not null references public.profiles(id) on delete cascade,
  name               text not null check (length(name) between 1 and 80),
  location_type      text not null check (location_type in ('house','balcony','garden','farm','greenhouse')), -- FR-A04
  area               text check (length(area) <= 80),                       -- room or area, FR-A04
  soil_type          text not null check (soil_type in ('potting','garden','sand','clay','peat','other')),
                     -- [proposed] value list; Mira must map it to the model's soil code (edge-ai-concept 2.2)
  species            text check (length(species) <= 120),                   -- optional, FR-A04
  city               text check (length(city) <= 120),                      -- weather place, FR-A04, FR-P02
  dry_threshold_pct  numeric(4,1) not null default 25 check (dry_threshold_pct between 0 and 100), -- G1: dry < 25 %
  wet_threshold_pct  numeric(4,1) not null default 85 check (wet_threshold_pct between 0 and 100), -- G1: wet > 85 %
  created_at         timestamptz not null default now(),
  updated_at         timestamptz not null default now(),
  check (dry_threshold_pct < wet_threshold_pct)
);
create index plants_owner_idx on public.plants(owner_id);
create trigger plants_updated before update on public.plants for each row execute function public.set_updated_at();
alter table public.plants enable row level security;
create policy plants_all_own on public.plants for all using (owner_id = auth.uid()) with check (owner_id = auth.uid());

-- ---------------------------------------------------------------- devices (FR-A02, FR-A08, FR-D03)
create table public.devices (
  id              uuid primary key default gen_random_uuid(),
  hw_id           text not null unique check (hw_id ~ '^nw-[0-9a-f]{12}$'),  -- label/MQTT identity, from MAC
  owner_id        uuid references public.profiles(id) on delete set null,     -- null = unclaimed/released (FR-A08)
  plant_id        uuid unique references public.plants(id) on delete set null, -- at most one plant per device
  name            text check (length(name) <= 80),
  claimed_at      timestamptz,
  last_seen_at    timestamptz,                                               -- last accepted /ingest, offline rule
  fw_version      text,
  model_version   text,
  fw_target       text,                                                      -- OTA target, null = none (FR-D05)
  model_target    text,
  low_battery_mv  integer not null default 3400 check (low_battery_mv between 3000 and 4250), -- G1: 3.4 V (FR-D06)
  forecast_h      numeric(5,1) check (forecast_h between 0 and 72),          -- latest, UC-08, FR-E01
  forecast_at     timestamptz,
  cal_dry_raw     integer,                                                   -- latest device calibration (4.F5)
  cal_wet_raw     integer,
  cal_at          timestamptz,
  created_at      timestamptz not null default now()
);
create index devices_owner_idx on public.devices(owner_id);
alter table public.devices enable row level security;
create policy devices_select_own on public.devices for select using (owner_id = auth.uid());
-- Users rename / assign a plant via the update policy; protected columns are guarded by a trigger.
create policy devices_update_own on public.devices for update
  using (owner_id = auth.uid())
  with check (owner_id = auth.uid()
    and (plant_id is null or exists (select 1 from public.plants p where p.id = plant_id and p.owner_id = auth.uid())));
create or replace function public.devices_guard() returns trigger
language plpgsql as $$
begin
  if current_user not in ('postgres', 'service_role', 'supabase_admin') and (
       new.hw_id is distinct from old.hw_id or new.owner_id is distinct from old.owner_id
    or new.claimed_at is distinct from old.claimed_at or new.last_seen_at is distinct from old.last_seen_at
    or new.fw_version is distinct from old.fw_version or new.model_version is distinct from old.model_version
    or new.fw_target is distinct from old.fw_target or new.model_target is distinct from old.model_target
    or new.forecast_h is distinct from old.forecast_h or new.forecast_at is distinct from old.forecast_at
    or new.cal_dry_raw is distinct from old.cal_dry_raw or new.cal_wet_raw is distinct from old.cal_wet_raw
    or new.cal_at is distinct from old.cal_at or new.created_at is distinct from old.created_at) then
    raise exception 'device column is server-managed' using errcode = '42501';
  end if;
  return new;
end $$;
create trigger devices_guard before update on public.devices for each row execute function public.devices_guard();
-- no insert/delete policy: rows are created by /device-claim; release is /device-release (FR-A08).

-- Device bearer token, SHA-256 hash only (ADR-004, NFR-06). RLS on, NO policy => service role only.
create table public.device_credentials (
  device_id   uuid primary key references public.devices(id) on delete cascade,
  token_hash  bytea not null unique,        -- sha256(token); token = 32 random bytes, shown once
  created_at  timestamptz not null default now(),
  revoked_at  timestamptz
);
alter table public.device_credentials enable row level security;

-- One-time claim tokens (ADR-002/011). RLS on, no policy => service role only.
create table public.claim_tokens (
  token_hash  bytea primary key,            -- sha256(token); token = 16 random bytes, base64url
  user_id     uuid not null references public.profiles(id) on delete cascade,
  expires_at  timestamptz not null,         -- now() + 15 min [proposed TTL]
  used_at     timestamptz,
  device_id   uuid references public.devices(id) on delete set null
);
alter table public.claim_tokens enable row level security;

-- Firmware / model artefacts for OTA (FR-D05, ADR-009). Service role only; the ingest function
-- turns a row into a signed Storage URL. Integrity = SHA-256 over TLS (G1, A-009); no signature column.
create table public.firmware_releases (
  version         text not null,
  kind            text not null check (kind in ('fw','model')),
  storage_path    text not null,            -- private bucket 'firmware'
  sha256          text not null check (sha256 ~ '^[0-9a-f]{64}$'),
  size_bytes      integer not null check (size_bytes > 0),
  min_battery_mv  integer not null default 3700,   -- [proposed] do not update below this
  created_at      timestamptz not null default now(),
  primary key (kind, version)
);
alter table public.firmware_releases enable row level security;

-- ---------------------------------------------------------------- plant_images (FR-A05)
create table public.plant_images (
  id            uuid primary key default gen_random_uuid(),
  plant_id      uuid not null references public.plants(id) on delete cascade,
  owner_id      uuid not null references public.profiles(id) on delete cascade,
  storage_path  text not null unique,       -- '<owner_id>/<plant_id>/<uuid>.jpg' in private bucket 'plant-photos'
  taken_at      timestamptz not null default now(),   -- date shown in gallery, FR-A05
  created_at    timestamptz not null default now()
);
create index plant_images_plant_idx on public.plant_images(plant_id, taken_at);
alter table public.plant_images enable row level security;
create policy plant_images_all_own on public.plant_images for all
  using (owner_id = auth.uid())
  with check (owner_id = auth.uid() and exists (select 1 from public.plants p where p.id = plant_id and p.owner_id = auth.uid()));
-- Storage policies (bucket 'plant-photos', private): owner folder only (FR-A05, NFR-06).
-- Applied by Supabase in the storage schema; kept as comments here because the schema is Supabase-provided:
--   create policy photos_own on storage.objects for all
--     using (bucket_id = 'plant-photos' and (storage.foldername(name))[1] = auth.uid()::text)
--     with check (bucket_id = 'plant-photos' and (storage.foldername(name))[1] = auth.uid()::text);

-- ---------------------------------------------------------------- readings (FR-D01, FR-D02, FR-D04)
-- Unit of record = one 15-minute sample (decision 2.4; 96 per 24 h). Raw retention 3 months, then hourly roll-up (below) kept 12 months (NFR-13, A-028).
-- owner_id / plant_id are stamped at ingest, so history stays with the owner who had the device
-- when it was recorded (release + re-claim by another user never leaks history, FR-A08).
create table public.readings (
  device_id     uuid not null references public.devices(id) on delete cascade,
  ts            timestamptz not null,        -- sample time, clock-corrected by the server (api: ingest)
  owner_id      uuid not null references public.profiles(id) on delete cascade,
  plant_id      uuid references public.plants(id) on delete set null,
  moisture_pct  real,                        -- relative 0-100 between dry/wet points (edge-ai-concept 2.1)
  moisture_raw  integer,                     -- raw ADC counts, kept for retraining (Req section 5)
  temp_c        real,
  rh_pct        real,
  lux           real,
  vbat_mv       integer,
  plausible     boolean not null default true,  -- false if any value outside the G1 ranges
  received_at   timestamptz not null default now(),
  primary key (device_id, ts),               -- idempotency key (retry-safe, FR-D04)
  -- G1 plausible ranges: see reading_is_plausible(). NULL = sensor failed. The ingest function sets
  -- plausible=false instead of rejecting, so one bad value never loses the rest of the batch.
  constraint readings_vbat_type check (vbat_mv is null or vbat_mv >= 0)
);
create index readings_plant_ts_idx on public.readings(plant_id, ts desc);
create index readings_owner_ts_idx on public.readings(owner_id, ts desc);
alter table public.readings enable row level security;
-- Free users see 7 days (FR-A06), premium users all retained data (FR-P01: 30/90-day history).
-- Enforced here, not only in the app, so direct supabase-js queries cannot bypass it (NFR-06, ADR-008).
create policy readings_select_own on public.readings for select
  using (owner_id = auth.uid() and (ts > now() - interval '7 days' or public.is_premium()));

-- Hourly roll-up of readings (NFR-13, A-028): raw 15-min rows are kept ~3 months, the roll-up 12 months.
-- One row per device and UTC hour, built from PLAUSIBLE raw samples only. Written by rollup_readings()
-- (service_role); users only read. Daily values are a view over this table (readings_daily).
create table public.readings_hourly (
  device_id     uuid not null references public.devices(id) on delete cascade,
  hour          timestamptz not null check (hour = date_trunc('hour', hour)),   -- start of the UTC hour
  owner_id      uuid not null references public.profiles(id) on delete cascade, -- same ownership rule as readings
  plant_id      uuid references public.plants(id) on delete set null,
  n             smallint not null check (n between 1 and 4),                    -- plausible samples in the hour
  moisture_avg  real, moisture_min real, moisture_max real,
  temp_avg      real, rh_avg real, lux_avg real,
  vbat_min_mv   integer,
  primary key (device_id, hour)
);
create index readings_hourly_plant_hour_idx on public.readings_hourly(plant_id, hour desc);
create index readings_hourly_owner_hour_idx on public.readings_hourly(owner_id, hour desc);
alter table public.readings_hourly enable row level security;
create policy readings_hourly_select_own on public.readings_hourly for select
  using (owner_id = auth.uid() and (hour > now() - interval '7 days' or public.is_premium()));

-- Daily values for 30/90-day and 12-month charts (FR-P01): sample-weighted over the hourly rows.
create view public.readings_daily with (security_invoker = true) as
select device_id, owner_id, plant_id, (hour at time zone 'UTC')::date as day, sum(n)::int as n,
       (sum(moisture_avg * n) / nullif(sum(n) filter (where moisture_avg is not null), 0))::real as moisture_avg,
       min(moisture_min) as moisture_min, max(moisture_max) as moisture_max,
       (sum(temp_avg * n) / nullif(sum(n) filter (where temp_avg is not null), 0))::real as temp_avg,
       (sum(rh_avg * n)   / nullif(sum(n) filter (where rh_avg   is not null), 0))::real as rh_avg,
       (sum(lux_avg * n)  / nullif(sum(n) filter (where lux_avg  is not null), 0))::real as lux_avg,
       min(vbat_min_mv) as vbat_min_mv
from public.readings_hourly
group by device_id, owner_id, plant_id, (hour at time zone 'UTC')::date;

-- Plausibility helper used by the ingest function and by tests (G1 ranges, FR-D01).
create or replace function public.reading_is_plausible(
  temp_c real, rh_pct real, lux real, vbat_mv integer, moisture_pct real) returns boolean
language sql immutable as $$
  select (temp_c is null or temp_c between -10 and 60)
     and (rh_pct is null or rh_pct between 0 and 100)
     and (lux is null or lux between 0 and 100000)
     and (vbat_mv is null or vbat_mv between 3000 and 4250)
     and (moisture_pct is null or moisture_pct between 0 and 100)
$$;

-- ---------------------------------------------------------------- events (FR-E02, FR-E03, FR-A07)
create table public.events (
  id           bigint generated always as identity primary key,
  device_id    uuid not null references public.devices(id) on delete cascade,
  owner_id     uuid not null references public.profiles(id) on delete cascade,
  plant_id     uuid references public.plants(id) on delete set null,
  ts           timestamptz not null,
  type         text not null check (type in
               ('wetting','wetting_unexpected','fast_drying','waterlogged','sensor_out_of_soil','sensor_fault')),
               -- names from edge-ai-concept 2.4 (finalised here)
  critical     boolean not null,            -- true: wetting_unexpected, waterlogged, sensor_out_of_soil, sensor_fault
  received_at  timestamptz not null default now(),
  unique (device_id, ts, type)
);
create index events_owner_ts_idx on public.events(owner_id, ts desc);
alter table public.events enable row level security;
create policy events_select_own on public.events for select using (owner_id = auth.uid());

-- ---------------------------------------------------------------- alerts (FR-A07, FR-D06)
-- One OPEN alert per (device, kind): fires once until resolved (dedupe).
create table public.alerts (
  id           bigint generated always as identity primary key,
  owner_id     uuid not null references public.profiles(id) on delete cascade,
  device_id    uuid not null references public.devices(id) on delete cascade,
  plant_id     uuid references public.plants(id) on delete set null,
  kind         text not null check (kind in
               ('too_dry','too_wet','low_battery','device_offline',
                'wetting_unexpected','waterlogged','sensor_out_of_soil','sensor_fault')),
  opened_at    timestamptz not null default now(),
  resolved_at  timestamptz,
  notified_at  timestamptz,                 -- set by push dispatcher; null = push pending
  detail       jsonb not null default '{}'
);
create unique index alerts_one_open on public.alerts(device_id, kind) where resolved_at is null;
create index alerts_owner_idx on public.alerts(owner_id, opened_at desc);
alter table public.alerts enable row level security;
create policy alerts_select_own on public.alerts for select using (owner_id = auth.uid());

create table public.push_tokens (
  id          uuid primary key default gen_random_uuid(),
  owner_id    uuid not null references public.profiles(id) on delete cascade,
  expo_token  text not null unique,         -- Expo push token; payload never carries sensor data (L-10)
  created_at  timestamptz not null default now()
);
alter table public.push_tokens enable row level security;
create policy push_tokens_all_own on public.push_tokens for all using (owner_id = auth.uid()) with check (owner_id = auth.uid());

-- ---------------------------------------------------------------- tips (FR-P02, FR-P04)
create table public.tips (
  id                 uuid primary key default gen_random_uuid(),
  plant_id           uuid not null references public.plants(id) on delete cascade,
  owner_id           uuid not null references public.profiles(id) on delete cascade,
  generated_at       timestamptz not null default now(),
  expires_at         timestamptz not null,           -- cache for a few hours (architecture section 5)
  content            jsonb not null,                 -- {"items":[{"id","category","text"}]} after guardrails
  weather            jsonb,                          -- forecast snapshot used (traceability of "tips change with weather")
  model              text,                           -- LLM id
  guardrail_version  text not null                   -- version of the deterministic rule layer (FR-P02)
);
create index tips_plant_idx on public.tips(plant_id, generated_at desc);
alter table public.tips enable row level security;
create policy tips_select_own_premium on public.tips for select using (owner_id = auth.uid() and public.is_premium());
-- writes: tips edge function (service role) only.

-- ---------------------------------------------------------------- api_keys for MCP (FR-P03, NFR-06)
create table public.api_keys (
  id           uuid primary key default gen_random_uuid(),
  owner_id     uuid not null references public.profiles(id) on delete cascade,
  name         text not null check (length(name) between 1 and 60),
  prefix       text not null,                         -- first 8 chars of the key, for display
  key_hash     bytea not null unique,                 -- sha256(key); key = 'nwk_' + 32 random bytes base64url, shown once
  created_at   timestamptz not null default now(),
  last_used_at timestamptz,
  revoked_at   timestamptz                            -- revoked => next MCP call fails (FR-P03)
);
create index api_keys_owner_idx on public.api_keys(owner_id);
alter table public.api_keys enable row level security;
create policy api_keys_select_own on public.api_keys for select using (owner_id = auth.uid());
revoke select on public.api_keys from anon, authenticated;
grant select (id, owner_id, name, prefix, created_at, last_used_at, revoked_at) on public.api_keys to authenticated;
-- create / revoke only through the /api-keys edge function (service role).

-- MCP: resolve a key to its owner. Callable by service role only; the MCP function then runs the
-- read-only RPCs below with p_owner set from this result, never a broad service-role query (ADR-007).
create or replace function public.mcp_resolve_key(p_key_hash bytea) returns uuid
language plpgsql security definer set search_path = public as $$
declare v_owner uuid;
begin
  update public.api_keys k set last_used_at = now()
   where k.key_hash = p_key_hash and k.revoked_at is null
   returning k.owner_id into v_owner;
  if v_owner is null then return null; end if;                       -- unknown or revoked
  if not coalesce((select is_premium from public.profiles where id = v_owner), false) then
    raise exception 'premium_required' using errcode = 'P0001';       -- FR-P04
  end if;
  return v_owner;
end $$;
revoke all on function public.mcp_resolve_key(bytea) from public, anon, authenticated;
grant execute on function public.mcp_resolve_key(bytea) to service_role;

-- ---------------------------------------------------------------- views (app + MCP)
-- Current state per plant. security_invoker => RLS of the caller applies (PG15+).
create view public.plant_status with (security_invoker = true) as
select p.id as plant_id, p.owner_id, p.name, p.location_type, p.area, p.soil_type, p.species, p.city,
       p.dry_threshold_pct, p.wet_threshold_pct,
       d.id as device_id, d.name as device_name, d.last_seen_at, d.forecast_h, d.forecast_at,
       r.ts as reading_ts, r.moisture_pct, r.temp_c, r.rh_pct, r.lux, r.vbat_mv,
       coalesce((select array_agg(a.kind order by a.opened_at) from public.alerts a
                  where a.device_id = d.id and a.resolved_at is null), '{}') as open_alerts
from public.plants p
left join public.devices d on d.plant_id = p.id
left join lateral (select * from public.readings x where x.device_id = d.id and x.plausible
                    order by x.ts desc limit 1) r on true;

-- ---------------------------------------------------------------- alert evaluation (FR-A07, FR-D06)
-- Called by the ingest function after inserting a batch; p_since = the request's start time (picks up the batch's events). Thresholds: plants.dry/wet (default 25 / 85),
-- devices.low_battery_mv (default 3400). Resolve with hysteresis [proposed]: 5 points / 100 mV.
create or replace function public.evaluate_alerts(p_device uuid, p_since timestamptz) returns void
language plpgsql security definer set search_path = public as $$
declare d public.devices; pl public.plants; r public.readings;
begin
  select * into d from public.devices where id = p_device;
  if d.owner_id is null then return; end if;
  select * into pl from public.plants where id = d.plant_id;
  select * into r from public.readings where device_id = p_device and plausible order by ts desc limit 1;
  if r.ts is null then return; end if;

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

  if r.vbat_mv is not null then
    if r.vbat_mv < d.low_battery_mv then
      insert into public.alerts (owner_id, device_id, plant_id, kind, detail)
      values (d.owner_id, d.id, d.plant_id, 'low_battery', jsonb_build_object('vbat_mv', r.vbat_mv, 'threshold', d.low_battery_mv))
      on conflict (device_id, kind) where resolved_at is null do nothing;
    elsif r.vbat_mv >= d.low_battery_mv + 100 then
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

-- Offline = 3 missed hourly reports (G1, A-008 point 21): last report older than 3 h + 10 min jitter grace [grace proposed].
create or replace function public.scan_offline() returns integer
language plpgsql security definer set search_path = public as $$
declare n integer;
begin
  with ins as (
    insert into public.alerts (owner_id, device_id, plant_id, kind, detail)
    select d.owner_id, d.id, d.plant_id, 'device_offline', jsonb_build_object('last_seen_at', d.last_seen_at)
      from public.devices d
     where d.owner_id is not null and d.last_seen_at is not null
       and d.last_seen_at < now() - interval '3 hours 10 minutes'
    on conflict (device_id, kind) where resolved_at is null do nothing
    returning 1)
  select count(*) into n from ins;
  return n;
end $$;
revoke all on function public.scan_offline() from public, anon, authenticated;
grant execute on function public.scan_offline() to service_role;

-- Delete a plant (FR-A08, NFR-07; Arsany A-022): removes the plant, its photos (rows) and its readings,
-- events, alerts and tips. The sensor stays CLAIMED (devices.plant_id is set null by the FK) and is released
-- separately via POST /device-release. The app must warn first and offer the JSON/CSV export (GET /export).
-- Returns the storage paths of the deleted photos: the caller (edge function or app) must delete those
-- objects from bucket 'plant-photos', because SQL cannot remove Storage objects safely.
-- Readings recorded before the sensor was assigned to this plant have plant_id null and are NOT touched.
create or replace function public.delete_plant(p_plant uuid) returns jsonb
language plpgsql security definer set search_path = public as $$
declare
  v_uid     uuid := auth.uid();
  v_paths   text[];
  v_readings bigint; v_events bigint; v_alerts bigint;
begin
  if v_uid is null then raise exception 'not authenticated' using errcode = '28000'; end if;
  if not exists (select 1 from public.plants where id = p_plant and owner_id = v_uid) then
    raise exception 'plant not found' using errcode = 'P0002';   -- same answer for unknown and foreign ids
  end if;
  select coalesce(array_agg(storage_path), '{}') into v_paths from public.plant_images where plant_id = p_plant;
  with d as (delete from public.readings where plant_id = p_plant and owner_id = v_uid returning 1) select count(*) into v_readings from d;
  delete from public.readings_hourly where plant_id = p_plant and owner_id = v_uid;   -- roll-up rows (NFR-07)
  with d as (delete from public.events   where plant_id = p_plant and owner_id = v_uid returning 1) select count(*) into v_events   from d;
  with d as (delete from public.alerts   where plant_id = p_plant and owner_id = v_uid returning 1) select count(*) into v_alerts   from d;
  delete from public.plants where id = p_plant and owner_id = v_uid;   -- cascades plant_images, tips; devices.plant_id -> null
  return jsonb_build_object('plant_id', p_plant, 'photo_paths', to_jsonb(v_paths),
                            'deleted', jsonb_build_object('readings', v_readings, 'events', v_events, 'alerts', v_alerts,
                                                          'photos', coalesce(array_length(v_paths, 1), 0)));
end $$;
revoke all on function public.delete_plant(uuid) from public, anon;
grant execute on function public.delete_plant(uuid) to authenticated;

-- Setup "save plant" (4.A4c, FR-A03, FR-A04, NFR-06, FR-A08): one call inserts the plant AND points the device at it, or does neither.
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

-- Retention (NFR-13, A-028): raw readings ~3 months, hourly roll-up 12 months. Replaces purge_old_readings().
-- raw_months is the single knob (default 3). Order matters: complete hours are rolled up FIRST, then raw rows
-- older than the cut-off are deleted, so no data is lost between the two steps. Idempotent (upsert).
create or replace function public.rollup_readings(p_from timestamptz default null, p_to timestamptz default null) returns bigint
language plpgsql security definer set search_path = public as $$
declare v_n bigint;
begin
  with agg as (
    select device_id, date_trunc('hour', ts) as hour, owner_id, (array_agg(plant_id order by ts desc))[1] as plant_id,
           count(*) as n, avg(moisture_pct) as m_avg, min(moisture_pct) as m_min, max(moisture_pct) as m_max,
           avg(temp_c) as t_avg, avg(rh_pct) as rh_avg, avg(lux) as lux_avg, min(vbat_mv) as vbat_min
    from public.readings
    where plausible
      and ts >= date_trunc('hour', coalesce(p_from, now() - interval '2 days'))
      and ts <  least(date_trunc('hour', now()), coalesce(p_to, 'infinity'))   -- complete hours only
    group by device_id, date_trunc('hour', ts), owner_id
  ), up as (
    insert into public.readings_hourly(device_id, hour, owner_id, plant_id, n, moisture_avg, moisture_min, moisture_max,
                                       temp_avg, rh_avg, lux_avg, vbat_min_mv)
    select device_id, hour, owner_id, plant_id, n, m_avg, m_min, m_max, t_avg, rh_avg, lux_avg, vbat_min from agg
    on conflict (device_id, hour) do update set
      owner_id = excluded.owner_id, plant_id = excluded.plant_id, n = excluded.n,
      moisture_avg = excluded.moisture_avg, moisture_min = excluded.moisture_min, moisture_max = excluded.moisture_max,
      temp_avg = excluded.temp_avg, rh_avg = excluded.rh_avg, lux_avg = excluded.lux_avg, vbat_min_mv = excluded.vbat_min_mv
      where excluded.n >= public.readings_hourly.n          -- never overwrite with fewer samples (raw partly deleted)
    returning 1)
  select count(*) into v_n from up;
  return v_n;
end $$;
revoke all on function public.rollup_readings(timestamptz, timestamptz) from public, anon, authenticated;
grant execute on function public.rollup_readings(timestamptz, timestamptz) to service_role;

create or replace function public.apply_retention(raw_months int default 3, rollup_months int default 12) returns jsonb
language plpgsql security definer set search_path = public as $$
declare v_rolled bigint; v_raw bigint; v_hourly bigint; v_cut timestamptz := date_trunc('hour', now() - make_interval(months => raw_months));  -- whole hours only
begin
  -- roll up every raw hour that is about to expire (oldest raw row .. cut-off + 1 day), so missed nights lose nothing
  v_rolled := public.rollup_readings((select min(ts) from public.readings), v_cut + interval '1 day');
  with d as (delete from public.readings where ts < v_cut returning 1) select count(*) into v_raw from d;
  with d as (delete from public.readings_hourly where hour < now() - make_interval(months => rollup_months) returning 1)
  select count(*) into v_hourly from d;
  return jsonb_build_object('rolled_up', v_rolled, 'raw_deleted', v_raw, 'hourly_deleted', v_hourly);
end $$;
revoke all on function public.apply_retention(int, int) from public, anon, authenticated;
grant execute on function public.apply_retention(int, int) to service_role;

-- Schedules (Supabase pg_cron; enabled in 4.B1, not executed in the local syntax check):
--   select cron.schedule('nw-offline-scan', '*/5 * * * *', 'select public.scan_offline()');
--   select cron.schedule('nw-rollup',       '5 * * * *',   'select public.rollup_readings()');        -- hourly, last 2 days
--   select cron.schedule('nw-retention',    '17 3 * * *',  'select public.apply_retention()');       -- nightly: roll up, then delete

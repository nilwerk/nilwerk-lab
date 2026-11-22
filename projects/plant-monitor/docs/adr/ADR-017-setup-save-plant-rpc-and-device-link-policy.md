# ADR-017: Setup "save plant" as one RPC, and the plant check in devices_update_own (4.A4c)

Status: Proposed, for the architect to accept together with the contract change (Theo) · Date: 2026-11-22 · Deciders: Theo (architect, contract); Arsany (owner; confirmed on 2026-11-22 that no Supabase environment has applied migration 20261107000001) · Amends: `docs/interfaces/db-schema.sql` (`devices_update_own`; new `create_plant_and_link_device`), and migration `cloud/supabase/migrations/20261107000001_core_schema.sql` (byte-identical copy of the same two blocks). Migration `20261108000005_devices_plant_check.sql` is on main and not changed here.

## Context
Setup's "Save plant" (FR-A03 setup flow, FR-A04 plant fields) has to create the plant and point the sensor at it. Two separate client calls (insert the plant, then set `devices.plant_id`) can leave an orphan plant or a plant the sensor never got. The app talks to Supabase through PostgREST with the user's JWT, which has no multi-statement transaction.

The owner-isolation rules (NFR-06) already exist: `devices` and `plants` have owner-scoped RLS, and migration 20261108000005 (4.B2 security fix) stops a user from pointing their device at another user's plant. The contract draft `db-schema.sql` still had the old, weaker `devices_update_own` clause, so it did not match the migration.

## Decision
1. **One RPC does the save.** `public.create_plant_and_link_device(p_device uuid, p_name, p_location_type, p_area, p_soil_type, p_species, p_city, p_move boolean default false) returns uuid`:
   - `language plpgsql security definer set search_path = public`; RLS does not apply inside, so the owner checks are explicit.
   - `auth.uid()` must not be null (`28000`). The device must be owned by `auth.uid()`; an unknown and a foreign device get the same answer (`P0002`).
   - If the device already has a plant and `p_move` is false, it raises `P0005`. A sensor is never moved silently. The app sets `p_move` only after the user chooses "move".
   - It inserts the plant with `owner_id = auth.uid()`, sets `devices.plant_id` for the owned device, and returns the plant id. Both writes are one transaction: if the link fails, the plant insert is rolled back.
   - `revoke all ... from public, anon`; `grant execute ... to authenticated`.
2. **`devices_update_own` gets the plant check.** `with check` adds `plant_id is null or the plant belongs to auth.uid()`. This is the same clause as migration 20261108000005; the contract file now says what the database enforces.
3. **Migration 1 is edited in place.** The owner confirmed on 2026-11-22 that no Supabase environment has applied `20261107000001_core_schema.sql`. The contract file and migration 1 stay byte-identical for the RPC and the policy (the drift guard checks this).
4. **Condition for item 3.** If any environment has applied migration 1, this change must go into a new migration instead (the pattern of 20261108000005), and the drift guard must be updated with it. Do not edit an applied migration.

## Requirements served
FR-A03 (the setup flow's plant step saves the plant and the sensor link), FR-A04 (the six plant fields are written), NFR-06 (plant and device writes are limited to the signed-in owner). FR-A08 (edit, remove, release) is not served by this RPC or this policy and is not cited for them.

## Alternatives
- **Two client calls** (insert, then update the device): rejected, because a failure between them leaves an orphan plant or an unlinked sensor, and PostgREST cannot join them in one transaction.
- **Silent move on save:** rejected. The user decides whether a sensor moves (N2 in the PR review); the RPC refuses it (`P0005`).
- **A new migration for the RPC now:** not chosen while no environment has applied migration 1. Item 4 is the rule if that changes.

## Consequences
- The RPC and the policy are tested only on local Postgres (`cloud/test/rls_isolation.sql`, section 2b: foreign device refused, silent move refused, confirmed move keeps the old plant). They are **not** verified against a live Supabase project. Live verification is still open.
- A confirmed move leaves the old plant without a sensor; its readings stay with it.
- Any later change to these two blocks must be made in `db-schema.sql` and migration 1 together.
- Traceability: `docs/traceability.md` row for FR-A03 / FR-A04 / NFR-06 (task 4.A4c) cites this ADR.

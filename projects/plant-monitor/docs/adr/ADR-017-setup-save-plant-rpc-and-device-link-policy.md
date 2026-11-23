# ADR-017: Setup "save plant" as one RPC, and the plant check in devices_update_own (4.A4c)

Status: Accepted (accepted by Theo (System Architect) on merge of PR #159) · Date: 2026-11-22 · Deciders: Theo (architect, contract); Arsany (owner; decision C6, option B, on 2026-11-22) · Amends: `docs/interfaces/db-schema.sql` (`devices_update_own`; new `create_plant_and_link_device`) and adds migration `cloud/supabase/migrations/20261122000009_setup_save_plant_rpc.sql` (the same two blocks). Migration `20261107000001_core_schema.sql` is not changed (restored to its origin/main bytes). Migration `20261108000005_devices_plant_check.sql` is on main and not changed here.

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
3. **The change ships as a new migration, not an edit of migration 1.** `cloud/supabase/migrations/20261122000009_setup_save_plant_rpc.sql` holds items 1 and 2. Migration `20261107000001_core_schema.sql` is restored to its origin/main bytes (its sha256 is pinned in `cloud/test.sh`). Reason: `cloud/README.md` "Migration rules" freezes migration 1 once it is pushed to a real project, and `cloud/README.md` records that the 6 migrations were deployed to `nilwerk-cloud` on 2026-11-16. The new file's `devices_update_own` is the same clause as migration 20261108000005; `drop policy if exists` + `create policy` gives the same definition, so the policy does not change in effect.
4. **The contract file carries the same change.** `docs/interfaces/db-schema.sql` contains both blocks and must produce the same public schema as migration 1 plus `20261122000009`. `cloud/test.sh` (section 0b) checks this with `pg_dump --schema-only` of both databases.

## Requirements served
FR-A03 (the setup flow's plant step saves the plant and the sensor link), FR-A04 (the six plant fields are written), NFR-06 (plant and device writes are limited to the signed-in owner). FR-A08 (edit, remove, release) is not served by this RPC or this policy and is not cited for them.

## Alternatives
- **Two client calls** (insert, then update the device): rejected, because a failure between them leaves an orphan plant or an unlinked sensor, and PostgREST cannot join them in one transaction.
- **Silent move on save:** rejected. The user decides whether a sensor moves (N2 in the PR review); the RPC refuses it (`P0005`).
- **Edit migration 1 in place:** rejected by owner decision C6. Migration 1 is frozen after its push, and an edit would make the repo file differ from the applied migration.

## Consequences
- The RPC and the policy are tested only on local Postgres (`cloud/test/rls_isolation.sql`, section 2b: foreign device refused, silent move refused, confirmed move keeps the old plant). They are **not** verified against a live Supabase project. Live verification is still open.
- A confirmed move leaves the old plant without a sensor; its readings stay with it.
- Any later change to these two blocks must be made in `db-schema.sql` and in a new migration file together; migration 1 is not edited.
- Traceability: `docs/traceability.md` row for FR-A03 / FR-A04 / NFR-06 (task 4.A4c) cites this ADR.

## Migration check
Recorded for the owner's decision (C6). The change is placed in the new migration above (Decision 3); migration 1 is restored.
- **Rule.** `cloud/README.md` "Migration rules": migration 1 is frozen once it is pushed to any real project; later changes are new migration files.
- **Recorded deploy.** `cloud/README.md` says the 6 migrations were deployed to the project `nilwerk-cloud` on 2026-11-16. Migration 1 is therefore treated as applied. This is not checked against the live project in this change; no live Supabase change was made.
- **Check on each Supabase project (nilwerk-cloud and any other), read-only, still open:**
  1. Applied migration list: `select version, name from supabase_migrations.schema_migrations order by version;` (or the Supabase MCP `list_migrations`). Expect `20261107000001` listed. `20261122000009` is listed only after it is applied.
  2. After `20261122000009` is applied: `select polname, pg_get_expr(polwithcheck, polrelid) from pg_policy where polname = 'devices_update_own';` and `select proname from pg_proc where proname = 'create_plant_and_link_device';`. Compare with the file; record any difference.
  3. Record the project ref, the date and the result. Never record keys.
- **Applying the new migration** to any project is a separate owner step (with Theo). Nothing in this ADR says it is applied.

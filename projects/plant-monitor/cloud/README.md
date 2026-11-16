# Plant Monitor cloud backend (tasks 4.B1, 4.B2)

Supabase scaffold implementing the merged 2.4 contract. **Source of truth for the schema:**
[`../docs/interfaces/db-schema.sql`](../docs/interfaces/db-schema.sql) (+ `openapi.yaml`). Migration 1 is a verbatim copy; `test.sh` fails on drift.

| Path | What |
|---|---|
| `supabase/config.toml` | local Supabase config (no secrets) |
| `supabase/migrations/..01_core_schema.sql` | all 14 tables, RLS on every one, `delete_plant` RPC, `readings_hourly` roll-up, `apply_retention`, alert functions (FR-A08, FR-A06, FR-P01, FR-P04, NFR-06/07/13) |
| `supabase/migrations/..02_schedules.sql` | pg_cron: offline scan 5 min, roll-up hourly, retention nightly (fails loudly without pg_cron; test.sh sets `nilwerk.allow_no_cron=on`) |
| `supabase/migrations/..03_storage.sql` | private buckets `plant-photos`, `firmware`, owner-folder policy (FR-A05) |
| `supabase/seed.sql` | local fake data: user A (free), user B (premium), one row per table |
| `test.sh`, `test/` | CI-friendly tests (below) |

## Edge functions (task 4.B2: device claim + ingest)
TypeScript, no npm dependencies (Deno on Supabase, Node 22.6+ for tests). Contract: [`../docs/interfaces/openapi.yaml`](../docs/interfaces/openapi.yaml) + `device-report.schema.json`.

| Function | Path | Caller | Does | Requirements |
|---|---|---|---|---|
| `claim-token` | `POST /claim-token` | app, user JWT | one-time claim token (16 bytes, 15 min, single use, SHA-256 stored, max 10 open) | FR-D03, FR-A03, FR-A02, NFR-06 |
| `device-claim` | `POST /device-claim` | sensor | claim token -> device row + per-device token (32 bytes hex, shown once, **SHA-256 stored**) | FR-D03, FR-A03, FR-A08, NFR-06 |
| `delete-account` | `DELETE /account` (4.B2b) | app, user JWT (`verify_jwt=false`, checked in the function with `auth.getUser`) | body `{"confirm":"DELETE"}`; releases + revokes the user's devices (SQL `release_account_devices`, migration `..0006`), deletes Storage photos under `<uid>/`, deletes the auth user (FK cascade erases the rest). Idempotent; 500 before the auth delete on any failure so a retry is safe. The user is only the token's user, never from the body | FR-A01, FR-A08, NFR-07, NFR-06 |
| `ingest` | `POST /ingest` | sensor, bearer device token | up to 192 buffered samples (96 = 24 h offline, FR-D04) + events; idempotent on (device, ts); returns time, config | FR-D01, FR-D02, FR-D04, FR-A07, FR-E03, NFR-04, NFR-06 |

* `supabase/functions/_shared/lib.ts` hashing + report validation, `handlers.ts` request logic, `supabase.ts` the only Supabase-specific file (`env.ts` holds the testable key-name fallback), `<name>/index.ts` Deno entry points.
* The data logic is in SQL (`migrations/20261108000004_device_api.sql`: `issue_claim_token`, `device_claim`, `ingest_batch`, `device_config`; `..0006_delete_account.sql`: `release_account_devices`), executable by `service_role` only. The edge functions pass SHA-256 digests, never plaintext tokens. A caller never names a device: the device is the owner of the token (device A cannot write device B).
* **Not built** (marked `[not in 4.B2]` in the OpenAPI): rate limits (429 on `/ingest`, `/device-claim`), push dispatch, OTA manifest (`fw_target`/`model_target` are always `null`), `/device-release`, other app endpoints. `delete-account`: Storage listing/removal and `auth.admin.deleteUser` in `supabase.ts` are **never run against a live project** (the tests stub Storage and Auth); Deno was not run either. Tips, analytics, MCP are 4.B3-4.B5.
* Batch size: the contract (schema, ADR-013) allows 192 samples per request; the task text said 96. 96 (24 h of buffer, FR-D04) is accepted, 193+ gets 413.

## Run the tests (no Docker, no account)
```bash
projects/plant-monitor/cloud/test.sh                  # starts a throw-away local PostgreSQL 15+, needs initdb/pg_ctl/psql
DATABASE_URL=postgres://postgres:postgres@localhost:5432/postgres projects/plant-monitor/cloud/test.sh   # or an existing superuser server
```
It checks: migration 1 == 2.4 schema file; RLS enabled on every table and user A cannot read, update, delete or forge
rows of user B on each table (`test/rls_isolation.sql`); retention/roll-up (`test/retention.sql`, A-028: raw ~3 months,
hourly roll-up 12 months); the Architect's `db-schema.test.sql` on the migrated DB; the edge functions end to end against that DB (`test/functions/api.test.ts`: claim, hash-only storage, 96-sample batch, replay idempotency, token isolation A vs B, revoked/released tokens, API roles locked out of the functions); `test/openapi_check.py` (code == OpenAPI; needs PyYAML) and Node >= 22.6.
`test/mutation.sh` is the mutation check: 17 one-line mutants of the token-hash, auth, claim and idempotency logic, each must make the tests fail (`NW_ONLY=api test.sh` is its quick mode). A stub `auth` schema and the roles
`anon/authenticated/service_role` replace what Supabase provides (`test/stub_auth.sql`, `test/grants.sql`).

## Run the full stack locally
Needs Docker and the [Supabase CLI](https://supabase.com/docs/guides/cli): `cd projects/plant-monitor/cloud && supabase start && supabase db reset`
(applies migrations + seed; Studio on http://localhost:54323). **Not run in the agent session** (no Docker there).

## Migration rules
- Migration 1 is the 2.4 schema as of 2026-11-07. **Once it is pushed to any real project it is frozen**: every later schema change is a NEW migration file (and an update to `docs/interfaces/db-schema.sql` so the contract stays current). From then on the drift guard in `test.sh` must compare the cumulative state (migrations applied in order vs. the schema file, e.g. via `pg_dump --schema-only` of both), not the byte copy of migration 1. Until the first push, migration 1 may still be re-copied.
- `seed.sql` inserts into `auth.users(id, email)`: **unverified against real Supabase** (local test uses a stub table; the real table has more columns/triggers). Check with `supabase db reset` before relying on it.

## Production (not done here)
One free Supabase project in an EU region (A-025 zero-cost rule, NFR-07), e.g. Frankfurt. Creating it, enabling `pg_cron`
and pushing migrations is Arsany's step (account, terms). Secrets by name only, never committed. `supabase/functions/_shared/supabase.ts` reads `SUPABASE_URL` plus, in this order, `SUPABASE_SECRET_KEY` then `SUPABASE_SERVICE_ROLE_KEY`, and `SUPABASE_PUBLISHABLE_KEY` then `SUPABASE_ANON_KEY` (resolution in `_shared/env.ts`, unit-tested; if neither name of a pair exists the error names both). **Observed, reported by the Lead after the 2026-11-16 deploy (not re-checked by Sana, no access to the live project):** the hosted function runtime injected the legacy names `SUPABASE_SERVICE_ROLE_KEY` / `SUPABASE_ANON_KEY`, so the fallback is needed there; the new names (A-035) win when set, e.g. locally. The deployed `supabase.ts` includes this fallback (per the Lead; comments stripped, otherwise equal to the repo). The project is `nilwerk-cloud`; the Lead deployed the 6 migrations and 4 functions (`claim-token`, `ingest`, `device-claim`, `delete-account`) through the connector, which cannot read the secret key. Pushing migrations and deploying are done; the deployed files had their comments stripped, the repo copy keeps them. After pushing migrations run `select jobname, schedule from cron.job;` and expect `nw-offline-scan`, `nw-rollup`, `nw-retention`. Free tier pauses on inactivity (unverified, see `docs/stack-and-costs.md`).

## Live smoke test (NOT RUN)
Procedure for Arsany / the Lead against `nilwerk-cloud`. Nothing below has been executed; no agent has run the functions on the live project. Use a throwaway user and delete it at the end. Set `URL` (project URL) and `PUB` (publishable/anon key) in your shell; never paste keys into the repo, chat or logs.
1. **Sign up** a throwaway user (e.g. `smoke+<date>@<your-domain>`): `curl -s "$URL/auth/v1/signup" -H "apikey: $PUB" -H 'Content-Type: application/json' -d '{"email":"...","password":"..."}'`. If email confirmation is on, confirm it, then sign in via `/auth/v1/token?grant_type=password`. Keep `access_token` as `JWT`. Expect 200 and a user id.
2. **claim-token**: `curl -s -X POST "$URL/functions/v1/claim-token" -H "Authorization: Bearer $JWT" -H "apikey: $PUB"`. Expect 200 with a one-time claim token (valid 15 min). Without the header expect 401.
3. **device-claim** (as the device, no user JWT): `POST $URL/functions/v1/device-claim` with the claim token and a made-up `hw_id` as in `docs/interfaces/openapi.yaml`. Expect 200 with a device token. Repeating with the same claim token must fail (single use).
4. **ingest**: `POST $URL/functions/v1/ingest` with `Authorization: Bearer <device token>` and the body `docs/interfaces/fixtures/device-report.valid.json`. Expect 200; repeat it and expect the same rows, not duplicates (idempotent). Check in the SQL editor that `readings` has the rows for that device and the token columns hold SHA-256 digests, not the plaintext token.
5. **delete-account**: `curl -s -X DELETE "$URL/functions/v1/delete-account" -H "Authorization: Bearer $JWT" -H "apikey: $PUB" -H 'Content-Type: application/json' -d '{"confirm":"DELETE"}'`. Expect 204; then the user, plant, reading and photo rows are gone and the device token from step 3 returns 401 on `ingest`. A second call returns 204 or 401, never 500.
6. If any step returns 500, read the function logs (Dashboard > Edge Functions > Logs); a "missing environment variable: set ... or ..." message means neither key name is available in the runtime. Record the result (pass/fail per step, no secrets) in the Agent Log.

## Not here yet
Auth UI, deployment, rate limits, OTA manifest, `/device-release` and the remaining app endpoints. No `package.json` in `cloud/` on purpose: its presence switches on the CI `cloud` job, which applies migrations to a plain Postgres without the `auth` schema and would fail; the `cloud-db` job runs `test.sh`, which now also runs the edge function tests.

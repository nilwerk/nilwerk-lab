# Plant Monitor cloud backend (task 4.B1)

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

## Run the tests (no Docker, no account)
```bash
projects/plant-monitor/cloud/test.sh                  # starts a throw-away local PostgreSQL 15+, needs initdb/pg_ctl/psql
DATABASE_URL=postgres://postgres:postgres@localhost:5432/postgres projects/plant-monitor/cloud/test.sh   # or an existing superuser server
```
It checks: migration 1 == 2.4 schema file; RLS enabled on every table and user A cannot read, update, delete or forge
rows of user B on each table (`test/rls_isolation.sql`); retention/roll-up (`test/retention.sql`, A-028: raw ~3 months,
hourly roll-up 12 months); the Architect's `db-schema.test.sql` on the migrated DB. A stub `auth` schema and the roles
`anon/authenticated/service_role` replace what Supabase provides (`test/stub_auth.sql`, `test/grants.sql`).

## Run the full stack locally
Needs Docker and the [Supabase CLI](https://supabase.com/docs/guides/cli): `cd projects/plant-monitor/cloud && supabase start && supabase db reset`
(applies migrations + seed; Studio on http://localhost:54323). **Not run in the agent session** (no Docker there).

## Migration rules
- Migration 1 is the 2.4 schema as of 2026-11-07. **Once it is pushed to any real project it is frozen**: every later schema change is a NEW migration file (and an update to `docs/interfaces/db-schema.sql` so the contract stays current). From then on the drift guard in `test.sh` must compare the cumulative state (migrations applied in order vs. the schema file, e.g. via `pg_dump --schema-only` of both), not the byte copy of migration 1. Until the first push, migration 1 may still be re-copied.
- `seed.sql` inserts into `auth.users(id, email)`: **unverified against real Supabase** (local test uses a stub table; the real table has more columns/triggers). Check with `supabase db reset` before relying on it.

## Production (not done here)
One free Supabase project in an EU region (A-025 zero-cost rule, NFR-07), e.g. Frankfurt. Creating it, enabling `pg_cron`
and pushing migrations is Arsany's step (account, terms). Secrets by name only: `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`,
`SUPABASE_SERVICE_ROLE_KEY` (GitHub/Supabase secrets, never committed). After pushing migrations run `select jobname, schedule from cron.job;` and expect `nw-offline-scan`, `nw-rollup`, `nw-retention`. Free tier pauses on inactivity (unverified, see `docs/stack-and-costs.md`).

## Not here yet
Edge functions / ingest + claim API (4.B2), auth UI, deployment. No `package.json` on purpose: its presence switches on the CI
`cloud` job, which applies migrations to a plain Postgres without the `auth` schema and would fail (see PR note; Kai to wire `test.sh` into CI).

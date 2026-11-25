# Plant Monitor cloud backend (tasks 4.B1, 4.B2, 4.B3 slice 1)

Supabase scaffold implementing the merged 2.4 contract. **Source of truth for the schema:**
[`../docs/interfaces/db-schema.sql`](../docs/interfaces/db-schema.sql) (+ `openapi.yaml`). Migration 1 is a verbatim copy of the 2.4 schema as applied; `test.sh` pins its sha256 and checks that the contract file equals migration 1 plus the 4.A4c migration.

| Path | What |
|---|---|
| `supabase/config.toml` | local Supabase config (no secrets) |
| `supabase/migrations/..01_core_schema.sql` | all 14 tables, RLS on every one, `delete_plant` RPC, `readings_hourly` roll-up, `apply_retention`, alert functions (FR-A08, FR-A06, FR-P01, FR-P04, NFR-06/07/13) |
| `supabase/migrations/..02_schedules.sql` | pg_cron: offline scan 5 min, roll-up hourly, retention nightly (fails loudly without pg_cron; test.sh sets `nilwerk.allow_no_cron=on`) |
| `supabase/migrations/..03_storage.sql` | private buckets `plant-photos`, `firmware`, owner-folder policy (FR-A05) |
| `supabase/migrations/20261122000009_setup_save_plant_rpc.sql` | 4.A4c: `create_plant_and_link_device` RPC (setup "save plant", FR-A03/A04, NFR-06; ADR-017) and the plant check in `devices_update_own` (restates the clause of `..05`). Added as a new file because migration 1 is frozen |
| `supabase/seed.sql` | local fake data: user A (free), user B (premium), one row per table |
| `test.sh`, `test/` | CI-friendly tests (below) |

## Edge functions (task 4.B2: device claim + ingest)
TypeScript, no npm dependencies (Deno on Supabase, Node 22.6+ for tests). Contract: [`../docs/interfaces/openapi.yaml`](../docs/interfaces/openapi.yaml) + `device-report.schema.json`.

| Function | Path | Caller | Does | Requirements |
|---|---|---|---|---|
| `claim-token` | `POST /claim-token` | app, user JWT | one-time claim token (16 bytes, 15 min, single use, SHA-256 stored, max 10 open) | FR-D03, FR-A03, FR-A02, NFR-06 |
| `device-claim` | `POST /device-claim` | sensor | claim token -> device row + per-device token (32 bytes hex, shown once, **SHA-256 stored**) | FR-D03, FR-A03, FR-A08, NFR-06 |
| `delete-account` | `DELETE /account` (4.B2b) | app, user JWT (`verify_jwt=false`, checked in the function with `auth.getUser`) | body `{"confirm":"DELETE"}`; releases + revokes the user's devices (SQL `release_account_devices`, migration `..0006`), deletes Storage photos under `<uid>/`, deletes the auth user (FK cascade erases the rest). Idempotent; 500 before the auth delete on any failure so a retry is safe. The user is only the token's user, never from the body | FR-A01, FR-A08, NFR-07, NFR-06 |
| `export` | `GET /export?format=json\|csv` (4.B2c) | app, user JWT (`verify_jwt=false`, checked in the function with `auth.getUser`) | all of the caller's data (SQL `export_account`, migration `..0008`, service_role only, explicit `owner_id` filter on every table; not limited to the 7-day free window): JSON `{exported_at, profile, plants, devices, readings, readings_hourly, events, alerts, tips, photos}` or a ZIP of 8 CSVs. Photos are linked as 7-day signed Storage URLs with an absolute `expires_at`; only paths of exactly the form `<uid>/<folder>/<file>` under the caller's own id are signed (upload path contract `<uid>/<plant_id>/<uuid>.<ext>`, every segment only `[A-Za-z0-9._-]`; other paths, e.g. with `..`, leading `/`, backslash, `%`, control characters or another prefix, export with `url: null`; a stored row that fails this gets `url: null` and is never signed; QA N1), the app downloads them before the delete screen unlocks (A-107 b). No secrets (device tokens, key hashes) in the export | NFR-07, FR-A01, NFR-06 |
| `ingest` | `POST /ingest` | sensor, bearer device token | up to 192 buffered samples (96 = 24 h offline, FR-D04) + events; idempotent on (device, ts); returns time, config | FR-D01, FR-D02, FR-D04, FR-A07, FR-E03, NFR-04, NFR-06 |

* `supabase/functions/_shared/lib.ts` hashing + report validation, `handlers.ts` request logic, `supabase.ts` the only Supabase-specific file (`env.ts` holds the testable key-name fallback), `<name>/index.ts` Deno entry points.
* The data logic is in SQL (`migrations/20261108000004_device_api.sql`: `issue_claim_token`, `device_claim`, `ingest_batch`, `device_config`; `..0006_delete_account.sql`: `release_account_devices`; `..0008_export_account.sql`: `export_account`), executable by `service_role` only. The edge functions pass SHA-256 digests, never plaintext tokens. A caller never names a device: the device is the owner of the token (device A cannot write device B).
* **Not built** (marked `[not in 4.B2]` in the OpenAPI): rate limits (429 on `/ingest`, `/device-claim`), push dispatch, OTA manifest (`fw_target`/`model_target` are always `null`), `/device-release`, other app endpoints. `delete-account`: Storage listing/removal and `auth.admin.deleteUser` in `supabase.ts` are **never run against a live project** (the tests stub Storage and Auth); Deno was not run either. `export`: Storage signing (`createSignedUrls`) in `supabase.ts` is likewise never run against a live project, and the runtime size/time limit for a large export is unverified (built in memory; async job if it ever times out). Tips, analytics, MCP are 4.B3-4.B5.
* Batch size: the contract (schema, ADR-013) allows 192 samples per request; the task text said 96. 96 (24 h of buffer, FR-D04) is accepted, 193+ gets 413.

## Care-tips engine (task 4.B3, slice 1: guardrail layer only)
Premium feature (FR-P02, FR-P04, ADR-006). Pure TypeScript in `tips/`, no dependencies, no I/O, no clock, no LLM, no keys. **Not an edge function yet**: no `/tips` endpoint, no DB read/write, no cache, no deploy (slice 2).

| File | What |
|---|---|
| `tips/types.ts` | input/output contract; injected interfaces `WeatherProvider` (Q-13 open) and `TextAssistant` (LLM seam) |
| `tips/guardrails.ts` | rule layer `g1.1`: rules G-01..G-13, text classifier, validation of untrusted assistant output (architecture O-7) |
| `tips/engine.ts` | `generateTips(request, deps)`: rule-based baseline tips -> optional assistant (`mode: "live"`, 5 s timeout) -> guardrails; `TIPS_MODE` default `rule_based` (A-029) |
| `tips/test/tips.test.ts`, `tips/test/mutation.sh` | 31 tests (one per rule, adversarial assistant output, error paths, property sweep of 400 combinations); 42 mutants that must all be killed |

* Input: plant (location type, soil type, species, city, thresholds), recent readings, `now`, `premium`, forecast via `WeatherProvider`, season derived from `now` (northern hemisphere assumed: only a city is stored). Output: tips with `reason` and `evidence`, the `removed` list (which rule dropped what, for audit), the weather snapshot, `notes`.
* Guardrails win over everything (ADR-006): no watering when saturated (G-01), outdoors in rain or frost (G-02, G-03), without a fresh plausible reading (G-04) or when the soil is not dry (G-05); no fertilising in frost, in winter, on dry soil, or outdoors without a forecast (G-06..G-09); no "move it outside" in storm or frost (G-10, G-11); no direct-sun advice in heat (G-12). Thresholds are named constants in `guardrails.ts` and are **proposals, not agreed values** (frost <= 2 C, heat >= 30 C, rain >= 5 mm, reading age <= 6 h, dormancy = Dec-Feb).
* Errors: `TipsError` `premium_required` (FR-P04; the weather provider is not called) and `invalid_input`. A failing weather provider, assistant, timeout or malformed assistant output degrades to rule-based tips plus a `notes` entry, never to unchecked text.
* Known limit: the text classifier is keyword based (English and a few German stems). A hostile phrasing it does not know could pass; the sweep and adversarial tests cover the known cases only. Prompts, a real provider and the cost note per premium user are slice 2 (the cost is 0 in `rule_based`; `live` see `docs/stack-and-costs.md`, unverified).
* Run: `node --experimental-strip-types --test tips/test/tips.test.ts` and `bash tips/test/mutation.sh` from `cloud/`; `test.sh` runs the tests as its last stage (CI job `cloud-db`).
* FR-P02 requirement text itself (Google Doc) was not readable in this session; the contract above is taken from ADR-006, `architecture.md` section 5 / O-7, `db-schema.sql` (`tips`, `plants`) and `mcp-tools.json` `get_tips`.

## MCP server (task 4.B5, premium, FR-P03)
Lets the user's own AI client read their own plants. TypeScript, no dependencies. Edge function `mcp` (`supabase/functions/mcp/index.ts`, logic in `supabase/functions/_shared/mcp.ts`): JSON-RPC 2.0 over HTTP POST (single JSON responses, no SSE), `verify_jwt = false` (the bearer token is the user's API key, checked in the function). Contract: `../docs/interfaces/mcp-tools.json` (ADR-007); a test compares names, descriptions, annotations and both schemas with it. Read-only SQL: `migrations/20261123000010_mcp_read_rpcs.sql`.

Tools, all read-only: `list_plants`, `get_plant_status(plant_id)`, `get_history(plant_id, days 1..90 default 7, resolution raw|hourly|daily default hourly)` (at most 2000 points, the server downsamples; watering events from the device's wetting events), `get_tips(plant_id)` (cached tips only, see below).

**API keys (FR-P03, NFR-06)**
* Format: `nwk_` + 32 random bytes, base64url without padding (43 characters, 47 in total). Shown once, when created.
* Storage: `public.api_keys` (migration 1). `key_hash` = SHA-256 of the whole key string (bytea, unique). `prefix` = the first 8 characters, for display. `owner_id`, `revoked_at`, `last_used_at`. The key itself is never stored, logged or returned after creation.
* Check on every request, before any read: the function computes `sha256(key)` and calls `mcp_resolve_key` (service_role only). Unknown or revoked keys give the same answer (401 `key_revoked_or_unknown`). A missing or malformed key gives 401 `unauthorized` without any database call. Revoking = setting `revoked_at`; the next call with that key fails.
* Creating and revoking keys (`POST /api-keys`, `DELETE /api-keys/{id}`, openapi) is built in task 4.B2d (edge function `api-keys`, not deployed, not run against a live project).

**Errors:** HTTP 401 `unauthorized` / `key_revoked_or_unknown`. For a free user, a `tools/call` returns a tool error `premium_required` (FR-P04) and any other method HTTP 403 `premium_required`. Tool errors: `invalid_input`, `not_found` (another user's plant is indistinguishable from an unknown one), `tips_unavailable`, `server_error`, `unknown_tool`. Database messages are never returned.

**Isolation (FR-P03, NFR-07), mechanism: explicit owner filter, not RLS.** The function uses the service role, which bypasses RLS, so RLS cannot protect these reads. Every read goes through an `mcp_*` function that takes `p_owner` (the owner that the verified key resolved to) and filters `owner_id = p_owner` and the plant's owner in SQL. A plant that is not the caller's returns null, which becomes `not_found`. The functions are executable by `service_role` only (`anon` and `authenticated` get permission denied; tested).

**Tips (FR-P02).** `get_tips` reads the newest unexpired row of `tips` and never generates tips (the server is read-only). A row is refused (`tips_unavailable`) when its `guardrail_version` is not `GUARDRAIL_VERSION_EXPECTED` (= `g1.1`, a test checks it equals `tips/guardrails.ts`) or when any item is outside the contract (category enum, text 1..400).

**Tests:** `test/functions/mcp.test.ts`, stage "MCP server" of `test.sh` (own database, seeded). Unit tests cover the key pattern, the hashed key sent to the database, the 401/403/405 paths, input validation, the contract and the tips re-check. Integration tests cover the owner filter (A's key vs B's plant through every tool and at RPC level), revocation, the free-user refusal, history downsampling and the tips guardrail re-check.

**Not built (marked, not claimed):** generation of tips on a cache miss (the contract says it generates; this returns `tips_unavailable`, see 4.B3 slice 2 and Q-13); the rate limit of 60 calls per minute (proposed in the contract); key creation; deployment to `nilwerk-cloud` (no live run; the `verify_jwt = false` setting is unverified in the hosted runtime).

**Cost:** no LLM or paid API on this path. Reads only, so no marginal cost beyond the Supabase function calls.

## Security review of anon RPC access: deferred (A-104 (2))
**Status: not done, deferred by Arsany on 2026-11-16 (A-104 (2)).** The review of what the `anon` role can reach through RPC/function access (`handle_new_user`, `is_premium` and the other functions in `public`, including their `EXECUTE` grants and `SECURITY DEFINER` use) was postponed. **Revisit when moving from the prototype to the real app**, before real users or real data. Until then treat the live `nilwerk-cloud` project as prototype-only: no real personal data. This section records the decision only; no review was done or is claimed here. `test/grants.sql` and `test/functions/api.test.ts` already check that API roles are locked out of the 4.B2 token functions, which is not a full review.

## Run the tests (no Docker, no account)
```bash
projects/plant-monitor/cloud/test.sh                  # starts a throw-away local PostgreSQL 15+, needs initdb/pg_ctl/psql
DATABASE_URL=postgres://postgres:postgres@localhost:5432/postgres projects/plant-monitor/cloud/test.sh   # or an existing superuser server
```
It checks: migration 1 is frozen (sha256 pinned); `db-schema.sql` == migration 1 + `20261122000009` (pg_dump --schema-only, public schema); RLS enabled on every table and user A cannot read, update, delete or forge
rows of user B on each table (`test/rls_isolation.sql`); retention/roll-up (`test/retention.sql`, A-028: raw ~3 months,
hourly roll-up 12 months); the Architect's `db-schema.test.sql` on the migrated DB; the edge functions end to end against that DB (`test/functions/api.test.ts`: claim, hash-only storage, 96-sample batch, replay idempotency, token isolation A vs B, revoked/released tokens, API roles locked out of the functions); `test/openapi_check.py` (code == OpenAPI; needs PyYAML) and Node >= 22.6.
`test/mutation.sh` is the mutation check: 17 one-line mutants of the token-hash, auth, claim and idempotency logic, each must make the tests fail (`NW_ONLY=api test.sh` is its quick mode). A stub `auth` schema and the roles
`anon/authenticated/service_role` replace what Supabase provides (`test/stub_auth.sql`, `test/grants.sql`).

## Run the full stack locally
Needs Docker and the [Supabase CLI](https://supabase.com/docs/guides/cli): `cd projects/plant-monitor/cloud && supabase start && supabase db reset`
(applies migrations + seed; Studio on http://localhost:54323). **Not run in the agent session** (no Docker there).

## Migration rules
- Migration 1 is the 2.4 schema as of 2026-11-07. **Once it is pushed to any real project it is frozen**: every later schema change is a NEW migration file (and an update to `docs/interfaces/db-schema.sql` so the contract stays current). `test.sh` pins migration 1's sha256 (origin/main bytes). The contract check compares `db-schema.sql` with migration 1 plus the 4.A4c migration via `pg_dump --schema-only` of both (only those two: migrations 2-8 add objects the contract file does not list). A future change to the schema: new migration file, plus the same change in `db-schema.sql`, plus the guard's expected list if it adds a migration to the contract check.
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

## Deferred security review (revisit at real-app phase)
Decision by Arsany, 16 Nov 2026: the security review of the anonymous RPC access is **deferred**, not accepted. It is not done now. No SQL, migration or function was changed for it. Source: Supabase database advisors on `nilwerk-cloud`, as reported on 16 Nov (not re-run for this section).

| # | Finding | Object |
|---|---|---|
| 1 | anon role can call the function through the API (most serious) | `handle_new_user` |
| 2 | anon role can call the function through the API (most serious) | `is_premium` |
| 3 | SECURITY DEFINER, executable by anon/authenticated | `delete_plant` and others (full list in the advisor output) |
| 4 | mutable `search_path` | several functions |
| 5 | RLS enabled, no policy | `claim_tokens`, `device_credentials`, `firmware_releases` |
| 6 | unindexed foreign keys | 7 tables |
| 7 | `auth_rls_initplan` (auth call re-evaluated per row) | 13 policies |

**Revisit trigger:** the project moves from prototype to the real app. Items 1 and 2 are first. Until then the exposure stays as listed; the device functions are covered by `test/grants.sql` only, not by these advisors.

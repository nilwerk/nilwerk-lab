# Two implementations of 4.B2: comparison and recommendation

Date: 2026-11-08 · Author: Sana (Cloud AI Engineer) · Status: for Arsany / Lead decision. Nothing was deleted.

**What happened.** Task 4.B2 was implemented twice, independently, by two parallel sessions:

| | Branch | PR | Head |
|---|---|---|---|
| A (mine) | `agent/cloud-ai/4.B2` | #45 (open, Architect: approved with conditions, QA: pass with notes) | see `git log` |
| B (parallel Lead session) | `agent/cloud/4.B2` | none | `2285c60` (one commit, 2026-11-08 14:09 UTC, branched from an older main) |

Branch B was never turned into a PR, which is why it looks orphaned. B is based on a main before #42/#43 and still says `SUPABASE_SERVICE_ROLE_KEY` in its README; its showcase item is `2026-11-07_4.B2` (A: `2026-11-08_4.B2`).

## Side by side

| Topic | A (#45) | B (`agent/cloud/4.B2`) |
|---|---|---|
| Migration | `20261108000004_device_api.sql`: `issue_claim_token`, `device_config`, `device_claim`, `ingest_batch` | `20261107000004_device_api.sql`: `device_config`, `authenticate_device`, `claim_device`, `ingest_report` |
| Endpoints | **3**: `/claim-token` (user JWT, max 10 open tokens, 15 min), `/device-claim`, `/ingest` | **2**: `/device-claim`, `/ingest`. No `/claim-token`: nobody can issue a claim token, so the claim flow cannot be used end to end |
| Token handling | SHA-256 hex computed in the function, `decode(hex)` in SQL, plaintext never reaches the DB (ADR-004). Auth + write in ONE SQL call (`ingest_batch`) | Same hashing (bytea hex). Auth is a separate call (`authenticate_device`), then `ingest_report(device_id, ...)`: two round trips, small race window (handled by an NW403 -> 401 mapping) |
| Error signalling | `jsonb {"error": ...}` returned by SQL | Custom SQLSTATEs NW401/NW409/NW403 raised in SQL, mapped in TS |
| 401 detail | `token_invalid` / `token_revoked` (same as openapi) | same, plus distinguishes via `authenticate_device` status |
| Claim: plant link on hand-over | **Kept** when a new owner claims a released device (bug, fixed in #45 today, see below) | **Cleared** for a new owner, kept for same owner |
| Claim: `last_seen_at` | not set | set to now |
| OTA manifest (FR-D05) | not built: `fw_target`/`model_target` = null | built: joins `firmware_releases`, signed Storage URL via `signUrl` |
| Validation | hand-written `validateReport`, tested against the schema fixtures; `openapi_check.py` ties spec to code in CI | similar hand-written `validate.ts` |
| `config.toml` `verify_jwt = false` | set for all 3 functions | not set in the repo (only a code comment "deploy with --no-verify-jwt"); a plain `supabase functions deploy` would put the gateway JWT check in front of devices that have no JWT |
| Function directory | `cloud/supabase/functions/...` (moved there in #45, the CLI default; tests in `cloud/test/functions/`) | `cloud/supabase/functions/...` (default CLI location) |
| Tests | 16 `node:test` tests: handlers + **real PostgreSQL end to end** (psql-backed `Deps`), token isolation A vs B, RLS lock-out of API roles, 10-token cap, unlimited devices, 96-sample buffer, replay, skew, + 15 min / 120 s / 32 events / MIN_TS boundaries | 14 mock-DB handler tests + **`test/device_api.sql`**: SQL-level tests of claim/ingest (counts, alerts open **and resolve**, 96 buffer, overlap, small skew must not shift, released device refused, app roles cannot call functions) |
| Mutation check | `test/mutation.sh`, 26 mutants, 0 survive (after QA follow-up) | 4 mutants (revoked, unknown token, idempotency, authenticate) |
| Node requirement | >= 22.6 (`--experimental-strip-types`), CI uses setup-node 22 | >= 22.18, otherwise the TS tests print "NOT RUN" and pass (can silently skip) |
| Secrets wording | A-035 new key model: `SUPABASE_SECRET_KEY`, `SUPABASE_PUBLISHABLE_KEY` | old `SUPABASE_SERVICE_ROLE_KEY` |

## What is better in B (worth porting)

1. **OTA manifest in `ingest_report`** (FR-D05): `firmware_releases` join, "only if target differs from the reported version", signed URL hook. A returns null. This is the biggest functional difference; it belongs in a follow-up PR on #45's base, not copy-pasted (A has a single-call `ingest_batch`, so the join would go there).
2. **SQL-level test file** `test/device_api.sql`: two things A did not assert (until today): alerts **resolve** after a good reading, and a skew of 100 s must not shift timestamps (A now covers skew at exactly 120/121 s).
3. Clearing `plant_id` for a new owner. **Already ported into #45 today** (one line in `device_claim`, test + mutant SQL-14).
4. `last_seen_at = now()` on claim (cosmetic, not ported).
5. Function files in `supabase/functions/` (default CLI location). See the open risk below.

## What is better in A

- `/claim-token` exists (B has no way to issue a claim token).
- One SQL call per ingest (auth and write in one transaction, no TOCTOU).
- `verify_jwt = false` configured; JWT verified in-function for `/claim-token`.
- Real-DB end-to-end tests and RLS lock-out test; `openapi_check.py` keeps spec and code in sync; mutation harness with 26 mutants, boundary tests from the QA review.
- Independent Architect and QA reviews already done on #45.

## What would break if both were merged

- Different migration versions (`..07000004` and `..08000004`) so both would apply; both define `public.device_config(uuid)` with `create or replace`, and the bodies are equivalent, so the second silently replaces the first (no error, but two sources of truth).
- Otherwise the function names differ, so the SQL does not collide, but the schema would carry two parallel API sets (`device_claim`/`ingest_batch` and `claim_device`/`ingest_report`) with different error contracts and only one used by the edge functions: dead, `service_role`-callable code that is a needless attack surface.
- Two `ingest` and two `device-claim` function directories (A before the move to `cloud/supabase/functions`, and B), two `test.sh` stages, two showcase items and a README/CI conflict.
- B's migration would be applied **before** A's (older version number). A fresh DB is fine; an environment that already applied A's `..08000004` would get B's `..07000004` out of order (`supabase db push` refuses out-of-order migrations without `--include-all`).
- Not both of them can be real: whichever is chosen, the other migration must never reach main.

## Function directory (resolved in #45)

Verified in the Supabase docs (config reference, `functions.<name>.entrypoint`): the default is `supabase/functions/<function_name>/index.ts` next to `config.toml`. A's functions were moved with `git mv` to `cloud/supabase/functions/` and its tests to `cloud/test/functions/` (outside the deploy tree). Still to confirm on the first deploy smoke test (Theo's C3).

## Recommendation

1. **Keep PR #45 as the 4.B2 implementation.** It is the complete flow (claim-token, claim, ingest), reviewed by the Architect and QA, and CI is green.
2. **Do not merge `agent/cloud/4.B2`** and do not open a PR for it. Keep the branch for now as reference (not deleted; deletion is Arsany's / the Lead's decision) until the OTA manifest is ported.
3. **Port from B, in a follow-up task (4.B2c or inside the FR-D05 task), not in #45:** the OTA manifest (`firmware_releases` join, signed URL) and the two SQL-level assertions (alerts resolve, small skew). Credit B's session in the commit.
4. **Process fix (for the Lead):** two sessions took the same task because the Plan row was not locked. One owner per task and a branch name per role (`agent/<role>/<task>`) would have shown the clash; the two branch names differ (`cloud` vs `cloud-ai`), which is exactly why it went unnoticed.

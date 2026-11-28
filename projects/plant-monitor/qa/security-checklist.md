# Security and privacy checklist (task 5.9)

Owner: Ines (QA & Test Engineer). Scope: TLS, device tokens, row-level security, API key revocation, GDPR-style export and delete (NFR-06, NFR-07), plus the premium gate (FR-P04) where it protects data.
Base: `origin/main` at 51b4b6e. Branch `agent/qa/5.9`. Nothing in the product was changed by this task.

## Status legend and rules
- **Pass**: the check ran here, offline, and the evidence is listed. "Offline" means local PostgreSQL 16.15, Node 22.23, Jest and CMake/CTest in this sandbox.
- **Fail**: the code or config does not meet the requirement or the ADR it cites. Each Fail has an entry in *Open findings*.
- **Not run**: needs the live `nilwerk-cloud` project, a deployed edge function (api-keys and analytics are not deployed, A-146/A-152), a phone, or the device bench. Nothing here is a live result.
- RLS in this checklist is proven by `cloud/test/rls_isolation.sql` on a local PostgreSQL with `auth.uid()` stubbed by `cloud/test/stub_auth.sql` (`request.uid` setting), and by the migrations. It is **not** a result from a live Supabase project. The mutation suite that checks these tests (`cloud/test/mutation.sh`, CI job `cloud-mutation`) was **not run** here (about 15 min, CI-only).

## Requirements used
- NFR-06 (TLS everywhere, per-device credentials, users only see their own data, MCP keys can be revoked; acceptance: security checklist passes) and NFR-07 (EU hosting, export and deletion; acceptance: export and delete work).
- FR-A01 (delete account removes its data), FR-A08 (release a device), FR-D03 (claim token -> device token), FR-D07 (factory reset), FR-P03 (personal API key, revocable), FR-P04 (free/premium flag), FR-P01 (premium analytics), NFR-13 (retention, A-028).
- Source: "Requirements v0.1 (draft)" Google Doc `1T4k3rK4KQDeGtIN8pjdmohGUAohFrtATLhMYSBsYA6g`, read through the Google Docs connector (rows FR-A01, FR-P03, FR-P04, NFR-06, NFR-07). Also `projects/plant-monitor/docs/requirements-v1.0-delta.md` (NFR-07 export as JSON and CSV; NFR-13 retention 3 months raw and 12 months roll-ups).

## Commands run (offline)
| Command | Result |
|---|---|
| `bash projects/plant-monitor/cloud/test.sh` | exit 0, last line `ALL CLOUD TESTS PASSED`. Migration 1 frozen (sha256 ok). db-schema.sql == migrations 1+9. Migration 2 fails without pg_cron (ok). RLS isolation: "RLS enabled on all 14 public tables", then `RLS ISOLATION OK`. Retention: `raw_deleted 5, hourly_deleted 1`, second run no-op. 2.4 contract test ran. OpenAPI check ran. Node suites: api 23/23, export 22/22, mcp 32/32, analytics 18/18, analytics_deps 7/7, api_keys 20/20, api_keys_deps 6/6, tips 68/68 (all 6 tips/analytics test files run, glob check), analytics pure 34/34. Total 230 Node tests, 0 fail, 0 skipped. |
| `cd projects/plant-monitor/app && npm ci --ignore-scripts && npx jest <16 security-relevant suites>` | 16 suites, 170 tests, all pass (apiKeysApi, analyticsApi, premiumDashboard, exportClient, fileHandOff, exportGate, deleteAccount x3, supabaseAuth, accountApi, authState, connectAi, profileDashboardEntry, realPlantSetup, setupRealSave). |
| `cmake -S firmware/test/host -B <build> && cmake --build <build> && ctest` | 34/34 pass. Includes upload_unit, upload_contract, ota_unit, sec2_unit, provisioning_unit, sec2_mutation_checks, provisioning_mutation_checks. Host only, no ESP-IDF build, no device. |

## A. Cloud: row-level security (NFR-06, NFR-07)
| ID | Req | Check | Evidence | Status |
|---|---|---|---|---|
| R-01 | NFR-06 | RLS enabled on every public table | Migration 1 `cloud/supabase/migrations/20261107000001_core_schema.sql` `enable row level security` on each table (profiles l.30, plants l.84, devices l.109, device_credentials l.138, claim_tokens l.147, firmware_releases l.162, plant_images l.174, readings l.208, readings_hourly l.230, events l.272, alerts l.292, push_tokens l.301, tips l.317, api_keys l.333). Offline proof: `rls_isolation.sql` section 0, output "RLS enabled on all 14 public tables". | Pass (offline) |
| R-02 | NFR-06 | User A cannot read B's rows, on every table | `cloud/test/rls_isolation.sql` section 1 (l.20-54), output "read ok" for all 11 owner tables with "A sees N own, 0 foreign". Policies: `plants_all_own` (l.85), `devices_select_own` (l.110), `readings_select_own` (l.211), `api_keys_select_own` (l.334), etc. | Pass (offline) |
| R-03 | NFR-06 | User A cannot update, delete or forge B's rows | `rls_isolation.sql` section 2 (l.66-114): output "write ok" for all 14 tables and "forged inserts refused on all 14 tables". Write policies have `with check (owner_id = auth.uid())`. | Pass (offline) |
| R-04 | NFR-06 | Service-only tables are invisible to users (device_credentials, claim_tokens, firmware_releases) | RLS on, no policy. `rls_isolation.sql` output "service-only, A sees 0". `api.test.ts:237` "API roles cannot call the functions or read credentials/claim tokens". | Pass (offline) |
| R-05 | NFR-06 | A user cannot point its device at another user's plant | Migration 5 `cloud/supabase/migrations/20261108000005_devices_plant_check.sql` l.7-11 (`with check` requires `p.owner_id = auth.uid()`). `rls_isolation.sql` l.115 and output "A cannot point its device at B plant". | Pass (offline) |
| R-06 | NFR-06, FR-P04 | A user cannot grant itself premium | Trigger `profiles_guard` in migration 1 l.38-42 raises 42501 when `is_premium` changes outside service role. `rls_isolation.sql` l.128 "cannot grant itself premium". | Pass (offline) |
| R-07 | NFR-06 | Views run with the caller's RLS | `rls_isolation.sql` l.60 (security_invoker). | Pass (offline) |
| R-08 | NFR-06 | Setup RPC cannot move a sensor silently or link a foreign device | Migration 9 `20261122000009_setup_save_plant_rpc.sql` (function l.21, grant to authenticated l.34). `rls_isolation.sql` section 2b, output "contract ok". | Pass (offline) |
| R-09 | NFR-06 | Storage photos: user only reaches own folder | Policy `photos_own` in `cloud/supabase/migrations/20261107000003_storage.sql` l.10-13. **Not exercised offline**: test.sh prints "storage schema not present: buckets skipped". | Not run (see F-03) |
| R-10 | NFR-06 | Storage `firmware` bucket has no user policy | Migration 3 l.6-7 comment; no policy created. Live bucket policy not checked. | Not run |
| R-11 | NFR-06 | Live project: deployed policies and advisors match the repo | Needs `nilwerk-cloud` (Supabase get_advisors, pg_policies). | Not run |

## B. Cloud: device tokens (NFR-06, FR-D03, FR-D07, FR-A08)
| ID | Req | Check | Evidence | Status |
|---|---|---|---|---|
| D-01 | NFR-06 | Device bearer token stored as SHA-256 only, never plaintext | `device_credentials.token_hash bytea` (migration 1 l.134, "sha256(token); token = 32 random bytes, shown once"). Token creation in `device_api.sql` `device_claim` l.30-52 writes `decode(p_token_hash,'hex')`. `api.test.ts:54` "handlers send only SHA-256 digests to the database, never plaintext tokens"; `api.test.ts:99` "hash only stored, single use". | Pass (offline) |
| D-02 | NFR-06 | Device token is checked on every ingest by hash; unknown, malformed, revoked or released tokens get 401 and write nothing | `ingest_batch` in migration 4 `20261108000004_device_api.sql` l.61-67 (lookup by hash). `api.test.ts:204` "unknown, malformed, revoked and released tokens get 401 and write nothing". | Pass (offline) |
| D-03 | NFR-06 | Device A's token cannot write device B | `api.test.ts:189` "device A's token cannot write device B; the body cannot name a device". | Pass (offline) |
| D-04 | FR-D03, FR-A08 | Re-claim rotates the token; the old one dies; a released device can be claimed by another user | `device_api.sql` l.50-51 (`on conflict ... set token_hash = excluded.token_hash`). `api.test.ts:218`. | Pass (offline) |
| D-05 | FR-A08, NFR-06 | Account delete revokes all device tokens and releases devices | `cloud/supabase/migrations/20261110000006_delete_account.sql` l.9-26 (`release_account_devices`, comment l.15). `api.test.ts:360`. | Pass (offline) |
| D-06 | FR-D03 | Claim token: 16 random bytes, stored as hash, 15 min, single use | `claim_tokens` migration 1 l.141-148; `api.test.ts:99`, `:118` (expired and unknown refused), `:254` (15 min). | Pass (offline) |
| D-07 | NFR-06 | Device token stored on the device (flash) is protected | ADR-004 "Decision": token in NVS on the device; "Consequences": no flash encryption planned. No flash-encryption setting found in the firmware config. | Fail (F-02, accepted risk in ADR-004, needs Arsany's decision) |
| D-08 | NFR-06 | Claim token and Wi-Fi credentials are encrypted over BLE (security 2) | `docs/architecture.md` l.191; ADR-011. Host tests: `sec2_unit`, `sec2_mutation_checks`, `provisioning_unit` (34/34 ctest). BLE with a real phone not run. | Not run (bench, B1-B5 in `tests/procedures/4.F2b-sec2-provisioning.md`) |

## C. Cloud: API keys for MCP (FR-P03, NFR-06)
| ID | Req | Check | Evidence | Status |
|---|---|---|---|---|
| K-01 | FR-P03 | Key = `nwk_` + 32 random bytes (43 base64url characters), random per creation | `cloud/supabase/functions/_shared/api_keys.ts` l.70-71; `mcp.test.ts:68` (format), `api_keys.test.ts:122` (two keys differ). | Pass (offline) |
| K-02 | NFR-06 | Only SHA-256 and the 8-character prefix are stored; the key is not stored, logged or in the store call | `api_keys.ts` l.72; schema migration 1 `api_keys` l.322-327 (`key_hash bytea`, "shown once"). `api_keys.test.ts:102`; `api_keys.test.ts:199` (row has the hash and prefix, never the key); `mcp.test.ts:76` and `:309`. | Pass (offline) |
| K-03 | NFR-06 | The key is returned once, with no-store caching | `api_keys.ts` l.74 (`cache-control: no-store`). App: `app/src/screens/ConnectAiScreen.tsx` l.88 keeps the created key only in component state; no storage call found for it in `app/src`. | Pass (offline, code) |
| K-04 | FR-P03 | Revoked key stops working on the next call, with no data read | `mcp_resolve_key` migration 1 l.342-355 (revoked keys fail). `mcp.test.ts:97` (`key_revoked_or_unknown`, no reads), `:351` ("fails on the next call"), `:362`. `api_keys.test.ts:212` (created key authenticates, then fails once revoked). | Pass (offline, local DB) |
| K-05 | NFR-06 | Users cannot revoke another user's key; the answer does not reveal existence | `api_keys.test.ts:241` (404 for another user's key, key stays valid), `:253` (service revoke filtered by owner). | Pass (offline) |
| K-06 | FR-P03 | Revoke is idempotent and keeps the first `revoked_at` | `api_keys.test.ts:129`, `:232`. | Pass (offline) |
| K-07 | NFR-06 | Key hash is never selectable by a user; a user sees only own keys | Column grant migration 1 l.335-336 (`revoke select`, `grant select (id, owner_id, name, prefix, created_at, last_used_at, revoked_at)`). `rls_isolation.sql:55`. `api_keys.test.ts:259`. | Pass (offline) |
| K-08 | NFR-07 | Account delete removes the user's keys | `api_keys.owner_id references profiles on delete cascade` (migration 1 l.323-324); account delete deletes the profile (`api.test.ts:360`). No test asserts the key rows explicitly. | Pass (offline, by FK; test gap F-06) |
| K-09 | FR-P03, FR-P04 | Key creation is refused for free users before any write | `api_keys.ts` premium check before insert; `api_keys.test.ts:62` (nothing written), `:191` (real `is_premium()`). | Pass (offline) |
| K-10 | FR-P03 | Api-keys edge function live: create, list, revoke | Function not deployed (A-146/A-152). | Not run |
| K-11 | FR-P03 | MCP server live: revoked key refused, cross-user isolation | `mcp` function not verified on the live project. | Not run |

## D. Cloud: premium gate and privacy (FR-P04, FR-P01, NFR-07, NFR-13)
| ID | Req | Check | Evidence | Status |
|---|---|---|---|---|
| P-01 | FR-P04 | Free users are refused on analytics before any read | `analytics.test.ts:58` ("no plant or reading is read"), `:222` (real `is_premium()`). | Pass (offline) |
| P-02 | FR-P04 | Free users are refused on MCP tool calls, with no data read | `mcp.test.ts:106`, `:371`. | Pass (offline) |
| P-03 | FR-P04 | Tips are readable only for premium users (RLS) | `tips_select_own_premium` migration 1 l.317-318. `rls_isolation.sql` output "tips: A sees 1 own" (seed premium). | Pass (offline) |
| P-04 | FR-P04 | App shows premium screens only for premium, with no fetch for free users | `app/src/__tests__/premiumDashboard.test.tsx` (free: no fetch, upgrade message); `profileDashboardEntry.test.tsx`. Jest pass. Phone not run. | Pass (app, offline) |
| P-05 | NFR-07 | Export as JSON and CSV, with all the user's retained data (also older than the 7-day free window) | `cloud/supabase/functions/export/index.ts`; `export.test.ts:124` (JSON, all data), `:299` (CSV zip, one CSV per table, valid CRC). `export_account` migration 8 `20261117000008_export_account.sql` (service_role only, l.29-30). | Pass (offline) |
| P-06 | NFR-07, NFR-06 | Export never contains secrets or hashes | Migration 8 l.7 (device_credentials, api_keys, push_tokens, claim_tokens left out); `export.test.ts:280` ("no secret column"). | Pass (offline) |
| P-07 | NFR-06 | Export photo links are only for the caller's own files; traversal rejected | `export.test.ts:208`, `:223`, `:226`, `:236`, `:256`, `:266`, `:178`. | Pass (offline) |
| P-08 | FR-A01, NFR-07 | Delete account: wrong token or body refused, nothing deleted; wrong method 405 | `api.test.ts:324` (401), `:339` (400, body must be `{confirm:'DELETE'}`). | Pass (offline) |
| P-09 | FR-A01, NFR-07 | Delete account removes readings, photo rows, plants, profile and auth user; other user untouched | `api.test.ts:360`; no cross-user deletion `:395`. | Pass (offline) |
| P-10 | NFR-07 | Account is not deleted if photo deletion fails; retry completes | `api.test.ts:350`. | Pass (offline) |
| P-11 | FR-A01 | Repeated delete is idempotent | `api.test.ts:384`. | Pass (offline) |
| P-12 | NFR-07 | Delete and export on the live project (real Storage, real Auth) | Functions not verified live; Storage and Auth not in offline tests. | Not run |
| P-13 | NFR-13 | Raw readings older than 3 months are rolled up to hourly, then deleted; roll-ups older than 12 months are deleted; second run is a no-op | `cloud/test/retention.sql` l.23-38, output `apply_retention #1 -> {"rolled_up": 1, "raw_deleted": 5, "hourly_deleted": 1}`, `#2` all zero. Function migration 1 l.506-518. | Pass (offline) |
| P-14 | NFR-13 | Nightly retention and roll-up jobs are scheduled on the live project | Schedules in migration 2 `20261107000002_schedules.sql` (`nw-retention` 03:17, `nw-rollup` hourly, `nw-offline-scan` every 5 min, l.9-11). Locally pg_cron is absent and the job is skipped (test.sh "pg_cron not available"). | Not run |
| P-15 | NFR-07 | Personal data sent to the LLM tips path is minimal and inside the EU | `cloud/tips/engine.ts` l.104: assistant context includes the plant's free-text name, type, soil, species, season, forecast and moisture. Default mode is `rule_based` (l.101), live assistant not wired. Claude API is outside the EU (O-5, `docs/architecture.md` l.262; `docs/stack-and-costs.md` S4). | Not run (live mode off; see F-04, needs Arsany's decision) |
| P-16 | NFR-07 | EU hosting of the Supabase project | Region is a Supabase project setting; not checked here. | Not run |

## E. TLS (NFR-06)
| ID | Req | Check | Evidence | Status |
|---|---|---|---|---|
| T-01 | NFR-06 | Device uploads use https only; the URL builder refuses http, query, fragment and trailing slash | `firmware/components/upload/src/nw_upload.c` l.7 (`https://` scheme); `firmware/test/host/test_upload.c` l.78-82 (http refused). `upload_unit` and `upload_contract` pass in ctest. | Pass (host, offline) |
| T-02 | NFR-06, ADR-004 | Device checks the server certificate with the pinned CA bundle that ADR-004 specifies | `firmware/components/upload/src/nw_upload_idf.c` l.142 `crt_bundle_attach = esp_crt_bundle_attach` (the full ESP-IDF certificate bundle, not a pinned bundle). Redirects disabled l.144. | Fail (F-01) |
| T-03 | NFR-06 | Device TLS handshake against the real endpoint | Needs device, Wi-Fi and the live endpoint. | Not run |
| T-04 | NFR-06 | OTA: download over TLS, SHA-256 checked before activation | `firmware/components/ota/include/nw_ota.h` l.7 "NOT RUN ON HARDWARE" (esp_https_ota). `ota_unit` passes (host, SHA-256 parse and verify). | Not run (device) |
| T-05 | NFR-06 | App calls the backend only over https; no cleartext override | No `http://` literal in `app/src` (non-test). No `usesCleartextTraffic` / `NSAllowsArbitraryLoads` in app config. Endpoint comes from env `SUPABASE_URL` (`app/app.config.ts` l.38). | Pass (code, offline) |
| T-06 | NFR-06 | Live endpoints serve TLS with a valid chain (Supabase edge functions) | Needs the live project. | Not run |
| T-07 | NFR-06 | Local dev config is not used in hosted config | `cloud/supabase/config.toml` l.27 `site_url = "http://localhost:8081"` (local config). Hosted settings not checked. | Not run (see F-05) |

## F. App (NFR-06, FR-A01, FR-P03)
| ID | Req | Check | Evidence | Status |
|---|---|---|---|---|
| A-01 | NFR-06 | Session tokens kept in secure storage on the phone | `app/src/auth/supabaseAuth.ts` l.4, l.11-13 (`expo-secure-store`); `app/src/auth/storage.ts` l.1-2 (chunking). | Pass (code, offline) |
| A-02 | NFR-06 | On web the session falls back to localStorage (JWT readable by page scripts) | `app/src/auth/supabaseAuth.ts` l.17-19. | Fail for web builds (F-05, low; applies only if a web build ships) |
| A-03 | NFR-06 | No service-role key in the app | No `service_role` reference in `app/src`. The app uses only the publishable key from env (`app/app.config.ts` l.39). | Pass (code, offline) |
| A-04 | NFR-06 | The app does not log tokens or keys | 0 `console.*` calls in non-test `app/src` files. | Pass (code, offline) |
| A-05 | FR-A01, NFR-07 | Export gate: export before delete; exact name typed; no skip | `app/src/export/exportGate.ts` (`canDelete`); `exportGate.test.ts`, `deleteAccount.test.tsx`, `deleteAccountBypass.test.tsx` (Jest pass). A-106. | Pass (app, offline, fake fetch) |
| A-06 | NFR-07 | Export file hand-off: write, size read-back, user confirms it is saved | `app/src/export/fileHandOff.ts`; `fileHandOff.test.ts` (Jest pass). | Pass (app, offline) |
| A-07 | FR-P03 | API key screen: create, list, revoke with confirmation | `app/src/__tests__/apiKeysApi.test.ts`, `connectAi.test.tsx` (Jest pass). | Pass (app, offline, fake service) |
| A-08 | FR-A01, NFR-07 | Export and delete on a real phone and the live backend | Needs phone and live project. A-107 photo download (task 4.A9b) not built. | Not run |

## G. Open findings
| ID | Severity | Where (file:line) | Requirement | Finding | Needs |
|---|---|---|---|---|---|
| F-01 | Medium | `projects/plant-monitor/firmware/components/upload/src/nw_upload_idf.c:142` | NFR-06, ADR-004 | Device trusts the full ESP-IDF certificate bundle, not the pinned CA bundle that ADR-004 says ("TLS with pinned CA bundle"). Any public CA in the bundle can sign a certificate the device accepts. | Decision by Theo: pin, or update ADR-004 to the bundle. Arsany if the ADR changes. |
| F-02 | Medium | `projects/plant-monitor/docs/adr/ADR-004-device-identity-and-tokens.md` (Consequences); no flash-encryption setting in the firmware config | NFR-06 | Device bearer token sits in NVS in plain flash, and flash encryption is not configured. The ADR accepts this (risk O-3 in the ADR's text). Offline checks cannot show the flash contents. | Arsany: accept for the demo (and write it down), or plan flash encryption. |
| F-03 | Medium | `projects/plant-monitor/cloud/supabase/migrations/20261107000003_storage.sql:10-13`; `cloud/test.sh` output "storage schema not present: buckets skipped" | NFR-06, FR-A05 | The photo Storage policy (`photos_own`) is never run offline, so no test proves that a user can reach only their own photo folder. The export and delete tests use a fake Storage client. | Sana or Leo: add a Storage stub to the offline RLS test, and check the policy on the live project. |
| F-04 | Medium | `projects/plant-monitor/cloud/tips/engine.ts:104`; `projects/plant-monitor/docs/architecture.md:262` (O-5) | NFR-07 | When live mode is switched on, the plant's free-text name and weather context go to the Claude API, which is processed outside the EU. The O-5 question is still open. Live mode is off today (`engine.ts:101`). | Arsany: decide on O-5 before live mode is enabled. Option: send only the plant type, not the name. |
| F-05 | Low | `projects/plant-monitor/app/src/auth/supabaseAuth.ts:17-19`; `projects/plant-monitor/cloud/supabase/config.toml:27` | NFR-06 | Web builds keep the session JWT in localStorage. The local config points at http://localhost, which is fine for dev only. | Leo: confirm no web build ships with real sessions; confirm hosted config is separate. |
| F-06 | Low | `projects/plant-monitor/cloud/test/`; `cloud/test/functions/api.test.ts:360` | FR-A01, NFR-07 | No test asserts that account delete removes the `api_keys` rows. It relies on the foreign key cascade (migration 1 l.323-324). | Sana: add one assertion. |
| F-07 | Info | `projects/plant-monitor/cloud/test/mutation.sh`, CI job `cloud-mutation` | NFR-06 | The RLS and token tests were not checked for mutation strength in this task (CI-only, about 15 min). | Kai or Ines: run in CI on the 5.9 PR head. |

## H. Needs Arsany (not decided by an agent)
- Deploy the api-keys and analytics edge functions (A-146/A-152), then re-run K-10, K-11, P-12 and P-14 on the live project. Until then, the MCP key and premium analytics checks are offline only.
- Decide F-02 (device token on flash) and F-04 / O-5 (LLM tips outside the EU, NFR-07). Give each its A-ID in Needs Arsany.
- Run the live checks in the `nilwerk-cloud` project (R-09 to R-11, T-06, P-14, P-16) with a read-only role.

## Counts
Items: 61 (section A RLS 11, B device tokens 8, C API keys 11, D premium and privacy 16, E TLS 7, F app 8).
Status: **43 Pass**, **3 Fail** (D-07, T-02, A-02), **15 Not run**. Findings: 7 (F-01 to F-07): 0 Critical, 0 High, 4 Medium (F-01 to F-04), 2 Low (F-05, F-06), 1 Info (F-07). F-03 is a gap in proof (no offline test), F-04 is an open privacy decision; no breach was found in either.
Counted with `grep` over the item rows of this file.

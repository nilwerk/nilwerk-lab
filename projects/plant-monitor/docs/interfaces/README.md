# Interface contracts (task 2.4) - DRAFT v0.1 for the G2 design review

Author: Theo (System Architect) · 2026-11-04 · **Self-authored: needs independent review before approval.**
Builders code against these files. A change to any of them needs an ADR (role file). Synced with Requirements v0.1 + Arsany's G1 answers (PR #2 comments) + ADR-001..012 + `architecture.md` v0.3.

| File | Contract | Main consumers |
|---|---|---|
| `db-schema.sql` | Postgres tables, RLS on every table, alert/offline/retention + roll-up functions | Leo (4.B1, 4.B2), Sana, Ines |
| `db-schema.test.sql` | Smoke test of the above (RLS, premium window, alerts, retention, cascade) | Ines, Kai |
| `openapi.yaml` + `device-report.schema.json` | `/claim-token`, `/device-claim`, `/ingest`, `/device-release`, `/plants/{id}` (delete), `/api-keys`, `/export`, `/account` | Mira (4.F2/4.F3), Leo (4.A*, 4.B2) |
| `hub-mqtt.md` | Device -> Pi hub MQTT topics and payloads (ADR-012) | Mira (4.F6), hub tasks 4.H1/4.H2 |
| `ble-provisioning.md` | BLE setup endpoints and payloads (ADR-011) | Mira (4.F2), Leo (4.A3) |
| `mcp-tools.json` | MCP tools, premium and key rules | Sana (4.B5) |

Not in this draft (no builder needs them yet): tips/analytics HTTP endpoints (contracts of 4.B3/4.B4), hub HTTP API `hub-api.md`, HA discovery topics `ha-discovery.md` (FR-I01 is "Could").
The `cloud/` scaffold is empty (`.gitkeep`), so no migration is placed there; Leo copies `db-schema.sql` into `cloud/supabase/migrations/` in 4.B1.

## Decisions made here (the new facts)
| # | Decision | Req |
|---|---|---|
| 1 | Unit of record = the **15-min sample** (96 per 24 h). The hourly report is only transport. Settles Ines's follow-up 1 | FR-D04, FR-D02 |
| 2 | `(device_id, ts)` is the idempotency key; the server shifts `ts` by the clock skew if above 120 s | FR-D04, D-8 |
| 3 | Out-of-range values are **stored with `plausible=false`**, not rejected (one bad sensor never loses the batch); alerts and charts ignore them | FR-D01 |
| 4 | Claim is its own call `/device-claim`, not a side effect of `/ingest` (different auth mode). Changes architecture section 5 step 5 | FR-D03, FR-A08 |
| 5 | Readings/events/alerts carry `owner_id` stamped at ingest: release + re-claim never leaks history, RLS is one predicate | FR-A08, NFR-06 |
| 6 | No roll-up tables: 90 days x 4/h x 24 = 8,640 rows per device, charts query raw/hourly (answers D-2) | FR-P01 |
| 7 | Hub MQTT has **no Last-Will**; hub decides offline (clean disconnects never fire an LWT) | ADR-012 amend |
| 8 | Hub identity in MQTT = `hw_id` (`nw-<12 hex>`), not the cloud UUID | FR-D08 |

## G1 decisions as implemented (Arsany, PR #2 comments)
| Decision | Where |
|---|---|
| Offline = 3 missed hourly reports (replaces 2.5 h in D-6/ADR-012) | `scan_offline()`: last report older than 3 h + 10 min jitter grace [10 min grace decided, A-018]; hub: same rule |
| Retention: raw ~3 months, hourly/daily roll-up 12 months (NFR-13, A-028) | `rollup_readings()` hourly + `apply_retention()` nightly (pg_cron), table `readings_hourly`, view `readings_daily` |
| Export JSON + CSV | `GET /export?format=json\|csv` |
| FR-D02 = 24 +/- 1 reports per day | `/ingest` limit 6 requests/device/hour leaves room for critical + reconnect; cadence in `config.report_interval_s = 3600` |
| OTA = SHA-256 over TLS, signing is a follow-up, FR-D05(c) dropped | `Artifact.sha256`, `firmware_releases.sha256`, `ota.status = hash_mismatch` in the report |
| Alert thresholds dry < 25 %, wet > 85 %, low battery 3.4 V (**the 3.4 V value is Arsany's answer to A-008**) | `plants.dry/wet_threshold_pct` (defaults), `devices.low_battery_mv = 3400`, pushed in `config`; resolve with hysteresis 5 points / 100 mV (decided, A-018) |
| Plausible ranges temp -10..60 degC, RH 0..100, lux 0..100000, battery 3.0..4.25 V | `reading_is_plausible()`, `x-plausible` in the report schema, hub applies the same |
| FR-E03 = <= 15 min after the first tick that observes the event (fast-path classes only) | `trigger = critical`; event enum and critical set from edge-ai-concept 2.4: `wetting_unexpected`, `waterlogged`, `sensor_out_of_soil`, `sensor_fault` critical; `wetting`, `fast_drying` not |
| Dry threshold default 25 comes from the plant field, not the model | `config.dry_pct` |

## Premium entitlement (FR-P04, ADR-008, 4.B7)
- The flag is `profiles.is_premium`. A trigger refuses any change except by `postgres`/`service_role`; Arsany flips it in the Supabase dashboard: `update profiles set is_premium = true where id = '<uuid>';` (no payments, Req section 8).
- Enforced **server-side at four points**, the app only mirrors it for UI:
  1. `readings` RLS: free users read 7 days (FR-A06), premium all retained data (FR-P01). A free user querying 90 days through supabase-js gets 7.
  2. `tips` RLS: select only if premium (FR-P02); generation in the tips function also checks.
  3. `api_keys` creation: `/api-keys` returns 403 `premium_required`; MCP resolves the key with `mcp_resolve_key()`, which raises `premium_required` if the owner lost the flag.
  4. Analytics functions (4.B4) call `public.is_premium()` first.
- Switching the flag takes effect on the next request (no cached claim). Test (5.6): flip, repeat the same call, expect 200 vs 403.

## Cross-checks I could do (see "Verification")
- Every table in `db-schema.sql` has RLS enabled, test fails otherwise (NFR-06). Tables: profiles, plants, devices, device_credentials, claim_tokens, firmware_releases, plant_images, readings, readings_hourly, readings_hourly, events, alerts, push_tokens, tips, api_keys. The Plan lists seven; the other six are required by FR-A07, FR-D03, FR-D05, FR-P03 and ADR-004.
- Field names match across `device-report.schema.json`, `hub-mqtt.md`, `db-schema.sql` and `mcp-tools.json`.

## Verification (what was and was not run)
- **Run:** `db-schema.sql` + `db-schema.test.sql` on a local PostgreSQL 16 with a stub `auth` schema: loads without error, test prints `ALL OK` (RLS everywhere, user B sees nothing of A, self-grant of premium refused, free = 7 rows of 31 / premium = 31, alert dedupe, offline at 3 h 10 min and cleared by a report, plausibility ranges, 3-month raw / 12-month roll-up retention (roll-up values, outdated-hour rule, implausible excluded, idempotent, owner/RLS scoped, user cannot call it; mutation-checked), account-delete cascade, `delete_plant`: removes photos+readings, refused for foreign user and anon, sensor stays claimed, readings without plant kept).
- **Run:** `device-report.schema.json` is a valid Draft 2020-12 schema and accepts/rejects 1 valid + 4 invalid sample reports (now committed in `fixtures/`, run `python3 validate_fixtures.py`; the CI `interfaces` job validates `fixtures/device-report*.json` as valid, `fixtures/invalid/` is only checked by the script; Kai is adding OpenAPI/JSON validation to CI); `openapi.yaml` and `mcp-tools.json` parse and all local `$ref`s resolve.
- **Not run:** anything on a real Supabase project (`auth.uid()`, `storage` policies, pg_cron, the `current_user` role names used by the guard triggers are assumptions to confirm in 4.B1); OpenAPI linting with an external validator (not available here); BLE/MQTT on real devices; Edge Function limits for `/export` on large accounts.

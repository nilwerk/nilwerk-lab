# Test plan v1.0 — Plant Monitor (task 5.1)

Author: Ines (QA & Test Engineer). Milestone M2, gates G5 (after 5.10) and G2/G4a where a row says so.
Base: `origin/main` at 02e5c05 (worktree `agent/qa/5.1`); S4 update on `origin/main` at ca8b9ed, section 11 (rows FR-P01, FR-P04 and the bench round rows changed there). Status of every row: see the Status column; results are recorded in `tests/results/5.1.md`.
Internal document. Task IDs and file names are allowed here; no public text is derived from this file.

Source of requirements and tags: `tests/acceptance-matrix.md` (v1.0-candidate r3). This plan does not change requirements or criteria. Where the matrix says [proposed], the test is not PASS evidence until Arsany confirms.

## 1. Count and coverage

| Set | Count | Where |
|---|---|---|
| FR-* IDs in the matrix | 25 | Table 2 |
| NFR-* IDs in the matrix | 11 | Table 2 |
| **Total IDs, each appears once** | **36** | Table 2 (`grep` check: 0 duplicates) |
| Matrix label "Sec. 7 constraint" (not an ID) | 1 | Table 3 |

Not counted (not rows of the matrix, no test ID): FR-D08, FR-D09, FR-H01..H03, NFR-10, NFR-11 (proposed in `docs/architecture.md` 10.1, no Arsany answer; matrix open point 8). NFR-06c is a sub-criterion of NFR-06, not a separate ID.

Method: the 36 IDs were taken from the two requirement tables of `tests/acceptance-matrix.md` (lines 14–59) and counted with `grep` and `uniq -d`. For each ID, every test file on the branch was searched for the ID (`grep -l -F`); the result is in section 4.

## 2. How to read the table

Test types:
- **Auto**: runs in this environment or CI from the repo (command in the Automated column).
- **Bench** (Y): hands-on hardware, done by Peter through a work order (TEAM.md §12).
- **Manual**: phone or live-session checks by Arsany, or a document decision.

Status vocabulary (after the run in section 5):
- **PASS (auto)**: the automated part ran here and passed. A bench or manual part is still open unless the status says otherwise.
- **PARTIAL**: some automated parts pass; the rest is NOT RUN, NO TEST or BLOCKED as stated.
- **NOT RUN**: the test needs hardware, a tool, data or an account that was not available here (section 6).
- **NO TEST**: no automated test on the branch cites the ID.
- **BLOCKED (ID)**: a blocker recorded in a repo document (A-xxx or a task). Blockers come from `projects/plant-monitor/LESSONS.md` and the matrix.
- **FAIL**: a run failed.
- **NOT MET / OPEN**: the matrix or traceability says so; a decision by Arsany is needed.

Gate: G5 for every row, except NFR-08 (G4a, task 4.P3) and NFR-09 (G2, task 2.5), as the matrix states. No row is marked passed by an agent (TEAM.md §4).

## 3. Test plan table

Automated paths are relative to `projects/plant-monitor/`. The firmware host suite is run as `cmake -S firmware/test/host -B <build> && cmake --build <build> && ctest --test-dir <build>` (CI step "Host unit tests"). Test IDs `TP-<req>` are plan labels, not Plan rows.

### Table 2 — FR and NFR rows (36)

| Test ID | Req | Prio | Type | Automated test (on branch) | Bench / manual procedure | Task(s) | Gate | Status after this run |
|---|---|---|---|---|---|---|---|---|
| TP-FR-D01 | FR-D01 | M | Auto + Bench (Y+SW) | ctest `sensors_unit`, `board_v1_unit`, `cycle_unit` (`firmware/test/host`); `cloud/test/functions/api.test.ts` (ingest) | 24 h on-device log vs reference instruments; procedure to write (5.2/5.3) | 4.F1, 5.2, 5.3 | G5 | PARTIAL: host PASS; 24 h bench NOT RUN |
| TP-FR-D02 | FR-D02 | M | Auto + Bench (Y) | ctest `cycle_unit`, `report_contract_drift`, `upload_unit`; `app/src/__tests__/hourly.test.ts`; `api.test.ts` | 72 h run, SQL count of `readings` per day (23–25 per day, 3 days); procedure to write (5.5) | 4.F3, 5.5 | G5 | PARTIAL: host PASS; 72 h run NOT RUN |
| TP-FR-D03 | FR-D03 | M | Auto + Bench (Y) | ctest `provisioning_unit`, `provisioning_contract`, `provisioning_mutation_checks` (`test_prov.c`); `app/src/__tests__/bleProvisioning.test.ts`, `provisioning.test.ts`, `setupFlow.test.tsx` | Phone runs (1 iOS, 1 Android, 3 each) with timestamps and account screenshot; existing `tests/procedures/4.F2b-sec2-provisioning.md` (device side) | 4.A3b, 4.F2b, 5.5 | G5 | BLOCKED (4.A3b: real phone + BLE run not done); auto PASS. **Bench run pending** (partial scope: step c and d only, no account check; section 11) |
| TP-FR-D04 | FR-D04 | M | Auto + Bench (Y+SW) | ctest `report_buffer_unit`, `cycle_unit`, `upload_unit`; `firmware/test/host/test_report.c`; `api.test.ts` (idempotency); `docs/interfaces/db-schema.test.sql` (cloud 2.4 stage) | AP off 24 h, reconnect, SQL diff of expected 96 vs received sample timestamps; procedure to write (5.5) | 4.F3, 5.5 | G5 | PARTIAL: host PASS; 24 h outage NOT RUN |
| TP-FR-D05 | FR-D05 | M | Auto + Bench (Y) | ctest `ota_unit`, `ota_mutation_checks` (`test_ota.c`) | OTA from cloud; flash deliberately broken image; read version via reports or serial; procedure to write (5.5) | 4.F4, 5.5 | G5 | PARTIAL: host PASS; bench NOT RUN |
| TP-FR-D06 | FR-D06 | M | Auto + Bench (Y) | `app/src/__tests__/alerts.test.ts` (3399 mV opens, 3450 mV stays open, 3500 mV clears); ctest `sleep_decision_unit` | Bench supply and discharged cell, serial log, multimeter, LED photo per state; existing `tests/procedures/4.F3-vbat-thresholds.md`; charge-current part depends on A-094 | 4.F3, 5.2 | G5 | BLOCKED (A-094: LiPo max charge current measurement; open at last LESSONS entry, 20 Nov). Auto PASS |
| TP-FR-D07 | FR-D07 | M | Auto + Bench (Y) | ctest `provisioning_unit`, `sec2_unit` (`test_prov.c`, `test_sec2.c`); `app/src/__tests__/bleProvisioning.test.ts` | 3 of 3 pinhole resets, serial log shows NVS erase; `tests/procedures/4.F2b-sec2-provisioning.md` | 4.F2b, 5.5 | G5 | BLOCKED (4.F2b: per-unit provisioning on hardware not run, LESSONS S3). Auto PASS |
| TP-FR-D10 | FR-D10 | M | Auto (partial) + Bench (Y+SW) | `firmware/test/host/test_main.c`, soil calibration section (cites FR-D01 and NFR-02, not FR-D10). No test cites FR-D10 | Calibrate, fresh dry and wet samples, 3 reboots, OTA, compare serial raw values with `devices.cal_dry_raw` / `cal_wet_raw`; procedure to write (5.3, 5.5) | 4.F5, 5.3, 5.5, 5.6 | G5 | NO TEST cites FR-D10; bench NOT RUN. Matrix open point 7 (fresh sample, 3 reboots, per-soil storage) |
| TP-FR-A01 | FR-A01 | M | Auto + Manual (Arsany phones) | `app/src/__tests__/accountApi.test.ts`, `authState.test.tsx`, `deleteAccount.test.tsx`, `deleteAccountBypass.test.tsx`, `supabaseAuth.test.ts`; `app/e2e/web-flow.test.js` (sign-up, mock build); `cloud/test/functions/api.test.ts`; `cloud/test/rls_isolation.sql` | iOS and Android flows (Arsany); SQL check after account deletion incl. storage buckets on the real project | 5.6, 5.9 | G5 | PARTIAL: jest and cloud PASS; phones NOT RUN; storage SQL NOT RUN (local run skips buckets) |
| TP-FR-A02 | FR-A02 | M | Auto + Manual (Arsany) | `app/src/__tests__/plants.test.tsx`, `plantsSlice2.test.tsx`, `realPlantsRead.test.ts`; `cloud/test/functions/api.test.ts` (device-claim) | 3 claimed devices on one account, all report; schema check for no device cap | 5.6 | G5 | PARTIAL: jest and cloud PASS; 3-device run NOT RUN |
| TP-FR-A03 | FR-A03 | M | Auto + Bench (Y) | `app/src/__tests__/setupFlow.test.tsx`, `provisioning.test.ts`; `app/e2e/web-flow.test.js` (mock BLE, 8 of 8) | Stopwatch and screen recording with first-time users; same run as NFR-03 | 4.A3b, 5.5 | G5 | BLOCKED (4.A3b). Mock web flow PASS. **Bench run pending** (partial scope: step d only; section 11) |
| TP-FR-A04 | FR-A04 | M | Auto (API and E2E) | `app/src/__tests__/validation.test.ts`, `plantsSlice2.test.tsx`; `cloud/test/functions/api.test.ts`; `app/e2e/web-flow.test.js` | None (no bench) | 5.6 | G5 | PARTIAL: auto PASS. The location-type enum (house, balcony, garden, farm, greenhouse) was not found by grep in app tests; owner to confirm |
| TP-FR-A05 | FR-A05 | M | Auto + Manual (Arsany camera) | `app/src/__tests__/photoExport.test.ts`, `plantsSlice2.test.tsx`, `realPlantsRead.test.ts`, `setupFlow.test.tsx` | 12 photos uploaded to one plant on phone, sorted by date (Arsany) | 5.6 | G5 | PARTIAL: jest PASS; 12-photo E2E NOT RUN |
| TP-FR-A06 | FR-A06 | M | Auto + Manual (phone) | `app/src/__tests__/hourly.test.ts`, `plants.test.tsx`, `realPlantsRead.test.ts`; `app/e2e/web-flow.test.js` | API vs app comparison on phone; 168-point chart | 5.6 | G5 | PARTIAL: jest PASS; live comparison NOT RUN |
| TP-FR-A07 | FR-A07 | M | Auto + Manual (Arsany phone) | `app/src/__tests__/alerts.test.ts` (rules, hysteresis, offline at 3 h 05 / 3 h 10 / 3 h 15, moisture 29.9 % and 30.0 %, 3399 and 3500 mV); `alertsScreen.test.tsx`; `api.test.ts` (ingest) | Push receipt on test phone, each of 5 alert types exactly once | 5.6 | G5 | PARTIAL: rules PASS (jest); push delivery NOT RUN. Edge-AI alert kinds tied to FR-E02/E03 decision |
| TP-FR-A08 | FR-A08 | M | Auto + Manual (2 accounts) | `app/src/__tests__/plants.test.tsx`, `removeLeftover.test.tsx`, `realPlantsRead.test.ts`; `cloud/test/functions/api.test.ts`; `cloud/test/rls_isolation.sql` | Two-account E2E on release and re-claim (Arsany) | 5.6 | G5 | PARTIAL: jest and RLS PASS; two-account E2E NOT RUN |
| TP-FR-P01 | FR-P01 | M | Auto + E2E (seeded) | `cloud/analytics/test/aggregate.test.ts` (11 tests PASS; includes free users getting `premium_required` for 30 and 90 days) | Seeded UI check of four premium views; API call with free token gets 403 | 5.6 | G5 | PARTIAL (S4 update, ca8b9ed). RAN locally: `cloud/test/functions/analytics.test.ts` 13 of 13 (free user 403 `premium_required` and no plant or reading read; premium window=30 and 90 returns 200 with hand-computed values; RLS isolation, only the caller's plants), `cloud/analytics/test/aggregate.test.ts` 11 of 11; app `premiumDashboard.test.tsx`, `analyticsApi.test.ts`, `profileDashboardEntry.test.tsx` 25 of 25 (free: no fetch). NOT RUN: live Supabase, the PostgREST adapter (tests use local Postgres and injected deps), seeded UI check on a phone. NOT BUILT: the 30/90-day line chart; scope pending owner decision A-131. Not a Pass. See section 11 |
| TP-FR-P02 | FR-P02 | M | Auto (rule engine) + flag test | `cloud/tips/test/tips.test.ts`, `slice1b.test.ts`, `qa-adv.test.ts`, `qa-adv2.test.ts` (68 tests across these files, PASS in `cloud/test.sh`); guardrail list `tests/fr-p02-guardrails.md` | Optional live-Claude run by Arsany (not demo-blocking) | 5.6 | G5 | PARTIAL: 68 of 68 PASS. Guardrail list OPEN (Arsany approval, matrix open point 1). Flag-off and flag-on cases exist in `tips.test.ts` (mock assistant); not checked line by line. Deny-list bypasses open (LESSONS, cloud-ai) |
| TP-FR-P03 | FR-P03 | M | Auto + Manual (Arsany live Claude) | `cloud/tips/test/slice1b.test.ts`; `docs/interfaces/mcp-tools.json` (parses, cloud 2.4 JSON check) | Live Claude session: lowest-moisture plant, 3 of 3 runs (Arsany); revoke test, 401 within 1 min | 5.6, 5.9 | G5 | PARTIAL: MCP tool contract tests NOT FOUND by grep; live session NOT RUN |
| TP-FR-P04 | FR-P04 | M | Auto | `cloud/analytics/test/aggregate.test.ts` (premium gate); `cloud/test/rls_isolation.sql` (user A cannot grant itself premium); `docs/interfaces/db-schema.test.sql` | Toggle flag in DB, access changes within 1 min (SQL or API) | 5.6 | G5 | PARTIAL (S4 update, ca8b9ed). RAN locally: analytics endpoint free user 403 with no read and premium 200 (`analytics.test.ts` 13 of 13, real `is_premium()` on migrated local Postgres), `rls_isolation.sql` RLS ISOLATION OK, `aggregate.test.ts` 11 of 11. NOT RUN: live Supabase and PostgREST adapter, 1-minute flag toggle timing (the [proposed] 1 min), access to FR-P02 and FR-P03 on the live project. Not a Pass. See section 11 |
| TP-FR-I01 | FR-I01 | C | Manual (Arsany HA) | None on branch | Check HA entity list against app values (Arsany) | 5.6 | G5 | NO TEST. Could-item: waive if not delivered (matrix) |
| TP-FR-E01 | FR-E01 | M | Auto (metric code) + Manual (display) + public-data eval | `ml/tests/test_evaluate.py`, `test_features.py`, `test_contracts.py`, `test_export.py` (ml pytest: 140 PASS, 2 skipped); held-out MAE on public data | App shows forecast from device report (phone); bench calibration | 4.AI3, 5.8 | G5 | PARTIAL: unit PASS; held-out MAE NOT RUN (Mendeley data not downloaded); bench calibration BLOCKED (A-094: 4.AI3 waits for it, LESSONS) |
| TP-FR-E02 | FR-E02 | M | Auto (held-out eval) + Bench (field soak) | `ml/tests/test_evaluate.py`, `test_event_classes.py`, `test_event_classes_default_pad.py`, `test_labels.py` (ignore-mask rule, A-032) | Field soak 48 h on 3 units, at most 1 false alert in total; written waiver for the one-week observation | 4.AI3, 5.8 | G5 | NOT MET as shipped (matrix, traceability). Held-out recall and precision NOT RUN (data). Field soak NOT RUN (units). OPEN: G5 waiver or second data source; precision reading A-019 |
| TP-FR-E03 | FR-E03 | M | Auto (ingest and labels) + Bench (staged events) | `cloud/test/functions/api.test.ts` (FR-E03 cited at /ingest); `ml/tests/test_labels.py`; ctest `sleep_decision_unit` (`test_sleep.c`) | 5 of 5 staged events (wetting, out of soil, sensor fault): push within 15 min of first observing tick (Peter stages, Arsany receives) | 5.8 | G5 | NOT MET as shipped (2-of-3 debounce adds up to 30 min, matrix). OPEN: G5 decision |
| TP-FR-E04 | FR-E04 | M | Auto (flash) + Bench (RAM, inference) | CI "Model budget check" (model file ≤ 30 720 B): `ml/models/model_b_wetting_int8.tflite` = 3 664 B, PASS; `ml/tests/test_contracts.py`, `test_export.py` | ESP-IDF size report from build; heap logs; one `Invoke()` timed on board | 5.8 | G5 | PARTIAL: flash budget PASS; RAM and inference NOT RUN (no board, no ESP-IDF) |
| TP-NFR-01 | NFR-01 | — | Auto (design check) + Bench (Y) | `hardware/power-budget/test_power_budget.py` (30 tests PASS, `python3 -m unittest discover -v`); ctest `sleep_decision_unit` | Measured hourly average current on assembled board, scenarios M1..M6 (power analyzer); arithmetic in report | 2.3 (design), 5.4 | G5 | PARTIAL: design check PASS; measured NOT RUN. Matrix says the worst-case 730 h verdict line is still to be added to the script (not checked by me) |
| TP-NFR-02 | NFR-02 | — | Bench (Y) | `firmware/test/host/test_main.c` (soil calibration section, cites NFR-02) | ±5 points vs gravimetric reference, temp ±0.5 °C, RH ±3 %RH; potting and garden soil, n ≥ 5 per point, 3 units; procedure to write (5.3) | 4.F5, 5.3 | G5 | NOT RUN (hardware) |
| TP-NFR-03 | NFR-03 | — | Auto + Bench (Y) | `app/src/__tests__/setupFlow.test.tsx`, `theme.test.ts` (cites NFR-03); `firmware/test/host/test_prov.c` | Stopwatch, 3 first-time users, median ≤ 180 s and none > 240 s (same run as FR-A03) | 5.5 | G5 | BLOCKED (4.A3b). Auto PASS |
| TP-NFR-04 | NFR-04 | — | Auto (cloud) + Phone timing | `cloud/test/functions/api.test.ts` (cites NFR-04, ingest) | ≥ 20 uploads, server timestamp vs app-visible time, ≤ 120 s for 100 % (live Supabase and phone) | 5.6 | G5 | PARTIAL: citation only; live timing NOT RUN. **Bench run pending** (step e shows a row arrived; latency is not measured; section 11) |
| TP-NFR-05 | NFR-05 | — | Bench (Y) + CAD geometry (auto) | `mechanical/enclosure_v3/test_v3.py` (geometry checks; needs cadquery, NOT RUN here). No test cites NFR-05 | IPX4-style spray test, 10 min from all sides; enclosure UV datasheet (ASA or PETG-UV); wall ≥ 1.2 mm; procedure to write (5.7) | 5.7, 4.E3, 4.E5 | G5 | BLOCKED (A-094: part heights and under-board height open; v1 fit check, 4.E5). Geometry NOT RUN |
| TP-NFR-06 | NFR-06 | — | Auto (cloud, app, firmware) + checks | `cloud/test/rls_isolation.sql` (PASS), `cloud/test/openapi_check.py` (PASS), `api.test.ts`; `app/src/__tests__/supabaseAuth.test.ts`, `bleProvisioning.test.ts`; ctest `sec2_unit`, `sec2_mutation_checks` | TLS scan (a); device-token scope test (b); revoked MCP key (d); secret scan (e); real Supabase | 5.9 | G5 | PARTIAL: (c) SQL PASS on local Postgres; Storage RLS NOT COVERED; (a), (b), (d), (e) NOT RUN. Accepted risk A-110 (plaintext BLE setup codes on 3 demo units). **Bench run pending** (partial scope: step e, one row reached the cloud; section 11) |
| TP-NFR-07 | NFR-07 | — | Auto + Manual + SQL | `app/src/__tests__/exportClient.test.ts`, `exportGate.test.ts`, `deleteAccount*.test.tsx`, `photoExport.test.ts`, `fileHandOff.test.ts`, `zip.test.ts`; `cloud/test/functions/export.test.ts` (22 PASS); `api.test.ts` | EU region screenshot (Arsany); JSON and CSV export on real project; delete leaves 0 rows incl. storage (SQL) | 5.9 | G5 | BLOCKED (A-108: export function merged but not deployed until A-108 is approved, LESSONS). Auto PASS locally. **Bench run pending** (step e does not check the region, export or delete; section 11) |
| TP-NFR-08 | NFR-08 | — | Auto (PCB) + Manual checklist | `pcb/check_layout.py` (all layout checks PASS: antenna keep-out, via-in-pad); `pcb/check_netlist.py` (ALL CHECKS PASS); ERC/DRC via kicad-cli (CI pcb job) | PCB review checklist fully ticked, ESD on USB lines (4.P3, Arsany sign-off) | 4.P3 | G4a (not 5.x) | PARTIAL: layout and netlist PASS; ERC/DRC NOT RUN (kicad-cli missing); checklist NOT RUN |
| TP-NFR-09 | NFR-09 | — | Auto (BOM) | `hardware/bom/test_bom.py`: 13 of 15 PASS | BOM tab completeness check (2.5) | 2.5 | G2 (not 5.x) | FAIL: 2 tests fail (doc prose vs CSV; see section 7) |
| TP-NFR-12 | NFR-12 | M | Auto (design check) + Bench (Y) | `hardware/power-budget/test_power_budget.py` (sleep-current tests PASS); `firmware/test/host/test_cycle.c`, `test_main.c`; ctest `board_pins_cite_pinmap` | µA meter, 60 s mean at battery terminal, 3.7 V, 3 units; procedure to write (5.2, 5.4) | 5.2, 5.4 | G5 | PARTIAL: design check PASS; measured NOT RUN. Open 4.P1 item: U7 supply GPIO held low in deep sleep (`hardware/bom/bom-draft.md`) |
| TP-NFR-13 | NFR-13 | M | Auto (local Postgres) + Real Supabase | `cloud/test/retention.sql` (RETENTION OK); `docs/interfaces/db-schema.test.sql` (2.4 stage); both PASS in `cloud/test.sh` | Real Supabase: pg_cron job entry and log, nightly run with back-dated rows | 5.9 | G5 | PARTIAL: local PASS; real pg_cron and nightly run NOT RUN (local run uses `nilwerk.allow_no_cron=on`) |

### Table 3 — matrix label without an ID

| Test ID | Label | Type | Automated test | Procedure | Task(s) | Gate | Status |
|---|---|---|---|---|---|---|---|
| TP-SEC7 | Sec. 7 constraint: iOS 16+ and Android 10+ (no NFR number) | Manual (Arsany phones) | None | Install, setup (FR-A03) and data (FR-A06) on one iOS 16+ and one Android 10+ phone, with OS version and screen recording | 5.5, 5.6 | G5 | NOT RUN (phones) |

## 4. Plan task index (5.2–5.10)

Task IDs are those cited in `tests/acceptance-matrix.md`. The Plan sheet (titles, dates, gate tab) is not in the repo and was not read for this plan.

| Plan ID | Rows that name it as a proving task | Count |
|---|---|---|
| 5.2 | TP-FR-D01, TP-FR-D06, TP-NFR-12 | 3 |
| 5.3 | TP-FR-D01, TP-FR-D10, TP-NFR-02 | 3 |
| 5.4 | TP-NFR-01, TP-NFR-12 | 2 |
| 5.5 | TP-FR-D02, TP-FR-D03, TP-FR-D04, TP-FR-D05, TP-FR-D07, TP-FR-D10, TP-FR-A03, TP-NFR-03, TP-SEC7 | 9 |
| 5.6 | TP-FR-D10, TP-FR-A01, TP-FR-A02, TP-FR-A04, TP-FR-A05, TP-FR-A06, TP-FR-A07, TP-FR-A08, TP-FR-P01, TP-FR-P02, TP-FR-P03, TP-FR-P04, TP-FR-I01, TP-NFR-04, TP-SEC7 | 15 |
| 5.7 | TP-NFR-05 | 1 |
| 5.8 | TP-FR-E01, TP-FR-E02, TP-FR-E03, TP-FR-E04 | 4 |
| 5.9 | TP-FR-A01, TP-FR-P03, TP-NFR-06, TP-NFR-07, TP-NFR-13 | 5 |
| 5.10 | No row names 5.10 as a proving task. The matrix says 5.10 and G5 need every row passed or waived with a written reason. | 0 (gate) |

Other task IDs named in rows: 4.F1, 4.F2b, 4.F3, 4.F4, 4.F5, 4.A3b, 4.AI3, 4.P3 (G4a), 4.E3, 4.E5, 2.3, 2.5 (G2).
Note for Nora: the matrix says the Plan has 5.9 and 5.10 after 5.8, and G5 moves to after 5.10 (matrix, Requirements additions note). Quality Gates tab not read here.

## 5. Automated runs (this environment, base 02e5c05; counts are historic, current counts in section 11)

All runs on the 5.1 worktree at 02e5c05 (equal to origin/main). Working tree was clean apart from gitignored build output.

| Suite | Command | Result |
|---|---|---|
| Firmware host unit and contract tests (CI "Host unit tests") | `cmake -S firmware/test/host -B <scratch>/build-host && cmake --build ... && ctest --test-dir ...` | **26 of 26 PASS**, 0 failed, 70.8 s (includes sensors, board, cycle, report buffer, OTA, provisioning, sec2, upload, sleep units, contract checks and mutation checks) |
| Cloud DB and API tests (CI "Cloud DB tests") | `bash projects/plant-monitor/cloud/test.sh` (local PostgreSQL 16.15, throwaway cluster) | exit 0, **ALL CLOUD TESTS PASSED**. Stages: migration freeze PASS; 2.4 contract (`db-schema.sql` vs migrations) PASS; RLS isolation PASS; retention ("RETENTION OK") PASS; OpenAPI check 71 checks PASS; edge functions `api.test.ts` 23 of 23; export `export.test.ts` 22 of 22; care tips 68 of 68 (4 files); analytics `aggregate.test.ts` 11 of 11 |
| App typecheck (CI "lint" = `tsc --noEmit`) | `npm ci` then `npx tsc --noEmit` in `projects/plant-monitor/app` | exit 0 |
| App unit tests (CI "npm test") | `npm test -- --ci` (jest) | **29 of 29 suites, 418 of 418 tests PASS** |
| App web-flow e2e (mock build, Playwright) | `npm run test:web-flow` | **8 of 8 PASS**, 0 fail (mock auth and BLE, not the live backend) |
| ML tests (CI "ml") | `pytest -q` in `projects/plant-monitor/ml` (pytest on Python 3.13; CI uses 3.11) | **140 passed, 2 skipped**. Skips: `test_loaders.py:66` (Mendeley files not downloaded), `test_train.py:155` (TensorFlow not installed) |
| ML model budget (CI) | size of `ml/models/*.tflite` vs 30 720 B | `model_b_wetting_int8.tflite` 3 664 B: PASS |
| Power budget (CI "power-budget tests") | `python3 -m unittest discover -v` in `hardware/power-budget` | **30 tests OK** (all in `test_power_budget`). The matrix says 23; the matrix count is stale |
| Cost model (CI "cost-model tests") | `python3 -m unittest discover -v` in `docs/costs` | **17 tests OK** |
| Interface schemas and fixtures (CI "Validate schemas and fixtures") | Python script of the CI step, run directly | 1 schema, 1 valid fixture ok, 7 JSON and 1 YAML parsed: overall OK |
| Interface fixtures, valid and invalid | `python3 docs/interfaces/validate_fixtures.py` | exit 0: valid fixture accepted; 4 invalid fixtures rejected |
| Soil frontend (hardware) | `pytest -q test_soil_frontend.py` in `hardware/soil-frontend` | **4 of 4 PASS** |
| BOM (hardware) | `python3 -m unittest test_bom -v` in `hardware/bom` | **13 of 15 PASS, 2 FAIL** (section 7) |
| PCB netlist check (CI pcb job) | `python3 pcb/check_netlist.py` | exit 0, "ALL CHECKS PASS" (note printed: footprints still to be drawn SW1, SW2, SW3, E1) |
| PCB layout check (CI pcb job) | `python3 pcb/check_layout.py` | exit 0, "all layout checks PASS" (278 track segments; GND zone not filled; signal nets not routed, per script output) |

Counts above are the numbers printed by each tool in this run. No number was copied from a PR body, a commit message or a matrix row. The CI logs for these jobs on the PR head are the authoritative counts once the PR is in CI.

## 6. Not run

Each item is a test in the plan that could not run here, with the reason.

| Test | Why not run |
|---|---|
| All bench rows (Y): TP-FR-D01/D02/D04/D05/D06/D07/D10, TP-FR-A03, TP-NFR-01/02/03/05/12, TP-FR-E03 staged events, TP-FR-E02 field soak | No hardware in this environment. Hardware work is Peter's through work orders (TEAM.md §5, §12). The firmware build and host tests are not evidence of hardware behaviour (playbook rule 32). |
| Firmware QEMU boot check (`firmware/tests/qemu_boot_check.sh`) and ESP-IDF builds, `idf.py size` (TP-FR-E04 RAM part, TP-FR-D01 size) | ESP-IDF and QEMU not installed (`idf.py` and `qemu-system-riscv32` missing). |
| KiCad ERC/DRC and fabrication exports (TP-NFR-08) | `kicad-cli` not installed; the CI pcb job runs in the KiCad 9 container. |
| ngspice simulations (4.P1 sims) | `ngspice` not installed. |
| Mechanical geometry (TP-NFR-05): `mechanical/test_bay.py`, `mechanical/enclosure_v3/test_v3.py`, `mechanical/jlc_prep/test_jlc_prep.py` | `test_bay.py` fails at collection (`trimesh` missing); cadquery missing for the v3 tests. |
| ML held-out evaluation (TP-FR-E01, TP-FR-E02 recall and precision) and 2 skipped ML tests | Public datasets not downloaded in this environment (`ml/scripts/fetch_mendeley.sh` not run); TensorFlow not installed, so the training and TFLite export tests skip. |
| Cloud mutation suites (`cloud/test/mutation.sh`, `cloud/tips/test/mutation.sh`, CI `cloud-mutation.yml`) | Nightly job of about 14–18 min, not run here. Last CI run figures are in LESSONS.md (devops section); I did not verify them. |
| Real Supabase: Auth, PostgREST, Storage buckets, `pg_cron` schedules, nightly retention job (TP-NFR-06, TP-NFR-07, TP-NFR-13, TP-FR-A01 storage, TP-FR-P04 timing) | No project access in this run; local PostgreSQL only, with `pg_cron` and storage skipped. |
| Phone E2E on iOS and Android (TP-FR-A01, A02, A05–A08, TP-NFR-03/04, TP-SEC7) and live Claude session (TP-FR-P03) | Arsany's phones and session. Not available to QA. |
| TLS scan, secret scan, revoked-key test (TP-NFR-06 a, d, e) | No tool run; the revoke test needs the live API. |
| `firmware/test/host` tests on the CI runner image | Ran here with the local toolchain (gcc, cmake, ctest), not the CI runner. |

## 7. Failures and mismatches found

1. **TP-NFR-09: BOM tests fail on main (2 of 15).** `hardware/bom/test_bom.py`: `test_doc_matches_csv` expects `6.56` (CSV total) in the doc, but the doc has `6.57`; `test_prose_has_no_stale_schematic_claims` expects the CSV live-data stamp `2026-11-09 20:17 UTC` in the doc header, but the doc says `2026-11-08 15:12 UTC`. The CSV was refreshed and the doc was not. Owner: Emil (2.5). Not fixed here (out of scope).
2. **Matrix count is stale.** The matrix says `test_power_budget.py` has 23 tests (run 2026-11-07). This run found 30 tests, all in that file, all passing. The matrix should be updated by its owner.
3. **FR-A04 location types:** the grep for `greenhouse` in app tests found nothing. Confirm the enum test exists.
4. **FR-D10 has no test that cites it.** Matrix open point 7 is still open.
5. **FR-P03 MCP tool contract tests** (matrix row) were not found by grep on the branch.
6. **NFR-05 has no test that cites it**, and the geometry check cannot run here.
7. **Records:** `tests/results/` is empty on main. Per-task records are added as each row closes.

## 8. Open points and blockers (for Nora to log in Needs Arsany)

Nothing in this plan is marked passed or waived. These need a decision or a hand from Arsany (TEAM.md §9). A-IDs are the ones cited in repo documents; new items would need Nora's numbers.

| Item | Affects | Source | Blocked or open |
|---|---|---|---|
| A-094 v1 bench checks (R3 across TP4056 PROG, LiPo max charge current, soil AOUT in air, part heights). Last recorded as overdue, open 20 Nov | TP-FR-D06 charge part, TP-FR-E01 bench calibration, TP-FR-E02 field calibration, TP-NFR-05 fit | LESSONS.md (pcb, mechanical, qa) | BLOCKED |
| A-108 approve export function deploy and migration (path guard, DB CHECK) | TP-NFR-07 live export | LESSONS.md (cloud-ai, fullstack) | BLOCKED |
| G5 decision on FR-E02 and FR-E03 (written waiver or second data source; precision reading A-019) | TP-FR-E02, TP-FR-E03, TP-FR-A07 edge-AI alerts | matrix; traceability.md; edge-ai-concept.md | OPEN |
| FR-P02 guardrail list approval (matrix open point 1) | TP-FR-P02 | matrix; `tests/fr-p02-guardrails.md` | OPEN |
| Live Claude session run by Arsany (3 of 3) | TP-FR-P03 | matrix | OPEN |
| A-110 plaintext BLE setup codes on 3 demo units (accepted for demo) | TP-NFR-06 (b) | LESSONS.md | Accepted risk, to revisit before live units |
| A-111 150 MB export cap not measured | TP-NFR-07, TP-FR-A05 | LESSONS.md | OPEN |
| A-112 named watcher for nightly cloud mutation run | Mutation suite (not a row) | LESSONS.md | OPEN |
| Hardware runs: 4.A3b phone and BLE, 4.F2b per-unit provisioning, 4.F3 upload on hardware | TP-FR-D03, D07, A03, NFR-03 | LESSONS.md (S3 19 Nov) | BLOCKED (work orders for Peter, via Nora) |
| U7 supply GPIO held in deep sleep, TP4056 TEMP pin (NTC or not), 500 mA USB check | TP-NFR-12, TP-FR-D06 | `hardware/bom/bom-draft.md` checklist for 4.P1 | OPEN (4.P1) |

## 9. Test IDs for the bench procedures

Procedures written so far under `tests/procedures/`: `4.F2b-sec2-provisioning.md` (TP-FR-D03, TP-FR-D07) and `4.F3-vbat-thresholds.md` (TP-FR-D06). Procedures for TP-FR-D01/D02/D04/D05/D10, TP-NFR-02, TP-NFR-05, TP-NFR-12 and TP-FR-E03 are not written yet. They are QA work under 5.2–5.5 and 5.7, and are the next step after this plan is merged.

## 10. Reproduce

From the repo root, after `git fetch origin main` and a worktree on the branch:
1. Firmware host: `cmake -S projects/plant-monitor/firmware/test/host -B /tmp/<scratch>/build-host && cmake --build /tmp/<scratch>/build-host && ctest --test-dir /tmp/<scratch>/build-host`
2. Cloud: `bash projects/plant-monitor/cloud/test.sh`
3. App: `cd projects/plant-monitor/app && npm ci && npx tsc --noEmit && npm test -- --ci && npm run test:web-flow`
4. ML: `cd projects/plant-monitor/ml && pytest -q`
5. Hardware and docs: `python3 -m unittest discover -v` in `hardware/power-budget` and `docs/costs`; `python3 -m unittest test_bom -v` in `hardware/bom`; `pytest -q test_soil_frontend.py` in `hardware/soil-frontend`
6. Interfaces: `python3 docs/interfaces/validate_fixtures.py`
7. PCB: `python3 pcb/check_netlist.py` and `python3 pcb/check_layout.py`


S3 Lessons: [the matrix had drifted from the code: its power-budget test count (23) was stale against the 30 tests that run, and one CI-gated suite (BOM) was red on main without a visible flag] → [recount tests from the tool output and re-grep the IDs before any row changes status; a red test on main is reported in the plan, not left to the next reader].

## 11. S4 update (24 Nov 2026): what ran on main, what did not

Base: `origin/main` ca8b9ed in a clean worktree (`git status --porcelain` empty). Ancestry of the two merged slices: `git merge-base --is-ancestor a6185f4 origin/main` exit 0 (analytics endpoint), same for 76dbd72 exit 0 (premium dashboard). No test code was changed. Section 5 numbers are from 02e5c05 and are historic.

### 11.1 Commands run and counts (this run)

| Command | Result |
|---|---|
| `bash projects/plant-monitor/cloud/test.sh` (local PostgreSQL, 33 s) | exit 0, ALL CLOUD TESTS PASSED. RLS ISOLATION OK; RETENTION OK; 2.4 contract ALL OK; edge functions `api.test.ts` 23 of 23; export 22 of 22; MCP 32 of 32; **analytics endpoint `analytics.test.ts` 13 of 13**; care tips 68 of 68; **analytics pure `aggregate.test.ts` 11 of 11**. 0 failed, 0 skipped in every stage. Files in the three test folders: 9 (api, export, mcp, analytics, aggregate, 4 tips files); all 9 ran |
| `npm ci && npx tsc --noEmit` in `projects/plant-monitor/app` | exit 0 |
| `npx jest --ci` in `projects/plant-monitor/app` | 32 suites passed of 32, **443 tests passed of 443** (section 5 had 29 and 418). Premium slice alone: `premiumDashboard.test.tsx`, `analyticsApi.test.ts`, `profileDashboardEntry.test.tsx` = 3 suites, 25 tests |

Not re-run in this round: firmware host ctest, ML pytest, hardware tests, PCB checks, web-flow e2e (section 5 numbers stay as recorded at 02e5c05, not re-verified at ca8b9ed).

### 11.2 TP-FR-P01 and TP-FR-P04

| Item | State |
|---|---|
| Free user, API: 403 `premium_required`, no plant or reading read | RAN, PASS locally (`analytics.test.ts`: injected deps and real `is_premium()` on local Postgres) |
| Premium user, API: 200, window 30 and 90, hand-computed aggregates for Basil, zeros for Aloe | RAN, PASS locally |
| RLS isolation: answer names only the caller's plants | RAN, PASS locally (`analytics.test.ts`, `rls_isolation.sql`) |
| App: free account makes no analytics call and sees the upgrade message; premium sees windows, empty, error and ready states from a fixture | RAN, PASS (jest, 25 tests, fixtures, not the live API) |
| Live Supabase (Auth, PostgREST adapter, real project data) | NOT RUN (no project access in this run) |
| PostgREST adapter (`makeAnalyticsDeps`) against a real PostgREST | NOT RUN; local tests use a database driver, not PostgREST |
| Seeded UI check of the four premium views on a device | NOT RUN |
| 30/90-day line chart | NOT BUILT (the dashboard shows aggregates per window; `MoistureChart` is the 7-day chart only). Scope pending owner decision A-131 |
| FR-P04 flag toggle gives or removes access within 1 min [proposed] | NOT RUN (timing needs a live project) |

Neither row is Pass. FR-P01 also cannot pass while the chart scope is undecided.

### 11.3 Bench round rows (run 45434991511)

Criterion: a row may leave "bench run pending" only when the named steps of a bench run on main have completed, with the run id and step letters in this section.

Check at 17:20 (Berlin, 24 Nov), command `gh api repos/nilwerk/nilwerk-lab/actions/runs/45434991511 --jq '[.status,.conclusion]|@tsv'`: `in_progress` with no conclusion. Head SHA ca8b9ed (event workflow_dispatch). Jobs from `.../jobs`:
- build setup firmware (GitHub-hosted): completed, success. This is a build job. It is not a bench step.
- Android debug APK (GitHub-hosted): completed, success at 17:26 Berlin (a build job, not a bench step).
- bench smoke and E2E (the Pi): in progress at 17:26 Berlin. At 17:26:39 only setup steps (job start, checkout, clear artifacts, runner smoke check) had completed; step 1 (download firmware) was in progress and steps 2, a, 3, c, b, 4, d, e and E2E were pending. None of the bench steps has completed.

So the run is in progress and no bench step has completed. All rows below stay pending.

| Row | Bench steps that touch it (workflow header) | Status now |
|---|---|---|
| FR-D03 | c (find device by name), d (write setup data, app shows connected). Not checked: device claimed by, or visible in, the user's account | bench run pending (partial scope only) |
| FR-A03 | d only. Not checked: the rest of the setup flow | bench run pending (partial scope only) |
| NFR-04 | e (a row reached the cloud after test start). Latency not measured | bench run pending |
| NFR-06 | e (one row from this device reached the cloud). Per-device credentials and user isolation not checked | bench run pending (partial scope only) |
| NFR-07 | not checked by the workflow (one row in the project named by the config; region, export and delete not tested) | bench run pending; the workflow alone cannot pass it |

When the run completes, update this table with the run conclusion and, per step letter, only the steps whose status is `completed` and `success`. Even then the workflow header says it passes none of these rows alone.

### 11.4 Open decisions that block rows

| ID | Blocks | State |
|---|---|---|
| A-131 | FR-P01 (30/90-day line chart) | open, tracked in the Needs Arsany tab |
| A-115 | FR-P01 watering-event thresholds (provisional in code and OpenAPI, text still says TO CONFIRM) | decided; code comments and `openapi.yaml` not yet updated (docs only here) |
| A-129 | row link given by the Lead, not backed by a repo file | open, tracked in the Needs Arsany tab |
| A-130 | row link given by the Lead, not backed by a repo file | open, tracked in the Needs Arsany tab |
| A-108, A-094 | unchanged, see section 8 | as in section 8 |

The repo has no source text for A-129, A-130 or A-131 (grep of all .md, .yml, .ts files: 0 hits). They are listed by ID only, tracked in the Needs Arsany tab, which is not in the repo.

S4 Lessons: [a status table that says PASS for a slice whose live backend and chart never ran reads as earned] → [list ran and not run side by side; a bench row stays pending until its steps show completed and success].

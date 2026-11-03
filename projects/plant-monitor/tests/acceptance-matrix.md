# Acceptance matrix v0.1 — Plant Monitor (task 1.5)

Source: Requirements v0.1 (Google Doc `1T4k3rK4KQDeGtIN8pjdmohGUAohFrtATLhMYSBsYA6g`, draft 2026-11-02) and Plan tasks 5.1–5.9.
Author: Ines (QA & Test Engineer). Requirements are **not changed** here: where the requirement text is vague, the "Measurable pass/fail" column proposes a measurable reading (marked **[proposed]**) and the gap is listed in *Open points for G1* below.
Status of every row: **not run** (nothing is built yet). Status is updated per PR in `tests/results/<task-id>.md`.

Bench column: **Y** = Arsany must do it with hardware/phone/people (procedure written in 5.x), **SW** = QA can run it automatically, **Y+SW** = both.
Prio: M must, S should, C could (from the Requirements doc).

## Functional requirements

| Req ID | Requirement | Prio | Measurable pass/fail | Test method | Proving task | Bench? |
|---|---|---|---|---|---|---|
| FR-D01 | Measure soil moisture, air temp, air humidity, light, battery level | M | PASS if every report in a 24 h run contains all 5 fields, none null/NaN, and each is inside the plausible range **[proposed]**: temp −10…60 °C, RH 0…100 %, lux 0…100 000, battery 3.0…4.25 V, soil raw ADC within dry/wet calibration band. Any missing/out-of-range value = FAIL. | Host unit tests on drivers (Unity) for parse/range; on-device 24 h log of reports compared to reference instruments | 5.2, 5.3 (+4.F1 unit tests) | Y+SW |
| FR-D02 | Report to cloud once per hour | M | PASS if `readings` rows for the device in each of 3 consecutive 24 h days number 23–25 (24 ± 1), with inter-report gaps 60 ± 5 min **[gap tolerance proposed]**. | SQL count per day on the ingest table after a 72 h run | 5.5 | Y |
| FR-D03 | BLE setup mode (first boot / button): Wi-Fi creds, device name, claim token | M | PASS if on 1 iOS and 1 Android phone (min. 3 runs each) setup completes and the device shows in the user's account within 60 s of provisioning; wrong password gives an error and device stays in setup mode. | Bench procedure with timestamps + account screenshot; app-side provisioning unit tests with mocked BLE | 5.5 | Y |
| FR-D04 | Store readings offline, upload later | M | PASS if after 24 h without Wi-Fi and reconnect, the cloud holds all 96 × 15-min samples / 24 hourly records of the outage (0 missing, 0 duplicates, timestamps preserved). | Disable AP for 24 h, reconnect, diff expected vs received timestamps (SQL) | 5.5 (+4.F3 host test of ring buffer) | Y+SW |
| FR-D05 | OTA firmware + model update with rollback | M | PASS if (a) a signed newer image installs and the new version is reported within 1 report cycle; (b) a deliberately broken image reverts to the previous version automatically and device resumes reporting; (c) an unsigned image is refused **[c proposed, see open point]**. | Bench: trigger OTA from cloud, then flash broken image; read version via reports/serial log | 5.5 | Y |
| FR-D06 | Low-battery warning; USB-C charging with charge LED | M | PASS if low-battery event is sent when battery voltage crosses the threshold (value to be fixed, open point) and LED shows distinct states for charging and full; charge current measured ≤ charger spec. | Bench: bench supply / discharged cell, serial log, multimeter; LED photo per state | 5.2 | Y |
| FR-D07 | Factory reset with pinhole button | M | PASS if after pinhole press (hold time as specified in firmware) stored Wi-Fi + claim token are erased (verified by reboot: device is in setup mode, no connection attempt) in 3/3 trials. | Bench procedure; serial log shows NVS erase | 5.5 | Y |
| FR-A01 | Sign up/in, profile, sign out, delete account | M | PASS if each flow works on iOS and Android and after account deletion 0 rows remain for that user_id in all tables and storage buckets (SQL check). | E2E script (Detox/API) + SQL assertion | 5.6, 5.9 | SW (+Y for phone UI) |
| FR-A02 | Unlimited devices per user | M | PASS if one account holds 3 claimed devices and all appear and report. No code-level device cap (grep/schema check: no limit constraint). | E2E with 3 devices; schema review | 5.6 | Y+SW |
| FR-A03 | Setup flow: device → Wi-Fi → name → photo → plant details | M | PASS if 5 steps complete in order and plant+device record exists. Timing criterion is under FR-A03/NFR-03: ≤ 180 s median over ≥ 3 first-time users, none > 240 s **[proposed]**. | Stopwatch with first-time users, screen recording | 5.5 | Y |
| FR-A04 | Plant details fields (name, location type, room/area, soil type, optional species, city) | M | PASS if all 6 fields can be set, edited, persisted after app restart and read back via API with identical values; location type accepts exactly house/balcony/garden/farm/greenhouse; species optional (empty accepted), others required. | API contract tests + E2E | 5.6 | SW |
| FR-A05 | Unlimited photos per plant, with date | M | PASS if 12 photos uploaded to one plant all appear, sorted by date (ascending/descending as specified in design), each with its date; no cap in schema. | E2E + storage listing | 5.6 | SW (+Y for camera) |
| FR-A06 | Plant list with status; detail with latest values + 7-day chart | M | PASS if the app's latest values equal the last uploaded report (exact) and the chart shows 168 hourly points (±1 report cycle of lag). | API vs app comparison in E2E | 5.6 | Y+SW |
| FR-A07 | Push alerts: too dry, too wet, low battery, offline, edge-AI events | M | PASS if each of the 5 alert types is delivered exactly once on a test phone per triggered condition (no duplicates within 1 h, no missed). Thresholds: see open point. | E2E: inject readings/events; check notification receipt and alert table | 5.6 | Y |
| FR-A08 | Edit/remove plants and devices; release a device for re-claim | M | PASS if edit persists; removing a plant keeps/clears its data as specified; a released device is claimed by a second account and then appears there and no longer in the first. | E2E with 2 accounts | 5.6 | Y+SW |
| FR-P01 | Premium graphs: 30/90-day history, trends, watering events, plant comparison | M | PASS if a free user gets denied (UI hidden AND API 403) and a premium user sees all four views with seeded data (30 and 90 days). | Seeded data E2E; API call with free token | 5.6 | SW |
| FR-P02 | Care tips from location, weather, season, plant, soil, readings | M | PASS if (a) changing the weather input (hot/dry vs rain) or season changes the tip text in ≥ 3 seeded scenarios; (b) guardrail suite of ≥ 20 adversarial/edge inputs yields 0 unsafe tips (e.g. toxic substance, extreme dosage, watering a waterlogged plant). | Rule-guardrail unit tests with mocked weather + LLM; recorded outputs | 5.6 | SW |
| FR-P03 | MCP: personal API key; tools list_plants, get_plant_status, get_history, get_tips | M | PASS if (a) all 4 tools respond per schema; (b) Claude, given a seeded account, names the plant with lowest moisture for "which plant needs water first?" (3/3 runs); (c) revoked key returns 401 within 1 min and tools stop working. | MCP contract tests; live Claude session; revoke test | 5.6, 5.9 | SW + Y (Claude session) |
| FR-P04 | Free/premium flag per user | M | PASS if toggling the flag in the DB gives/removes access to FR-P01–P03 within 1 min and RLS prevents users from setting their own flag. | API tests both states + RLS test | 5.6 | SW |
| FR-I01 | Optional HA bridge via MQTT discovery | C | PASS if the plant's sensors appear as entities in Arsany's HA instance with correct values (matching app within one report). If not delivered: **waived** (Could). | Check HA entity list | 5.6 | Y |
| FR-E01 | Thirst forecast on device, shown in app | M | PASS if on held-out public data MAE ≤ 12 h for horizons ≤ 72 h AND MAE < baseline (average watering interval) on the same set; and the app shows the forecast from the device report. | Python eval script on held-out split, metrics report; app display check | 5.8 | SW (+Y display) |
| FR-E02 | Event + sensor-fault detection on device | M | PASS if on held-out public data recall ≥ 95 % (watering/rain) and ≥ 90 % (faults); and ≤ 1 false alert per unit per week on our units (see open point re: duration). Precision reported alongside (no threshold given). | Eval script (confusion matrix); field log of alerts on 3 units | 5.8 | SW + Y (field) |
| FR-E03 | Immediate report on critical events | M | PASS if in ≥ 5 staged events (e.g. watering, probe pulled) phone alert arrives ≤ 15 min after the event, 5/5. | Staged events with timestamps vs push receipt time | 5.8 | Y |
| FR-E04 | Model fits budget | M | PASS if on the real ESP32-C3 board: model flash < 30 KB, RAM < 20 KB, inference < 50 ms (from edge-AI constraints text). | Size report from build; on-device timing + heap logs | 5.8 | Y+SW |

## Non-functional requirements

| Req ID | Requirement | Prio | Measurable pass/fail | Test method | Proving task | Bench? |
|---|---|---|---|---|---|---|
| NFR-01 | Battery ≥ 6 months/charge at hourly reporting | — | PASS if projected life = rated capacity ÷ measured average current over a full hour cycle (incl. 4 × 15-min wakes, 1 Wi-Fi report) ≥ 4380 h (6 months); capacity and derating assumption stated in report **[derating proposed]**. 12 months = stretch, informational. | Current profile with power analyzer / µA meter, arithmetic in report | 5.4 (design check 2.3) | Y |
| NFR-02 | Accuracy after calibration: moisture ±5 pts, temp ±0.5 °C, RH ±3 %RH | — | PASS if at ≥ 3 temp/RH points each reading is within limit vs reference, and soil moisture within ±5 points vs reference for each soil type used (see open point), n ≥ 5 per point on each of 3 units. | Bench comparison vs reference thermometer/hygrometer; soil dry/wet points | 5.3 | Y |
| NFR-03 | Setup ≤ 3 minutes | — | Same as FR-A03 timing: ≤ 180 s for the median first-time user, none > 240 s **[proposed]**. | Stopwatch | 5.5 | Y |
| NFR-04 | Data in app ≤ 2 min after upload | — | PASS if over ≥ 20 uploads, time from device HTTP 2xx to value visible in app ≤ 120 s for 100 % (or p95, to be decided). | Timestamp diff server vs app log | 5.6 | SW (+Y for phone) |
| NFR-05 | Splash-proof enclosure, indoor + balcony, UV-stable | — | PASS if after splash test (spec to be fixed, proposed IPX4-style: water spray 10 min from all sides) no water inside and device still reports; enclosure material datasheet states UV resistance (e.g. ASA/PETG-UV) and geometry checks wall ≥ 1.2 mm, USB-C and vent clearance OK. | Splash test + inspection; CAD geometry script on STEP | 5.7 (+4.E3 geometry) | Y+SW |
| NFR-06 | Security: TLS everywhere, per-device creds, user isolation, MCP revocation | — | PASS if (a) no plaintext HTTP/MQTT endpoint accepts connections; TLS ≥ 1.2 only; (b) each device has a unique token and a stolen token reads/writes only its own device; (c) RLS: user A gets 0 rows / 403 for user B's data on every table + storage; (d) revoked MCP key rejected; (e) no secrets in repo (secret scan clean). | Security checklist, RLS test suite, TLS scan, secret scan | 5.9 | SW |
| NFR-07 | Privacy: EU hosting, export and deletion | — | PASS if project region is EU (screenshot/config), export returns all user data (plants, readings, photos, profile) as machine-readable file, and delete leaves 0 rows (SQL) incl. storage and backups policy documented. | Config check + export/delete E2E | 5.9 | SW |
| NFR-08 | CE/RED-minded design | — | PASS if PCB review checklist is fully ticked: pre-certified module used, antenna keep-out honoured (DRC/visual), ESD protection on USB lines in schematic. | KiCad ERC/DRC + checklist | 4.P3 (gate G4a) — not a 5.x task | SW (+Y sign-off) |
| NFR-09 | Unit cost low; BOM at 1k pcs; ~10 EUR target reviewed | — | PASS if BOM tab has 3-pc and 1k-pc prices for every line, with sum and a written verdict versus the 10 EUR target. (No numeric cost limit exists, see open point.) | BOM tab completeness check | 2.5 (G2) — not a 5.x task | N |

## Cross-cutting evidence (not a requirement row)
- 5.1 turns this matrix into the test plan (due 2026-11-13); 5.10 and G5 need every row above passed or waived with a written reason.
- Code-level proof (unit/RLS/contract tests, model metrics, geometry scripts) runs in CI on the PR long before the bench tasks; bench tasks 5.2–5.5 and 5.7 are Arsany's, with procedures written by QA under `tests/procedures/`.

## Open points for G1

Ambiguous / not measurable:
1. **"Plausible" values (FR-D01)** — no ranges. Proposed ranges above; please confirm or give others.
2. **Low-battery threshold (FR-D06)** — no voltage or % given. Needed value, e.g. 3.4 V.
3. **Alert thresholds (FR-A07)** — "too dry", "too wet", "offline" undefined (moisture % per soil type? offline after how many missed reports, e.g. 3 h?). Also what counts as a "critical event" (FR-E03).
4. **FR-D02 wording** — "24 ± 1 reports per day over 3 days": per day or total? I read it per day.
5. **FR-D04 vs Plan 4.F3** — requirement says 24 h without Wi-Fi, Plan says buffer up to 7 days. Which is the target? (Test uses 24 h unless told otherwise.)
6. **FR-A03 / NFR-03 duplicate** — same ≤ 3 min; need user count, median vs worst case, what counts as a first-time user, and whether BLE scan time is included.
7. **FR-A02 "unlimited"** — can only be tested with 3 devices; confirm "no hard-coded cap, tested with 3" is acceptable.
8. **FR-E02 "≤ 1 false alert per week on our units"** — units are ready ~25 Nov, 5.8 runs 26 Nov, so a one-week observation cannot finish before G5; also with 3 units the evidence is thin. Propose a shorter soak (e.g. 72 h x 3 units, ≤ 1 total) or a waiver.
9. **FR-E02 precision** — only recall is specified; no precision/false-positive target on held-out data although Plan 5.8 mentions precision/recall.
10. **FR-E01** — "mean error" = MAE assumed; forecasts only valid when the dry threshold is reachable in 72 h; per-plant dry threshold source undefined.
11. **FR-E04** — the 30 KB / 20 KB / 50 ms numbers live in the constraints text, not in the table row.
12. **NFR-01** — no battery capacity or derating; "6 months" = 4380 h assumed.
13. **NFR-02** — which soil types, which reference method for soil moisture (gravimetric?), and the calibration procedure are unspecified. Sensor percent on a bench table is meaningless (see LESSONS), so the soil test must be in real soil.
14. **NFR-05** — no IP rating or test method ("splash-proof"), no UV test; proposed IPX4 spray + material datasheet. Needs your pick.
15. **NFR-09** — "as low as possible" has no numeric limit; the check can only be "BOM complete + verdict vs 10 EUR".
16. **FR-P02 "no unsafe advice"** — define unsafe (my guardrail suite list needs your approval); LLM output is non-deterministic, so tests use mocked LLM plus recorded real outputs.
17. **FR-P03** — "Claude answers correctly" requires a live Claude session run by you (cannot be automated reliably).

Missing requirements (suggest adding before freeze v1.0):
18. **OTA signing** — Plan 4.F4 says "signed images", requirement doesn't; FR-D05(c) is my proposal.
19. **Deep-sleep/average current figures** — only indirect via NFR-01; no separate sleep-current limit though 5.2 measures it.
20. **Calibration** — NFR-02 depends on dry/wet calibration but there is no FR for the calibration procedure (Plan 4.F5 only).
21. **Offline detection / data retention / export format** — not defined.
22. **Platform versions** — minimum iOS/Android version and tested devices not given.
23. **Test-ID mapping** — the doc's Test column points NFR-08 to 4.P3 and NFR-09 to 2.5 (not 5.x); fine, but they are then outside the 5.x bench runs and G5 evidence.
24. **Deliverables** (3 units, docs, source) have no acceptance criteria in the requirements; they sit in G6 / task 6.x.

Plan observations:
25. **G5 "after task 5.8"** in Quality Gates, but 5.9 (26 Nov) and 5.10 inspection (27 Nov) come later, and 5.9/5.10 are not listed in its entry. Suggest G5 follows 5.10.
26. **Late bench window** — 5.2–5.5 are planned 24–25 Nov, same days as unit assembly (6.1). Any defect found there leaves ~1 day. Consider early partial runs on dev kits.
27. Plan says 5.x Owner = Arsany; role file says QA writes procedures and runs software parts (5.1, 5.6, 5.8, 5.9). Matrix "Bench?" column reflects the role file.

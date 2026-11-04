# Requirements v0.1 -> v1.0: text changes derived in task 2.4

Author: Theo (System Architect) · 2026-11-04 · Status: **PROPOSAL for the Requirements owner (Arsany / Lead); the Google Doc is not edited by this file.** Self-authored; needs independent review.
Sources: Requirements v0.1 (Doc `1T4k3rK4KQDeGtIN8pjdmohGUAohFrtATLhMYSBsYA6g`), Arsany's G1 answers (PR #2 comments, "G1 answers"), PR #4 open items 7/8 (`edge-ai-concept.md`), Plan 4.F5, `architecture.md` section 10.1 (v0.2 items, not repeated here), `interfaces/`.
IDs: new IDs continue after the proposed v0.2 ones (FR-D08/D09, FR-H01..H03, NFR-10/11 in architecture.md 10.1).

## A. Changed requirements (old -> new)
| ID | v0.1 text / criterion | Proposed v1.0 text / criterion | Source |
|---|---|---|---|
| FR-D01 | "All five values plausible and present in every report" | Keep. Add: "Plausible = temperature -10..60 degC, humidity 0..100 %RH, light 0..100,000 lux, battery 3.0..4.25 V, relative moisture 0..100 %. A sample outside a range is stored but flagged and excluded from alerts and charts." | G1 point A-008.1; `db-schema.sql reading_is_plausible` |
| FR-D02 | Criterion: "24 +/- 1 reports per day over 3 days" | Criterion: "**24 +/- 1 reports on each of 3 days**" (per day, not the average). Each report carries the samples since the last report (4 per scheduled report). | G1 point 4 |
| FR-D04 | "Store readings when Wi-Fi is unavailable and upload them later" / "24 h without Wi-Fi -> no data lost after reconnect" | "Store **15-minute samples** while Wi-Fi is unavailable, **for at least 24 h (96 samples)**, and upload them later." Criterion: "after 24 h without Wi-Fi and reconnect, all 96 samples (unit of record: the 15-min sample) are in the cloud, none duplicated, none missing." The hub copy is best effort (v0.2). Plan 4.F3 says 7 days: **the requirement wins (24 h)**; 4.F3 text should be corrected or a longer buffer asked for as an explicit change. | Ines follow-up 1; `interfaces/README.md` decision 1; PR #3 note |
| FR-D05 | "Over-the-air firmware and model updates with rollback" / "Update succeeds; a broken image rolls back automatically" | Add to the requirement: "The image is verified by SHA-256 (published over TLS) before it is activated; a hash mismatch aborts the update." **Do not add** "unsigned image refused" (FR-D05(c) dropped). Signed images = follow-up, own ADR. Plan 4.F4 "Signed images" should read "SHA-256-verified images". | G1 point 18, A-009; ADR-009 |
| FR-D06 | "Low-battery warning below threshold" | "Low-battery warning when the battery voltage is **below 3.4 V**; cleared again at 3.5 V or above [hysteresis proposed]." | G1 thresholds; `devices.low_battery_mv` |
| FR-A02 | "unlimited number of devices" | Keep. Criterion: "No hard-coded cap; tested with 3 devices on one account." | G1 point 7 |
| FR-A07 | "Push alerts: too dry, too wet, low battery, device offline, edge-AI events" | Define the terms: **too dry** = relative moisture below the plant's dry threshold (default **25 %**); **too wet** = above the wet threshold (default **85 %**); **low battery** = below 3.4 V; **device offline** = **3 missed hourly reports** (no report for 3 h 10 min); **edge-AI events** = `wetting_unexpected`, `waterlogged`, `sensor_out_of_soil`, `sensor_fault` (critical set, `edge-ai-concept.md` 2.4). Each alert fires once until it clears. | G1 point 21, thresholds, A-008; PR #4 item 8 |
| FR-E03 | "Alert on the phone <= 15 min after the event" | "Alert on the phone **<= 15 min after the first 15-minute tick that observes the event**, for the fast-path classes only (unexpected wetting, sensor out of soil, sensor fault). Waterlogged and fast drying are debounced and are not covered by this limit." Measured from the observing tick to push receipt; includes connect and send. | PR #4 item 7 (Arsany "yes to both"); Ines follow-up 3 |
| FR-E04 | "Model fits the budget" / "Size, RAM and inference time measured on the real board" | Put the numbers in the requirement: flash **< 30 KB** (model flatbuffer), RAM **< 20 KB** (tensor arena + model-specific persistent buffers + feature history; interpreter/kernels code reported separately), inference **< 50 ms** (one `Invoke()` on the board). | G1 point 11; PR #4 counting rule |
| NFR-01 | "Battery life >= 6 months per charge at hourly reporting" / "Measured average current projects >= 6 months" | Criterion: "projected life >= 6 months using the **rated capacity of the chosen 1S LiPo derated by 20 %**; both capacities stated in the report." Includes the hub publish (v0.2). | G1 point 12 |
| NFR-02 | "Accuracy after calibration ..." | Criterion adds: "tested in real potting soil and one garden soil, gravimetric reference, **2-point dry/wet calibration per FR-D10**." | G1 point 13 |
| NFR-07 | "EU hosting, data export and deletion on request" | "... **export as JSON and as CSV**; deletion removes all rows and photos. **Raw readings are kept 12 months**, then deleted automatically." | G1 point 21; `GET /export`, `purge_old_readings()` |
| Sec. 7 constraints | App: Expo + TS, iOS + Android | Add: "**Minimum iOS 16 and Android 10**, tested on the owner's phones." | G1 point 22 |

## B. New requirements
| ID | Prio | Text | Acceptance criterion | Test | Source |
|---|---|---|---|---|---|
| **FR-D10** | M | **Calibration procedure.** The device calibrates soil moisture with a 2-point procedure: a **dry point** (probe in air / dry soil of the chosen soil type) and a **wet point** (probe in saturated soil of that type); the raw ADC values are stored on the device, used to compute relative moisture 0-100 %, and reported to the cloud (`cal.dry_raw`, `cal.wet_raw`). The procedure is started from the app or by a documented button sequence and is repeatable per soil type. | After calibration, relative moisture of the dry and wet references reads <= 5 points from 0 and 100 respectively; the points survive reboot and OTA; the cloud shows them. Accuracy is then judged by NFR-02. | 5.3 | G1 point 20; Plan 4.F5 ("dry/wet calibration per soil type"); NFR-02; edge-ai-concept 2.1 |
| **NFR-12** | M | **Deep-sleep current.** With Wi-Fi/BLE off, sensors powered down and RTC retained, the board draws at most **I_sleep_max = TBD** at 3.7 V. | Measured at the battery terminal on the assembled board; value <= I_sleep_max. | 5.2 / 4.P5 | G1 point 19 |
| **NFR-13** | M | **Data retention.** Raw 15-minute readings are retained 12 months and deleted automatically afterwards. | Rows older than 12 months are absent after the nightly job (test with back-dated rows). | 5.9 | G1 point 21 |

### NFR-12: how the TBD is derived (Emil's 2.3 budget is being drafted in parallel; not available to me, so the number stays TBD)
The limit comes from the NFR-01 budget; do not fill it in before 2.3 is final:
1. Usable capacity `C_use = C_rated x 0.8` (20 % derating, G1 point 12), in mAh, for the cell chosen in 2.3.
2. Target time `T = 6 months = 4380 h` (Ines's figure; 182.5 days x 24 h).
3. Allowed average current `I_avg_max = C_use / T`.
4. Energy per hour cycle from 2.3: 4 wakes for sampling (+ AI inference), 1 Wi-Fi report (cloud TLS POST + hub MQTT publish), with their durations and currents `Q_active` (mAh per hour).
5. `I_sleep_max = I_avg_max - Q_active / 1 h` (the hour-average current the sleep state may use), then rounded down with a margin set by Emil.
Illustration only, not a requirement and with an assumed cell: a 1000 mAh cell gives `C_use` 800 mAh and `I_avg_max` of about 183 uA average over the hour; the sleep limit is whatever remains after the active share, so it is necessarily below that. The ESP32-C3 datasheet-class deep-sleep figure (about 5 uA, Plan 2.2) is not a measurement of our board and is not used as a limit.
**Open:** TBD until Emil's 2.3 budget lands. Whoever receives 2.3 fills the number here and in the Requirements doc.

## C. Items I checked and do NOT propose to change
FR-A03/NFR-03 (timing rule = first-time users, median <= 180 s, none > 240 s, G1 point 6) and FR-E01/E02 test conditions (G1 points 8-10) are acceptance-matrix details owned by Ines (task 1.5), not requirement text. G1 point 15 (NFR-09) and points 16/17 (FR-P02/P03 test method) likewise. The v0.2 hub/BLE changes stay in `architecture.md` 10.1.

## D. Needs Arsany (answer in the PR thread)
1. **FR-D10 wording and ID, NFR-12 placeholder, NFR-13**: OK to add as above? Recommendation: accept; fill I_sleep_max when 2.3 is final.
2. **FR-D04 vs Plan 4.F3 (7 days)**: confirm 24 h (requirement) and correct 4.F3. Recommendation: 24 h.
3. **FR-D06 hysteresis 3.4 V / 3.5 V and FR-A07 clear rules (5 points, 3 h 10 min grace)**: my proposals, marked as such; accept or give other values.

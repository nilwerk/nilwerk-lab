# Claim-check: draft pack 23 Nov 2026 ("Before the sensor is wired up")

Internal file. File names and IDs are allowed here; they are not allowed in `posts.md` public text. Every claim in `posts.md` has an ID below. Checked 23 Nov 2026, Berlin time, against `origin/main` at 02e5c05.

| ID | Claim in the draft | Type | Source (file, line or section) | As of | Status |
|---|---|---|---|---|---|
| C1 | The app's main screens run in a browser with fake sensor values and a fake Bluetooth scan; five screens (welcome, sign-up error, profile, plant list, plant detail) | measured | `showcase/items/2026-11-20_sim-evidence/caption.md` (What it shows; Images 01–05) | 20 Nov run | Screen 04 viewed 23 Nov (plant list, MOCK banner). Screens 01–03 and 05 not yet viewed: **OPEN**, look at them before approval |
| C2 | The firmware starts in an ESP32-C3 simulator (QEMU, ESP-IDF 5.4, v1 build with simulator overlay) and prints five mock readings, numbered 0 to 4 | measured | `showcase/items/2026-11-20_sim-evidence/boot-log.txt`: lines `NWBENCH wake=1 i=0` to `i=4`; header lines (ESP-IDF v5.4, QEMU esp32c3) | build compile time 20 Nov 2026 18:10 | Checked 23 Nov in the log |
| C3 | Sensor values are fixed mocks; calibration constants are placeholders until set on the bench; QEMU has no USB serial; no live database | measured and caveat | `boot-log.txt`: line `NWSIMMOCK sensors=MOCK fixed values, NOT sensor data`; line `CALIBRATION IS A PLACEHOLDER UNTIL SET ON THE BENCH`; `caption.md` (Caveats, Unverified) | 20 Nov | Checked in the log; the no-USB and no-database points come from `caption.md` |
| C4 | Agent minutes about 6.5 (app) and about 18.5 (firmware, incl. toolchain install), wall clock | measured (as stated in item) | `caption.md` (Time) | 20 Nov | **OPEN**: check the Agent Log rows for this item before posting; the caption figure is the only source so far |
| C5 | Own human estimates about 4 h (app) and about 4 h (firmware) | estimated | `caption.md` (Time) | 20 Nov | Labelled "estimated" in the post. Not a measured figure |
| C6 | Nothing ran on a phone or a real board; no real sensor data; no real Bluetooth pairing | caveat | `caption.md` (Unverified); `boot-log.txt` header line "Nothing here was measured on hardware" | 20 Nov | Checked |
| C7 | The real sensor board has not been tested yet (used in the lead-in) | status | `caption.md` (Unverified: real sensors and soil probe); `team/reports/2026-11-21.md`, bench checks still open | 21 Nov report | **OPEN** as a status word: recheck the day of posting, since bench checks can move |
| C8 | Closing line "AI agents, led and reviewed by humans" | team fact | `showcase/workflow/team-workflow.md` (intro paragraph) | 23 Nov | Checked: the same wording is used in the team workflow |

## Open points before any approval

1. Look at screens 01–03 and 05 of the item and confirm each fake-data screen carries MOCK (C1). Screen 04 is confirmed.
2. Agent Log rows for the simulator item: confirm or correct the 6.5 and 18.5 minutes (C4).
3. Technical check by the architect role: the simulator claims (C2, C3).
4. Native German check of the DE text. The check must cover the layout as well as the words.
5. Image 06 (`fw-boot-log.png`) is not used. It shows build paths on screen (a crop of the reading lines would need a new review).
6. Confidentiality check: the post text names no people, no file names, no PR numbers, no task IDs.
7. Approval: the owner decides. Nothing is published. The Metricool planner is not used for this pack.

## Source notes

- The item caption says the simulator images use a stand-in backend and a web build, not a phone. Posts keep that wording.
- The 20 Nov item folders for the app, cloud and firmware work (other than the simulator item) are not in this pack. They have open review points, and the draft counts from their captions are not yet settled. They can go into a later pack after review.

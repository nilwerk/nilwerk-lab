# Plant Monitor — project-specific lessons

Facts and lessons that only apply to this project. Generic rules go to `team/learnings/<role>.md`.
Added by the Lead from each day's `Lesson:` notes; reviewed in the Friday retro.

- 2026-11-02 · ESP32-C3-MINI-1 replaces the earlier ESP8266 (Q-02) — old soil-sensor code and calibration values are reference only.

## Sprint 1 (Theo)
- NFR-12 lives in one place only; other docs link to it (it was proposed twice).
- A-025 vs NFR-13 conflict was flagged to the Lead, not edited silently; resolve via Arsany.
- Row-count check: expected rows = reporting interval x window (720 vs 2880 mistake, PR #18).
- Postgres tests run as superuser `postgres`; RLS checked with a normal role.

## Sprint 1 (Ines)
- Open thresholds in the acceptance matrix (plausible ranges etc.) are marked [proposed] until Arsany answers; grep "12 months"/"6 months" style numbers across docs after each decision.
- Postgres/RLS test results: read CI job logs for real counts; skipped jobs show green.

## Sprint 1 (Leo)
- T-13 interface differed from assumptions (param name, security mode, export param); the Architect's file is the source, cite file+line.
- Wireframe/doc tables must scroll horizontally at 390px (overflow-x:auto).

## Sprint 1 (Mira)
- Persistent device state to keep across deep sleep (EMA, debounce counters, last values) must be listed in the edge-AI spec; the model is int8 TFLite Micro, so the feature spec is integer too.
- Alert latency (NFR) depends on 15-min sampling plus hourly Wi-Fi report; N-of-M debounce adds (N-1) x 15 min on top.
- Licences of open datasets that the sandbox cannot reach stay "unverified" in the data card until CI or Arsany confirms.

## Sprint 1 (Emil)
- NFR-10 already existed in the architecture docs; new NFR IDs must be grepped first.
- Battery-life target is the single parameter `NFR01_MONTHS`; power-budget doc tables are generated from the script.
- Strapping pins on ESP32-C3-MINI-1 must match `firmware/main/board.h` and the PR pin table.
- Shop hosts (LCSC/JLCPCB) must be requested before the BOM can be called verified; until then stock/price are `unverified`.

## PR/social examples (moved from the playbook)
- Time numbers: "99 min of agent time on 3-5 Nov, without the lead" (measured, day totals 16.2 + 50.0 + 33.0) next to "about 145 working hours of a human without AI" (agents' own estimate) was easy to read as "X times faster"; the report of 5 Nov also shows 103.1 for sprint to date, a different sum.
- Canon drift: the origin canon said parts were ordered on Wed 4 Nov; the daily reports say Tue 3 Nov. Fixed in `showcase/stories/origin/README.md`.
- Counts grow: Saturday 7 Nov had 7 merges in the morning and 10 by 20:46.
- Outdated simulation: the 1 Nov simulation gave a battery life of 150-226 days; the later calculation gives about 4.5 months typical and 1.4 months worst case. Posts must not repeat the old figure.


## Sprint S3 retro (2026-11-20)
### firmware
- Sensor readings after power-on are noisy: give the capacitive probe ≥ 1.5 s warm-up, take several spaced samples and smooth with EMA (learning log 06).
- The default DevKit build with the setup flow on shows no sensor lines on USB serial; DevKit bench builds need the setup flow off (issue #68, corrected 18 Nov).
- The upload path compiles only with `CONFIG_PLANT_UPLOAD` (`sdkconfig.defaults.upload`), but the `upload` component is required in all builds (PR #128). Default and v1 CI steps must stay green.
- The 3 demo units keep per-unit BLE setup credentials in plaintext NVS; accepted for the demo only, pending A-110 (PR #132, procedure §7).
- RTC retained state proposal: NW cycle state 3140 B of a 4096 B cap (PR #140). The cap is a design proposal, not NFR-12; `idf.py size` and the RTC share used by Wi-Fi, ULP and bootloader are unverified.
- Hardware status at 17 Nov: the wired v1 board with the v1 build outputs sensor lines on USB serial only. No end-to-end data existed until a provisioned unit and a phone dev build (4.A3b) ran.
- 4.AI3 (edge model) uses online data only, per A-102. Calibration against bench data waits for the v1 bench checks (A-094).

### fullstack
- Photo export: 7-day signed URLs die on account delete, so export must download photos before delete unlocks (A-107 option b; 4.A9b #133).
- Photos with `url:null` count as missing and do not block delete, but an all-null set locks delete; the 150 MB export cap is unmeasured (A-111).
- Export function 4.B2c (#130) is merged but NOT deployed until A-108 is approved. Merge #137 (path guard) before deploying, or the guard is not on main.
- Photo upload path contract: `<uid>/<plant_id>/<uuid>.<ext>` (Theo schema comment, 4.A9b).
- Per-unit BLE setup codes: plaintext NVS risk accepted for the 3 demo units only (A-110, #132). Not acceptable for production units.
- DevKit default build has the setup flow on, so it shows no sensor lines until a unit is provisioned (issue #68).
- No end-to-end data yet: real sensor connection needs the 4.A3b dev build on a phone and 4.F2b unit provisioning on hardware (both not run as of 19 Nov).
- Tips tests: `cloud/test.sh` ran 31 of 68 tests in CI until the glob fix (#121); nightly mutation run (#138) is 127 mutants, 0 survived, owner to watch (A-112).
- Public posts carry no PR numbers, task IDs or real first names (Theo, #137/#140).

### cloud-ai
- The tips test runner in `projects/plant-monitor/cloud/test.sh` ran 31 of 68 tests in CI until the glob fix in #121. Verify the count after any change to the runner.
- Tips deny-list bypasses remain open. Close them before live mode (open item from #121).
- The export path guard (4.B2c, PR #137 on main after the #134 rescue) needs the DB CHECK on `storage_path`. Migration approval is still open. Apply the migration and deploy `export` only after A-108 is answered.
- Photos in an export are 7-day signed URLs. Decision A-107 (b): the app downloads photos before the delete unlocks. Photos with `url:null` count as missing; they do not block delete, but an all-null set locks delete (A-111, recommended: accept).
- The 150 MB export cap is unmeasured. Measure it before live use (A-111).
- The mutation suite (CI-M1, #138) runs 66 + 61 mutants in about 18 min. It is nightly and path-gated. Name a watcher (A-112) and add an issue-on-failure step.
- Sprint S3 claim check: 4.B2c, 4.A4c, 4.F3 slice 4 and CI-M1 were in review at the 19 Nov close, pending merge.

### pcb
- 2026-11-12 · PCBA order 12 Nov was not realistic (A-064): board not fully routed, panel, fiducials and U5/U6 footprints open. G4a/4.P4 moved 2–3 working days.
- 2026-11-14 · v1 is a function demo on perfboard with ESP32-C3 SuperMini and owned parts (decision in the 14 Nov report); the v1 wiring spec is PR #101.
- 2026-11-15 · QA note on #101: R_PROG 1200 → 1100. Re-derive the charge current from the TP4056 datasheet before the wiring is built.
- 2026-11-14 · CI does not run `projects/plant-monitor/v1/`. The wiring spec has no automated gate (question to Kai).
- 2026-11-17 · A-094 v1 bench checks: R3 reading across the TP4056 PROG resistor first; LiPo max charge current; soil AOUT in air (stop above about 2.4 V); parts you own. Blocks Emil and Yara. Still open 20 Nov.
- Enclosure heights (`enclosure/v1_demo_compact`) are ASSUMED until A-094 items 2 and 4 are measured. First print is a fit-check part only.
- Battery life: the 1 Nov simulation (150–226 days) is superseded by about 4.5 months typical and 1.4 months worst case. Posts must not repeat the old figure.
- Strapping pins on ESP32-C3-MINI-1 must match `firmware/main/board.h` and the PR pin table (Sprint 1, still valid).

### mechanical
- **Status correction for the 4.E5 brief:** A-093 is ANSWERED (Arsany's L × W × T of bare boards: perfboard 70 × 50 × 2, soil sensor 95 × 22 × 2, TP4056 28 × 17 × 2, BH1750 17 × 14 × 2, AHT20 15 × 10 × 2). The open owner item is **A-094** (due 17 Nov, overdue): part heights with parts fitted, under-board height, SuperMini length × width, LED window position. No caliper measurement of part heights exists yet.
- **PR #102 (4.E5 v1 base + lid) is merged on GitHub**, and the compact round 2 (PR #108) merged 16 Nov. The first print is still FIT-CHECK only until A-094 is answered.
- **Fit-check state (round 2, compact):** 7 PASS / 0 FAIL / 3 NOT MET / 51 OPEN (`fit_check_v1.py`). Everything depending on a part height, the SuperMini size, the cell datasheet or an RF distance is OPEN.
- **v1 demo is indoor only:** open light window and vents; not splash-proof, not IP-rated. Never charge unattended in the closed box (TP4056 and LiPo in 1.6 mm PETG). Keep the antenna keep-out (x 27–40 in the model, no metal, cell or wire).
- **Battery placement under the right half** is accepted for the demo (A-100 option a), a known deviation from WIRING §5 (left half).
- **Light sensor placement:** never mount the light sensor where it cannot see ambient light (an earlier concept put the unit under the pot). Source: learning log 02.
- **Soil sensor cable** exits through a slot in the bottom wall; the 95 × 22 mm sensor board sits outside the box (confirm with Arsany that this is intended).

### qa
- Soil sensor percentages are not trustworthy on the bench; test calibration in the soil it is for (learning log 06, Sprint 1).
- `cloud/test.sh` ran 31 of 68 tips tests in CI until the glob was fixed (S3 19 Nov, #121). Check the count after any runner change.
- Mutation evidence so far: tips slice 2 (#122) 622 checks, 49/49 mutants; cloud nightly mutation run (#138) 127 mutants, 0 survived (S3 18 Nov).
- Hardware runs are not run as of 19 Nov: 4.A3b real BLE (no phone or sensor run), 4.F2b per-unit provisioning, 4.F3 upload on hardware. QA passes there cover build and host tests only.
- Demo BLE setup codes are stored in plaintext NVS on the 3 demo units. This is an accepted risk (A-110) and must be revisited before any live unit.
- Export before delete: photos with `url:null` count as missing and do not block delete, but all-null blocks delete. The 150 MB export cap is unmeasured (A-111).
- Nightly cloud mutation run (#138) has no watcher until A-112 is answered.

### devops
- **Mutation counts differ by source.** The script headers say 62 (`cloud/test/mutation.sh`) and 67 (`cloud/tips/test/mutation.sh`). The 19 Nov run reported 66 and 61. Quote the count the CI log prints, never the comment or a PR body. (Source: `cloud-mutation.yml` header; `team/reports/2026-11-19.md`.)
- **Nightly cloud mutation:** 02:17 UTC on main, about 14–18 min. Run 44664245292 on 20 Nov: success, 14m02s. Not part of Final status. (Source: `cloud-mutation.yml`; `gh run list`.)
- **Final status** fails only if detect fails or a job fails or is cancelled. Skipped jobs pass, so jobs that should run need a gate that is tested. (Source: `ci.yml` summary step.)
- **Firmware CI** compiles the devkit configuration and the v1 configuration (since 17 Nov). It proves the code compiles, not that it runs on hardware. (Source: `team/reports/2026-11-17.md`.)
- **Stacked PRs:** code merged into another PR's branch after that PR reached main never reaches main (#117, #134). Ported as #137. Retarget stacked PRs to main after the parent merges. (Source: `team/reports/2026-11-19.md`.)
- **Tips tests:** `cloud/test.sh` ran 31 of 68 tips tests until the glob fix. Count again after any change to test layout. (Source: `team/reports/2026-11-17.md`.)

### pr-social
- **CI numbers are the source for the mutation claims.** The #138 nightly/PR cloud mutation job ran 66 care-tips mutants and 61 cloud mutants (127), 0 survived, in 18 minutes (run 7002274114). The PR body and docs said 67 + 62; use 66 + 61 until the docs are corrected. *Source:* 19 Nov report; `showcase/content/2026-11-19/claim-check.md` S1.
- **Brand canon mismatch.** The origin carousel (5 Nov) uses a different palette and fonts from the website (nilwerk.de). The brand kit proposes the website system; the origin pack is off-brand until Arsany approves the kit. *Source:* `showcase/brand/brand-kit.md` §1.
- **Rendering on this machine.** Headless Chrome (`google-chrome --headless=new --no-sandbox --screenshot`) renders HTML to PNG without Playwright. numpy is only in `/usr/bin/python3`. *Source:* 17 Nov (PR-2026-11-17).
- **Avatar clip path fix.** `diary/build_diary.py` `avatar()` breaks the `pr-social.svg` clip path (square corners); `company/build_company.py` has the fixed version. Use unique SVG ids per use. *Source:* company carousel render, 8 Nov.
- **No text-to-speech in the sandbox.** No espeak, pico, flite or pyttsx3; the rough cut is frames, synthesised music and burned-in captions. *Source:* environment check 17 Nov.
- **Sprint status at 19 Nov:** #117 is not on main (in the #114 branch only, shipped via #123); the 4.B2c path guard reached main via #137. *Source:* 19 Nov report.
- **Unpublished IDs in drafts.** `showcase/content/2026-11-18/posts.md` still has a PR number and a task ID in public text (found in the S3 spot check, read-only). Fix before any approval. *Source:* grep on the 18 Nov drafts.

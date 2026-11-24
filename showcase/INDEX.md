# Showcase library

Proof of what the Nilwerk team builds and how fast — captured during the work (TEAM.md §13), curated by Poppy.

- `workflow/` — how the team works (safe to publish)
- `items/<YYYY-MM-DD>_<task-id>/` — one folder per showcase item: images, optional short animation, `caption.md`
- `brand/` — **brand kit v0.1 (KEPT by Arsany's decision; palette, fonts and logo as in `brand-kit.md`)**: `brand-kit.md`, `USAGE.md` (use case x audience matrix), `glossary.md`, tokens `brand.css` + `brand-status.css`, logo mark, post templates (portrait, LinkedIn, square, story, carousel), contrast checkers, previews
  - `brand/slides/` 16:9 demo slide templates (SVG + PNG + Google Slides instructions) · `brand/web/` web component kit sample (light/dark, self-hosted fonts) · `brand/app/` React Native/Expo theme (`theme.ts`, `tokens.json`), app icon and splash, mapping to the wireframe palette
- `content/` — post drafts and the content calendar: `calendar.md` (superseded by `series.md`), `2026-11-07/` (two drafted posts with images and claim-check)
- `learning/pr-skills-plan.md` — PR and social skills: ranked free/paid resources, tools, Claude skills check, 30-day schedule
- `content/series.md` — **Nilwerk Logbook**: series format, episode types, daily routine and the 14-day calendar (replaces `content/calendar.md`); drafts for days 2-5 in `content/2026-11-10`, `-11`, `-12`, `-13`
- `content/DAILY.md` — Poppy's daily checklist (read, recount commands, posting-day checklist); `content/about-nilwerk.md` — profile boilerplate EN/DE (50 and 100 words, two layers, claim-checked); episodes: day 5 = PR #48 (`content/2026-11-13`), day 6 sprint-2 template `content/2026-11-14`, day 7 `content/2026-11-15`; **10 Nov: draft pack "A test that could not fail" (5-slide carousel EN/DE, LinkedIn EN/DE, claim-check) in `content/2026-11-10/catches/`**
- **`content/2026-11-17/` — "The crew has a life" (fun series, owner direction 17 Nov): 5 episodes from one real Tuesday, 10 images (`images/`), 25 s Reel rough cut with synthesised sound (`video/`), LinkedIn EN/DE + Instagram copy (`posts.md`), scripts and character voices (`episodes.md`, `video-script.md`), claim sources + fiction-vs-fact (`claim-check.md`); build scripts `build_pack.py`, `build_video.py`; voice guide: `brand/brand-kit.md` section 5c**
- `content/2026-11-18/` — small draft pack (`posts.md`, `claim-check.md`): two ideas from PRs #132 and #133, plain story first, "For engineers" second, EN LinkedIn + DE; **not for posting before PR #131 is merged and Arsany approves**
- `content/2026-11-19/` — small draft pack (`posts.md`, `claim-check.md`, `plan-notes.md`): "The fix that went to the wrong place", plain story first, "For engineers" second, EN + DE LinkedIn, Instagram text; **not for posting before the rescue PR (#137) is merged and Arsany approves**
- `content/2026-11-23/` — small draft pack from the 20 Nov simulator evidence (`posts.md`, `claim-check.md`): plain story first, "For engineers" second, EN LinkedIn + DE, one image; **not for posting until the owner approves and the German and technical checks are done**
- `content/2026-11-24/` — small draft pack "The reviewers caught what the builders missed" (`posts.md`): plain story first, "For engineers" second, EN + DE LinkedIn, Instagram carousel outline (5 slides, alt text), claim-sources table; **not for posting until the owner approves and the German and technical checks are done**
- `stories/origin/` — origin story canon and first carousel (pre-brand look, to be re-rendered if the brand is approved)

## Items
| Date | Task | What it shows | Agent min | PR |
|---|---|---|---|---|
| 2026-11-07 | 2.5 follow-up | Charger resistor R9 recomputed from the datasheet formula; soil oscillator across datasheet corners (`items/2026-11-07_2.5`) | see Agent Log | #30 |
| 2026-11-07 | 4.AI1 | Wetting labels from real irrigation data: 250 positives, 556 events ignored (`items/2026-11-07_4.AI1`) | see Agent Log | #13 |
| 2026-11-07 | 4.B1 | Backend scaffold: RLS on 14 tables, user A cannot read or write user B's rows (`items/2026-11-07_4.B1`) | see Agent Log | #29 |
| 2026-11-07 | Origin story v2 | The Nilwerk story so far, 10 slides EN/DE in the approved brand (`items/2026-11-07_story`) | see Agent Log | link added by Lead |
| 2026-11-07 | PR-2026-11-07 | Brand kit v0.1 for social, slides, web and app (both audiences), two post drafts, 14-day calendar (`items/2026-11-07_PR`) | see Agent Log | link added by Lead |
| 2026-11-08 | 4.P1 | PCB schematic (KiCad 9, generated); no image, ERC never run (`items/2026-11-08_4.P1`) | 6.3 | #41 (open, **pending merge**) |
| 2026-11-08 | 4.A2 | App account and profile screens, 5 screenshots, mock backend (`items/2026-11-08_4.A2`) | 7.4 | #42 (open, **pending merge**) |
| 2026-11-08 | 4.E3 | Enclosure battery-bay study, two cells compared, section render (`items/2026-11-08_4.E3`) | 13.2 | #44 (open, **pending merge**) |
| 2026-11-08 | 4.B2 | Device claim + ingest API, 13 tests, 17 of 17 mutants caught (`items/2026-11-08_4.B2`) | 14.0 | #45 (open, **pending merge**) |
| 2026-11-08 | 4.AI2 | First edge-AI training run, FR-E02 not met (`items/2026-11-08_4.AI2`) | 15.5 | #46 (open, **pending merge**) |
| 2026-11-08 | PR-2026-11-08 | Logbook day 5 draft pack: three review catches, two honest negatives (`content/2026-11-13`) | see Agent Log | link added by Lead |
| 2026-11-10 | 4.P2 slice 2 | PCB with real footprints: 16 vias moved out of pads (now 0), antenna keep-out check now in CI, a real short in a placeholder switch found; still not routed, not fab-ready (`items/2026-11-10_4.P2-s2`) | see Agent Log | #73 (merged) |
| 2026-11-10 | 4.E3 slice 2 | Enclosure v3 plan view and exploded render, inner space 93.3 x 52.7 x 7.6 mm (head b98bd69); QA found a fit check that could not fail (hard-coded overhang 6.0 vs 4.5 mm), fixed with a drift test (`items/2026-11-10_4.E3-s2`) | see Agent Log | #74 (open, draft, stacked) |
| 2026-11-10 | 4.F2 slice 2 | Setup glue core tested on a PC (348 checks); the Wi-Fi/Bluetooth part compiled in CI after two fixes, nothing ran on a board; start-up pin cannot carry a "hold at power-up" button (`items/2026-11-10_4.F2-s2`) | see Agent Log | #72 (merged, stacked on #66) |
| 2026-11-10 | 4.B2b | DELETE /account (GDPR erasure): tests and 41 of 41 mutants killed (QA full run on head 9984d24), local database only (`items/2026-11-10_4.B2b`) | see Agent Log | #75 (merged) |
| 2026-11-10 | 4.A3 on main | Device setup flow in the app re-based on main: typecheck clean, 135 tests; QA mutation testing found a trim bug, fixed (`items/2026-11-10_4.A3-main`) | see Agent Log | #71 (merged) |
| 2026-11-10 | PR-2026-11-10 | Draft pack "A test that could not fail" built from the five items above (`content/2026-11-10/catches`) | see Agent Log | link added by Lead |
| 2026-11-17 | 4.A2 delete gate | Delete-account screen wired to the API, locked until the data export ran; test output only (`items/2026-11-17_4.A2-delete-gate`) | see Agent Log | #117 (merged into the 4.A4 branch; reached main via #123) |
| 2026-11-17 | 4.A4 slice 2 | Photo gallery, hourly table, export-before-delete, mock backend, test output (`items/2026-11-17_4.A4`) | 7 + 6 review round | #114 (merged) |
| 2026-11-17 | 4.A9 | Real export client + file hand-off before delete unlocks; test output, no phone (`items/2026-11-17_4.A9-export-client`) | see Agent Log | #123 (merged) |
| 2026-11-17 | 4.B3 slices 1, 1b | Care-tips guardrails: test and mutation output (`items/2026-11-17_4.B3`, `..._4.B3-slice1b`) | see Agent Log | #118, #121 (merged) |
| 2026-11-17 | 4.F1 v1 bench | v1 board option host tests, 15 of 15; compiled in CI since #120, never flashed (`items/2026-11-17_4.F1-v1-bench`) | see Agent Log | #116 (merged) |
| 2026-11-17 | 4.F3 slice 2 | Upload logic host tests, 622 checks, 49 of 49 mutants (`items/2026-11-17_4.F3-slice2`) | see Agent Log | #122 (merged) |
| 2026-11-17 | CI v1 + tips | Second firmware build with v1 defaults, Deno checks for care tips (`items/2026-11-17_ci-v1-and-tips`) | see Agent Log | #120 (merged) |
| 2026-11-17 | PR-2026-11-17 | Content pack "The crew has a life": fictional crew life on top of five real events of 17 Nov (poison-batch guard that could never fire, PR in the wrong branch, prototype that sleeps, 8 of 23 filter tricks, honest ledger); 10 images + rough-cut video (`content/2026-11-17`, `items/2026-11-17_PR-2026-11-17`) | see Agent Log | link added by Lead |
| 2026-11-17 | 4.A10 try-it guide | Five real screenshots of the app's web mock from the hands-on guide; nothing run on a phone (`items/2026-11-17_4.A10-try-it`) | see Agent Log | #125 (merged) |
| 2026-11-17 | 4.F6 dev guide | Firmware dev guide for new joiners; 19 of 19 host tests and link check, no toolchain run (`items/2026-11-17_4.F6-dev-guide`) | see Agent Log | #124 (merged) |
| 2026-11-17 | 4.A3b slice 1 | Real Bluetooth setup service in the app: 261 tests, 41 new; not run on any phone or sensor (`items/2026-11-17_4.A3b-real-ble-slice1`) | see Agent Log | #126 (open, **not merged**) |
| 2026-11-17 | 4.F3 slice 3 | One-wake cycle host tests: 134 checks, 40 of 40 mutants; the Wi-Fi/upload code was never compiled or run (`items/2026-11-17_4.F3-slice3`) | see Agent Log | #128 (open, **not merged**) |
| 2026-11-17 | BLE contract | Setup contract names user name, step order and stored keys; docs only (`items/2026-11-17_ble-contract-srp-nvs`) | see Agent Log | #129 (open, **not merged**) |
| 2026-11-17 | 4.B2c export | Export function: all of a user's data, photos as 7-day links; tests only, nothing deployed (`items/2026-11-17_4.B2c-export`) | see Agent Log | #130 (open, **not merged**) |
| 2026-11-18 | 4.B2c path fix | Export signs photo links only for the user's own path shape; stacked on #130 (`items/2026-11-18_4.B2c-pathfix`) | about 32 | branch only, no PR yet (stacked on #130, **not merged**) |
| 2026-11-18 | 4.F2b | One setup code per sensor: provisioning tool + validator, 22 host tests, 29 mutants; nothing run on a board. Item folder: `items/2026-11-18_4.F2b` on branch `agent/firmware/4.F2b-provision` | 7.1 + fix round | #132 (open, **on PR #132, not merged**) |
| 2026-11-18 | 4.A9b | Photos saved inside the export before delete unlocks: 287 app tests, 11 mutations caught; not run on a phone. Item folder: `items/2026-11-18_4.A9b` on branch `agent/fullstack/4.A9b-photo-export` | 7.4 first push | #133 (open, **on PR #133, not merged**) |
| 2026-11-18 | PR-2026-11-18 | Small draft pack "Delete my account must first give me ALL my data" and "one setup code per sensor, never in the repo" (EN LinkedIn + DE, claim-check); not for posting before PR #131 is merged and Arsany approves (`content/2026-11-18`) | see Agent Log | link added by Lead |
| 2026-11-19 | 4.B2c rescue, 4.B3 | Export photo-path guard that was merged into the wrong branch is ported back to main; export tests 19/19, care-tips 68/68; Deno lint not run (`items/2026-11-19_4.B2c-4.B3-s2`) | about 6 | #137 (open, **not merged**) |
| 2026-11-19 | CI-M1 | The cloud mutation suite runs in CI only when cloud code changes; terminal replay of the gating scripts, Actions engine itself not run locally; the PR's own CI run: 127 mutants, 0 survived (`items/2026-11-19_CI-M1`) | see PR description | #138 (open, **not merged**) |
| 2026-11-19 | 4.A4c | App reads real plant data: type check and new tests against a faked network, not on a phone or a backend (`items/2026-11-19_4.A4c`) | about 8 | #139 (open, **not merged**) |
| 2026-11-19 | 4.F3 slice 4 | Firmware checks its saved sample buffer after every deep sleep; host tests only, no board, no ESP-IDF build (`items/2026-11-19_4.F3-slice4`) | see PR description | #140 (open, **not merged**) |
| 2026-11-19 | PR-2026-11-19 | Small draft pack "The fix that went to the wrong place" (EN LinkedIn + DE, Instagram text, claim-check, plan notes); not for posting before #137 is merged and Arsany approves (`content/2026-11-19`) | see Agent Log | link added by Lead |
| 2026-11-20 | App: remove-plant leftover test (fix round) | Screen-level test for a partial photo delete: 2 of 12 photos left, then 1, then none; the sensor stays claimed. Test output and two mutation checks; not run on a phone (`items/2026-11-20_4.A3b`) | about 1.3 (fix round) | see caption |
| 2026-11-20 | App: alerts list and alert rules (mock readings) | Alerts list at phone width on the mock build; rules run on fixed test readings; push notifications not built. Caption under review (`items/2026-11-20_4.A5`) | 6.4 | see caption |
| 2026-11-20 | Export: path guard segment tests | Export path guard refuses a percent sign and plain `..` segments and accepts a normal path; a mutation that lets `%` through is caught; local database only, nothing deployed (`items/2026-11-20_4.B2c`) | about 3 | see caption |
| 2026-11-20 | Cloud: premium analytics functions | 30/90-day aggregates, watering events, trend and plant comparison as pure functions; 11 tests pass; a changed comparison operator makes 4 tests fail. Thresholds are proposals, no endpoint built (`items/2026-11-20_4.B4`) | about 3 | see caption |
| 2026-11-20 | Firmware: OTA image check and rollback decision | Image hash check and rollback decision as pure C; host tests on a PC only, no device, no network. Caption counts under review (`items/2026-11-20_4.F4`) | about 5 | see caption |
| 2026-11-20 | Simulator evidence: app web flow and firmware boot | App screens in a browser with fake sensor values, each marked MOCK; firmware booting in a chip simulator and printing five mock readings; driver checks pass. Not a phone, not real sensors (`items/2026-11-20_sim-evidence`) | app about 6.5, firmware about 18.5 | see caption |
| 2026-11-24 | 4.A6 | Premium dashboard screen: soil range bars and first-week vs last-week bars, missing readings handled; no picture captured, nothing run on a phone or live backend (`items/2026-11-24_4.A6`) | see Agent Log | #191 (merged) |
| 2026-11-24 | 4.B4 slice 2 | Premium analytics endpoint: premium check before any reading; 13 checks against a local database with row-level security; test-output image; not run on a live backend (`items/2026-11-24_4.B4-s2`) | 7.5 | #192 (merged) |

The six 2026-11-20 items are on `origin/main` (checked 23 Nov 2026, Berlin time, at 02e5c05). Their captions are under review, so the rows above give no test counts for the alerts and firmware OTA items; recheck after the review closes.


The four 2026-11-19 items live on their PR branches (`origin/agent/cloud-ai/4.B3-s2`, `agent/devops/ci-mutation-full`, `agent/fullstack/4.A4c`, `agent/firmware/4.F3-s4`) and are listed by PR, not copied (status as of 19 Nov 2026, 08:10 Berlin: #132, #133, #137-#140 open; #126, #128, #129, #130 and #134 have merged since the 18 Nov note below; recheck after merges).

The 2026-11-17 items marked "not merged" and the two 2026-11-18 items live on their PR branches (`origin/agent/fullstack/4.A3b-real-ble-slice1`, `agent/firmware/4.F3-adapter`, `agent/architect/ble-contract-srp-nvs`, `agent/cloud-ai/4.B2c-export`, `agent/cloud-ai/4.B2c-pathfix`, `agent/firmware/4.F2b-provision`, `agent/fullstack/4.A9b-photo-export`) and are listed here by PR, not copied (status as of 18 Nov 2026, 08:20 Berlin: #126, #128, #129, #130, #132, #133 open; recheck after merges). 17 Nov items that were on branches at the time and have since merged (#124, #125) are marked merged above.
The 2026-11-08 item folders live on the PR branches until the PRs are merged (status as of 8 Nov 2026; recheck after merges).

The 2026-11-10 item folders live on the PR branches (`origin/agent/pcb/4.P2-s2`, `agent/mechanical/4.E3-s2`, `agent/firmware/4.F2-s2`, `agent/cloud-ai/4.B2b`, `agent/fullstack/4.A3-main`) until the PRs are merged; they are listed here by PR, not copied (status as of 10 Nov 2026, 10:45 Berlin: #71, #72, #73, #75 merged; #74 draft, open; recheck after merges).

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
- `stories/origin/` — origin story canon and first carousel (pre-brand look, to be re-rendered if the brand is approved)

## Items
| Date | Task | What it shows | Agent min | PR |
|---|---|---|---|---|
| 2026-11-07 | 2.5 follow-up | Charger resistor R9 recomputed from the datasheet formula; soil oscillator across datasheet corners (`items/2026-11-07_2.5`) | see Agent Log | #30 |
| 2026-11-07 | 4.AI1 | Wetting labels from real irrigation data: 250 positives, 556 events ignored (`items/2026-11-07_4.AI1`) | see Agent Log | #13 |
| 2026-11-07 | 4.AI2 slice 1 | First honest baselines on real Mendeley data: average-interval thirst baseline against a constant, no model trained (`items/2026-11-07_4.AI2`) | see Agent Log | #49 (merged 8 Nov) |
| 2026-11-07 | 4.B1 | Backend scaffold: RLS on 14 tables, user A cannot read or write user B's rows (`items/2026-11-07_4.B1`) | see Agent Log | #29 |
| 2026-11-07 | Origin story v2 | The Nilwerk story so far, 10 slides EN/DE in the approved brand (`items/2026-11-07_story`) | see Agent Log | link added by Lead |
| 2026-11-07 | PR-2026-11-07 | Brand kit v0.1 for social, slides, web and app (both audiences), two post drafts, 14-day calendar (`items/2026-11-07_PR`) | see Agent Log | link added by Lead |
| 2026-11-08 | 4.P1 | PCB schematic (KiCad 9, generated); no image, ERC never run (`items/2026-11-08_4.P1`) | 6.3 | #41 (merged 8 Nov) |
| 2026-11-08 | 4.A2 | App account and profile screens, 5 screenshots, mock backend (`items/2026-11-08_4.A2`) | 7.4 | #42 (merged 8 Nov) |
| 2026-11-08 | 4.E3 | Enclosure battery-bay study, two cells compared, section render (`items/2026-11-08_4.E3`) | 13.2 | #44 (merged 8 Nov) |
| 2026-11-08 | 4.B2 | Device claim + ingest API, 13 tests, 17 of 17 mutants caught (`items/2026-11-08_4.B2`) | 14.0 | #45 (merged 8 Nov) |
| 2026-11-08 | 4.AI2 | First edge-AI training run, FR-E02 not met (`items/2026-11-08_4.AI2`) | 15.5 | #46 (merged 8 Nov) |
| 2026-11-08 | 4.F1 | Sensor drivers, host-tested (41 deliberate mutations caught), nothing run on a board (`items/2026-11-08_4.F1`) | see Agent Log | #57 (merged 8 Nov) |
| 2026-11-08 | 4.B2 follow-up | Merge conflicts fixed, six QA gaps closed, 26 of 26 mutants caught, one bug found by comparing with a second implementation (`items/2026-11-08_4.B2-x`) | about 30 (own measurement) | follow-up to #45 (no own PR found) |
| 2026-11-08 | ADR-015 NFR-01 flexed | Battery life by scenario, estimates only (`items/2026-11-08_extra-nfr01-x`) | about 5 (own measurement) | #53 (merged 8 Nov) |
| 2026-11-08 | PR-2026-11-08 Metricool plan | Three company carousels (EN/DE), 14-day one-post-a-day calendar, Metricool plan, no Metricool draft yet (`items/2026-11-08_PR-metricool-x`) | about 9 (own measurement) | #62 (merged 8 Nov) |
| 2026-11-08 | PR-2026-11-08 | Logbook day 5 draft pack: three review catches, two honest negatives (`content/2026-11-13`) | see Agent Log | link added by Lead |
| 2026-11-10 | 4.P2 slice 2 | PCB with real footprints: 16 vias moved out of pads (now 0), antenna keep-out check now in CI, a real short in a placeholder switch found; still not routed, not fab-ready (`items/2026-11-10_4.P2-s2`) | see Agent Log | #73 (merged 10 Nov) |
| 2026-11-09 | 4.A4 slice 1 | Plant list with status chips and plant detail with a 7-day chart, real screenshots of the web build against the mock backend (`items/2026-11-09_4.A4`) | 6.8 (measured) | #65 (merged 9 Nov) |
| 2026-11-09 | 4.P2 slice 1 | First generated board file, 46 parts placed, not routed, not fab-ready (`items/2026-11-09_4.P2`) | see Agent Log | #64 (merged 10 Nov) |
| 2026-11-09 | 4.F2 | Setup logic state machine, 530 host checks, 45 mutants caught; nothing ran on a board (`items/2026-11-09_4.F2`) | see Agent Log | #66 (merged 10 Nov) |
| 2026-11-09 | 4.E3 JLC dry run | Board outline and footprints placed in the battery bay, board not routed (`items/2026-11-09_4.E3-jlc-prep`) | see Agent Log | #70 (merged 10 Nov) |
| 2026-11-10 | 4.E3 slice 2 | Enclosure v3 plan view and exploded render, inner space 93.3 x 52.7 x 7.6 mm; QA found a fit check that could not fail (hard-coded overhang 6.0 vs 4.5 mm), fixed with a drift test (`items/2026-11-10_4.E3-s2`) | see Agent Log | #74 (open, draft, stacked) |
| 2026-11-10 | 4.F2 slice 2 | Setup glue core tested on a PC (348 checks); the Wi-Fi/Bluetooth part compiled in CI after two fixes, nothing ran on a board; start-up pin cannot carry a "hold at power-up" button (`items/2026-11-10_4.F2-s2`) | see Agent Log | #72 (merged 10 Nov, stacked on #66) |
| 2026-11-10 | 4.B2b | DELETE /account (GDPR erasure): tests and 41 of 41 mutants killed, local database only (`items/2026-11-10_4.B2b`) | see Agent Log | #75 (merged 10 Nov) |
| 2026-11-10 | 4.A3 on main | Device setup flow in the app re-based on main: typecheck clean, 135 tests; QA mutation testing found a trim bug, fixed (`items/2026-11-10_4.A3-main`) | see Agent Log | #71 (merged 10 Nov) |
| 2026-11-10 | PR-2026-11-10 | Draft pack "A test that could not fail" built from the five items above (`content/2026-11-10/catches`); fact-check fixes in #79 still open | see Agent Log | #76 (merged 10 Nov) |

The 2026-11-08 item folders were on the PR branches until those PRs merged on 8 Nov 2026; all item folders are on `main` now (checked 11 Nov 2026 07:50 Berlin).

Not indexed yet: a few item folders that carry decision IDs or procurement details; they wait for Theo's check against TEAM.md §5 before they are listed.

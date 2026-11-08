# Showcase library

Proof of what the Nilwerk team builds and how fast — captured during the work (TEAM.md §13), curated by Poppy.

- `workflow/` — how the team works (safe to publish)
- `items/<YYYY-MM-DD>_<task-id>/` — one folder per showcase item: images, optional short animation, `caption.md`
- `brand/` — **brand kit v0.1 (KEPT by Arsany's decision; palette, fonts and logo as in `brand-kit.md`)**: `brand-kit.md`, `USAGE.md` (use case x audience matrix), `glossary.md`, tokens `brand.css` + `brand-status.css`, logo mark, post templates (portrait, LinkedIn, square, story, carousel), contrast checkers, previews
  - `brand/slides/` 16:9 demo slide templates (SVG + PNG + Google Slides instructions) · `brand/web/` web component kit sample (light/dark, self-hosted fonts) · `brand/app/` React Native/Expo theme (`theme.ts`, `tokens.json`), app icon and splash, mapping to the wireframe palette
- `content/` — post drafts and the content calendar: `calendar.md` (superseded by `series.md`), `2026-11-07/` (two drafted posts with images and claim-check)
- `learning/pr-skills-plan.md` — PR and social skills: ranked free/paid resources, tools, Claude skills check, 30-day schedule
- `content/series.md` — **Nilwerk Logbook**: series format, episode types, daily routine and the 14-day calendar (replaces `content/calendar.md`); drafts for days 2-5 in `content/2026-11-10`, `-11`, `-12`, `-13`
- `content/DAILY.md` — Poppy's daily checklist (read, recount commands, posting-day checklist); `content/about-nilwerk.md` — profile boilerplate EN/DE (50 and 100 words, two layers, claim-checked); episodes: day 5 = PR #48 (`content/2026-11-13`), day 6 sprint-2 template `content/2026-11-14`, day 7 `content/2026-11-15`
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

The 2026-11-08 item folders live on the PR branches until the PRs are merged (status as of 8 Nov 2026; recheck after merges).

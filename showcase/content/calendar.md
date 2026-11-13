# SUPERSEDED by `series.md` (Nilwerk Logbook) and, for Instagram, `company/calendar.md` (latest re-score 10 Nov 2026). Kept for its daily routine and rules.

# Content calendar: Mon 9 Nov to Fri 20 Nov 2026 (next 14 days, earlier version)

Author: Poppy · drafted 2026-11-07 · **plan only: nothing is scheduled or published; Arsany approves each post and publishes himself.** One post per weekday, LinkedIn plus Instagram unless noted. Weekends (14-15 Nov, 21 Nov): no post, optional Story from Arsany's phone if real hardware footage exists.

Plan: S2 Mon 9 to Fri 13 Nov, S3 Mon 16 to Fri 20 Nov. How to read it: every slot depends on a real milestone. If the evidence is not there by the evening before, the slot switches to a **reserve post** (bottom) and the milestone post moves, never a post without proof. Milestone dates below are the planned dates from the Plan as Nora gave them; they can slip. No prices, offers, customer or lead content; hardware photos and videos only with the integrator's OK. The PCB order (4.P4, planned 12 Nov) is Arsany's action and gets no post.

**Audience column:** A = non-technical layer leads (plain story, benefit first, glossary terms), B = technical layer leads (numbers, formula, source first), both = equal. Every post carries both layers (`brand-kit.md` section 5b); audiences alternate across the week, so neither waits long. Brand: all images from `showcase/brand/templates` (proposal, pending approval). Formats: **C** carousel, **N** sprint-in-numbers card, **B** behind the scenes, **M** myth vs proof, **P** proof tile (single image like today's).

| Day | Audience (leads) | Format | Topic and hook | Real milestone | Evidence needed (and where) | Status |
|---|---|---|---|---|---|---|
| Mon 9 Nov | A (plain story first) | P | "A review caught a charger resistor before any order" | 2.5 BOM follow-up, merged | Done: `content/2026-11-07/` post 1 (Theo to confirm the datasheet formula, claim-check note A) | drafted |
| Tue 10 Nov | B (proof first) | P | "User A cannot read user B's plant data" | 4.B1 backend scaffold, merged | Done: post 2, test output in `showcase/items/2026-11-07_4.B1` | drafted |
| Wed 11 Nov | both | M | What the power budget says: requirement (since 8 Nov: best and typical >= 3 months, worst > 1 month), calculated typical 4.5 months, worst-case stack 1.4 months (a stress bound), bench test pending | Power budget with datasheet currents (2.5/2.9) | `projects/plant-monitor/hardware/power-budget/power-budget.md` (figures are modelled; label "simulated"); chart from `power_budget.py`; Theo checks wording | needs draft |
| Thu 12 Nov | A | B | "A day at Nilwerk: plan, build, review, test, green, human merge" (carousel of the workflow diagram, 5 slides) | none (evergreen) | `showcase/workflow/team-workflow.md`; refresh it against TEAM.md (7-day week, extra rounds) first | needs draft |
| Fri 13 Nov | B (numbers) | N | "Sprint 2 in numbers": PRs merged, tests passing, agent minutes, human-hour estimate (labelled estimate) | S2 review (Nora, Fri 13 Nov) | Agent Log sums and Nora's `team/reports/2026-11-13.md`; numbers only from those, estimate always labelled | blocked until Nora's review |
| Mon 16 Nov | A (what users see) | C | "From QR code to live reading": the BLE setup flow in the app, 6 screens | 4.A2 app setup flow (planned 10-11 Nov; post when merged); 4.F1 BLE only if merged | Real app screenshots (Expo) and the PR; no mock-up; setup time claim (3 min, NFR-03) only if measured | depends on 4.A2 |
| Tue 17 Nov | B | P | "The first reading travels device to database" (backend ingest) | 4.B2 ingest endpoint (planned 10-12 Nov) | Test output of the ingest run (like 4.B1's test-output.txt); say "simulated device" unless the real board sent it | depends on 4.B2 |
| Wed 18 Nov | B | C | "Our schematic, checked by a machine": PCB schematic with ERC 0 errors, soil front end and charger | 4.P1 PCB schematic (planned about 9 Nov) | KiCad render of the schematic, `kicad-cli` ERC report from the PR (say "ERC 0 errors" only if the PR shows it); parts "in stock" only with date | depends on 4.P1 |
| Thu 19 Nov | A (before/after picture) | P (before/after) | "Enclosure v3: it fits the board" v2 against v3 render, bay 51 x 34.5 x 6.3 mm | 4.E3 enclosure (planned 10-11 Nov) | CadQuery renders v2 and v3 (before/after), dimension check output; "printed" only with a photo from the integrator and his OK | depends on 4.E3 |
| Fri 20 Nov | both | N | "Sprint 3 in numbers" plus "what the humans did" (approvals, hardware test only if reported) | S3 review (Nora, Fri 20 Nov) | Agent Log sums, Nora's report; hardware result only if the integrator reports a bench test (credit as "our hardware integrator") | blocked until review |

## Reserve posts (always ready, evidence already in the repo)

1. **Data honesty (P):** "Which wetting events do we trust enough to train on?" 250 labelled wetting positives (184 watering, 66 rain), 556 events ignored, sector 5 fully ignored. Source: `showcase/items/2026-11-07_4.AI1`, PR #13. Needs Mira/Theo to confirm wording and that the dataset (CC BY 4.0) is credited; no model has been trained, so say "labels", not "accuracy". No percentage of unexplained events is quoted (not traceable to a source).
2. **Origin story carousel** re-rendered in the new brand (C): `showcase/stories/origin/README.md` is the only canon; after brand approval.
3. **Soil sensor sizing (M):** "Will the soil probe oscillator work?" The sized front end across datasheet corners; image `showcase/items/2026-11-07_2.5/soil-oscillator-corners.svg`; the probe capacitance is an assumption, say so.
4. **Meet the team (B):** one persona per post (avatars), with what each checks; no human names beyond the founder.

## Rules for every slot

- Evidence first: the claim-check table is written before the text (template: `content/2026-11-07/claim-check.md`); Theo checks technical statements, Theo or Nora the German text, then Arsany approves.
- German LinkedIn text for every post; Instagram English plus one German line.
- Human-hour equivalents only as "about N h (estimated)"; battery and range figures "simulated" until a bench test exists.
- Drafts go to the Content Plan sheet and Metricool as drafts when available; until then these files are the drafts.
- Weekly pack (Friday) = the Friday N card plus the next week's two best proofs.

## Daily routine (Poppy runs every day, owner decision 2026-11-06)

**Inputs, read each morning:** the Agent Log (yesterday's rows, measured minutes), `team/reports/<yesterday>.md`, PRs merged since yesterday, new `showcase/items/*`, and this calendar.
**Steps:** pick the calendar slot for today (or the reserve if evidence is missing), write the claim-check first, then the LinkedIn EN/DE and Instagram text, render the images from the templates, view at least one PNG, commit.
**Output:** one draft pack in `showcase/content/<YYYY-MM-DD>/` (`posts.md`, `claim-check.md`, `images/`, `build_images.py`), the calendar updated, and a short result to the Lead with the Needs-Arsany rows (Post approval). Drafts only; Theo checks technical claims, Theo or Nora the German, Arsany approves and publishes.

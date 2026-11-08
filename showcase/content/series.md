# Series: "Nilwerk Logbook" (how we are growing the business, one episode a day)

Decision of the owner (2026-11-07): the first post is the Nilwerk story so far (`showcase/stories/origin/`), then daily episodes about how we are growing the company. Technical detail only in the short, marked "For engineers" layer. Drafts only; Arsany approves and publishes. This file and the calendar below **replace** the 14-day calendar of 2026-11-07 (`calendar.md` now points here).

## Format

- Name: **Nilwerk Logbook**, numbered **Day N** (Day 1 = Mon 9 Nov 2026, the origin story). Kicker on every image: `LOGBOOK · DAY N · <EPISODE TYPE>`.
- One post a day, LinkedIn (EN + DE) and Instagram (EN + one German line), 1080x1350 plus the 1200x627 LinkedIn image, from the approved v0.1 templates. Weekends: a short Instagram Story only if there is real news; otherwise no post.
- Two layers: plain story first (2-3 short paragraphs, benefit first), then "For engineers:" (3 lines at most: numbers, how it was checked, what is unmeasured). A status chip on every image (counted, measured, simulated, estimated).
- Honest about the humans: AI agents, led and reviewed by humans. Hardware tester: "our hardware integrator", never a name. No prices, offers, customers, leads, open questions, A-IDs, private URLs.
- Effort numbers: agent minutes are **measured** (daily reports), human-equivalent hours are always **estimated** ("the agents' own estimate"), never "X times faster".

## Episode types (rotate; one evidence source each)

| Type | In plain language | Evidence pulled every day |
|---|---|---|
| **Built today** | What we built today in one sentence, with the one picture that proves it | merged PRs of the day (repo history), new `showcase/items/*` |
| **Number of the day** | One number, its meaning, measured or estimated, with the source | Agent Log / `team/reports/<day>.md` time table; Plan status counts |
| **We decided** | A decision we made and why, in two sentences | decision records (`projects/plant-monitor/docs/adr`, decisions), answered questions in the daily report |
| **We caught a mistake** | A wrong value or wrong assumption found by review before it cost anything | architect and QA verdicts in the report; fix-round commits |
| **Behind the scenes** | A moment of how the team works (Saturday, the review gate, the work order) | `team/TEAM.md`, workflow doc, report stand-up |
| **What we learned** (Fridays) | One lesson from the week | "Lessons captured" in the reports; retro PR |

## Daily 10-minute routine for Poppy

1. (2 min) Read yesterday's `team/reports/<date>.md` and the Agent Log rows; list merged PRs of the day (`git log --merges --since=yesterday`).
2. (2 min) Pick the episode type from the calendar; if its evidence is missing take the reserve.
3. (3 min) Write the claim-check rows first (every number: source and type), then the plain story and the engineers' paragraph, EN then DE.
4. (2 min) Fill the template (`content/build_episodes.py` pattern), render, **look at the PNG**.
5. (1 min) Commit to `showcase/content/<date>/`, update this calendar, list the Needs-Arsany row (Post approval). Theo checks technical rows, Theo or Nora the German.

## Calendar: next 14 days (replaces the earlier calendar)

| Day | Date | Episode | Audience leads | Evidence | Status |
|---|---|---|---|---|---|
| 1 | Mon 9 Nov | The Nilwerk story so far (origin carousel, 10 slides) | A | `showcase/stories/origin/claim-check.md` | drafted |
| 2 | Tue 10 Nov | Number of the day: Sprint 1, 3 done, 9 waiting for review | A | report 6 Nov | drafted (`content/2026-11-10`) |
| 3 | Wed 11 Nov | Behind the scenes: a Saturday at Nilwerk, 10 merges as of 20:46 on 7 Nov (recount on posting day) | A | repo history 7 Nov, TEAM.md §7 | drafted (`content/2026-11-11`) |
| 4 | Thu 12 Nov | We decided: your plant's data lives in the EU | both | ADR-003, stack and costs | drafted (`content/2026-11-12`) |
| 5 | Fri 13 Nov | We caught a mistake: the charger resistor | both | claim-check of post 1, retro | drafted (`content/2026-11-13`) |
| 6 | Sat 14 Nov | Sprint 2 in numbers: template, filled on the day from the Agent Log | both | Plan, Agent Log | template (`content/2026-11-14`) |
| 7 | Sun 15 Nov | Behind the scenes: how a change moves through the team (13 merges on Sat 7 Nov, counted 8 Nov 15:07) | both | TEAM.md, git log | drafted (`content/2026-11-15`) |
| 8 | Mon 16 Nov | Built today: the first sprint-2 result (pick from merged PRs of 9-13 Nov: schematic, ingest, app setup) | A | merged PRs, showcase items | needs evidence |
| 9 | Tue 17 Nov | Side-episode for engineers: "User A cannot read user B's data" (`content/2026-11-07` post 2) | B | claim-check post 2 | text exists |
| 10 | Wed 18 Nov | Number of the day: what the power budget says (requirement 3 months, calculated typical 4.5 months, simulated) | both | `power-budget.md` | needs draft |
| 11 | Thu 19 Nov | Built today: enclosure v3 before/after, only if merged | A | CadQuery renders | depends on 4.E3 |
| 12 | Fri 20 Nov | Sprint 2 in numbers (measured minutes next to estimated hours) + what we learned | both | report 13 Nov, Agent Log | needs Friday data |
| 13-14 | Sat 21, Sun 22 Nov | no post | | | |
| (reserve) | any | data honesty (labels from real irrigation data, 250 positives, 556 ignored, "labels not accuracy"); meet the team (one agent per post); soil sensor sizing | | showcase items | ready |

The PCB order (Arsany's action) gets no post until something real is built from it. Milestone dates are the Plan's; if evidence is missing on the day, switch to the reserve, never post without proof.

## Rules that stay from the earlier calendar

German LinkedIn text for every post (checked by Theo or Nora, then Arsany); battery and range figures "simulated" until a bench test; every number in `claim-check.md`; Instagram AI flag only for AI-generated images (none planned).

# Claim check: Day 1, the Nilwerk story so far

Types: **M** measured, **S** simulated, **E** estimated, **D** fact of record, **C** counted from records. Sources are repo paths, daily reports and the repo history (private repo, no URLs). Checked by Poppy 2026-11-07; **Theo to check the technical rows (T)**, Theo or Nora the German text.

| # | Statement (slide / post) | Type | Source | Status |
|---|---|---|---|---|
| 1 | Sun 1 Nov, one prompt to Claude: "Can you design a simple 3D model and a PCB?" | D | `showcase/stories/origin/README.md` (canon, told by Arsany 2026-11-05) | ok |
| 2 | Result: plant stake v1, printable two-part enclosure and a PCB plan, generated in code | D | README canon; v1 design README (Drive, 1 Nov) | ok (renders are in `assets/`) |
| 3 | v1: 2×AAA, PCB blade probe, head 34 x 84 x 19.8 mm | D | `posts.md` of 2026-11-05 claim table: Drive `v1/README.md` | ok (T) |
| 4 | Same day: requirements + request to review its own design; v2 rechargeable (400 mAh LiPo, USB-C), replaceable capacitive probe, AHT20 + BH1750 (temperature, humidity, light) | D | README canon (v2 line); 2026-11-05 claim table: Drive `v2/README.md` | ok (T) |
| 5 | ~~Battery 150-226 days, simulated~~ **removed everywhere** (posts, slides, story_content.py). v2 is the 1 Nov first draft; its battery life is "not measured". The later calculation (4.5 months typical, 1.4 months worst case, bench test pending) is named only in the engineers' layer | C | `projects/plant-monitor/hardware/power-budget/power-budget.md` (verdict lines: typical 4.5 months, worst stack 1.4 months, stress bound); the old simulation figure is not repeated because a newer calculation exists | ok (T) |
| 6 | Mon 2 Nov: ten AI agents with job titles, personalities, skills (lead, architect, QA, DevOps, firmware, full-stack, cloud AI, PCB, 3D, sales) | D | README canon (Mon 2 Nov); `team/PERSONAS.md` (ten agents plus Poppy, who joined on 5 Nov) | ok |
| 7 | A code change is **meant to** go through architect review, QA test and pipeline, and our founder decides on the merge (the rule); **in practice most did**, consistent with Logbook day 3; reports and docs go through the same human merge (no per-PR verdict claimed) | D | `team/TEAM.md` sections 3-5; `showcase/workflow/team-workflow.md` | ok |
| 8 | Tue 3 Nov (first working day): lead plans at 07:30; four proposals (architecture, acceptance tests, edge-AI concept, parts list), each a pull request | C | `team/reports/2026-11-03.md` (PRs #1-#4: 4.H0 dev-kit list, 1.5 matrix, 2.1 architecture, 2.7 edge-AI concept) | ok |
| 9 | Each was reviewed (Theo), tested (Ines), pipeline checked (Kai); two got a second independent reviewer the next day (Theo's wording) | D | report 3 Nov "In review (all: Architect ✔ with notes, QA pass w/ notes, CI green)" | ok |
| 10 | About one hour of Arsany's time for the questions | E (his statement) | README canon: "about 1 h of his time (his statement)" | ok, labelled "his own statement" |
| 11 | "That week": the first dev kits ordered by Arsany after checking the list himself (no date on the slides) | D | report 3 Nov (A-002 check-before-click list) and report 4 Nov ("Arsany ordered 11-03") | ok. **Correction to the canon:** the canon says "Wed 4 Nov parts ordered"; the reports say ordered on 3 Nov. The slide therefore says "that week" and does not name the date |
| 12 | That week: a human joined as junior hardware integrator, working from abroad (one convention everywhere: "a human integrator" / "ein Mensch als Hardware-Integrator"; no name, no country), from work orders | D | README canon (Wed 4 Nov); `team/TEAM.md` section 12 (work-order template) | ok; no name per owner decision |
| 13 | Thu 5 Nov: first app wireframes, free users see 7 days (168 hourly means) | D | README canon (Thu 5 Nov); `projects/plant-monitor/app/wireframes/03-plants.png` text | ok |
| 14 | Fri 6 Nov evening: of 20 committed, 7 done (3 by the agents + 4 by Arsany), 7 in review, 1 in progress, 5 not started; the Plan showed 9 in review in total (2 pulled-in tasks included) | C | `team/reports/2026-11-06.md` "Sprint S1 burn-down: Committed 20; Done by Plan 3 ...; in review 9" | ok, as of 6 Nov |
| 15 | The team now works seven days a week | D | `team/TEAM.md` section 7 (owner decision 2026-11-06) | ok |
| 16 | Sat 7 Nov: **ten** pull requests merged, **as of 20:46** (#13, #24, #27, #29, #30, #34, #33, #35, #36, #38), a person merges every one | C | repo history `git log --merges` dated 2026-11-07 | ok with the "as of" label on slide 8; **recount on the day of posting** |
| 17 | Our reviewing AI agent caught a wrong resistor value before anything was ordered | D | report 6 Nov (Theo reviews, "R9 charger resistor error"); `projects/plant-monitor/hardware/bom/bom-draft.md` ("Nothing was ordered"). Details in `showcase/content/2026-11-07/claim-check.md` | ok (T) |
| 18 | 15 pull requests in the first three days, 8 of them merged by 5 Nov | C | README canon numbers (GitHub PRs #1-#5, #12-#21) | ok, "by 5 Nov" |
| 19 | 99 min of agent time on 3-5 Nov **without the lead's own time**: 16.2 + 50.0 + 33.0 = 99.2 | M | reports 3, 4, 5 Nov time tables (day totals). "Measured" = the Lead times each agent run (TEAM.md §10). **Note:** the report of 5 Nov gives "sprint to date 103.1 agent min" (a different sum, 3.9 min more); we use the three day totals and say "99" | ok |
| 20 | About 145 working hours of a human without AI, the agents' own estimate (37 + 61.5 + 46 = 144.5) | E | same tables, column "agent's own estimate" | ok, labelled **estimated**, not a promise; not "X times faster" |
| 21 | Agents do not buy, pay, publish or merge; Arsany approves and merges every change | D | `team/TEAM.md` section 5 hard rules, section 4 | ok |
| 22 | On 5 Nov the team got a storyteller (Poppy) | D | README canon (Thu 5 Nov: "Poppy hired the same evening") | ok |
| 23 | "Our founder, Arsany" named; no other person named; hardware integrator unnamed | D | owner decision 2026-11-05 (`team/learnings/pr-social.md` rule on names) | ok |
| 24 | "in its first week" (1-7 Nov) | D | dates above | ok |
| 25 | Nilwerk Logbook, one episode a day | plan | `showcase/content/series.md` | proposal until Arsany approves |

Not used: prices, offers, customers, leads, open questions, A-IDs, private URLs, PR numbers on the images.
Estimated vs measured: slide 3 simulated; slide 9 measured (99 min) next to estimated (~145 h); slide 5 "about one hour" is Arsany's own statement.

# Claim check: Agent Diary week 1

As of **Sun 8 Nov 2026, 16:10 Berlin**. Types: M measured (agent-run, QA re-ran where stated), C calculated, E estimated, D decision, F fact of record. "PR" ids stay here and never appear on the images. Comment ids are GitHub issue-comment ids. Recount everything on the day of posting. Theo checks technical rows; Theo or Nora the German.

| # | Day | Claim (as written) | Type | Source | Note |
|---|---|---|---|---|---|
| 1 | Mon | Account screens exist: welcome, sign-up/in, profile, premium sheet, delete account | F | PR #42 body; `showcase/items/2026-11-08_4.A2` | web export screenshots are real |
| 2 | Mon | 54 automated checks pass (jest 5 suites) | M | PR #42; QA 6718478019 | QA re-ran |
| 3 | Mon | 7.4 minutes of agent time | M | `showcase/items/2026-11-08_4.A2/caption.md` | measured wall clock of the build run; excludes review and fixes; no speed claim made |
| 4 | Mon | Merged 8 Nov, stand-in backend, not a phone | F | `git log` merge 3328707 (15:10); PR #42 "Not verified" | |
| 5 | Mon | "Three minutes for a newcomer? Not measured yet." | persona voice | NFR-03 (setup <= 3 min); no measurement exists | Leo's own persona line; not a quote |
| 6 | Tue | Model finds 27 % val / 40 % test; goal 95 % | M | PR #46 body; QA 6718564565 | shipped int8 model; float model 27 / 35 |
| 7 | Tue | 8 of 20 events, 95 % CI 22-61 %, 0.52 false alerts per unit-week | M | PR #46 body, `ml/reports/model-b-wetting-v0.md` | verified in `ml/reports/model-b-wetting-v0.md` on branch 4.AI2: test 8/20, 40.0 % (21.9 to 61.3 %), 0.52 FA/unit-week |
| 8 | Tue | 134 tests pass | M | PR #46 body; QA | |
| 9 | Tue | "The report now shows the whole curve of the simple rule" | F | PR #46 body (sweep in the report) | do not write "beats the rule": the PR says it is not claimed |
| 10 | Tue | PR open; decision continue-or-fallback is the founder's | F | PR #46 open at 15:08; the founder decision is recorded in PR comment 6718547128 | decision is the founder's, 8 Nov |
| 11 | Wed | Sensor drawn with 4 pins vs 6 on the datasheet; all four wrong | F | Architect review PR #41, comment 6718450327 (U5 AHT20 row) | the review compared with a datasheet it could read |
| 12 | Wed | "before any board existed" | F | PR #41: layout (4.P2) not started; nothing ordered | |
| 13 | Wed | First automatic electrical check ran 8 Nov, no errors | M | Nora's CI comment 6722540595 (ERC exit 0, `--severity-error`) | errors only; warnings not counted; generic pin symbols, so no pin-level proof (said in the engineers' layer) |
| 14 | Wed | QA closed the fix from the artefact, not the datasheet | F | QA 6718490484, row C1 ("Closed (from the artefact) ... I did not re-read the Aosong datasheet") | wording checked by Theo; DE says "anhand der Datei geschlossen" |
| 15 | Wed | Founder chose the battery cell and ordered it | F, confirmed by the founder in chat on 8 Nov (no document yet) | Arsany in chat 8 Nov ("I ordered the Amazon cell"); `docs/adr/ADR-015` (PR #53, open); PR #44 README | **HOLD**: card and cell paragraph wait for Arsany's OK of the wording; shop, price, delivery and arrival unknown, so not named and "arrived" is not claimed |
| 16 | Wed | Agents may prepare a purchase but never make one | F | TEAM.md hard rules (nothing ordered or bought by agents) | |
| 17 | Wed | Cell (as built): best 11.0, typical 4.3, worst 1.36 months vs at least 3 / 3 / more than 1 | E | `showcase/items/2026-11-08_4.P1-cell-a045/caption.md` (11.0 / 4.3 / 1.36) | as-built sleep currents after A-045 (power-budget section 12); Theo (review of 8 Nov): the 12.8 / 4.5 / 1.4 in ADR-015 on PR #53 use baseline sleep currents and are being updated; quote only 11.0 / 4.3 / 1.36 |
| 18 | Thu | 26 of 26 mutants caught | M, author's run | `cloud/DUPLICATE-4.B2.md` line "26 mutants, 0 survive"; `showcase/items/2026-11-08_4.B2-x/caption.md` (branch `agent/cloud-ai/4.B2`, commit 12e036c) | QA re-ran only the first 17 (81 s, comment 6718541538); **QA re-run of 26 pending** |
| 19 | Thu | 17 first, then QA's 12 own bugs: 5 caught, 6 real gaps + 1 equivalent; 9 more mutants added | M | QA 6718541538; Theo delta 6722943921 (QA-1..8 + SQL-14 = 9) | |
| 20 | Thu | A real bug: new owner's device kept the old owner's plant link; fixed with a test | F | caption of 4.B2-x; Theo delta 6722943921 section (b) | **found by comparing with the parallel second copy, not by Sana's own tests** (the Lead's brief said "her own tests"; the source says comparison) |
| 21 | Thu | Not live: local database only; PR open | F | PR #45 body; QA "unverified" list | |
| 22 | Fri | Cavity 7.2 mm tall for the chosen cell | C | PR #44 README line 31: 6.3 x 1.1 + 0.2 = 7.13 mm, rounded up to 7.2 mm; Theo 6722955890 | the posts say "7.13 mm, rounded up to 7.2"; old draft said 7.4 mm for another cell (not selected); do not use 7.4 |
| 23 | Fri | 22 tests pass; QA's 4 mutants all failed the tests | M | QA 6723142563 (22 passed; M1-M4) | |
| 24 | Fri | Design rule: function first, then one touch that may never break print, seal or fit; first touch = lid trace relief behind a flag, default off | F, D | `team/learnings/mechanical.md` (rules of 8 Nov, "Arsany ... PR #44"); README design intent | the rule is the founder's, dated 8 Nov |
| 25 | Fri | Nothing printed yet | F | PR #44 "Not run: slicer, physical print" | |
| 26 | Fri | Tracker: 5 builds, 2 merged, as of 8 Nov 16:10; each reviewed and tested | counted | PR states via `gh api`, comments: #41 (6718450327, 6722952512, QA 6718490484, 6722939143), #42 (6718451152, 6718478019), #45 (6718503046, 6718541538, 6722943921), #44 (6718496261, 6718513882, 6722955890, 6723142563), #46 (6718522115, 6718564565, 6723144608) | verdicts: all "approved (with conditions)" and "pass (with notes)"; merged = #41 (15:03) and #42 (14:10 UTC) |
| 27 | Sat | Pipeline could not start the circuit check (EACCES at checkout) | F | PR #43; Nora comment 6718485514 | |
| 28 | Sat | Fix: container as root, nullglob, ERC strict; merged 8 Nov | F | PR #43 body; merge 749ccc5 (15:08) | |
| 29 | Sat | ERC ran, exit 0, no errors | M | Nora 6722540595 (run on 00edafe) | errors only; DRC skipped (no board file) |
| 30 | Sat | FICTION card: kettle, Ines, "Show me the log" | fiction | none (imagined) | no real number, person, customer or quote; labelled in image and first text line |
| 31 | Sun | Founder relaxed the battery rule: best >= 3 months, worst > 1 month | D | PR #53 body ("Arsany decided 2026-11-08, chat"); ADR-015 | PR #53 is open |
| 32 | Sun | Ten documents brought in line | F | PR #53 body list (acceptance matrix, traceability, requirements delta, architecture, risk register, power budget, BOM, A-034 note, bay note, showcase series = 10) | |
| 33 | Sun | Power-budget 25 tests, BOM 12 tests OK | M | PR #53 body | docs PR; agent-reported |
| 34 | Sun | Chosen battery passes on estimates, typical above 4 months, not bench-tested | E | rows 17; ADR-015 | see row 17 |
| 35 | Sun | Two Lead sessions built the same cloud job on 8 Nov; one copy became the PR, the other a branch without PR; nothing deleted; one real bug found by comparing | F | `cloud/DUPLICATE-4.B2.md` (branches `agent/cloud-ai/4.B2` and `agent/cloud/4.B2`, "parallel Lead session") | funny but true; no person blamed |
| 36 | Sun | Cause: shared git clone; rule since: each agent works in its own git worktree | F / D | PR #42 and #44 bodies ("cherry-picked by the Lead, shared-clone mix-up"); the Lead's instruction of 8 Nov | **TEAM.md on main has no worktree rule yet**; posts say "since 8 November we work this way" (a practice from the Lead's instruction), not a TEAM.md rule |
| 37 | all | "AI agents, led and reviewed by humans" | F | brand-kit 5b | |
| 38 | all | Speech bubbles are persona voice written from the evidence | label | `team/PERSONAS.md` | printed on every card |
| 39 | all | No AI-generated imagery; avatars are the team's drawn SVGs | F | `team/avatars/*.svg`; images built by `build_diary.py` | no AI flag needed |
| 40 | all | Human-hour estimates | none used | | no human-hour or minute-saving figures in the posts except Leo's 7.4 agent minutes (measured) |

## Not claimed anywhere (checked)
No price, shop, delivery date, customer, lead, A-ID, private URL, human name beyond the founder's role, "first", "best", "fastest", "autonomous", "X times faster", and no statement that a person merged anything.

## Strict checks run
`python3 -I showcase/brand/check_svg_wellformed.py` (all SVGs in `showcase`, strict XML) and the builder's bounding-box check (`check_bbox.js`, no text past the margin); every PNG viewed (EN and DE), see the result.

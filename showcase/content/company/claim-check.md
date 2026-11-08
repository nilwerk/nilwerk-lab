# Claim check: company posts, days 1-3

As of **Sun 8 Nov 2026, 18:54 Berlin**. Types: F fact of record, D decision or rule, M measured (agent-run), C counted from git, E estimated, P persona voice, none = no number. PR ids and comment ids stay here, never on images. Recount every changing number on the posting day. Theo checks the technical rows; Theo or Nora the German.

| # | Post | Claim (as written) | Type | Source | Note |
|---|---|---|---|---|---|
| 1 | 1 | Sunday 1 Nov: one question to an AI assistant, "can you design a simple 3D model and a PCB?" | F | `showcase/stories/origin/README.md` (canon, told by Arsany 5 Nov) | 1 Nov 2026 was a Sunday (8 Nov is a Sunday) |
| 2 | 1 | A tiny plant-stake sensor came out; then checked against requirements and fixed (v2) | F | origin canon | |
| 3 | 1 | v2: rechargeable battery (400 mAh LiPo), USB-C, soil probe, AHT20 + BH1750 | F | origin canon | "battery life never measured; the first simulated figure is outdated" is in the engineers' layer |
| 4 | 1 | A connected gadget needs six skills (firmware, board, case, app, cloud, tests) | D | nilwerk.de "Sechs Disziplinen, ein Gerät" (read 7 Nov, see `about-nilwerk.md` row 2); TEAM.md section 6 | an opinion framing, not a statistic; "small companies rarely have all six" is the founder's premise, no number given |
| 5 | 1 | One team covers all six: AI agents, led and reviewed by humans | D | TEAM.md sections 2, 4; brand-kit 5b | |
| 6 | 1 | Our plant monitor is a prototype, not a product for sale | F | `about-nilwerk.md` row 8 | |
| 7 | 1 | Every number gets a label: measured, simulated or estimated | D | playbook rule; TEAM.md sections 5, 10 | |
| 8 | 1 | **48 changes merged from 3 to 8 Nov** | C | `git log origin/main --merges --first-parent` on 8 Nov 18:54: 3 Nov 2, 4 Nov 4, 5 Nov 2, 6 Nov 11, 7 Nov 13, 8 Nov 16 = 48 (all subjects "Merge pull request"); last merge 8 Nov 18:23 | includes docs, reports and showcase PRs, said so in the text; "six days" = 3 to 8 Nov inclusive; as-of label on the image |
| 9 | 1 | "One post a day" | D | `series.md` (Arsany's decision 7 and 8 Nov) | a plan |
| 10 | 1 | Persona line "Hi, I'm Poppy ... pull up a chair" | P | `team/PERSONAS.md` (Poppy) | labelled "persona voice" on the image |
| 11 | 1 | Stack: ESP32-C3 firmware (ESP-IDF), KiCad, CadQuery, Expo / React Native, Supabase, EU region a decision not live; helper services may process pseudonymous data elsewhere | D | TEAM.md section 6; ADR-003; `about-nilwerk.md` row 7 | Theo's wording rule (region claims) applied |
| 12 | 1 | Avatars of the six disciplines are Mira, Emil, Yara, Leo, Sana, Ines | F | TEAM.md section 2 | Ines = QA, tests |
| 13 | 2 | Eleven AI agents | F | TEAM.md section 2: Nora, Theo, Ines, Kai, Mira, Leo, Sana, Emil, Yara, Poppy, Max = 11 | Max runs as a separate scheduled task (said in the engineers' layer) |
| 14 | 2 | Two humans: the founder and a hardware integrator | F | TEAM.md section 2 | no integrator name; the avatar is `human-public.svg` (the integrator avatar file carries initials and was **not** used) |
| 15 | 2 | Roles and "always asks" lines | F | `team/PERSONAS.md` ("Always asks") | shortened wording of Nora, Theo, Leo, Sana, Kai, Mira, Emil, Yara, Ines, Poppy, Max |
| 16 | 2 | Founder leads, decides and orders; "by our rule nothing is done without his yes" | D | TEAM.md sections 4, 5 ("Arsany merges"; agents never order) | a rule, not an observed fact about each PR (the GitHub login is shared) |
| 17 | 2 | The integrator "will assemble, flash and bench-test the first real boards" | D | TEAM.md section 12; `about-nilwerk.md` row 5 | future tense on purpose |
| 18 | 2 | Agents may prepare a purchase but never make one | D | TEAM.md section 5 (first rule) | |
| 19 | 2 | No board is built yet; so far design, simulation and tests | F | PR #41 (schematic, layout not started), diary claim row 12; `showcase/items/2026-11-08_4.P2-prep` (layout brief only) | recheck on the day |
| 20 | 2 | Review, test and pipeline are separate roles; the author never signs off their own change | D | TEAM.md section 3 (steps 4 to 6), section 4 | |
| 21 | 2 | Personas shape tone, never permissions | D | `team/PERSONAS.md` intro | |
| 22 | 2 | Hands-on work reaches the integrator as a written work order and comes back with measurements | D | TEAM.md sections 5, 12 | |
| 23 | 2 | Hardware figures stay simulated or estimated until measured | D | playbook rule (battery life "simulated") | |
| 24 | 2 | Persona lines are written from the evidence, not quotes | P | brand and diary rules | the image says so; no words in a human's mouth |
| 25 | 3 | Lead agent runs at 07:30 Berlin time, picks one task per builder, smallest useful slice | D | TEAM.md sections 1 and 3 ("at most one task per role per day, smallest shippable slice") | Nora's line is persona voice |
| 26 | 3 | Six steps: plan, build, review, test, pipeline, decide | D | TEAM.md section 3 (steps 1, 3 to 6) and section 4 | "Arsany decides on the merge": rule |
| 27 | 3 | One PR per slice; done = architect approved + QA pass + pipeline green + founder's merge; docs and report PRs have no architect verdict | D | TEAM.md sections 4, 5; Theo's review of PR #40 (playbook) | |
| 28 | 3 | The team works seven days a week | D | TEAM.md section 7 (owner decision 6 Nov) | |
| 29 | 3 | **13 merges on Saturday 7 Nov** | C | `TZ=Europe/Berlin git log origin/main --merges --first-parent` 7 Nov: 13 (counted 8 Nov 18:54; also 15:07 in DAILY.md) | fixed historic day, no recount needed |
| 30 | 3 | A reviewing agent found a sensor drawn with 4 wrong pins; the datasheet has 6; before any board existed | F | architect review of PR #41, comment 6718450327 (U5 AHT20 row); diary claim rows 11-12 | "4 vs 6" tile |
| 31 | 3 | Edge-AI model found 27 % (validation) and 40 % (test) of wetting events against a 95 % goal; the miss was published | M | PR #46 body, QA comment 6718564565; diary claim rows 6-7 | 8 of 20 events; label "target not met" on the image; PR #46 is merged on main (merge e11aa8f, 8 Nov), so "published" is the report on main |
| 32 | 3 | Work needing hands goes to the human integrator as a written work order; what he measures we publish, what is unmeasured we label | D | TEAM.md section 12, playbook | |
| 33 | 3 | "Tomorrow the Agent Diary starts: one agent, one real achievement a day" | D | `diary/README.md`; `calendar.md` (day 4 = Thu 12 Nov) | holds only if Arsany approves the calendar |
| 34 | all | "AI agents, led and reviewed by humans" in the footer | F | brand-kit 5b | |
| 35 | all | No AI-generated imagery; avatars are the team's drawn SVGs; images built by `build_company.py` | F | `team/avatars/*.svg` | no Instagram AI flag needed |

## Not claimed anywhere (checked)
No price, shop, delivery date, customer, lead, A-ID, private URL, human name beyond the founder's, "first", "best", "fastest", "autonomous", "X times faster", human-hour or minute-saving figure, battery-life figure, or a statement that a person merged a specific PR.

## Checks run
`python3 -I showcase/brand/check_svg_wellformed.py` and the builder's bounding-box check (`check_bbox.js`: no text past the margins); every PNG viewed (EN and DE) after the last build, see the result report.

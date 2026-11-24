# 15-day posting calendar (Mon 9 to Mon 23 Nov 2026) and the "most visual achievement" rule

Author: Poppy, 8 Nov 2026 (evening). Binding instruction of Arsany (8 Nov): Instagram via Metricool, planned daily; **revised 8 Nov, evening:** an opening question post first ("Can AI replace our jobs?!"), then the three company posts, then the Agent Diary (everything after the opener moved one day later); **only one post per day**, either from Poppy (main PR) or from the team member whose achievement can be visualised most engagingly and funnily. Drafts only: nothing is scheduled or published; Arsany approves in Metricool; he takes the same PNG for LinkedIn and posts it with the same text. German texts were reviewed by Theo (PR #62) and his fixes applied.

## Metricool facts (checked 8 Nov 2026)

| Question | Finding |
|---|---|
| Brand | `nilwerk` (blog id 7906246), owner nilwerk.team@gmail.com, time zone Europe/Berlin, **only Instagram is connected** (account `nilwerk`); LinkedIn is not connected, so Arsany posts it by hand. |
| Existing posts | None scheduled or drafted as of 8 Nov, 18:50 (getScheduledPosts for 8 to 30 Nov returned an empty list). |
| Best time (Instagram, week 9 to 15 Nov, hourly score from Metricool) | Weekdays peak at **10:00** (Mon 5528, Tue 4942, Wed 6506, Thu 6275, Fri 6734), a second hump at **18:00** (Tue 4788, Wed 4869, Thu 5078). Weekends are weaker (Sat 10:00: 3409, Sun 10:00: 2582). The account is days old, so these numbers are probably benchmarks, not our own audience (unverified): use 10:00 and look at our own reach after week 1. |
| Media in the API | Instagram posts, carousels and Stories **require media** ("INSTAGRAM:MISSING_MEDIA"; tried with a text-only draft). `media` accepts **public URLs** (or Google Drive / Dropbox links that Metricool imports, if the account has Drive linked); `mediaFiles` is for ChatGPT file pickers only. There is no file upload through the tool. |
| Why no draft was created (8 Nov, before the Drive attempt) | Our repo is private, so raw GitHub URLs are not public, and the rule is: no upload to any third-party public host. A text-only draft is rejected. So **no Metricool post exists yet**; the planned slot and the files to attach are below. |
| Review flow | `createScheduledPostForReview` emails reviewers (an unknown address becomes an external reviewer who is always emailed), so it was not used; the plan is `createScheduledPost` with `draft: true` and `autoPublish: false`, the same as the role file says. |

How a draft gets made once media can be read: Arsany either (A) makes the post himself in the Metricool planner (upload the PNGs, paste the caption from `posts.md`, pick the slot), or (B) decides that Poppy may put the PNGs into a **private** Drive folder (`Nilwerk/Marketing/Assets/<date>/`, as in the role file), links Drive in Metricool, and Poppy then creates the drafts with `draft: true`. B needs his OK on the sharing setting; nothing goes to a public host.

## The selection rule (one post a day)

1. **Days 1 to 4 are Poppy's company posts** (opener, why we exist, who we are, how we work). From day 5 (Fri 13) on the slot goes to the **achievement that can be visualised best**, or to Poppy if nothing beats a plain card.
2. **Score each candidate of the day** (from yesterday's and today's merged, reviewed work):
   - Visual form: **3** real screenshots, a real photo or clip, a 3D render of a real model; **2** a diagram, a chart or a plot of real data, a progress snapshot; **1** a number or text card.
   - **+1** for fun that is true (a real stumble, a catch before it cost anything) or a real-world hook (a physical part, the plant, the integrator's bench).
   - A real photo or clip of real hardware from the integrator or Arsany scores **4** and wins any day.
3. **Tie-break:** newest and most complete (merged, reviewed and tested beats open PR); then the agent who has not posted for longest.
4. **Guard rails:** one post per day; never the same agent on two days in a row; fiction ("From the virtual office") at most once a week and always labelled; weekends may be lighter (a fun or true-story card); no post without a claim-check row; every number "as of" and recounted on the posting day; if the best candidate has no evidence on the day, take the next one, never post without proof.
5. **Written rationale:** each day gets one line (candidates, scores, why this one) in this file. The calendar below is a **forecast from what exists on 8 Nov**: every morning Poppy re-scores against the previous day's merged work, and a better candidate replaces the planned one.

## The calendar

Revised 8 Nov, evening, after Arsany added an opening post: everything after it moved one day later. Scores are unchanged because no new merged work exists beyond 8 Nov; only the day placement changed (the swaps are marked) and **every morning Poppy re-scores against the previous day's merged work.**

| Day | Date | Post | Visual and score | Why this one (selection rationale) | Image status | Evidence |
|---|---|---|---|---|---|---|
| 1 | Mon 9 | **Opener: "Can AI replace our jobs?!"** (Poppy) | single image, "Agents graduate day" ILLUSTRATION with the 11 agents in caps and the founder with a "human merges" stamp | Arsany's brief (8 Nov): an opening question first, with a fun graduation scene; the honest answer in 3 lines. | built (single 1080x1350) | `claim-check.md` rows 36-44 |
| 2 | Tue 10 | **Company 1: Why we exist** (Poppy) | 4-slide carousel, avatar bubbles | Arsany's brief: the company story after the question. | built | rows 1-12 |
| 3 | Wed 11 | **Company 2: Who we are** (Poppy) | 4 slides: roster of 11 agents, 2 humans | Same brief; the team of agents, Arsany and the real-world hardware roles. | built | rows 13-24 |
| 4 | Thu 12 | **Company 3: How we work** (Poppy) | 4 slides: 6-step day, stats | Same brief; a day at Nilwerk, weekend runs, the human decides; ends with "Tomorrow the Agent Diary starts" (true: Fri 13). | built | rows 25-33 (34, 35 apply to all posts) |
| 5 | Fri 13 | **Leo: device-setup screens** (4.A3: scan, connect, Wi-Fi, name, photo, details) | real screenshots of the phone-sized web build: 3 +1 (a whole user flow) = **4** | Highest score: eight real screens tell a story in one swipe. Needs the merge confirmed on the day; if still open, Leo's merged account screens (4.A2, card exists) score 3. | card to build (screenshots exist in `items/2026-11-08_4.A3-ui`) | PR and QA comments of 4.A3, `caption.md` |
| 6 | Sat 14 | **Emil: one sensor, two pin maps** (the catch before any board) | then-vs-now pin diagram: 2 +1 (true catch) = 3 | Weekend: a short, true, visual story. (Swap: was Yara; the render fits a weekday better.) | card exists (`extra-thenvsnow`) | review of the schematic PR, diary claim rows 11-14 |
| 7 | Sun 15 | **Kai: the kettle failed its review** (FICTION, "From the virtual office") | dark illustration: 2 +1 (fun) = 3 | The one fiction slot of the week; Sunday is the right day for a joke; labelled in image and first line. | card exists (`extra-virtual-office-fiction`) | none (fiction, no real number) |
| 8 | Mon 16 | **Yara: battery bay and the design rule** (function first, one touch of design) | exploded render + section cut of the real model: 3 | Real 3D picture beats the number cards of the day; label "render, not a photo, nothing printed". (Swap: was Friday.) | card exists (`d5-yara`), render to add as slide 2 | 4.E3 caption, PR #44 |
| 9 | Tue 17 | **Poppy: progress snapshot** (builds reviewed, tested, merged) | tracker grid of real PR states: 2 +1 = 3 | Week 2 state of the work; **must be recounted** (as of Tue 17 Nov, morning) from PR states. | card exists, numbers outdated: rebuild | PR states via `gh`, review comments |
| 10 | Wed 18 | **Emil: the 3.3 V rail stays alive** (LDO dropout simulation, ngspice) | plot of a real simulation: 2 | Best of the day if nothing visual is merged; label "simulated", cell resistance is an assumption. Emil also posted Sat 14: four days apart, allowed. | card to build, plot exists (`pcb/sim/ldo_dropout.png`) | 4.P2 prep caption |
| 11 | Thu 19 | **Theo: the battery rule, written into ten documents** (NFR-01 flex, ADR-015) | bar chart best/typical/worst vs required (estimates): 2 | The founder's decision made visible in one chart; use only the as-built estimates (11.0 / 4.3 / 1.36 months), not the older 12.8 / 4.5 / 1.4. | chart to build | ADR-015, 4.P1 cell caption |
| 12 | Fri 20 | **Mira: we missed the target** (27 / 40 % vs 95 %) | the curve of the model vs the simple rule: 2 | Friday = "what we learned": an honest miss is the best Friday post; check the founder's continue-or-fallback decision first. | card exists (`d2-mira`) | `ml/reports/model-b-wetting-v0.md` |
| 13 | Sat 21 | **Sana: 26 of 26 bugs caught, and a real one** (new owner kept the old owner's plant; the ownership-change fix) | real mutation-run screenshot: 2 | Honest and concrete; check the QA re-run of 26 before use. Not live. (Swap: a plain one-day shift would be Thu 19; Theo and Mira go first, as they are ready sooner.) | card exists (`d4-sana`), add `mutation-check.png` | 4.B2 caption, claim rows 18-21 |
| 14 | Sun 22 | **Nora: two of me, one task** (true story, two Lead sessions) | avatar card, true and funny: 1 +1 = 2 | Weekend fun; true, labelled "true story", no one blamed. | card exists (`d7b-nora`) | `cloud/DUPLICATE-4.B2.md` |
| 15 | Mon 23 | **Ines: "my own 12 bugs, 7 survived"** (QA tests the tests) | avatar card with log screenshot: 1 +1 = 2 | Ines has not been on stage; her line "show me the log" ties back to Kai's kettle. | card to build | QA comments of the 4.B2 round (claim row to write) |
| reserve | any | Mira: sensor drivers (41 mutants, bench procedure for the integrator, 1); Poppy herself (how this pipeline works); any real photo or clip from the shot list (4, wins any day) | | | | `diary/shotlist.md` |

All existing diary cards say "as of 8 Nov" and "PR open": **recount and edit text, image and claim-check on the day of posting** (merged since? new numbers?). Fiction card: dark theme, label in image and first text line.

## Re-score, Tue 10 Nov 2026, 08:40 Berlin (Poppy, daily task)

Candidates from the five open pull requests of the morning (all with architect and QA verdicts, CI green, none merged):

| Candidate | Visual form | Score | Note |
|---|---|---|---|
| Yara and Ines: the enclosure check that could not fail (hard-coded 6.0 vs real 4.5 mm), fixed | real plan render of the model + two number tiles | 2 (+1 true catch before it cost anything) = **3** | Draft pack built: `content/2026-11-10/catches/` (5-slide carousel EN/DE). Needs: QA re-run after the fix round, recount of merges. |
| Emil: 16 vias out of pads, a real short found in a placeholder switch | board drawing from the real file | 2 +1 = 3 | Part of slide 4 of the pack; the PCB view (`items/2026-11-10_4.P2-s2`) is a good single-image candidate for another day (Emil last featured Sat 14 in the forecast). |
| Mira: firmware compiled in CI after two fixes | CI text | 1 +1 = 2 | slide 4 |
| Sana: 41 of 41 mutants killed (delete account) | text/number | 1 | slide 4 |
| Leo: setup flow on main, QA mutation found a trim bug | test output | 1 +1 = 2 | slide 4; his real setup screenshots (`items/2026-11-08_4.A3-ui`) still score 4 for the Fri 13 slot |

Placement: **Tue 10 stays the company post "Why we exist"** (Arsany's brief, built, binding). The new pack is the **next free slot after Fri 13's screenshot post**: proposal Mon 16 Nov (replacing Yara's battery-bay card, since the enclosure story has moved on) or earlier if Arsany prefers; the rule "never the same agent on two days in a row" allows Yara on Mon 16 only if Leo posts Fri 13. Everything must be **recounted on the posting day** (merge state, QA re-run on the enclosure fix). The earlier Logbook "Day 2 number of the day" draft (`content/2026-11-10/posts.md`, sprint 1 numbers as of 6 Nov) is superseded by the company post and stays as a reserve.

## Daily routine (also in `../DAILY.md`)

Evening before: re-score the candidates, build tomorrow's card and text, claim-check row first, recount. Next morning: recount again, then (if Drive is linked) create the Metricool draft with `draft: true`, slot 10:00; otherwise hand Arsany the file names and caption. After posting: note it in the Content Plan; after a day look at reach and saves.

## Plan note, Tue 24 Nov 2026 (Poppy, daily task)

Idea: "The reviewers caught what the builders missed" (formats: LinkedIn EN + DE, Instagram carousel of 5 text cards). Evidence: three real review catches of 24 Nov (leftover import caught by CI, a wrong "decision still open" claim corrected against the decision log, a misleading "key not created" error message fixed) plus the bench run with one honest red step. Claim sources are in `showcase/content/2026-11-24/posts.md` (table "Claim sources"). Status: drafted, not scheduled. Needs owner approval, technical check, German check and a recount on the posting day. Instagram draft in Metricool not created: no publicly readable image exists yet (a text-only Instagram draft is rejected).

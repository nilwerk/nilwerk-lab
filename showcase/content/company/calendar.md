# 14-day posting calendar (Mon 9 to Sun 22 Nov 2026) and the "most visual achievement" rule

Author: Poppy, 8 Nov 2026 (evening). Binding instruction of Arsany (8 Nov): Instagram via Metricool, planned daily; first 3 posts about the company, then the Agent Diary; **only one post per day**, either from Poppy (main PR) or from the team member whose achievement can be visualised most engagingly and funnily. Drafts only: nothing is scheduled or published; Arsany approves in Metricool; he takes the same PNG for LinkedIn and posts it with the same text. German texts were reviewed by Theo (PR #62) and his fixes applied.

## Metricool facts (checked 8 Nov 2026)

| Question | Finding |
|---|---|
| Brand | `nilwerk` (blog id 7906246), owner nilwerk.team@gmail.com, time zone Europe/Berlin, **only Instagram is connected** (account `nilwerk`); LinkedIn is not connected, so Arsany posts it by hand. |
| Existing posts | None scheduled or drafted as of 8 Nov, 18:50 (getScheduledPosts for 8 to 30 Nov returned an empty list). |
| Best time (Instagram, week 9 to 15 Nov, hourly score from Metricool) | Weekdays peak at **10:00** (Mon 5528, Tue 4942, Wed 6506, Thu 6275, Fri 6734), a second hump at **18:00** (Tue 4788, Wed 4869, Thu 5078). Weekends are weaker (Sat 10:00: 3409, Sun 10:00: 2582). The account is days old, so these numbers are probably benchmarks, not our own audience (unverified): use 10:00 and look at our own reach after week 1. |
| Media in the API | Instagram posts, carousels and Stories **require media** ("INSTAGRAM:MISSING_MEDIA"; tried with a text-only draft). `media` accepts **public URLs** (or Google Drive / Dropbox links that Metricool imports, if the account has Drive linked); `mediaFiles` is for ChatGPT file pickers only. There is no file upload through the tool. |
| Why no draft was created | Our repo is private, so raw GitHub URLs are not public, and the rule is: no upload to any third-party public host. A text-only draft is rejected. So **no Metricool post exists yet**; the planned slot and the files to attach are below. |
| Review flow | `createScheduledPostForReview` emails reviewers (an unknown address becomes an external reviewer who is always emailed), so it was not used; the plan is `createScheduledPost` with `draft: true` and `autoPublish: false`, the same as the role file says. |

How a draft gets made once media can be read: Arsany either (A) makes the post himself in the Metricool planner (upload the PNGs, paste the caption from `posts.md`, pick the slot), or (B) decides that Poppy may put the PNGs into a **private** Drive folder (`Nilwerk/Marketing/Assets/<date>/`, as in the role file), links Drive in Metricool, and Poppy then creates the drafts with `draft: true`. B needs his OK on the sharing setting; nothing goes to a public host.

## The selection rule (one post a day)

1. **Days 1 to 3 are Poppy's company posts** (why we exist, who we are, how we work). From day 4 on the slot goes to the **achievement that can be visualised best**, or to Poppy if nothing beats a plain card.
2. **Score each candidate of the day** (from yesterday's and today's merged, reviewed work):
   - Visual form: **3** real screenshots, a real photo or clip, a 3D render of a real model; **2** a diagram, a chart or a plot of real data, a progress snapshot; **1** a number or text card.
   - **+1** for fun that is true (a real stumble, a catch before it cost anything) or a real-world hook (a physical part, the plant, the integrator's bench).
   - A real photo or clip of real hardware from the integrator or Arsany scores **4** and wins any day.
3. **Tie-break:** newest and most complete (merged, reviewed and tested beats open PR); then the agent who has not posted for longest.
4. **Guard rails:** one post per day; never the same agent on two days in a row; fiction ("From the virtual office") at most once a week and always labelled; weekends may be lighter (a fun or true-story card); no post without a claim-check row; every number "as of" and recounted on the posting day; if the best candidate has no evidence on the day, take the next one, never post without proof.
5. **Written rationale:** each day gets one line (candidates, scores, why this one) in this file. The calendar below is a **forecast from what exists on 8 Nov**: every morning Poppy re-scores against the previous day's merged work, and a better candidate replaces the planned one.

## The calendar

| Day | Date | Post | Visual and score | Why this one (selection rationale) | Image status | Evidence |
|---|---|---|---|---|---|---|
| 1 | Mon 9 | **Company 1: Why we exist** (Poppy) | 4-slide carousel, avatar bubbles | Arsany's brief: a strong start with the company story. | built | `claim-check.md` rows 1-12 |
| 2 | Tue 10 | **Company 2: Who we are** (Poppy) | 4 slides: roster of 11 agents, 2 humans | Same brief; the team of agents, Arsany and the real-world hardware roles. | built | rows 13-24 |
| 3 | Wed 11 | **Company 3: How we work** (Poppy) | 4 slides: 6-step day, stats | Same brief; a day at Nilwerk, weekend runs, the human decides. | built | rows 25-33 (34, 35 apply to all posts) |
| 4 | Thu 12 | **Leo: device-setup screens** (4.A3: scan, connect, Wi-Fi, name, photo, details) | real screenshots of the phone-sized web build: 3 +1 (a whole user flow) = **4** | Highest score: eight real screens tell a story in one swipe. Needs the merge confirmed on the day; if still open, Leo's merged account screens (4.A2, card exists) score 3. | card to build (screenshots exist in `items/2026-11-08_4.A3-ui`) | PR and QA comments of 4.A3, `caption.md` |
| 5 | Fri 13 | **Yara: battery bay and the design rule** (function first, one touch of design) | exploded render + section cut of the real model: 3 | Beats the number cards of the day; a real 3D picture, label "render, not a photo, nothing printed". Friday suits the rule "function first". | card exists (`d5-yara`), render to add as slide 2 | 4.E3 caption, PR #44 |
| 6 | Sat 14 | **Emil: one sensor, two pin maps** (the catch before any board) | then-vs-now pin diagram: 2 +1 (true catch) = 3 | Weekend: a short, true, visual story; Emil makes his first appearance. | card exists (`extra-thenvsnow`) | review of the schematic PR, diary claim rows 11-14 |
| 7 | Sun 15 | **Kai: the kettle failed its review** (FICTION, "From the virtual office") | dark illustration: 2 +1 (fun) = 3 | The one fiction slot of the week; Sunday is the right day for a joke; labelled in image and first line. | card exists (`extra-virtual-office-fiction`) | none (fiction, no real number) |
| 8 | Mon 16 | **Poppy: progress snapshot** (builds reviewed, tested, merged) | tracker grid of real PR states: 2 +1 = 3 | Week 2 opens with the state of the work; **must be recounted** (as of Mon 16 Nov, morning) from PR states. | card exists, numbers outdated: rebuild | PR states via `gh`, review comments |
| 9 | Tue 17 | **Emil: the 3.3 V rail stays alive** (LDO dropout simulation, ngspice) | plot of a real simulation: 2 | Best of the day if nothing visual is merged; label "simulated", cell resistance is an assumption. | card to build, plot exists (`pcb/sim/ldo_dropout.png`) | 4.P2 prep caption |
| 10 | Wed 18 | **Sana: 26 of 26 bugs caught, and a real one** (new owner kept the old owner's plant; the ownership-change fix) | real mutation-run screenshot: 2 | Honest and concrete; check the QA re-run of 26 before use. Not live. | card exists (`d4-sana`), add `mutation-check.png` | 4.B2 caption, claim rows 18-21 |
| 11 | Thu 19 | **Theo: the battery rule, written into ten documents** (NFR-01 flex, ADR-015) | bar chart best/typical/worst vs required (estimates): 2 | The founder's decision made visible in one chart; use only the as-built estimates (11.0 / 4.3 / 1.36 months), not the older 12.8 / 4.5 / 1.4. | chart to build | ADR-015, 4.P1 cell caption |
| 12 | Fri 20 | **Mira: we missed the target** (27 / 40 % vs 95 %) | the curve of the model vs the simple rule: 2 | Friday = "what we learned": an honest miss is the best Friday post; check the founder's continue-or-fallback decision first. | card exists (`d2-mira`) | `ml/reports/model-b-wetting-v0.md` |
| 13 | Sat 21 | **Nora: two of me, one task** (true story, two Lead sessions) | avatar card, true and funny: 1 +1 = 2 | Weekend fun; true, labelled "true story", no one blamed. | card exists (`d7b-nora`) | `cloud/DUPLICATE-4.B2.md` |
| 14 | Sun 22 | **Ines: "my own 12 bugs, 7 survived"** (QA tests the tests) | avatar card with log screenshot: 1 +1 = 2 | Rest day for the visual score; Ines has not been on stage; her line "show me the log" ties back to Kai's kettle. | card to build | QA comments of the 4.B2 round (claim row to write) |
| reserve | any | Mira: sensor drivers (41 mutants, bench procedure for the integrator, 1); Poppy herself (how this pipeline works); any real photo or clip from the shot list (4, wins any day) | | | | `diary/shotlist.md` |

All existing diary cards say "as of 8 Nov" and "PR open": **recount and edit text, image and claim-check on the day of posting** (merged since? new numbers?). Fiction card: dark theme, label in image and first text line.

## Daily routine (also in `../DAILY.md`)

Evening before: re-score the candidates, build tomorrow's card and text, claim-check row first, recount. Next morning: recount again, then (if Drive is linked) create the Metricool draft with `draft: true`, slot 10:00; otherwise hand Arsany the file names and caption. After posting: note it in the Content Plan; after a day look at reach and saves.

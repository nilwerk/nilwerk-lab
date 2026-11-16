# Week post plan, Mon 16 to Sun 22 Nov 2026

Author: Poppy (PR & Social) · written Sat 14 Nov 2026, evening Berlin · **PLAN ONLY. Nothing is written beyond what already exists, nothing is scheduled, no Metricool draft exists, nothing is published. Arsany approves each post and publishes himself.**

**Facts are as of Sat 14 Nov 2026, about 19:20 Berlin** (pull-request states read with `gh api`). Every changing fact is recounted on the posting day.

**Theo's fact check of the claims in this plan is still pending.** The only pack that already had one is "A test that could not fail" (checked by Theo, fixed in PR #79; the numbers in it still need a recount). Every other row below is Poppy's reading of the repo, not yet checked by Theo. The German texts have not been checked by Theo or Nora either (open for every post).

## 1. Channels, language, rules this plan follows

| Item | Setting | Source |
|---|---|---|
| Channels | LinkedIn `@nilwerk` and Instagram `@nilwerk`. Only Instagram is connected in Metricool; LinkedIn is posted by hand. No Metricool draft is made in this task (the repo is private, so Metricool cannot read the images; Arsany uploads the PNGs himself) | `company/calendar.md`, `DAILY.md` section 5 |
| Language | LinkedIn: English text plus a German text of the same post (Arsany posts one of them, see question Q1). Instagram: English caption plus one German line. Plain, correct German; the check by Theo or Nora is open | `team/roles/pr-social.md` |
| Time | Weekdays 10:00 Europe/Berlin (Metricool best-time data, 8 Nov: weekday peak at 10:00, second hump at 18:00; the account is days old, so this is a benchmark, not our own audience). Weekend lighter. Look at our own reach after this week | `company/calendar.md` |
| Rhythm | One post a day at most, the best-evidenced one; no post without a claim-check row; never the same agent two days in a row (see note under the table) | `DAILY.md` section 5 |
| Honesty line on every post | "AI agents, led and reviewed by humans." Hardware work by "our hardware integrator", no names except the founder; no prices, offers, customers, leads, open questions, decision ids, private URLs | playbook, `brand/USAGE.md` |
| Estimates | Agent minutes only as "measured" with the source; human-hour equivalents only as "the agents' own estimate"; battery life and every v1 number only "simulated" or "not measured" | playbook |

## 2. The week at a glance

| Day | Channel | Language | Post | Format | Time (Berlin) |
|---|---|---|---|---|---|
| Mon 16 Nov | LinkedIn + Instagram | LI EN/DE, IG EN + DE line | A test that could not fail (approved pack) | LI: single post with 1 to 5 images; IG: carousel, 5 slides | 10:00 |
| Tue 17 Nov | LinkedIn + Instagram | LI EN/DE, IG EN + DE line | The plan changed: a function demo on a perfboard while the custom board waits | LI: single post with the wiring diagram; IG: carousel, 3 slides | 10:00 |
| Wed 18 Nov | LinkedIn poll + Instagram Story | EN (LinkedIn poll also DE) | Engagement: "If the custom board is weeks away, what would you do?" | LI: native poll; IG: Story with poll sticker made by Arsany on the phone | 10:00 (Story 18:00) |
| Thu 19 Nov | LinkedIn + Instagram | LI EN/DE, IG EN + DE line | A fab-file package that says NOT FOR ORDER (quote kit, stale files marked) | single image, fresh render needed | 10:00 |
| Fri 20 Nov | LinkedIn + Instagram | LI EN/DE, IG EN + DE line | Weekly update #3: teaser of what the client update shows | single image (the "sprint in numbers" card layout) | 18:00 |
| Sat 21 Nov | Instagram first, LinkedIn optional | IG EN + DE line | Two housings, one week: the compact one paused, the demo one drawn | before/after, 2 images | 10:00 |
| Sun 22 Nov | none | none | Rest day (no post; nothing is queued) | none | none |

That is 6 posts (the Wednesday Story belongs to the poll). The Sunday gap is on purpose: no real news is due, and the weekend run does not create evidence.

**Guard-rail note.** Tue (Emil's wiring diagram, Yara's housing) and Thu (Emil's fab files) are two days apart, not consecutive, so the rule holds. Mon features QA (Ines) and the enclosure fit check (Yara); Yara appears again on Tue and Sat in a supporting role. If Arsany prefers fewer repeats, Sat can move to the reserve list (section 5).

## 3. Post by post

Legend for evidence status: **M** measured, **C** calculated, **S** simulated, **F** fact in a file or PR, **D** decision. "NOT claimable" is the list of things that must not appear in the post.

### Mon 16 Nov, 10:00: "A test that could not fail" (approved pack)

- **Channels and format:** LinkedIn (EN or DE text, one image or the 5 slides as a document) and Instagram carousel, 5 slides, 1080x1350. Slot proposed in the pack itself: Mon 16 Nov 10:00.
- **Built on:** `showcase/content/2026-11-10/catches/` (`posts.md`, `claim-check.md`, `images/catches-s1..s5-{en,de}-portrait-1080x1350.png`, `build_images.py`, texts in `catches_data.py`). Showcase item `showcase/items/2026-11-10_4.E3-s2/` (2026-11-10, task 4.E3 slice 2, PR #74, merged 13 Nov 18:31 UTC); pack PR #76 and fixes PR #79 are both merged (#79 on 13 Nov 17:19 UTC), so the "post after PR #79" condition is met.
- **What the post says (already checked and approved):** our own enclosure fit check could not fail (antenna overhang typed in as 6.0 mm, the real board file says 4.5 mm; 4 of 35 rows gave the same answer on two boards); QA found it; the fix reads the board file; QA re-ran the fixed head b98bd69 on 11 Nov: PASS WITH NOTES. Five more catches of the same week.
- **MUST CHANGE on the posting day (recount, `AS_OF` in `catches_data.py`):** the pack says "four of the five changes are merged, the enclosure change is still a draft" (as of 10 Nov 10:45). Since then #74 (the enclosure) merged on 13 Nov. Re-write the status sentence in the LinkedIn text, both captions and slide 5 ("5 of 5 merged" only after re-checking all five with `gh api`; the architect and QA comments of #74 are on earlier heads, keep that wording). Also state, if Arsany wants, that the compact v2 housing work was paused by him on 14 Nov (a decision, not a result).
- **NOT claimable:** anything about a print, a seal test, a measured fit; "every" check or review without a verdict per PR; the 41 of 41 figure beyond "QA's full run at head 9984d24, local PostgreSQL, not real Supabase"; any agent-minutes number (cut in the pack because the Agent Log gave no source for it).
- **Approvals before posting:** (1) Theo's technical rows re-check after the recount; (2) the German check by Theo or Nora, **open**; (3) Poppy recount and edit of the status sentence (Mon morning, before 09:30); (4) Arsany approves the edited text and images; (5) Alt text added, Impressum link on the profile, no AI imagery (none used).
- **Who:** Poppy edits and re-renders the 10 PNGs (Sun 15 Nov evening and Mon 07:30 recount); Theo and Nora check; Arsany uploads the PNGs and posts.

### Tue 17 Nov, 10:00: the plan changed, a function demo on a perfboard

- **Channels and format:** LinkedIn single post (EN or DE) with the wiring diagram; Instagram carousel, 3 slides: (1) wiring diagram, (2) perfboard layout, (3) one line on the housing render. Story line for "agile": we changed the plan in a day, and wrote down what is not proven.
- **Built on:** the owner decision of 14 Nov (daily report 14 Nov, evening update: v1 is a function demo on a perfboard with an ESP32-C3 SuperMini and parts the founder already owns; v2 custom board routing is low priority; the compact v2 housing is stopped). Images and facts from two **open, not merged** pull requests:
  - PR #101, branch `agent/pcb/v1-wiring`, 2026-11-14, task 4.P6 (Emil): `projects/plant-monitor/v1/WIRING.md`, `wiring-diagram.png`, `perfboard-layout.png` (generated from `gen_wiring.py`). Theo APPROVE WITH CONDITIONS and fix round, Ines PASS WITH NOTES (daily report 14 Nov), CI green but CI does not run `v1/` (no gate).
  - PR #102, branch `agent/mechanical/4.E5-v1-housing`, 2026-11-14, task 4.E5 (Yara), stacked on #101 (merge #101 first): `showcase/items/2026-11-14_4.E5/` (`caption.md`, `v1_demo_exploded.png`). 76 tests passed, fit check 15 PASS / 0 FAIL / 35 OPEN.
  - Neither is merged yet. **Condition:** post only after Arsany has merged #101 (and #102 if its render is used), or word it exactly as "in review, not merged yet". The 14 Nov report lists QA notes that change the text after merge: the charge-current formula in `WIRING.md` 2.6 (1200 vs 1100 divided by R_PROG, Emil corrects it), and the old 49 x 34 x 6.0 cell text in #102. Use neither number in the post.
- **What the post can say:** the team had a custom board in progress; the owner decided on 14 Nov to build a working demo first from a perfboard, an ESP32-C3 SuperMini and parts already on the bench; the wiring guide, a wiring diagram and a perfboard layout were drawn and reviewed the same day; a printable two-part housing is modelled for it. "The team changed course in a day; our process is the reason it was cheap to change." Both diagrams are labelled "diagram from our wiring generator, not a photo".
- **NOT claimable:** that the demo is built, wired, powered, flashed or working; any measured current, battery life or range (v1 numbers are not product figures); that the housing is printed, sliced or fitted (all part heights are assumed, the first print is a fit-check part); "splash-proof", "outdoor", "safe to charge unattended" (the housing is indoor-only, no unattended charging); that the custom board is routed, ordered or cancelled (it is paused at low priority, not routed, nothing ordered); the SuperMini brand name beyond "ESP32-C3 SuperMini"; the part-list questions still open; any price or the cost estimate in the housing README; any date for the first physical board (a planning estimate, not a result); decision ids.
- **Approvals before posting:** (1) Arsany merges #101 (and #102) or accepts the "in review" wording; (2) Theo checks the technical rows once the wiring text has the formula fix; (3) German check by Theo or Nora, **open**; (4) Arsany approves text and images; (5) alt text for the diagrams.
- **Who:** Poppy writes the pack on Mon 16 Nov (claim-check first, 3 slides + LinkedIn image 1200x627 from the brand templates); Emil fixes the formula in #101; Theo and Nora check; Arsany posts.

### Wed 18 Nov, 10:00: engagement post (poll)

- **Channels and format:** LinkedIn native poll (4 options, 7 days) with a short EN text and a German version; Instagram Story with a poll sticker, made by Arsany on his phone at 18:00 (Metricool cannot create stickers).
- **Question (EN):** "Our custom circuit board is weeks away. What would you do first?" Options: "Wait for the real board" / "Perfboard demo now" / "Dev kit and firmware first" / "Something else (comment)". DE: "Unsere eigene Platine ist noch Wochen entfernt. Was würdet ihr zuerst tun?" with the same four options.
- **Built on:** the Tuesday post (decision of 14 Nov, `showcase/items/2026-11-14_4.E5/caption.md` and `projects/plant-monitor/v1/WIRING.md` on the #101 branch). It needs no number, so there is nothing to recount; the poll only asks an opinion.
- **NOT claimable:** that the poll result decides anything, that the team follows the majority, any "most people" claim; no result may be quoted as a statistic.
- **Approvals before posting:** Arsany approves the wording; German check by Theo or Nora, **open**; Arsany answers comments himself (agents never reply).
- **Who:** Poppy writes the text on Tue; Arsany posts the poll and the Story. After 7 days Poppy notes the result in the Content Plan (answers never leave the repo without Arsany's OK).

### Thu 19 Nov, 10:00: a fab-file package that says NOT FOR ORDER

- **Channels and format:** LinkedIn single post and Instagram single image (1080x1350 or 1200x627), no price anywhere.
- **Built on:** the JLCPCB quote kit on `main` (PR #98, merged 14 Nov 12:03 Berlin; `projects/plant-monitor/pcb/jlcpcb/quote-kit/`: `QUOTE-KIT.md`, `NOT-FOR-ORDER.txt`, `QUOTE-ONLY_bom-jlc.csv`, `QUOTE-ONLY_cpl-jlc.csv`, the board zip made by KiCad 9.0.9 in CI from main head `1ea7784`, outline 34.5 x 67.8 mm) and the Gerber item `showcase/items/2026-11-13_4.P2-gerber/` (2026-11-13, task 4.P2, PR #87/#95, Emil). The story: we built a click-by-click quote sheet, and we also marked our own older fab files STALE because their board size (67.0 mm) no longer matched the design (67.8 mm). That is a true catch, funny and honest.
  - **Image:** the existing renders in `items/2026-11-13_4.P2-gerber/` carry the old 67.0 mm outline and the item's own caption says "do not publish 67.0 mm as the board size". **They must not be used as the current board.** A fresh render from the CI board zip in the quote kit is needed (Emil or Poppy with gerbonara/matplotlib, as in PR #87); it does not exist yet. If it is not ready by Wed evening, use the fallback: a text card "STALE vs FRESH: 67.0 vs 67.8 mm, two files, one label" built from the numbers in the two documents (no board picture), or move this post to the reserve list.
- **What the post can say:** a fab-file set for a price check exists (board files, parts list with 45 parts on 27 lines, placement file), built from the CI; the board is T-shaped, 34.5 x 67.8 mm; it is a quote kit only, not an order; the human step is Arsany's review before any order.
- **NOT claimable:** any price, quote, cost per board, JLCPCB fee or stock figure (the repo holds catalogue prices read on 9 Nov; prices are never published); that anything is ordered, uploaded or accepted by a manufacturer (nobody opened the JLCPCB order pages); that the board is routed or fab-ready (signal routing is open, 117 unconnected items in the author's earlier DRC report, JLCPCB CAM unverified, no fresh 2-up panel file exists); the panel zip; "ready to order"; any claim that the AHT20 and BH1750 footprints are final (they are placeholders).
- **Approvals before posting:** (1) Theo checks the technical rows and that no price slipped in; (2) German check, **open**; (3) Arsany approves; (4) Emil confirms the fresh render comes from the CI zip (file hash in the claim-check).
- **Who:** Emil (render, Wed), Poppy (text and card, Wed evening), Theo (check), Arsany posts.

### Fri 20 Nov, 18:00: weekly update #3 teaser

- **Channels and format:** LinkedIn single post and Instagram single image using the "sprint in numbers" layout (`showcase/content/2026-11-14/` has the template with "n" placeholders, chip "SAMPLE LAYOUT"; it must be re-rendered with real values). Teaser only: it points to the weekly client update, it does not publish the update.
- **Built on:** weekly update #3 and the sprint review, both drafted by Nora on Friday 20 Nov (4.W3; update #2 was drafted 13 Nov and not sent). Numbers only from Nora's `team/reports/2026-11-20.md`, the Plan sheet and the Agent Log, each with "as of <date, time>". Counts: committed = done + in review + in progress/not started; say separately what Arsany did himself; merges recounted with the command in `DAILY.md` section 2; agent minutes "measured, without the lead's own time"; human hours "the agents' own estimate".
- **What the post can say:** what the week was for (the function demo and what was reviewed), what the update will show (e.g. the wiring diagram and housing render if merged), what is not done yet (one honest sentence).
- **NOT claimable:** anything not in Nora's draft; demo results (nothing is built or measured as of 14 Nov: if Arsany or the hardware integrator build the demo this week, a real photo or clip with their OK can replace the card and wins the slot); battery life; "sprint goal met" unless Nora's review says so; client names or the update's confidential content.
- **Approvals before posting:** (1) Nora's draft exists and Arsany has read it; (2) Poppy fills and recounts after Nora's report (Fri about 16:00); (3) Theo checks the numbers rows, German check **open**; (4) Arsany approves and posts. If Nora's draft is late, the slot moves to Sat 10:00; if it is not there by Sat, use the reserve post.
- **Who:** Nora (update), Poppy (card and text), Theo/Nora (checks), Arsany.

### Sat 21 Nov, 10:00: two housings, one week

- **Channels and format:** Instagram first (before/after, 2 images), LinkedIn optional the same day with the same text; Saturday is a lighter slot (weaker benchmark reach).
- **Built on:** `showcase/items/2026-11-14_4.E3-s5/` (2026-11-14, task 4.E3 slice 5, PR #96, merged 14 Nov; image `side_stake.png`: the compact v2 housing in side profile with a 14 mm soil-stake tail, model outer size 97.3 x 56.9 x 12.2 mm) against `showcase/items/2026-11-14_4.E5/v1_demo_exploded.png` (task 4.E5, PR #102, **not merged**; demo housing 118.5 x 72.6 x 24.2 mm, base + lid, USB-C openings, light window, vents). Before/after: the compact housing for the custom board (paused by the owner on 14 Nov) and the simple box for the perfboard demo. Same week, same design habit: dimensions come from a parametric model, heights are labelled assumed.
- **What the post can say:** both are real renders of parametric models, not photos; the USB-C connector on the custom board was changed to a flat edge-mounted one this week (a decision of 13 Nov); we rejected an unsourced connector height from a brief (11.94 mm upright figure) instead of building on it; the datasheet value read for the flat connector is 3.26 mm, confirmed in a second read by QA (tolerance about +-0.10 mm), while the model still uses 3.30 mm as an assumption until the follow-up slice.
- **NOT claimable:** that either housing is printed, sliced, sealed, splash-proof or fitted (renders only); that the compact housing is cancelled (it is paused); "IP-rated" or any protection class (the demo box is indoor only, open light window and vents); radio range through the 1.6 mm PETG (not measured); that the fit check passes (v1: 15 PASS / 0 FAIL / 35 OPEN; v2 tail variants: 40 PASS / 0 FAIL / 19 OPEN); the 3.30 mm figure as a datasheet value; decision ids; prices or the PETG cost estimate in the README.
- **Approvals before posting:** (1) #102 merged, or "in review" wording; (2) Theo checks (it is the least-checked post of the week; his fix-round conditions on #95/#96 are the source); (3) German line check, **open**; (4) Arsany approves and posts.
- **Who:** Poppy (before/after card from the two renders), Theo (check), Arsany posts. If Yara re-renders after the #102 update (the 14 Nov report says #102 needs an update after #101 merges), use the new render.

### Sun 22 Nov: rest day

No post. Poppy's weekend run only recounts the Monday-to-Saturday numbers for the Content Plan and checks what is reserved for Monday 23 Nov. Arsany answers comments on his own time.

## 4. What Arsany approves before each post (one list)

1. **Text and images** of the post as drafted (he may edit; his edits are the strongest lesson for the playbook).
2. **Claim check:** every number, date and name has a row with type (M, C, S, F, D) and source; "as of" label recounted on the day; nothing from the NOT-claimable list.
3. **Checks by others:** Theo on the technical rows (pending for every post except the Monday pack's original rows), Theo or Nora on the German text (open for every post).
4. **Merge state:** for Tue and Sat, that #101 (and #102) are merged or that the text says "in review, not merged yet".
5. **Legal basics:** alt text on every image, advertising labelling and the Impressum link on the profile; no AI imagery (all visuals are code-generated renders, diagrams and plots; none is AI-generated, so no AI flag).
6. **He posts himself**: he uploads the PNGs and pastes the caption into Instagram (Metricool planner) and LinkedIn; agents do not schedule or publish anything.

Open questions for Arsany:

- **Q1** LinkedIn language: post the English text, the German text, or alternate? (Plan: one language per post, never both on the same day.)
- **Q2** May the hardware integrator be mentioned as "our hardware integrator" in the Tuesday and Friday posts if he builds the demo this week (name only with his OK)?
- **Q3** Real photos or a short clip of the demo, if built this week, would replace the Friday card and win the slot (scores 4 in the selection rule). Does he want that?
- **Q4** Is the Wednesday poll acceptable as asked (opinion only)?

## 5. Reserve posts (evidence already in the repo)

1. **How a change moves through the team** (`showcase/content/2026-11-15/`, day 7 draft): needs a recount of the 13-merge figure and the German check; usable on any free day.
2. **Sprint in numbers template** (`showcase/content/2026-11-14/`): fill with real values; same slot as Friday if Nora's draft is late.
3. **Origin story** (`showcase/stories/origin/`), unchanged canon; good for new followers.

## 6. Unverified in this plan (not hidden)

- Theo's fact check of everything above except the Monday pack's original rows: pending.
- German texts: no check by Theo or Nora yet.
- The two v1 pull requests (#101, #102) are open; their text and numbers can still change in the next fix round.
- The weekday best-time figures are benchmarks from Metricool, not our own audience.
- Nothing about the demo is built, measured or printed as of Sat 14 Nov 2026, 19:20 Berlin; the custom board is not routed and nothing is ordered.

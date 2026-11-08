# Poppy daily checklist (next run and every run)

Goal: one draft pack in `showcase/content/<YYYY-MM-DD>/` (posts EN + DE + Instagram, claim-check, 4 images). Drafts only; Arsany approves and publishes. Series and episode types: `showcase/content/series.md`. Brand: `showcase/brand/USAGE.md`, checks: `showcase/brand/CHECKS.md`.

## 1. Read (about 3 min)

- Yesterday's `team/reports/<date>.md` (time table, Sprint, "Lessons captured", decisions).
- The **Agent Log** (Google Sheet *Plant Monitor – Project Plan*, tab Agent Log): yesterday's rows for measured agent minutes and the agents' own estimates.
- The **Plan** tab (Status, sprint column X) for Done / In review counts.
- Merged PRs of the day (command below) and new `showcase/items/*`.
- `showcase/content/series.md` for today's slot and `team/learnings/pr-social.md` for the rules.

## 2. Recount commands (as-of labels)

Always write "as of <date, time>" next to any count and recount on the day of posting.

- Merges on a day (Berlin time is +0100 in November; use the qualified range):
  `git fetch origin && git log origin/main --merges --first-parent --since="2026-11-07 00:00 +0100" --until="2026-11-08 00:00 +0100" --format='%h %ad %s' --date=format:'%Y-%m-%d %H:%M'`
  Count the lines; note the time of the last one for the "as of" label. **Time zone:** Berlin is +0100 until 28 Mar 2027 (summer time +0200 afterwards; the offset changes on that date), so do not hard-code it for later ranges. Safer: `TZ=Europe/Berlin git log origin/main --merges --first-parent --since="2026-11-07 00:00" --until="2026-11-08 00:00" --format='%h %ad %s' --date=format-local:'%Y-%m-%d %H:%M'`. Example: Sat 7 Nov had 10 merges as of 20:46 and 13 for the whole day (counted 8 Nov 15:07). (Merge commits may show UTC or Berlin time depending on the committer; qualify the range and say which.)
- Merges since Monday of the sprint: same command with `--since="<Monday> 00:00 +0100"`.
- Done and in-review counts: Plan sheet (status column) or the latest report; say which and when. Say whether tasks Arsany does himself are counted.
- Agent minutes: Agent Log, sum of the sprint's rows **without the lead's own time**; "measured". Human hours: "the agents' own estimate".

## 3. Write (about 5 min)

1. Claim-check first: one row per number, date and name (type: measured, calculated, simulated, estimated, decision; source; as-of).
2. Plain story (2-3 short paragraphs), then "For engineers:" (3 lines at most). German: plain, correct.
3. Theo's rules: as-of labels and a recount note; no "every/each" about reviews without a verdict per PR; a region claim lists non-EU helper services and says decision or live; never repeat an old simulated figure once a newer calculation exists.
4. Humans: "AI agents, led and reviewed by humans"; hardware work by "our hardware integrator", no names; no prices, offers, customers, leads, open questions, A-IDs, private URLs.
5. Render from the templates (`content/build_episodes.py`, optional date arguments), **look at every PNG** (EN and DE), run the `CHECKS.md` commands.

## 4. Posting-day checklist (before Arsany publishes)

- [ ] Recount every changing number (merges, tasks, minutes) and update text, image and claim-check.
- [ ] Theo checks the technical rows; **Theo or Nora check the German text**.
- [ ] Alt text for every image; advertising labelling and Impressum link on the profile; no AI imagery without the AI flag.
- [ ] Arsany approves the draft (Needs-Arsany row type "Post approval"); **Arsany publishes himself**. Agents never schedule or publish.
- [ ] After publishing: note the post in the Content Plan and, a day later, reach and saves (3 metrics: reach, saves, profile visits).

## 5. Metricool daily routine and the one-post-a-day rule (Arsany, 8 Nov 2026, binding)

Instagram `@nilwerk` is the only network connected in Metricool; Arsany takes the same PNG and text for LinkedIn by hand. **One post per day**: Poppy's own (company or general PR) or the team member whose achievement is the most visual and fun. Mon 9 Nov is the opening question ("Can AI replace our jobs?!", single image), Tue 10 to Thu 12 Nov are the three company posts (why we exist, who we are, how we work), the Agent Diary starts Fri 13 Nov; the 15-day plan and the written reason for every day are in `company/calendar.md`.

**Selection rule** (details and guard rails in `company/calendar.md`): score the day's candidates from merged, reviewed work: visual form 3 (real screenshots, photo or clip, 3D render), 2 (diagram, chart, plot, progress snapshot), 1 (number or text card); +1 for true fun or a real-world hook; a real photo or clip of real hardware scores 4 and wins. Tie: newest and most complete, then the agent who posted longest ago. Never the same agent two days in a row; fiction at most once a week and labelled; no proof, no post. Write one line of rationale into the calendar.

**Evening before** (about 10 min): read the day's merged PRs (command in section 2), re-score, pick tomorrow's post, write the claim-check row first, build the card from `company/build_company.py` or `diary/build_diary.py`, look at every PNG (EN and DE), run the `CHECKS.md` commands, update `company/calendar.md`.
**Morning of the post**: recount every changing number and edit text, image and claim-check; then make the Metricool draft: `createScheduledPost` with `draft: true`, `autoPublish: false`, `providers: [{network: instagram}]`, `instagramData.type: POST`, `mediaAltText` = the EN alt texts, date 10:00 Europe/Berlin (Metricool's best-time data peaks there on weekdays; check `getBestTimeToPostByNetwork` for the week). Instagram needs **media**: the API accepts public URLs (or linked Drive/Dropbox) only, and a private repo is not public; so as long as Arsany has not enabled a private Drive folder linked in Metricool, hand him the file names and caption instead of a draft, and never use a public third-party host. Never `createScheduledPostForReview` (it emails reviewers), never auto-publish.
**After**: Needs-Arsany row (type Post approval) as text to the Lead, never inside `showcase/`; a day later note reach and saves.

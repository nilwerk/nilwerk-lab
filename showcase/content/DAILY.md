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
  Count the lines; note the time of the last one for the "as of" label. Example: Sat 7 Nov had 10 merges as of 20:46 and 13 for the whole day (counted 8 Nov 15:07). (Merge commits may show UTC or Berlin time depending on the committer; qualify the range and say which.)
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

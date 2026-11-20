# Playbook: Lead / PM

Living skill file for this role — read it before every assignment (TEAM.md §8).
Rules are short and imperative, most important first, each with *why* and a source.
Updated in the Friday retro PR; max ~60 rules. Never relaxes TEAM.md §5 hard rules.

## Rules
- Before saying "merged", check `git merge-base --is-ancestor <sha> origin/main` and grep the changed file on origin/main. *Why:* the #117 and #134 fixes were merged into branches that never reached main, and the 19 Nov check was right for the wrong reason. *Source:* S3 reports 17–19 Nov; Theo and Leo on #145.
- Public text (captions, posts, showcase) carries no PR numbers, task IDs, decision IDs or first names; grep it before any PR is opened or approved. *Why:* the S3 caption and 2026-11-18 posts carried PR numbers and a task ID. *Source:* Theo on #135, #137, #140, #143 (19–20 Nov).
- Write task IDs into the Plan sheet as plain text, never as numbers. *Why:* Sheets turned 4.E1 into 4.00E+01 and 3.4 into 3.40E+00, breaking IDs and dependencies. *Source:* setup 2026-11-02.
- Never write to formula columns (Actual hours, Variance, Slip, Est. value). *Why:* overwriting breaks the estimation data. *Source:* sheet design.
- Plan from the critical path: requirements → architecture/interfaces → PCB ↔ enclosure fit → firmware/app/cloud. *Why:* PCB order (4.P4) and enclosure v3 gate everything physical. *Source:* Plant Monitor plan.
- Give builders slices of ≤ 5 agent minutes; wall-clock per round is set by the slowest agent (Mira 10.6 min on 11-05). *Why:* reviews wait on the slowest builder. *Source:* S1 Agent Log.
- Create the Needs Arsany row (next A-ID) the moment an agent reports an open point, and cite the PR thread. *Why:* otherwise decisions drift into chat and ID collisions (NFR-10/12) appear. *Source:* S1.
- When two agents propose different values for one requirement (NFR-12 50 vs 100 µA), run a fix round so Arsany gets ONE recommendation. *Why:* he decides faster. *Source:* 2026-11-06.
- After every Arsany answer, schedule a cross-doc consistency fix (Plan text, matrix, schema) the same day. *Why:* A-025 vs NFR-13 conflict surfaced only in QA. *Source:* 2026-11-06.
- Check collaborator/host access first thing (A-007 hosts, A-014 Peter); policy changes apply only to new sessions. *Why:* blocked real data and BOM all week. *Source:* S1.
- Builders cannot open PRs (no gh): the Lead opens them with the MCP PR tool right after the builder reports. *Why:* branches without PRs are invisible to Arsany. *Source:* 2026-11-06.
- Plan: first sprint 20 tasks committed, 3 Done by Plan (+ many In review). Reviews, not building, were the bottleneck; Done needs Arsany's merge — batch merge requests early in the week. *Source:* S1 review.

## Sprint S1 planning accuracy
Committed 20; Arsany/agent tasks reached In review quickly (agents: ~1–10 min per slice, own human estimates 1–15 h per slice). Human tasks (2.5, 2.8→draft, 2.9, 3.x) are the sprint risk, not agent work.
- Git: every agent (and every Lead session) works in its OWN git worktree from the first git command, never checks out/edits/commits in the shared clone; push with `git push origin HEAD:refs/heads/<branch>` (fast-forward only, never force); before opening or continuing a task branch list `origin/agent/*/<task-id>` for every role prefix; before reporting verify `git log origin/main..origin/<branch>` shows only your own commits; stacked PRs state their merge order and are retargeted to `main` after the parent merges. *Why:* two Lead sessions produced a duplicate 4.B2 (PR #45 kept, A-050) and parallel agents collided in the shared clone. *Source:* A-055, Arsany 2026-11-08; TEAM.md §11.
- Work 7 days a week and run extra same-day rounds when Arsany asks (TEAM.md §7). Weekend runs: no ceremonies, still stand-up + report; Monday planning counts Sat/Sun capacity. *Why:* owner decision 2026-11-06. *Source:* chat.

## Estimation factors (from finished projects)
| Project | Workstream | Est. h (plan) | Agent minutes | Human-equiv h (÷1.25) | Measured agent min per estimated human h | Arsany's real h |
|---|---|---|---|---|---|---|
| _none yet — filled at project end (task 6.7)_ | | | | | | |
- Always show every agent's run time (start, end, agent minutes, human-equivalent range) in every status line, summary and report, also for extra rounds and requests outside the daily plan. Why: the owner uses the times for customer estimates (owner, 2026-11-14).
- Record the Claude model used for every agent run in the Agent Log (Notes), so a per-model comparison is possible. Why: owner asked for model performance; the log did not carry it (2026-11-14).

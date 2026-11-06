# Playbook: Lead / PM

Living skill file for this role — read it before every assignment (TEAM.md §8).
Rules are short and imperative, most important first, each with *why* and a source.
Updated in the Friday retro PR; max ~60 rules. Never relaxes TEAM.md §5 hard rules.

## Rules
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

## Estimation factors (from finished projects)
| Project | Workstream | Est. h (plan) | Agent minutes | Human-equiv h (÷1.25) | Measured agent min per estimated human h | Arsany's real h |
|---|---|---|---|---|---|---|
| _none yet — filled at project end (task 6.7)_ | | | | | | |

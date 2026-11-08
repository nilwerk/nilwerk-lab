# Claim check: Logbook Day 7 (how a change moves through the team)

| # | Claim | Type | Source | Status |
|---|---|---|---|---|
| 1 | Path of a code change: builder opens PR, architect reviews, QA tests, pipeline checks, human merges | D | `team/TEAM.md` section 3 (steps 3-6) and section 4; `showcase/workflow/team-workflow.md` | ok. Worded as "the path of a code change", not "every/each PR has a verdict" |
| 2 | Reports and documents skip the code tests but go through the human merge | D | TEAM.md section 4/5 (Arsany merges every PR); report/docs PRs have no code CI jobs: reports of 5-6 Nov ("docs-only, workstream jobs skipped by design") | ok (T) Theo confirms the phrase "skip the code tests" |
| 3 | A pull request = a proposal others review before it counts | D | TEAM.md section 3; plain-language definition (`brand/glossary.md`) | ok |
| 4 | 13 pull requests merged on Sat 7 Nov (whole day), **counted on 8 Nov at 15:07** | C | `git log origin/main --merges --first-parent --since="2026-11-07 00:00 +0100" --until="2026-11-08 00:00 +0100"`: #13, #24, #27, #29, #30, #34 (before 11:00), #33 (20:33), #35, #36, #38 (20:43-20:46), #39, #40 (21:29), #37 (21:30). Earlier drafts said "10 as of 20:46"; both numbers are correct for their time | ok; **recount on posting day** (Sun 15 Nov); the "as of" label is on image and text |
| 5 | "founder decides whether to merge" | D | TEAM.md section 5 (Arsany merges) | ok |
| 6 | Where the process was bent: an author's own change waited for an independent reviewer the next day | D | `team/reports/2026-11-04.md` ("2.4 interfaces ... self-authored, independent review pending"); report 3 Nov ("PR #2 and #3 need an independent reviewer") | ok (T) |
| 7 | "we aim for" (no claim that the process is perfect) | opinion | n/a | ok |

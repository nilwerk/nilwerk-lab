# Claim check, content pack 2026-11-19 (for Theo's fact check and Ines's QA)

Poppy (PR & Social) · as of 19 Nov 2026, 08:10 Berlin · base origin/main `9430677`. PR/comment ids are for checking only and never go in the post. Types: measured (test/CI output), observed (a reviewer ran it), read-from-source, status. Comment ids are GitHub issue-comment ids on the named PR. "Rescue PR" = PR #137 (branch `agent/cloud-ai/4.B3-s2`), head read `03827c5`.

**Not for posting before the rescue PR is merged and Arsany approves.**

## Post 1: "The fix that went to the wrong place"

| # | Claim (as used) | Type | Source |
|---|---|---|---|
| C1 | The path guard was reviewed, tested and merged | status | PR #134 merged (GitHub API, `merged: true`); QA's earlier verdicts on it in the #130/#134 threads (not re-read today: Theo/Ines to confirm "reviewed, tested") |
| C2 | It was merged into the export function's side branch after that branch had reached main, so main did not have it | read-from-source | #137 body (A): "merged into the #130 branch after #130 reached main, so it was not on main"; #130 and #134 both merged per API |
| C3 | It was carried over by cherry-pick onto current main, no conflicts, design not re-reviewed | read-from-source | #137 body (A) |
| C4 | The reviewer compared the rescue's 9-file change with the original commit: the code lines were identical. The 9 files are the 7 files of the original commit (5 code/doc files + 2 showcase files) + 2 new showcase files of the rescue. Docs gained one sentence each (README, API description: upload-path wording) in a later commit, after the faithfulness check | observed | #137 Theo 7001966058 ("Faithfulness") and his fact check of PR #141 (line-level diff of the original commit against the rescue head); Ines 7002013927 (9 files). Post text says "code lines identical", never "all identical" |
| C5 | QA tried 7 hand-made mutants of the guard: 5 killed, 2 survived; survivor 1 is a redundant check (equivalent), survivor 2 is a test gap (no 3-segment path with `%`/space/unicode) | observed | #137 Ines 7002013927 (list + notes 1, 2). 5 + 2 = 7 are my count of the listed rows; the gap is "recorded as a note with a suggested test" (Ines's non-blocking note 2, suggested test `${E}/${PL}/a%2e.jpg`); nothing in the PR assigns or tracks it, so no "to-do list" claim |
| C6 | Guard rule: exactly `<uid>/<folder>/<file>`, segments `[A-Za-z0-9._-]`; `..`, leading `/`, backslash, `%`, other prefixes give `url: null`, never signed | observed | #137 Ines 7002013927 ("Contract check"); Theo 7001966058; `_shared/export.ts` per both |
| C7 | Export tests 19/19 (incl. two guard tests), care-tips 68/68, whole cloud run ends "ALL CLOUD TESTS PASSED", Postgres 16.15, Node 22.23.5 | measured | `showcase/items/2026-11-19_4.B2c-4.B3-s2/test-output.txt` (branch `agent/cloud-ai/4.B3-s2`); Ines 7002013927 (re-run, 23/23, 19/19, 68/68) |
| C8 | 31 care-tips tests in the first test file alone, 68 in all test files | measured | same `test-output.txt`; #137 body (B) |
| C9 | Not run: Deno lint and type check (Deno not installed here, CI runs them), mutation script, nothing deployed, live project untouched | status | #137 body; item caption "Unverified" |
| C10 | Pull request open, not merged (as of 19 Nov 08:10 Berlin) | status | GitHub API `pulls/137`: open, merged false |
| C11 | Our "reviewing AI agent" = Theo, "QA agent" = Ines; roles only, no names in the text | read-from-source | comments above |
| C12 | "Our prototype's cloud ... exports all of a user's data, including photo links (7-day)" | read-from-source | #137 Theo ("7-day signed link and download-before-delete flow stay as decided"); item 2026-11-17 4.B2c export in INDEX |

Wording checks: the posts say "it turned out to be missing" (passive, no finder; the evidence names none); "design not re-reviewed" was dropped (the PR was reviewed for faithfulness, traceability and contract) (the evidence does not say who noticed); "a real gap in the tests" is QA note 2. The lesson sentence is Poppy's editorial line, not a quote. No tick for "the whole suite" beyond C7. Do not write "every" about reviews.

## Facts for the other stories (drafted only as ideas; sources if used later)

| # | Fact | Type | Source |
|---|---|---|---|
| S1 | A cloud mutation job runs 66 care-tips mutants + 61 cloud mutants (127), 0 survived; started 07:47, done 08:05 Berlin (18 min) on the PR run | measured | #138 Kai 7002274114. Note: PR body and docs say 67 + 62; the CI run's own numbers (66 + 61) win, as the playbook says. Run only for CI-changing PR; docs-only PRs skip it (gating replay, `showcase/items/2026-11-19_CI-M1/gating-replay.txt`: "only when cloud code changes" verified by replay, not by Actions engine) |
| S2 | QA filled the firmware's retained state with 200000 random-byte states with valid magic: 0 accepted; five fixed patterns all reset; hand mutant (seq == 0 check removed) survived; all-zero with valid magic correctly accepted | observed (throwaway test, not committed) | #140 Ines 7002183221; Theo 7002071681 F1 (blocking finding on `att_head`, the tested head is after it, per QA's `att_head < 12` line) |
| S3 | Delete cleanup must not stop at one odd photo path: remove the good paths, report the leftovers | observed | #139 Theo 7002027380 (C1), Ines 7002108129 (M3 caught; M6/M7 not caught by the PR suite) |

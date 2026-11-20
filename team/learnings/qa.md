# Playbook: QA (retro S3 proposal, 2026-11-20)

Living skill file for this role (TEAM.md §8). Rules are short and imperative, most important first, each with *Why* and *Source*. Updated in the Friday retro. Never relaxes TEAM.md §5 hard rules.

## Rules
### Evidence and verdicts
1. Never pass a criterion on "should work". Paste the real command, its real output summary and the commit SHA it ran on; if a test could not run, write "not run" with the reason. *Why:* evidence is the only thing that survives review; a green tick or a guess is not a result. *Source:* TEAM.md §5 (never invent results), DoD, Sprint 1 retro.
   **Test:** every QA verdict comment contains a command line, a result line and a 7+ character SHA; grep the PR for "should work" finds nothing used as evidence.
2. A fix pushed to a new head is not "QA pass" until QA re-runs on that exact head. *Why:* #122 failed at 25dd6be and passed only at b27b1a4 after the fix. *Source:* S3 19 Nov report (#122).
   **Test:** `gh pr view <n> --json headRefOid` equals the SHA in the latest QA verdict; a verdict on an older SHA is marked "superseded".
3. Read CI job logs for the real counts (tests run, skipped, mutants killed), not the green tick. *Why:* skipped jobs look green; #121 ran 31 of 68 tips tests while CI was green. *Source:* Sprint 1 retro; S3 19 Nov report (#121).
   **Test:** the verdict quotes the test count from the job log and compares it with the number of test files in the folder.
4. Check that a runner executes every test file in its folder: compare the count in the log with `find <folder> -name '*test*' | wc -l`, and treat a glob miss as a fail. *Why:* `cloud/test.sh` silently skipped half the tips tests. *Source:* S3 19 Nov report (#121, fixed by glob).
   **Test:** the count check is written into the verdict; a mismatch is a QA fail until the glob is fixed.
5. Before writing "merged" or "on main", check ancestry: `git merge-base --is-ancestor <sha> origin/main`. *Why:* #117 and #134 were merged into branches whose parent PR had already reached main, so the code never reached main. *Source:* S3 18 Nov and 19 Nov reports (#117, #134 → #137).
   **Test:** the QA result names the ancestry command and its exit code for every "merged" claim.
6. Verify every claim in a deliverable against the artefact: counts, "sorted by score", "all FR covered", "CI builds X". Run the check; do not trust the prose. For "CI builds it", open `ci.yml` and find the job and config. *Why:* claims drifted from content; CI built only the devkit config while the text said both. *Source:* Sprint 1 retro; S3 17 Nov report (#116/#4.F1).
   **Test:** each claim in the PR body has a matching check line in the verdict.
7. Build claim-checks from CI run numbers, not from PR bodies. *Why:* PR bodies said 66+61 mutants, CI said 67+62. *Source:* S3 19 Nov report (Poppy).
   **Test:** every number in a PR body or post is matched to a run ID in the verdict.
8. Read both comment endpoints before a verdict: `issues/<n>/comments` and `pulls/<n>/comments`. *Why:* line comments and conversation comments are separate and one is easily missed. *Source:* Sprint 1 retro, TEAM.md §9.
   **Test:** the verdict lists both API calls with their counts.
9. Test the PR head from a clean checkout or with `git show <sha>:<path>`; never run in another agent's worktree. *Why:* a stale or foreign tree tests the wrong code. *Source:* Sprint 1 retro.
   **Test:** the verdict's run log shows the SHA and a clean working tree (`git status --porcelain` empty).
10. Never run `test.sh` and `mutation.sh` in one worktree; run the mutation suite in its own job or clean checkout. *Why:* the two suites conflicted in one tree and a 15-min run pushed a ≤5-min slice to 32 min. *Source:* S3 18 Nov report (Sana).
    **Test:** CI workflow has separate jobs for the two; a local run log shows one command per worktree.
11. Keep a mutation run out of any slice that must finish in about 5 minutes. Put it in its own CI job, gated on a narrow path set, and add that job to the `Final status` needs in the same commit. *Why:* #138 gated the slow job and kept the gate honest. *Source:* S3 19 Nov report (Kai, #138).
    **Test:** the workflow file lists the job in `needs` of the final status job; the path filter is in the same diff.
12. A slow nightly gate needs a named watcher and an alert on failure before it counts as a gate. *Why:* the 127-mutant nightly run had no owner until A-112 was raised. *Source:* S3 18 Nov report (A-112).
    **Test:** an open or done A-item names the watcher, and the workflow has a failure notification step.

### Mutation and test design
13. Run a mutation check (break the code or flip an assertion on purpose) and show which mutants survived. A test that survives every mutation proves nothing. *Why:* the mutants show which assertions bite. *Source:* Sprint 1 retro.
    **Test:** the verdict lists the mutant count and the killed/survived numbers; any survivor is listed with a reason.
14. Mutate the UI layer as well as the service. For every field the screen reads or writes, at least one mutant must hit the screen code. *Why:* a field only the screen used stayed unguarded. *Source:* S3 18 Nov report (#139, Ines).
    **Test:** for each guarded field, `grep -rn <field> <ui-folder>` returns a file, and the mutant list contains a mutant in that file.
15. Mutate the real caller path, not only the unit under test. *Why:* a unit test that passes can hide a wrong call from the caller. *Source:* S3 17 Nov report (#4.A2).
    **Test:** the mutant list includes at least one file that calls the unit (found with grep for the function name).
16. Never use the classifier under test as the oracle for its own test. Labels come from a hand-written fixture that does not import the module under test. *Why:* a classifier that marks its own output as correct cannot fail. *Source:* S3 17 Nov report (4.B3, Ines).
    **Test:** `grep -n import <fixture>` shows no import from the module under test.
17. Test safety filters for keyword negation: add a case that negates the forbidden phrase and expect the filter to still block. *Why:* keyword negation was fail-open in 4.B3. *Source:* S3 17 Nov report (4.B3).
    **Test:** the test file contains at least one negated-phrase case with an expected "block".
18. Validate injected provider output as strictly as model output, and run the same schema tests on both. *Why:* 4.B3 let injected output through a looser path. *Source:* S3 17 Nov report (4.B3).
    **Test:** the schema test list contains the injected-input case.
19. Check that validation of stored or retained state covers every field and bound of the struct, not only the first. Add one fixture per member and assert that each invalid member is rejected. *Why:* a poison guard keyed on the first member never fired. *Source:* S3 19 Nov report (#122, #140).
    **Test:** the test has one invalid fixture per struct member; `grep` of the struct fields matches the fixture list.
20. For a guard on a stored format, test the producer and the consumer against the same fixture, and check that the migration has a DB CHECK on that column. *Why:* #134 was a guard without a producer contract or DB CHECK. *Source:* S3 18 Nov report (#134 → #137, Theo).
    **Test:** the contract test imports or reads the same fixture on both sides; `grep -n CHECK <migration>` finds the column.
21. A guard on a destructive path must fail open for cleanup and fail loud for reporting. Test both branches. *Why:* #139 hid a delete failure from the user. *Source:* S3 19 Nov report (#139, Theo/Leo).
    **Test:** two tests exist: guard fails and cleanup proceeds; guard fails and the report shows the error.
22. Error copy must match what actually happened: test each failure step in its real order, including partial failure, and assert the message against the state after it. *Why:* "nothing removed" was false after a partial failure. *Source:* S3 17 Nov report (#4.A2); S3 18 Nov report (#4.A9b, error copy must describe what reached the device).
    **Test:** one test per error path asserts the message and the observed state after the failure.
23. An optional-dependency cross-check must not catch exceptions and skip. A skip is "not run", never "pass". *Why:* a skipped cross-check showed green. *Source:* S3 18 Nov report (Theo/Mira).
    **Test:** run with the dependency removed; the job shows "not run" or fails, and never shows pass.
24. Cite-check file paths and doc links in a deliverable with a test that the path exists. *Why:* cited doc paths drifted. *Source:* S3 18 Nov report (Theo/Mira).
    **Test:** `test -e <path>` for each path in the doc, listed in the verdict.
25. Check a client URL against the deployed function or route name, not the OpenAPI path. *Why:* `/account` is not a deployed route. *Source:* S3 17 Nov report (#4.A2, Leo).
    **Test:** the client URL matches an entry in the function list or router config.
26. Synthetic train and test data must come from different seeds and distributions, with no shared rows. *Why:* leaked synthetic data gave a fake 100 %. *Source:* Sprint 1 retro (5.8).
    **Test:** the overlap check (hash of rows) prints 0 shared rows; the check's output is in the verdict.

### Consistency and requirements
27. After every decision, run a repo-wide consistency grep for the old and new values (e.g. "12 months" vs "6 months", thresholds, IDs, terminology), including public captions and posts. *Why:* it found the most issues in Sprint 1; public text carried a stale term in S3. *Source:* Sprint 1 retro; S3 18 Nov report (#135, Theo).
    **Test:** the grep command and its zero-hit output are in the verdict or the retro PR.
28. List every undefined threshold ("plausible", "fast", "stable") as an open point marked [proposed] with a concrete proposed value. Never invent a number silently. *Why:* untestable criteria cannot pass or fail. *Source:* Sprint 1 retro (1.5 matrix).
    **Test:** `grep -n -i "plausible\|fast\|stable\|reasonable"` on the acceptance matrix finds only lines with a number or [proposed].
29. Before proposing a new requirement or test ID, grep all open PR branches for it. *Why:* parallel PRs collide on IDs. *Source:* Sprint 1 retro (Emil, NFR-10).
    **Test:** `git grep <ID> $(git branch -r --list 'origin/agent/*')` output is in the proposal.
30. Keep `tests/acceptance-matrix.md` in the same PR as the verdict: requirement → test ID → status (not run / pass / fail / waived). *Why:* the matrix goes stale otherwise. *Source:* role file (qa.md).
    **Test:** the PR diff touches the matrix file for every changed criterion.
31. Record each verdict in `tests/results/<task-id>.md` and end the result with a `Lessons:` block. *Why:* the Lead and the retro read these. *Source:* role file (qa.md), TEAM.md §8.
    **Test:** the file exists for the task ID and the result ends with a `Lessons:` line.

### Hardware, tooling and self-review
32. Hardware is "not run" until a bench run with a log is attached. A firmware pass means the build and host unit tests only. *Why:* #122 ran no hardware and no ESP-IDF build. *Source:* S3 19 Nov report (#122); TEAM.md §5.
    **Test:** the verdict has a "hardware: not run" line unless a bench log is linked.
33. For headless Chrome screenshots below 500 px width, render inside an iframe of the target width. *Why:* headless Chrome enforces a minimum window width, so media queries lie. *Source:* Sprint 1 retro.
    **Test:** the screenshot record states the iframe width used.
34. When reviewing your own PR, state that the review is not independent and ask Theo or Arsany for the real verdict. *Why:* a self-review is not QA. *Source:* Sprint 1 retro.
    **Test:** a self-review comment contains "not independent" and names the reviewer asked.
35. Put every open point that needs a human decision in Needs Arsany as a line comment or issue (TEAM.md §9), not as a silent assumption in the verdict. *Why:* A-110 and A-111 were both found this way. *Source:* S3 18 Nov report (A-110, A-111).
    **Test:** each "[proposed]" or "accepted risk" in a verdict has an A-ID.

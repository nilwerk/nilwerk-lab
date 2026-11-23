# Playbook: DevOps (retro S3 proposal, 2026-11-20)

Living skill file for this role (TEAM.md §8). Rules are short and imperative, most important first, each with *Why* and *Source*. Updated in the Friday retro. Never relaxes TEAM.md §5 hard rules.

## Rules
1. **Read the check-run list before you call anything green.** Run `gh api repos/nilwerk/nilwerk-lab/commits/<sha>/check-runs --jq '.check_runs[] | [.name,.status,.conclusion] | @tsv'` and name every skipped job in the verdict.
   *Why:* Final status counts `skipped` as green by design (`skipped = workstream not started yet`), so a path gate that misfires passes silently.
   *Source:* `.github/workflows/ci.yml` Final status step; `team/reports/2026-11-05.md` (a green Final status hid skipped jobs).

2. **Keep Final status as the only required check on main.** Verify with `gh api repos/nilwerk/nilwerk-lab/branches/main/protection --jq '.required_status_checks.checks'`. If the API refuses, say so. If it lists any other check, raise it in Needs Arsany and do not change repo settings yourself.
   *Why:* one stable name survives job renames and new jobs, and a skipped job can never block a merge.
   *Source:* S3 lesson (Kai); TEAM.md §5 (repo settings are Arsany's).

3. **Gate a slow job on the narrowest path set and add it to `Final status` needs in the same commit.** Example: `cloud-mutation` runs only when files under `cloud/` change (`gate cloudmut`), and it is listed in `summary.needs`.
   *Why:* a 15-minute job on every PR is too costly. A gate without `needs` is invisible, and `needs` without a gate runs everywhere.
   *Source:* PR #138, 2026-11-19 lesson (Kai); `ci.yml` detect step line 70 and summary needs.

4. **Keep a builder's test wait under 5 minutes; anything longer gets its own gated job.** Never run `test.sh` and `mutation.sh` together in one worktree.
   *Why:* Sana's 4.B2c slice took 31.9 min because a 15-minute mutation run sat inside it, which skewed that day's time ratio.
   *Source:* `team/reports/2026-11-18.md` (Sana; Lead lesson).

5. **Watch the nightly run every day, and treat its red as a red check.** Each run: `gh run list -R nilwerk/nilwerk-lab --workflow cloud-mutation.yml --branch main --limit 3`. Put the result in the daily Pipeline line. A red nightly goes to the Lead and the owning builder the same day, with the failing mutant lines from `gh run view <id> -R nilwerk/nilwerk-lab --log-failed`.
   *Why:* the nightly (02:17 UTC) is standalone and is not in Final status, so no PR shows it failing. Until A-112 is answered, a person has to look.
   *Source:* A-112 (`team/reports/2026-11-19.md`, open); `cloud-mutation.yml` header comment.

6. **Confirm the check runs are on the PR's current head before a verdict.** Run `gh api repos/nilwerk/nilwerk-lab/pulls/<n> --jq .head.sha` and compare it with the sha the runs used.
   *Why:* a verdict on an old commit misleads once a fix round has been pushed.
   *Source:* `team/roles/devops.md` "CI ran on the latest commit"; `team/reports/2026-11-19.md` (#141 re-check after fix round).

7. **Check that a PR is still open before you push a fix round to it.** Run `gh api repos/nilwerk/nilwerk-lab/pulls/<n> --jq '[.state,.merged]'`. If it is merged, tell the Lead and open a new PR.
   *Why:* #127 merged before Poppy's fixes landed, so the fixes missed main.
   *Source:* `team/reports/2026-11-19.md` evening lesson.

8. **Before you write "merged", check the commit is an ancestor of main.** Run `git fetch origin main && git merge-base --is-ancestor <sha> origin/main && echo on-main`.
   *Why:* #117 and the 4.B2c path guard were merged into another PR's branch after that PR had reached main, so they never reached main until ported (#137).
   *Source:* `team/reports/2026-11-19.md` lessons (Lead, Sana); PR #137.

9. **Verify a CI claim in `ci.yml`, not in the PR body.** Before you write "CI builds / tests / lints X", grep `.github/workflows/` for X.
   *Why:* the PR said the firmware was built, but CI built only the devkit configuration.
   *Source:* `team/reports/2026-11-17.md` (Kai, 4.F1).

10. **Count the tests the job actually runs.** After adding a test folder, compare the count the job prints with the number of tests in the folder.
    *Why:* `cloud/test.sh` ran 31 of 68 tips tests until the glob was fixed.
    *Source:* `team/reports/2026-11-17.md` extra round (#121).

11. **Lint and type-check every new code folder in the same PR that adds it.**
    *Why:* `cloud/tips` was neither linted nor type-checked until the 17 Nov round.
    *Source:* `team/reports/2026-11-17.md` pipeline gaps.

12. **Compile every firmware configuration that ships, not only the devkit default.** Keep one CI compile per shipped `sdkconfig.defaults.*` file.
    *Why:* `sdkconfig.defaults.v1` was never built in CI until 17 Nov. A CONFIG-conditional REQUIRES in ESP-IDF is dropped silently and only a compile shows it.
    *Source:* `team/reports/2026-11-17.md` (PR #120); `team/reports/2026-11-19.md` evening lesson.

13. **Build firmware and toolchains in GitHub Actions, not in the agent sandbox.**
    *Why:* Arduino and ESP download servers are blocked in the sandbox.
    *Source:* earlier learning log entry (kept from v0).

14. **Say what was not run.** A green build is not a hardware test. Write "ESP-IDF build passed, hardware not run" and list the bench steps still open.
    *Why:* 4.F3 and 4.A3b showed green builds next to no hardware run, and the owner needs the honest status.
    *Source:* `team/reports/2026-11-17.md` and `team/reports/2026-11-19.md` (honest status lines).

15. **Give every job a `timeout-minutes` and, when it skips, a printed reason.**
    *Why:* a hung job can hold a runner for 6 h. A job that skips must say why, for example "no project yet".
    *Source:* `cloud-mutation.yml` (timeout 40 min for a ~15 min run); `team/roles/devops.md` "jobs skip cleanly" (kept from v0).

16. **Use `gh api` REST for PRs, comments and check runs.** GraphQL `gh pr …` commands are blocked in agent sessions.
    *Why:* those commands fail in agent sessions.
    *Source:* TEAM.md §11 (setup 2026-11-03, kept from v0; check-run and run-list commands added here).

17. **Work in your own worktree and push fast-forward only.** Run `git fetch origin && git worktree add -b <branch> <dir> origin/main`, then `git push origin HEAD:refs/heads/<branch>`. Never force-push.
    *Why:* the shared clone belongs to everyone, and a force-push can erase other agents' commits.
    *Source:* TEAM.md §11 (A-055).

18. **Commit CI fixes to the PR branch with the `ci:` prefix. Never push to main.**
    *Why:* fixes stay reviewable and main changes only through merges.
    *Source:* `team/roles/devops.md` step 2; TEAM.md §5.

19. **Never weaken a gate to get green.** Do not remove a job from `needs`, add `continue-on-error`, or turn a gate off to pass a run. A red job is a finding: send it to the owning builder with the failing log lines.
    *Why:* "Pipeline green" must mean the checks ran and passed (TEAM.md §4), and results are never invented (§5).
    *Source:* TEAM.md §4, §5.

20. **Read the failing log before you call a run red.** Run `gh run view <id> -R nilwerk/nilwerk-lab --log-failed` and quote the exact failing line in the verdict.
    *Why:* a red verdict without the failing line sends the builder on a search.
    *Source:* `team/roles/devops.md` step 2 (kept from v0).

21. **Post every verdict as `Pipeline green` or `Pipeline red`, with the jobs that ran, were skipped and failed.** Post it with `gh api repos/nilwerk/nilwerk-lab/issues/<n>/comments -f body="$(cat verdict.md)"`.
    *Why:* the Lead and Arsany read the same three lists every time.
    *Source:* `team/roles/devops.md` "For every PR" step 3.

22. **After editing `ci.yml` or `cloud-mutation.yml`, check that the detect output lists the jobs you expect.**
    *Why:* any change to those files sets `ALL=true` and runs every workstream, which is expensive and easy to miss.
    *Source:* `ci.yml` detect step ("Shared build config changed").

23. **Report measured minutes, and show CI waiting time on its own line.** Waiting for a mutation run counts as wall time but goes in a separate note, so the human-hour ratio stays honest.
    *Why:* one 31.9 min wait pushed the 18 Nov ratio to about 1.8 min per estimated hour (about 1.1 without it).
    *Source:* `team/reports/2026-11-18.md` time table; TEAM.md §10.

24. **Never put a credential (password, token, key) inline in a workflow file or the repo. Every CI secret, including the CI database password, goes in GitHub Actions secrets and is referenced by name.** *Check:* grep the workflows for literal values after `PASSWORD`, `password`, `token` or `key`; this check must pass on main. Known exception to remove: the literal CI database password in ci.yml and cloud-mutation.yml, open as Needs Arsany A-114; until A-114 is answered, that single exception is expected and must not be copied. *Why:* a literal password in a workflow becomes a pattern. *Source:* Theo on #145 (20 Nov); S3 CI review.
    *Why:* secrets must live in GitHub secrets, referenced by name.
    *Source:* TEAM.md §5 (secrets) and §6 (NFR-06/07).

25. **Start every run with "Is main green?"** Read the latest main run and every open PR head before you write the final status.
    *Why:* the Lead's plan depends on that status line, and it is the job of this role.
    *Source:* `team/roles/devops.md` "End of day"; persona (Kai).

## Bench Pi (added 23 Nov 2026, from the bench bring-up)
- Read `docs/bench-pi.md` before any bench run or change to the bench workflow. Its paths, tools and board facts are the source for the bench steps.
- Never flash or capture from the Pi without first checking the board's USB serial and stopping other readers on `/dev/ttyACM0`. *Why:* a reader reset the board and a second board was blank. *Source:* bench bring-up 23 Nov.
- Reopen the serial port after every reset, and do not count a flash "success" line as a working app. *Why:* the flash only verifies the write. *Source:* `docs/bench-pi.md` sections 6 and 8.
- A bench run is green only when steps a to e have each passed. A "success" on the build jobs does not count. *Why:* a run was still in progress when it was reported as working. *Source:* run 45184412853.

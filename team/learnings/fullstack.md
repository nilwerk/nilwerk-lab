# Playbook: Full-stack (retro S3 proposal, 2026-11-20)

Living skill file for this role (TEAM.md §8). Rules are short and imperative, most important first, each with *Why* and *Source*. Updated in the Friday retro. Never relaxes TEAM.md §5 hard rules.

## Rules
1. **Before you write "merged" or "on main", verify it.** Run `git merge-base --is-ancestor <sha> origin/main` and grep the changed file or test on `origin/main`. If the fix went into another PR's branch, open it as a PR to main and say so.
   *Why:* #117 (4.A2) was merged into the #114 branch after #114 reached main, so its own PR never merged. Its code reached main only through #123's merge (75f09d5). The #134 path guard (4.B2c) had the same fate and was rescued by #137. Ancestry alone is not enough: it said "yes" for #117 for the indirect reason, so check the file too.
   *Source:* Sprint S3 reports 17, 18, 19 Nov; PRs #117, #123, #134, #137.

2. **Check the PR's state and head before a fix round, and never stack on an unmerged branch.** If you must stack, retarget to `main` as soon as the base merges, then re-run CI.
   *Why:* a fix pushed to an already-merged PR never reaches main (#127 merged before Poppy's fixes). #117 was stacked on #114 and #134 on #130; both landed off main.
   *Source:* 17 Nov Lead lesson; #117, #134; 19 Nov report.

3. **Write "compiled, not run" until a dev build has run on a real phone or device.** A green CI build or a headless check is not a device test.
   *Why:* 4.A3b (real BLE, #126) and 4.F3 (upload adapter, #128) were compiled in CI but never run on a phone or the board. The Done bar is "tested on a phone", so label the status honestly.
   *Source:* Sprint S3 reports 17–19 Nov; #126, #128; Definition of Done (role file).

4. **Trace the default build and a never-provisioned device end-to-end before calling a flow done.** Ask what the first-time user sees with no setup.
   *Why:* the default DevKit build had the setup flow on and silently slept, so Peter would have seen no data. Leo's test: "Can a first-time user do it in three minutes?"
   *Source:* 17 Nov evening lesson; issue #68 correction.

5. **Confirm every endpoint and RPC exists in `docs/interfaces/`, and match the deployed function name, not the OpenAPI path template.** If the contract is missing, mark it "proposed" and ask via the Lead.
   *Why:* the client called `/account`, which is not a route. Inventing a contract breaks the code-against-contract rule.
   *Source:* 4.A2 (#117, 17 Nov); Sprint 1 PR reviews.

6. **Cite file and line for every interface claim, and re-read the Architect's file each round.**
   *Why:* T-13 differed in parameter name, security mode and export parameter from what was assumed.
   *Source:* Sprint 1 PR reviews (T-13).

7. **Draw the user flow against the schema's NOT NULL and key rules before coding.**
   *Why:* flows that violate a constraint are found only at insert time.
   *Source:* Sprint 1 Agent Log.

8. **Never send device data over plain HTTP or without auth.**
   *Why:* the first IoT example did both.
   *Source:* learning log 01.

9. **Use an Expo dev build, not Expo Go, for BLE provisioning.**
   *Why:* the BLE native module does not run in Expo Go.
   *Source:* Plan 4.A3.

10. **Gate a destructive account delete on a completed export that includes photos.** Do not rely on expiring signed URLs as the only copy of user data.
    *Why:* 7-day signed URLs die when the account is deleted, so the export was incomplete. The owner chose to download photos before delete unlocks (A-107 option b).
    *Source:* A-107 (17 Nov); 4.A9b (#133); A-111 (18 Nov).

11. **On a destructive path, separate storage cleanup from row cascades; cleanup fails open and reporting fails loud.** A failed cleanup must not block the user's delete, and it must not be reported as success.
    *Why:* ON DELETE CASCADE does not remove storage files, and the #139 review found the guard on the delete path had to fail open for cleanup and loud for reporting.
    *Source:* Sprint 1 Agent Log; #139 review (19 Nov).

12. **Write error and success copy from the server's real step order and from what actually reached the user or device.**
    *Why:* "nothing removed" was false after a partial failure in 4.A2, and the 4.A9b copy had to describe what reached the device.
    *Source:* 4.A2 (#117, 17 Nov); 4.A9b (18 Nov).

13. **Test the real caller path and the screen, not only the unit: mutate the UI layer too.** A field only the screen reads stays unguarded by service tests.
    *Why:* the 4.A2 QA found the gap only at the real caller path, and on #139 a field used only by the screen stayed unguarded.
    *Source:* 17 Nov lesson (4.A2); 19 Nov lesson (#139).

14. **Check CI-coverage claims against `ci.yml` and the test script's glob, and quote test counts from the CI run log.** Never quote counts from the PR body or memory.
    *Why:* `cloud/test.sh` ran only 31 of 68 tips tests in CI until the glob was fixed; PR-body counts (67+62) did not match the run (66+61).
    *Source:* #121 QA (17 Nov); claim check (19 Nov).

15. **Run test scripts one at a time per worktree, and keep long suites out of your slice.** A 15-minute mutation run belongs in CI, not in a ≤5-minute slice.
    *Why:* the 18 Nov run of test.sh and mutation.sh in one worktree was a mistake to avoid, and the slice took 31.9 min because the 15-minute mutation suite ran inside it.
    *Source:* 18 Nov Lead and Sana lessons (#134).

16. **Put colours in the CSS/theme tokens and user-facing strings in the string catalogue, never inline.**
    *Why:* inline values drift and block theming and translation.
    *Source:* Sprint 1 PR reviews.

17. **At 390px, check each changed screen in headless Chrome or a simulator before calling it done, and wrap wide tables in `overflow-x:auto`.** A headless check is not a device test (rule 3).
    *Why:* wide tables break the 390px layout; the check matches the "tested on a phone" definition as closely as possible without a device.
    *Source:* Sprint 1 PR reviews; Sprint 1 Agent Log.

18. **After any edit, grep the whole repo for stale IDs and terms, and update all copies in one change.**
    *Why:* partial renames left contradictory text in Sprint 1, and the 19 Nov terminology sync needed a repo-wide grep.
    *Source:* Sprint 1 PR reviews; #135 review (19 Nov).

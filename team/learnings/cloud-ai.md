# Playbook: Cloud AI (retro S3 proposal, 2026-11-20)

Living skill file for this role (TEAM.md §8). Rules are short and imperative, most important first, each with *Why* and *Source*. Updated in the Friday retro. Never relaxes TEAM.md §5 hard rules.

## Rules
1. **Never show LLM output to a user without deterministic, unit-tested guardrails.** Guardrails run after the model and can veto it.
   *Why:* the model suggests, the rules decide; a guardrail that is not tested is not a guardrail.
   *Source:* FR-P02; role file (tips).

2. **Say "merged" or "on main" only after `git merge-base --is-ancestor <sha> origin/main` succeeds.** A fix pushed into another PR's branch after that PR reached main is not on main.
   *Why:* #117 went into the #114 branch after #114 merged and shipped only through #123; #134 went into the #130 branch and needed the rescue in #137.
   *Source:* S3 reports 17 Nov (#117), 19 Nov (#137, #134).

3. **Before any fix round, check the PR's state and base.** If the PR is already merged or its base is not main, open the fix against main (or retarget it) and say so.
   *Why:* #127 merged before Poppy's fixes; #134 was stacked on #130 and missed main.
   *Source:* 18 Nov and 19 Nov reports (lesson lines).

4. **Estimate the runtime of any suite before you add it to a slice. A suite over ~2 min goes to a CI job, not to the slice.** Put the mutation suite (about 15–18 min) in a scheduled or path-gated CI job.
   *Why:* the 15-min mutation suite ran inside a ≤5-min slice and took 31.9 min for a 2.5 h task.
   *Source:* 4.B2c path guard, 18 Nov report; CI-M1 #138.

5. **Never run `test.sh` and `mutation.sh` together in one worktree.** Run them one after the other, or in separate worktrees.
   *Why:* the two runs clash on shared state and give false results.
   *Source:* 18 Nov lesson (Sana, Lead).

6. **Safety filters fail closed.** A negation or keyword check that misses a negation must block, not pass.
   *Why:* keyword negation in the tips filter was fail-open (N-1); one miss is a bad-advice path to a user.
   *Source:* 4.B3 slice 1 QA, 17 Nov (Ines).

7. **Never use the classifier under test as its own oracle.** Expected results come from fixtures written by hand, or from an independent rule list.
   *Why:* a self-checking test passes whatever the classifier does.
   *Source:* 4.B3 QA, 17 Nov (Ines).

8. **Validate provider output and injected-provider output as strictly as model output.** Malformed forecast input, empty fields and out-of-range values are rejected before the guardrail runs.
   *Why:* the injected provider path skipped checks that the model path had (N-3).
   *Source:* 4.B3 QA, 17 Nov (Ines).

9. **Any guard on a stored format needs a contract note in the producing task and a DB CHECK constraint.** The migration that adds the CHECK needs Arsany's approval before it is applied (Needs Arsany).
   *Why:* a path guard that is only in code can be bypassed by any writer that skips the function.
   *Source:* #134 (Theo); 18 Nov report, A-108 (migration 20261117000008).

10. **Do not say "deployed" until the migration is applied and the function is deployed.** A merged PR is not a deployment. Order the Needs Arsany items: the guard PR is merged first, then the deploy.
    *Why:* #130 was merged while its deploy waited on A-108, and the path guard was on main only after #137.
    *Source:* 19 Nov report, A-108 note.

11. **Mutate the real caller path and the UI layer, not only the unit under test.** A field that only the screen reads stays unguarded unless a UI-level test covers it.
    *Why:* the export gate was guarded in the service but not in the screen.
    *Source:* #117 (Ines), #139 (Ines), 19 Nov lessons.

12. **On a destructive path, fail open for cleanup and fail loud for reporting.** A "nothing to lose" exception that opens a gate needs a guard against systematic use.
    *Why:* a cleanup error must not block delete, but a report that says "removed" must be true; an all-null exception could be used to skip the export check (A-111).
    *Source:* #139 (Theo/Leo), #133 (Theo), 18 Nov and 19 Nov reports.

13. **When validating retained state, check every index and bound member of the struct, not only the first.**
    *Why:* the poison guard keyed on the last sequence number never fired; only the first member was checked.
    *Source:* #122 (Theo, QA FAIL), #140 (Theo/Mira).

14. **Make the test runner run every test file, and check the count in CI.** Compare the count with the local count, and fail CI if the count drops.
    *Why:* `cloud/test.sh` ran 31 of 68 tips tests in CI because of a glob mismatch.
    *Source:* #121, 17 Nov report (Kai).

15. **Every new `cloud/` folder is linted and type-checked in CI before its first merge.**
    *Why:* `cloud/tips` was not Deno-linted or typechecked until #120.
    *Source:* 17 Nov pipeline gaps (Kai).

16. **A new scheduled CI job names a watcher and gets an alert on failure before the team relies on it.**
    *Why:* the nightly mutation run (#138) had no named watcher; A-112 was raised for it.
    *Source:* #138, A-112 (19 Nov report).

17. **Error messages match the server's real step order and what reached the device.** Test the message against the failure you are describing, including partial failure.
    *Why:* "nothing removed" was false on partial failure; a copy that does not match the step order misleads the user.
    *Source:* #133 and #117 (Theo/Leo), 18 Nov and 17 Nov lessons.

18. **Quote test counts and mutant counts only from the CI run log, never from a PR body or memory.**
    *Why:* a PR body said 67+62 while the CI run showed 66+61.
    *Source:* Poppy, 19 Nov lessons; #138.

19. **Code against a provider interface with a mock provider until Q-13 is answered.** No real provider call is made in code or tests.
    *Why:* the provider decision is still open; a mock keeps CI deterministic and key-free.
    *Source:* Questions tab Q-13; role file.

20. **Never put real API keys in code, tests or logs.** CI uses mocks only.
    *Why:* secret leakage is a hard-rule risk (TEAM.md §5).
    *Source:* role file; TEAM.md §5.

21. **Version every prompt file and test prompts with fixtures that assert constraints on the output, not exact text.**
    *Why:* exact-text tests break on every wording change and miss real violations.
    *Source:* role file (tips prompts).

22. **Put an estimated cost per premium user per month in the PR for every LLM or API call path.**
    *Why:* cost feeds the 2.6 plan; a call path without a cost note cannot be priced.
    *Source:* role file (cost rule).

23. **The MCP server is read-only, and a test proves that a revoked key fails.**
    *Why:* a write tool or a revoked key that still works is a security break.
    *Source:* role file (MCP, FR-P03).

24. **Measure the agent minutes of every build and fix round, and log them with the human estimate.** Harness durations are the source, not the agent's own clock.
    *Why:* the own clock read short against wall time; the S3 ratio is only comparable when measured the same way.
    *Source:* 19 Nov report (time note).

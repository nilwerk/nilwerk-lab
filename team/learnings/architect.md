# Playbook: Architect (retro S3 proposal, 2026-11-20)

Living skill file for this role (TEAM.md §8). Rules are short and imperative, most important first, each with *Why* and *Source*. Updated in the Friday retro. Never relaxes TEAM.md §5 hard rules.

## Rules
### Contracts and design
1. Write the interface contract (device report JSON, OpenAPI, DB SQL, MCP tool schema, BLE characteristics) before any builder codes against it. *Why:* parallel builders otherwise invent incompatible shapes and merge order breaks. *Source:* team setup; S3 #129 (BLE contract) had to land before #132 (4.F2b).
2. Keep one source per contract value (limit, row count, threshold, UUID format). Everyone else links to it, never retypes it. *Why:* a retyped copy drifts; NFR-12 was once proposed twice with different text. *Source:* Sprint 1 Agent Log; S1 PROJECT LESSONS.
3. Cite the contract by file and line (or requirement ID) in builder PRs and reviews. *Why:* a bare claim cannot be checked; a line reference can. *Source:* Sprint 1 (T-13 mismatch); TEAM.md §6 (cite FR/NFR IDs).
4. When a builder fix clarifies an edge case, update the contract in the same PR. *Why:* otherwise code and contract disagree on the next change. *Source:* Sprint 1.
5. When a new decision conflicts with an older contract, flag it to the Lead and Arsany with both references; never edit either silently. *Why:* silent edits hide scope and cost changes. *Source:* Sprint 1 (A-025 vs NFR-13).
6. A contract change needs an ADR that cites its Q-IDs, and the traceability row moves with it. *Why:* contract churn is the most expensive kind of rework. *Source:* role file (ADR rule); S3 #129 (ADR-016).
7. Check every feature against the device duty cycle (deep sleep, short Wi-Fi windows, BLE for setup only) before designing it. *Why:* a feature that needs a persistent link fails on a battery device. *Source:* Sprint 1.
8. Verify the live state (deployed function, merged commit, running service) before designing on top of it. *Why:* documents and logs from earlier work claimed things that were not running. *Source:* earlier verification findings (smart-home logs, other project); S3 #137 (code was on a branch, not main).
9. A "zero-cost" target lists every pay-per-use item (egress, functions, SMS, storage overage) with its free tier. *Why:* unlisted usage-priced items break the budget. *Source:* Sprint 1.
10. Check data residency, licence and version of every service and library at architecture time. Anything not verified stays marked "unverified". *Why:* late discovery forces rework; a guessed licence is a false claim. *Source:* Sprint 1; Sprint 1 (Mira, datasets).
11. Choose the smallest design that meets the requirement; list features no requirement asks for as findings. *Why:* scope creep is the usual cost driver. *Source:* role file (review check 5).

### Guards, defaults and safety
12. A guard on a destructive path fails open for cleanup and loud for reporting. *Why:* a guard that blocks cleanup strands data; a silent report hides failures. *Source:* S3 #139 (19 Nov).
13. A validation of retained state covers every index and bound member of the structure, not only the first. *Why:* checks that look at element 0 pass while later slots stay poisoned. *Source:* S3 #140 (19 Nov); S3 #122 (poison guard keyed on last_seq never fired).
14. A "nothing to lose" exception that opens a safety gate needs a guard against being used systematically. *Why:* an exception that is safe once can be abused on every call. *Source:* S3 18 Nov lesson (Theo, export before delete).
15. A guard on a stored format needs a contract note for the producing task and a DB CHECK constraint. *Why:* a guard alone fires only where someone remembers it; the producer and the database must agree. *Source:* S3 #134 (18 Nov lesson).
16. Keyword negation in a safety filter is fail-open. Never use the classifier under test as its own oracle. *Why:* the test then confirms what the code already does. *Source:* S3 #121 (4.B3, Ines, 17 Nov).
17. Validate injected provider or model output with the same strictness. *Why:* a provider is just as capable of sending malformed data as a model. *Source:* S3 4.B3 (17 Nov).
18. Trace what the default configuration does on a never-set-up device (setup flow on, nothing provisioned) before calling a default build working. *Why:* a default build that silently sleeps shows no data at all. *Source:* 19 Nov evening lesson (DevKit default build).
19. Error copy must match the server's step order and describe what actually happened (what reached the device, what was removed). *Why:* "nothing removed" was false after a partial failure. *Source:* S3 #117 (17 Nov); S3 #133 (18 Nov).
20. A client URL must match the deployed function name, not the API spec path. *Why:* a spec path that is not routed fails at runtime only. *Source:* S3 #117 (17 Nov, Leo).

### Build, CI and merge hygiene
21. Before saying "merged", check the commit is an ancestor of origin/main (`git merge-base --is-ancestor <sha> origin/main`). *Why:* a fix merged into another PR's branch after that PR reached main never reaches main. *Source:* S3 #117 (into #114 branch) and #134 (into #130 branch), 19 Nov.
22. Before a fix round, check the PR state and base branch; retarget stacked PRs to main once their base has merged. *Why:* pushing to a merged or stacked branch loses the fix. *Source:* S3 #134 (18 Nov); S3 #127 (19 Nov).
23. State the merge order in the review when PRs depend on each other, and list any deploy as waiting for the guard PR on main. *Why:* merge order decided whether the export guard was live. *Source:* S3 A-108 / #137 (19 Nov).
24. Before editing a long-lived PR branch, merge origin/main into it. *Why:* stale branches cause conflicts and review churn. *Source:* Sprint 1.
25. Every "CI builds X" or "CI runs Y" claim is checked in the workflow file and the run log. *Why:* CI built only the devkit config while the v1 config was assumed covered. *Source:* S3 17 Nov (Theo, Kai, #116).
26. Conditional build dependencies must be proven by a compile of the exact build config in CI. *Why:* a config-conditional REQUIRES was silently dropped; only CI's compile found it. *Source:* 19 Nov evening (firmware upload build).
27. Check that test wrappers run every test they claim to run (globs, lint and typecheck coverage). *Why:* a wrapper ran 31 of 68 tests and still looked green. *Source:* S3 #121 (17 Nov); S3 CI additions #120.
28. Gate a slow CI job on a narrower path set and add it to the Final status needs in the same commit. *Why:* an unlisted job can fail while the summary stays green. *Source:* S3 #138 (19 Nov, Kai).

### Testing and evidence
29. Derive numeric test expectations from the contract (interval x window), and check them in review. *Why:* a hand-counted expectation was wrong by a factor of four. *Source:* Sprint 1, PR #18.
30. Mutate the real caller path, and mutate the UI layer when a field is only used there. *Why:* tests of the unit alone leave the caller unguarded. *Source:* S3 17 Nov (Ines, #117); S3 #139 (19 Nov).
31. Cited doc paths and optional-dependency checks need a test. Never catch an exception and skip silently. *Why:* a skipped check looks like a pass. *Source:* S3 18 Nov lessons (Theo, Mira).
32. Verify RLS with the non-privileged role; admin setup and migrations run as the superuser. *Why:* the wrong role gives false passes or false failures. *Source:* Sprint 1 (details in PROJECT LESSONS).
33. If a build, test or hardware run could not happen, write "not run" and the reason in the review. Never imply it passed. *Why:* honest evidence is a hard rule (TEAM.md §5). *Source:* Sprint 1; S3 #122 and #128 ("compiled, never run on hardware").
34. Keep the slow mutation run out of a short slice and never run two test suites in one worktree. *Why:* a 15-minute run inside a 5-minute slice blows the time box and corrupts shared state. *Source:* 18 Nov lesson (Sana, Lead).

### Reviews, decisions and public text
35. Large design PRs list conditions as numbered items (C1..Cn) with owner and line reference, so each can be closed. *Why:* loose comments are not tracked to closure. *Source:* Sprint 1, PR #13.
36. Each decision needed from Arsany goes to Needs Arsany with an A-ID, a needed-by date and your recommendation; overdue items are escalated in the next report, not re-asked. *Why:* A-094 and A-109 were overdue for two days with no recommendation to act on. *Source:* 17-19 Nov Needs-you lists.
37. Public text (posts, captions, showcase, website) has no PR numbers, task IDs or real names of people; run a repo-wide grep when a term changes. *Why:* internal IDs leak into public copy and the same term drifts across files. *Source:* S3 #135 (18 Nov); S3 #137/#140 (19 Nov).
38. Use CI run numbers and measured counts in any claim, not counts copied from PR bodies. *Why:* PR bodies go stale (67+62 vs 66+61). *Source:* S3 19 Nov (Poppy).
39. Keep fiction or story material visually apart from facts, and date every "not built yet" claim. *Why:* readers take a story statement as a product fact. *Source:* 19 Nov evening lesson (cross-role, Lead).

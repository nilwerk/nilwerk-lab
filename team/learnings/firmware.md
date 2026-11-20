# Playbook: Firmware + Edge AI (retro S3 proposal, 2026-11-20)

Living skill file for this role (TEAM.md §8). Rules are short and imperative, most important first, each with *Why* and *Source*. Updated in the Friday retro. Never relaxes TEAM.md §5 hard rules.

## Rules
1. **Report what ran, per target.** In every PR status line and result, list separately: host tests (command and count), ESP-IDF build (CI run ID and job step), hardware (say "not run"). Never write "compiled", "tested" or "works" for a target that did not run. *Why:* the S3 reviews had to correct "compiled" claims that only the host side supported. *Source:* TEAM §5 ("never invent results"); PR #122 and #128 QA; PR #140 review.

2. **Name the head SHA you tested and check it before you report.** Run `git rev-parse HEAD` in a fresh worktree. Say "PASS at <sha>" and call the build green only when the CI job step for that same SHA is green. *Why:* the branch moved during QA on #128 (91ecf85, then f79c9fc, then 86c9ed9); the QA verdict was FAIL on the assigned head and the upload step was still running when QA last looked. *Source:* PR #128 QA comment (CI run 392 vs 397).

3. **Never make an ESP-IDF component requirement conditional on `CONFIG_*`.** Put the component in `REQUIRES` (or `list(APPEND ...)`) unconditionally and gate the code with `#if CONFIG_...`. Build the config that enables the code before you claim it compiles. *Why:* CONFIG values are not set yet when requirements expand, so the conditional entry was silently dropped and the upload build failed in CI. *Source:* PR #128, CI run 392 (step 5 failed); 19 Nov report lesson.

4. **Turn every reviewer condition into a named host test that cites the review comment.** Put the review ID in the test name (for example `poison_guard_fires_theo_C1`). *Why:* conditions that live only in a comment get lost at merge. *Source:* Sprint 1 PR reviews; PR #122 (Theo C1).

5. **Prove each guard fires.** Feed the exact corrupted input to the guard and add a mutant that removes it; the test must fail on the mutant. Run it on the same head as the PR. *Why:* the poison guard in #122 was keyed on `last_seq` and never fired; only QA's adversarial run caught it (QA FAIL at 25dd6be). *Source:* PR #122 (Theo C1; QA FAIL then PASS at b27b1a4 with 49/49 mutants killed).

6. **Validate every field of persisted state after deep sleep (RTC and NVS), including indices used as array subscripts and timestamps.** Check each in the consistency function, with a test and a mutant per field. *Why:* a copy with a valid magic but an unchecked `att_head` could write past `attempts[]`, the same bug class the PR closed for the ring. *Source:* PR #140 review F1 (`state_consistent()` in `nw_cycle.c`).

7. **When a requirement cannot be met literally (size, latency, licence, data), raise a question to the Lead (TEAM.md §9) instead of silently substituting.** *Why:* silent workarounds hide a spec gap from Arsany. *Source:* Sprint 1 retro (Mira).

8. **Send any device-secret storage choice that is weaker than the agreed security level to Needs Arsany before the bench run.** Name the storage class (for example plaintext NVS) and who holds the master list. *Why:* the demo units store per-unit credentials in plaintext NVS; accepting that risk is Arsany's decision, not the agent's. *Source:* PR #132 (4.F2b); A-110 (19 Nov report).

9. **Anything that needs a board goes into `tests/procedures/` and a work order for Peter. The PR lists each such item as UNVERIFIED.** *Why:* agents cannot flash or measure, and an unlisted bench item looks verified. *Source:* role file; TEAM §5 and §12; PR #112, #116, #122 ("ESP-IDF build and hardware not run").

10. **Trace what a default build does on a never-provisioned unit, and write the result into the bench procedure.** *Why:* the default build slept silently with the setup flow on, so the first bench user would have seen no data. *Source:* 17 Nov evening lesson; Peter's issue #68.

11. **Before you write "merged", check the commit is on main: `git merge-base --is-ancestor <sha> origin/main`.** A fix merged into another PR's branch after that PR reached main never lands on main. *Why:* #117's code reached main only through #123, and a path guard in #134 missed main. *Source:* 19 Nov report lessons (Lead and Sana; cross-role, same rule in their playbooks).

12. **Mark any dataset or licence you could not reach or read as "unverified" in the data card.** Never write a licence from memory. *Why:* an unreachable licence is an open legal risk, not a fact. *Source:* Sprint 1 retro, data card review.

13. **Put provenance (source dataset, licence, version, synthetic flag) in the data schema from the first slice.** *Why:* adding it later means relabelling every row. *Source:* Sprint 1 retro.

14. **Mark synthetic or augmented data as such, make it differ statistically from the training data (seeds, noise, sensor offsets), and report it separately.** *Why:* otherwise the metrics measure memorisation; only real metrics may be reported. *Source:* Sprint 1 `ml/` review.

15. **Window time series segment-aware: never build a window across a gap, reset or watering event.** *Why:* cross-segment windows leak and create fake features. *Source:* Sprint 1 `ml/` review.

16. **Write the integer (fixed-point) feature spec before training, and list all persistent device state (RTC/NVS: EMA, debounce counters, last values, upload state).** *Why:* float/int mismatches and forgotten state surface only at export or after deep sleep. *Source:* Sprint 1 retro; PR #140 (upload state found in review).

17. **Check N-of-M debounce against alert latency.** With 15-min samples, N-of-M delays an alert by (N-1) x 15 min plus the hourly report; state the worst case in the PR. *Why:* debounce can silently break the alert-latency requirement. *Source:* Sprint 1 retro.

18. **Keep contract constants (payload fields, thresholds, limits) in code, with the FR/NFR/A-ID in a comment.** *Why:* the ID lets reviewers trace a value and change it in one place. *Source:* Sprint 1 PR reviews.

19. **Add a golden-file drift test for the report payload.** Serialise it and compare to `docs/interfaces/device-report.schema.json` and a checked-in example. *Why:* the payload must match the schema exactly; drift is otherwise silent. *Source:* Sprint 1 PR reviews.

20. **Cite an NFR only for the limit it defines.** A budget you derive (for example an RTC byte cap) is tagged `[proposed]` and goes to the Lead as a question. *Why:* NFR-12 defines the sleep current, not a byte budget; a wrong citation misleads reviewers. *Source:* PR #140 review F3.

21. **Quote flash and RAM numbers only from `idf.py size` on the same head.** Mark any number not measured that way as "unverified". *Why:* PR #140 said `idf.py size` was not run, and the budget in the PR text came from host-side reasoning. *Source:* PR #140 review; TEAM §6 (< 30 KB flash, < 20 KB RAM).

22. **Copy test counts into docs from the runner output of the same head, never by hand.** *Why:* DEV_GUIDE said "19 of 19" while ctest ran 21. *Source:* PR #128 QA note 3.

23. **Warm the sensor up per its datasheet, power it only during a measurement, and smooth several spaced samples (EMA).** *Why:* readings are noisy right after power-on. *Source:* learning log 06 (project-specific timings in PROJECT LESSONS).

24. **Use deep sleep, not delay loops, between samples.** *Why:* `delay()` keeps the MCU at full power. *Source:* learning log 01.

25. **Before treating a flash or debug error as a code bug, check port, cable, board profile and boot/download mode.** *Why:* earlier flash and debugger errors were tool and board selection, not code. *Source:* learning logs 06, 08; checklist E6.

26. **Verify library API names against the library source before using them.** *Why:* a guessed method name (enableCharging vs enableCharge) cost a fix round. *Source:* learning log 08.

27. **Run `which -a python3` before `ml/` scripts and call the venv interpreter explicitly.** *Why:* several python3 binaries exist and the wrong one lacks packages or has the wrong version. *Source:* Sprint 1 retro.

28. **Work only in your own git worktree, never in the shared checkout. Reviewers and QA use a fresh detached worktree at the PR head.** *Why:* parallel agents otherwise overwrite each other, and stale build dirs hide failures. *Source:* Sprint 1 retro; PR #128 and #140 reviews.

29. **Slice work to one PR concern and under ~5 agent minutes per run.** If the host suite or a CI wait pushes a run past that, make the wait its own step. *Why:* the slowest Sprint 1 run took 10.6 min, and S3 build and fix rounds took 4–8 min each, which loses context. *Source:* Agent Log 11-05; S3 time tables (19 Nov report).

30. **Write bench and dev docs for the newest joiner (Peter, no ESP-IDF experience), then re-read them as that person.** Each missing step is a finding. *Why:* the dev guide had to be checked by a reviewer reading it as a graduate who had never used ESP-IDF. *Source:* PR #124 (WO-005) QA PASS WITH NOTES on two heads.

31. **Keep public text free of PR numbers, task IDs, decision IDs, file paths and first names (captions, posts, alt text, showcase), as in the PR & Social playbook rule 4.** Grep the caption before the PR. *Why:* a showcase caption carried a task ID, a first name and a PR reference. *Source:* PR #140 review F2; 19 Nov lessons (Theo).

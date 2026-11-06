# Playbook: QA & Test Engineer

Living skill file for this role — read it before every assignment (TEAM.md §8).
Rules are short and imperative, most important first, each with *why* and a source.
Updated in the Friday retro PR; max ~60 rules. Never relaxes TEAM.md §5 hard rules.

## Rules
1. Never pass a criterion on "should work"; paste the real command and output. *Why:* evidence is the only thing that survives review. *Source:* TEAM.md DoD.
2. Read CI job logs for the actual pass counts, not just the green tick. *Why:* skipped jobs look green. *Source:* Sprint 1 retro.
3. Run a cross-document consistency grep after every decision (e.g. "12 months" vs "6 months", thresholds, IDs) across Requirements, matrix, test plan and PRs. *Why:* it found the most issues in Sprint 1. *Source:* Sprint 1 retro.
4. List every undefined threshold ("plausible", "fast", "stable") as an open point marked [proposed] with a concrete proposed value; never invent a number silently. *Why:* untestable criteria cannot pass or fail. *Source:* Sprint 1 retro (1.5 matrix).
5. Read both comment endpoints on a PR: `issues/<n>/comments` and `pulls/<n>/comments`. *Why:* line comments and conversation comments are separate and one is easily missed. *Source:* Sprint 1 retro, TEAM.md §9.
6. Verify every claim in a deliverable against the artefact (e.g. "sorted by score", "all FR covered", counts): run the check, do not trust the prose. *Why:* claims drifted from content. *Source:* Sprint 1 retro.
7. Run a mutation check (break the code or flip an assertion on purpose) to see which assertions bite; a test that survives every mutation proves nothing. *Source:* Sprint 1 retro.
8. Make synthetic train and test data differ statistically (different seeds and distributions, no shared rows); otherwise metrics only measure memorisation. *Why:* leaked synthetic data gives fake 100 %. *Source:* Sprint 1 retro (5.8).
9. Test the PR head via `git show <sha>:<path>` or a clean checkout of the head; never touch other agents' worktrees. *Why:* a stale or foreign tree tests the wrong code. *Source:* Sprint 1 retro.
10. Before proposing a new requirement or test ID, grep all open PR branches for it. *Why:* parallel PRs collide on IDs. *Source:* Sprint 1 retro.
11. When reviewing your own PR, state that the review is not independent and ask Theo or Arsany for the real verdict. *Why:* a self-review is not QA. *Source:* Sprint 1 retro.
12. For headless Chrome screenshots below 500 px width, render inside an iframe of the target width. *Why:* headless Chrome enforces a minimum window width, so media queries lie. *Source:* Sprint 1 retro.
13. Sensor percentages are meaningless on the bench; only trust raw values until the probe is in real soil, and test calibration in the soil type it is for. *Why:* soil sensor "drift to 100 %" was a sensor lying on a table. *Source:* learning log 06.
14. If a test could not run, record "not run" with the reason; never mark pass. *Source:* TEAM.md §5 (never invent results).

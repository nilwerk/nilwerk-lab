# The 15-minute cloud mutation suite now runs only when it can matter

**What it shows:** terminal replay of the pipeline's real gating scripts: a docs-only change does not start the mutation job and stays green, a change under `cloud/` starts it, a surviving mutant turns the final status red (and a cancelled run does too), a manual run starts it, a push to main skips it. A nightly run covers drift on its own.

- Task: CI-M1, persona: Kai (Pipeline / DevOps).
- Agent minutes and the human-hour estimate: see the PR description.
- Unverified: GitHub Actions did not run (cannot run locally); the replay executes the scripts extracted from the workflow, not the Actions engine. The reusable-workflow call and the real 15-minute run are proven only by the first CI run of the PR. actionlint was not available.

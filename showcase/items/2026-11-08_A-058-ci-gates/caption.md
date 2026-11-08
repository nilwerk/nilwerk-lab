# A-058: two CI gates that never matched now match

**Shows:** the `cloud` job (Deno lint + typecheck of the Supabase edge functions) and the `sim` job (ngspice via `ldo_dropout.py`) now switch on, because their detect gates look for the files the repo really has (`cloud/supabase/functions/*/index.ts`, `pcb/sim/*.py`) instead of `cloud/package.json` and `*.cir`.
**Task:** A-058 · persona: Kai (Pipeline / DevOps) · PR: see PR list (branch `agent/devops/ci-gates`)
**Agent minutes:** about 25 (measured start 18:53 Berlin; see the result of the run) · **my human estimate:** 3 h (find the gaps, verify Deno locally, rewrite two jobs, read CI, plus the 2-option firmware-in-the-loop note)
**Evidence:** `deno lint` and `deno check` exit 0 locally (Deno 2.1.4); `ldo_dropout.py` exit 0 locally; CI run of the PR branch is linked in the PR.
**Unverified:** the Deno jobs on a GitHub runner until the CI run is read; the QEMU and HIL options in `docs/ci-firmware-in-the-loop.md` are a design, nothing of it was run.

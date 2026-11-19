# CI: full cloud mutation suite

The two mutation scripts (`cloud/test/mutation.sh`, 62 mutants; `cloud/tips/test/mutation.sh`, 67 mutants) take about 15 minutes together, so they do not run on every PR. They live in `.github/workflows/cloud-mutation.yml` (one job, throw-away Postgres 16 service, no secrets, 40 min timeout). A surviving mutant makes the script exit 1 and the job red.

## When it runs
| Trigger | Runs? | Counts in `Final status`? |
|---|---|---|
| `pull_request` changing `projects/plant-monitor/cloud/**` | yes (job `cloud-mutation` in `ci.yml`, calls the workflow) | yes |
| `pull_request` changing `ci.yml`, `cloud-mutation.yml`, `.tool-versions`, `.github/actions/` | yes (shared build config, `detect` sets ALL) | yes |
| `pull_request` that touches neither (docs-only, firmware-only, ...) | no, job skipped | skipped = fine |
| push to `main` | no (the PR already ran it) | skipped = fine |
| nightly `schedule` (02:17 UTC, default branch) | yes, standalone run | no (own workflow run, red in the Actions list) |
| manual `workflow_dispatch` of "Cloud mutation suite" | yes, standalone | no |
| manual `workflow_dispatch` of "CI" | yes (ALL) | yes |

Contract-doc-only changes (`docs/interfaces`, `docs/adr`) re-run `cloud` and `cloud-db` but not the mutation suite: `cloudmut` is gated on `cloud/` only, on purpose.

## Gating in `Final status`
`summary` lists `cloud-mutation` in `needs` and treats `failure` or `cancelled` as red; `skipped` and `success` are green. A reusable-workflow job that is skipped by its `if` reports `skipped`. `detect` must still succeed.

## Required-check note
If branch protection requires `Final status`, nothing to change. Do not require the inner job name (`cloud-mutation / mutation`): on docs-only PRs it never exists. A red nightly is not a PR check; someone has to look at the Actions list (GitHub emails the person who last edited the cron line, which is not a team alert). Recommendation for Arsany: decide who watches the nightly.

## Verification status
YAML parsed (PyYAML); actionlint not available in the sandbox. The `detect` and `Final status` scripts were replayed locally (`showcase/items/2026-11-19_CI-M1/gating-replay.txt`). GitHub Actions itself, the reusable-workflow call and the real 15-minute run were not run here: first proof is the CI run of this PR (cloud/ is untouched, so the job should show as skipped unless ci.yml's change turns ALL on, which it does: expect one real mutation run on this PR).

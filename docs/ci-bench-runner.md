# Bench runner (self-hosted GitHub Actions)

## What it is
A self-hosted GitHub Actions runner on the bench Raspberry Pi. It runs the hardware-near
checks (the end-to-end bench setup) that GitHub-hosted runners cannot do.

- Runner name: `plant-bench-pi`
- Label: `bench` (jobs use `runs-on: [self-hosted, bench]`)
- Hardware: 32-bit Raspberry Pi (`armv7l`)
- Workflow: `.github/workflows/bench.yml`

## Trigger rules and why
The runner executes whatever code a job checks out. On a private repo that is safe only
while untrusted code cannot reach it. So `bench.yml` allows only:

- `schedule`: nightly at 02:00 UTC, on `main`.
- `workflow_dispatch`: manual runs, and the job runs only when the ref is `refs/heads/main`.

Never add `pull_request`, `pull_request_target`, `push` or `issue_comment` to a bench
workflow. Those let a pull request, a fork or a comment run code on the Pi.

## Node workaround
The runner's service uses a symlinked `node20` folder instead of the Node version the runner
would otherwise pick (node24). This is a workaround, not the intended setup.
After every runner update, check again:

1. `node --version` in the runner's environment still answers.
2. The `bench` smoke step in a manual run prints the expected Node version.
3. If the runner reports a new Node requirement, remove or update the symlink first.

## Triggering a manual run
1. Open the repository on GitHub and go to **Actions**.
2. Pick **Bench (self-hosted)** in the left list.
3. Click **Run workflow**, set the branch to **main**, and confirm.
4. Watch the job on the runner `plant-bench-pi`. A run from any other branch does nothing.

## Current state
The smoke step (host, architecture, Node, adb) runs. The E2E step prints
"bench E2E not yet configured" until `bench/run_e2e.sh` exists on `main`.

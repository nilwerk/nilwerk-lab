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
This is a workaround, not the intended setup.

- **Expected Node:** major version 20. `node --version` must print `v20.x.y`; the patch
  number is whatever the Node 20 install on the Pi provides. The workflow reads the expected
  major from `EXPECTED_NODE_MAJOR` in `.github/workflows/bench.yml`.
- **Why:** the runner would otherwise pick node24 for its service. The service instead uses a
  `node20` folder that is symlinked to a Node 20 install.
- **Symlink:** `<runner-root>/externals/node20` is a symlink whose target is the Node 20 install
  directory on the Pi. The real local paths are set on the Pi and are not kept in this repo;
  the owner of the Pi checks them there.
- **Smoke check:** the `Runner smoke check` step in `bench.yml` FAILS if `node` is not on PATH
  or if its major version is not `EXPECTED_NODE_MAJOR`. A green run therefore means Node 20 was present.

After every runner update, check again:

1. `node --version` in the runner's environment prints `v20.x.y`.
2. A manual run's `Runner smoke check` step passes and prints the same version.
3. If the runner reports a new Node requirement, follow "Removing the workaround" first.

### Removing the workaround
1. Stop the runner service.
2. Remove only the symlink `<runner-root>/externals/node20` (the link itself; the target directory stays).
3. Confirm the Node major the runner now needs, and set `EXPECTED_NODE_MAJOR` in
   `bench.yml` to that major in the same commit as this doc change.
4. Start the service and run **Bench (self-hosted)** manually from `main`. The smoke step must pass.

## Triggering a manual run
1. Open the repository on GitHub and go to **Actions**.
2. Pick **Bench (self-hosted)** in the left list.
3. Click **Run workflow**, set the branch to **main**, and confirm.
4. Watch the job on the runner `plant-bench-pi`. A run from any other branch does nothing.

## Current state
The smoke step (host, architecture, Node, adb) runs and FAILS if Node is missing or is not
major 20. The E2E step FAILS with "bench E2E not configured: nothing tested" until
`bench/run_e2e.sh` exists on `main`. A green run therefore always means something was tested.

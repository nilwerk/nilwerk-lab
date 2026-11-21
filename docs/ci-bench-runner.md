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
- `workflow_dispatch`: manual runs. The job runs only when the ref is `refs/heads/main`
  or `refs/heads/agent/devops/bench-workflow`. Any other ref runs nothing.

The branch `agent/devops/bench-workflow` is allowed by the owner's decision of 21 Nov 2026
(the owner): it is for the one PR that adds the hardware steps, and nothing else may run on the
Pi. Remove that branch from the guard when that PR is closed.

Never add `pull_request`, `pull_request_target`, `push` or `issue_comment` to a bench
workflow. Those let a pull request, a fork or a comment run code on the Pi.

Residual risk, two places:

- `main`: the nightly schedule runs the workflow file on `main`, so it also runs code on the Pi.
  Anyone who can push to `main` controls what runs on the Pi, nightly and on a manual run
  from `main`.
- `agent/devops/bench-workflow`: a manual run uses the workflow file on that branch. Anyone who
  can push to it can change what runs on the Pi, so only that branch's owner pushes to it.
  This branch has NO branch protection today (checked on 21 Nov 2026: the branch protection
  API returns 404, not protected). Protecting it is an open decision for the owner.
  A run from this branch or from `main` gets the bench secrets `BENCH_ANDROID_SERIAL`,
  `BENCH_APP_TEST_ACCOUNT` and `BENCH_CLOUD_CHECK_CONFIG`, so whoever can change the workflow
  file on either ref can reach them on the Pi. These secrets are the reason the bench branch
  needs protection (open decision for the owner).

## Steps of the bench job
The job runs these steps in order. Each hardware step fails closed: if its input is missing
it prints `not configured: nothing tested` and exits 1. Nothing is built on the Pi.

**Scope of the bench round (owner decision, 21 Nov 2026):** the bench round tests the
ESP32-to-app and ESP32-to-cloud communication only. Sensor values are not checked yet. The
firmware is the normal build, with no simulated-sensor firmware.

| Step | What it does | Input it needs | If missing |
|---|---|---|---|
| Runner smoke check | Host, arch, Node major, adb | none | fails |
| a. Firmware flash | Reads the chip id (must be ESP32-C3), then writes `bench/firmware/image.bin` with esptool at `BENCH_FLASH_OFFSET` (`0x0`, merged image) to the USB port `BENCH_ESP_PORT` (`/dev/ttyACM0`) | `bench/firmware/image.bin` (prebuilt, not built on the Pi), a device at the port, `esptool` on the runner | fails, no flash |
| b. Serial boot log | Reads the boot log for 20 s after a reset and asserts the first non-empty line of the expect file is in it. Boot line only. | `bench/firmware/expect.txt` | fails |
| c. BLE scan | `bluetoothctl` scan for 10 s; asserts that the first non-empty line of the expect file, with all whitespace removed, is the start of a device name seen in the scan. A name with a space in it cannot match, so a space in the bench name must be avoided, or the code changed in its own PR. Only the name field is read. The accepted line forms are `Device <MAC> <Name>`, `[NEW] Device <MAC> <Name>` and `[CHG] Device <MAC> Name: <name>`. A prompt or other text before the tag or `Device` is ignored when the line is otherwise one of these forms. On a plain or `[NEW]` line everything after the MAC is the name, so text that looks like a property, such as `RSSI: -60`, is read as a name. This is a known limit: on success the run log prints the matched name (`c. BLE: device name '...' starts with prefix ...`), and on failure it prints the last 20 raw scan lines, so a wrong match can be seen by a person. Any other `[CHG]` line (RSSI, TxPower, UUIDs, ...) is ignored, `[DEL]` lines are skipped, and the MAC never matches. That is the only check. | `bench/ble/expect.txt`, `bluetoothctl` | fails |
| d. App flow | Runs `bench/app/run_appium.sh` on the phone (Appium 2.x, UiAutomator2). The flow checks only the communication path: scan finds the device, connect, write the setup data, and the app shows the device as connected. It asserts no sensor value. Before the script runs, the step records the test start time (UTC) as `BENCH_TEST_START_UTC` for step e. | `bench/app/run_appium.sh`; secrets `BENCH_ANDROID_SERIAL` (phone id) and `BENCH_APP_TEST_ACCOUNT` (test account config); Appium 2.x on the runner | fails |
| e. Cloud check | Runs `bench/cloud/check.sh`. It checks only that the device communicated with the cloud: at least one row from this device exists in the EU project and was received after `BENCH_TEST_START_UTC`. It does not read, print or compare any reading value. | `bench/cloud/check.sh`; secret `BENCH_CLOUD_CHECK_CONFIG`; `BENCH_TEST_START_UTC` from step d | fails |
| Bench E2E | Runs `bench/run_e2e.sh` | `bench/run_e2e.sh` | fails |

Steps a to c need no secrets. Secrets are referenced by name only in the workflow; their values
live in the repository's Actions secrets and are never written to the repo. The `bench/` input
files are not in the repo yet and must come from the owner or the hardware work.

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
3. Click **Run workflow**, set the branch to **main** (or to `agent/devops/bench-workflow` for
   the PR branch only), and confirm.
4. Watch the job on the runner `plant-bench-pi`. A run from any other branch does nothing.

Manual run from the PR branch, in the order the owner allowed it:
1. Push the branch (fast-forward only) and check the head sha on GitHub.
2. Make sure `bench/firmware/image.bin` (and the other inputs) exist on the branch, or the
   steps stop with `not configured: nothing tested`. The inputs are not added by this PR.
3. Run the workflow from `agent/devops/bench-workflow` as above. Read each step's output.
4. A green run from this branch proves only the steps that ran. A red run names the first step
   that failed and the input it is missing.

## Current state
- The smoke step (host, architecture, Node, adb) runs and FAILS if Node is missing or is not
  major 20.
- Steps a to e fail closed until their inputs exist (see the table above). Today none of the
  `bench/` inputs are in the repo, so a manual run stops at step a with
  `not configured: nothing tested`.
- The E2E step FAILS with "bench E2E not configured: nothing tested" until `bench/run_e2e.sh`
  exists on `main`. A green run therefore always means something was tested.

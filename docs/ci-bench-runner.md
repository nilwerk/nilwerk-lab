# Bench runner (self-hosted GitHub Actions)

## What it is
A self-hosted GitHub Actions runner on the bench Raspberry Pi. It runs the hardware-near
checks (the end-to-end bench setup) that GitHub-hosted runners cannot do.

- Runner name: `plant-bench-pi`
- Label: `bench` (jobs use `runs-on: [self-hosted, bench]`)
- Hardware: 32-bit Raspberry Pi (`armv7l`)
- Workflow: `.github/workflows/bench.yml`

**Supersedes** the hardware-in-the-loop design in `projects/plant-monitor/docs/ci-firmware-in-the-loop.md`
(option b: `hil.yml`, label `esp32c3-bench`, GitHub Environment `bench` as the approval gate). This design uses
`bench.yml`, label `bench`, and **no Environment gate** (the owner declined it). `hil.yml` and `esp32c3-bench` are not used.

**Label check:** the label in this doc and in `bench.yml` (`runs-on: [self-hosted, bench]`) is `bench`. The label on the
Pi is confirmed (C1, closed): the runner `plant-bench-pi` is Idle with label `bench` (Pi setup comment on PR #156, 22 Nov 2026).

**Requirements:** the bench round touches FR-D03, FR-A03, NFR-04, NFR-06 and NFR-07 (rows in
`projects/plant-monitor/tests/acceptance-matrix.md`). It covers the communication path only and does not pass those
rows. The mapping to steps is in the header of `bench.yml`.

## Trigger rules and why
The runner executes whatever code a job checks out. On a private repo that is safe only
while untrusted code cannot reach it. So `bench.yml` allows only:

- `workflow_dispatch`: **manual runs only** (owner decision, 22 Nov 2026: manual trigger only). There is no schedule.
  The job runs only when the ref is `refs/heads/main` or `refs/heads/agent/devops/bench-workflow`.
  Any other ref runs nothing.

**Trigger the bench chain (after this PR is merged):** GitHub > **Actions** > **bench (self-hosted)** >
**Run workflow** > branch **main** > Run. The workflow file is on `main` only after the merge, so before that
the `main` branch is not offered; the PR branch is used only for the PR's own test runs (see below).

**Why no schedule:** if a schedule were added, it would run the workflow file on `main` every night, and
steps 1 to 4, d and e would then run unattended on the Pi with the bench secrets. That would be a new owner
decision, not a config change.

The branch `agent/devops/bench-workflow` is allowed by the owner's decision of 21 Nov 2026
(the owner): it is for the one PR that adds the hardware steps, and nothing else may run on the
Pi. Remove that branch from the guard when that PR is closed.

Never add `pull_request`, `pull_request_target`, `push` or `issue_comment` to a bench
workflow. Those let a pull request, a fork or a comment run code on the Pi.

Residual risk, two places:

- `main`: a manual run from `main` runs the workflow file on `main` on the Pi. Anyone who can push to `main`
  controls what runs on the Pi on that run.
- `agent/devops/bench-workflow`: a manual run uses the workflow file on that branch. Anyone who
  can push to it can change what runs on the Pi, so only that branch's owner pushes to it.
  This branch has NO branch protection today (checked on 21 Nov 2026: the branch protection
  API returns 404, not protected). Protecting it is an open decision for the owner.
  A run from this branch or from `main` gets the bench secrets `BENCH_ANDROID_SERIAL`,
  `BENCH_TEST_EMAIL`, `BENCH_TEST_EMAIL_PASSWORD`, `BENCH_CLOUD_CHECK_CONFIG`, `BENCH_BOARD_POP`, `BENCH_WIFI_SSID`
  and `BENCH_WIFI_PASSWORD`, so whoever can change the workflow file on either ref can reach
  them on the Pi. **Owner decision (22 Nov 2026): the bench branch can read these secrets.** The
  owner accepted this for the bench round. Protecting the branch stays an open decision.
- The bench job reads the provisioning folder on the Pi (`$HOME/nilwerk-secrets/provision-out/`,
  or `BENCH_PROVISION_DIR`). It is local to the Pi and never leaves it. Owner decision, 22 Nov 2026.

## Steps of the bench job
The job runs these steps in order. Each hardware step fails closed: if its input is missing
it prints `not configured: nothing tested` and exits 1. Nothing is built on the Pi.

**Scope of the bench round (owner decision, 21 Nov 2026):** the bench round tests the
ESP32-to-app and ESP32-to-cloud communication only. Sensor values are not checked yet. The
firmware is the normal build, with no simulated-sensor firmware.

| Step | What it does | Input it needs | If missing |
|---|---|---|---|
| Runner smoke check | Host, arch, Node major, adb | none | Node missing or wrong major: fails. adb: printed only, not checked |
| a. Firmware flash | Reads the chip id (must be ESP32-C3), then writes `bench/firmware/image.bin` with esptool at `BENCH_FLASH_OFFSET` (`0x0`, merged image) to the USB port `BENCH_ESP_PORT` (`/dev/ttyACM0`) | `bench/firmware/image.bin` (prebuilt, not built on the Pi), a device at the port, `esptool` on the runner | fails, no flash |
| b. Serial boot log | Reads the boot log for 20 s after a reset and asserts the first non-empty line of the expect file is in it. Boot line only. | `bench/firmware/expect.txt` | fails |
| c. BLE scan | `bluetoothctl` scan for 10 s; asserts that the first non-empty line of the expect file, with all whitespace removed, is the start of a device name seen in the scan. The expected name must have no spaces: all whitespace is removed from it before matching, and it matches the START of the device name, so a longer device name also matches (expected `Bench` matches `Bench Dev`). Only the name field is read. The accepted line forms are `Device <MAC> <Name>`, `[NEW] Device <MAC> <Name>` and `[CHG] Device <MAC> Name: <name>`. A prompt or other text before the tag or `Device` is ignored when the line is otherwise one of these forms. On a plain or `[NEW]` line everything after the MAC is the name, so text that looks like a property, such as `RSSI: -60`, is read as a name. This is a known limit: on success the run log prints the matched name (`c. BLE: device name '...' starts with prefix ...`), and on failure it prints the last 20 raw scan lines, so a wrong match can be seen by a person. Any other `[CHG]` line (RSSI, TxPower, UUIDs, ...) is ignored, `[DEL]` lines are skipped, and the MAC never matches. That is the only check. | `bench/ble/expect.txt`, `bluetoothctl` | fails |
| 1. App APK | Downloads the newest successful `app-apk` artifact from `main` (`plant-monitor-app-debug-<sha>`, the run of `app-apk.yml`) with the workflow token. Saved to `bench-artifacts/app-apk/` in the runner workspace only. Not committed, not uploaded. | Job permission `actions: read`; a successful app-apk run on `main` | fails: `APK not found` |
| 2. Firmware image | Downloads the artifact `plant-monitor-firmware-setup` from the newest successful run of the CI workflow `.github/workflows/ci.yml` on `main` that has that artifact. The artifact is uploaded by the `firmware` job of `ci.yml`, step "Upload setup firmware artifact", only for pushes to `main` and same-repo PRs (fork PRs skip it), and only in runs where that job ran. The artifact is a folder: `build-setup/` with the `.bin` files and `flasher_args.json`. The whole folder is extracted to `bench-artifacts/firmware/build-setup/` (the path step 3 reads). Fails closed if `build-setup/flasher_args.json` is missing. Logs the commit sha of that firmware run (`2. firmware: ... commit <sha>`); step 1 logs the commit sha of the APK run, so both can be traced to commits. | Job permission `actions: read`; `ci.yml` on `main` with the step "Upload setup firmware artifact" (added by PR #158, not on `main` until that PR merges), and a successful `main` run that has the artifact | fails: `firmware artifact not found` |
| 3. Provisioning and flash | Reads the board ID from the repo variable `BENCH_BOARD_HW_ID` (`nw-c8da2986f470`, not a secret). Checks that `<hw_id>.nvs.csv` and `<hw_id>.label.txt` exist in `BENCH_PROVISION_DIR` (default `$HOME/nilwerk-secrets/provision-out`) and are mode `0600`. Checks for an ESP32-C3 on `/dev/ttyACM0`. Checks that the NVS tool is exactly 0.3.0 in the Pi venv (provisional pin, lines 394-401). Reads the flash plan from the step 2 build-setup folder before any write (lines 416-477): every file in `flash_files` of `flasher_args.json` with its listed offset, and the offset and size of the single partition named `nvs` in the partition table binary of the build. It stops before any write if that `nvs` entry is missing, duplicated, or has a zero offset or size, or if any `flash_files` file overlaps it (the `nvs` lookup is lines 458-468, the overlap check lines 469-471). It builds the NVS partition from the CSV in a 0700 temp dir with the size from that entry (lines 484-491), writes each `flash_files` file at its offset in offset order (lines 493-497), and writes the NVS partition last (lines 498-500). The temp dir is removed by an EXIT trap (line 415). The label and the CSV are never printed. The label is checked but not used by the flash. | Repo variable `BENCH_BOARD_HW_ID`; the provisioning folder on the Pi with both files at `0600`; the image from step 2; `esptool`; the ESP-IDF NVS partition tool (0.3.0, provisional) | fails before any write (lines 373-414 and 416-481) |
| 4. APK install | Checks that exactly one device with the serial in secret `BENCH_ANDROID_SERIAL` is attached in state `device`, then runs `adb -s <serial> install -r` with the APK from step 1. The serial is never printed. | Secret `BENCH_ANDROID_SERIAL`; the APK from step 1; `adb` | fails, no install |
| d. App flow | Runs `bench/app/run_appium.sh` on the phone (Appium 2.x, UiAutomator2). The flow checks only the communication path: scan finds the device, connect, write the setup data, and the app shows the device as connected. It asserts no sensor value. Before the script runs, the step records the test start time (UTC) as `BENCH_TEST_START_UTC` for step e. | `bench/app/run_appium.sh`; secrets `BENCH_ANDROID_SERIAL` (phone id), `BENCH_TEST_EMAIL` and `BENCH_TEST_EMAIL_PASSWORD` (test account, passed as environment variables only); Appium 2.x on the runner | fails closed if `BENCH_TEST_EMAIL` or `BENCH_TEST_EMAIL_PASSWORD` is not set (lines 545-552); also fails if `BENCH_ANDROID_SERIAL` is not set (lines 553-556) |
| e. Cloud check | Runs `bench/cloud/check.sh`. It checks only that the device communicated with the cloud: at least one row from this device exists in the EU project and was received after `BENCH_TEST_START_UTC`. It does not read, print or compare any reading value. | `bench/cloud/check.sh`; secret `BENCH_CLOUD_CHECK_CONFIG`; `BENCH_TEST_START_UTC` from step d | fails |
| Bench E2E | Runs `bench/run_e2e.sh` | `bench/run_e2e.sh` | fails |

Steps a to c need no secrets. Steps 1 to 3 use only the workflow token and repo variables. Steps 4, d and e use the repo secrets by name only; their values
live in the repository's Actions secrets and are never written to the repo. The `bench/` input
files are not in the repo yet and must come from the owner or the hardware work.

**Version pins (fix round, 22 Nov 2026). Not run on the Pi, not run here.** esptool is pinned to **v5.x**: steps a, b and 3
run `esptool version` and fail if the major is not 5, and steps a and 3 use the v5 command name `chip-id`. This was
checked against the esptool 5.6.0 source on PyPI (`version` prints `5.6.0`; `chip-id` is the v5 command).
The ESP-IDF NVS tool is pinned to **esp-idf-nvs-partition-gen 0.3.0** from the Pi venv `~/nvs-venv` (`nvs_venv` and
`nvs_pin` in `bench.yml` lines 375-376; version check lines 394-401). The pin is **PROVISIONAL**: it is not yet checked
against the ESP-IDF v5.4 constraints file (the fetch failed from the Pi and from the Mac). The v5.4 check is open.
Step 3 fails unless the installed version is exactly 0.3.0, installs nothing from the network, and calls the tool as
`python3 -I -m esp_idf_nvs_partition_gen generate <csv> <bin> <size>`, the form the 0.3.0 package accepts.

**Scratch folder:** `bench-artifacts/` (APK and firmware of steps 1 and 2) is git-ignored and is cleared at the
start of every run.

Order (22 Nov 2026): smoke check, a, b, c, then steps 1 to 4 (download, provision and flash,
install the APK), then d and e. The provisioned board is the one that d and e test. Because a to c
run first, they test the bench image from `bench/firmware/`, not the provisioned board.

**Secrets for step d:** `BENCH_TEST_EMAIL`, `BENCH_TEST_EMAIL_PASSWORD`, `BENCH_BOARD_POP`,
`BENCH_WIFI_SSID` and `BENCH_WIFI_PASSWORD` are passed into the Appium step as environment variables
only. Step d fails closed if `BENCH_TEST_EMAIL` or `BENCH_TEST_EMAIL_PASSWORD` is missing: both must be set (lines 545-552), and they are
passed as environment variables only (lines 530-535), never echoed. The script `bench/app/run_appium.sh` must not
echo them.

**Job permission:** `permissions: actions: read` is set on the bench job only. The workflow-level
permissions stay `contents: read`.

**Repository variables** (not secrets, set by the owner, not by this PR): `BENCH_BOARD_HW_ID`
(`nw-c8da2986f470`) and optionally `BENCH_PROVISION_DIR` (default `$HOME/nilwerk-secrets/provision-out`).

**Open for steps 1 to 4 (checked on 22 Nov 2026 with stubs only):**
- Step 2 needs the step "Upload setup firmware artifact" in `.github/workflows/ci.yml` on `main`. PR #158 adds it. Until that PR merges and a successful `main` run of `ci.yml` has the artifact, the step fails. The artifact is published only for pushes to `main` and same-repo PRs; fork PRs skip it.
- Each file from step 2 is written at the offset in its `flasher_args.json`. A file that overlaps the NVS partition
  stops the run before any write (lines 469-471). NVS is written last (lines 498-500), so an earlier file cannot overwrite it.
  Check the offsets with Mira if the build layout changes.
- The ESP-IDF NVS tool must be in the venv `$HOME/nvs-venv` of the runner user, at exactly 0.3.0 (step 3 fails otherwise).
  **C4: pinned to 0.3.0, provisional; v5.4 check open.**
- The NVS offset and size are not set in this repo. Step 3 reads them from the `nvs` entry of the partition table binary in the build (lines 458-468).
  Any fixed value (the ESP-IDF default table) is only a default and must be checked against the build's table.

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
From `main`, this works only after the PR is merged (the workflow file is on `main` only then).
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
- Not run in this session: the Pi, esptool, the NVS tool, actionlint. This doc change and the workflow edit were
  checked only by a YAML parse and a shell syntax check of the edited run blocks.
- The smoke step (host, architecture, Node, adb) runs and FAILS if Node is missing or is not
  major 20.
- Steps a to e and steps 1 to 4 fail closed until their inputs exist (see the table above). Today none of the
  `bench/` inputs are in the repo, so a manual run stops at step a with
  `not configured: nothing tested`. Steps 1 to 4 need the CI artifacts and the repo variable
  `BENCH_BOARD_HW_ID` as described above.
- The E2E step FAILS with "bench E2E not configured: nothing tested" until `bench/run_e2e.sh`
  exists on `main`. A green run therefore always means something was tested.

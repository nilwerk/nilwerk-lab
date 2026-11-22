# Bench runner (self-hosted GitHub Actions)

## What it is
A self-hosted GitHub Actions runner on the bench host. It runs the hardware-near
checks (the end-to-end bench setup) that GitHub-hosted runners cannot do.

- Runner name: `plant-bench-pi`
- Label: `bench` (the bench job uses `runs-on: [self-hosted, bench]`)
- Host: Debian GNU/Linux 13 (trixie), 64-bit, arm64 (`aarch64`). See "Bench host and runner" below.
- Workflow: `.github/workflows/bench.yml`

**Supersedes** the hardware-in-the-loop design in `projects/plant-monitor/docs/ci-firmware-in-the-loop.md`
(option b: `hil.yml`, label `esp32c3-bench`, GitHub Environment `bench` as the approval gate). This design uses
`bench.yml`, label `bench`, and **no Environment gate** (the owner declined it). `hil.yml` and `esp32c3-bench` are not used.

**Label check:** the label in this doc and in `bench.yml` (`runs-on: [self-hosted, bench]`) is `bench`. The label on the
Pi is confirmed: the runner `plant-bench-pi` is Idle with label `bench` (Pi setup comment on PR #156, 22 Nov 2026).

**Requirements:** the bench round touches FR-D03, FR-A03, NFR-04, NFR-06 and NFR-07 (rows in
`projects/plant-monitor/tests/acceptance-matrix.md`). It covers the communication path only and does not pass those
rows. The mapping to steps is in the header of `bench.yml`.

## Order of the workflow (build first, then install and test; decided by the owner)
The workflow builds first and tests second. The jobs and steps run in this order:

1. **`build-firmware`** (GitHub-hosted, `ubuntu-latest`, no secrets). Builds the setup-flow firmware with the same
   steps as the `firmware` job of `.github/workflows/ci.yml` for the setup image: the ESP-IDF action pinned to a full
   commit SHA, `set -e`, `CONFIG_PLANT_SETUP_FLOW=y`, `CONFIG_PLANT_SIM_MOCK_SENSORS` off, and the `flasher_args.json`
   file check. Uploads `plant-monitor-firmware-setup`.
2. **`build-apk`** (GitHub-hosted, `ubuntu-latest`, no secrets). Builds the Android debug APK with the steps of
   `.github/workflows/app-apk.yml`. Uploads `plant-monitor-app-debug-<sha7>`. The two build inputs are repository
   variables (`SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, public client values), not secrets.
3. **`bench`** (the Pi, `[self-hosted, bench]`, `needs: [build-firmware, build-apk]`). Runs these steps in order:
   - 1. Download firmware image (the `build-firmware` artifact of this run)
   - 2. Download app APK (the `build-apk` artifact of this run), then a check that exactly one APK is there
   - a. Firmware flash
   - b. Serial boot log check
   - c. BLE scan
   - 4. Install app APK on the 6P (adb)
   - 3. Provision and flash board (NVS last)
   - d. App flow on phone
   - e. Cloud check
   - Bench E2E

Both build jobs run only on GitHub-hosted runners. Nothing is built on the Pi. If a build fails or is skipped, the
bench job does not start.

**Step numbers.** The download steps are numbered in the order they run (1 firmware, 2 APK). The letters a to e and
the numbers 3 and 4 keep their names. Step 3 runs after 4 and before d and e (see "Provisioning order" below).

## Artifacts and where each comes from

| Artifact | Produced by | Downloaded by (this run only) | Contents |
|---|---|---|---|
| `plant-monitor-firmware-setup` | `build-firmware`, step "Upload setup firmware artifact" | bench step 1 (`actions/download-artifact`, `run-id` = this run) | The files named in `flasher_args.json` plus that file. The artifact root is the build-setup folder: `flasher_args.json` at the root, no `build-setup/` folder inside. No sdkconfig, no logs, no NVS. |
| `plant-monitor-app-debug-<sha7>` | `build-apk`, step "Upload the debug APK" | bench step 2 (`actions/download-artifact`, `run-id` = this run, pattern `plant-monitor-app-debug-*`) | One debug APK, 14-day retention. `<sha7>` is the short commit sha of the run. |

There is no merged image. Step a writes each file of `flash_files` at its offset from `flasher_args.json`.
Step 3 does the same and then writes the NVS partition last.

The bench job downloads each artifact with the run id of this run. It never searches older runs.
Both downloads need the job permission `actions: read` (set on the bench job only).

## Trigger rules and why
The runner executes whatever code a job checks out. The repository is **public** (`gh api repos/nilwerk/nilwerk-lab --jq .visibility` returns `public`, checked 22 Nov 2026), so anyone can open a pull request or fork it. That is safe only while untrusted code cannot reach the runner. Only users with write access can start a `workflow_dispatch` run, which is why manual dispatch is the only trigger. So `bench.yml` allows only:

- `workflow_dispatch`: **manual runs only** (owner decision, 22 Nov 2026: manual trigger only). There is no schedule.
  The bench job runs only when the ref is `refs/heads/main`. There is no branch allowance: no PR branch
  or other branch runs the bench job. Any other ref runs only the two build jobs.

**Owner decision (accepted, option B): bench logs are not masked.** Run logs of this public repo are readable by anyone.
They show BLE device names and device addresses (step c) and chip-id output (steps a and 3). Logs stay unmasked by design;
no masking is added.

**Trigger the bench chain (after this PR is merged):** GitHub > **Actions** > **bench (self-hosted)** >
**Run workflow** > branch **main** > Run. The workflow file is on `main` only after the merge, so before that
the `main` branch is not offered. A PR branch never runs the bench job (see below).

**Why no schedule:** if a schedule were added, it would run the workflow file on `main` every night, and
the build jobs and steps 1, 2, a to e, 3 and E2E would then run unattended on the Pi with the bench secrets. That would be a new owner
decision, not a config change.

The branch allowance for `agent/devops/bench-workflow` (PR #156, closed) is removed. The bench job runs
only from `main`. Nothing else may run on the Pi.

Never add `pull_request`, `pull_request_target`, `push` or `issue_comment` to a bench
workflow. Those let a pull request, a fork or a comment run code on the Pi.

Residual risk, two places:

- `main`: a manual run from `main` runs the workflow file on `main` on the Pi. Anyone who can push to `main`
  controls what runs on the Pi on that run.
- `agent/devops/bench-workflow`: removed from the guard. A manual run from this branch does not run the bench job,
  so it does not get the bench secrets.
- The bench secrets (`BENCH_ANDROID_SERIAL`, `BENCH_TEST_EMAIL`, `BENCH_TEST_EMAIL_PASSWORD`, `BENCH_CLOUD_CHECK_CONFIG`,
  `BENCH_BOARD_POP`, `BENCH_WIFI_SSID`, `BENCH_WIFI_PASSWORD`) are read only by the bench job, which runs from `main` only.
- The bench job reads the provisioning folder from the repository variable `BENCH_PROVISION_DIR` (required; the
  workflow has no default). The folder is local to the Pi and its files never leave it. Owner decision, 22 Nov 2026.

## Steps of the bench job
The job runs these steps in order. Each hardware step fails closed: if its input is missing
it prints `not configured: nothing tested` and exits 1. Nothing is built on the Pi.

**Scope of the bench round (owner decision, 21 Nov 2026):** the bench round tests the
ESP32-to-app and ESP32-to-cloud communication only. Sensor values are not checked yet. The
firmware is the setup-flow build (`CONFIG_PLANT_SETUP_FLOW=y`, simulator off), built by `build-firmware` in the same run.

| Step | What it does | Input it needs | If missing |
|---|---|---|---|
| Runner smoke check | Host, arch, Node major, adb | none | Node missing or wrong major: fails. adb: printed only, not checked |
| 1. Download firmware image | Downloads `plant-monitor-firmware-setup` from the `build-firmware` job of this run (`run-id` = this run) to `bench-artifacts/firmware/build-setup/`. The artifact root is that folder. | Job permission `actions: read`; the `build-firmware` job succeeded | the download step fails (artifact not found) |
| 2. Download app APK, then check | Downloads `plant-monitor-app-debug-*` from the `build-apk` job of this run to `bench-artifacts/app-apk/`. The check step requires exactly one `.apk` there and sets `BENCH_APK_PATH`. Not committed, not uploaded. | Job permission `actions: read`; the `build-apk` job succeeded | the check step fails: `APK not found` |
| a. Firmware flash | Reads the chip id (must be ESP32-C3). Then reads `flasher_args.json` from step 1 and writes every file in `flash_files` at its listed offset, in offset order, with esptool, to the USB port `BENCH_ESP_PORT` (`/dev/ttyACM0`). Offsets are not hard-coded. | the step 1 artifact (`flasher_args.json` and the files it lists); a device at the port; `esptool` v5 on the runner | fails, no flash |
| b. Serial boot log | Reads the boot log for 20 s after a reset and asserts that the first line of the expect file that is not empty and not a `#` comment is in it. Boot line only. | `bench/firmware/expect.txt` (created from the firmware sources; not yet run on hardware) | fails |
| c. BLE scan | `bluetoothctl` scan for 10 s; asserts that the first line of the expect file that is not empty and not a `#` comment, with all whitespace removed, is the start of a device name seen in the scan. Only the name field is read, and the device address never matches. | `bench/ble/expect.txt` (created from the firmware sources: prefix `NW-`; the value `UNSET` stops the step), `bluetoothctl` | fails |
| 4. Install app APK on the 6P | Checks that exactly one device with the device id in secret `BENCH_ANDROID_SERIAL` is attached in state `device`, then runs `adb -s <device-id> install -r` with the APK from step 2. The device id is never printed. | Secret `BENCH_ANDROID_SERIAL`; the APK from step 2; `adb` | fails, no install |
| 3. Provision and flash | Reads the board ID from the repo variable `BENCH_BOARD_HW_ID` (value `<board-hw-id>`, not a secret). Reads the provisioning folder from the repo variable `BENCH_PROVISION_DIR` (required, no default; fails if empty). Checks that `<hw_id>.nvs.csv` and `<hw_id>.label.txt` exist in that folder and are mode `0600`. Checks for an ESP32-C3 on `/dev/ttyACM0`. Checks that the NVS tool is exactly 0.3.0 in the Pi venv. Reads the flash plan from the step 1 build-setup folder before any write. It builds the NVS partition from the CSV in a 0700 temp dir, writes each `flash_files` file at its offset in offset order, and writes the NVS partition last. The CSV and label are never printed. The label is checked but not used by the flash. | Repo variables `BENCH_BOARD_HW_ID` and `BENCH_PROVISION_DIR`; the provisioning folder on the Pi with both files at `0600`; the artifact from step 1; `esptool`; the ESP-IDF NVS tool (0.3.0, provisional) | fails before any write |
| d. App flow | Runs `bench/app/run_appium.sh` on the phone (Appium 2.x, UiAutomator2). **As written, the script only opens the app (package from `app.config.ts`) and checks that the first screen title (`app.name`) exists.** The device steps (scan, connect, write the setup data, connected) are not in the script yet (owner input). It asserts no sensor value. Before the script runs, the step records the test start time (UTC) as `BENCH_TEST_START_UTC` for step e. | `bench/app/run_appium.sh` (created; device steps are an owner input); secrets `BENCH_ANDROID_SERIAL` (phone id), `BENCH_TEST_EMAIL` and `BENCH_TEST_EMAIL_PASSWORD` (test account, passed as environment variables only); Appium 2.x on the runner | fails closed if a secret or Appium 2.x is missing |
| e. Cloud check | Runs `bench/cloud/check.sh`. It checks only that the device communicated with the cloud: at least one row from this device exists in the EU project and was received after `BENCH_TEST_START_UTC`. It does not read, print or compare any reading value. | `bench/cloud/check.sh` (created; one read of `public.readings` with the secret key, read-only); secret `BENCH_CLOUD_CHECK_CONFIG` (JSON `{url, secret_key}`, owner input); repository variable `BENCH_BOARD_HW_ID`; `BENCH_TEST_START_UTC` from step d | fails |
| Bench E2E | Runs `bench/run_e2e.sh` | `bench/run_e2e.sh` (created; runs `npm run test:web-flow`, a mock web flow, when the app's `node_modules` exist on the runner) | fails |

Steps 1 and 2 use the workflow token and the run's artifacts. Step 3 uses the repo variables. Steps 4, d and e use the repo secrets by name only; their values
live in the repository's Actions secrets and are never written to the repo.

**Provisioning order (decided by the owner).** Step 3 runs after 4 and before d and e. Steps d and e therefore test the
board as provisioned by step 3 (the build-setup files rewritten, then the NVS partition written last), not the board as
flashed by step a alone.

**Version pins (fix round, 22 Nov 2026). Not run on the Pi, not run here.** esptool is pinned to **v5.x**: steps a, b and 3
run `esptool version` and fail if the major is not 5, and steps a and 3 use the v5 command name `chip-id`. This was
checked against the esptool 5.6.0 source on PyPI (`version` prints `5.6.0`; `chip-id` is the v5 command).
The ESP-IDF NVS tool is pinned to **esp-idf-nvs-partition-gen 0.3.0** from the Pi venv `~/nvs-venv` (`nvs_venv` and
`nvs_pin` in `bench.yml`; the version check is in step 3). The pin is **PROVISIONAL**: it is not yet checked
against the ESP-IDF v5.4 constraints file (the fetch failed from the Pi and from the Mac). The v5.4 check is open.
Step 3 fails unless the installed version is exactly 0.3.0, installs nothing from the network, and calls the tool as
`python3 -I -m esp_idf_nvs_partition_gen generate <csv> <bin> <size>`, the form the 0.3.0 package accepts.

**Scratch folder:** `bench-artifacts/` (the firmware of step 1 and the APK of step 2) is git-ignored and is cleared at the
start of every run.

**Secrets for step d:** `BENCH_TEST_EMAIL`, `BENCH_TEST_EMAIL_PASSWORD`, `BENCH_BOARD_POP`,
`BENCH_WIFI_SSID` and `BENCH_WIFI_PASSWORD` are passed into the Appium step as environment variables
only. Step d fails closed if `BENCH_TEST_EMAIL` or `BENCH_TEST_EMAIL_PASSWORD` is missing, and they are
passed as environment variables only, never echoed. The script `bench/app/run_appium.sh` must not
echo them.

**Job permission:** `permissions: actions: read` is set on the bench job only (the download steps need it). The
workflow-level permissions stay `contents: read`. The two build jobs have `contents: read` only.

**Repository variables** (not secrets, set by the owner, not by this PR):
- `BENCH_BOARD_HW_ID` (value `<board-hw-id>`): the board's hw_id. Used by step 3 and by step e.
- `BENCH_PROVISION_DIR`: **required**, no default. The folder on the Pi that holds the provisioning files of step 3
  (`<hw_id>.nvs.csv` and `<hw_id>.label.txt`, mode `0600`). The workflow fails closed if it is empty. Its value is
  not written in this repo.

**Inputs created by this change (from the repo sources, see the header of each file):**
- `bench/firmware/expect.txt` (step b): `NWBENCH start board=`, from `projects/plant-monitor/firmware/main/main.c:105`.
- `bench/ble/expect.txt` (step c): `NW-`, the advertised name prefix, from `nw_prov_proto.c:58-69`. The value `UNSET`
  makes step c fail with "bench/ble/expect.txt has no expected name yet: owner input needed".
- `bench/app/run_appium.sh` (step d): opens the package from `app.config.ts` and checks the first screen title
  (`app.name`). It fails with "screen expectation missing: owner or app owner input needed" if the title is not readable.
- `bench/cloud/check.sh` (step e): one read-only GET of `public.readings` for the bench device. It fails with
  "cloud check not defined: owner input needed" if `BENCH_CLOUD_CHECK_CONFIG` is not the JSON form in its header.
- `bench/run_e2e.sh` (E2E): runs `npm run test:web-flow` (a mock web flow). It fails with
  "E2E not defined: owner input needed" if the script or the app's `node_modules` is missing.
- The expect files begin with a `#` header. Steps b and c skip `#` lines.

**Owner inputs still needed (not in the repo):**
- `bench/app/run_appium.sh`: the device steps (scan, connect, write setup data, connected) and the test-account
  sign-in are not in the script. The app owner confirms the first screen title.
- `bench/cloud/check.sh`: the owner sets `BENCH_CLOUD_CHECK_CONFIG` as the JSON object `{url, secret_key}` and approves
  that the check uses the secret key for one read (the key bypasses row-level security).
- `bench/run_e2e.sh`: whether the mock web flow is the bench E2E. The flow runs `expo export` (a build) and needs the
  app's dependencies and Chromium on the Pi; the Pi does not build (see the header of `bench.yml`).
- The provisioning files for the board on the Pi (step 3), in the folder named by `BENCH_PROVISION_DIR`.
- No longer needed: `bench/firmware/image.bin`. The firmware now comes from the `build-firmware` job of the same run.

**Open points (checked on 22 Nov 2026 by reading the workflow only):**
- Step 3 writes the NVS partition from the CSV at the offset of the `nvs` entry in the partition table binary. The
  flash plan (offsets and sizes) comes from the build. Check the offsets with Mira if the build layout changes.
- The ESP-IDF NVS tool must be in the venv `$HOME/nvs-venv` of the runner user, at exactly 0.3.0 (step 3 fails otherwise).
  The pin to 0.3.0 is provisional; the v5.4 check is open.
- The NVS offset and size are not set in this repo. Step 3 reads them from the `nvs` entry of the partition table binary in the build.
  Any fixed value (the ESP-IDF default table) is only a default and must be checked against the build's table.
- Step a flashes the board as soon as both builds succeed. No `bench/` file gates that flash any more (the old gate was
  `bench/firmware/image.bin`). Owner to confirm.

## Node workaround
This is a workaround, not the intended setup.

- **Expected Node:** major version 20. `node --version` must print `v20.x.y`; the patch
  number on the host is v20.19.2 (owner, 2026-11-22). The workflow reads the expected
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
3. Click **Run workflow**, set the branch to **main**, and confirm.
4. The two build jobs run on GitHub-hosted runners. The bench job then runs on the runner `plant-bench-pi`.
   A run from any other branch starts the two build jobs only; the bench job does not run.

Manual runs from a PR branch do not run the bench job (no branch allowance). Such a run starts only the two
GitHub-hosted build jobs. `build-apk` needs the repository variables `SUPABASE_URL` and `SUPABASE_PUBLISHABLE_KEY`
(Settings > Secrets and variables > Actions > Variables). They are variables, not secrets, and this doc records
their names only. Without them `build-apk` fails closed. The bench job runs only after the PR is merged, from `main`.

## Current state
- Not run in this session: the Pi, esptool, the NVS tool, the ESP-IDF build, the APK build, actionlint. This change was
  checked only by a YAML parse, a needs-graph check and a shell syntax check of the run blocks.
- The smoke step (host, architecture, Node, adb) runs and FAILS if Node is missing or is not
  major 20.
- Steps a to e, 3 and E2E fail closed until their inputs exist (see the table above). The `bench/` inputs are
  created by this change (see "Inputs created by this change"); the owner inputs listed above remain. A step that
  lacks an input stops with `not configured: nothing tested` or the owner-input message named in its row.
- Step a flashes the board before the serial and BLE checks run (see "Open points").
- The E2E step FAILS with "bench E2E not configured: nothing tested" until `bench/run_e2e.sh`
  exists on `main`. A green run therefore always means something was tested.

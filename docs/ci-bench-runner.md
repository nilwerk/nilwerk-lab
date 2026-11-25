# Bench runner (self-hosted GitHub Actions)

## What it is
A self-hosted GitHub Actions runner on the bench host. It runs the hardware-near
checks (the end-to-end bench setup) that GitHub-hosted runners cannot do.

- Runner name: the name chosen when the runner was registered (shown in the repository's runner list)
- Label: `bench` (the bench job uses `runs-on: [self-hosted, bench]`)
- Host: Debian GNU/Linux 13 (trixie), 64-bit, arm64 (`aarch64`).
- Workflow: `.github/workflows/bench.yml`

**Supersedes** the hardware-in-the-loop design in `projects/plant-monitor/docs/ci-firmware-in-the-loop.md`
(option b: `hil.yml`, label `esp32c3-bench`, GitHub Environment `bench` as the approval gate). This design uses
`bench.yml`, label `bench`, and **no Environment gate** (the owner declined it). `hil.yml` and `esp32c3-bench` are not used.

**Label check:** the label in this doc and in `bench.yml` (`runs-on: [self-hosted, bench]`) is `bench`. The label on the
Pi is confirmed: the runner is Idle with label `bench` (checked by the owner on 22 Nov 2026).

**Requirements:** the bench round touches FR-D03, FR-A03, NFR-04, NFR-06 and NFR-07 (rows in
`projects/plant-monitor/tests/acceptance-matrix.md`). It covers the communication path only and does not pass those
rows. The mapping to steps is in the header of `bench.yml`.

## Order of the workflow (build first, then install and test; decided by the owner)
The workflow builds first and tests second. The jobs and steps run in this order (a, 3, c, 4, d, b, e; A-138 and A-139, see "Order and window" below):

1. **`build-firmware`** (GitHub-hosted, `ubuntu-latest`, no secrets). Builds the setup-flow firmware with the same
   steps as the `firmware` job of `.github/workflows/ci.yml` for the setup image, and the same overlay list
   (`sdkconfig.defaults.bench-ci` last, so the bench image stays awake on USB): the ESP-IDF action pinned to a full
   commit SHA, `set -e`, `CONFIG_PLANT_SETUP_FLOW=y`, `CONFIG_PLANT_SIM_MOCK_SENSORS` off, `CONFIG_PLANT_BENCH_SLEEP_CYCLE`
   unset, and the `flasher_args.json` file check. Uploads `plant-monitor-firmware-setup`.
2. **`build-apk`** (GitHub-hosted, `ubuntu-latest`, no secrets). Builds the Android debug APK with the steps of
   `.github/workflows/app-apk.yml`. Uploads `plant-monitor-app-debug-<sha7>`. The two build inputs are repository
   variables (`SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, public client values), not secrets.
3. **`bench`** (the Pi, `[self-hosted, bench]`, `needs: [build-firmware, build-apk]`). Runs these steps in order:
   - 1. Download firmware image (the `build-firmware` artifact of this run)
   - 2. Download app APK (the `build-apk` artifact of this run), then a check that exactly one APK is there
   - a. Firmware flash
   - 3. Provision and flash board (NVS last)
   - c. BLE scan (inside the 300 s bench setup window)
   - 4. Install app APK on the 6P (adb)
   - d. App flow on phone
   - b. Serial live stream check (no reset, after d; waits for the setup window to close)
   - e. Cloud check
   - Bench E2E

Both build jobs run only on GitHub-hosted runners. The E2E test bundle (`expo export`, run by `bench/run_e2e.sh`) is built
on the Pi only when the app's `node_modules` are installed on the runner; that is not yet the case. If a build fails or is skipped, the
bench job does not start.

**Step numbers.** The download steps are numbered in the order they run (1 firmware, 2 APK). The letters a to e and
the numbers 3 and 4 keep their names. Step 3 runs after a and before c, 4, d and b (see "Provisioning order" below).

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

The branch allowance for `agent/devops/bench-workflow` (its pull request is closed) is removed. The bench job runs
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
it prints `not configured: nothing tested` and exits 1. The E2E test bundle is built on the Pi only when the app's
`node_modules` are installed there; that is not yet the case.

**Scope of the bench round (owner decision, 21 Nov 2026):** the bench round tests the
ESP32-to-app and ESP32-to-cloud communication only. Sensor values are not checked yet. The
firmware is the setup-flow build (`CONFIG_PLANT_SETUP_FLOW=y`, simulator off), built by `build-firmware` in the same run.

| Step | What it does | Input it needs | If missing |
|---|---|---|---|
| Runner smoke check | Host, arch, Node major, adb | none | Node missing or wrong major: fails. adb: printed only, not checked |
| 1. Download firmware image | Downloads `plant-monitor-firmware-setup` from the `build-firmware` job of this run (`run-id` = this run) to `bench-artifacts/firmware/build-setup/`. The artifact root is that folder. | Job permission `actions: read`; the `build-firmware` job succeeded | the download step fails (artifact not found) |
| 2. Download app APK, then check | Downloads `plant-monitor-app-debug-*` from the `build-apk` job of this run to `bench-artifacts/app-apk/`. The check step requires exactly one `.apk` there and sets `BENCH_APK_PATH`. Not committed, not uploaded. | Job permission `actions: read`; the `build-apk` job succeeded | the check step fails: `APK not found` |
| a. Firmware flash | Reads the chip id (must be ESP32-C3). Then reads `flasher_args.json` from step 1 and writes every file in `flash_files` at its listed offset, in offset order, with esptool, to the USB port `BENCH_ESP_PORT` (`/dev/ttyACM0`). Offsets are not hard-coded. | the step 1 artifact (`flasher_args.json` and the files it lists); a device at the port; `esptool` v5 on the runner | fails, no flash |
| 3. Provision and flash | Reads the board ID from the repo variable `BENCH_BOARD_HW_ID` (value `<board-hw-id>`, not a secret). Reads the provisioning folder from the repo variable `BENCH_PROVISION_DIR` (required, no default; fails if empty). Checks that `<hw_id>.nvs.csv` and `<hw_id>.label.txt` exist in that folder and are mode `0600`. Checks for an ESP32-C3 on `/dev/ttyACM0`. Checks that the NVS tool is exactly 0.3.0 in the Pi venv. Reads the flash plan from the step 1 build-setup folder before any write. It builds the NVS partition from the CSV in a 0700 temp dir, writes each `flash_files` file at its offset in offset order, and writes the NVS partition last. The CSV and label are never printed. The label is checked but not used by the flash. | Repo variables `BENCH_BOARD_HW_ID` and `BENCH_PROVISION_DIR`; the provisioning folder on the Pi with both files at `0600`; the artifact from step 1; `esptool`; the ESP-IDF NVS tool (0.3.0, provisional) | fails before any write |
| c. BLE scan | Runs after step 3, before step 4. `hcitool lescan` for 10 s (the step uses hcitool, not bluetoothctl), inside the bench setup window (300 s from the reset; `CONFIG_PLANT_BENCH_SETUP_WINDOW_S`, see "Timing" below). Asserts that the first line of the expect file that is not empty and not a `#` comment, with all whitespace removed, is the start of a device name seen in the scan. Only the name field is read, and the device address never matches. | `bench/ble/expect.txt` (created from the firmware sources: prefix `NW-`; the value `UNSET` stops the step), `bluetoothctl` | fails |
| b. Serial live stream | Runs after step d, before step e (A-139; it ran after c before). Waits until 310 s after the reset of step 3 (`BENCH_RESET_EPOCH`, written by step 3) in `bench/firmware/wait_setup_window.sh`, which fails closed if the wait would be longer than 310 s. The measurement loop starts when `nw_setup_run` returns, about 300 s after the reset (see "Order and window"). **No reset** (no esptool run, no reset, no RTS/DTR toggle). Reads the live serial stream for 75 s (owner decision, option 1). The bench image never deep-sleeps (`CONFIG_PLANT_BENCH_SLEEP_CYCLE` unset), so the wake lines start when the measurement loop starts and then keep coming, one per minute (upload build). Asserts that the first line of the expect file that is not empty and not a `#` comment, `NWBENCH wake=`, is in it. A board that prints no wake line for the whole window fails. | `bench/firmware/expect.txt` (created from the firmware sources; not yet run on hardware); a device at `/dev/ttyACM0` | fails, with "timeout, expected line not seen" |
| 4. Install app APK on the 6P | Checks that exactly one device with the device id in secret `BENCH_ANDROID_SERIAL` is attached in state `device`, then runs `adb -s <device-id> install -r` with the APK from step 2. The device id is never printed. | Secret `BENCH_ANDROID_SERIAL`; the APK from step 2; `adb` | fails, no install |
| d. App flow | Runs `bench/app/run_appium.sh` on the phone (Appium 2.x, UiAutomator2) with the real app build. The script signs in with the test account, adds a sensor through the app (scan, setup code, Wi-Fi, name, photo skip, plant details, done) and waits until this run's plant shows a reading on My plants. It reads and prints no sensor value. The screen order and the string keys are in the header of the script and in the PR. Not yet run on a phone. Before the script runs, the step records the test start time (UTC) as `BENCH_TEST_START_UTC` for step e. | `bench/app/run_appium.sh` (created); secrets `BENCH_ANDROID_SERIAL` (phone id), `BENCH_TEST_EMAIL`, `BENCH_TEST_EMAIL_PASSWORD`, `BENCH_BOARD_POP`, `BENCH_WIFI_SSID`, `BENCH_WIFI_PASSWORD` (environment variables only); repository variable `BENCH_BOARD_HW_ID`; Appium 2.x on the runner. Fixed limits in the script: first reading at most 900 s, whole step at most 2400 s, and each wait must fit the job clock (3300 s from the first step's `BENCH_JOB_START_EPOCH`, set by the job's first step); the job step has `timeout-minutes: 45` | fails closed if an input is missing or the setup code is malformed |
| e. Cloud check | Runs `bench/cloud/check.sh`. It checks only that the device communicated with the cloud: at least one row from this device exists in the EU project and was received after `BENCH_TEST_START_UTC`. It does not read, print or compare any reading value. | `bench/cloud/check.sh` (created; one read of `public.readings` with the secret key, read-only); secret `BENCH_CLOUD_CHECK_CONFIG` (JSON `{url, secret_key}`, owner input); repository variable `BENCH_BOARD_HW_ID`; `BENCH_TEST_START_UTC` from step d | fails |
| Bench E2E | Runs `bench/run_e2e.sh` | `bench/run_e2e.sh` (created; runs `npm run test:web-flow`, a mock web flow, when the app's `node_modules` exist on the runner) | fails |

**Appium health check (step d).** Before the step runs any phone command, `bench/app/appium_health.sh` asks Appium's `/status` URL (the `APPIUM_URL` value the app flow uses, default `http://localhost:4723`) up to 4 times, 5 s each, about 30 s in all. If the reply is HTTP 200 and says `ready: true`, the flow starts as before. Otherwise the step fails with one line: `d. app flow: 0. Appium not ready at APPIUM_URL (HTTP <code>): check the appium service on the Pi (systemctl status appium), then re-run`. On this status check, HTTP `000` means the server gave no answer (service down, wrong address or hung); any other code means Appium answered but is not ready. This tells a down Appium server apart from a failed app flow. `bench/app/test_appium_health.sh` tests the check against a local fake server and needs no Pi or phone.

**Slow session start (step d, `0. launch`).** The Pi's journal shows a session that was still being created when the old 30 s limit fired. It started at 17:29:58 and ended at 17:32:28 by the 120 s idle timeout, 150 s in all, which fits about 30 s of creation plus 120 s idle. The likely cause is a slow first start of the UiAutomator2 driver, which checks and may reinstall its helper APKs; that cause is probable, not proven, and the reinstall is an inference. `bench/app/appium_session.sh` therefore gives that one request 120 s (the other calls keep 30 s; the step has `timeout-minutes: 45` and the script stops at 2400 s) and sends `appium:uiautomator2ServerLaunchTimeout`, `appium:uiautomator2ServerInstallTimeout` and `appium:adbExecTimeout` of 60000 ms each. HTTP `000` on the session request is a different case from the status check: the server answered `/status`, but gave no reply in time, so the start is slow or stuck. The step fails with one line: `d. app flow: 0. launch: no reply from Appium within 120 s while starting the session: ...` and names the checks: `adb devices`, `journalctl -u appium -n 50`, and whether aapt2 (Android build-tools) is installed. Any other non-200 code reads `Appium did not start a session at APPIUM_URL (HTTP <code>)`. `bench/app/test_appium_session.sh` tests this against a local fake server (no Pi or phone). The check that a 200 reply holds a session id stays in `run_appium.sh` and is not covered by that test.

**Known gap on the current Pi:** `aapt2` (Android build-tools) is missing. The Appium journal shows `Could not find 'aapt2'` and `Cannot read version codes/names` of the helper APKs. The owner is checking whether it can be installed; until it is, a slow first start is expected.

Steps 1 and 2 use the workflow token and the run's artifacts. Step 3 uses the repo variables. Steps 4, d and e use the repo secrets by name only; their values
live in the repository's Actions secrets and are never written to the repo.

**Provisioning order (decided by the owner, option 1; A-139 moved b).** Step 3 runs after a and before c, 4, d and b. Steps c, 4, d, b and e therefore
run on the board as provisioned by step 3 (the build-setup files rewritten, then the NVS partition written last), not
the board as flashed by step a alone.
- Step 3 reads nothing that steps c and b write. It uses the step 1 build-setup folder, the repo variables and the USB port.
- Step 3 ends with a board reset: esptool's default `--after` is `hard-reset` (esptool 5.6.0 source), and this workflow
  does not change it. The board therefore boots the provisioned image right after the NVS write. Step 3 leaves the board running.
- Steps c, d and b need the board running after provisioning. Step b sends no reset (no esptool run, no RTS/DTR toggle); neither does
  step c. Do not add a reset to either step.
- The wake line exists only once the unit is provisioned (`main/main.c:81-87` deep-sleeps an unprovisioned unit before any read).
- Timing (not measured on hardware): the bench image is the one built by `build-firmware` in this workflow, with
  `sdkconfig.defaults.bench-ci` listed last. That overlay unsets `CONFIG_PLANT_BENCH_SLEEP_CYCLE`, so the measurement
  loop never ends (`main/main.c:37-41`): after a wake the app prints a `NWBENCH wake=` line once a minute (upload build)
  (`main/main.c:148`) and never reaches the deep sleep at `:155-159`. The board stays on USB. The bench image
  has no 60 s deep sleep.
- **Order and window (A-138 and A-139; owner-approved, bench image only).** Step 3 ends with the reset. The board
  opens its BLE setup window on that cold start (`main/main.c`, `button_held_ms_after_cold_start`, and `nw_setup_run`), and the
  window closes `CONFIG_PLANT_BENCH_SETUP_WINDOW_S` seconds later. It is **300 s** on the bench image (`sdkconfig.defaults.bench-ci`,
  A-137; it was 60 s, and the CI guards in `ci.yml` and `bench.yml` now pin 300). Everywhere else it is `NW_PROV_SETUP_TIMEOUT_MS`
  (300 s, `components/provisioning/include/nw_prov.h`). The window is measured from the boot in `nw_prov_boot`, so it closes about
  300 s after the reset. `nw_setup_run` returns; the measurement loop starts then and prints `NWBENCH wake=`. That is at window
  close, or earlier if a Wi-Fi claim succeeds (`nw_prov_glue.c:182-186`, `nw_prov_idf.c:257`), or later while a Wi-Fi join or
  claim is in flight (up to about 35 s past 300 s). Step b reads R+310 to R+385, so it still passes in all these cases.
  Whether BLE stops at the same moment is not stated here (not checked).
- **Why step b moved (A-139).** With a 60 s window, step b (75 s) could run inside the window's tail and read wake lines
  that only start at 60 s. With the 300 s window, step b would need to wait about 5 minutes after the reset, or it reads nothing.
  Moving b to after the app flow d means the wait is zero whenever steps 4 and d took 310 s or more (expected, not measured). Step b still
  waits when they do not: it sleeps until `BENCH_RESET_EPOCH + 310` s (10 s margin), then reads 75 s. The step is otherwise unchanged.
- **Timing margin for step c (estimates, not measured on hardware; no run exists for this head).** Step 3's reset to step c's
  first command: the runner's step hand-over, about 2 to 5 s. Step c: the BLE scan start plus 10 s, about 12 to 15 s. So c ends
  about 15 to 20 s after the reset, and the window closes about 300 s after it. The margin is about 280 s. Step c fails with
  "no device with name prefix" only if the window has closed before its scan, which the margin makes unlikely.
- **Window must cover step d (not measured; the main new risk of 300 s).** Steps 4 and d add the sensor in the app while the
  window is open. Both must finish within about 300 s of the reset, or the phone cannot connect to the open BLE window and step d
  fails. Wi-Fi credentials must go out before R+300, when the window closes. Step d's Wi-Fi wait (`bench/app/run_appium.sh`
  line 385, 360 s) has no window check, so a Wi-Fi step that comes late fails later, without a clear reason. A window check before
  that wait is a follow-up, not in this change. Step e is not affected. If d regularly runs past the window, the fix is a longer window (in four places: the
  `sdkconfig.defaults.bench-ci` value, the two `ci.yml`/`bench.yml` guards, and the 310 s wait in step b), not a shorter step b.
- **Job time budget (A-139, arithmetic from the workflow, not measured).** The bench job has `timeout-minutes: 60` (3600 s) from its
  first step. Step b adds at most about 80 s (the 75 s read, the esptool version check and a few seconds), plus any wait for
  the window. That wait is at most about 310 s minus the time from the reset to the start of step b. Because b runs after d,
  the wait is nonzero only when steps 4 and d took less than about 310 s, so the extra time is at most about 5 minutes in
  that case and zero otherwise. Step e's fail-closed budget check runs after b and reads the elapsed time, so b's time is
  counted in it. The 900 s reserve for `check.sh` and Bench E2E is unchanged. Whether the whole job fits in 60 minutes depends on the
  durations of steps a to d, which have not run yet. If they do not fit, step e fails closed with "nothing tested" (the same
  rule as before), and the owner decides whether to raise `timeout-minutes`.
- **Bench upload build (owner decision 2026-11-23, `CONFIG_PLANT_BENCH_UPLOAD_MINUTE` in `sdkconfig.defaults.bench-ci`).** The image
  uploads once a minute and does not deep-sleep. It prints one `NWBENCH wake=` line per minute, before the upload, so the first
  line comes when the measurement loop starts: when `nw_setup_run` returns, at window close (about 300 s after the reset), or
  earlier on a Wi-Fi claim, or later while a join or claim is in flight (up to about 35 s past 300 s). Step b reads R+310 to R+385,
  so a 75 s read always holds one line (lines are 60 s apart). Not checked on hardware.
- **BLE on every cold start, bench image only (owner sign-off needed).** `sdkconfig.defaults.bench-ci` sets
  `CONFIG_PLANT_BENCH_AUTO_SETUP=y` (`main/Kconfig.projbuild`, `depends on PLANT_SETUP_FLOW`). On that image each cold start
  (not a deep-sleep wake) passes the setup request to `nw_setup_run` as if BOOT were held for 3 s
  (`main/main.c`, `button_held_ms_after_cold_start`). BLE then advertises the `NW-` name for the bench setup window (300 s), with no
  button press. The production window (300 s, `NW_PROV_SETUP_TIMEOUT_MS`, `components/provisioning/include/nw_prov.h:16`) is
  unchanged, and so is the host test that checks it (`test/host/test_prov.c`, `test_five_minute_limit`).
  The window is shortened only through `CONFIG_PLANT_BENCH_SETUP_WINDOW_S` (`main/Kconfig.projbuild`, defined only when
  `PLANT_BENCH_AUTO_SETUP` is on). The glue sets `nw_prov_t.setup_window_ms` from it (`components/provisioning/src/nw_prov_idf.c`);
  `nw_prov_tick` uses that field only when it is non-zero (`components/provisioning/src/nw_prov.c`). Production builds leave it at 0.
  This opens BLE setup without the button on that image only. A provisioned unit can enter setup there too, because the
  bench flag passes the setup request that `nw_prov_boot` (`components/provisioning/src/nw_prov.c`, the check that refuses setup
  without a button) would otherwise refuse. PoP is unchanged: the security-2 salt and verifier must be in NVS, or BLE stays off (`nw_prov_idf.c`, `start_ble`).
  Production, v1 and upload builds do not set the flag: they still need BOOT held on a cold start, and a provisioned unit
  still refuses setup without it.
- Production (default) build: `main/Kconfig.projbuild:39-41` defaults the option to `y`, so that build still
  deep-sleeps after five readings (`main/main.c:155-159`). The overlay is not part of the production build, the v1
  build or the upload build.

**Version pins (fix round, 22 Nov 2026). Not run on the Pi, not run here.** esptool is pinned to **v5.x**: steps a, b and 3
run `esptool version` and fail if the major is not 5, and steps a and 3 use the v5 command name `chip-id`. This was
checked against the esptool 5.6.0 source on PyPI (`version` prints `5.6.0`; `chip-id` is the v5 command).
The ESP-IDF NVS tool is pinned to **esp-idf-nvs-partition-gen 0.3.0** from the Pi venv `~/nvs-venv` (`nvs_venv` and
`nvs_pin` in `bench.yml`; the version check is in step 3). The pin is **PROVISIONAL**: it is not yet checked
against the ESP-IDF v5.4 constraints file (the fetch failed from the Pi and from a developer machine). The v5.4 check is open.
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
- `SUPABASE_URL`: the project URL only (`https://<project-ref>.supabase.co`, no path, no trailing slash). The job
  `build-firmware` builds `CONFIG_PLANT_API_BASE_URL` from it as `<SUPABASE_URL>/functions/v1` (the functions path in
  `docs/interfaces/openapi.yaml`), writes it to the git-ignored `firmware/sdkconfig.defaults.local` and passes that file
  in `SDKCONFIG_DEFAULTS` (DEV_GUIDE 7.1, option 2). The job fails closed if it is missing or not `https://`. The value is
  never printed and the file is never uploaded. Also used by the Android APK job (same variable).
- `BENCH_FIRST_READING_WAIT_S`: **required**, no default, whole seconds from 60 to 3600. Step e sleeps this long before its
  one read of the cloud, so the first upload of the 1-minute bench build can arrive. Step e fails closed if it is missing
  or out of range. **Note:** the bench job has `timeout-minutes: 60`, which also limits this wait (steps a to d and b run first). A longer job limit is an owner decision, not made here. The 900 s reserve in the budget check (for `check.sh` and Bench E2E) is an **assumption, not measured**; the owner may tune it.
- `BENCH_PROVISION_DIR`: **required**, no default. The folder on the Pi that holds the provisioning files of step 3
  (`<hw_id>.nvs.csv` and `<hw_id>.label.txt`, mode `0600`). The workflow fails closed if it is empty. Its value is
  not written in this repo.

**Inputs created by this change (from the repo sources, see the header of each file):**
- `bench/firmware/expect.txt` (step b): `NWBENCH wake=`, from the `printf` in `projects/plant-monitor/firmware/main/main.c` (printed once per reading cycle; step b sends no reset).
- `bench/ble/expect.txt` (step c): `NW-`, the advertised name prefix, from `nw_prov_proto.c:58-69`. The value `UNSET`
  makes step c fail with "bench/ble/expect.txt has no expected name yet: owner input needed".
- `bench/app/run_appium.sh` (step d): the app flow in the real build (sign in, add a sensor, first reading on My plants).
  It fails with "d. app flow: <step>: <reason>" at the first step that does not show the expected text.
- `bench/cloud/check.sh` (step e): one read-only GET of `public.readings` for the bench device. It fails with
  "cloud check not defined: owner input needed" if `BENCH_CLOUD_CHECK_CONFIG` is not the JSON form in its header.
- `bench/run_e2e.sh` (E2E): runs `npm run test:web-flow` (a mock web flow). It fails with
  "E2E not defined: owner input needed" if the script or the app's `node_modules` is missing.
- The expect files begin with a `#` header. Steps b and c skip `#` lines.

**Owner inputs still needed (not in the repo):**
- `bench/app/run_appium.sh`: none (the wait limits are fixed in the script; the first reading may take up to 900 s, so the DevOps role
  should confirm that the upload interval fits). The workflow step d passes `BENCH_BOARD_HW_ID` (repository variable).
  The BLE setup window (300 s from the reset of step 3) must be open while step d adds the sensor.
- `bench/cloud/check.sh`: the owner sets `BENCH_CLOUD_CHECK_CONFIG` as the JSON object `{url, secret_key}` and approves
  that the check uses the secret key for one read (the key bypasses row-level security).
- `bench/run_e2e.sh`: whether the mock web flow is the bench E2E. The flow runs `expo export` (a build) and needs the
  app's dependencies and Chromium on the Pi. The export is built on the Pi only once the dependencies are installed there,
  and that is not yet the case (see the header of `bench.yml`).
- The provisioning files for the board on the Pi (step 3), in the folder named by `BENCH_PROVISION_DIR`.
- No longer needed: `bench/firmware/image.bin`. The firmware now comes from the `build-firmware` job of the same run.

**Open points (checked on 22 Nov 2026 by reading the workflow only):**
- Step 3 writes the NVS partition from the CSV at the offset of the `nvs` entry in the partition table binary. The
  flash plan (offsets and sizes) comes from the build. Check the offsets with the firmware role if the build layout changes.
- The ESP-IDF NVS tool must be in the venv `$HOME/nvs-venv` of the runner user, at exactly 0.3.0 (step 3 fails otherwise).
  The pin to 0.3.0 is provisional; the v5.4 check is open.
- The NVS offset and size are not set in this repo. Step 3 reads them from the `nvs` entry of the partition table binary in the build.
  Any fixed value (the ESP-IDF default table) is only a default and must be checked against the build's table.
- Step a flashes the board as soon as both builds succeed. No `bench/` file gates that flash any more (the old gate was
  `bench/firmware/image.bin`). Owner to confirm.
- Step b timing: the read window is 75 s. Step b now waits until 310 s after the reset of step 3 (A-139), capped at 310 s by `bench/firmware/wait_setup_window.sh` (offline test: `bench/firmware/test_wait_setup_window.sh`). The bench image stays awake, so wake lines continue
  through the read window. Not checked on hardware. Any change must not add a reset to step b.
- Step 3 and step b use the same port (`/dev/ttyACM0`). After a hard reset the USB port may re-enumerate; step b checks
  that the port exists when it starts. Not checked on hardware.

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
4. The two build jobs run on GitHub-hosted runners. The bench job then runs on the bench runner (label `bench`).
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
- Steps a and 3 flash the board before the serial and BLE checks run (see "Open points").
- The E2E step FAILS with "bench E2E not configured: nothing tested" until `bench/run_e2e.sh`
  exists on `main`. A green run therefore always means something was tested.

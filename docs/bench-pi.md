# Bench Pi: setup, paths, board facts and lessons

For the team: what the bench Raspberry Pi is, where things live, and what we learned bringing it up on 23 Nov 2026.
Secrets, provisioning values and account details are NOT in this file on purpose. They stay on the Pi and in the GitHub settings.

## 1. The Pi

- Raspberry Pi 3B+ on 64-bit Raspberry Pi OS (Trixie). GitHub rejected a 32-bit runner, so the Pi was reflashed to 64-bit and the runner was re-registered as `plant-bench-pi` (arm64).
- Runner user: `ghrunner`. Runner service: `actions.runner.nilwerk-nilwerk-lab.plant-bench-pi.service`.
- Runner workspace: `/home/ghrunner/actions-runner/_work/nilwerk-lab/nilwerk-lab`.
- Bench artifacts, cleared at the start of each run: `bench-artifacts/firmware/build-setup` and `bench-artifacts/app-apk`.
- Admin login `pi` has passwordless sudo. Its home folder is mode `0700`, so `ghrunner` cannot read files there.
- Reach the Pi through its Tailscale name or IP, not a LAN address. The name is in the team's access notes, not here.
- Admin access uses an SSH key with a passphrase. Load it once into the SSH agent so it is not asked for each time.

## 2. Paths and tools on the Pi

- Provisioning folder: `/var/lib/nilwerk-provision`, owned by `ghrunner`, mode `0600`. The repo variable `BENCH_PROVISION_DIR` points here. The files stay out of git and out of chat.
- Repo variable `BENCH_BOARD_HW_ID` holds the test board's hw_id. It is not a secret.
- esptool 5.6.0 lives in `/home/ghrunner/esptool-venv`. Run it with `sudo` from the `pi` login, because `pi` cannot run it directly.
- NVS partition tool `esp-idf-nvs-partition-gen==0.3.0` lives in `/home/ghrunner/nvs-venv`.
- Node 20.19 for the app test, Appium 2.19.0 (running as the `appium` service under `ghrunner` on 127.0.0.1:4723), UiAutomator2 driver 3.8.0 for the runner user, adb 1.0.41 for the phone, jq 1.7.
- Tools already checked on the Pi: Node, adb, esptool, the NVS tool, hcitool with its Bluetooth capabilities, flock, python3, curl, Java.
- Bluetooth restart: `ghrunner` may restart Bluetooth without a password (approved by the owner).
- Docker on a Mac (`espressif/idf:v5.4`) builds the firmware with the same settings as CI, for local checks.

## 3. Board facts (ESP32-C3 SuperMini)

- USB device `303a:1001`. Serial port `/dev/ttyACM0`.
- Test board: USB serial `C8:DA:29:86:F4:70`, hw_id `nw-c8da2986f470`.
- Second board: USB serial `E8:F6:0A:4F:63:E8`. It was blank in this session. Check the serial before you flash or provision.
- The Bluetooth name is `NW-` plus the last six hex digits of the hw_id, for example `NW-86f470`.

## 4. Hardware fix: GPIO9 pull-up

- Symptom: after a reset from the host, the chip booted into ROM download mode (`boot:0x5`). The app never ran, so nothing advertised.
- Cause: GPIO9, the boot-mode pin, was pulled low during reset.
- Fix: a 10 kOhm resistor from GPIO9 to 3V3 on the board. First check that the board does not already have one. Do not tie GPIO9 straight to 3V3.
- Result: the board boots normally (`boot:0xd SPI_FAST_FLASH_BOOT`).
- The product PCB and the v1 perfboard wiring guide (task 4.P6) must include this pull-up.

## 5. Firmware fixes (branch `fix/ble-discoverable`)

- NVS before Wi-Fi: `nw_setup_run` started Wi-Fi before flash storage (NVS). Wi-Fi failed with `ESP_ERR_NVS_NOT_INITIALIZED` (4353), so BLE setup never started. NVS init now runs first.
- Logging: `start_ble` logs which call failed, so the cause shows in the serial log.
- Bench-only sleep skip: the bench image (`CONFIG_PLANT_BENCH_AUTO_SETUP`) does not deep-sleep after a closed setup. Production builds are unchanged.

## 6. Reset and serial lessons

- Opening `/dev/ttyACM0` (for example with `cat`) can pull the reset lines, and a host-side reset can drop the board into download mode.
- A watchdog reset (`esptool --after watchdog-reset`) did not reliably bring the board back. Do not rely on it.
- For a serial capture, reopen the port after each reset. A reader stuck on the old device gets nothing.
- Flash with `--after no-reset` when you want to read the boot output afterwards.
- Before any capture or flash, stop other readers on the port. Use PIDs, not `pkill -f ttyACM0`, which can kill your own shell.

## 7. Diagnostics that worked

- `dmesg | grep 1-1.3` on the Pi shows connect, disconnect and "error -71" (device not accepting address) events.
- `vcgencmd get_throttled` shows Pi power problems. `0x0` means clean. Use the official 5 V 3 A supply.
- `hcitool lescan --duplicates` shows the advertisement. `bluetoothctl scan` missed it.
- Read the first lines of the boot log: `rst:` says why it reset, `boot:` says which mode it booted in.

## 8. Mistakes to avoid

- A "success" line from a flash step only means the write verified. It does not mean the app runs.
- Do not blame the firmware until the boot log shows the app running.
- Do not push from a shared login. Git may reuse a stored account; check the account name in the `git push` output.

## 9. Open TODOs

1. Switch the bench step c (BLE check) from `bluetoothctl` to `hcitool lescan` in `.github/workflows/bench.yml`.
2. Run the bench flow on the fixed branch with the GPIO9 pull-up fitted, and confirm step c passes.
3. Add the simulator setup-flow scenario (branch `sim-setup-check`, not yet run).
4. Put the NVS-before-Wi-Fi fix into the team's firmware review notes.
5. Decide who owns the Pi (the `ghrunner` secrets folder and the `pi` admin login).
6. Confirm which physical board (C8 or E8) is assigned to each bench slot.
7. Document the Docker build recipe in the firmware guide.

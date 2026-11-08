# Running the firmware (4.F1) inside the pipeline - design note

Status: proposal by Kai (Pipeline / DevOps), 2026-11-08. **Nothing in here has been run.** The agent sandbox cannot download ESP
toolchains or QEMU (playbook rule), so every claim about QEMU behaviour below is from the Espressif documentation as we know it and
is marked *unverified* until one CI run proves it. No runner is set up and no secret is touched by this note.

## Where we are
- CI already builds the firmware for `esp32c3` with ESP-IDF v5.4 (`espressif/esp-idf-ci-action`) and runs the host unit tests
  (`firmware/test/host`, fake HAL). Nothing runs the *binary*.
- The 4.F1 app (`firmware/main/main.c`) prints `NWBENCH start ...`, then one `NWBENCH wake=.. i=.. ... err=soil:a,aht:b,bh:c,bat:d`
  line every 2 s, and with `CONFIG_PLANT_BENCH_SLEEP_CYCLE` a `NWBENCH sleep s=60` line and deep sleep after 5 lines.
  Error codes are in `components/sensors/include/nw_hal.h` (`0` ok, `-1` I/O failed, `-6` unsupported).
- The bench procedure is the work order `docs/work-orders/WO-firmware-4.F1.md`. It has not been run on hardware yet.

## Option (a): ESP32-C3 in QEMU, boot smoke test (no sensors)

**What it is.** Espressif's QEMU fork has an `esp32c3` machine. `pytest-embedded` (services `idf` + `qemu`) builds a flash image
from the IDF build, starts QEMU, and lets a pytest function `expect()` regexes on the console. Install in the job with
`python $IDF_PATH/tools/idf_tools.py install qemu-riscv32` (the `espressif/idf:v5.4` image does not ship it, *unverified*), then
`pip install pytest-embedded pytest-embedded-idf pytest-embedded-qemu` and `pytest --embedded-services idf,qemu --target esp32c3`.

**Feasible with `espressif/idf` v5.4?** Yes in principle: IDF 5.4 documents QEMU for esp32c3 and the same container already builds our
firmware. Use the `container:` form (`image: espressif/idf:v5.4`) in a new job `firmware-qemu` that `needs: firmware`, or run build and
test in one job to avoid passing the build directory around (simpler: one job, one extra step after the existing build).

**What it covers.**
| Covered | Not covered |
|---|---|
| Firmware boots on a C3 core (bootloader, partition table, app_main reached, no panic/abort/reboot loop) | I2C: no emulated AHT20/BH1750, so no sensor data, no wiring, no timing |
| `NWBENCH start wake=1 ...` line with the Kconfig calibration values and divider printed | ADC and calibration: not emulated, so battery/soil values are meaningless |
| Format of the `NWBENCH` lines (a regex that the host tests cannot give us, because it is the real `printf` path) | Deep-sleep current, wake source, RTC memory across sleep: emulation of low-power modes is limited (*unverified*) |
| With no sensors: `aht:-1` and `bh:-1` on every line (the I2C driver reports a failed transfer, which `hal_esp32.c` maps to `-1`) | Wi-Fi/BLE (later tasks, 4.F2+) |

Caveats to settle in the first CI run, not by argument: (1) `i2c_new_master_bus` and `adc_oneshot_*` may fail or block in QEMU;
if `nw_hal_esp32_init` returns an error the app prints only `HAL init failed` and returns, so the smoke test would see no `NWBENCH`
line. Then the smoke test must assert on that behaviour or the test needs a QEMU build flag (a Kconfig `PLANT_SIM_NO_HW` that skips
init), which is a firmware change for Mira. (2) Each failed I2C transfer waits for its timeout, so lines may be slower than 2 s.
Assert `err=` only for `aht` and `bh` (`-1`), do not assert on `soil` and `bat` in QEMU.

**Cost.** Build is paid already. Extra: QEMU install about 1 min, pytest run about 1-2 min (boot a few seconds, wait for 3
`NWBENCH` lines about 10 s at most), so roughly **+3 to 4 CI minutes** per firmware run, no extra cost on a private repo beyond
the Actions minutes already used (the `firmware` job is gated by the detect step, so docs-only PRs do not pay it).

**Value.** Catches: boot crashes, stack overflow at start, bad `sdkconfig` defaults, changed log format that breaks the bench
parser, panics in the "no sensor" path (which is a real product case: an unplugged sensor must not crash the device).
Does not catch anything electrical.

## Option (b): hardware in the loop (HIL) on a self-hosted runner

**Idea.** A small always-on machine in Reutlingen (Raspberry Pi 4/5 or any Linux box) with the ESP32-C3 dev kit on USB and the real
sensors wired (AHT20, BH1750, soil probe, battery divider) runs a GitHub Actions runner. A workflow job with
`runs-on: [self-hosted, linux, esp32c3-bench]`:
1. downloads the firmware artifact built by the normal `firmware` job (do **not** build on the Pi: the IDF container is amd64, the
   build is already done in the cloud, and a binary that was built in CI is the binary we ship);
2. flashes it with `esptool.py --chip esp32c3 -p /dev/serial/by-id/<kit> write_flash @flasher_args.json` (or `idf.py flash` if IDF
   is installed on the Pi; esptool alone is lighter);
3. opens the same serial port with `pyserial`, collects `NWBENCH` lines for about 15 s (the USB Serial/JTAG port re-enumerates
   after the reset, so use the `by-id` path and retry the open for a few seconds);
4. asserts, with a small `hil_check.py`: `err=soil:0,aht:0,bh:0,bat:0` on at least 5 lines, `temp_c` 10-40, `rh_pct` 5-95,
   `lux_raw != 65535`, `vbat_plausible=1`, `soil_pct` inside 0-100 (the soil raw span and the finger/breath tests of the work order
   stay manual: they need a human);
5. optional later: a Pi GPIO wired to IO3 reads 0 V during deep sleep (NFR-12 check, step 9 of the work order) and a relay on the
   USB/3V3 line to power-cycle a hung kit.

**Not possible even with HIL:** sleep current (the dev kit has USB bridge, LED, LDO; the work order says so), calibration quality,
range/Wi-Fi behaviour. Those stay with the real board and a power analyser.

**Security of a self-hosted runner on a private repo.**
- A runner executes whatever a workflow says. Anyone who can push a branch and change a workflow (agents, collaborators) can run code
  on that machine. So: put HIL in its **own workflow file** (`.github/workflows/hil.yml`) triggered only by `workflow_dispatch` and
  `push` to `main`, **never `pull_request`** or `pull_request_target`; protect it with a GitHub **Environment** `bench` with Arsany as
  required reviewer (environment protection on private repos depends on the GitHub plan: Arsany to check, *unverified*); use
  `permissions: contents: read`.
- Dedicated machine with nothing else on it: no personal files, no SSH keys, no cloud credentials, no access to the home network
  beyond internet (separate VLAN or guest Wi-Fi if the router allows). Runner runs as an unprivileged user (member of `dialout` for the
  serial port, no `sudo`), as a systemd service, with `--ephemeral` registration if he wants a fresh state per job.
- Keep the HIL job free of secrets: it needs none (flash + read serial). If a later job needs Supabase test credentials, they come
  from GitHub Environment secrets by name, never from the repo, and not on this runner.
- Pin third-party actions by commit SHA in `hil.yml`; keep the runner binary updated (GitHub drops old runner versions).
- Disable the runner (stop the service) when nobody is around; the job simply queues.
- Never print the runner registration token or paste it anywhere: it is single use and expires after about an hour. It is created in
  the repo's Settings > Actions > Runners > New self-hosted runner and typed on the machine only.

**What Arsany has to do (the agents will not).**
1. Decide the machine (Pi 4/5 with 64-bit Raspberry Pi OS or Ubuntu, 2 GB RAM is enough because nothing is built there) and where the dev kit
   sits on a USB cable with the sensors wired as in the work order.
2. Create the runner in GitHub (Settings > Actions > Runners > New), run the shown commands on the machine as the unprivileged user,
   label it `esp32c3-bench`. The token stays on his screen and that machine.
3. Create the Environment `bench` with himself as required reviewer, and check that his plan supports it for a private repo.
4. Plug in the kit, tell us the by-id serial path (`ls /dev/serial/by-id/`), then Kai writes `hil.yml` + `hil_check.py` in a PR.

**Cost.** Hardware: a Pi and a cable, about 60-100 EUR if he has none (he decides and orders, agents do not buy). Actions minutes:
self-hosted runners are not billed. Time per run about 1-2 min plus waiting for approval.

## Recommended sequence
1. **Manual bench test first** (work order WO-firmware-4.F1, Peter or Arsany). It finds out whether the sensor drivers work at all, and
   gives the real `NWBENCH` lines and ranges that the CI asserts must be based on. Never write thresholds from datasheets only.
2. **QEMU smoke test** (about half a day of Kai plus Mira, only for the QEMU caveats above). Cheap, needs no hardware and no
   approval, protects boot and the unplugged-sensor path from now on. If QEMU turns out to hang in I2C or ADC init, a small firmware
   switch (`PLANT_SIM_NO_HW`) is the price, which Mira decides.
3. **HIL last**, once the bench test passed and the firmware has more than the bench app (4.F2 reporting makes the end-to-end check
   worth it: device to ingest API). Needs Arsany's machine and the security setup above. Until then the manual bench test is
   repeated by hand for each firmware release.

Open for Arsany: A-xxx (to be raised by the Lead) - which machine, and whether the `bench` Environment is available on our GitHub plan.

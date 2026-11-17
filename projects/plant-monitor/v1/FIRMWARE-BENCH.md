# v1 bench run: firmware build, serial output spec and pass/fail (task 4.F1, v1 slice)

Author: Mira (Firmware + Edge AI), 2026-11-17, branch `agent/firmware/4.F1-v1-bench`. Audience: Peter (builds, flashes, records), Arsany (reads the result).
Hardware: the v1 perfboard from [`WIRING.md`](WIRING.md) (ESP32-C3 SuperMini, AHT20, BH1750, capacitive soil probe v1.2, 2 x 100 kOhm divider).
Requirements: FR-D01 (five readings), NFR-12 (soil supply low in sleep: function check only). v1 numbers are never product figures (WIRING.md section 2.7).

**Status: nothing in this file has run on hardware. The firmware was not built for the target by its author (no ESP-IDF toolchain in the authoring session).
**CI compiles the v1 option too** (second `idf.py -B build-v1 ... build size` step in the `firmware` job of `ci.yml`, separate build dir and sdkconfig). Still NOT built on the board: the CI build only proves it compiles.
So step 0 below (build with the v1 defaults) is the first time this option is built on your machine and flashed to the board.** Every "expected" line below is read from `firmware/main/main.c`, every expected value is a typical value or UNVERIFIED. A FAIL with a good log is a useful result.**
Peter: do not decide anything the checklist says to report. Report with the log and stop.

## 1. What the v1 build is (cites)
| Item | Value | Source |
|---|---|---|
| Board option | `PLANT_BOARD_V1_SUPERMINI` (Kconfig choice, `firmware/main/Kconfig.projbuild`), selected by `firmware/sdkconfig.defaults.v1` | this PR |
| SDA / SCL | GPIO6 / GPIO7, explicit (not the SuperMini Arduino default GPIO8/GPIO9) | WIRING.md section 3 |
| Soil power / AOUT | GPIO3 (HIGH only while measuring) / GPIO4 = ADC1_CH4 | WIRING.md section 3 |
| Battery sense | GPIO0 = ADC1_CH0, divider 100 kOhm / 100 kOhm on the switched side of J1 | WIRING.md sections 3, 4.2, 2.7 |
| Button | GPIO9 = BOOT key (not used by the bench loop; setup flow is off) | WIRING.md section 3 |
| Console | native USB Serial/JTAG (`CONFIG_ESP_CONSOLE_USB_SERIAL_JTAG=y`): the SuperMini has no UART bridge, the dev-kit UART console would print nothing on the USB port | `sdkconfig.defaults.v1` (UNVERIFIED on the board) |
| BLE setup flow | off (`CONFIG_PLANT_SETUP_FLOW=n`): with it on, a never-provisioned unit deep sleeps with no timer before any sensor is read (`main.c`) | `sdkconfig.defaults.v1` |
| Soil calibration | `PLANT_SOIL_DRY_RAW` 2800 / `PLANT_SOIL_WET_RAW` 1200 are PLACEHOLDERS; `soil_pct` is not a result until you measure and Mira sets them | `Kconfig.projbuild` |
`test/host/check_board_v1.py` fails CI if board.h and the WIRING.md section 3 table disagree. CI does not run on `v1/` changes alone: if WIRING.md changes, run the host tests.

## 2. Build settings (nothing secret is committed)
Needs ESP-IDF v5.4 (the version CI uses for its devkit build). From `projects/plant-monitor/firmware`:
```
idf.py -D SDKCONFIG_DEFAULTS="sdkconfig.defaults;sdkconfig.defaults.v1" set-target esp32c3
idf.py build
```
If a `sdkconfig` file already exists from another build, delete it first (`SDKCONFIG_DEFAULTS` only seeds a new one), then repeat. Ends with "Project build complete".

**`PLANT_API_BASE_URL` is a build setting and is not committed (A-082).** The real nilwerk-cloud project API URL is given later by Arsany. Until then the default `https://api.invalid` stays
(it never resolves). **The v1 bench does not use it:** the bench loop does no network call. To set a real value later, locally only:
1. create `firmware/sdkconfig.defaults.local` (git-ignored, never `git add -f` it) with one line: `CONFIG_PLANT_API_BASE_URL="https://<project>.example/functions/v1"` (placeholder shown), then add it as a third entry in `SDKCONFIG_DEFAULTS`; or
2. `idf.py menuconfig` -> Plant Monitor -> Cloud API base URL (stored in the git-ignored `sdkconfig`).
Format: https, no trailing slash (Kconfig help). `test/host/check_api_url_not_committed.py` fails CI if any tracked firmware file sets another value or the local file is not ignored.
This is a project URL, not a key: no token or key belongs in any of these files either (per-device tokens come from provisioning, not from the build).

## 3. Before you flash (from WIRING.md; do not skip)
Bring-up steps 1-5 of WIRING.md section 7 are done (continuity, polarity, pull-up decision 4.3). Flash with **J1 open**, USB **data** cable into the SuperMini only, TP4056 USB unplugged (2.3).
If the port does not appear or it boot-loops: hold BOOT, tap RESET, release BOOT.

## 4. Steps, expected serial lines, pass/fail
**Step 0 (do this first, before anything else in this table): the build with the v1 defaults (section 2) succeeds ("Project build complete") and then the S1 line appears on the serial port.**
Nothing else in this document is meaningful until both hold. If the build fails, stop and send the full build log to Mira; nothing was flashed, so it is a software finding, not a hardware fault.
CI compiles the v1 option (PR #120), so a build failure here points to your setup or a difference from CI: report it, do not work around it.
**If S1 shows no output, report it as a USB console finding to Mira (`CONFIG_ESP_CONSOLE_USB_SERIAL_JTAG` on the SuperMini is UNVERIFIED), not as a hardware fault.** Send the `idf.py monitor` header and the `lsusb`/Device Manager entry.

Flash and watch: `idf.py -p <PORT> flash monitor | tee v1-run1.log` (Ctrl+] exits). If you built into `build-v1/` as in `firmware/DEV_GUIDE.md` section 3.2, use the full command there (it adds `-B build-v1 -DSDKCONFIG=sdkconfig.v1`); the short form only finds the default `build/`. Keep the whole log; attach it with the readings table.
All sample lines below are **format examples with invented numbers, not measurements.**

| # | Step | Expected serial line / reading | PASS | FAIL (what to send) |
|---|---|---|---|---|
| S1 | Boot | one line `I (<ms>) plant_monitor: NWBENCH start board=v1_supermini wake=1 cal_dry=2800 cal_wet=1200 divider=100000/100000 (CALIBRATION IS A PLACEHOLDER ...)`. **No** `NWSETUP` line. | line present with `board=v1_supermini` and `divider=100000/100000` | no output at all: **USB console finding for Mira, not a hardware fault** (see step 0); check port/cable/BOOT-RESET, then report the `idf.py monitor` header and `lsusb`/Device Manager entry. `board=devkit`: wrong build, redo section 2 from a clean `sdkconfig` |
| S2 | Five reading lines | `NWBENCH wake=1 i=0 soil_raw=2000 soil_pct=50.0 soil_flags=0x00 temp_c=23.45 rh_pct=41.25 lux=250.0 lux_raw=300 vbat_mv=5000 vbat_adc_mv=2500 vbat_plausible=0 divider_na=50000 err=soil:0,aht:0,bh:0,bat:0` for i=0..4. One line takes about 4-5 s (sensor time plus a 2 s pause; derived from the driver constants, UNVERIFIED on the board) | 5 lines, `err=soil:0,aht:0,bh:0,bat:0` in all | any non-zero `err=`: `-1` chip/ADC call failed, `-2` AHT20 CRC, `-3` AHT20 busy, `-5` no ADC calibration (soil/battery), `-6` not supported. `aht:-1` = no ACK from 0x38; `bh:-1` = no ACK from 0x23. These two lines are the I2C scan: a missing address shows as -1 (WIRING.md 7 step 7: only 0x23 missing = check ADDR W09 and pin order; both missing = W13-W18 and the pull-ups, 4.3). Send the log |
| S3 | USB battery value | on USB with J1 open the divider sees USB 5 V (WIRING.md 2.7): expect `vbat_adc_mv` about 2500 (2630 at 5.25 V), `vbat_mv` about 5000 and `vbat_plausible=0` | record only: this is **not** a battery reading. `vbat_plausible=0` here is correct | the bench loop only prints this value (`main.c`; no sleep, report or Wi-Fi decision runs in the bench app). If `err=...bat:-5`: ADC has no eFuse calibration, send the `nw_hal` warning line from the log |
| S4 | Soil, AOUT in air (multimeter first, WIRING.md 4.5 and 7 step 8) | multimeter on J3 AOUT to GND, probe in dry air, GPIO3 high (during a reading line) | AOUT **at or below about 2.4 V**: continue | **AOUT above about 2.4 V in air: STOP the soil steps and report to Emil/Mira with the voltage (A-094 item 7: the ADC may clip the dry end).** Do not add a divider or change attenuation at the bench. Also report `soil_flags` containing `0x04` (raw 0 or 4095 = rail) |
| S5 | Soil, air then water | record `soil_raw` for 5 lines in air, then probe in water to the marked line (not above), 5 lines. Multimeter AOUT at the same time | raw in air and raw in water are both recorded with the multimeter volts, and they differ by **500 counts or more** (issue #68 step A4, the governing limit). Note: the firmware itself uses 50 counts (`NW_SOIL_MIN_SPAN_COUNTS`) only as a sanity constant for its own calibration check; it is not the pass limit | record the numbers anyway. Calibration is **not** set from this run: send the table, Mira sets `PLANT_SOIL_DRY_RAW/WET_RAW` |
| S6 | Light, temperature, humidity | cover and uncover the BH1750 with a hand; breathe on the AHT20 for 3 s; room thermometer reading noted | `lux` drops when covered and rises when uncovered; `rh_pct` rises at least 10 %RH within 10 s of breathing | no change: send the log. Absolute accuracy is not judged here |
| S7 | Soil supply in sleep (NFR-12 function check) | after the 5th line: `NWBENCH sleep s=60 (IO3 must read 0 V now)`. Meter on J3 VCC to GND at once and during the 60 s | J3 VCC (GPIO3) at most **0.05 V** during sleep (issue #68 step A5, the governing limit) | J3 VCC above 0.05 V: FAIL for NFR-12, report with the reading. Not a current measurement |
| S8 | Wake | after about 60 s: new `NWBENCH start board=v1_supermini wake=2 ...`, then lines again with `wake=2`. With USB Serial/JTAG the USB port may drop during deep sleep and come back: re-run `idf.py monitor` if it hangs (UNVERIFIED which of the two happens) | `wake=2` appears | no wake: report; a restart of `monitor` first |
| S9 | Battery read on the cell (WIRING.md 7 step 9) | **not run in this bench**: there is no serial without USB, and USB with J1 closed is forbidden (WIRING.md 2.3 step 7). The ADC-vs-multimeter battery comparison needs a separate procedure from Mira (not written) | write "not run" | - |

Result table Peter returns (one row per step): step, PASS / FAIL / not run, the line or reading, date and time, USB cable used. Anything not run is written "not run", never left blank.

## 5. What this does not cover
No Wi-Fi, no report, no BLE, no OTA, no edge AI (A-102), no current measurement, no cell-voltage reading from serial (S9). The soil percentage is meaningless until calibrated.
Not proven by the author: that the build compiles for the SuperMini with these defaults, that the console choice prints on the USB port, the loop timing, the ADC behaviour above 2.4 V.

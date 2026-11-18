# Plant Monitor firmware: developer guide for new joiners

Task 4.F6 · Author: Mira (Firmware + Edge AI) · Written 2026-11-17 · Audience: someone who has **never used ESP-IDF** (first reader: Peter, work order WO-005 = [issue #68](https://github.com/nilwerk/nilwerk-lab/issues/68)).

**How to read the labels in this guide.**
Everything marked *(repo)* was read from a file in this repository and the file is named next to it.
**UNVERIFIED** means nobody has run or checked it on a real machine or board (the author works in a sandbox with no ESP-IDF toolchain and no hardware).
*(Espressif docs)* means general ESP-IDF knowledge from Espressif's public documentation, not checked in this repo. If one of these turns out wrong on your machine, tell us in the issue: that is a useful result, not your mistake.

**Honest status of the firmware today.** It compiles in CI (ESP-IDF v5.4, ESP32-C3) and its pure-C logic passes the PC tests. **It has never run on a board.** WO-005 is the first time it touches hardware. A FAIL with a good log is a useful result.

---

## Quick start (12 steps)

**Which shell?** Linux/macOS: any normal terminal, after you load ESP-IDF (step 3). **Windows: use the "ESP-IDF 5.4 PowerShell" (or "ESP-IDF 5.4 CMD") shortcut from the Start menu for everything in this guide.** Do not chain commands with `&&` in Windows PowerShell 5.1: it does not know `&&` (PowerShell 7 does). This guide therefore gives one command per line wherever it matters. *(PowerShell 5.1 behaviour: general knowledge, UNVERIFIED with ESP-IDF here.)*

1. **Get access to the repo.** The repository is private. Your GitHub account must be added as a collaborator: ask Nora (section 10) if `git clone` says "not found" or asks for a password you do not have. Sign in with git when it asks (browser sign-in or a personal access token; never put a token into a tracked file).
2. Install **git**, **Python 3** and **ESP-IDF v5.4** for the ESP32-C3 (section 2; on Linux first the package list in 2.2).
3. Open the ESP-IDF terminal **every time you work** (section 2.5): Windows "ESP-IDF 5.4 PowerShell"; Linux/macOS `. ~/esp/esp-idf/export.sh`. Check: `idf.py --version`.
4. Clone the repo **once** and go into the firmware folder (section 2.6). On Linux/macOS first run `cd ~` (after step 2 your shell sits in `~/esp/esp-idf`; do not clone inside that folder). From here on "**the firmware folder**" means `nilwerk-lab/projects/plant-monitor/firmware`; every command below starts there, so do not `cd` into it again.
5. **No hardware yet?** From the firmware folder run the PC tests (section 5.1: three commands, one per line). They show 19 of 19 passed.
6. Decide your board: **DevKitM-1** (section 3.1) or **v1 SuperMini perfboard** (section 3.2).
7. **Wire the board first, before you flash.** DevKit: issue #68 steps 2 and 3 and [`hardware/devkit-order-list.md`](../hardware/devkit-order-list.md). SuperMini: [`v1/WIRING.md`](../v1/WIRING.md) section 7. Do not skip it: **on a bare board (nothing wired) the firmware still boots and prints lines, but with `err=...aht:-1,bh:-1` (sensors do not answer), `soil` and `bat` readings are meaningless noise.** That output means "not wired", not "firmware broken".
8. **Build.** DevKit: `idf.py set-target esp32c3`, then `idf.py menuconfig` and **switch off "Run the BLE setup flow at boot"** (otherwise you see no sensor lines, see 3.1), then `idf.py build`. SuperMini: the v1 build command from 3.2.
9. **Flash and monitor** (plug in USB first, find the port with 4.3). DevKit: `idf.py -p PORT flash monitor`. SuperMini: the full command per OS is in 3.2 (it needs `-B build-v1`, `-DSDKCONFIG=sdkconfig.v1` and `-p PORT`).
10. Look for `NWBENCH start board=...` and then five `NWBENCH wake=1 i=0 ...` lines (section 6).
11. Check the `err=` field is all zeros and the sensors react (breath, hand over the light sensor).
12. Leave with `Ctrl+]`, save the log, report in the issue (section 9).

### First-day checklist
- [ ] git, Python 3 and ESP-IDF v5.4 installed; `idf.py --version` prints a v5.4 version
- [ ] repo access works (you are a collaborator), repo cloned; you know which folder you are in (the firmware folder, `projects/plant-monitor/firmware`)
- [ ] the board is wired (step 7) before the first flash
- [ ] host tests: 19 of 19 passed (section 5), log saved
- [ ] board chosen and the matching config built: "Project build complete", last 30 lines saved
- [ ] USB cable is a **data** cable; port found; flash finished without error
- [ ] `NWBENCH start` line seen with the right `board=`
- [ ] five reading lines with `err=soil:0,aht:0,bh:0,bat:0`
- [ ] full session log saved to a text file
- [ ] no secret (URL, token, password) typed into a tracked file (`git status` shows nothing you did not intend)
- [ ] result posted in the issue (section 9)

---

## 1. What the firmware does and where things are

**What it does today.** `main/main.c` is a *sensor bench application* (task 4.F1, FR-D01). After boot it prints one `NWBENCH ...` line about every 4 to 5 s (about 2.4 s of sensor time from the driver constants plus a 2 s pause in `main.c`; UNVERIFIED on the board). Issue #68 says every 2 s; expect 4 to 5 s, that is not a fault with the five readings (soil moisture, air temperature, air humidity, light, battery voltage). After 5 lines it switches the soil probe supply (GPIO3) off, prints `NWBENCH sleep s=60 ...`, goes into deep sleep for 60 s, wakes up and repeats. *(repo: `main/main.c`)*

**Repository layout** (everything below `projects/plant-monitor/`):

| Path | What is in it |
|---|---|
| [`firmware/main/`](main/) | `main.c` (the bench app), `board.h` (pin map per board), `Kconfig.projbuild` (the "Plant Monitor" menu in `menuconfig`) |
| [`firmware/components/sensors/`](components/sensors/) | Drivers for AHT20 (temperature, humidity), BH1750 (light), soil probe (ADC), battery divider, ESP32 hardware layer `hal_esp32.c` |
| [`firmware/components/provisioning/`](components/provisioning/) | BLE setup and device claim (task 4.F2); logic in pure C, ESP-IDF glue in `nw_prov_idf.c` |
| [`firmware/components/report/`](components/report/), [`storage/`](components/storage/), [`power/`](components/power/), [`upload/`](components/upload/) | Report payload, sample ring buffer, deep-sleep decision, hourly upload decision (task 4.F3). Pure C with PC tests. **Not called from `main.c` yet** (section 7) |
| [`firmware/test/host/`](test/host/) | PC tests (no ESP-IDF, no board needed): C unit tests plus Python contract checks, started with `cmake`/`ctest` |
| [`firmware/sdkconfig.defaults`](sdkconfig.defaults) | Default build settings for every board (BLE on, 4 MB flash, single large app partition) |
| [`firmware/sdkconfig.defaults.v1`](sdkconfig.defaults.v1) | Extra settings for the v1 SuperMini perfboard |
| [`v1/`](../v1/) | The v1 perfboard demo: [`WIRING.md`](../v1/WIRING.md) (parts, wiring, bring-up checklist), [`FIRMWARE-BENCH.md`](../v1/FIRMWARE-BENCH.md) (build, expected serial output, pass/fail) |
| [`tests/procedures/`](../tests/procedures/) | Bench test procedures written by agents for people with hardware |
| [`docs/work-orders/`](../docs/work-orders/) | Drafts of the work orders (WO-firmware-4.F1 is the DevKit bench test that became WO-005) |
| [`hardware/devkit-order-list.md`](../hardware/devkit-order-list.md) | What the DevKit parts are and the wiring warnings |
| [`docs/interfaces/`](../docs/interfaces/) | Contracts: report schema, OpenAPI, BLE provisioning ([`ble-provisioning.md`](../docs/interfaces/ble-provisioning.md)) |

**Two boards, one codebase.** *(repo: `main/Kconfig.projbuild`, `main/board.h`)*

| Option | Board | Console (where `NWBENCH` appears) |
|---|---|---|
| `PLANT_BOARD_DEVKIT` (default) | ESP32-C3-DevKitM-1 + AHT20 + BH1750 + analog soil probe | UART port via the USB-UART chip (ESP-IDF default console; the repo sets nothing else for it) |
| `PLANT_BOARD_V1_SUPERMINI` | v1 perfboard: ESP32-C3 SuperMini + same sensors | The chip's native USB (`CONFIG_ESP_CONSOLE_USB_SERIAL_JTAG=y`); the SuperMini has no UART chip |
| `PLANT_BOARD_CUSTOM` | The future Plant Monitor PCB | Soil reading not implemented yet (returns "unsupported", `soil:-6`). Not for the bench |

Both bench boards use the same GPIOs: SDA = GPIO6, SCL = GPIO7, soil power = GPIO3, soil analog out = GPIO4, battery divider middle = GPIO0. **`board.h` is the truth**: if any document disagrees with it, stop and ask. *(repo: `main/board.h`)*

---

## 2. Prerequisites and ESP-IDF install

### 2.1 Version
**ESP-IDF v5.4**, target `esp32c3`. This is what CI builds with: `esp_idf_version: v5.4` in [`.github/workflows/ci.yml`](../../../.github/workflows/ci.yml) (job `firmware`). Use v5.4 (any v5.4.x) so your build matches CI. Exact patch version used by CI: UNVERIFIED (the action takes `v5.4`).

### 2.2 What to install

| Tool | Why | Windows | macOS | Linux (Debian/Ubuntu) |
|---|---|---|---|---|
| git | get the repo and ESP-IDF | git-scm.com installer | `xcode-select --install` | `sudo apt install git` |
| Python 3 | ESP-IDF tools run on it; PC test scripts | ESP-IDF installer brings its own *(Espressif docs)* | python.org or Homebrew | `sudo apt install python3 python3-venv python3-pip` |
| cmake, ninja, C compiler | build; the PC tests need `cmake` + `gcc`/`clang` | installed by the ESP-IDF installer *(for the firmware build)*. PC tests: see 5.3 | `brew install cmake ninja` | `sudo apt install cmake ninja-build gcc` |
| USB driver | to see the board as a serial port | see 2.4 | usually none needed | usually none needed; permissions, see 4.3 |

**Linux: full prerequisite list.** Espressif's official list for ESP-IDF v5.4 on Debian/Ubuntu *(from Espressif docs, UNVERIFIED here: not run by the author; the exact list can differ per release, the Espressif guide linked in 2.3 is the reference)*:
```bash
sudo apt-get install git wget flex bison gperf python3 python3-venv cmake ninja-build ccache libffi-dev libssl-dev dfu-util libusb-1.0-0
```
For the PC tests (section 5) you additionally need a C compiler: `sudo apt install gcc`.

Exact Python minimum for ESP-IDF 5.4: UNVERIFIED; the install script tells you if yours is too old.

### 2.3 Install ESP-IDF step by step
Official guide (the same link as in issue #68): <https://docs.espressif.com/projects/esp-idf/en/v5.4/esp32c3/get-started/index.html>. The steps below follow it *(Espressif docs; not run by the author)*.

**Where ESP-IDF lives.** Linux/macOS: the steps below clone it to `~/esp/esp-idf` (your home folder). Windows: the installer asks for a location; the default is under `C:\Espressif` *(Espressif docs, UNVERIFIED; read the path on the installer page and write it down)*. This is separate from the `nilwerk-lab` repo, which you clone in 2.6.

**Linux and macOS** (macOS also needs the prerequisites from Espressif's guide: UNVERIFIED here)
```bash
mkdir -p ~/esp
cd ~/esp
git clone -b v5.4 --recursive https://github.com/espressif/esp-idf.git
cd esp-idf
./install.sh esp32c3          # downloads the RISC-V compiler and Python packages, takes a while
. ./export.sh                 # loads ESP-IDF into THIS terminal (see 2.5)
idf.py --version              # should print ESP-IDF v5.4...
```

**Windows**
1. Download the **ESP-IDF Tools Installer** from the Espressif guide above (online or offline installer), choose **v5.4**, accept the defaults, select target ESP32-C3 if asked.
2. Start the shortcut **"ESP-IDF 5.4 PowerShell"** (or "ESP-IDF 5.4 CMD") from the Start menu. Use this terminal for every `idf.py` command: a normal terminal does not know `idf.py`.
3. Check: `idf.py --version`.
4. Keep paths short and without spaces (for example `C:\work\nilwerk-lab`): very long paths are a known Windows build problem *(Espressif docs, UNVERIFIED here)*.

### 2.5 Open the ESP-IDF shell, every time
`idf.py` only exists in a terminal where ESP-IDF was loaded. A new terminal window does **not** have it.
- **Linux/macOS:** in each new terminal run `. ~/esp/esp-idf/export.sh` (note the leading dot and space). Then `idf.py --version`.
- **Windows:** start "ESP-IDF 5.4 PowerShell" or "ESP-IDF 5.4 CMD" from the Start menu. Then `idf.py --version`.
- If `idf.py` is "not found" or "not recognised": you are in the wrong terminal (section 8).

### 2.6 Clone the repo (once) and set the target
The repo is private: your GitHub account must be a collaborator (ask Nora). Then, once, in a projects folder you like (Windows: a short path, see above). **Linux/macOS: run `cd ~` first** (or `cd` to your projects folder): after 2.4 your shell is still inside `~/esp/esp-idf`, and the repo must **not** be cloned inside the esp-idf folder.
```bash
git clone https://github.com/nilwerk/nilwerk-lab.git
cd nilwerk-lab/projects/plant-monitor/firmware
```
(Two lines, not chained with `&&`, so they also work in Windows PowerShell 5.1. Windows can also use backslashes; forward slashes work in PowerShell and CMD for `cd`.) If you already did this in Quick start step 4, do not repeat it. From the firmware folder:
```bash
idf.py set-target esp32c3
```
`set-target` tells ESP-IDF which chip to build for. It **deletes and recreates** `sdkconfig` and `build/`, so run it before you change any setting, not after. (SuperMini: skip it; 3.2 sets the target in its own command.)

### 2.4 USB and drivers
- **DevKitM-1:** has a USB-to-serial chip (UART port). The repo only says "USB-UART" (`hardware/devkit-order-list.md`). Which chip it is and which driver Windows needs: UNVERIFIED; Espressif's guide for the board lists it. If Windows shows an unknown device, install the driver named there.
- **SuperMini:** no UART chip. The ESP32-C3 shows up directly over USB (USB Serial/JTAG). Windows 10/11 and Linux normally need no driver *(Espressif docs, UNVERIFIED on this board)*.
- **Cable:** it must be a **data** cable. A charge-only cable gives no port at all (`v1/WIRING.md` section 2.3).

---

## 3. Pick the board configuration

Settings come in layers: `sdkconfig.defaults` (all boards), then optional extra files, then your own changes in `menuconfig`. **The defaults files only seed a *new* `sdkconfig`.** If an `sdkconfig` already exists from another build, the new defaults are silently ignored and you build the old board again. That is why CI uses a separate build folder and a separate settings file for v1.

### 3.1 DevKitM-1 (default)

From the firmware folder:
```bash
idf.py set-target esp32c3
idf.py menuconfig
```
In `menuconfig`: **Plant Monitor** menu, then
- **"Run the BLE setup flow at boot (task 4.F2)": switch OFF** (space bar toggles, `S` saves, `Q` quits).
- Later (WO-005 Step 8.4) the two soil calibration numbers are in the same menu.

```bash
idf.py build
```
PASS: the output ends with `Project build complete`.

**Why switch the setup flow off (read this, it matters).** The default for that option is ON. With it on, a never-provisioned unit starts the BLE setup, finds no per-unit security keys, closes setup, prints `NWSETUP closed, never provisioned: deep sleep with no timer; reset to try again` and sleeps without ever reading a sensor (`main/main.c`, `components/provisioning/src/nw_prov_idf.c`). So with the plain default build you would see **no `NWBENCH` lines**. This is read from the source, UNVERIFIED on hardware. The v1 defaults file already switches it off; the DevKit has no such file, so you do it by hand. Note: issue #68 step 1.3 lists only `idf.py set-target esp32c3` and `idf.py build`; do the extra `menuconfig` step from this guide as well.

Alternative without the menu (bash only; on Windows use a text editor, because PowerShell `echo` writes UTF-16 which ESP-IDF cannot read; this is general PowerShell behaviour, noted by the author, not tested with ESP-IDF here):
```bash
printf 'CONFIG_PLANT_SETUP_FLOW=n\n' > sdkconfig.defaults.local     # git-ignored file, see section 7
idf.py -D SDKCONFIG_DEFAULTS="sdkconfig.defaults;sdkconfig.defaults.local" set-target esp32c3
idf.py build
```

### 3.2 v1 SuperMini perfboard

This is exactly what CI runs for v1 (`ci.yml`, second build step of job `firmware`), plus nothing else. Separate build folder `build-v1/` and separate settings file `sdkconfig.v1` (both git-ignored). From the firmware folder:

**Build** (Linux/macOS/CMD/bash; one line):
```bash
idf.py -B build-v1 -DIDF_TARGET=esp32c3 -DSDKCONFIG=sdkconfig.v1 -DSDKCONFIG_DEFAULTS="sdkconfig.defaults;sdkconfig.defaults.v1" build size
```
**Windows PowerShell 5.1:** quote the whole option so the `;` is not read as a command separator *(UNVERIFIED in PowerShell 5.1; this is the CI line, adapted)*:
```powershell
idf.py -B build-v1 -DIDF_TARGET=esp32c3 -DSDKCONFIG=sdkconfig.v1 "-DSDKCONFIG_DEFAULTS=sdkconfig.defaults;sdkconfig.defaults.v1" build size
```
**Flash and monitor**, the full command (replace the port, section 4.3). The **build part** is what CI runs (built in CI, never on a board). **UNVERIFIED (not run by anybody):** passing the `-DSDKCONFIG=...` and `-B build-v1` options together with `flash monitor`, the port names, and the whole flash step on the SuperMini.

| OS | Full command (one line, from the firmware folder) |
|---|---|
| Linux | `idf.py -B build-v1 -DSDKCONFIG=sdkconfig.v1 -p /dev/ttyACM0 flash monitor` |
| macOS | `idf.py -B build-v1 -DSDKCONFIG=sdkconfig.v1 -p /dev/cu.usbmodem101 flash monitor` |
| Windows (ESP-IDF PowerShell or CMD) | `idf.py -B build-v1 -DSDKCONFIG=sdkconfig.v1 -p COM5 flash monitor` |

The port names (`/dev/ttyACM0`, `/dev/cu.usbmodem101`, `COM5`) are typical examples, not facts about your machine (UNVERIFIED): use the port you found in 4.3. If `-B build-v1` flashing fails with a "not built" message, run the build line above first, then repeat.

Prove that the v1 option was really selected (CI does the same):
```bash
grep '^CONFIG_PLANT_BOARD_V1_SUPERMINI=y' sdkconfig.v1        # Windows PowerShell: Select-String '^CONFIG_PLANT_BOARD_V1_SUPERMINI=y' sdkconfig.v1
```
It must print that one line. No line means you built the wrong board.

What `sdkconfig.defaults.v1` switches (repo): board option `PLANT_BOARD_V1_SUPERMINI`, console on the native USB, **BLE setup flow off**, bench sleep cycle on.

Every later `idf.py` call for this board needs the same two options so it finds the right folder and settings, for example `idf.py -B build-v1 -DSDKCONFIG=sdkconfig.v1 menuconfig`. Running these later calls this way (not only `build`): UNVERIFIED, not run.

> `v1/FIRMWARE-BENCH.md` section 2 shows a shorter variant that builds in the default `build/` folder and says "delete `sdkconfig` first". Both work in principle; use the CI form above, it cannot silently reuse an old `sdkconfig`.

### 3.3 Where the board name shows up
The first serial line says `board=devkit` or `board=v1_supermini` (`NW_BOARD_NAME` in `board.h`). If it is not the board you meant: wrong config, see the troubleshooting table.

---

## 4. Build, flash, monitor

### 4.1 Commands (DevKit shown; for v1 add `-B build-v1 -DSDKCONFIG=sdkconfig.v1`)
```bash
idf.py build                          # compile
idf.py size                           # flash/RAM usage report
idf.py -p <PORT> flash                # write the program to the board
idf.py -p <PORT> monitor              # show serial output; leave with Ctrl+]
idf.py -p <PORT> flash monitor        # both in one go
idf.py -p <PORT> flash monitor | tee run1.log     # same, and save the session in run1.log
idf.py fullclean                      # wipe the build folder if something is badly stuck (keeps your sdkconfig)
```
Replace `<PORT>` with the real port, for example `COM5` or `/dev/ttyUSB0`.
`flash monitor | tee ...` saving a clean log: UNVERIFIED (monitor may need a real terminal; if it complains, run `idf.py monitor` in the terminal and copy the output, or use your terminal program's log function).

### 4.2 SuperMini: download mode (BOOT / RESET)
Normally flashing just works. If the port is missing or the board boot-loops *(repo: `v1/WIRING.md` section 2.3 step 5)*:
1. Hold the **BOOT** button (GPIO9).
2. Tap **RESET** once.
3. Release **BOOT**.
4. Run the flash command again.

The port name may change while the board is in download mode and again after the flash: UNVERIFIED, look again.
**Safety (v1 perfboard):** flash with the battery jumper **J1 open**, USB data cable into the **SuperMini only**, and never plug USB into the SuperMini with J1 closed. Details: [`v1/WIRING.md`](../v1/WIRING.md) section 2.3. On a bare DevKit with only USB nothing of this applies.

DevKitM-1: the BOOT/RESET dance is not normally needed; the flash tool resets the board itself *(Espressif docs)*. If flashing fails, hold BOOT while tapping RESET, same as above.

### 4.3 Find the serial port

| OS | How to look | Typical name |
|---|---|---|
| Windows | Device Manager, section "Ports (COM & LPT)"; unplug and replug and see which entry appears | `COM3`, `COM5` ... |
| Linux | `ls /dev/ttyUSB* /dev/ttyACM*` before and after plugging in; `dmesg \| tail` shows the name | DevKit (UART chip): usually `/dev/ttyUSB0`; SuperMini (native USB): usually `/dev/ttyACM0` |
| macOS | `ls /dev/cu.*` before and after plugging in | `/dev/cu.usbserial-...` or `/dev/cu.usbmodem...` |

The typical names are general knowledge *(UNVERIFIED on these boards)*.
- **Linux "permission denied":** add yourself to the serial group, then log out and in: `sudo usermod -aG dialout $USER` (on some distributions the group is `uucp`).
- **Port busy:** only one program may hold the port. Close other monitors (a second terminal with `idf.py monitor`, Arduino IDE, PuTTY, a serial plotter) before you flash.
- **SuperMini and deep sleep:** the native USB port can disappear during the 60 s sleep and come back; if the monitor hangs, start it again (`v1/FIRMWARE-BENCH.md` step S8, UNVERIFIED which of the two happens).

---

## 5. Host tests (no hardware, no ESP-IDF)

These run the pure-C logic (sensor drivers, provisioning, report, sleep, upload decisions) and several Python contract checks on your PC. They are exactly the commands CI runs (`ci.yml`, step "Host unit tests"). Run them first: they prove your checkout is healthy.

### 5.1 Commands
From the firmware folder (one command per line; no `&&`, so Windows PowerShell 5.1 can run them too):
```bash
cmake -S test/host -B build-host
cmake --build build-host
ctest --test-dir build-host --output-on-failure
```
Needs `cmake`, a C compiler (gcc or clang) and Python 3 on the PATH. `build-host/` is a build folder: do not commit it.

### 5.2 What a good run looks like
Real output of the author's run on 2026-11-17 (Linux, cmake 3.28.3, gcc 13.3.0, Python 3.11.18; shortened to the summary):
```
19/19 Test #19: api_url_check_selftest ...........   Passed    0.03 sec

100% tests passed, 0 tests failed out of 19

Total Test time (real) =  23.01 sec
```
The 19 tests: `board_v1_unit`, `glue_unit`, `sensors_unit`, `provisioning_unit`, `report_buffer_unit`, `sleep_decision_unit`, `upload_unit`, `report_contract_drift`, `board_pins_cite_pinmap`, `provisioning_contract`, `provisioning_mutation_checks`, `mutation_checks`, `upload_contract`, `upload_contract_selftest`, `upload_mutation_checks`, `board_v1_matches_wiring`, `board_v1_check_selftest`, `api_url_not_committed`, `api_url_check_selftest`. Any "Failed" line: copy the whole output into the issue.

### 5.3 Per OS
- **Linux:** works as above (the tested case).
- **macOS:** same commands; clang instead of gcc. UNVERIFIED (not run by the author).
- **Windows:** the tests use gcc/clang options and Python scripts that call the C compiler; the CMake file skips the sanitizer flags for MSVC. The easiest path is **WSL2** (Ubuntu) and then the Linux commands. Running natively on Windows: UNVERIFIED. If you cannot get the host tests to run on Windows, say so in the issue and continue with the board; the host tests are a bonus, not a blocker for WO-005.

---

## 6. First-run bench check

You need the wiring first: WO-005 steps 2 and 3 (DevKit) or [`v1/WIRING.md`](../v1/WIRING.md) section 7 (v1 perfboard). **Do not duplicate or reinterpret them here**; follow the issue/WIRING exactly. Pin numbers come from `board.h`; if the issue and `board.h` disagree, `board.h` wins and you ask.

### 6.1 What you should see (format examples; the numbers are invented, NOT measurements)

Right after the boot messages of ESP-IDF, one start line:
```
I (<ms>) plant_monitor: NWBENCH start board=devkit wake=1 cal_dry=2800 cal_wet=1200 divider=100000/100000 (CALIBRATION IS A PLACEHOLDER UNTIL SET ON THE BENCH)
```
(SuperMini: `board=v1_supermini`.) On the v1 build there must be **no** `NWSETUP` line.

Then five reading lines, one every few seconds (`i=0` ... `i=4`):
```
NWBENCH wake=1 i=0 soil_raw=2000 soil_pct=50.0 soil_flags=0x00 temp_c=23.45 rh_pct=41.25 lux=250.0 lux_raw=300 vbat_mv=3990 vbat_adc_mv=1995 vbat_plausible=1 divider_na=19950 err=soil:0,aht:0,bh:0,bat:0
```
Then:
```
NWBENCH sleep s=60 (IO3 must read 0 V now)
```
About 60 s later the board restarts and prints `NWBENCH start ... wake=2 ...` and the lines again with `wake=2`.

### 6.2 What each field means

| Field | Sensor | Healthy looks like | Source |
|---|---|---|---|
| `soil_raw` | capacitive probe, 12-bit ADC counts | a number between 0 and 4095; **higher in dry air, lower in water**; steady within about 30 counts | issue #68 step 8 |
| `soil_pct`, `soil_flags` | calibrated 0 to 100 % | meaningless until you set the dry/wet numbers (defaults 2800/1200 are placeholders); `soil_flags` `0x01`/`0x02` = clamped at an end, `0x04` = raw 0 or 4095 (stuck at a rail: report it) | issue #68 step 8.5, `v1/FIRMWARE-BENCH.md` S4 |
| `temp_c`, `rh_pct` | AHT20 | plausible room values; breath raises `rh_pct` by 10 %RH or more within 10 s; a finger nearby raises `temp_c` by 0.5 degC or more in 20 s | issue #68 step 6 |
| `lux`, `lux_raw` | BH1750 | room light: `lux_raw` is not 65535 and `lux` above 0; covered: below 5; torch 5 cm away: above 100 | issue #68 step 7 |
| `vbat_mv`, `vbat_adc_mv`, `vbat_plausible` | battery divider on GPIO0 | with a cell: within 50 mV of your multimeter; `vbat_plausible=1` for 3.0 to 4.25 V. **On USB only (v1, J1 open) the divider sees USB 5 V: about 5000 mV and `vbat_plausible=0` is correct, it is not a battery reading** | issue #68 step 10, `v1/FIRMWARE-BENCH.md` S3 |
| `divider_na` | current through the bench divider | informational | `main.c` |
| `err=soil:..,aht:..,bh:..,bat:..` | result of each sensor read | **all 0** | codes below |

`err` codes (`components/sensors/include/nw_hal.h`): `0` fine, `-1` the chip or ADC did not answer (wiring: SDA/SCL swapped, wrong supply pin), `-2` AHT20 CRC error, `-3` AHT20 busy, `-5` no calibration (the chip's ADC has no calibration data, or soil dry equals wet), `-6` not supported (soil on the custom board).

### 6.3 Pass/fail table for the first run

| # | Check | PASS | FAIL: what to do |
|---|---|---|---|
| 1 | Build | `Project build complete` | send the last 30 lines of the output; nothing was flashed, so this is a software finding |
| 2 | Boot line | `NWBENCH start` with the expected `board=` | no output at all: troubleshooting table; wrong `board=`: section 3 |
| 3 | `err=` in 5 consecutive lines | `soil:0,aht:0,bh:0,bat:0` in all 5 | note which one is non-zero; `aht:-1` or `bh:-1` = wiring |
| 4 | Sensors react | humidity up on breath, lux down when covered, soil raw differs air vs water by 500 counts or more **and** the 5 readings of each state differ by at most 30 counts (spread) (issue #68 step 8.3 and A4) | write the numbers down anyway; never change a number to make it fit |
| 5 | Sleep and wake | `NWBENCH sleep` then `wake=2` after about 60 s | no wake: restart the monitor first, then report |
| 6 | GPIO3 in sleep (multimeter) | 0.00 V (at most 0.05 V) in **2 different sleep cycles**, measure again after the next wake (issue #68 step 9 and A5) | write the voltage down |

The authoritative step lists and limits are in **issue #68** (DevKit, steps 1 to 11, with the result table you must fill) and in [`v1/FIRMWARE-BENCH.md`](../v1/FIRMWARE-BENCH.md) section 4 (SuperMini, steps S1 to S9). Use those for the actual result; this table is only for a quick first look. The limits are the same for both boards: soil raw air vs water differs by **500 counts or more**, with the 5 readings of each state within **30 counts** of each other (source: issue #68 step 8.3 and A4; the 30-count limit is set there); GPIO3 in sleep **at most 0.05 V**, checked in **2 different sleep cycles** (source: issue #68 step 9 and A5; the 2-cycle limit is set there). The 50 counts in the firmware (`NW_SOIL_MIN_SPAN_COUNTS`) is only an internal sanity constant, not a pass limit.

---

## 7. API URL, tokens, BLE setup: what exists, what does not

### 7.1 Rules for secrets (A-082)
- **Never commit a secret.** No passwords, Wi-Fi credentials, tokens, API keys, real cloud URLs, in any tracked file, issue text, log you paste or screenshot. *(TEAM.md section 5)*
- `PLANT_API_BASE_URL` is a **build setting**. Its committed default is the placeholder `https://api.invalid`, which never resolves. **The real URL comes from Arsany** (A-082) and is set only on your own machine. You do **not** need it for WO-005: the bench app makes no network call.
- To set it later, locally only, either:
  1. `idf.py menuconfig` then Plant Monitor then "Cloud API base URL" (stored in the git-ignored `sdkconfig`); or
  2. a file `firmware/sdkconfig.defaults.local` (git-ignored, never `git add -f`) with one line of the form `CONFIG_PLANT_API_BASE_URL="https://api.invalid"` where you replace the value with the one Arsany gives you, and add that file as a third entry in `SDKCONFIG_DEFAULTS`.
  Format: https, no trailing slash.
- A PC test (`api_url_not_committed`) fails when a real URL is found in a tracked firmware file. Before every commit run `git status` and look at what you are adding.
- Per-device tokens are **not** build settings: they come from provisioning at run time.

### 7.2 BLE setup and claim flow (summary)
Code exists (task 4.F2) and is **NOT RUN ON HARDWARE**. In short *(repo: `docs/interfaces/ble-provisioning.md`, `components/provisioning/include/nw_prov.h`)*:
1. First boot, a button hold of 3 s (setup) or 10 s (factory reset), or after a reset puts the unit in setup mode. BLE is on only then.
2. The phone app finds `NW-<last 6 hex of hw_id>` and opens an encrypted session (protocomm security 2; the proof-of-possession code is on the unit's label).
3. The app sends Wi-Fi name and password, then a device name and a one-time claim token.
4. The unit joins Wi-Fi and calls `POST /device-claim` on the cloud; the answer contains a per-device token stored on the unit.
5. Setup ends after 5 wrong handshakes or 5 minutes.
It needs a per-unit security-2 salt and verifier stored in NVS namespace `nw_sec2`, otherwise BLE stays off (fail closed). Since task 4.F2b the repo has the tool (`firmware/tools/nw_sec2_gen.py`, PC only, tested on the PC) and the bench procedure `tests/procedures/4.F2b-sec2-provisioning.md` (build with `sdkconfig.defaults.setup` last in `SDKCONFIG_DEFAULTS`, generate per-unit data outside the repo, flash the NVS image). **None of the device steps has been run (UNVERIFIED)**; the bench builds still have the setup flow switched off.

### 7.3 What is wired and what is not (today, 2026-11-17)

| Part | State |
|---|---|
| Sensor bench app (read, print, sleep 60 s) | Written, compiles in CI, unit tests on PC, **never run on hardware** |
| v1 SuperMini config | Compiles in CI (second build step), **not run on the board**; console choice on native USB is UNVERIFIED |
| BLE setup and claim (4.F2, 4.F2b) | Code exists, off in bench builds, not run on hardware; per-unit provisioning tool + bench procedure written (4.F2b), device steps UNVERIFIED (7.2) |
| Report payload, sample ring, sleep decision, hourly upload decision (4.F3) | Pure C with PC tests. **Not called from `main.c`** |
| 4.F3 upload adapter (Wi-Fi bring-up, TLS client, SNTP, RTC-retained state) | **Not written.** No data leaves the device today |
| Edge AI (TFLite Micro model on the device) | **Not integrated.** Training code is in `ml/`; the firmware has no model or `esp-tflite-micro` dependency |
| OTA update, 15-minute sampling schedule, custom-PCB soil reading (PCNT) | Not written |
| Soil calibration | Placeholder numbers until measured on the bench (WO-005 step 8) |

---

## 8. Troubleshooting

| Symptom | Likely cause (source) | What to do |
|---|---|---|
| `idf.py: command not found` / not recognised | The ESP-IDF environment is not loaded in this terminal | Linux/macOS: `. ~/esp/esp-idf/export.sh`. Windows: open "ESP-IDF 5.4 PowerShell" |
| Build error right at the start about target or chip | Wrong target or stale `sdkconfig` | `idf.py set-target esp32c3` (it recreates `sdkconfig`), build again |
| Build error, other | Different ESP-IDF version than CI, or a code finding | `idf.py --version` must say v5.4. If it does, send the last 30 lines to Mira. Do not edit source files to make it pass |
| No port appears | Charge-only cable; board not in download mode; missing driver *(`v1/WIRING.md` 2.3)* | Other cable; SuperMini: BOOT+RESET (4.2); DevKit on the UART port, not another connector; driver (2.4) |
| `Permission denied` on the port (Linux) | User not in `dialout`/`uucp` | `sudo usermod -aG dialout $USER`, log out and in |
| Port busy / "could not open port" / "access denied" (Windows) | Another program holds the port | Close other monitors; unplug and replug |
| Flash fails ("Failed to connect", timeouts, "chip not detected") | Wrong port, bad cable, board not in bootloader mode, wrong chip target *(playbook rule: check profile, port, cable, bootloader mode before suspecting code)* | Check port; other cable; hold BOOT, tap RESET (4.2); `idf.py set-target esp32c3`; lower speed `-b 115200` (flash option, UNVERIFIED) |
| Monitor shows garbage characters | Wrong baud rate or wrong console for the board | `idf.py monitor` normally takes the right rate from the build; rebuild if you changed the board config. SuperMini on the wrong config prints nothing, see next rows |
| **DevKit: boot messages but no `NWBENCH` lines**, maybe `NWSETUP closed, never provisioned` | BLE setup flow still ON (default) (`main.c`) | Section 3.1: switch it off in `menuconfig`, rebuild, flash. This is read from the source: UNVERIFIED on hardware |
| **SuperMini: no output at all** | Console is on native USB (`sdkconfig.defaults.v1`), UNVERIFIED on the board; or the DevKit config was flashed (its console is the UART pins, nothing on USB) | Check `grep` proof in 3.2; check port and cable; BOOT+RESET. Report as a *USB console finding* with the `idf.py monitor` header and Device Manager / `lsusb` entry (`v1/FIRMWARE-BENCH.md` step 0) |
| `board=devkit` on the SuperMini (or the reverse) | Reused old `sdkconfig`: defaults files only seed a new one (`ci.yml` comment) | Use the separate `-B build-v1 -DSDKCONFIG=sdkconfig.v1` form (3.2) from a clean state, or delete `sdkconfig` and `set-target` again |
| Reset loop, "Brownout detector was triggered" | Supply sags: weak USB port or cable, or on the v1 board a low cell: the 3.3 V LDO can drop out below about 3.5 V (`v1/WIRING.md` 2.2, a known v1 limit, not a firmware fault) | Other USB port or a short good cable; for a cell, charge it; write down the cell voltage |
| `err=...aht:-1` or `bh:-1` | No answer on I2C (AHT20 at 0x38, BH1750 at 0x23): SDA/SCL swapped, 3V3 on the wrong pin, loose wire | Check against `board.h` (SDA GPIO6, SCL GPIO7); v1: `WIRING.md` section 7 step 7 |
| `err=...aht:-2` / `-3` | AHT20 CRC error / busy | Check wiring and supply; note it and report |
| `err=...soil:-1` or `soil_flags` `0x04` | Soil probe not wired, or at a rail | Check GPIO3 (power) and GPIO4 (AOUT); v1: stop soil steps if AOUT is above about 2.4 V in air and report (`FIRMWARE-BENCH.md` S4) |
| `err=...bat:-5` | The chip's ADC has no calibration data | Report it: a finding, not your mistake (issue #68 step 10.3) |
| `vbat_mv` about 5000 on the SuperMini | USB 5 V is on the divider with J1 open | Expected there (`FIRMWARE-BENCH.md` S3), not a battery value |
| Monitor hangs after `NWBENCH sleep` | Native USB dropped during deep sleep | Restart `idf.py monitor` |
| `ctest` not found / compiler missing | PC tools missing | Section 2.2; on Windows use WSL2 |

---

## 9. Reporting back and "definition of working"

### 9.1 What to paste into issue #68
One comment on [issue #68](https://github.com/nilwerk/nilwerk-lab/issues/68) with:
1. **The filled result table** from the issue (every step a row, PASS / FAIL / "not done" with the reason). Never change a measured number.
2. **Versions and setup** so we can reproduce: OS and version; `idf.py --version`; `git rev-parse --short HEAD` of your checkout; board (DevKitM-1 or SuperMini) and the config used (3.1 or 3.2); USB cable and port used.
3. **Build output:** the last 30 lines of `idf.py build` (and `idf.py size`).
4. **Host tests:** the last lines of the `ctest` run ("100% tests passed ..."), or "not run" and why.
5. **The serial log** (`run1.log`), whole session, attached as a text file. Includes the `NWBENCH start` line and the five lines of each wake.
6. **Photos and video** as the issue asks (2 to 3 photos: wiring from above, monitor screen with the lines, multimeter on GPIO3 in sleep; one 10 to 20 s video), and whether we may use them publicly.
7. **Your hours** (start, end, total) and every problem.
Do **not** paste Wi-Fi names, passwords, tokens or any real cloud URL into the log or screenshots.

### 9.2 Definition of working (first bring-up)
The environment and firmware count as **working** when all of this holds:
- the host tests pass (19 of 19), or you reported why they could not run;
- the build for your board ends with "Project build complete";
- flash succeeds and `NWBENCH start` shows the right `board=`;
- five consecutive lines show `err=soil:0,aht:0,bh:0,bat:0` (acceptance A1);
- the sensors react as in 6.2 (breath, finger, light, soil air vs water);
- after `NWBENCH sleep s=60` the board wakes with `wake=2`;
- the full log is attached.

Complete WO-005 = every row of the issue's table PASS. **A FAIL with a good log is still a good result.** Not working is not a failure of yours: report it with the log and stop; do not decide on fixes (`v1/FIRMWARE-BENCH.md`).

---

## 10. Where to ask, and the rules of the team

- **Ask in the work-order issue** (#68 for WO-005). Nora (Lead/PM) reads it and answers the same day; Mira (firmware) answers technical questions via Nora. If you are blocked for more than 4 hours write `BLOCKED:` and what you tried. *(TEAM.md section 12)*
- Hardware tasks reach you **only as work orders** from Nora. One hands-on order at a time. Do not buy anything unless Arsany confirmed it in the issue.
- **Never commit secrets** (section 7.1). Never push to `main`. Agents and team members work on their own branch, named `agent/<role>/<task-id>` for agents; if you are not sure how to branch or push, ask Nora instead of trying. Arsany merges. *(TEAM.md section 5)*
- Do not "fix" a failing build or test by editing source files or checks. Report it with the log.
- Anything that needs Arsany (money, scope, real URLs, approvals) goes through Nora.
- Read next: [`TEAM.md`](../../../team/TEAM.md) (charter and hard rules), [`LESSONS.md`](../LESSONS.md) (project lessons).

### Glossary
- **ESP-IDF:** Espressif's official toolkit for programming ESP32 chips; `idf.py` is its command-line tool.
- **Target:** the chip family to build for (`esp32c3`).
- **`sdkconfig`:** the generated file with all build settings; `sdkconfig.defaults*` seed it; git-ignored.
- **`menuconfig`:** text menu to change those settings.
- **Flash / monitor:** write the program to the chip / show its serial output.
- **Deep sleep:** the chip is almost off and restarts by itself after a timer; the program starts again from the top (`wake=2`, `wake=3` ...).
- **DevKitM-1:** Espressif's ESP32-C3 development board (USB-UART chip). **SuperMini:** a small ESP32-C3 board with native USB, used on the v1 perfboard.
- **GPIO:** a numbered pin of the chip. **ADC:** converts a voltage to a number. **I2C:** two-wire bus (SDA data, SCL clock) for AHT20 and BH1750.
- **FR-/NFR-xx, A-xxx, WO-xxx:** requirement, requirement-type "quality", question-for-Arsany and work-order numbers used across the repo.

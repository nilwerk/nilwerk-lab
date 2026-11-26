# Boot-loop guard bench check (task 4.F7b) - DRAFT

**Status: DRAFT written by Mira (firmware) for Nora. This is NOT a work order and NOT a GitHub issue.**
Nora decides when it becomes a work order for Peter (TEAM.md section 12). Due: TBD by Nora.

**Authoritative procedure:** [`projects/plant-monitor/tests/procedures/4.F7-boot-loop-guard.md`](../../tests/procedures/4.F7-boot-loop-guard.md).
This draft EXTENDS that file with bench detail for Peter (part C and part E below). It does not replace it. Where the two differ,
that file wins until Nora decides. Its steps 2 and 4 to 9 (fallback current, confirm, rollback, RTC loss, unprovisioned unit,
reset button, rollback failure) are NOT in this draft and stay in that file.

Every step that needs a board, a serial port or the ESP-IDF toolchain is marked **NOT YET VERIFIED ON HARDWARE**.
The Kconfig help for `PLANT_BOOTGUARD` (`projects/plant-monitor/firmware/main/Kconfig.projbuild:135`) points to the authoritative file above
(the path there is relative to `projects/plant-monitor/`).
Nobody has built or flashed the guard image yet. The steps are written from the source code on `main`
(file references below), so every timing and every log text must be checked on the real board before Peter relies on it.

---

## Why

The boot-loop guard (task 4.F7b) stops a unit that resets again and again from burning its battery on endless Wi-Fi and BLE attempts.
The fallback (no BLE, no Wi-Fi, one log line, a 6 h deep sleep) is required by NFR-01 and NFR-12. FR-D05 covers only the rollback branch,
which this check does not test (open point O4).
After 5 boots that never reach the normal end of a cycle, the next boot goes into the fallback.
This procedure checks that behaviour on a real board. The guard is OFF in the normal firmware build and stays off until this check passes.

## Inputs (what you get)

- **Firmware source:** the repository folder `projects/plant-monitor/firmware` (after the 4.F7b PR is merged, it is on `main`).
- **Build overlay (already in the repo):** `projects/plant-monitor/firmware/sdkconfig.defaults.bootguard`. You do not edit it.
- **Board:** ESP32-C3 SuperMini on the v1 perfboard, wired as in `projects/plant-monitor/v1/WIRING.md`.
  The v1 SuperMini is the bench board (owner decision of 14 Nov, Nora's decision O1). The build command in step A3 uses the v1 settings.
- **Cable:** USB-C **data** cable (not a charge-only cable), connected to the SuperMini only.
- **Computer:** Linux, macOS or Windows with ESP-IDF v5.4 installed as in `projects/plant-monitor/firmware/DEV_GUIDE.md` (sections 2 and 4).
- **Stopwatch:** a phone timer or a kitchen timer that counts hours and minutes.
- **Paper or a spreadsheet** for the table in "Expected output".
- **Parts to buy:** none for this procedure. No money is spent.
- **Time needed:** about 7 h 30 min in total, mostly waiting (the 6 h sleep in part E).

## Steps

Read the "Safety" block first.

**Safety**
- Battery: do NOT connect a LiPo battery for this procedure. USB power only. [proposed]
- Flashing on the v1 perfboard: battery jumper J1 must be OPEN and the USB cable goes into the SuperMini only.
  (`projects/plant-monitor/firmware/DEV_GUIDE.md` section 4, and `WIRING.md` section 2.3.)
- **Never unplug USB during parts C and E.** Unplugging USB removes the power, and the guard then counts the next boot as a new
  power-on. The count restarts from zero and the test is invalid. The RST button is the only reset you use in part C.

**Part A - Prepare the build (toolchain needed: NOT YET VERIFIED ON HARDWARE)**

A1. Open the ESP-IDF terminal and load ESP-IDF (`. ~/esp/esp-idf/export.sh` on Linux and macOS; the "ESP-IDF 5.4 PowerShell" shortcut on Windows).
    Run `idf.py --version`. Expected: a line that starts with `ESP-IDF v5.4`. If not, STOP.

A2. Change into the firmware folder: `cd nilwerk-lab/projects/plant-monitor/firmware` (the path inside your clone).

A3. Build the guard image. Copy the command exactly, on one line:
    `idf.py -B build-bootguard -DIDF_TARGET=esp32c3 -DSDKCONFIG=sdkconfig.bootguard -DSDKCONFIG_DEFAULTS="sdkconfig.defaults;sdkconfig.defaults.v1;sdkconfig.defaults.bootguard" build size`
    Expected: the build ends with `Project build complete` and the size table. No red error lines.

A4. Check that the guard option is on: `grep -q '^CONFIG_PLANT_BOOTGUARD=y' sdkconfig.bootguard` and then `echo $?`.
    Expected: `0`. (Windows PowerShell: `Select-String '^CONFIG_PLANT_BOOTGUARD=y' sdkconfig.bootguard`; expected: one line printed.)
    If the result is not `0`, STOP and write "BLOCKED:" in the report.

**Part B - Flash and first power-on (board needed: NOT YET VERIFIED ON HARDWARE)**

B1. Unplug the USB cable. Check that the battery jumper J1 is open. Expected: nothing is connected to the SuperMini.

B2. Plug the USB cable into the SuperMini. Expected: a new port appears on the computer: `/dev/ttyACM0` or similar on Linux,
    `/dev/cu.usbmodem...` on macOS, or `COMx` on Windows. If no new port appears, try another cable (data cable) and write "BLOCKED: no port".
    Find the port number as in `DEV_GUIDE.md` section 4.3. Write it here: `PORT = ________`.

B3. Flash WITHOUT the monitor: `idf.py -B build-bootguard -DSDKCONFIG=sdkconfig.bootguard -p PORT flash`
    Expected: the flash ends with `Hash of data verified` and `Hard resetting`. No `error` lines.

B4. Unplug the USB cable. Wait 10 seconds. Plug it in again. Expected: no text on the screen, because no monitor is open yet.
    This is the bench detail for step 0 of the authoritative file (option (a): a power cycle after the flash). That file leaves the choice open;
    Nora decides. (A reset that is not a power-on can make the guard fall back on the first boot, see open point O2.)

B5. Open the serial monitor: `idf.py -B build-bootguard -DSDKCONFIG=sdkconfig.bootguard -p PORT monitor`
    Expected: a line that contains `NWBENCH start` (for example `... NWBENCH start board=v1_supermini wake=1 ...`).
    Expected: NO line that contains `NWBOOTGUARD`. Boot 1 is counted silently, the guard only logs when it stops a boot.
    Write this boot as **Boot 1** in the table.

**Part C - Five forced failed boots (board needed: NOT YET VERIFIED ON HARDWARE)**

Why this works: a boot counts as good only when the 5-reading bench loop finishes (`main/main.c:189-194`: the 2 s pause per reading,
then `nw_bootguard_idf_confirm(NW_BG_PATH_NORMAL_END)`). The loop takes about 20 s after `NWBENCH start`
(about 5 x (2 s pause, `main.c:190`, plus about 1.75 s soil time, `nw_soil.h:9-11`), UNVERIFIED).
If you press RST before the loop ends, the boot is counted as failed.

Press-window rule (the only one): **press RST within 5 s of the `NWBENCH start` line.**

C1. Wait until the line `NWBENCH start` is on screen. This is boot k, where k = 1, 2, 3, 4 or 5.

C2. Within 5 s of that line, press the RST button on the SuperMini once. Count the press: forced reset number k.
    You do ONE press for each of boots 1, 2, 3, 4 and 5. Five presses in total.

C3. Check the new boot: a new `NWBENCH start` line must appear (boot k+1). It must not be followed by `NWBOOTGUARD` at this point.

C4. If the monitor stops showing text after a press (the native USB port of the SuperMini can re-enumerate),
    restart the monitor with the same command as B5. A monitor restart is NOT a reset and does not count.
    Do NOT unplug the USB cable. If you do, write "BLOCKED: unplugged USB" and start again from B4.

C5. FAIL during part C: if `NWBENCH sleep s=60` appears during part C, the run is invalid. Write "FAIL: loop finished".
    Restart from B4. Do NOT press RST during boot 6. Boot 6 must stop by itself (part D).

**Part D - Boot 6 must fall back (board needed: NOT YET VERIFIED ON HARDWARE)**

D1. After the 5th press, watch the monitor. The next line that contains `NWBOOTGUARD` is the answer of boot 6.
    **PASS line (exact text, the ESP-IDF log prefix in front of it may differ):**
    `NWBOOTGUARD fallback why=count failed=5 limit=5 sleep_s=21600 ble=off wifi=off`
    The source for this line is `components/bootguard/src/nw_bootguard.c` (function `nw_bootguard_log_line`).

D2. After the PASS line there must be NO further `NWBENCH` line and no BLE message until the sleep ends (part E).

D3. Start the stopwatch at the moment the PASS line appears. Write the time in the table.

D4. FAIL cases, write them down and stop:
    - `why=corrupt` instead of `why=count`: FAIL. See open point O2.
    - `why=ota_loop` or `why=ota_window` or `why=rollback_failed`: FAIL and STOP. The rollback path is not part of this check (open point O4).
    - No `NWBOOTGUARD` line after 5 presses, or a `NWBENCH wake=` reading line after boot 6 starts: FAIL. The guard did not stop the boot.

**Part E - 6 hour sleep check (board needed: NOT YET VERIFIED ON HARDWARE)**

Observation method: the serial monitor is kept open for the WHOLE test (Method A). Method B (no serial, restart the monitor later) is NOT used
in this procedure: without a serial line during the sleep, nothing shows when the board woke up. Nora's decision, open point O3.

E1. Leave the board powered from USB. Do not press any button. Do not unplug. Keep the monitor window open and do not close it.

E2. The board is now asleep for 21600 s (6 h). The USB serial port may disappear during the sleep (`DEV_GUIDE.md` section 4.3, the SuperMini
    note on deep sleep). If the monitor loses the port, the run is INCONCLUSIVE, not PASS. Write "INCONCLUSIVE: port lost at <time>", keep the stopwatch
    running, do not restart the board, and tell Nora. Do not change the method.

E3. After 6 h (21600 s) the board wakes up by itself. The probation boot prints `NWBENCH start` on the open monitor (UNVERIFIED that the
    line appears after deep sleep on this board). Stop the stopwatch when that line appears. Write the time.

E4. Compare the times: the time between the PASS line (D3) and the first `NWBENCH start` after the sleep.
    PASS: 6 h, within a tolerance of +/- 10 min [proposed until first bench run].
    FAIL: much earlier (the sleep was cut short) or never (the board stayed silent for more than 7 h, with the port still up). Write "FAIL: sleep" and stop.
    INCONCLUSIVE: the port was lost (E2). Not a pass.

**Part F - Probation boot and recovery (board needed: NOT YET VERIFIED ON HARDWARE)**

F1. The boot after the sleep is the probation boot: it gets exactly one normal attempt. Let it run.
    PASS: the 5 `NWBENCH wake=...` reading lines appear, then `NWBENCH sleep s=60`. This boot completes its loop and the guard counter goes back to zero.

F2. Wait 3 minutes with the monitor open (one cycle is about 20 s of readings plus 60 s of sleep, so about 80 s).
    Expect at least 2 `NWBENCH sleep s=60` lines and NO `NWBOOTGUARD` line in these 3 minutes. Write "no guard line" in the table.
    FAIL: any `NWBOOTGUARD` line. Write it down exactly.

F3. Optional (only if Nora asks for it): repeat part C once more during the probation boot. Expected: the next boot logs
    `NWBOOTGUARD fallback why=count failed=5 ...` straight away, without 5 presses. Another 6 h wait. Not required for the first pass.

**Part G - Restore the normal firmware (board and toolchain needed: NOT YET VERIFIED ON HARDWARE)**

G1. Stop the monitor with Ctrl+] (Ctrl and the right square bracket key).

G2. Build the normal v1 image (the same command as `DEV_GUIDE.md` section 3.2, which is the CI build):
    `idf.py -B build-v1 -DIDF_TARGET=esp32c3 -DSDKCONFIG=sdkconfig.v1 -DSDKCONFIG_DEFAULTS="sdkconfig.defaults;sdkconfig.defaults.v1" build size`
    Expected: `Project build complete` at the end.

G3. Flash it: `idf.py -B build-v1 -DSDKCONFIG=sdkconfig.v1 -p PORT flash`
    Expected: `Hash of data verified` and `Hard resetting`. Then unplug USB, wait 10 seconds, plug in again.

G4. Open the monitor: `idf.py -B build-v1 -DSDKCONFIG=sdkconfig.v1 -p PORT monitor`
    PASS: `NWBENCH start` lines appear, and there is NO `NWBOOTGUARD` text anywhere in the log.
    (The normal image does not contain the guard. This is the proof that the default build is unchanged.)

---

## Expected output (what you deliver)

1. **Filled table** (copy this table into your report comment):

| Boot no. | Reset before it | `NWBENCH start` seen? | Guard line seen (exact text) | Time (stopwatch) |
|---|---|---|---|---|
| 1 (power-on) | none (B4 power-on) | yes / no | none expected | - |
| 2 | forced reset 1 | yes / no | none expected | - |
| 3 | forced reset 2 | yes / no | none expected | - |
| 4 | forced reset 3 | yes / no | none expected | - |
| 5 | forced reset 4 | yes / no | none expected | - |
| 6 | forced reset 5 | no | PASS line / other | time of PASS line |
| probation (after 6 h) | none (sleep) | yes / no | none expected | time since PASS line |

   Also: the exact PASS line text, the total time measured in E4, and the result (PASS, FAIL or INCONCLUSIVE).
2. **Full serial log** of the whole session, saved to a file with `idf.py -p PORT monitor | tee bootguard-run.log` if your monitor allows it.
   If `tee` does not work, copy the log from the terminal into a text file. [UNVERIFIED tool step, see `DEV_GUIDE.md` section 4.]
3. **Photos:** 2 photos (the board on the bench, and the screen with the PASS line). Crop out any serial number, label or Wi-Fi name.
4. **A 10 to 20 second video** of the five presses (RST) with the monitor on screen.
5. Your hours in the closing comment (planned and actual).

## Acceptance criteria

1. Part A builds the guard image, and `grep` in A4 returns 0. (Source: `sdkconfig.defaults.bootguard`.)
2. Boots 1 to 5 each show `NWBENCH start` and no `NWBOOTGUARD` line.
3. Boot 6 shows exactly the PASS line in D1, with `why=count failed=5 limit=5 sleep_s=21600`. The fallback is required by NFR-01 and NFR-12.
4. After the PASS line no sensor reading and no BLE message appears until the sleep ends.
5. The first `NWBENCH start` after the sleep comes 6 h later, within the tolerance in E4 [proposed until first bench run, +/- 10 min].
6. The probation boot completes its loop, and the next 3 minutes show no `NWBOOTGUARD` line (F1, F2).
7. Part G shows the normal image with no `NWBOOTGUARD` text. (Proves the default build is unchanged.)
8. NOT measured in this procedure: the sleep current (NFR-12, 50 uA). That is step 2 of the authoritative file, a separate work order.
9. NOT tested in this procedure: the rollback branch (FR-D05, open point O4).

## Due

TBD by Nora.

## How to report

Comment on the work order issue (once Nora opens it): the filled table, the PASS line text, photos and video as above, and any FAIL or INCONCLUSIVE with the exact log text.
Questions at any time in the issue. If blocked for more than 4 hours, write "BLOCKED:" and what you tried.
Results that pass are copied into the PR and the test record with your name as the tester.

## Open points (for Nora, Mira, Theo)

- **O1. Board type: closed.** v1 SuperMini (owner decision of 14 Nov). The DevKit is not part of this procedure.
- **O2. First boot after a flash.** Read from `nw_bootguard.c`: a reset that is not a power-on, with a wrong magic in the retained memory, counts as corruption and goes straight to the 6 h fallback. A flash ends with a reset that is not a power-on. That is why B4 asks for a real power-on before the monitor. The authoritative file's step 0 keeps this decision open. Whether the first boot after a plain flash really falls back is NOT VERIFIED.
- **O3. Observation method: closed as Method A.** Serial monitor open for the whole test. Method B is dropped. Open risk: the USB port may drop during deep sleep, which makes the run INCONCLUSIVE (E2). Whether the port drops on this board is NOT VERIFIED.
- **O4. Rollback is not testable on this build.** `sdkconfig.defaults.bootguard` says the rollback needs an OTA partition table and `CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE`. Neither is set. Rollback is for the OTA task (authoritative file, step 5).
- **O5. Brownout.** Whether a brownout keeps the RTC memory is UNVERIFIED (authoritative file, step 6). This procedure does not test brownouts.
- **O6. Tolerance and duration.** The +/- 10 min tolerance (E4) and the 3 min check (F2) are [proposed until first bench run]. Nora confirms after the first bench run.
- **O7. Forced resets instead of the test abort.** The authoritative file's step 1 expects a test-only `abort()` image behind a Kconfig switch that does not exist yet. This draft uses 5 manual RST presses on the normal guard image instead (part C). That is a bench detail that extends step 1, not a replacement. Nora decides whether the abort image is still wanted.

## Glossary

- **RTC memory:** a small memory inside the ESP32-C3 chip that keeps its contents during a deep sleep and a reset. It is lost when the power is removed.
- **OTA:** "over the air". Updating the firmware through the network instead of a cable. The guard's rollback is part of that task.
- **Serial monitor:** a window that shows the text the board prints over USB (here `idf.py ... monitor`). Leave it with Ctrl+].
- **esptool:** Espressif's program that writes the firmware into the chip. `idf.py flash` calls it for you.
- **ESP-IDF:** Espressif's software development kit for the ESP32 chips. `idf.py` is its command-line tool.
- **Deep sleep:** the lowest-power sleep of the chip. It ends with a timer, and the board starts again from the beginning (a new boot).
- **Boot:** one start of the firmware, from power-on or a reset, until the board sleeps or stops.
- **Reset (RST):** the small button on the board that restarts the chip without removing the power.
- **Power-on:** the board gets power again after being off, for example after unplugging USB. The guard treats this as a new start.
- **Port:** the name the computer gives the USB connection, for example `COM5` (Windows) or `/dev/ttyACM0` (Linux). It is only an example.
- **Fallback:** the guard's safe mode. No BLE, no Wi-Fi, just a long deep sleep.
- **Probation boot:** the one normal try after the 6 h fallback sleep.
- **sdkconfig:** the file where the build settings are stored. Each build folder has its own.
- **Stopwatch:** a timer you start at a given moment and read later.

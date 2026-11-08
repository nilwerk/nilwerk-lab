# [WO-xxx] Bench test of the sensor firmware on the dev kit (task 4.F1)

Draft by Mira (Firmware + Edge AI) for Nora to issue as a GitHub issue (label `peter`, assign `@peterjosephgaras-ops`, TEAM.md section 12). Theo checks it before it is opened. The WO number is Nora's.

**Status of the firmware: written and unit-tested on a PC only. It has NEVER run on a board.** This work order is the first time it touches hardware. Expect problems and report them; a FAIL with a good log is a useful result.

## Status for reviewers (PR #57)
- **CI:** the `firmware` job (ESP-IDF v5.4 build for esp32c3 plus host tests) is GREEN on head `62bec99`, run 42494238390 (checked 2026-11-08 with `gh run view`: conclusion success; the other jobs were skipped as unaffected). So the ESP-IDF layer (`hal_esp32.c`, `main.c`) does compile. It still has never run on a board.
- **Dev-kit calibration does not carry over (C3):** the dry/wet numbers you measure in Step 8 are for the dev-kit analog probe only. The custom board reads its soil probe with PCNT (pulse counts), so they do NOT apply there; it needs its own calibration.

## Why
The product measures soil moisture, air temperature, air humidity, light and battery voltage in every report (FR-D01, FR-D02: every report carries all five values, 24 reports per day). Before we build the reporting on top, we need to know that the five readings are correct and that the soil probe supply is switched off during sleep (NFR-12: whole-board deep sleep at most 50 uA, and an on soil supply would break that). You are testing the first firmware that reads the five sensors.

## Inputs (what you get)
- Firmware source (branch `agent/firmware/4.F1`, later `main`): https://github.com/nilwerk/nilwerk-lab/tree/agent/firmware/4.F1/projects/plant-monitor/firmware
- Pin definitions: `firmware/main/board.h` (https://github.com/nilwerk/nilwerk-lab/blob/agent/firmware/4.F1/projects/plant-monitor/firmware/main/board.h). If this work order and `board.h` disagree, `board.h` wins: stop and ask in the issue.
- Dev-kit parts list and notes (what was ordered, wiring warnings): https://github.com/nilwerk/nilwerk-lab/blob/main/projects/plant-monitor/hardware/devkit-order-list.md
- ESP-IDF v5.4 install guide (ESP32-C3): https://docs.espressif.com/projects/esp-idf/en/v5.4/esp32c3/get-started/index.html
- Parts you have: ESP32-C3-DevKitM-1, AHT20 breakout, BH1750 (GY-302) breakout, capacitive soil moisture sensor v1.2 (analog), 2 x 100 kOhm 1 % resistors, LiPo cell with protection (polarity check, see Steps 0), USB cable.
- Tools you need: multimeter, breadboard and jumper wires, a glass of water, a dry paper towel, a phone with a torch, a room thermometer/hygrometer if you have one (any is fine, say which), 2 x AA/AAA cells in a holder (optional second battery point).
- Budget: nothing needs buying. If you need something, ask in the issue first (receipts are reimbursed).
- What the firmware does: after boot it prints one line starting `NWBENCH` every 2 s with all five readings. After 5 lines it switches the soil supply off, goes to deep sleep for 60 s, wakes and repeats. Example of the format (invented numbers, NOT a measurement):
  `NWBENCH wake=1 i=0 soil_raw=2000 soil_pct=50.0 soil_flags=0x00 temp_c=23.45 rh_pct=41.25 lux=250.0 lux_raw=300 vbat_mv=3990 vbat_adc_mv=1995 vbat_plausible=1 divider_na=19950 err=soil:0,aht:0,bh:0,bat:0`
  `err=` fields are 0 when fine. -1 = the chip did not answer (wiring), -2 = AHT20 CRC error, -3 = AHT20 busy, -5 = battery ADC has no calibration, -6 = not supported.

## Steps
**Step 0 - safety.**
0.1 LiPo: red and black wires are NOT the same on every cell. Check with the multimeter which wire is plus (it reads +3.0..4.2 V on the red probe). Never connect the cell plus to a GPIO pin, only to the top of the 100 kOhm divider (Step 3).
0.2 Never connect the LiPo to the dev kit 5V or 3V3 pins. The dev kit is powered by USB only.
0.3 Do not put the soil probe in water above its marked line; the electronics must stay dry.

**Step 1 - install and build.**
1.1 Install ESP-IDF v5.4 (link above). Open the IDF terminal.
1.2 `git clone https://github.com/nilwerk/nilwerk-lab.git && cd nilwerk-lab && git checkout agent/firmware/4.F1 && cd projects/plant-monitor/firmware`
1.3 `idf.py set-target esp32c3` then `idf.py build`. PASS: ends with "Project build complete". Save the last 30 lines of the output.

**Step 2 - wiring (all sensors from the dev-kit 3V3 pin; ground everything together). GPIO numbers are from `board.h`, which cites `pcb/pinmap-sleep.md`.**
| Dev kit pin | Connect to |
|---|---|
| 3V3 | AHT20 VIN, BH1750 VCC, nothing else (NOT the soil probe) |
| GND | AHT20 GND, BH1750 GND, soil probe GND, cell minus (Step 3) |
| GPIO6 | SDA of AHT20 and BH1750 (both on the same two wires) |
| GPIO7 | SCL of AHT20 and BH1750 |
| GPIO3 | soil probe VCC (the probe is powered from this pin only while measuring) |
| GPIO4 | soil probe analog output (AOUT) |
| GPIO0 | middle of the divider (Step 3) |
Do NOT use GPIO1, GPIO2, GPIO8, GPIO9. BH1750 ADDR pin: leave unconnected (address 0x23).

**Step 3 - battery divider.** Two 100 kOhm resistors in series: cell plus -> resistor A -> middle point -> resistor B -> GND. Middle point -> GPIO0. Cell minus -> dev-kit GND. Check with the multimeter that the middle point reads half of the cell voltage before you connect it to GPIO0.

**Step 4 - flash and read.** Plug in USB (the port marked UART on the DevKitM-1). `idf.py -p <PORT> flash monitor` (PORT = COMx on Windows, /dev/ttyUSBx on Linux). You should see `NWBENCH start ...` then `NWBENCH ...` lines every 2 s. Leave it running for the tests. Exit the monitor with Ctrl+]. Save the log of the whole session to a text file (`idf.py monitor | tee run1.log` if needed).

**Step 5 - AHT20, BH1750 present (FR-D01).** Record 5 consecutive lines. PASS: all `err=` fields 0 in all 5 lines. If `aht:-1` or `bh:-1`: wiring (SDA/SCL swapped? 3V3 on VIN?).

**Step 6 - temperature and humidity (FR-D01).**
6.1 Room value: write down temp_c and rh_pct of 5 lines and the room thermometer/hygrometer reading (say which device).
6.2 Breath test: breathe on the AHT20 for 3 s. PASS: rh_pct rises by at least 10 %RH within 10 s and falls back near the old value within 2 min.
6.3 Finger test: hold a finger near the AHT20 for 20 s. PASS: temp_c rises by at least 0.5 degC.

**Step 7 - light (FR-D01).**
7.1 Normal room light: write lux. PASS: lux_raw is not 65535 and lux is greater than 0.
7.2 Cover the BH1750 completely with your hand or a dark cloth. PASS: lux below 5.
7.3 Phone torch 5 cm from the sensor. PASS: lux above 100 and at least 20 times the covered value, and lux_raw not 65535 (if it is, move the torch away to 20 cm and note it).

**Step 8 - soil probe calibration points (FR-D01).** The calibration in the firmware is a placeholder until you measure it.
8.1 Probe held in the air, not touching anything, dry: record soil_raw of 5 lines -> `raw_dry`.
8.2 Probe in the glass of water up to its marked line (electronics dry): wait 30 s, record soil_raw of 5 lines -> `raw_wet`.
8.3 PASS: `raw_dry - raw_wet` is at least 500 counts, and the 5 readings of each state differ by at most 30 counts. FAIL: smaller span or noisy; write down the numbers anyway (probes vary a lot).
8.4 `idf.py menuconfig` -> Plant Monitor -> set "dry" = `raw_dry`, "wet" = `raw_wet`; save, `idf.py build flash monitor`.
8.5 Check the percent: in air `soil_pct` at most 5.0, in water at least 95.0, in damp paper towel between 5.0 and 95.0 and bigger than in air. `soil_flags` in air/water may show 0x01 / 0x02 (clamped) if you are slightly outside the points: write it down.

**Step 9 - soil supply is OFF in deep sleep (NFR-12).** After 5 lines the monitor prints `NWBENCH sleep s=60 (IO3 must read 0 V now)`. Within those 60 s put the multimeter (DC volts) red probe on GPIO3, black on GND. PASS: 0.00 V (at most 0.05 V). FAIL: anything higher (write down the value; this would break the 50 uA limit). Repeat in 2 different sleep cycles. Do not try to measure microamps: the dev kit cannot give a valid sleep current (USB bridge, LED, LDO; see devkit-order-list section 3 note 5).

**Step 10 - battery voltage (FR-D01).**
10.1 With the divider connected, measure the cell voltage directly at the cell with the multimeter (V_cell). Write down the `vbat_mv` of 5 lines. PASS: the average of vbat_mv is within 50 mV of V_cell.
10.2 Optional second point: replace the cell by 2 x AA/AAA in series (about 3.0 V) and repeat. PASS: within 50 mV.
10.3 `vbat_plausible` is 1 for a cell between 3.0 and 4.25 V. If `err=...bat:-5` appears: the chip has no ADC calibration data; report it, this is a finding, not your mistake.
10.4 Note: the 2 x 100 kOhm divider draws about 21 uA at 4.2 V. That is for the bench only; the product board uses 1 MOhm + 1 MOhm (2.1 uA). Disconnect the divider from the cell when you finish.

**Step 11 - photos and video.** 2-3 photos (whole wiring from above, the monitor screen with the lines, the multimeter on GPIO3 in sleep) and one 10-20 s phone video (breath test with the lines scrolling). Say in your comment whether we may use them publicly.

## Expected output (what you deliver)
Comment on the issue with:
1. Table (one row per step, filled):

| Step | Measured | PASS/FAIL | Note |
|---|---|---|---|
| 1 build (last lines of output) | | | |
| 5 err fields (5 lines) | | | |
| 6.1 temp_c / rh_pct vs reference (which device) | | | |
| 6.2 breath: rh rise in 10 s | | | |
| 6.3 finger: temp rise | | | |
| 7.1 / 7.2 / 7.3 lux room / covered / torch | | | |
| 8.1 raw_dry (5 values) | | | |
| 8.2 raw_wet (5 values) | | | |
| 8.5 soil_pct air / damp / water | | | |
| 9 IO3 volts in sleep (2 cycles) | | | |
| 10.1 vbat_mv avg vs V_cell | | | |
| 10.2 vbat_mv avg vs V_cell (2 x AA, optional) | | | |

2. The log file (`run1.log`), the build output, the photos and the video.
3. Your hours (start, end, total) and any problem.
**PASS** of the whole order = every row PASS. **FAIL** = any row FAIL: still deliver everything. A row you could not do = write "not done" and why. Never change a measured number to make it fit.

## Acceptance criteria
1. A1 (FR-D01): all five values appear in `NWBENCH` lines with `err=soil:0,aht:0,bh:0,bat:0` in 5 consecutive lines (Steps 4-5, 8, 10).
2. A2 (FR-D01): temperature and humidity react to breath/finger as in Step 6, and match the reference within 1.0 degC and 5 %RH if a reference exists (these two limits are Mira's bench proposal, not a requirement).
3. A3 (FR-D01): lux reacts as in Step 7.
4. A4 (FR-D01, NFR-02 input): soil span at least 500 counts, spread at most 30 counts, 0-100 % behaviour as in Step 8.
5. A5 (NFR-12): GPIO3 (soil supply) reads at most 0.05 V during deep sleep, both cycles (Step 9). Only this one NFR-12 aspect is tested here; the 50 uA limit itself is task 5.2/4.P5 on the real board.
6. A6 (FR-D01): vbat_mv within 50 mV of the multimeter value (Step 10; the 50 mV limit is Mira's proposal).
7. FR-D02 (24 reports per day) is NOT tested here: there is no Wi-Fi/reporting yet. This order only checks that each report could carry the five values.

## Notes for the next firmware slices (TODOs, not part of this bench order)
- **4.F1b (PCNT soil reader) needs a report-schema decision first (PR #57 C2):** `cal.dry_raw` / `cal.wet_raw` in `docs/interfaces/device-report.schema.json` are 12-bit ADC counts (max 4095). PCNT counts of the custom-board oscillator are not bounded like that and are a different quantity. Options (Theo decides via the Lead): widen the schema range, add a probe-type field, or scale/define PCNT counts into the same range. Do not write the PCNT reader against the current schema until this is decided.
- **4.F2 / 4.F3 TODO, Wi-Fi TX gate (from Emil's LDO simulation):** the firmware must not start Wi-Fi TX (report, provisioning, OTA) while the cell voltage is below about 3.3 V (provisional; M8 decides the final value). At a ~350 mA TX peak the XC6220 LDO has almost no headroom (see `pcb/README.md` C5), so a low cell would sag the 3.3 V rail towards brown-out. Use the battery reading from this slice (`nw_battery`) before every radio start, skip or defer the report below the gate, and add a host test for the gate once the value is fixed.

## Due
Proposal (Nora decides): Wed 2026-11-11 18:00 Berlin = 19:00 Cairo (Cairo is one hour ahead of Berlin in November). Check-in Mon 2026-11-09 evening: build done (Step 1) and the first `NWBENCH` lines (Step 4), or "BLOCKED:" with what you tried. Expected effort: about 4-6 hours.

## How to report
Comment on this issue: the filled table, photos, logs, problems. Questions any time in the issue. If blocked for more than 4 hours, write "BLOCKED:" and what you tried.

## Glossary
- **ESP-IDF**: Espressif's programming framework for the ESP32 chip; `idf.py` is its command-line tool.
- **ADC**: converts a voltage to a number; here 12 bit = 0..4095 counts ("raw").
- **Deep sleep**: the chip is almost off and wakes by timer; the soil probe supply pin must be 0 V then.
- **Divider**: two equal resistors in series that halve a voltage so the chip can measure it (4.2 V -> 2.1 V).
- **I2C**: two-wire bus (SDA data, SCL clock) the AHT20 and BH1750 share; each chip has an address (0x38, 0x23).
- **NWBENCH**: the prefix of the lines the firmware prints.
- **Calibration (dry/wet)**: the two raw numbers of the soil probe in air and in water; used to turn raw counts into 0-100 %.
- **FR-D01 / NFR-12**: requirement IDs: the five readings in every report / the sleep-current limit.

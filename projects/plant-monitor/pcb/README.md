# PCB (Plan 4.P1: schematic) — Emil (PCB Designer)

KiCad 9 project `plant-monitor.kicad_pro` / `plant-monitor.kicad_sch` (one A1 sheet, net labels at every pin, no wires).
It is **generated** from [`design.py`](design.py) by [`gen_schematic.py`](gen_schematic.py) (no GUI was available);
[`check_netlist.py`](check_netlist.py) is the independent netlist/BOM/sleep check. Requirements: NFR-01 (3 months, A-020), NFR-12 (<= 50 uA, target 25 uA, A-027).
Layout is 4.P2 and not started. Nothing was ordered.

## Status of the checks

| Check | Result |
|---|---|
| KiCad ERC (`kicad-cli sch erc`) | **NOT RUN.** kicad-cli is not installed; Ubuntu's own package is KiCad 7 (cannot read a KiCad 9 file) and the KiCad 9 PPA install was blocked by the session's permission policy. The `.kicad_sch` has never been opened in KiCad: first action for anyone with KiCad 9 is open it and run ERC. |
| `python3 -I check_netlist.py` | all PASS (nets rebuilt from the file = model, no unconnected pin, no 1-pin net, BOM draft lcsc/qty = schematic, R9, strap pins, sleep sum) |
| Simulations (LDO dropout, divider, soil, charger, inrush) | not done in this slice |

## Charge current R9 (A-034 open)

`design.py` block `CHARGE CURRENT`: `CELL_MIN_MAH`, `R9_OHM`, `R9_LCSC`. R9 = 2.4k (C22940), I = 1100/R9 = 458 mA = 0.46C of 1000 mAh (603449); with the 850 mAh LP603443JU the same resistor is 0.54C (+15 % tolerance 527 mA = 0.62C, still < 1C), 2.7k (407 mA = 0.48C) would be the 0.5C choice. Change only that block, rerun the generator and the check.

## Cell connector, NTC / TEMP

J2 = JST PH 2-pin (C295747): pin 1 = CELL+ (VBAT), pin 2 = CELL- (CELL_NEG). A 2-pin cell has no NTC, so TP4056 **TEMP is tied to GND (sense disabled, datasheet p.7)**. The Jauch 3-pin variant (J2b C564183) would route the NTC to TEMP (remove the TEMP-GND tie). Plug polarity must be checked on receipt.

## Sleep-current path and pin map

Generated: [`pinmap-sleep.md`](pinmap-sleep.md). Typical 19.5 uA, worst 37.6 uA vs NFR-12 25 / 50 uA, mostly assumptions.

## Differences against the BOM draft (hardware/bom)

All BOM lines match by LCSC number and quantity, except: **added** R13, R14 (4.7k I2C pull-ups, C23162 unverified) and R15 (1k DW01A CS, C21190); R6 is a **pull-down** (BOM text said pull-up); footprints for SW1-3, U5, U6, E1 are custom names still to be drawn. `bom.csv` lists the schematic BOM; the BOM tab/CSV in `hardware/bom` was **not** edited (that is the Lead's/2.5 owner decision).

## Open points

1. **Battery sense, Q2 off:** BAT_SENS floats up to VBAT (4.2 V) on IO0 through R7 (above 3.3 V + 0.3 V). ~0.5 uA through the pin clamp, out of the absolute-max spec. Options: high-side P-FET (BOM change), or a divider tap clamp. Needs a decision.
2. **TEMP / cold charging:** cell may be charged 0-45 C only; no NTC, TEMP grounded. Mitigation options: NTC cell (J2b), or a GPIO on CE (CE internal default not read).
3. **USB 500 mA:** 458 mA charge + board load is at the USB 2.0 limit; TP4056 dissipates 0.78 W at 5 V in / 3.3 V cell (thermal foldback, not simulated).
4. **Double protection:** with a PCM cell, U4/Q1 are redundant (series works, costs); variant C needs a link from CELL_NEG to GND instead.
5. **GPIO2 strap left unconnected;** whether the module needs an external pull-up is unverified (R-pull-up costs one 10k).
6. **USB data:** BOM says "power only"; D+/D- are wired to IO19/IO18 (USB Serial/JTAG) so D1 is meaningful. Arsany/Mira to confirm (affects flashing).
7. **Pin numbers of U1, J1, U2, U4, Q1, U5, U6 are not datasheet-verified** (written from memory/listing; datasheets of XC6220, DW01A, 8205A, AHT20, BH1750, module not read). AHT20 package (4 vs 6 pin) undecided. BH1750 DVI handling to confirm.
8. Soil: electrode capacitance still assumed, no electrode ESD, wet/salty soil loading, U7 supply GPIO must be held low in deep sleep (firmware).
9. No power path: board does not run from USB without a cell. No VBUS fuse/TVS (only USBLC6). No DW01A VCC filter resistor. No VBUS-present or CHRG sense to a GPIO.
10. LDO Iq is 8 uA per listing, 6 uA above the power-budget typical (2 uA); the power budget should be updated after the datasheet is read.
11. Cell A-034 decision (603449 1000 mAh vs LP603443JU 850 mAh) open; R9 follows it. `firmware/main/board.h` does not exist; this pin table is the proposal.

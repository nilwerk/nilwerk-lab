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
| Simulations (LDO dropout, divider, soil, charger, inrush) | **NOT RUN.** `ngspice` is not installed in this session and could not be installed (`pip` has no package). The LDO dropout limit is only a hand estimate, see "Fix round". |

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
5. ~~GPIO2 strap left unconnected~~ **Closed (Theo C4):** R16 10k to 3V3 on GPIO2 (Espressif datasheet v2.2 s.4.1 recommends a pull-up). No sleep current.
6. **USB data:** BOM says "power only"; D+/D- are wired to IO19/IO18 (USB Serial/JTAG) so D1 is meaningful. Arsany/Mira to confirm (affects flashing).
7. **Pin numbers: all now checked against datasheets** (see Fix round). Remaining: BH1750 DVI is tied directly to VCC; the datasheet wants DVI low >= 1 us after VCC (reset), example RC 1k/1uF. Decide in 4.P2 (add RC or accept and re-init in firmware).
8. Soil: electrode capacitance still assumed, no electrode ESD, wet/salty soil loading, U7 supply GPIO must be held low in deep sleep (firmware).
9. No power path: board does not run from USB without a cell. No VBUS fuse/TVS (only USBLC6). No DW01A VCC filter resistor. No VBUS-present or CHRG sense to a GPIO.
10. LDO Iq is 8 uA typ (datasheet, PS mode, 0.1 mA load; 18 uA max), 6 uA above the power-budget typical (2 uA, assumption A). Cost: 6 uA x 24 h = 0.144 mAh/day (about 53 mAh/year). The sleep sum in `pinmap-sleep.md` already uses 8 uA. `hardware/power-budget` still has 2 uA: update it with the next power-budget revision (not done here).
11. Cell A-034 decision (603449 1000 mAh vs LP603443JU 850 mAh) open; R9 follows it. `firmware/main/board.h` does not exist; this pin table is the proposal.

## Fix round for Theo's review (PR #41, C1-C8)

| Item | Result |
|---|---|
| C1 AHT20 U5 | LCSC C2757850 resolved through the LCSC API (`wmsc.lcsc.com`) and its datasheet (Aosong/ASAIR, 2024-07, Table 5 and Figure 1): **6-pin DFN 3.0 x 3.0 x 1.0 mm**, 1 NC, 2 VDD, 3 SCL, 4 SDA, 5 GND, 6 NC. Symbol fixed (`design.py`), `pin_verified` now true, checked by `check_netlist.py`. Footprint `NW:AHT20_DFN-6_3x3` still to be drawn in 4.P2. Stock 32649 at the time of the call. |
| C2 pins | Read from the LCSC-linked datasheets: **U2** XC6220 SOT-25 (VIN 1, VSS 2, CE 3, NC 4, VOUT 5), **U4** DW01A (1 OD, 2 VM = CS, 3 OC, 4 TD, 5 VCC, 6 GND), **Q1** 8205A TSSOP-8 (package drawing: 1 D1, 2-3 S1, 4 G1, 5 G2, 6-7 S2, 8 D2; no numbered table in the datasheet, read from the drawing), **U6** BH1750 (1 VCC, 2 ADDR, 3 GND, 4 SDA, 5 DVI, 6 SCL), **J1** HRO TYPE-C-31-M-12 (signal-to-pad table; shield pad numbers belong to the footprint). Also checked: U3 TP4056 (1 TEMP, 2 PROG, 3 GND, 4 VCC, 5 BAT, 6 STDBY, 7 CHRG, 8 CE), U7 SN74LVC1G14 DBV (1 NC, 2 A, 3 GND, 4 Y, 5 VCC), D1 USBLC6-2SC6. All match the schematic. U1 was verified by Theo. `pin_verified=False` is gone from every part. |
| C4 GPIO2 | R16 10k 3V3 to GPIO2 added (declared addition, BOM qty of C25804 5). |
| C5 LDO dropout sim | **NOT RUN: ngspice unavailable.** Hand estimate only: datasheet gives 60 mV typ dropout at 300 mA (3.3 V version; the table row is ambiguous), the 3.4 V warning leaves 100 mV, so at a ~350 mA TX peak typ headroom is about 30 mV before the cell resistance drop (0.15 ohm x 0.35 A = 52 mV, assumed). That is negative margin: the rail may sag to roughly 3.25-3.3 V, which stays above the C3 brown-out level but this needs the real sim and the real cell resistance (4.P3). Do not take the estimate as a pass. LDO Iq 8 uA vs 2 uA in the budget: see open point 10. |
| C8 caption | Corrected (6.3 agent min, PR link, persona, no ratio). |
| C3, C6 | Decisions below, not changed. |

## Decisions for Arsany (routed by the Lead)

**D-C3: battery-sense node floats to VBAT (4.2 V) on IO0 when Q2 is off** (pin abs-max 3.6 V).
- Option A (Emil recommends): drop Q2, keep R7/R8 1M+1M as a permanent divider. The divider is 4.2 V / 2 M = 2.1 uA, total typ 21.6 uA, under the 25 uA target (worst 39.7 uA < 50 uA NFR-12). Removes a part (Q2, R6, one GPIO IO1 freed), no BOM addition, node never above 2.1 V. Cost: 2.1 uA about 0.05 mAh/day.
- Option B: keep the switched divider and make it safe with a high-side P-FET switch on the top of the divider (BOM change, 1 added part, 0 uA off). Saves 2.1 uA, costs a part and a pull-up on its gate.

**D-C6: no power path (charging while the board runs).** The TP4056 sees the load as charge current, so termination (end of charge) may not trigger while the board draws current, and the cell can be cycled by the load.
- Option A (Emil recommends): accept for v1. Document that the board needs a cell and that "charge complete" can be late while Wi-Fi is active; the sleep load (about 20 uA) is far below the TP4056 termination threshold (C/10 of 458 mA = about 46 mA), so it matters only when the board is awake. Cost: nothing.
- Option B: add a power path (P-FET ideal diode or load-sharing, 1-2 parts, about 0.1 uA). Lets the board run from USB with a flat or missing cell and removes the termination issue. Needs a BOM and layout change.

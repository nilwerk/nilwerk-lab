# PCB (Plan 4.P1: schematic) — Emil (PCB Designer)

KiCad 9 project `plant-monitor.kicad_pro` / `plant-monitor.kicad_sch` (one A1 sheet, net labels at every pin, no wires).
It is **generated** from [`design.py`](design.py) by [`gen_schematic.py`](gen_schematic.py) (no GUI was available);
[`check_netlist.py`](check_netlist.py) is the independent netlist/BOM/sleep check. Requirements: NFR-01 (best and typical case >= 3 months, worst case > 1 month; relaxed by Arsany 2026-11-08), NFR-12 (<= 50 uA, target 25 uA, A-027).
Layout is 4.P2 and not started. Nothing was ordered.

**Update 2026-11-08 (Arsany's answers):** A-034 the cell is the **EEMB LP603449-PCM from Amazon.de (ASIN B08FD39Y5R)**; NFR-01 relaxed; **A-045 Option A** and **A-046 Option A** applied (below). Cell facts and what is still unverified: [`../hardware/bom/cell-decision-A034.md`](../hardware/bom/cell-decision-A034.md).

## Status of the checks

| Check | Result |
|---|---|
| KiCad ERC (`kicad-cli sch erc`) | Runs in CI (job `pcb`, KiCad 9 container) on every push of this PR; not available in the agent session. 0 violations on 00edafe; the result for the A-045 head is in the PR report. |
| `python3 -I check_netlist.py` | all PASS (nets rebuilt from the file = model, no unconnected pin, no 1-pin net, BOM draft lcsc/qty = schematic, R9, strap pins, sleep sum) |
| Simulations (LDO dropout, divider, soil, charger, inrush) | **NOT RUN.** `ngspice` is not installed in this session and could not be installed (`pip` has no package). The LDO dropout limit is only a hand estimate, see "Fix round". |

## Charge current R9 (A-034 decided 2026-11-08)

Cell: EEMB LP603449-PCM, 1000 mAh minimum (1100 typical), maximum charging current 1100 mA, charge 0 to 45 C (Amazon.de listing, A+ text). `design.py` block `CHARGE CURRENT`: `CELL_MIN_MAH`, `CELL_MAX_CHARGE_MA`, `R9_OHM`, `R9_LCSC`. Recomputed for this cell: R_PROG = 1100 / I_BAT (TP4056 datasheet p. 9), target <= 0.5C = 500 mA. **R9 stays 2.4k (C22940): 458 mA = 0.46C of the minimum capacity (0.42C of typical); with the TP4056's +15 % tolerance 527 mA = 0.53C, below the 1100 mA cell maximum.** 2.2k would give exactly 0.50C (500 mA) but its LCSC number is not looked up and the USB 2.0 budget (500 mA, open point 3) has no room for it. USB draw is about 458 + 10 mA with no power path (A-046): inside 500 mA nominally; at +15 % tolerance (527 mA) the port limit is exceeded, accepted risk, see open point 3. `check_netlist.py` asserts <= 0.5C and tolerance <= cell maximum.

## Cell connector, NTC / TEMP (decided cell)

J2 = JST PH 2-pin (C295747): pin 1 = CELL+ (VBAT), pin 2 = CELL- (CELL_NEG). The listing says "JST plug" (picture 3 shows it) but **does not state the pitch or the polarity**: PH 2.0 mm is assumed and **unverified**; read it off the plug or the listing photo before ordering mating parts. An Amazon review of this listing reports a reversed plug: **check polarity with a meter before the first connection.** The listing mentions no NTC, so **TP4056 TEMP stays tied to GND (sense disabled, datasheet p.7)** and cold/hot charging (0 to 45 C only) is not enforced by the board. The Jauch 3-pin variant J2b (C564183) is not used.

## Sleep-current path and pin map

Generated: [`pinmap-sleep.md`](pinmap-sleep.md). Typical **21.6 uA**, worst **39.6 uA** vs NFR-12 25 / 50 uA (after A-045: +2.1 uA permanent divider), mostly assumptions.

## Differences against the BOM draft (hardware/bom)

All BOM lines match by LCSC number and quantity, except: **added** R13, R14 (4.7k I2C pull-ups, C23162 unverified) and R15 (1k DW01A CS, C21190); **removed** (A-045 Option A): Q2 and R6 (the BOM draft in `hardware/bom` still lists Q2 and R3-R6 qty 4: it needs Q2 deleted and R3-R6 qty 3, not done here, `check_netlist.py` declares the removal); footprints for SW1-3, U5, U6, E1 are custom names still to be drawn. `bom.csv` lists the schematic BOM; the BOM tab/CSV in `hardware/bom` was **not** edited (that is the Lead's/2.5 owner decision).

## Open points

1. ~~Battery sense, Q2 off: BAT_SENS floats to VBAT~~ **Closed (A-045 Option A, Arsany 2026-11-08):** Q2 and R6 dropped, R7/R8 1M+1M permanent divider (2.1 uA at 4.2 V), BAT_SENS never above 2.1 V, IO1 free.
2. **TEMP / cold charging:** cell may be charged 0-45 C only; the decided cell lists no NTC, TEMP grounded. Mitigation options: a GPIO on CE (CE internal default not read) or accept (indoor charging).
3. **USB 500 mA:** 458 mA charge + board load is at the USB 2.0 limit; TP4056 dissipates 0.78 W at 5 V in / 3.3 V cell (thermal foldback, not simulated).
4. **Double protection:** the decided cell has its own PCM (OC/OD/over-current/short per the listing), so U4/Q1/R15/C9 are a redundant second protection (series works; costs 4 parts and about 3 uA for the DW01A). Keep or delete is a decision for Arsany (not made here); deleting needs a link from CELL_NEG to GND.
5. ~~GPIO2 strap left unconnected~~ **Closed (Theo C4):** R16 10k to 3V3 on GPIO2 (Espressif datasheet v2.2 s.4.1 recommends a pull-up). No sleep current.
6. **USB data:** BOM says "power only"; D+/D- are wired to IO19/IO18 (USB Serial/JTAG) so D1 is meaningful. Arsany/Mira to confirm (affects flashing).
7. **Pin numbers: all now checked against datasheets** (see Fix round). Remaining: BH1750 DVI is tied directly to VCC; the datasheet wants DVI low >= 1 us after VCC (reset), example RC 1k/1uF. Decide in 4.P2 (add RC or accept and re-init in firmware).
8. Soil: electrode capacitance still assumed, no electrode ESD, wet/salty soil loading, U7 supply GPIO must be held low in deep sleep (firmware).
9. No power path (**A-046 Option A, Arsany 2026-11-08: accepted for v1; the board needs a cell**, document in the user guide: with USB only and no cell it does not run, and "charge complete" can be late while Wi-Fi is active): No VBUS fuse/TVS (only USBLC6). No DW01A VCC filter resistor. No VBUS-present or CHRG sense to a GPIO.
10. LDO Iq is 8 uA typ (datasheet, PS mode, 0.1 mA load; 18 uA max), 6 uA above the power-budget typical (2 uA, assumption A). Cost: 6 uA x 24 h = 0.144 mAh/day (about 53 mAh/year). The sleep sum in `pinmap-sleep.md` already uses 8 uA. `hardware/power-budget` keeps its 2 uA baseline rows; since 2026-11-08 it also has "as-built sleep" rows (LDO 8 uA, divider 2.1 uA, same sums as `pinmap-sleep.md`), see power-budget.md section 12.
11. ~~Cell A-034 decision~~ **Closed 2026-11-08:** EEMB LP603449-PCM; R9 recomputed (stays 2.4k). `firmware/main/board.h` does not exist; this pin table is the proposal. **IO1 is free (was BAT_SENS_EN): Mira must not drive it as a divider switch.**

## Fix round for Theo's review (PR #41, C1-C8)

| Item | Result |
|---|---|
| C1 AHT20 U5 | LCSC C2757850 resolved through the LCSC API (`wmsc.lcsc.com`) and its datasheet (Aosong/ASAIR, 2024-07, Table 5 and Figure 1): **6-pin DFN 3.0 x 3.0 x 1.0 mm**, 1 NC, 2 VDD, 3 SCL, 4 SDA, 5 GND, 6 NC. Symbol fixed (`design.py`), `pin_verified` now true, checked by `check_netlist.py`. Footprint `NW:AHT20_DFN-6_3x3` still to be drawn in 4.P2. Stock 32649 at the time of the call. |
| C2 pins | Read from the LCSC-linked datasheets: **U2** XC6220 SOT-25 (VIN 1, VSS 2, CE 3, NC 4, VOUT 5), **U4** DW01A (1 OD, 2 VM = CS, 3 OC, 4 TD, 5 VCC, 6 GND), **Q1** 8205A TSSOP-8 (package drawing: 1 D1, 2-3 S1, 4 G1, 5 G2, 6-7 S2, 8 D2; no numbered table in the datasheet, read from the drawing), **U6** BH1750 (1 VCC, 2 ADDR, 3 GND, 4 SDA, 5 DVI, 6 SCL), **J1** HRO TYPE-C-31-M-12 (signal-to-pad table; shield pad numbers belong to the footprint). Also checked: U3 TP4056 (1 TEMP, 2 PROG, 3 GND, 4 VCC, 5 BAT, 6 STDBY, 7 CHRG, 8 CE), U7 SN74LVC1G14 DBV (1 NC, 2 A, 3 GND, 4 Y, 5 VCC), D1 USBLC6-2SC6. All match the schematic. U1 was verified by Theo. `pin_verified=False` is gone from every part. |
| C4 GPIO2 | R16 10k 3V3 to GPIO2 added (declared addition, BOM qty of C25804 5). |
| C5 LDO dropout sim | **NOT RUN: ngspice unavailable.** Hand estimate only: datasheet gives 60 mV typ dropout at 300 mA (3.3 V version; the table row is ambiguous), the 3.4 V warning leaves 100 mV, so at a ~350 mA TX peak typ headroom is about 30 mV before the cell resistance drop (0.15 ohm x 0.35 A = 52 mV, assumed). That is negative margin: the rail may sag to roughly 3.25-3.3 V, which stays above the C3 brown-out level but this needs the real sim and the real cell resistance (4.P3). Do not take the estimate as a pass. LDO Iq 8 uA vs 2 uA in the budget: see open point 10. |
| C8 caption | Corrected (6.3 agent min, PR link, persona, no ratio). |
| C3, C6 | Decisions below, not changed. |

## Decisions (answered by Arsany 2026-11-08)

**D-C3 / A-045: ANSWERED 2026-11-08, Option A approved.** Q2 and R6 dropped, R7/R8 1M+1M stay as a permanent divider (4.2 V / 2 MOhm = 2.1 uA, about 0.05 mAh/day; total typical 21.6 uA under the 25 uA target, worst 39.6 uA under the 50 uA NFR-12 limit). BAT_SENS never exceeds 2.1 V on IO0; IO1 is free. Applied in `design.py`, the schematic, `bom.csv`, `pinmap-sleep.md`. (Option B, a high-side P-FET switch, was not chosen.)

**D-C6 / A-046: ANSWERED 2026-11-08, Option A approved.** No power path in v1. **The board needs a cell to run** (USB alone, with no cell connected, does not power it reliably, and charge termination can be late while the board is awake and drawing current; the sleep load of about 22 uA is far below the TP4056 termination threshold of about 46 mA, so it matters only when awake). To go into the user guide and the work order for Peter (power the board only with the cell fitted). (Option B, a P-FET ideal diode, was not chosen.)

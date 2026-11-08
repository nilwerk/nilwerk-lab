# Hardware BOM (Plan 2.5, revision 3 = synced with the 4.P1 schematic, 2026-11-08)

Author: Emil (PCB Designer). Branch `agent/pcb/2.5-followup`. CSV: [`bom-draft.csv`](bom-draft.csv) (rebuilt by [`refresh_live.py`](refresh_live.py)), cost tables from [`bom_calc.py`](bom_calc.py), tests in [`test_bom.py`](test_bom.py).
Live data re-read **2026-11-08 15:12 UTC (16:12 Berlin)** (as in the CSV) from `lcsc.com/product-detail/<C#>.html` (stock, price breaks, sales status) and the public JLCPCB parts search (JLC stock, library type, preferred flag). Prices are **USD as shown on LCSC**; stock and prices change daily.

> **No PCBA order and no purchase until Arsany has approved the order.** Nothing was ordered or bought (hard rule). The three G2 conditions (R9, cell + connector, soil front end) are now in the schematic (4.P1 sync, 2026-11-08; this banner supersedes the earlier "three G2 conditions pending" text). Still open: (a) the cell B1 (EEMB LP603449-PCM, A-034) has **no verified price, seller or stock, and its plug pitch and polarity are unverified**: nothing may be ordered until polarity is metered on the received cell; (b) the soil front end is a sized proposal that still needs simulation and measurement (4.P1 / 5.x); (c) the footprints of SW1-3, U5, U6 and E1 are still to be drawn.

## What changed against the G2 draft

| G2 condition | Done in this revision | Still open |
|---|---|---|
| R9 wrong for a 1000 mAh cell (1.2k = about 0.9 A) | R9 = **2.4 kOhm** (C22940, Basic), 458 mA = 0.46C, formula from the TP4056 datasheet (section "R9") | thermal and cell-temperature behaviour in 4.P1 |
| Missing cell + connector | B1 cell line (LP603449 class, **1000 mAh minimum**) with JST PH plug mating J2 (C295747); cell data from the EEMB datasheet | **cell price/stock/seller unverified**; polarity of the cell plug vs J2 must be checked on receipt; NFR-01 (3 months, A-020) is met in the typical case at 1000 mAh (4.5 months), see "Cell" |
| Missing soil front end | U7 SN74LVC1G14 + R12 470k + 1 more 100 nF; Q3 (gate MOSFET) dropped, U7 powered from a GPIO; sizing script with pass/fail | probe capacitance range is an **assumption**; real sim/measurement in 4.P1/5.x |
| Swap Extended for Basic where possible | D3 green LED to Basic KT-0805G; U3 TP4056 is Preferred (fee-exempt, newly readable); the rest has no Basic equivalent that I found | see "Variants" for 2 cost-down options that need a design decision |
| 2.5 flag: JLC fee not read | Fee read from the JLC price page: **3.07 USD per Extended part** (Economic), 8.18 setup, 1.53 stencil | the quote in the JLC cart is still the final word |

## Result: cost per board at 3 and 1000 boards

Components + JLC Economic PCBA loading fee (Extended, non-Preferred parts only) + setup and stencil, **excluding** bare PCB, assembly labour beyond the fees, the **cell (no live price)**, shipping/duty/VAT, enclosure, attrition. EUR at an **assumed** 0.90 EUR/USD (unverified).

| | 3 boards | 1000 boards |
|---|---|---|
| Components per board (45 pieces, 31 CSV lines, of which 3 are alternatives not in the sums: B2, B3, J2b; B1 is the decided cell, no price) | 6.57 USD | 4.01 USD |
| Loading fee: 10 Extended non-Preferred parts x 3.07 USD per order | +10.23 USD / board | +0.03 USD / board |
| Setup 8.18 + stencil 1.53 USD per order | +3.24 USD / board | +0.01 USD / board |
| **Total per board** | **20.04 USD (EUR 18.03)** | **4.05 USD (EUR 3.65)** |
| Same rules as the first draft (fee only, no setup/stencil) | 16.88 USD; first draft said 17.89 | 4.07 USD; first draft said 4.07 |
| Target about 10 EUR (NFR-09) | **missed at 3 pcs** (the fee and setup dominate: 67 % of the total); components alone are met | met for components alone; the full unit cost is not known (PCB, assembly, cell, shipping missing) |

The 3-board price uses LCSC's first price break (minimum order), as in the first draft; JLC prices at 1 pc differ by a few percent. Fee source: `jlcpcb.com/help/article/pcb-assembly-price` (Economic PCBA: 3.07 USD per Extended part, 8.18 setup, 1.53 stencil; Standard PCBA 1.53 per unique part, Basic or Extended) and `/pcb-assembly-faqs` (FAQ 7: Preferred Extended parts are exempt from the Economic feeder loading fee; FAQ 6: Basic parts carry no labour cost), pages read 2026-11-07 through a page-summary tool, so re-check in the cart. Economic needs 10 x 3.07 = 30.70 USD per order; Standard would charge 1.53 x 25 unique parts = about 38.3 USD, so Economic stays the cheaper choice for the prototype.

### Variants (design decisions, not applied)

| Variant | Extended parts paying the fee | 3 boards USD/board (components + fee + setup/stencil) | 1000 boards USD/board |
|---|---|---|---|
| A baseline (this BOM) | 10 | 20.04 (EUR 18.03) | 4.05 (EUR 3.65) |
| B zero-IC soil front end (RC timing on GPIO, no U7/R12, one cap less) | 9 | 18.94 (EUR 17.04) | 4.00 (EUR 3.60) |
| C = B + cell with built-in protection (no U4/Q1) | 7 | 16.78 (EUR 15.10) | 3.91 (EUR 3.52) |
| D = A, delete the second protection (cell has a PCM): no U4/Q1/R15, C9 (one 100 nF) | 8 | 17.86 (EUR 16.08) | 3.96 (EUR 3.56) |

**D** is the question for Arsany (second protection with a PCM cell, `pcb/README.md` open point 4): it saves 2 Extended parts (U4, Q1) and so 6.14 USD of loading fee per order of 3 boards. B replaces U7 by timing the RC charge of the probe with ESP32 GPIOs (no extra IC); the ESP32 input thresholds are **not read**, so B is unproven. C additionally buys the cell with a built-in protection module (PCM) and drops DW01A + 8205A; a PCM cell is a different purchase spec and removes board-level protection tuning. Both are for Arsany/4.P1; neither is in the numbers above.

## R9: charger programming resistor for a 1000 mAh cell

Datasheet read: **TP4056 (NanJing Top Power ASIC), REV_2.4**, `https://datasheet.lcsc.com/datasheet/pdf/d328ee101cbb1f3719611cd61db479c2.pdf` (LCSC C16581 datasheet, 15 pages).

- Formula (datasheet page 9, "Programming Charge Current"): **R_PROG = 1100 / I_BAT** (R in kOhm, I in mA); inverse, page 7 PROG pin: I_BAT = (V_PROG / R_PROG) x 1100 with V_PROG = 1 V in constant-current mode.
- Datasheet table (p. 9): 2 kOhm = 580 mA, 3 kOhm = 400 mA, 1.2 kOhm = 900 mA, 1.1 kOhm = 1000 mA. Electrical characteristics (p. 1): R_PROG = 2.2 kOhm gives 425 / **500** / 575 mA (min/typ/max).
- The cell (EEMB LP603449 datasheet: 1100 mAh nominal, **1000 mAh minimum**, maximum charge 1C = 1100 mA, charge temperature 0 to 45 C): target 0.5C of the 1000 mAh minimum = 500 mA.
- Exact: 1100 / 500 mA = **2.2 kOhm**. E24 value chosen: **2.4 kOhm** (C22940, 0603WAF2401T5E, Basic) = **458 mA = 0.46C** of 1000 mAh (0.42C of 1100). With the datasheet's +15 % current tolerance the worst case is 527 mA = 0.53C, below the 1C cell limit. Cost of the choice: about 8 % longer charge time than 2.2k. 2.2 kOhm would give exactly 500 mA nominal but up to 575 mA = 0.58C.
- The first draft's 1.2k gave 917 mA by the formula (datasheet table: 900 mA) = 0.9C of the cell, about twice the target.
- Check for 4.P1 (**not simulated**): the TP4056 is a linear charger. At 458 mA from USB 5 V with the cell at 3.3 V the chip dissipates (5.0 - 3.3) x 0.458 = 0.78 W; the datasheet states thermal regulation at 145 C junction (p. 8) so the current folds back instead of overheating; the real charge time and the package thermal resistance were not read. Also a USB 2.0 port limit is 500 mA: 458 mA plus the board load is at the limit. The TEMP pin: the datasheet allows disabling cell temperature sense by grounding TEMP (p. 7), but then charging below 0 C is not blocked while this cell may be charged only at 0 to 45 C (outdoor winter use): 4.P1 must decide NTC or not.

## Cell and connector (B1, J2)

| | Value | Source |
|---|---|---|
| Reference cell | EEMB **LP603449**: 1100 mAh nominal, **1000 mAh minimum** (0.2C), 3.7 V, <= 50 x 34.5 x 6.3 mm, 22 g, internal resistance <= 40 mOhm, max charge 1100 mA (1C), max discharge 2200 mA, cutoff 2.75 V, charge 0-45 C, discharge -20 to 60 C | `eemb.com/product-147` and its datasheet PDF `eemb.oss-accelerate.aliyuncs.com//uploads/20230311/02fb7ee3e9c911840613a2a78b2d1483.pdf`, read 2026-11-07 |
| Variant offered | **bare cell with solder tabs**, no PCM, no connector listed; price "request quote" | same page |
| LCSC part number / stock / price | **none found; unverified.** JLC search for 603449 returned 0 hits; LCSC search is blocked for scripts; JLC does not assemble cells | this session |
| Purchase spec to be placed by Arsany | 603449 pouch, >= 1000 mAh minimum rated, **with PCM**, 2-pin JST PH 2.0 mm plug (or solder tabs and a pigtail) | proposal |
| Board-side connector J2 | JST S2B-PH-SM4-TB(LF)(SN), C295747, SMD, right angle, LCSC stock 5,920 / JLC 7,859, Extended, 0.2284 USD at 5 pcs / 0.1392 at 1000. Clone XY-S2B-PH-SM4-TB C54582899 is cheaper (0.0472 / 0.0288) but mechanical equivalence is unverified | live |
| Mating side | The plug on the cell lead. Housing PHR-2 is C157955 (0.0135 USD, Extended, stock 184,920 on JLC) if a pigtail is made in-house; not added to the BOM | live |
| Risk | Cells with a JST plug from the open market often have **reversed polarity** relative to the board header: check plug pin 1 against J2 before the first connection (a reversed cell destroys the board). No claim on a specific vendor | general hardware experience, no datasheet |

**NFR-01 with this cell (3 months, A-020).** Using the model (power-budget.md section 11): typical case **4.5 months at 1000 mAh** (4.9 at 1100 mAh nominal) = **PASS** with about 1.5x margin; with the datasheet-based currents 4.3 / 4.7 months. Rated capacity needed for 3 months: about **668 mAh** typical (699 with datasheet currents). The worst-case stack (every parameter at its worst at once) gives 1.4 months at 1000 mAh: a **stress bound to be measured in 5.4**, not a design point. The 6-month stretch goal (information only) is missed at 1000 mAh (4.5 months); a 1500 mAh cell would reach 6.4-6.7 months but may not fit the enclosure (envelope unknown, power-budget.md section 8).

## Soil front end (U7, R12)

Capacitive probe interface for the PCB-copper electrodes on the stake. The ESP32-C3 has no touch-sensor peripheral, so an oscillator and frequency count is used.

- **U7 SN74LVC1G14DBVR** (TI, C7835, SOT-23-5, Extended, LCSC stock 227,070 / JLC 227,010, 0.0586 USD at 10 pcs, 0.0402 at 1000): Schmitt-trigger inverter. **R12 470 kOhm** (C23178, Basic) from output to input, probe capacitance from input to GND: RC relaxation oscillator. U7 is **powered from an ESP32 GPIO** (low = off, 0 uA; supply current is at most 10 uA per datasheet), so the gate MOSFET Q3 is dropped (the battery divider has no switch any more: Q2 and R6 were deleted, A-045 Option A). The ESP32 counts the output edges with PCNT for a 20 ms gate: wetter soil = more capacitance = lower frequency.
- Datasheet read: **SN74LVC1G14, SCES218AA (revised October 2025)**, `https://www.ti.com/lit/ds/symlink/sn74lvc1g14.pdf`, section 5.5 Electrical Characteristics, DBV package, 3 V row: V_T+ 1.50-1.87 V, V_T- 0.84-1.14 V, I_CC <= 10 uA, C_i 4.5 pF typ (3.3 V), delta I_CC <= 500 uA at one input at V_CC - 0.6 V. The table has **no 3.3 V row**; the 3 V row is used for the thresholds and for V_CC in the formula.
- Script with pass/fail limits: [`../soil-frontend/soil_frontend.py`](../soil-frontend/soil_frontend.py), tests [`../soil-frontend/test_soil_frontend.py`](../soil-frontend/test_soil_frontend.py). Formula f = 1 / (R C [ln((V_CC - V_T-)/(V_CC - V_T+)) + ln(V_T+/V_T-)]). All four threshold corners and R +-1 %. With the probe capacitance **assumed** 5 to 50 pF (+ 4.5 pF input + 3 pF parasitic, also assumed): f = 25 kHz (worst corner, wet) to 351 kHz (dry), nominal 178 kHz dry / 39 kHz wet, at least 506 counts in the 20 ms gate and at least 1821 counts of dry-to-wet spread at the worst corner. All four limits PASS (limits are mine: f >= 10 kHz, f <= 2 MHz, >= 200 counts, >= 100 counts spread).
- **Not verified:** the electrode capacitance (the assumed 5-50 pF is not from a measurement or datasheet; if it is far outside, R12 must change, a 0603 value change costs nothing), the 3.3 V threshold shift, soil conductivity effects (wet salty soil is a resistive load in parallel to the electrodes and will pull the oscillator), temperature drift of the probe, ESD on the exposed electrodes. This is a sized proposal; the circuit simulation (role rule "soil-sensing front end response") belongs to 4.P1 and the measurement to 5.x. Power cost: delta I_CC bound 0.5 mA during the 20 ms gate x 96 wakes/day = about 0.0003 mAh/day, negligible against the model's 5.9 mAh/day.

## Lines

Generated by `bom_calc.py` from the CSV; a test keeps this text identical. "Type" = JLCPCB library type on the live part page (`base` = Basic, `expand` = Extended); "Preferred" = JLC preferred flag (only U3 is True). **B1** is the decided cell (EEMB LP603449-PCM, A-034, Arsany 2026-11-08; order 5 = 3 builds + 2 spare; price, plug and polarity unverified) and has no LCSC price, so it is outside the sums as `unverified`. **B2** (Jauch LP503030JU), **B3** (Jauch LP603443JU) and the connector alternative **J2b** are superseded candidates, flagged `alternative` and not in the sums. **Cell decision after A-034: [`cell-decision-A034.md`](cell-decision-A034.md)** (the Jauch LP503030JU fails NFR-01; LP603443JU passes but is 0.2 mm too thick for the A-020 bay).

| Line | Qty | LCSC | Type | Preferred | 3 pcs unit | 1k unit | USD/board 3 | USD/board 1k |
|---|---|---|---|---|---|---|---|---|
| U1 | 1 | C2838502 | expand | False | 3.0672 | 2.0536 | 3.067 | 2.054 |
| U2 | 1 | C86534 | expand | False | 0.4803 | 0.2245 | 0.480 | 0.225 |
| U3 | 1 | C16581 | expand | True | 0.1869 | 0.1121 | 0.187 | 0.112 |
| U4 | 1 | C351410 | expand | False | 0.0250 | 0.0172 | 0.025 | 0.017 |
| Q1 | 1 | C5148694 | expand | False | 0.0834 | 0.0598 | 0.083 | 0.060 |
| U5 | 1 | C2757850 | expand | False | 0.8054 | 0.4423 | 0.805 | 0.442 |
| U6 | 1 | C78960 | expand | False | 0.9295 | 0.5019 | 0.929 | 0.502 |
| U7 | 1 | C7835 | expand | False | 0.0586 | 0.0402 | 0.059 | 0.040 |
| J1 | 1 | C165948 | expand | False | 0.1887 | 0.1051 | 0.189 | 0.105 |
| D1 | 1 | C7519 | expand | False | 0.1639 | 0.0897 | 0.164 | 0.090 |
| J2 | 1 | C295747 | expand | False | 0.2284 | 0.1392 | 0.228 | 0.139 |
| SW1,SW2,SW3 | 3 | C318884 | base | False | 0.0208 | 0.0141 | 0.062 | 0.042 |
| D2 | 1 | C2286 | base | False | 0.0077 | 0.0059 | 0.008 | 0.006 |
| D3 | 1 | C2297 | base | False | 0.0166 | 0.0129 | 0.017 | 0.013 |
| R1,R2 | 2 | C23186 | base | False | 0.0016 | 0.0012 | 0.003 | 0.002 |
| R3-R5 | 3 | C25804 | base | False | 0.0022 | 0.0019 | 0.007 | 0.006 |
| R16 | 1 | C25804 | base | False | 0.0022 | 0.0019 | 0.002 | 0.002 |
| R7,R8 | 2 | C22935 | base | False | 0.0018 | 0.0014 | 0.004 | 0.003 |
| R9 | 1 | C22940 | base | False | 0.0026 | 0.0020 | 0.003 | 0.002 |
| R10,R11 | 2 | C21190 | base | False | 0.0017 | 0.0014 | 0.003 | 0.003 |
| R12 | 1 | C23178 | base | False | 0.0030 | 0.0024 | 0.003 | 0.002 |
| R13,R14 | 2 | C23162 | base | False | 0.0028 | 0.0023 | 0.006 | 0.005 |
| R15 | 1 | C21190 | base | False | 0.0017 | 0.0014 | 0.002 | 0.001 |
| C1-C4 | 4 | C19702 | base | False | 0.0205 | 0.0119 | 0.082 | 0.048 |
| C5-C11 | 7 | C14663 | base | False | 0.0157 | 0.0091 | 0.110 | 0.064 |
| C12,C13 | 2 | C15849 | base | False | 0.0110 | 0.0074 | 0.022 | 0.015 |
| C14 | 1 | C59461 | base | False | 0.0172 | 0.0114 | 0.017 | 0.011 |
| **Total components** | 45 pcs | | | | | | **6.57** | **4.01** |

## Swaps Extended to Basic: what was checked

Method: public JLCPCB parts search, filter library type = Basic, by model keyword; absence from that search means **I found none**, not that none exists.

- **Done:** D3 green LED KT-0603G (C12624, Extended) to **KT-0805G (C2297, Basic, 0805, JLC stock 1,967,310)**; same function.
- **U3 TP4056 (C16581)** is flagged Preferred on JLC: Economic loading fee exempt (FAQ 7), so it no longer counts in the fee although it is "Extended".
- **No Basic equivalent found for:** TP4056 charger, DW01A, 8205A, USBLC6-2SC6 / any USB ESD array, USB-C 16-pin, JST PH SMD, AHT20, BH1750, Schmitt-trigger gate, ESP32-C3 module.
- **LDO (U2):** the Basic LDOs in the JLC library are XC6206P332MR-G (C5446, **200 mA** per LCSC listing), HT7533-1 (C14289, **100 mA** per listing), AMS1117-3.3 (C6186, mA-class Iq, excluded in the power budget), none carries the 340 mA Wi-Fi TX peak (datasheet Table 5-7) with a low Iq. XC6220B331MR-G (C86534, listing: 1 A, 8 uA, 655 mV dropout at 1 A) stays Extended. Listing values, not datasheets (**unverified**).
- **100 nF (C5-C11):** Yageo C14663 has **0 stock on LCSC but about 34 million on JLC** (34,060,230 at the refresh of 2026-11-08 15:12Z, see the CSV); the Samsung alternative C1591 is Extended. Keep C14663 and re-check at order time (the first draft's "7,150 in stock" flag is obsolete).

Net: Extended parts on the board 11 (the first draft had 11: D3 swapped out, U7 added); fee-bearing parts **10** because U3 is Preferred.

## Flags: unverifiable or open

1. **Cell: no live price, stock or seller** (section "Cell"); Arsany owns the purchase spec (with PCM, PH plug, polarity check) and the order. Capacity is not a blocker (NFR-01 typical passes).
2. **EUR rate** 0.90 is an assumption.
3. **JLC fee amounts** read from the price page via a summary tool, not from a quote in the cart; the preferred exemption is stated under Economic assembly only.
4. **Lifecycle:** LCSC `productCycle` is "normal" for every priced line (LCSC sales status, not a manufacturer active/NRND/EOL statement); manufacturer status unverified (Espressif, ROHM, Aosong, Torex, TI).
5. **Datasheet-level parameters still unread:** XC6220 (Iq, dropout), DW01A, 8205A (Iq/leakage, Rds(on)), AHT20, BH1750, ESP32-C3-MINI-1 module. Read in this revision: TP4056 (R9), SN74LVC1G14 (soil), ESP32-C3 series v2.4 (power budget), EEMB LP603449 (cell).
6. **Prices and the 3-board basis:** first LCSC break; real JLC cart prices differ slightly; stock moves daily.
7. **Minimum order and packaging** as in the first draft (reels at 1k).
8. **AHT20 variants** (C2757850 used; C503357 DFN-6, AHT20-F C3012622): pick one footprint in 4.P1.
9. **Synced with the schematic (2026-11-08, 4.P1 sync):** Q2 deleted and R6 gone (A-045 Option A, divider permanent), R3-R5 qty 3, added R13/R14 (I2C pull-ups), R15 (DW01A CS) and R16 (GPIO2 pull-up); B1 is the decided EEMB LP603449-PCM. `pcb/bom.csv` = this CSV (check_netlist.py compares them). Prices moved by a few cents; live data re-read 2026-11-08 15:12 UTC (LCSC `productCycle` is empty for lines read through the JSON fallback).
10. **Out of scope here:** schematic (4.P1), layout, enclosure and cell bay (Yara).

## Checklist for 4.P1 (Theo's conditions, review of PR #30)

- [ ] **Soil front end:** simulate (ngspice, probe C range and threshold corners) and later measure on the real stake; replace the assumed 5-50 pF with a measured range; check wet/salty soil (resistive load) and electrode ESD.
- [ ] **U7 supply GPIO held low in deep sleep** (NFR-12: whole-board deep sleep <= 50 uA, target 25 uA): GPIO must hold level (RTC/hold) through deep sleep, or U7 floats/draws; verify in the schematic and measure in 5.2.
- [ ] **TP4056 TEMP pin: NTC or not.** Grounding TEMP disables temperature sense (datasheet p. 7), but this cell may be charged only at 0 to 45 C; decide NTC (cell has no NTC wire) or accept the outdoor-winter risk, and document it.
- [ ] **500 mA USB limit check:** 458 mA charge current plus board load against the USB 2.0 500 mA budget (and the CC 5.1k default-power advertisement); also TP4056 thermal foldback at 5 V in / 3.3 V cell.
- [ ] R9 = 2.4k (C22940), J2 polarity vs the cell plug, DW01A/8205A and XC6220 datasheet reads (Iq, leakage, dropout) still open.

Lessons: see the PR comment.

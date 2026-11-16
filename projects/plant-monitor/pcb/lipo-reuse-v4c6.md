# LiPo connector and charger: what to reuse from `v4_c6_lipo` (Emil, 2026-11-14)

Status: DESIGN NOTE, a recommendation, not a decision. No schematic, BOM, footprint or board file was changed.
Request: owner's extra round, 2026-11-14 (reuse what is good from Arsany's earlier board for a clean LiPo connector and charger option).

## 0. What was read and how

| Source | Read | Not read |
|---|---|---|
| Drive `v4_c6_lipo` (folder `1FXh76OPGqxBkrfGh78QNGHLYj-hBONJI`), read-only via the Drive connector | schematic PDF `1YuNUccizv4PZH2eigjAhXph7R87Se0xG` (text layer only: the layout is scrambled, so values below that I could not tie to a reference are marked), `bom/bom.csv`, `README.md` | the Gerber zip `1b4TndLXNjNlvMwOUjAeSD-v3HxCg6Dhs` (not opened, not needed for a schematic comparison), `.kicad_sch`, `.kicad_pcb`, the schematic as a picture |
| Microchip MCP73871 datasheet DS20002090F via the LCSC link of C5121473 (downloaded to a fresh empty directory, parsed with `pdftotext`, nothing executed) | supply current, output reverse leakage, IREG formula, PROG2/SEL behaviour | the application-circuit chapters in full |
| TI TPS63031 datasheet (`ti.com/lit/ds/symlink/tps63031.pdf`) | quiescent and shutdown current table | the rest |
| Our repo | `pcb/README.md`, `pcb/bom.csv`, `pcb/design.py` (J2, U3), `pcb/pinmap-sleep.md`, `pcb/jlcpcb/bom-lcsc.csv`, `hardware/bom/cell-decision-A034.md`, `hardware/power-budget/power-budget.md` | datasheets of TP4056, DW01A, 8205A, XC6220 (not re-read, our numbers for them are the repo's existing assumptions) |

Everything from `v4_c6_lipo` is internal reference only (its README: the v3 source had no general reuse licence). Nothing is copied into the repo; this note quotes designators and LCSC numbers only. v4 is a KiCad 10.0.8 project and we use KiCad 9, so no file can be copied across anyway.

## 1. Side-by-side

| Item | `v4_c6_lipo` (ESP32-C6) | Ours (ESP32-C3, `pcb/`) |
|---|---|---|
| MCU module | ESP32-C6-MINI-1U-H4, U4, C20627095 (external antenna, W.FL) | ESP32-C3-MINI-1-N4, U1, C2838502 (PCB antenna) |
| USB-C | J1 GCT USB4105-GF-A, C3020560 | J1 HRO TYPE-C-31-M-12, C165948 |
| Charger | **U5 MCP73871-2CCI/ML**, QFN-20, C5121473 (4.20 V option, "-2"; the BOM text does not show the option letter set, read from the part number) | **U3 TP4056** (TP4056-42-ESOP8), C16581 |
| JLC class | UNVERIFIED (v4 README says its stock/class claims are not live-checked; I did not query LCSC) | Extended (`pcb/jlcpcb/bom-lcsc.csv`, verified-live 2026-11-09) |
| Power path | **yes**: charger OUT = SYS_IN feeds the regulator, BAT to the cell, so the system runs from USB while charging and the cell is not in the load path when USB is present | **no** (A-046 Option A, Arsany 2026-11-08): load hangs on VBAT, TP4056 sees it |
| Regulator | **U1 TPS63031DSKR** buck-boost to 3.3 V, C15516, with L1 2.2 uH SRN4018 C913207 and C10 22 uF 1206 | **U2 XC6220B331MR-G** LDO, C86534 (Extended), from VBAT |
| Charge current | PROG1 resistor R13 4.02k (C491130) and PROG3 R14 40.2k (C137723): IREG = 1000 V / R_PROG1 per datasheet, so about **249 mA** (R13 to PROG1 is my reading of a scrambled PDF, UNVERIFIED). In USB mode (SEL low) the input limit is PROG2: low = 100 mA, high = 500 mA | **R9 2.4k (C22940) = 458 mA** (0.46C of 1000 mAh), nominal USB-2.0 limit use |
| USB current limit | SEL and PROG2 selectable; schematic note "USB limit defaults to 100 mA; populate R15 (0R, DNP) only for a verified 500 mA source" | none: fixed 458 mA, no negotiation |
| Input sense | VPCC divider from +5 V (R16/R17/R18 100k/270k/100k, C116674 / C403123, exact assignment UNVERIFIED), makes the charger back off a weak source | none |
| Battery temperature | THERM biased by **R19 10k to GND (C98220)**. The schematic says "biases THERM only, no battery temperature measurement". Per datasheet ITHERM = 50 uA typ, so 10k = 0.5 V = about a 10k NTC at room temperature: it fakes a healthy pack, it does not disable the check | TEMP **tied to GND = sense disabled** (TP4056 datasheet p. 7, per repo). Both designs have no cold/hot charge protection; both are the same risk |
| Status | STAT1/STAT2/PG to LED D3 + R11 0.33k and test pads; v4 LED is always-on (about 3 to 4 mA by Emil's earlier estimate, not measured) | CHRG/STDBY LEDs D2/D3, R10/R11 1k, no current when USB is unplugged |
| Cell protection | none on the board (relies on the pack) | DW01A U4 + 8205A Q1 (redundant with the cell's own PCM; open point 4 in `pcb/README.md`) |
| Cell connector | **J4 JST B2B-PH-K-S(LF)(SN)**, THT vertical 2.00 mm, C131337 (JLC class UNVERIFIED) | **J2 JST S2B-PH-SM4-TB(LF)(SN)**, SMD side-entry 2.00 mm with mounting pads, C295747, Extended |
| **Polarity (board side)** | **J4 pin 2 = BAT+, pin 1 = GND** (schematic note: "Verify received pack polarity before connection") | **J2 pin 1 = CELL+ (VBAT), pin 2 = CELL- (CELL_NEG)** (`design.py`, `pcb/README.md`) |
| Mismatch flag | **The two boards are wired opposite: a pack that plugs correctly into J4 is reversed in J2 and vice versa, for the same JST-PH-2 plug.** The orientation of pin 1 on a B2B (vertical) and an S2B (side-entry) is not necessarily the same physical side either, so nothing from J4's layout can be copied. Arsany's real EEMB LP603449-PCM plug: pitch and wire polarity **UNVERIFIED** until read from a real cell (an Amazon review of that listing reports a reversed plug). | same |
| Sleep current of the power stage | MCP73871 output reverse leakage **30 uA typ / 40 uA max** (datasheet DS20002090F, conditions "VBAT = Power Out, no load" and shutdown) plus TPS63031 quiescent **25 uA typ / 35 uA max** (TI table, IOUT = 0, VIN = 3.6 V); sum **55 typ / 75 max uA** | TP4056 BAT drain 3/6 uA (assumption) + DW01A 3/6 + 8205A 0.05/1 + XC6220 8/10 = **14 typ / 23 max uA** (`pinmap-sleep.md`) |
| Effect vs NFR-12 (target 25 uA, limit 50 uA, whole board) | n/a | board total 21.6 typ / 39.6 worst uA today |
| Dropout at low cell | buck-boost: no dropout, can use the cell down to its cutoff | LDO: 3.3 V rail dips under TX at a cell of 3.3 V or lower (`sim/ldo_dropout.txt`); the 3.4 V warning keeps us inside the limit |
| What v4 adds that we lack | VPCC input sense, USB 100/500 mA select, power path, buck-boost headroom | n/a |

## 2. What it costs us in sleep current and battery life (derived, not measured)

Replacing TP4056 + LDO (14 typ / 23 max) with MCP73871 + TPS63031 (55 / 75), with our DW01A/8205A counted as removed in the 14/23 figure (v4 has no protection IC; if we kept them the delta is about 3 uA typ larger):

- Whole-board sleep: 21.6 + 41 = **62.6 typ uA** (limit 50, target 25) and 39.6 + 52 = **91.6 worst uA**. **NFR-12 fails in both cases.**
- NFR-01 (rule: 0.8 x rated capacity / average current, 1000 mAh minimum cell, power-budget typical average 0.244 mA, stack averages from `power-budget.md` section 1): typical 4.5 months becomes about 800 / 0.285 = 2807 h = **3.8 months** (needs 3, margin 1.28x instead of 1.5x); the worst stack of about 1.4 months drops to about 1.3 months (needs more than 1). Still inside the relaxed NFR-01, but it burns most of the margin, UNVERIFIED because every current in the budget is an unmeasured assumption (5.4 decides).
- Caveat: the MCP73871 leakage is the datasheet's "VBAT = Power Out, no load" row; whether it is that large in our wiring with USB unplugged is a bench question. Nobody has measured it.

## 3. Recommendation (not a decision)

**Keep TP4056 + J2 for v1; take the parts of v4 that cost nothing in sleep current; defer MCP73871 + TPS63031 to a v2 or a variant if a measurement says the TP4056 "late full" behaviour hurts.**

Why:
1. NFR-12 and NFR-01. The MCP73871 + TPS63031 stack alone is 55 uA typ, more than the whole-board limit of 50 uA. This is a stack-level finding from two datasheet tables, not a guess, but it is an unmeasured datasheet number. Only a bench measurement of a real board settles it (5.2 / 4.P5).
2. A-046 Option A (no power path, board needs a cell) was answered by Arsany on 2026-11-08. v4 is the Option B family. Reversing it is his decision, not ours.
3. Cost and risk. Our TP4056 + LDO path is already in the dry-run (11 Extended unique parts on the whole board). MCP73871 is a 4x4 mm QFN-20 with exposed pad (hand rework harder, one more footprint to draw and check: our 4.P2 slice 3 is still not routed), plus an inductor and a 22 uF 1206 for the buck-boost, so more BOM lines and more Extended loading fees: fee value UNVERIFIED (not read), same open item as `dry-run-checklist.md` A8. I did not query live prices or stock; cost delta UNVERIFIED.
4. What power path would give us: no "charge complete" delay while Wi-Fi is awake on USB (TP4056 termination is about 46 mA by repo estimate, below an awake load), operation from USB with no cell, and no LDO dropout trouble. None of these is an NFR today (FR-D06 is a firmware-visible delay only).
5. If a power path is wanted later with less leakage, the cheaper route is A-046 Option B (P-FET ideal diode) kept on the table; I did not re-research it here.

Reusable now, at zero sleep cost:
- **A silkscreen polarity mark and a polarity-check line in the dry-run checklist for J2** (see section 4). Cost: nothing.
- **VPCC-style soft input limit** is not available on TP4056. Substitute: if the USB-2.0 overrun (527 mA at +15 %) bothers Arsany, drop R9 to a value for about 300 mA at the cost of 3 h charge time; this is a parameter decision, not a v4 reuse.
- **THERM lesson**: do not claim "sense disabled" by biasing; TP4056 TEMP to GND is the documented disable, keep the wording we already have in `pcb/README.md`.
- **Process ideas** already recorded in `skills/references/old-projects.md` (BOM grouping by LCSC code, CPL assertions, order notes) are unrelated to the charger and stay in their own task.

Not reusable as is:
- **MCU-side**: all C6 pins, the MINI-1U antenna, USB on GPIO12/GPIO13 (ours IO18/IO19), BME680 (we use AHT20 + BH1750), I2C and strap network of U4. C6 vs C3 matters only here, not for the charger.
- **J4 as a part**: B2B-PH-K is THT vertical, ours is the SMD side-entry J2 on a flat edge for the enclosure; the footprint, the height and the pin-1 side differ.
- **The always-on LED** (3 to 4 mA).
- **R19 THERM bias** for a cell without NTC: not relevant to TP4056.

## 4. Changes Emil would make next (each needs a go; none done in this slice)

Safe, small (no outline change, no new part):
1. `design.py` J2 note + `gen_pcb.py` silkscreen: print `+` next to J2 pin 1 and `-` next to pin 2, and put the pack plug label name in the silk (about 15 min incl. regenerate and both checks). Needs Yara to hear about it only if the silk text moves a courtyard.
2. `pcb/jlcpcb/dry-run-checklist.md`: add a line before the first cell connection: read the real EEMB plug, compare against J2 pin 1 = CELL+ with a meter, and if it is reversed use a re-crimped pigtail, not the board. Mention that v4_c6_lipo J4 is wired the other way round (pin 2 = BAT+), so **never swap a pack between the two boards.**

Conditional on Arsany's choice (below):
3. If MCP73871 is wanted: new symbol and footprint (QFN-20 4x4, EP 2.5x2.5 from the datasheet, README beside the footprint per our learnings), U2 replaced by TPS63031 + L1 + C10, R9 replaced by PROG1/PROG2/PROG3, SEL, VPCC divider, THERM resistor; BOM lines C5121473, C15516, C913207, C91604, C491130, C137723, C116674, C403123, C98220 (all from the v4 BOM, **not** live-checked by me); then rerun `check_netlist.py`, `check_layout.py`, re-estimate sleep, and redo the power budget. Estimate 1 to 2 agent days with the layout, because the 4.P2 power routing would be redone.
4. If a different connector orientation is wanted (cell wire direction vs enclosure): J2 variants only after Yara and Peter read the real plug.

## 5. For Arsany (proposed text for the Lead to open as an item; I did not edit the sheet)

> **Open item (proposed, PCB, Emil):** "LiPo connector polarity and charger option. (a) Please read the plug on your EEMB LP603449-PCM (photo 3 on Amazon.de B08FD39Y5R or the real cell): JST PH 2.0? Which wire is red, and is it pin 1 or pin 2? Our J2 expects pin 1 = +, your v4_c6_lipo J4 expects pin 2 = +, so one of the boards is reversed for the same plug. (b) Do you want to keep A-046 Option A (TP4056, no power path) for v1, as recommended in `pcb/lipo-reuse-v4c6.md`? A v4-style MCP73871 + TPS63031 stack is about 55 uA typical by datasheet, which alone breaks NFR-12 (50 uA) unless measured otherwise. Default if no answer: keep TP4056, add J2 polarity silk and a meter check."

UNVERIFIED list: real cell plug pitch and polarity; the v4 schematic reference-to-net assignment of R13/R14/R16/R17/R18 (scrambled PDF text); JLC basic/extended class and live stock/price of every v4 part (not queried); the sleep-current deltas on a bench; whether MCP73871 leakage is as high in our wiring with USB unplugged; availability of the Gerber details (not opened).

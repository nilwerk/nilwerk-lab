# Cart list: JLCPCB, plant-monitor (4.P4 prep)

**NOT ORDERED. Arsany submits.** Nothing was logged in, uploaded or paid. The status is BLOCKED: do not submit before the blockers below are cleared.

## Blockers (from dry-run-checklist.md)
- F5 Panel / rails for this outline: single outline 34.5 x 67.0 mm; no panel, no rails designed
- F6 SMT tooling and fiducials: fiducials 0, tooling holes 0
- A9 Placeholder footprints: 7 distinct placeholder footprints: E1 soil probe copper (no LCSC, not in CPL); J1 USB-C HRO TYPE-C-31-M-12; J2 JST PH 2-pin (cell); SW1-SW3 tact switch 5.1 mm (x3, one footprint); U1 ESP32-C3-MINI-1 module; U5 AHT20 DFN-6; U6 BH1750 WSOF-6
- R1 Routing: 0 tracks
- R2 Simulations: 4 of 5 NOT RUN (LDO dropout run)
- Gate 4.P3 (Arsany review) comes first.

## Step 1: PCB (bare board)
| Option | Value to select | Status |
|---|---|---|
| Quantity | 5 boards (proposal: 3 builds + 2 spare) | proposal, Arsany decides |
| Layers | 2 | from board file |
| Dimensions | the panel file, NOT the single outline (F5) | BLOCKED |
| Thickness | 1.6 mm | from board file |
| Outer copper | 1 oz | CHOICE (F3) |
| Surface finish | HASL (lead-free) | CHOICE (F16) |
| Solder mask / silkscreen colour | JLC default (green / white) | CHOICE, not read |
| Via process | Epoxy filled and capped for the 16 vias in pads (F12) | OPEN, price not read |
| Gerber file | `jlcpcb/gerbers/plant-monitor-gerber.zip` (CI export, head da39d2c) | BLOCKED until routed |
| Flying-probe test | JLC default | CHOICE |

## Step 2: PCBA (assembly)
| Option | Value to select | Status |
|---|---|---|
| Assembly side | Top | from CPL (A1) |
| Assembly quantity | 5 | proposal, same as step 1 |
| BOM file | `jlcpcb/bom-jlc.csv` | generated, LCSC numbers on every line |
| CPL file | `jlcpcb/cpl-jlc.csv` | generated; rotation and origin UNVERIFIED (A10, F23) |
| PCBA type | Economic or Standard | decision after the Extended-part fee is read (11 Extended unique parts, A8) |
| Stencil | JLC standard | cost not read |
| Parts | JLC stock (A5) | every line checked: see bom-lcsc.csv |

## Parts not from JLC (Arsany buys, never the agent)
- LiPo cell EEMB LP603449-PCM, Amazon.de ASIN B08FD39Y5R: price, stock and delivery UNVERIFIED (A-034).
- Check the JST plug polarity and pitch with a meter before the first connection (A12).

## Price (for the decision, not a quote)
- Parts only (LCSC catalogue): 6.56 USD per board at 5 boards, 5-board total 32.81 USD (no JLC fab, PCBA labour or fees: UNVERIFIED).
- JLC PCB fab and PCBA prices: UNVERIFIED, read on the JLC order page at checkout.


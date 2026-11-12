# Cart list: JLCPCB, plant-monitor (4.P4 prep)

**NOT ORDERED. Arsany submits.** Nothing was logged in, uploaded or paid. The status is BLOCKED: do not submit before the blockers below are cleared.

## Blockers (from dry-run-checklist.md)
- F6 SMT tooling and fiducials: designed: 3 fiducials (1 mm copper, centre 3.85 mm from the edge, copper edge 3.35 mm), 2 tooling holes (2 mm NPTH, centre 3.0 mm [mine, UNVERIFIED]), rails 6 mm; in the Gerber/drill set: fiducials 0, tooling holes 0
- A9 Placeholder footprints: 3 distinct placeholder footprints: E1 soil probe copper (own copper, no LCSC, not in CPL; size depends on Q5); U5 AHT20 DFN-6; U6 BH1750 WSOF-6
- R1 Routing: 4 tracks
- R2 Simulations: 4 of 5 NOT RUN (LDO dropout run)
- Gate 4.P3 (Arsany review) comes first.

## Step 1: PCB (bare board)
| Option | Value to select | Status |
|---|---|---|
| Quantity | Panels, 2 boards per panel: 2 panels = 4 boards, 3 panels = 6 boards. The number of panels is Arsany's choice; none is chosen here. Stock (A5, A6) is checked for 3 panels = 6 boards | Arsany decides |
| Layers | 2 | from board file |
| Dimensions | the panel file, NOT the single outline (F5) | BLOCKED |
| Thickness | 1.6 mm | from board file |
| Outer copper | 1 oz | CHOICE (F3) |
| Surface finish | HASL (lead-free) | CHOICE (F16) |
| Solder mask / silkscreen colour | JLC default (green / white) | CHOICE, not read |
| Via process | Standard, no filling: no vias in pads since slice 2 (F12); filled and capped only if Arsany chooses the alternative | CHOICE |
| Gerber file | `jlcpcb/gerbers/plant-monitor-gerber.zip` (CI export, head 8ad6122, run 42772372983; 22 of 22 Gerber/drill files match the artifact, content check 2026-11-12) | BLOCKED until routed |
| Flying-probe test | JLC default | CHOICE |

## Step 2: PCBA (assembly)
| Option | Value to select | Status |
|---|---|---|
| Assembly side | Top | from CPL (A1) |
| Assembly quantity | Same panel count as step 1 (boards = 2 x panels). Arsany's choice | Arsany decides |
| BOM file | `jlcpcb/bom-jlc.csv` | generated, LCSC numbers on every line |
| CPL file | `jlcpcb/cpl-jlc.csv` | generated; rotation and origin UNVERIFIED (A10, F23) |
| PCBA type | Economic or Standard | decision after the Extended-part fee is read (11 Extended unique parts, A8) |
| Stencil | JLC standard | cost not read |
| Parts | JLC stock (A5) | every line checked: see bom-lcsc.csv |

## Parts not from JLC (Arsany buys, never the agent)
- LiPo cell EEMB LP603449-PCM, Amazon.de ASIN B08FD39Y5R: price, stock and delivery UNVERIFIED (A-034).
- Check the JST plug polarity and pitch with a meter before the first connection (A12).

## Price (for the decision, not a quote)
- Parts only (LCSC catalogue): 6.56 USD per board at 6 boards (3 panels); 6.56 at 3 boards; 4.01 at 1000 boards. Total for the chosen quantity = per-board figure x boards (boards = 2 x panels). No JLC fab, PCBA labour or fees: UNVERIFIED.
- JLC PCB fab and PCBA prices: UNVERIFIED, read on the JLC order page at checkout.


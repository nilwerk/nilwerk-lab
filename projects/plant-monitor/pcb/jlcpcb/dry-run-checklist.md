# JLCPCB dry-run checklist: plant-monitor, Plan 4.P4 prep

**DRAFT. NOT ORDERED. NOT A RELEASE.** Routing is not done (0 tracks), the 7 distinct footprints are placeholders, 4 of 5 simulations are not run. 
Generated 2026-11-09 20:25Z by `make_jlcpcb_package.py` from head of branch `agent/pcb/4.P4-prep`, board from `plant-monitor.kicad_pcb` (4.P2 slice 1).

**Result:** NOT ORDERABLE: 5 FAIL, 12 OPEN or UNVERIFIED, 19 PASS (of 40 items). Dry run only.

Legend: PASS = within the limit; FAIL = outside the limit or missing; OPEN = cannot be checked until a later slice; UNVERIFIED = needs the JLC page or a physical check; CHOICE / NOTE = a cart choice or a remark.

| ID | Item | JLCPCB limit | This board | Result | Note / source |
|---|---|---|---|---|---|
| F1 | Copper layers | 1-32 layers; 2-layer FR-4 standard | 2 layers | **PASS** | https://jlcpcb.com/capabilities/pcb-capabilities (read 2026-11-09) |
| F2 | Board thickness | FR-4 0.4-4.5 mm; 1.6 mm in list (+-10 %) | 1.6 mm | **PASS** | https://jlcpcb.com/capabilities/pcb-capabilities (read 2026-11-09) |
| F3 | Outer copper weight | 2-layer: 1 / 2 / 2.5 / 3.5 / 4.5 oz | 1 oz (not stored in the board file; choice in cart) | **CHOICE** | https://jlcpcb.com/capabilities/pcb-capabilities (read 2026-11-09) |
| F4 | Board size | min 5 x 5 mm; 2-layer FR-4 max 1020 x 600 mm | 34.50 x 67.00 mm, 1 board | **PASS** | https://jlcpcb.com/capabilities/pcb-capabilities (read 2026-11-09) |
| F5 | Panel / rails for this outline | min panel 70 x 70 mm for V-cut; mouse-bite panel: rails >= 3 mm, 2 mm board spacing | single outline 34.5 x 67.0 mm; no panel, no rails designed | **FAIL** | Board is below the 70 mm panel minimum: needs a panel with rails (JLC `Panel` rules). Not designed in 4.P2 (layout-4P2.md). |
| F6 | SMT tooling and fiducials | SMT: 5 mm tooling edges, 2 mm tooling holes, 1 mm fiducials 3.85 mm from panel edge | fiducials 0, tooling holes 0 | **FAIL** | https://jlcpcb.com/capabilities/pcb-capabilities (read 2026-11-09) |
| F7 | Min track width / space | 0.15 / 0.15 mm under mask (1 oz); 0.25 mm bare | 0 tracks (unrouted) | **OPEN** | Nothing to check until routing. Design rule 0.2 mm (layout-brief section 5). |
| F8 | Pad to pad, different nets | 0.15 mm (JLC: SMD pad to pad, different nets) | check_layout clearance (>= 0.2 mm rule) | **PASS** | check_layout.py: PASS |
| F9 | Copper (pads) to routed edge | >= 0.2 mm copper clearance from routed edges | check_layout (>= 0.5 mm rule) | **PASS** | check_layout.py |
| F10 | Drill, smallest hole | 2-layer hole >= 0.15 mm (0.2 preferred) | via drill 0.30 mm; drill file tools 0.300 mm | **PASS** | https://jlcpcb.com/capabilities/pcb-capabilities (read 2026-11-09) |
| F11 | Via: pad minus hole, PTH annular ring | pad - hole >= 0.10 mm (0.15 preferred); annular >= 0.20 mm (recommended 0.25 mm at 1 oz, absolute 0.18 mm) | pad 0.70 / drill 0.30 mm: ring 0.200 mm | **PASS** | At the 0.20 mm minimum, below the 0.25 mm recommendation (NOTE). Option: 0.8 mm via pad (layout change, Emil to decide). |
| F12 | Via in pad (copper under via, within an SMD pad) | Via-in-pad needs filled and capped vias (epoxy or copper paste, 0.15-0.55 mm); otherwise vias must stay out of pads | 16 vias inside SMD pads: U1, U3 | **OPEN** | Module ground pad and TP4056 exposed pad vias. Choose filled and capped (cart step 1) or move vias. Price of that option NOT read (UNVERIFIED). |
| F13 | Via to via / hole spacing | via hole to hole >= 0.25 mm (layout-brief) | PASS  via-to-via hole/copper spacing >= 0.25 mm, 0 violations  [section 5 Via] | **PASS** | check_layout.py |
| F14 | Solder mask bridge | >= 0.10 mm bridge (1 oz green); mask opening 1:1 to pad | min pad gap >= 0.2 mm (check_layout); pad_to_mask_clearance 0 | **PASS** | https://jlcpcb.com/capabilities/pcb-capabilities (read 2026-11-09) |
| F15 | Silkscreen | text height >= 1.0 mm, line >= 0.15 mm, pad to silk >= 0.15 mm | no silkscreen text placed in the board file | **OPEN** | Reference designators and polarity marks for D2, D3, U1, U3 are still to be placed (4.P4 prep does not place them). |
| F16 | Surface finish | HASL lead-free / ENIG / OSP | HASL lead-free proposed (layout-brief section 5) | **CHOICE** | https://jlcpcb.com/capabilities/pcb-capabilities (read 2026-11-09) |
| F17 | NPTH / mounting holes | NPTH annular >= 0.45 mm recommended; mounting holes need the enclosure (Q7) | no NPTH in drill file; no mounting holes placed | **OPEN** | Mounting holes depend on Yara's answer Q7 (layout-4P2.md). |
| F18 | Gerber set complete | copper, mask, silk, paste, edge, drill | 22 files; missing: none | **PASS** | CI pcb-fab artifact of head da39d2c, run 42628752571. |
| F19 | Drill file vs board vias | drill holes = vias in the board | drill holes 16, vias 16 | **PASS** |  |
| F20 | KiCad DRC (CI, error level) | 0 errors | 0 DRC violations; 0 unconnected pads | **PASS** | Error level only. Unconnected items are warning-level and the board is unrouted, so this is no connectivity result. |
| F21 | KiCad ERC (CI) | 0 errors | errors 0, warnings 0 | **PASS** |  |
| F22 | Copper zones | zones must be filled before release (CAM) | 0/2 zones filled | **OPEN** | GND zone on B.Cu not filled: routing slice. |
| F23 | CPL origin / orientation vs Gerber | CPL coordinates must share the Gerber origin (JLC CAM preview) | KiCad pos (Y sign negated vs board file) | **UNVERIFIED** | Checked here only against the board file. JLC CAM preview must confirm. |
| A1 | All parts on top side | single-side SMT: standard JLC PCBA | 45 of 45 top | **PASS** | https://jlcpcb.com/capabilities/pcb-capabilities (read 2026-11-09) |
| A2 | Every BOM line has an LCSC part number | JLC PCBA BOM needs LCSC Part # | 27 lines, 27 with LCSC | **PASS** | B1 (LiPo cell) is not in the JLC BOM: Arsany buys it (A-034). |
| A3 | Designators: BOM = CPL | same set of 45 designators | BOM 45, CPL 45, equal True | **PASS** |  |
| A4 | LCSC lifecycle normal | not NRND / EOL | 0 lines not normal | **PASS** | LCSC productCycle, read 2026-11-09 (refresh_live.py) |
| A5 | JLC stock for 5 boards | JLC library stock >= qty per board x 5 | 0 lines short | **PASS** | JLC stock as read 2026-11-09 (refresh_live.py) |
| A6 | LCSC stock for 5 boards (hand-buy path) | LCSC stock >= qty x 5 | 2 lines short: C15849, C14663 | **NOTE** | Matters only if Arsany buys parts himself; JLC PCBA uses JLC stock (A5). |
| A7 | Price basis | LCSC catalogue USD price breaks (3, 5, 1000 boards) | parts only per board: 3 boards 6.56 USD, 5 boards 6.56 USD, 1000 boards 4.01 USD | **NOTE** | Excludes JLC PCB fab, PCBA labour, stencil, Extended-part fee, tax, shipping (UNVERIFIED: not read). Cell B1 excluded (UNVERIFIED). Lines below the first LCSC price break (first break used, UNVERIFIED for that quantity): 37 (C14663 at 3 boards; C14663 at 5 boards; C15849 at 3 boards; C15849 at 5 boards; C16581 at 3 boards; C165948 at 3 boards; C19702 at 3 boards; C21190 at 3 boards; C21190 at 5 boards; C2286 at 3 boards; C2286 at 5 boards; C22935 at 3 boards; C22935 at 5 boards; C22940 at 3 boards; C22940 at 5 boards; C2297 at 3 boards; C2297 at 5 boards; C23162 at 3 boards; C23162 at 5 boards; C23178 at 3 boards; C23178 at 5 boards; C23186 at 3 boards; C23186 at 5 boards; C25804 at 3 boards; C25804 at 5 boards; C295747 at 3 boards; C318884 at 3 boards; C318884 at 5 boards; C351410 at 3 boards; C351410 at 5 boards; C5148694 at 3 boards; C5148694 at 5 boards; C59461 at 3 boards; C59461 at 5 boards; C7519 at 3 boards; C7835 at 3 boards; C7835 at 5 boards) |
| A8 | Extended parts (JLC fee per unique part) | JLC Extended library: extra loading fee per part | 11 Extended unique parts: C16581, C165948, C2757850, C2838502, C295747, C351410, C5148694, C7519, C7835, C78960, C86534 | **UNVERIFIED** | Fee value not read on this run; check the JLC PCBA price page. |
| A9 | Placeholder footprints | footprints must match the manufacturer drawing for PCBA | 7 distinct placeholder footprints: E1 soil probe copper (no LCSC, not in CPL); J1 USB-C HRO TYPE-C-31-M-12; J2 JST PH 2-pin (cell); SW1-SW3 tact switch 5.1 mm (x3, one footprint); U1 ESP32-C3-MINI-1 module; U5 AHT20 DFN-6; U6 BH1750 WSOF-6 | **FAIL** | Blocks the order: layout-4P2.md 'What is NOT done'. Pad geometry not from drawings (U1 pattern, J1, J2, SW, U5, U6, E1). |
| A10 | CPL rotation convention | JLC applies its own rotation per library part | 2 parts with nonzero rotation: J2, R16 | **UNVERIFIED** | Check each rotated part in the JLC CPL preview (U1, U3, U4, U5, U6, U7, D1, J1, J2, Q1 pin 1). |
| A11 | Polarity: LEDs, pin 1 marks | JLC preview shows polarity from the footprint | D2, D3 cathode pin 1 assumed (design.py); U-pin 1 positions per footprint | **UNVERIFIED** | bom.csv note: 'pin 1 = cathode assumed'. |
| A12 | Cell connector J2 (JST PH) pitch and polarity | plug must match the decided cell | PH 2.0 mm assumed; polarity unverified (A-053) | **UNVERIFIED** | cell-decision-A034.md; check the physical plug before the order. |
| R1 | Routing | all nets routed, zones filled, DRC with connectivity | 0 tracks | **FAIL** | Blocks any release and any order (TEAM.md section 4, routing slice next). |
| R2 | Simulations | 4.P1 list: divider, soil front end, charger thresholds, USB inrush | 4 of 5 NOT RUN (LDO dropout run) | **FAIL** | README 'Status of the checks'. |
| R3 | Gate 4.P3 review | Arsany review of the package before any Gerber release | pending | **OPEN** | Arsany's gate, comes first. |
| R4 | Enclosure inputs Q1-Q11 | outline is fixed only after Yara's answers | unanswered (layout-brief section 4) | **OPEN** | Outline is a proposal. |
| R5 | Repo checks | check_layout.py and check_netlist.py pass with /usr/bin/python3 -I | check_layout rc 0: RESULT: all layout checks PASS; check_netlist rc 0: ALL CHECKS PASS | **PASS** |  |

JLCPCB limit source: https://jlcpcb.com/capabilities/pcb-capabilities (read 2026-11-09). Re-check on the day of the order, the pages change.
Repo checks run in this script: `check_layout.py` and `check_netlist.py` with `/usr/bin/python3 -I`. 

Cost basis (per board, USD, LCSC catalogue, read 2026-11-09): 3 boards 6.56, 5 boards 6.56, 1000 boards 4.01 (parts only, see A7).


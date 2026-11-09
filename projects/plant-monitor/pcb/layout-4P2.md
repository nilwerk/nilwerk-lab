# 4.P2 layout, slice 1: what exists, what each rule traces to, what blocks the PCBA order

Emil (PCB Designer) · 2026-11-09 · Branch `agent/pcb/4.P2` · Nothing ordered, no Gerber release (that is the 4.P3 gate, Arsany).
Tags as in `layout-brief.md`: [brief] taken from it, [mine] my assumption, [open] needs an answer.

## Files
| File | What |
|---|---|
| `gen_pcb.py` | generator: writes `plant-monitor.kicad_pcb`, the DFM rules/net classes in `plant-monitor.kicad_pro`, and `plant-monitor-outline.dxf` (O8, for Yara). Parts and nets come from `design.py`, so board and schematic cannot drift. |
| `plant-monitor.kicad_pcb` | the board: outline, 46 footprints placed on top, nets assigned, 16 ground/thermal vias, antenna keep-out, bottom GND zone (not filled). **No tracks.** |
| `check_layout.py` | own geometry check of the board file (not KiCad DRC), 19 checks, plus `--render` (the showcase image is drawn from the board file by this script). |

## Which checks ran, and where
| Check | Where | Result |
|---|---|---|
| KiCad ERC (`kicad-cli sch erc --severity-error`) | CI job `pcb`, KiCad 9 container, PR #64 head | 0 violations (error level) |
| KiCad DRC (`kicad-cli pcb drc --severity-error`) | same job, same head | **0 violations**, 0 unconnected pads/footprint errors reported. First head (before the fix) found 1 real error: `items_not_allowed`, footprint U1 inside keepout area ANT_KEEPOUT (module overhangs it by design); fixed by allowing footprints in the rule area, pads/tracks/vias/pour stay forbidden. |
| Gerber/drill/CPL/STEP export | same job | ran without error (CI artifact `pcb-fab`); **not a release**, placeholder footprints, unrouted |
| `check_layout.py` (own geometry rules) | agent session | 19/19 PASS, table below |
| `check_netlist.py` | agent session, unchanged | PASS (schematic untouched) |
| KiCad DRC locally, 3D view, DFM view | **not run**: no KiCad in the agent session | |

What the DRC does **not** say: it runs at error level only, so warnings are not in the log (I did not change `ci.yml`); `unconnected_items` is set to *warning* in `.kicad_pro` for this unrouted slice, so "0 unconnected" does not mean connected. "DRC 0" on this board means: outline closed, no clearance/edge/keep-out error among the placeholder pads and the vias. It does not prove the footprints are right.

## Traceability (rule -> where on the board -> check)
| ID | Rule | On the board | Check |
|---|---|---|---|
| O1 | cell bay is not copper; bottom flat, single side | cell cavity 53.0 x 35.1 mm (Yara's `pcb-enclosure-bay.md` numbers) on `Dwgs.User` beside the board, 5.0 mm gap [brief]; all 46 footprints F.Cu, no THT | all F.Cu; courtyards inside outline; 0 overlaps |
| O2, rule 14, R-06 | antenna at the edge, keep-out both layers, cell >= 15 mm away | module overhangs the top edge by 6.0 mm [mine], at the right side; keep-out rule area 17.2 x 2.0 mm on F.Cu+B.Cu (3 mm each side of the module [mine]); 15 mm clear box on `Cmts.User` | antenna end to cell cavity 26.2 mm; nothing else in the keep-out |
| O3 | >= 9 ground vias under the module, solid GND bottom | 12 vias 0.3/0.7 mm in the module ground pad area; GND zone on B.Cu over the body only (not the tail) | 12 vias; zone **not filled** |
| O4 | USB-C on an edge, far from the antenna, ESD within 10 mm | J1 right edge, mouth flush; D1 0.5 mm from it; C10 at the connector | J1 28.5 mm from antenna; D1 gap 0.5 mm |
| O5 / S1 | stake electrodes as copper on a tail of the board, opposite the antenna, under solder mask | tail 12 x 25 mm [mine], E1 pads on F.Cu only (no mask opening), SOIL_PROBE electrode between two GND electrodes (guard) | tail at the far end |
| O6 | AHT20 >= 10 mm from TP4056; soil front end at the tail; J2 at the cell end | U5 top left, U3 centre right (25.5 mm); U7/R12/C8 at the tail neck; J2 left edge facing the cell | U5-U3 25.5 mm |
| section 5 | 0.2/0.2 mm, via 0.3/0.7, copper to edge >= 0.5, 2 layers 1.6 mm, power 0.4 / VBAT 0.5 | `.kicad_pro` rules and net classes Default/Power/Battery | pad-to-pad >= 0.2 mm: 0 violations; pads >= 0.5 mm from edge; via spacing |
| section 5 | TP4056 EP: copper + 4-6 thermal vias | 4 vias in the EP pad | 4 |
| O8 | DXF outline for Yara | `plant-monitor-outline.dxf` (layers OUTLINE, CELL_BAY_CAVITY, ANT_KEEPOUT, MODULE_U1) | |

Outline (new, **announce to the Lead and Yara**): body 34.5 x 42 mm plus tail 12 x 25 mm = 34.5 x 67 mm overall, module overhang 6 mm above. Everything in this paragraph is [mine] and changes when Yara answers Q1-Q11.

## What is NOT done (honest list)
- **No routing**, no zone fill, no silkscreen text, no mounting holes (Q7), no fiducials/panel rails (section 5 panel rule).
- **Placeholder footprints** (right pad numbers and nets, geometry not from a drawing): U1 ESP32-C3-MINI-1 (pad pattern not the datasheet Fig 11-1), J1 USB-C (C165948 drawing not read), J2 JST PH (approximate), SW1-SW3, U5 AHT20, U6 BH1750, E1. Standard parts (0603, SOT-23, TSSOP-8, SOIC-8-EP, LEDs) use KiCad-library-like land patterns written by hand; not compared with the library. The CI container has the KiCad library, so a `lib_footprint_mismatch` warning is likely (not visible at error level).
- Pad numbers of the 5 custom parts and C165948 are [open] until the drawings are read (design.py flags `pin_verified`).
- Antenna keep-out size and module overhang are my numbers; the datasheet figure was not read in this slice [open].
- Simulations: divider, soil front end, charger thresholds, USB inrush still not run (unchanged since the brief).
- The second battery protection (U4/Q1/R15/C9) stays on the prototypes, per A-045/A-046/A-057 decisions you gave (README open point 4 remains the recommendation for a later spin).

## Blocks the PCBA order (12 Nov): Needs-Arsany candidates
1. **Enclosure inputs from Yara (Q1-Q11 of the brief)**: board orientation, usable inner size, USB-C entry wall, stake size and seal, pinhole/light-window/vent positions, screw positions, metal parts near the antenna. Arsany to confirm who answers by when; without them the outline is a proposal.
2. **Cell plug (A-053)**: pitch and polarity of the JST plug on the received EEMB cell are unverified; J2 footprint and the mating-part decision depend on it. Needs Arsany's photo/measurement of the real cell (or Peter's, per work order).
3. **Decision: cell beside the board (my recommendation, 94 x 34.5 mm class) or under it.** The layout assumes beside.
4. **Decision: stake as part of the board (S1, assumed) or separate stake PCB with connector (S2).**
5. **Footprint review before any Gerber**: someone (Theo review, then 4.P3 gate) must check the 7 placeholder footprints against the manufacturer drawings and the JLC DFM/3D view; this is Emil's work (next slice), not Arsany's, but the order date depends on it.
6. **Routing and the remaining four simulations** (next slices, Emil). With 4.P3 gate by Arsany after them. If 12 Nov must hold, routing + footprint fix + 4.P3 review is the critical path: realistic only if items 1-4 are answered today.
7. JLC stock/price for the BOM stays `unverified` until shop hosts are reachable (playbook rule 1).

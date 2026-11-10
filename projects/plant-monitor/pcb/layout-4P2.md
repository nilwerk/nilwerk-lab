# 4.P2 layout, slices 1 and 2: what exists, what each rule traces to, what blocks the PCBA order

Emil (PCB Designer) · 2026-11-09 · Branch `agent/pcb/4.P2` · Nothing ordered, no Gerber release (that is the 4.P3 gate, Arsany).
Tags as in `layout-brief.md`: [brief] taken from it, [mine] my assumption, [open] needs an answer.

## Slice 2 (2026-11-10, branch `agent/pcb/4.P2-s2`): what changed, and what is still open

Emil (PCB Designer). Stacked on PR #64 (slice 1) and PR #69 (4.P4 prep, merged into this branch so the dry-run checklist can be regenerated). Nothing ordered, not a release.
**Not fab-ready:** 4 short GND stubs are the only tracks, no net is routed, the GND zone is not filled, U5 (AHT20) and U6 (BH1750) are still placeholders.

| Item | Result | Evidence |
|---|---|---|
| Real footprints | U1 (Espressif footprint, checked against datasheet v2.2 Fig 11-1), J1 USB-C, J2 JST PH, the 9 standard parts (0603, LED, SOT-23, TSSOP-8, SOIC-8-EP) from the KiCad 9.0.0 library; SW1-SW3 drawn from the XKB TS-1187A "P.C.B. LAYOUT" drawing. Sources: `footprints/SOURCES.md`. Still placeholders: U5 AHT20 (the datasheet has a package drawing, no land pattern; pad size reading ambiguous), U6 BH1750 (land pattern is in a separate Rohm "Jisso" document, not available). | `kmod.py`, `gen_pcb.py` |
| **Found: SW1-SW3 were wired as a short** | In the XKB drawing terminals A-B are joined inside, C-D likewise. The slice-1 placeholder put the signal on the two left pads (A, C) and GND on the right pads (B, D), which shorts signal to GND through A-B and C-D. The new footprint numbers the top pair (A, B) 1,2 = signal and the bottom pair (C, D) 3,4 = GND, matching `design.py` pins. My reading of the drawing (A/B top, C/D bottom as in the left-hand body view); check with a meter on the first sample. | `gen_pcb.py` FOOT["NW:SW_..."] |
| Via in pad (A-069) | **0 vias in pads** (was 16). Module: 12 vias in the 0.525 mm gaps of the 3 x 3 ground pad grid (this is where Espressif Fig 11-1 draws the thermal vias; the 0.7 mm via ring touches the neighbouring same-net pad copper by about 0.09 mm, the hole is in the gap). TP4056: 4 vias just outside the exposed pad, each joined by a 0.4 mm GND stub (the first tracks on the board). Alternative left for Arsany: keep vias in the pads and order JLC filled and capped vias (price not read). | `check_layout.py` (0 holes in pads), CI DRC 0 |
| R16 angle (Yara) | R16 is now placed at rotation 0, so the question cannot matter for it. On the rule itself: KiCad writes the pad angle as the absolute orientation, footprint rotation included. The real rotated footprints J1 (90) and J2 (270) have 0.3 mm pitch pads; with a double rotation they would overlap and DRC would flag them, and KiCad 9 DRC in CI is clean. My own `make_jlcpcb_package.py` added the two angles (wrong, now fixed). | CI DRC |
| Antenna distance 26.2 vs 28.4 mm (Yara) | Both numbers were right for different things: 26.2 mm = the overhang strip (board edge to module end) to the cell cavity; 28.4 mm = module end corner to cavity corner. The rule-relevant value is the nearest point of the antenna area (module width x module end down to the first pad row). With the real land pattern the module moved (overhang 4.5 mm instead of 6.0, because the real pads start 5.7 mm below the module end) and the numbers are now: antenna area 25.7 mm, overhang strip 26.0 mm, corner to corner 27.7 mm; rule >= 15 mm. | `check_layout.py` INFO line |
| Antenna keep-out | Now 17.2 x 1.0 mm (3 mm beside the module, down to 0.2 mm above the first pad row; the pads of the real module are on the board from y = 1.2 mm). Size is still my assumption, not an Espressif number. | `gen_pcb.py` |
| CI enforcement | New step "Layout checks" in the `pcb` job runs `check_layout.py` (exit 1 on any FAIL: antenna keep-out empty, antenna area >= 15 mm from the cell, USB-C far from the antenna, no via in a pad, copper edge). Touching `ci.yml` re-runs all workstreams. | `.github/workflows/ci.yml` |
| Placement | Moved J1 (real footprint is 9.4 x 10.6 mm with shield legs), J2, U3, U4, Q1, D1, C1-C3, R9-R11, U7, C8, SW3 to keep the new courtyards apart. Outline unchanged (34.5 x 42 + 12 x 25 tail). | `check_layout.py`: 0 overlaps |
| New with the real J1 | 4 oval plated slots (0.6 x 1.2 / 1.7 mm) and 2 NPTH pegs (0.65 mm) in the drill file; the "all SMD, no THT" statement of slice 1 no longer holds for J1 (JLC accepts it on the SMT line, DFM view not seen). | drill file, CI artifact |

Real numbers from CI (KiCad 9, job `pcb`): ERC 0 errors, 0 warnings. DRC at error level 0 violations, 0 unconnected pads (error level; unconnected items are warning-level so this is not a connectivity result). **No local kicad-cli**: apt has KiCad 7 only, which cannot read the KiCad 9 file; installing the KiCad 9 PPA means changing the system package sources, which was not allowed in this session.
A first CI run of this slice found 2 real DRC errors (J2 mounting pads 0.2 mm outside the board edge); they are fixed and the edge check in `check_layout.py` now also catches pads outside the outline.

Not done: routing of any net, GND zone fill, silkscreen, mounting holes (Q7), fiducials and panel (F5, F6), U5/U6 footprints, 4 of 5 simulations. Next slice: route the power path (VBUS, VBAT, 3V3, GND) and verify with CI DRC including unconnected items at warning level.

## Files
| File | What |
|---|---|
| `gen_pcb.py` | generator: writes `plant-monitor.kicad_pcb`, the DFM rules/net classes in `plant-monitor.kicad_pro`, and `plant-monitor-outline.dxf` (O8, for Yara). Parts and nets come from `design.py`, so board and schematic cannot drift. |
| `plant-monitor.kicad_pcb` | the board: outline, 46 footprints placed on top (45 BOM pieces + E1, the stake electrode copper, which has no LCSC line; `check_netlist.py` confirms BOM = schematic), nets assigned, 16 ground/thermal vias, antenna keep-out, bottom GND zone (not filled). **No tracks.** |
| `check_layout.py` | own geometry check of the board file (not KiCad DRC), 18 checks, **mandatory gate item** (see "Gate checklist"), plus `--render` (the showcase image is drawn from the board file by this script). |

## Which checks ran, and where
| Check | Where | Result |
|---|---|---|
| KiCad ERC (`kicad-cli sch erc --severity-error`) | CI job `pcb`, KiCad 9 container, PR #64 head | 0 violations (error level) |
| KiCad DRC (`kicad-cli pcb drc --severity-error`) | same job, same head | **0 violations at error level.** Unconnected items are **warning-level, not in the error-level report** (rule downgraded to warning, board unrouted; CI runs `--severity-error`). First head (before the fix) found 1 real error: `items_not_allowed`, footprint U1 inside keepout area ANT_KEEPOUT (module overhangs it by design); fixed by allowing footprints in the rule area, pads/tracks/vias/pour stay forbidden. |
| Gerber/drill/CPL/STEP export | same job | ran without error (CI artifact `pcb-fab`); **not a release**, placeholder footprints, unrouted |
| `check_layout.py` (own geometry rules) | agent session | 18/18 PASS, table below |
| `check_netlist.py` | agent session, unchanged | PASS (schematic untouched) |
| KiCad DRC locally, 3D view, DFM view | **not run**: no KiCad in the agent session | |

What the DRC does **not** say: it runs at error level only, so warnings are not in the log (I did not change `ci.yml`); unconnected items are warning-level (`unconnected_items` = *warning* in `.kicad_pro`), not in the error-level report, so the 0 in the CI log is not a connectivity result. "DRC 0" on this board means: outline closed, no clearance/edge/keep-out error among the placeholder pads and the vias. It does not prove the footprints are right.

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

Requirement IDs (TEAM.md section 6; component C-01 in `architecture.md` maps them): FR-D01 (five plausible values: decoupling at the module and sensors, `gen_pcb.py` placement of C5/C4/C12/C6/C7), FR-D06 (low-battery: divider R7/R8 and ADC pin, unchanged), FR-D07 (pinhole factory reset SW3), NFR-01 and NFR-12 (no part or load added by the layout; sleep sum unchanged, `check_netlist.py`), NFR-02 and FR-D10 (soil probe E1 on the stake with guard electrodes, calibrated per FR-D10), NFR-08 (ESD D1 within 10 mm of J1), NFR-09 (BOM unchanged, no new part). The soil-sensing requirement is NFR-02/FR-D10; there is no separate layout NFR for the stake.

Outline (new, **announce to the Lead and Yara**): body 34.5 x 42 mm plus tail 12 x 25 mm = 34.5 x 67 mm overall, module overhang 6 mm above. Everything in this paragraph is [mine] and changes when Yara answers Q1-Q11.

## What is NOT done (honest list)
- **No routing**, no zone fill, no silkscreen text, no mounting holes (Q7), no fiducials/panel rails (section 5 panel rule).
- **Placeholder footprints** (right pad numbers and nets, geometry not from a drawing): U1 ESP32-C3-MINI-1 (pad pattern not the datasheet Fig 11-1), J1 USB-C (C165948 drawing not read), J2 JST PH (approximate), SW1-SW3, U5 AHT20, U6 BH1750, E1. Standard parts (0603, SOT-23, TSSOP-8, SOIC-8-EP, LEDs) use KiCad-library-like land patterns written by hand; not compared with the library. The CI container has the KiCad library, so a `lib_footprint_mismatch` warning is likely (not visible at error level).
- Pad numbers: `design.py` now sets `pin_verified=False` for SW1, SW2, SW3, U5, U6 (the custom footprints with vendor pinouts) and J1 (C165948). Signal-to-pin maps were taken from datasheets/drawings in 4.P1 (README C1/C2), but in slice 1 I did not compare the *placed* footprints with the drawings, so the flag is honest only as "not verified against the drawing in 4.P2". `check_netlist.py` prints exactly these six; BOM `PinMapStatus` shows it. Not flagged: U1 (verified by Theo in 4.P1), E1 and J2 (own/approximate geometry, 2 pads; J2 plug pitch/polarity is A-053, listed above). The flags go back to true only when the placed footprint is compared with the drawing (4.P3 footprint review).
- **Antenna keep-out size (17.2 x 2.0 mm) and module overhang (6.0 mm) are Emil's assumption.** The Espressif datasheet keep-out figure was not read in this slice [open]. The datasheet is the single source for these numbers; reading it is a condition before routing.
- Simulations: divider, soil front end, charger thresholds, USB inrush still not run (unchanged since the brief).
- The second battery protection (U4/Q1/R15/C9) stays on the prototypes, per A-045/A-046/A-057 decisions you gave (README open point 4 remains the recommendation for a later spin).

## Blocks the PCBA order (12 Nov): Needs-Arsany candidates
1. **Enclosure inputs from Yara (Q1-Q11 of the brief)**: board orientation, usable inner size, USB-C entry wall, stake size and seal, pinhole/light-window/vent positions, screw positions, metal parts near the antenna. Arsany to confirm who answers by when; without them the outline is a proposal.
2. **Cell plug (A-053)**: pitch and polarity of the JST plug on the received EEMB cell are unverified; J2 footprint and the mating-part decision depend on it. Needs Arsany's photo/measurement of the real cell (or Peter's, per work order).
3. **Decision: cell beside the board (my recommendation, about 92.5 mm cavity-to-board-edge: 53.0 + 5.0 + 34.5; the enclosure outer is larger by walls and lid, bay module 56.2 x 38.3 mm) or under it.** The layout assumes beside.
4. **Decision: stake as part of the board (S1, assumed) or separate stake PCB with connector (S2).**
5. **Footprint review before any Gerber**: someone (Theo review, then 4.P3 gate) must check the 7 placeholder footprints against the manufacturer drawings and the JLC DFM/3D view; this is Emil's work (next slice), not Arsany's, but the order date depends on it.
6. **Routing and the remaining four simulations** (next slices, Emil). With 4.P3 gate by Arsany after them. If 12 Nov must hold, routing + footprint fix + 4.P3 review is the critical path: realistic only if items 1-4 are answered today.
7. JLC stock/price for the BOM stays `unverified` until shop hosts are reachable (playbook rule 1).

## Gate checklist (4.P3, before any Gerber; Gerber release is Arsany's)
Mandatory, each must be shown green or explicitly waived by Arsany:
1. **`check_layout.py` keep-out check** ("antenna keep-out ... no pad/via/other footprint inside"): MANDATORY, because the KiCad rule area now allows footprints (the module overhangs it by design, `gen_pcb.py` keep-out rule), so KiCad DRC no longer catches a stray footprint in the zone. Run it on every board revision; a FAIL blocks the gate.
2. **Revert the `unconnected_items` downgrade when routing starts**: delete the `warning` override in `gen_pcb.py` (`unconnected_items`) in the first routed slice, so DRC at error level counts open connections. Until then no statement of connectivity, and no Gerber.
3. Keep-out size and overhang checked against the Espressif datasheet figure (Emil's assumption today).
4. Placeholder footprints compared with the manufacturer drawings and the JLC DFM/3D view; then the `pin_verified` flags may go back to true.
5. KiCad ERC and DRC green in CI (error level), outline announced to Lead and Yara, remaining four simulations run.

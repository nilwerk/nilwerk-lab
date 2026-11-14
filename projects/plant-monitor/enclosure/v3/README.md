# Enclosure v3, slice 2: inner size, bay and fit to the 4.P2 board

Yara (3D Product Designer) · 2026-11-10 · Task 4.E3 · Branch `agent/mechanical/4.E3-s3` (PR #83), stacked on PR #74 (slice 2, `agent/mechanical/4.E3-s2`, draft). Nothing printed, ordered or uploaded.
Tags: **[src]** read from a repo source · **ASSUMED** my assumption (not a datasheet value, not in the repo) · **[rule]** team rule.
Board source: **PR #73 (`agent/pcb/4.P2-s2` @ b2e211f)**, copied unchanged to `mechanical/enclosure_v3/input/` (sha256 in SOURCE.txt, a test fails if it drifts); every board number is read from it, none typed. Status: **geometry fixed for the board outline, not a print-ready release.** One design (board beside the cell, Emil's layout), no Prototype 1 yet.

## 1. Q2 answer: the model enclosure size (OPEN, not locked; for Emil's outline)
| | Value | Basis |
|---|---|---|
| Inner cavity X x Y x Z | **93.3 x 53.7 x 8.6 mm (model, slice 4)** | X: cell cavity 53.0 + gap 5.0 + board 34.5 + 0.5 (J1 shell protrudes beyond the board edge) + 0.3 margin [src: DXF, #73 board]. Y: antenna overhang 4.5 [src: #73 DXF MODULE_U1] + 1.0 air (ASSUMED) above, board body 42.0, + 6.2 mm boss strip below. Z: standoff 1.0 + board 1.6 + J2 5.5 (SECONDARY listing, A-076) + 0.5 air. Option A (inner 7.6) only if J2 is 4.5, which no source gives |
| Wall / rim land | **rim land 1.6 mm** left, top, bottom (slice 4; was 2.4); **2.4 mm** right side (USB overmold pocket) (rule >= 1.2) | rim carries a flat 1.0 mm silicone gasket (ASSUMED, ~0.7 mm compressed, not modelled) |
| Floor / lid | **1.2 / 2.4 mm** (slice 4: floor 1.6 -> 1.2, the rule floor) | lid 2.4 (was 2.0) for stiffness on a 98 mm PETG plate [ASSUMED sizing, FEA not run]; film counterbore 0.6 leaves 1.8 |
| **Outer, lid on (without gasket)** | **97.3 x 56.9 x 12.2 mm (model, slice 4)** (+0.7 gasket). Slice 3 was 98.1 x 57.7 x 11.6. Option A (J2 4.5, not sourced) would give 11.2 mm | fits P1S (256^3) by a wide margin |
| Board margin to wall | 0.3 mm beyond J1 (0.8 mm beyond the board edge), 1.0 mm above the antenna tip (ASSUMED), tail 0.3 per side in the 12.6 mm tunnel | FDM plus JLC outline +-0.2 [src: layout-brief s.5] |
| Cell bay | cavity 53.0 x 35.1 x 7.2 (unchanged), beside the board | pcb-enclosure-bay.md, EEMB LP603449-PCM 51 x 34.5 x 6.3 |
| Product form | flat 97.3 x 56.9 x 12.2 slab, **stake tail leaves the bottom edge** | board plane vertical when in use, antenna up, light window and vents on the front face |

Decisions I took (Q1-Q11 of `layout-brief.md`), all open to Arsany: Q1 cell **beside** (Emil's recommendation; thermal and RF safe by geometry). Q3 board plane vertical, antenna up. Q4 USB-C enters the **right wall, low** (board y 33): window 9.6 x 3.9 mm plus a 14 x 8 x 1.2 mm pocket for the plug overmold (ASSUMED plug 8.94 x 3.26 + 0.3 per side; the receptacle mouth sits 1.2 mm behind the outer surface, so the plug engages about 1.2 mm less: **check with a real cable in Prototype 1**). Q5 stake: tail passes the bottom wall through a **separate seal plug** (13.4 x 2.4 x 7.6, tunnel 12.6 x 2.2) that slides over the tail end and drops into a rim-open notch; the tunnel is sealed with sealant (ASSUMED silicone, needs a decision and a Peter step). Q6: light window d 3.6 (+ 6.4 counterbore for a clear film disc, ASSUMED part) over U6 with a 6.0 mm collar tube; AHT20 vents = 3 slots 0.8 x 3.2 over U5 inside a baffle cup that opens toward the board interior; pinhole d 1.8 over SW3 with a guide tube ending 0.4 mm above the switch. Q7: M2 + brass heat-set inserts, 6 bosses, all >= 21 mm from the antenna (Q9 met). Q10 antenna end: PETG wall 2.4 mm, no metal, no coating. Effect of the 2.4 mm wall on the antenna: **OPEN** (fit check row 24 "PETG top wall over the antenna", standards s.7; RF check on a Prototype 1 print or a thinner wall, decision pending). Q8 cell wires: the cell sits beside J2 across the 5.0 mm gap, no wall between them (bay notch not needed); wire length unknown.

## 1b. P1S/PETG review (Arsany answer 2026-11-10: P1S Combo, SUNLU PETG 1.75 mm, 0.4 mm nozzle, reliable not weak)
Standard applied: `team/standards/3d-manufacturing.md` s.2-3, s.6, s.7. Parameters: `params_v3.py` (PETG_* block). Checks: fit_check_v3 section 6b and the new tests.
ID note: the tail-length decision keeps the ID **A-071**. This review is cited by its label, not by an ID, because A-071 was used for both in slice 2.

| Topic | Before (slice 2) | Now (slice 3; slice 4 values are in section 10) | Why / status |
|---|---|---|---|
| Wall, rim, floor | 2.4 / 1.6 mm | unchanged | >= 1.2 rule; 2.4 = 6 lines, PETG-safe |
| Lid plate | 2.0 mm | **2.4 mm** | 98 mm PETG plate between bosses. Stiffness is ASSUMED sizing, no FE run |
| Insert boss OD / wall round hole | 5.6 / 1.2 mm | **6.4 / 1.6 mm** | PETG target 1.6 (floor 1.2). Insert hole 3.2 is ASSUMED for an M2 x 3 insert: check the insert datasheet |
| Lid screw clearance | 2.2 mm | **2.4 mm** | M2 clearance for FDM PETG (ASSUMED) |
| Bottom boss row | y = INNER_Y0 + 2.6 | **+2.0; BOSS_STRIP 5.2 -> 5.4** | the 6.4 boss would have hit the cell cavity (found by new check) and a 1.0 mm skin fails 1.2. Now: 1.2 skin, 0.2 mm clear of the cell |
| Boss tightening | not stated | **0.25 N m max (ASSUMED)** | PETG creeps; over-torque strips the insert. Insert datasheet governs |
| Vent slots | 0.8 mm | **1.0 mm** | 2.5 lines; 0.8 was 2 lines, too close to the floor |
| Seal tunnel | 12.6 x 1.9 | **12.6 x 2.2** | 0.15 mm per side was not printable; 0.3 per side now. Sealant fills the gap (ASSUMED silicone) |
| Snap fits | none | **none** | the lid is screwed, no PETG snap is used. Snaps need a tested print: not in this round |
| Lid seal (NFR-05) | 1.0 mm silicone sheet on the rim, not modelled | unchanged, **silicone is a bought part, not PETG** | groove or compression not designed yet; open for Prototype 1 |
| Feature floor | none checked | **0.8 mm checked** (vents, pinhole, screw hole, light window, plug wall) | PETG_MIN_FEATURE [ASSUMED 0.8] |

**Print orientation on the P1S (0.4 mm, PETG, no supports):** tray floor down; lid outer face down, so the collars, cup and boss lands point up; plug standing with its tunnel vertical (no bridge across the slot). Bridge spans measured on the meshes: tray 9.6 mm (USB window), lid 6.4 mm (film counterbore), plug 0 mm. All <= 10 mm. Settings still to set in Bambu Studio (standards s.3 starting values: 0.16-0.20 mm layers, 4 walls, 20-35 % infill).

**Still open (not decided here):** tail length: A-071 is approved at 14 mm (sheet, 2026-11-12); the board change to the matching length is pending with Emil, and the DXF is still 25.0 mm. Seal type (silicone gasket, bought part, ASSUMED); insert brand and datasheet (not read); PETG screw torque on the bench (0.25 N m ASSUMED: not checked, fit row 'Screw torque limit' OPEN); the 1.6 mm PETG top wall over the antenna (A-084 accepted as a risk on the sheet; RF effect not measured, fit row OPEN); test print to measure PETG shrink (PETG_SHRINK 0.4 % ASSUMED, not applied to the model).

## 2. Fit check (slice 4, real runs: `fit_check_v3.py --tail 14` and `--tail 20`, cadquery 2.8.0 in a scratch venv): **40 PASS, 0 FAIL, 19 OPEN** for each variant. Tables: `fit_check_v3_compact_tail14.md` and `fit_check_v3_compact_tail20.md`. The 37 PASS / 18 OPEN counts below are the slice-3 record.
Slice-3 record (not current): full tables [fit_check_v3_tail14.md](fit_check_v3_tail14.md) and [fit_check_v3_tail20.md](fit_check_v3_tail20.md). They describe INNER_H 7.6 and J2 4.5 (slice 3) and are kept as the record. Negative-control tests prove the check can fail; interference rows are boolean intersections of the CadQuery solids.

**Boss clearance (slice 4):** the nearest brass insert hole to the antenna rectangle is **22.2 mm** (fit row 24), against the 15 mm RF keep-out rule (layout-brief Q9): met. The top-left boss moved x -2.5 -> -3.5 because its plan gap to the board corner was **0.34 mm**: a full-height boss beside the board corner could catch the board on insertion. The gap is now **1.10 mm** (fit row 'Boss to board outline', OPEN: the 1.0 mm threshold is ASSUMED). The bottom-left boss moved the same way (gap 1.68 mm, y unchanged).

**Slice 3 fix round (record, not current; J2 4.5 and the 7.6 mm box were slice 3 values):**
- Item 1: the section 7 values now match the code: LID_T 2.4, TUNNEL 12.6 x 2.2, BOSS_D 6.4 (were 2.0, 1.9, 5.6).
- Item 2: `docs/interfaces/pcb-enclosure-bay.md` lid 2.4 (was 2.0).
- Item 4: J2 height stays **4.5 ASSUMED**. No repo source has it; not invented. Needs Arsany candidate (datasheet).
- Item 5: height rows fixed as above; not vacuous any more.
- Item 6: board retention (pads or M2 holes) is Emil's part. **Not changed, still open** (section 4 item 6).
- Item 7: tail length is **not decided** (A-071, Arsany). **Not changed**: still 25 mm.

## 3. Source answers for Emil and Nora (read from `agent/pcb/4.P2` @ da39d2c, files in `mechanical/jlc_prep/input`)
- **Placeholder footprints:** on the first board (da39d2c) the file tagged 9 (8 PLACEHOLDER + E1 ELECTRODE; the "7" was stale text). On the #73 board only **3 remain: U5, U6 (PLACEHOLDER) and E1 (ELECTRODE)**; U1, J1, J2, SW1-3 are real footprints (test `test_source_counts` reads the file).
- **Antenna gap: both numbers are correct, they measure different things.** 26.2 mm = `check_layout.py` `rect_gap(ant_tip, cell)`: the overhang rectangle (module x 20.3..33.5, y 0..+4.5 on #73) to the cell cavity, nearest corner (20.3, 0) to (-5.0, -6.9). 27.7 mm on #73 (28.4 on the old board, overhang 6.0) = from the antenna tip line (y +4.5) to the same corner. Use **26.2 (the smaller, conservative one)**; both pass the 15 mm rule (tests `test_antenna_gap_both_methods`).

## 4. What I need Emil to fix (board outline values) before 11-11
1. **Outline unchanged:** body 34.5 x 42.0, tail 12.0 x 25.0 (width tolerance +-0.2), thickness 1.6 +-10 %. Any change moves the tunnel and plug.
2. **Cell cavity position** relative to the board: 53.0 x 35.1, gap 5.0, cavity y -42.0..-6.9 (DXF). If he changes beside/under, the enclosure is redone.
3. **Antenna module** x 20.3..33.5, overhang now **+4.5** above the top edge (derived by Emil in #73). I keep 1.0 mm air above it.
4. **Positions I built features on:** U6 (11.5, -4.5), U5 (4.5, -4.5), SW3 (5.0, -23.5) (DXF coordinates, mm, read from #73), J1 centre y -33.0 rotated 90 deg, shell reaching x 35.0 (0.5 past the board edge). Lock these or tell me the new ones.
5. **Heights** of J2 (JST S2B-PH-SM4-TB; model 5.5 from the LCSC C295747 Z-height listing, A-076, SECONDARY), J1 (3.3 flat ASSUMED; A-087 flat approved 2026-11-13 (sheet Needs Arsany: Done); the 11.94 +-0.25 upright figure is an unsourced brief value, not in the HRO TYPE-C-31-M-12 drawing (see PR #95); REJECTED by A-087, record only), U1 (2.4, the only DATASHEET value), SW1-3 (1.5, SECONDARY), since they set the 8.6 mm inner height. **Still to confirm:** the JST drawing for the exact part (element14 lists 8.0 mm for a likely B2B variant), and the flat USB-C part, which Emil still picks. The other heights are also unread. Do not fill them with unsourced values.
6. **Board retention:** the board has no mounting holes. I clamp with 4 standoff pads below (bottom is bare GND, fine) and lid clamp pads above, but only **one** component-free 2 x 2 mm spot exists on the top face (about (1.3, -8.0)). Please give **two more keep-clear 2 x 2 mm pads** (e.g. near the bottom corners) **or** two M2 holes (d 2.2, no metal within 15 mm of the antenna). The lid pad modelled today is that one spot only.
7. **Decision (Arsany/Emil):** tail length. The seal plug and boss strip put the outer bottom wall at y -49.8 (`params_v3.py` OUT_Y0), so only about 13 mm of the 20 mm electrode copper (y -43..-63) is outside. If 20 mm must be in soil, the tail needs about +6 mm (to 31 mm). My stake size (Q5) is still an assumption.

## 4b. Merge order
Stacked: **PR #74 (slice 2, draft) first, then this PR (#83).** This branch contains #74's commits. The board copy in `mechanical/enclosure_v3/input/` is from PR #73 (merged). Retarget to `main` after #74 merges.

## 5. Open, honest list
- Prototype 1 print and a real cell are still needed (standards s.10); the 0.2 mm clearances and the USB plug engagement are untested.
- ASSUMED: component heights, 1.0 mm air above the antenna, gasket 1.0 mm silicone (not modelled), sealant, film window disc, insert hole 3.2 mm, plug dimensions, swelling 10 % (bay). No IP rating is claimed; NFR-05 (splash-proof) needs a spray test after Prototype 1.
- No Bambu Studio slice here: print time and real grams are **not run**. Solid-volume upper bound: tray 15.2 + lid 11.6 + plug 0.2 cm3 = 27.0 cm3 (about 34 g at 1.27 g/cm3, PETG density ASSUMED); infill-based mass is lower.
- Design touch (nilwerk trace relief, `DESIGN_TOUCH`) is **off** in this slice; the Arsany-approved single signature detail still needs placing on the lid.
- Cell retention (no printed cell clamp yet; foam tape ASSUMED), cell wire routing and plug polarity warning on the assembly drawing: next slice. Deliverables A-G: A, B, C (CAD, STEP/STL/3MF, dimensions) and D (orientation, no-support check) done at slice level; E, F (cost and margin), G not done.
- Not touched: the PCB, any order, printing. **Drive upload not done** (not attempted; exports are in git only, path below). Someone with Drive access copies `enclosure/v3/` to `Plant Monitor/04_Builds/Enclosure/v3`.

## 6. Print notes (0.4 mm nozzle, PETG, no supports)
Tray: floor down. Lid: **outer face down**, collars and cups point up; longest bridges 9.6 mm (USB window top) and 6.4 mm (film counterbore). Plug: standing, Y axis up. Starting settings from standards s.3 (layer 0.2, 4 walls, 25 % infill). Orientation and bridge spans were checked on the meshes (fit check rows 49-53).

## 7. Fusion 360 strategy (standard s.1a)
CadQuery is the source: `mechanical/enclosure_v3/params_v3.py` (parameters, same names as below), `enclosure_v3.py` (tray, lid, plug, reference bodies), `board_src.py` (reads the board file). Bodies: `tray`, `lid`, `tail_plug` (printed), `reference_board_cell` (not printed). Parameter table for Fusion: section 10 (slice 4 values; the slice-3 values in this line are the record). Arsany would edit in Fusion: boss positions, USB pocket, outer fillets, the lid face for the design touch. A changed STEP from him becomes the reference for the version.

## 8. Files (versioned v3; v1/v2 untouched)
`enclosure_v3_{tray,lid,tail_plug}.{step,stl,3mf}`, `enclosure_v3_assembly.step`, `enclosure_v3_reference_board_cell.step`, `renders/v3_{hero,exploded,section,plan}.png`, `fit_check_v3.md`.
Run from `projects/plant-monitor/mechanical/enclosure_v3/` (Python 3.11, `pip install cadquery trimesh numpy matplotlib networkx pytest`): `python3 build_v3.py && python3 render_v3.py && python3 fit_check_v3.py && python3 -m pytest test_v3.py` (12 tests; CadQuery 2.8.0 used in the fix round). Renders are matplotlib painter's-algorithm renders of the exported STL, so depth sorting has small artefacts.

## 9. Slice 3 (Yara, task 4.E3-s3): tail variants 14 / 20 mm and sourced heights

Stacked on slice 2 (sections above unchanged; their height values are superseded by section 9 where they differ). Nothing printed, ordered or uploaded.

**Tail length (A-071, DECIDED: 14 mm, Arsany 2026-11-12; sheet Done).** Read as the **soil electrode copper beyond the outer bottom face** of the enclosure (the number used in section 1b item 7). Today 13.2 mm of the 20 mm copper is outside (copper tip y -63.0, outer face y -49.8). The enclosure does not move between variants, so the printed housing is identical (same STL vertices and volumes as slice 2, checked). Only the **board tail** changes:

| Variant | Electrode beyond the outer face | Board tail (body edge to tip) | vs the 25.0 mm DXF | Status |
|---|---|---|---|---|
| 14 mm | 14.0 | 25.8 | +0.8 | **APPROVED** (A-071). `pcb/gen_pcb.py` on main has 25.8; the DXF copy in `mechanical/enclosure_v3/input/` is still 25.0, so the fit row stays OPEN until `input/` is refreshed |
| 20 mm | 20.0 | 31.8 | +6.8 | reference only (not chosen) |

Derivation: copper tip = outer face - electrode length; tail tip = copper tip - 4.0 (bare tip, DXF). Code: `params_v3.TAIL_VARIANTS`, `tail_len_for()`, `board_facts.electrode_span()`.

**Sourced heights (H_SRC in `params_v3.py`).** The fit check uses the same height table; each has a tag.

| Ref | Part (LCSC) | Model height | Source | Status |
|---|---|---|---|---|
| U1 | ESP32-C3-MINI-1-N4 (C2838502) | 2.4 | Espressif datasheet v2.2, Table 1-1 p.3: 13.2 x 16.6 x 2.4 mm | **DATASHEET** |
| U5 | AHT20 (C2757850) | 1.0 | datasheets.com, sekorm listings: 3 x 3 x 1.0 | SECONDARY (PDF not read) |
| U6 | BH1750FVI-TR (C78960) | 0.75 | Arrow and RS Online: max 0.75 (Future 0.7) | SECONDARY (PDF not read) |
| SW1-3 | TS-1187A-B-A-B (C318884) | 1.5 | JLCPCB, LCSC, HQ Online: 1.5 | SECONDARY (XKB PDF not read) |
| J2 | S2B-PH-SM4-TB (C295747) | **5.5** (slice 4 model, was 4.5) | sourced: LCSC C295747 Z-height listing 5.5 (A-076, answered 2026-11-13); IBS Electronics 5.5; element14 8.0 for a likely B2B variant (not confirmed as this part); JST drawing to confirm | **SECONDARY, OPEN** (fit rows 12, 14, 15: 0.5 mm air at INNER_H 8.6; the exact part and drawing are still to confirm) |
| J1 | TYPE-C-31-M-12 (C165948) | 3.3 flat | flat: none read (LCSC datasheet link gives a wrapper page). Upright 11.94 +-0.25: unsourced brief value, not in the HRO TYPE-C-31-M-12 drawing (see PR #95); REJECTED by A-087, record only | flat / edge-mount approved (A-087, Arsany 2026-11-13); height **ASSUMED, never PASS** until Ines confirms Emil's 3.26 mm reading. C165948 is already the flat part (no pick needed); its 3.26 mm is read once, by Emil, in PR #95 (docs/j1-usbc-flat.md on branch agent/pcb/gerber-pkg), second read by Ines pending. Fit row 'J1 USB-C height' OPEN. J1 is not the height driver: J2 sets the 8.6 mm inner height, J1 leaves 2.7 mm air |
| U3 | TP4056 ESOP-8 (C16581) | 1.75 | none (LCSC datasheet link gives a wrapper page) | ASSUMED |
| others | D1, U2, U4, U7, Q1, D2, D3, R/C | 0.55-1.1 | not read | ASSUMED |

Only U1 has a datasheet page. The Mouser JST datasheet returned HTTP 503 and the LCSC PDFs return wrapper pages in this session, so J1, J2 and U3 could not be read. Values not read from a source are tagged ASSUMED or SECONDARY; none is presented as sourced.

**Slice 3 record, fit check (fix round 3; not current):** 37 PASS, 0 FAIL, 18 OPEN for each variant. A pass against an ASSUMED threshold is OPEN, not PASS (Arsany rule). The OPEN rows: row 2 board outline change for the variant (A-071); row 5 antenna air 1.0 mm (ASSUMED); row 12 tallest part to lid underside (0.50 mm rests on J2 4.5 ASSUMED); row 13 heights sourced from a datasheet 1 of 17 (the rest SECONDARY, CONFLICT or ASSUMED); row 14 J2 at the distributor value 5.5 mm (A-076); row 15 lid interference (evaluated at the J2 4.5 model value); row 24 PETG top wall over the antenna (accepted for the demo, A-084); rows 33-37 PETG feature floor 0.8 mm (ASSUMED); rows 38-39 seal clearance 0.3 mm (ASSUMED, both sides); row 40 PETG boss wall 1.6 mm (our own target, insert datasheet not read); row 44 screw torque (ASSUMED, not checked); row 54 model heights equal their cited source (SECONDARY values not PDF-checked); row 55 J1 upright height 11.94 (OPEN, A-087). Fix round 3 (Theo's verdict on 689c161): rows 39 and 40 went from PASS to OPEN, row 55 was added, and the counts above are the real output. Reports: `fit_check_v3_tail14.md`, `fit_check_v3_tail20.md`. Tests: `test_v3.py` (28 passed, including one mutation test per sourced value; the mechanical folder `pytest -q` gives 55 passed, see the PR comment).

**Files.** `enclosure_v3_assembly_tail14.step`, `enclosure_v3_assembly_tail20.step`, `enclosure_v3_reference_board_cell_tail{14,20}.step` (reference bodies, not printed). Renders: `renders/tail14_plan.png`, `renders/tail20_plan.png`, `renders/tail_compare_side.png`. Interface values for Emil: `mechanical/enclosure_v3/LOCKED_INTERFACE.md` (generated, a test keeps it current). The slice 2 files stay as the record of the 25 mm DXF tail.

**Still open:** see section 10 (current list). The slice-3 list is superseded.

## 10. Slice 4 (Yara, task 4.E3 EXTRA, Arsany 2026-11-12): compact product shell
Branch `agent/mechanical/4.E3-s4`, stacked on PR #83 (slice 3), which is stacked on PR #74. Merge order: #74, #83, this. Files: `enclosure_v3_compact_*` (STEP, STL, 3MF; slice 2/3 files stay as the record). Renders: `renders/compact_*.png`. Fit check records: `fit_check_v3_compact_tail14.md`, `fit_check_v3_compact_tail20.md`.

**Outer size, slice 3 -> slice 4 (lid on, from `params_v3`):**

| | Outer X x Y x Z (mm) | Box volume (mm3) | Solid volume, outer skin (mm3) |
|---|---|---|---|
| Slice 3 (floor 1.6, inner 7.6 = J2 4.5, ASSUMED) | 98.1 x 57.7 x 11.6 | 65,660 | 65,571 |
| **Slice 4, model (inner 8.6 = J2 5.5 budget, A-076)** | **97.3 x 56.9 x 12.2** | 67,544 | 66,974 |
| Slice 4, option A if J2 is sourced at 4.5 (`INNER_H_OPT_A`) | 97.3 x 56.9 x 11.2 | 62,007 | 61,451 |

Read: the footprint is 2.2 % smaller (5,660 -> 5,536 mm2). The model is 0.6 mm taller than slice 3 because the J2 value (5.5 from the listing, A-076) is larger than the floor saving (-0.4 mm). The -5.5 % box volume case needs J2 <= 4.5 mm, which no source gives, so it is shown as option A for reference only.

**What changed:** plan corners rounded (R 4.0 outside, 1.5 inside); bottom edge 1.2 mm and lid top 2.2 mm rounded (one continuous skin, seam only at the lid line); floor 1.6 -> 1.2 (rule floor); rim land left/top/bottom 2.4 -> 1.6 (`WALL_LOW`), right side 2.4 kept (USB overmold pocket 1.2 deep leaves 1.2); bottom bosses at y -45.4 (cell clearance), top bosses y 3.2 -> 2.5 (skin to the 1.6 top wall); boss x -2.5 -> -3.5 in both rows (plan gap to the board corner, see Boss clearance).

**Interface changes for Emil (vs slice 3; these were wrongly described as unchanged before this round):** (1) screw bosses: top row y 3.2 -> 2.5, both rows x -2.5 -> -3.5; (2) outer envelope 98.1 x 57.7 x 11.6 -> **97.3 x 56.9 x 12.2** (inner 8.6); (3) floor 1.6 -> 1.2 and rim land 2.4 -> 1.6 (left, top, bottom); (4) outline corners R 4.0 and soft edges (bottom 1.2, top 2.2). Single source for all values: `mechanical/enclosure_v3/LOCKED_INTERFACE.md` section 8. **Unchanged:** board outline (from the #73 DXF), USB-C cut-out 9.6 x 3.9, light window, AHT20 vents, cell bay, pinhole, electrode tail (DXF 25 mm until the board change).

**Requirements (TEAM §6):** NFR-05 (splash-proof seal: lid rim and tail tunnel with sealant, owned by Yara), FR-D01 (five sensor values: light window over U6, AHT20 vents over U5, soil electrode), FR-D06 (USB-C charging: right-wall window), FR-D07 (factory reset: pinhole over SW3). No new requirement is added. Not verified: a seal or splash test, the light and vent performance, the RF effect.

**Print (0.4 mm nozzle, PETG, P1S):** tray floor down, lid outer face down, plug as before. No support needed for the shell: the checker's largest reach of a downward face above the bed is 0.9 mm (tray) and 1.4 mm (lid), both the soft edges; the USB window top spans 2.4 mm (wall thickness). Not verified in a slicer yet (no Bambu Studio run).

**Fusion 360 strategy (standard s.1a):** parameter table (names and values as in `params_v3.py`, mm):

| Parameter | Value | Note |
|---|---|---|
| STANDOFF | 1.0 | board underside above the floor |
| INNER_H | 8.6 | 1.0 + board 1.6 + J2 5.5 + air 0.5 (A-076 listing) |
| FLOOR / LID_T | 1.2 / 2.4 | tray floor / lid plate; counterbore WIN_CB_DEPTH 0.6 |
| WALL_LOW / WALL | 1.6 / 2.4 | rim land left, top, bottom / right (USB side) |
| FILLET / FILLET_BOT / FILLET_TOP | 4.0 / 1.2 / 2.2 | outer plan corner, bottom edge, lid top edge |
| FILLET_INNER | 1.5 | cavity corner radius |
| BOSS_D / INSERT_HOLE | 6.4 / 3.2 | boss diameter, heat-set insert hole |
| BOSS_XY | (-55, 2.5), (-27, 2.5), (-3.5, 2.5); y -45.4 row | screw positions |
| USB_W x USB_H / USB_POCKET | 9.6 x 3.9 / 14.0 x 8.0 x 1.2 | USB-C window and overmold pocket |
| WIN_D / WIN_CB_D / WIN_CB_DEPTH | 3.6 / 6.4 / 0.6 | light window and film counterbore |
| VENT_N / VENT_W / VENT_L / VENT_PITCH | 3 / 1.0 / 3.2 / 1.6 | AHT20 slots |
| TUNNEL_W x TUNNEL_H / PLUG_T | 12.6 x 2.2 / 1.6 | tail tunnel and plug wall |

Bodies: tray, lid, tail plug (3 bodies, STEP). Features to edit in Fusion: the outer fillets (`FILLET`, `FILLET_BOT`, `FILLET_TOP`), the cavity corner (`FILLET_INNER`), the USB window and pocket (`USB_W`, `USB_H`, `USB_POCKET`), the light window (`WIN_D`), the vents (`VENT_*`). A change to `INNER_H` (J2) moves the lid and the tray together: flag it in Fusion, do not edit one body only.

**Open in this slice (current, slice 4 round 2):** A-071 tail length approved at 14 mm (sheet, 2026-11-12), board change to the matching tail length pending with Emil (fit row 'Board tail in DXF', OPEN). A-076 J2 height: model 5.5 from the LCSC C295747 Z-height listing (SECONDARY); the JST drawing must confirm it, and element14 lists 8.0 mm for a likely B2B variant, so the exact part must be confirmed before the box height is locked (OPEN). A-087 J1 USB-C flat / edge-mount, approved 2026-11-13: model 3.30 flat, ASSUMED (no datasheet height for the flat part read); the part is still to be picked by Emil; the upright 11.94 value is not used. A-084 PETG wall over the antenna: sheet Done, RF risk accepted; the wall is 1.6 mm and the RF effect is not measured (fit row OPEN). Screw torque not checked (ASSUMED). Boss plan gap threshold 1.0 mm ASSUMED (OPEN). Not run: slicer, print, seal or splash test, RF measurement.

# Plant Monitor v1 demo housing, round 3: fit for 5 mm parts (4.E5)

> **FIT-CHECK ONLY. Indoor demo, not splash-proof, not IP-rated.** The first print is a fit-check part. Nothing here is printed, sliced, measured on hardware or RF-tested. The per-part heights are still open (A-094 measurement list); the 5 mm figure is the owner's bound, not a caliper reading per part.
> **Never charge unattended inside the closed box.** The LiPo sits under the perfboard, and the only vents are over the AHT20.

Yara (3D Product Designer) · 2026-11-28 · source `projects/plant-monitor/mechanical/enclosure_v1_demo/` (`params_v1.py` is the single source; round 2 values are in git history).
Round 2 exports stay in `enclosure/v1_demo_compact/` (not overwritten). Enclosure v3 (4.E3) is stopped and was not touched.

**Status of every number.** OWNER = Arsany, 28 Nov (A-094): every part on the perfboard is at most 5 mm high (a bound, not a per-part measurement). MEASURED = Arsany (bare perfboard and footprints). WIRING = Emil's typical value in `projects/plant-monitor/v1/WIRING.md`, UNVERIFIED. BRIEF = task brief, no datasheet read. ASSUMED = my assumption with the stated margin. OWNER, WIRING, ASSUMED and BRIEF values never give a PASS in the fit check.

## Why this round
The owner's bound is 5 mm per part. The round-2 model used WIRING heights up to 12 mm (J1 and J3 headers), so its lid sat 29.8 mm up. With 5 mm parts the lid can come down, but the USB-C openings still set the minimum height: the parting plane must stay above both openings (24.95 mm top + 1.05 mm rim = 26.0 mm). So the seam, not the parts, now governs the lid.

## Changes (round 2 -> round 3)
| Item | Round 2 | Round 3 | Basis |
|---|---|---|---|
| Part height used for lid clearance (`PART_H_OWNER`) | 12.0 (J1/J3), 6.8 (SuperMini) | **5.0** every part | OWNER (A-094) |
| Lid plate underside `Z_TOP` | 29.8 | **28.0** = seam 26.0 + skirt 2.0 | `max(parts + 2.0 margin, seam + skirt)` |
| Lid plate top `Z_LID_TOP` | 31.4 | **29.6** | |
| Lid shell above the parting plane | 5.4 | **3.6** (skirt 2.0 + plate 1.6) | skirt ASSUMED design value |
| Outer size L x W x H | 88.5 x 72.6 x 31.4 | **88.5 x 72.6 x 29.6** (-1.8 mm, -6 %) | |
| Lid print height (hold-down pins set the lowest point) | 15.3 | **13.5** | |
| Screw | M2 x 8 | **M2 x 6** (formula: need 5.4) | ASSUMED head and insert, nothing ordered |
| Board, cell cradle, USB-C, BH1750, AHT20, soil exit, J1 hatch, antenna keep-out | round 2 | unchanged | |

## Height reference (one frame for every stack height)
- **Frame:** all heights in this README are measured from the **perfboard top** (z = 0 at the top face, the component side), unless a row says "lid underside" or "floor". The lid clearance is then: lid underside z 28.0 minus perfboard top 15.8 = 12.2 mm of room above the board top.
- **Planned bound (used for the model):** 5.0 mm above the perfboard top for every part (owner bound, A-094).
- **Typical values, not measured (UNVERIFIED):** WIRING.md section 5 gives the SuperMini top (USB-C) as 8.8 mm. That figure starts at the perfboard underside (2.0 mm board + 6.8 mm), so it is **6.8 mm above the perfboard top**. The 6.8 mm is used only as the stress row (SuperMini at WIRING stack height). It is a typical value, not a measurement.
- J1 with jumper and J3 with Dupont plug: WIRING typical about 12 mm above the perfboard top. Stress row only.

## Owner caliper inputs still needed (height above the perfboard top, mm)
| Part | Point to measure | Reference | Used in model now |
|---|---|---|---|
| SuperMini, with USB-C | highest point incl. USB-C connector | perfboard top | bound 5.0; stress 6.8 |
| J1, with jumper | highest point incl. shunt | perfboard top | bound 5.0; stress 12 (WIRING about 12 is an assumption about the board-top reference until the caliper reading is in) |
| J3, with Dupont plug | highest point incl. plug | perfboard top | bound 5.0; stress 12 |
| TP4056 with USB-C, BH1750, AHT20 | highest point | perfboard top | bound 5.0 |
| Floor to perfboard underside (trimmed pins, wires) | lowest point under the board | perfboard underside | 12.2 = cell cavity 7.2 + pin tips 4.0 (UNVERIFIED) + margin 1.0 |

## Clearances (mm, from the model)
| What | Value | Need | Status |
|---|---|---|---|
| Board top to part tops (owner bound 5.0) | 5.0 | 5.0 (OWNER bound) | OWNER |
| Lid underside to 5 mm part tops | **7.2** | >= 2.0 margin | OPEN (per-part height UNVERIFIED) |
| Parting plane (seam) to 5 mm part tops | 5.2 | | geometry |
| Largest part height the lid clears with 2.0 margin | **10.2** | | derived |
| Stress: SuperMini at WIRING stack 6.8 mm | 5.4 clearance | >= 2.0 | OPEN (WIRING conflicts with the 5 mm bound) |
| **Stress: J1 / J3 at WIRING 12 mm** | **0.2 clearance, 1.8 mm short** | >= 2.0 | **NOT MET if the WIRING height is right** |
| Floor to board underside (cell cradle, pin tips 4.0 ASSUMED + cell cavity 7.2 + margin 1.0) | 12.2 | cavity + pin tips | OPEN (pin tips UNVERIFIED) |
| USB-C openings: highest top 24.95, rim to seam | 1.05 | >= 1.0 | OPEN (WIRING stack) |
| Lid part to tallest part: interference (lid vs part boxes) | 0.000 mm3 | 0 | OPEN (heights per owner bound) |
| Walls, floor, lid | 1.6 / 1.6 / 1.6 | >= 1.2 (rule), >= 1.6 (task) | PASS |
| Watertight STL base / lid | yes / yes (volume 29.3 / 12.0 cm3) | watertight | PASS |
| Both parts on the bed, no overhang beyond 0.67 mm (lid) | 0.67 mm | <= 0.8 (ASSUMED) | OPEN |
| Build volume | base 88.5 x 72.6 x 26.0; lid 88.5 x 72.6 x 13.5 | 256^3 | OPEN (derived from ASSUMED pin tips) |

**Fit check (`fit_check_round3.md` in this folder):** 7 PASS / 0 FAIL / 4 NOT MET / 52 OPEN. The PASS rows are watertight, on the bed, walls and pads inside the board. The NOT MET rows are the board support gap under x 48-70, the AHT20 over the cell, the cell 57 % under the board, and the J1/J3 stress row. Tests: `python -m pytest -q enclosure_v1_demo/test_v1.py` (26 passed).

## Parameter table (Fusion 360 strategy, standard 1a; mirrors `params_v1.py`)
| Name | Value | Status |
|---|---|---|
| `PB_L x PB_W x PB_T` | 70 x 50 x 2 | MEASURED |
| `PART_H_OWNER` | 5.0 | OWNER |
| `LID_MARGIN` | 2.0 | ASSUMED |
| `LID_SKIRT` | 2.0 | ASSUMED design value |
| `WALL`, `FLOOR`, `LID_T` | 1.6, 1.6, 1.6 | RULE |
| `FIT` | 0.4 per side | RULE (printer not calibrated) |
| `STANDOFF_H` (floor to board) | 12.2 | cell cavity + WIRING pin tips 4.0 (UNVERIFIED) + 1.0 ASSUMED |
| `PLUG_W x PLUG_H` (USB-C) | 14 x 8 | ASSUMED |
| `SCREW` | M2 x 6 pan head, M2 heat-set insert, hole 3.2 | ASSUMED, nothing ordered |

Body split: two bodies (base, lid). Features Arsany would edit in Fusion: `Z_TOP` (lid skirt and plate), `PART_H_OWNER`, the USB-C and vent sizes, boss positions. Any Fusion STEP he exports becomes the reference for this version; divergence from `params_v1.py` is flagged, not overwritten.

## Files (`enclosure/v1_demo_fit5/`)
- `enclosure_v1_demo_base.step|stl|3mf`, `enclosure_v1_demo_lid.step|stl|3mf`: base as printed (floor on the bed), lid as printed (top face on the bed). STEP files are the assembled position for Fusion 360.
- `enclosure_v1_demo_assembly_with_reference_parts.step`: base, lid, reference perfboard, 5 mm part boxes and cell. Not printed.
- `renders/`: `v1_demo_hero.png`, `v1_demo_exploded.png`, `v1_demo_section.png` (two cuts through the USB-C row and the BH1750 row), `v1_demo_plan.png`. Real renders of the exported meshes (VTK under xvfb; matplotlib for the cuts and the plan).
- `fit_check_round3.md`: the fit-check table, written by `fit_check_v1.py --md`.

## Print notes (P1S, PETG black/grey/white, 0.4 mm nozzle, not sliced)
- Base: floor on the bed, open side up. Bridges: two USB-C ceilings (14 mm x 1.6 mm) and the cable slot (9 mm). No supports planned; test on the first base.
- Lid: top face on the bed, one 0.6 mm chamfer as the only overhang.
- Material: solid-volume upper bound 41.2 cm3 (base 29.3 + lid 12.0), about 52 g at 1.27 g/cm3. This is a solid volume, not a slice. Cost at an ASSUMED 20 EUR/kg is about 1.05 EUR of filament. Print time: NOT RUN.
- Fasteners: 5 x M2 x 6 pan head, 5 x M2 heat-set inserts (hole 3.2, ASSUMED). Nothing ordered.
- Assembly: insert the inserts, lay the perfboard on the pads against the fins, feed the LiPo lead through the notch, check J1 is open, fit the lid, 5 screws. Charging rule as in round 2.

## Deliverables A-G (standard section 9), status
A concept: round-2 concept, unchanged. B architecture: seam and parts clearance done here; the board sits on pads with no support under x 48-70 (open). C CAD: done (source, STEP, STL, 3MF, renders). D manufacturing: estimates only, slice NOT RUN. E assembly: list above, no sequence photo. F cost and margin: NOT RUN (filament only, ASSUMED price). G quality control: NOT RUN (no print, no fit test).

## NOT RUN
- **Real print fit** (perfboard pocket, USB-C plug through the openings, lid over the parts): needs the owner's printed part and a caliper.
- **Per-part heights** (the owner gave a 5 mm bound; each part still needs a caliper reading, and the SuperMini stack needs a check against WIRING 6.8 mm).
- **Photo comparison with the as-built box:** the owner's photo is not in the repo, so no pixel check was done. From the owner's description: USB-C access, BH1750 window and soil cable exit at the bottom match the model. The LiPo is **under the board** in this model but was described as **along one wall** in the photo. This is an open conflict: the round-2 placement (A-100 option a) was decided on the model, not checked against the photo.
- **Bambu Studio slice** (print time, grams from the slicer), **RF range test**, **Drive upload** (no Drive access from this run), **CI regeneration** (no CI job yet).

## Arsany must verify (with the printed box and a caliper)
1. Height above the board top of J1 (with jumper), J3 (with Dupont plug), SuperMini (USB-C included) and the other parts: all must be at most 5 mm (the bound) and the SuperMini stack must be checked against 6.8 mm (WIRING). A 12 mm header does not clear the lid (NOT MET row).
2. Under-board height with trimmed pins and wires (sets the 12.2 mm floor gap).
3. Perfboard drops into the pocket with 0.4 mm per side; both USB-C plugs go through the 14 x 8 openings.
4. Where the LiPo really sits: under the board (this model) or along one wall (the photo).
5. The soil cable exit and the BOOT/RESET tubes (end 1 mm above the assumed key tops) against the built board.
6. Screws: M2 x 6 pan head and the insert hole 3.2 mm. Nothing ordered by the team.

## Run
From `projects/plant-monitor/mechanical`: `pip install cadquery trimesh numpy matplotlib networkx pytest vtk`; `python enclosure_v1_demo/build_v1.py`; `xvfb-run -a -s "-screen 0 1600x1200x24" python enclosure_v1_demo/render_v1.py`; `python enclosure_v1_demo/fit_check_v1.py --md <out.md>`; `python -m pytest -q enclosure_v1_demo/test_v1.py`.

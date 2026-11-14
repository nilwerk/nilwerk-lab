Tail variant: 14 mm (A-071: 14 mm approved by Arsany 2026-11-12)

| # | Check | Value | Need | Result | Source |
|---|---|---|---|---|---|
| 1 | Tail variant 14 mm: electrode copper beyond outer bottom face | 14.00 mm (copper tip y -63.80) | = 14.0 mm (variant) | **PASS** | params_v3 TAIL_VARIANTS; copper from board E1 pad (board_facts.electrode_span), tip margin 4.0 from DXF |
| 2 | Board tail in DXF (input/) matches the variant | DXF 25.00 mm vs variant 25.80 mm (+0.80) | = variant tail | **OPEN** | board DXF = #73; a longer tail for the 20 mm variant is a board outline change for Emil (not in repo) (OPEN: A-071 approved 14 mm (Arsany 2026-11-12) = board tail 25.8; the board copy in input/ is still the 25.0 mm DXF of #73 (pcb/gen_pcb.py on main already has 25.8). 20 mm is reference only) |
| 3 | Interference tail (14 variant) vs tray and seal plug | 0.000 mm3 | 0 (contact allowed) | **PASS** | boolean intersect: tail solid vs tray and tail_plug |
| 4 | Right-most part (J1 shell) to right wall (X) | 0.30 mm (board edge 0.80) | >= 0.30 (FDM + PCB +-0.2) | **PASS** | params_v3 INNER_X1, DXF outline |
| 5 | Antenna tip to top wall (Y) | 1.00 mm | >= 1.0 [ASSUMED] | **OPEN** | DXF MODULE_U1 (overhang derived by Emil); Q10 detuning open (OPEN: the 1.0 mm threshold is ASSUMED, so a pass against it is not a pass (Arsany rule)) |
| 6 | Tail width vs tunnel (per side) | 0.30 mm | >= 0.30 | **PASS** | DXF tail 12.0; JLC outline +-0.2 (layout-brief s.5) |
| 7 | Tail thickness vs tunnel height (per side) | 0.30 mm | >= 0.15 (JLC 1.6 +-10 % = 0.16) | **PASS** | layout-brief s.5 thickness tolerance |
| 8 | Cell cavity (X x Y) inside the inner box | 53.0 x 35.1 | = bay.dims A_eemb603449 (53.0 x 35.1) | **PASS** | pcb-enclosure-bay.md; bay.py |
| 9 | Cell 51 x 34.5 x 6.3 spare in cavity | L 2.0 / W 0.6 / H 0.9 | L>=2.0 W>=0.6 H>=0.9 | **PASS** | bay.dims |
| 10 | Cell cavity height vs inner height (cell only; no assumed part height in this row) | 7.2 vs 8.6 | cavity <= inner | **PASS** | bay.dims bay_h 7.2; INNER_H is a fixed design value |
| 11 | Board to cell cavity gap (X) | 5.0 mm | = 5.0 (gen_pcb CELL_GAP) | **PASS** | DXF CELL_BAY_CAVITY |
| 12 | Tallest part to lid underside (derived from assumed heights) | 0.50 mm (J2 5.5, SECONDARY) | >= 0.5 (+0.7 mm gasket thickness not counted) | **OPEN** | H_BY_REF; J2 height needs a datasheet value (OPEN, A-076) (OPEN: the number rests on J2 5.5, a SECONDARY listing value (A-076); the JST drawing is not read) |
| 13 | Heights with a datasheet page in the model | 1 of 17 DATASHEET (U1); 6 SECONDARY, 0 CONFLICT, 10 ASSUMED | every height cites a datasheet; the rest are listed as SECONDARY or ASSUMED | **OPEN** | params_v3 H_SRC; a distributor listing is not a datasheet citation (standards s.7) (OPEN: sourcing is incomplete; see H_SRC for each part) |
| 14 | J2 at 5.5 mm (model value, A-076) | 0.50 mm to lid underside (needs INNER_H >= 8.6) | >= 0.5 | **OPEN** | JLCPCB Z-height 5.5 mm and elecfans JST drawing (secondary); JST PDF not readable (OPEN (A-076): the model is 5.5 (INNER_H 8.6, 0.5 air), so this passes; the value is a listing, not a datasheet. Confirm the exact part (element14 8.0 mm B2B listing)) |
| 15 | Interference lid vs board+parts | 0.000 mm3 | 0 (contact allowed) | **OPEN** | boolean intersect of the CadQuery solids (OPEN: evaluated at the model height of J2 (5.5, SECONDARY); a height above the 5.5 budget is tested by the mutation test) |
| 16 | Interference tray vs board+parts | 0.000 mm3 | 0 (contact allowed) | **PASS** | boolean intersect of the CadQuery solids |
| 17 | Interference plug vs board+parts | 0.000 mm3 | 0 (contact allowed) | **PASS** | boolean intersect of the CadQuery solids |
| 18 | Interference tray vs cell | 0.000 mm3 | 0 (contact allowed) | **PASS** | boolean intersect of the CadQuery solids |
| 19 | Interference lid vs cell | 0.000 mm3 | 0 (contact allowed) | **PASS** | boolean intersect of the CadQuery solids |
| 20 | Interference plug vs tray | 0.000 mm3 | 0 (contact allowed) | **PASS** | boolean intersect of the CadQuery solids |
| 21 | Antenna overhang rect to cell cavity (Emil's 26.2 method) | 26.2 mm | >= 15 | **PASS** | layout-4P2 check_layout.py rect_gap(ant_tip, cell) |
| 22 | Antenna tip line to cell cavity (my 28.4 method) | 27.7 mm | >= 15 | **PASS** | jlc_prep/README s.1 item 2 |
| 23 | Antenna corner (33.5, 4.5) air to the rounded cavity corner | 1.00 mm | >= 1.0 (same air as the top wall) | **PASS** | params_v3 rr_dist, FILLET_INNER 1.5 (slice 4) |
| 24 | Nearest brass insert to antenna (Q9) | 22.2 mm | >= 15 | **PASS** | BOSS_XY, insert hole 3.2 |
| 25 | PETG top wall over the antenna | 1.60 mm wall, 1.0 mm air to antenna tip (ASSUMED) | no thick wall over the antenna (standards s.7): RF effect checked | **OPEN** | params_v3 WALL, INNER_Y1; standards s.7; P1S/PETG review (Arsany answer 2026-11-10) (OPEN: RF effect not measured. A-084: risk accepted for the demo with the 1.6 mm compact shell; RF check on a Prototype 1 print before any pilot batch) |
| 26 | Wall: Rim land left/top/bottom | 1.60 mm | >= 1.2 (role rule) | **PASS** | params_v3 |
| 27 | Wall: Rim land right (USB side) | 2.40 mm | >= 1.2 (role rule) | **PASS** | params_v3 |
| 28 | Wall: Tray floor | 1.20 mm | >= 1.2 (role rule) | **PASS** | params_v3 |
| 29 | Wall: Corner wall, min (cavity to skin) | 1.23 mm | >= 1.2 (role rule) | **PASS** | params_v3 |
| 30 | Wall: Lid under counterbore | 1.80 mm | >= 1.2 (role rule) | **PASS** | params_v3 |
| 31 | Wall: USB pocket remaining wall | 1.20 mm | >= 1.2 (role rule) | **PASS** | params_v3 |
| 32 | Wall: Light collar wall | 1.20 mm | >= 1.2 (role rule) | **PASS** | params_v3 |
| 33 | Wall: Vent cup wall | 1.20 mm | >= 1.2 (role rule) | **PASS** | params_v3 |
| 34 | Wall: Pinhole tube wall | 1.20 mm | >= 1.2 (role rule) | **PASS** | params_v3 |
| 35 | Wall: Boss wall around insert | 1.60 mm | >= 1.2 (role rule) | **PASS** | params_v3 |
| 36 | PETG min feature: vent slot width | 1.00 mm | >= 0.8 (2 lines) | **OPEN** | params_v3 PETG_MIN_FEATURE [ASSUMED 0.8] (OPEN: the 0.8 mm floor is ASSUMED (no sourced PETG limit), so a pass against it is not a pass) |
| 37 | PETG min feature: pinhole d | 1.80 mm | >= 0.8 (2 lines) | **OPEN** | params_v3 PETG_MIN_FEATURE [ASSUMED 0.8] (OPEN: the 0.8 mm floor is ASSUMED (no sourced PETG limit), so a pass against it is not a pass) |
| 38 | PETG min feature: light window d | 3.60 mm | >= 0.8 (2 lines) | **OPEN** | params_v3 PETG_MIN_FEATURE [ASSUMED 0.8] (OPEN: the 0.8 mm floor is ASSUMED (no sourced PETG limit), so a pass against it is not a pass) |
| 39 | PETG min feature: lid screw clearance hole | 2.40 mm | >= 0.8 (2 lines) | **OPEN** | params_v3 PETG_MIN_FEATURE [ASSUMED 0.8] (OPEN: the 0.8 mm floor is ASSUMED (no sourced PETG limit), so a pass against it is not a pass) |
| 40 | PETG min feature: plug wall (tail tunnel) | 1.60 mm | >= 0.8 (2 lines) | **OPEN** | params_v3 PETG_MIN_FEATURE [ASSUMED 0.8] (OPEN: the 0.8 mm floor is ASSUMED (no sourced PETG limit), so a pass against it is not a pass) |
| 41 | Seal tunnel clearance per side (thickness) | 0.30 mm | >= 0.30 (PETG/FDM; sealant fills the rest) | **OPEN** | params_v3 TUNNEL_H 2.2 [ASSUMED 0.3] (OPEN: the 0.3 mm clearance is ASSUMED, so a pass against it is not a pass) |
| 42 | Seal tunnel clearance per side (width) | 0.30 mm | >= 0.30 [ASSUMED] | **OPEN** | params_v3 TUNNEL_W 12.6; 0.3 per side as in the thickness row (OPEN: the 0.3 mm clearance is ASSUMED (same value as the thickness row), so a pass against it is not a pass) |
| 43 | PETG insert boss wall (round the 3.2 hole) | 1.60 mm | >= 1.6 (PETG target; floor 1.2) | **OPEN** | params_v3 BOSS_D 6.4; insert datasheet still to check (OPEN: 1.6 mm is this PR's own PETG target (PETG_BOSS_WALL), not a sourced limit; the insert datasheet is not read, so a pass against it is not a pass) |
| 44 | Boss to outside surface (skin) | 1.20 mm | >= 1.2 | **PASS** | params_v3 BOSS_XY, outer rounded outline (outer_dist) |
| 45 | Boss to board outline (plan gap, nearest boss) | 1.10 mm | >= 1.0 [ASSUMED] | **OPEN** | params_v3 BOSS_XY vs board outline (board_facts), BOSS_D / 2 (OPEN: the 1.0 mm threshold is ASSUMED (insertion slop and FDM spread), so a pass against it is not a pass. Found at 0.34 mm before the slice 4 fix) |
| 46 | Boss below the cell cavity (bottom row, y gap) | 0.20 mm | >= 0.2 (no overlap; tray vs cell boolean row also checks) | **PASS** | params_v3 BOSS_XY vs CELL_BAY_CAVITY y -42.0 |
| 47 | Lid plate above the film counterbore | 1.80 mm | >= 1.2 | **PASS** | params_v3 LID_T 2.4 |
| 48 | Screw torque limit | 0.25 N m (ASSUMED) | insert datasheet governs; bench check | **OPEN** | ASSUMED: no insert datasheet read; torque is for the bench, see README (NOT CHECKED: an assumed torque cannot pass a check) |
| 49 | P1S volume: tray | 97.3 x 56.9 x 9.8 | <= 256^3 | **PASS** | standards s.1 |
| 50 | P1S volume: lid | 97.3 x 56.9 x 8.0 | <= 256^3 | **PASS** | standards s.1 |
| 51 | P1S volume: plug | 13.4 x 1.6 x 8.6 | <= 256^3 | **PASS** | standards s.1 |
| 52 | STL watertight: tray | True | True | **PASS** | trimesh |
| 53 | Max bridge/overhang span, print orientation: tray | 0.9 mm (2644 faces) | <= 10 mm reach from bed contact (P1S bridges; no steep overhangs) | **PASS** | trimesh, faces with normal z < -0.7 above the bed, reach to bed-contact vertices (USB window top 9.6; lid counterbore 6.4) |
| 54 | STL watertight: lid | True | True | **PASS** | trimesh |
| 55 | Max bridge/overhang span, print orientation: lid | 1.4 mm (2556 faces) | <= 10 mm reach from bed contact (P1S bridges; no steep overhangs) | **PASS** | trimesh, faces with normal z < -0.7 above the bed, reach to bed-contact vertices (USB window top 9.6; lid counterbore 6.4) |
| 56 | STL watertight: plug | True | True | **PASS** | trimesh |
| 57 | Max bridge/overhang span, print orientation: plug | 0.0 mm (0 faces) | <= 10 mm reach from bed contact (P1S bridges; no steep overhangs) | **PASS** | trimesh, faces with normal z < -0.7 above the bed, reach to bed-contact vertices |
| 58 | Model heights equal their cited source (7 parts) | 7 of 7 equal | model value = cited value for every part | **OPEN** | params_v3 H_CITED vs H_BY_REF; standards s.7 (never invent a component dimension) (OPEN: U5, U6, SW1-3 cite distributor listings (SECONDARY), the PDFs were not read) |
| 59 | J1 USB-C height (flat / edge-mount, A-087) | flat 3.30 (ASSUMED): 2.70 mm to lid underside (inner 8.6) | >= 0.5 mm to lid; height of C165948 confirmed by a second reader | **OPEN** | params_v3 H_BY_REF['J1'], H_SRC J1; A-087 (flat approved 2026-11-13) (OPEN: height ASSUMED 3.30. C165948 is already the flat part (no pick needed); 3.26 mm read once by Emil in PR #95 docs/j1-usbc-flat.md (branch agent/pcb/gerber-pkg), second read by Ines pending; never PASS before that) |

40 PASS, 0 FAIL, 19 OPEN (tail 14 mm variant)

Tail variant: 20 mm (A-071 open)

| # | Check | Value | Need | Result | Source |
|---|---|---|---|---|---|
| 1 | Tail variant 20 mm: electrode copper beyond outer bottom face | 20.00 mm (copper tip y -69.80) | = 20.0 mm (variant) | **PASS** | params_v3 TAIL_VARIANTS; copper from board E1 pad (board_facts.electrode_span), tip margin 4.0 from DXF |
| 2 | Board tail in DXF (input/) matches the variant | DXF 25.00 mm vs variant 31.80 mm (+6.80) | = variant tail | **OPEN** | board DXF = #73; a longer tail for the 20 mm variant is a board outline change for Emil (not in repo) (OPEN: board outline change needed for this variant, Arsany A-071 decides) |
| 3 | Interference tail (20 variant) vs tray and seal plug | 0.000 mm3 | 0 (contact allowed) | **PASS** | boolean intersect: tail solid vs tray and tail_plug |
| 4 | Right-most part (J1 shell) to right wall (X) | 0.30 mm (board edge 0.80) | >= 0.30 (FDM + PCB +-0.2) | **PASS** | params_v3 INNER_X1, DXF outline |
| 5 | Antenna tip to top wall (Y) | 1.00 mm | >= 1.0 [ASSUMED] | **OPEN** | DXF MODULE_U1 (overhang derived by Emil); Q10 detuning open (OPEN: the 1.0 mm threshold is ASSUMED, so a pass against it is not a pass (Arsany rule)) |
| 6 | Tail width vs tunnel (per side) | 0.30 mm | >= 0.30 | **PASS** | DXF tail 12.0; JLC outline +-0.2 (layout-brief s.5) |
| 7 | Tail thickness vs tunnel height (per side) | 0.30 mm | >= 0.15 (JLC 1.6 +-10 % = 0.16) | **PASS** | layout-brief s.5 thickness tolerance |
| 8 | Cell cavity (X x Y) inside the inner box | 53.0 x 35.1 | = bay.dims A_eemb603449 (53.0 x 35.1) | **PASS** | pcb-enclosure-bay.md; bay.py |
| 9 | Cell 51 x 34.5 x 6.3 spare in cavity | L 2.0 / W 0.6 / H 0.9 | L>=2.0 W>=0.6 H>=0.9 | **PASS** | bay.dims |
| 10 | Cell cavity height vs inner height (cell only; no assumed part height in this row) | 7.2 vs 7.6 | cavity <= inner | **PASS** | bay.dims bay_h 7.2; INNER_H is a fixed design value |
| 11 | Board to cell cavity gap (X) | 5.0 mm | = 5.0 (gen_pcb CELL_GAP) | **PASS** | DXF CELL_BAY_CAVITY |
| 12 | Tallest part to lid underside (derived from assumed heights) | 0.50 mm (J2 4.5, CONFLICT) | >= 0.5 (+0.7 mm gasket thickness not counted) | **OPEN** | H_BY_REF; J2 height needs a datasheet value (OPEN, A-076) (OPEN: the number rests on J2 4.5, which is ASSUMED and conflicts with the 5.5 distributor value (row 14)) |
| 13 | Heights with a datasheet page in the model | 1 of 17 DATASHEET (U1); 5 SECONDARY, 1 CONFLICT, 10 ASSUMED | every height cites a datasheet; the rest are listed as SECONDARY or ASSUMED | **OPEN** | params_v3 H_SRC; a distributor listing is not a datasheet citation (standards s.7) (OPEN: sourcing is incomplete; see H_SRC for each part) |
| 14 | J2 at the distributor value 5.5 mm (not used in the model) | -0.50 mm to lid underside (needs INNER_H >= 8.6) | >= 0.5 | **OPEN** | JLCPCB Z-height 5.5 mm and elecfans JST drawing (secondary); JST PDF not readable (OPEN: model keeps 4.5 ASSUMED. If the datasheet says 5.5, INNER_H grows by 1.0 mm (box 98.1 x 57.7 x 12.6). Arsany/Emil decide) |
| 15 | Interference lid vs board+parts | 0.000 mm3 | 0 (contact allowed) | **OPEN** | boolean intersect of the CadQuery solids (OPEN: evaluated at the model height of J2 (4.5, CONFLICT); the sourced 5.5 is tested by the mutation test) |
| 16 | Interference tray vs board+parts | 0.000 mm3 | 0 (contact allowed) | **PASS** | boolean intersect of the CadQuery solids |
| 17 | Interference plug vs board+parts | 0.000 mm3 | 0 (contact allowed) | **PASS** | boolean intersect of the CadQuery solids |
| 18 | Interference tray vs cell | 0.000 mm3 | 0 (contact allowed) | **PASS** | boolean intersect of the CadQuery solids |
| 19 | Interference lid vs cell | 0.000 mm3 | 0 (contact allowed) | **PASS** | boolean intersect of the CadQuery solids |
| 20 | Interference plug vs tray | 0.000 mm3 | 0 (contact allowed) | **PASS** | boolean intersect of the CadQuery solids |
| 21 | Antenna overhang rect to cell cavity (Emil's 26.2 method) | 26.2 mm | >= 15 | **PASS** | layout-4P2 check_layout.py rect_gap(ant_tip, cell) |
| 22 | Antenna tip line to cell cavity (my 28.4 method) | 27.7 mm | >= 15 | **PASS** | jlc_prep/README s.1 item 2 |
| 23 | Nearest brass insert to antenna (Q9) | 21.2 mm | >= 15 | **PASS** | BOSS_XY, insert hole 3.2 |
| 24 | PETG top wall over the antenna | 2.40 mm wall, 1.0 mm air to antenna tip (ASSUMED) | no thick wall over the antenna (standards s.7): RF effect checked | **OPEN** | params_v3 WALL, INNER_Y1; standards s.7; P1S/PETG review (Arsany answer 2026-11-10) (OPEN: effect on the antenna not measured. Options: RF check on a Prototype 1 print, or a thinner wall over the antenna. Decide before the lid is locked) |
| 25 | Wall: Side wall (rim land) | 2.40 mm | >= 1.2 (role rule) | **PASS** | params_v3 |
| 26 | Wall: Tray floor | 1.60 mm | >= 1.2 (role rule) | **PASS** | params_v3 |
| 27 | Wall: Lid under counterbore | 1.80 mm | >= 1.2 (role rule) | **PASS** | params_v3 |
| 28 | Wall: USB pocket remaining wall | 1.20 mm | >= 1.2 (role rule) | **PASS** | params_v3 |
| 29 | Wall: Light collar wall | 1.20 mm | >= 1.2 (role rule) | **PASS** | params_v3 |
| 30 | Wall: Vent cup wall | 1.20 mm | >= 1.2 (role rule) | **PASS** | params_v3 |
| 31 | Wall: Pinhole tube wall | 1.20 mm | >= 1.2 (role rule) | **PASS** | params_v3 |
| 32 | Wall: Boss wall around insert | 1.60 mm | >= 1.2 (role rule) | **PASS** | params_v3 |
| 33 | PETG min feature: vent slot width | 1.00 mm | >= 0.8 (2 lines) | **OPEN** | params_v3 PETG_MIN_FEATURE [ASSUMED 0.8] (OPEN: the 0.8 mm floor is ASSUMED (no sourced PETG limit), so a pass against it is not a pass) |
| 34 | PETG min feature: pinhole d | 1.80 mm | >= 0.8 (2 lines) | **OPEN** | params_v3 PETG_MIN_FEATURE [ASSUMED 0.8] (OPEN: the 0.8 mm floor is ASSUMED (no sourced PETG limit), so a pass against it is not a pass) |
| 35 | PETG min feature: light window d | 3.60 mm | >= 0.8 (2 lines) | **OPEN** | params_v3 PETG_MIN_FEATURE [ASSUMED 0.8] (OPEN: the 0.8 mm floor is ASSUMED (no sourced PETG limit), so a pass against it is not a pass) |
| 36 | PETG min feature: lid screw clearance hole | 2.40 mm | >= 0.8 (2 lines) | **OPEN** | params_v3 PETG_MIN_FEATURE [ASSUMED 0.8] (OPEN: the 0.8 mm floor is ASSUMED (no sourced PETG limit), so a pass against it is not a pass) |
| 37 | PETG min feature: plug wall (tail tunnel) | 2.40 mm | >= 0.8 (2 lines) | **OPEN** | params_v3 PETG_MIN_FEATURE [ASSUMED 0.8] (OPEN: the 0.8 mm floor is ASSUMED (no sourced PETG limit), so a pass against it is not a pass) |
| 38 | Seal tunnel clearance per side (thickness) | 0.30 mm | >= 0.30 (PETG/FDM; sealant fills the rest) | **OPEN** | params_v3 TUNNEL_H 2.2 [ASSUMED 0.3] (OPEN: the 0.3 mm clearance is ASSUMED, so a pass against it is not a pass) |
| 39 | Seal tunnel clearance per side (width) | 0.30 mm | >= 0.30 [ASSUMED] | **OPEN** | params_v3 TUNNEL_W 12.6; 0.3 per side as in the thickness row (OPEN: the 0.3 mm clearance is ASSUMED (same value as the thickness row), so a pass against it is not a pass) |
| 40 | PETG insert boss wall (round the 3.2 hole) | 1.60 mm | >= 1.6 (PETG target; floor 1.2) | **OPEN** | params_v3 BOSS_D 6.4; insert datasheet still to check (OPEN: 1.6 mm is this PR's own PETG target (PETG_BOSS_WALL), not a sourced limit; the insert datasheet is not read, so a pass against it is not a pass) |
| 41 | Boss to outside surface (skin) | 1.20 mm | >= 1.2 | **PASS** | params_v3 BOSS_XY, OUT_Y0/OUT_Y1 |
| 42 | Boss below the cell cavity (bottom row, y gap) | 0.20 mm | >= 0.2 (no overlap; tray vs cell boolean row also checks) | **PASS** | params_v3 BOSS_XY vs CELL_BAY_CAVITY y -42.0 |
| 43 | Lid plate above the film counterbore | 1.80 mm | >= 1.2 | **PASS** | params_v3 LID_T 2.4 |
| 44 | Screw torque limit | 0.25 N m (ASSUMED) | insert datasheet governs; bench check | **OPEN** | ASSUMED: no insert datasheet read; torque is for the bench, see README (NOT CHECKED: an assumed torque cannot pass a check) |
| 45 | P1S volume: tray | 98.1 x 57.7 x 9.2 | <= 256^3 | **PASS** | standards s.1 |
| 46 | P1S volume: lid | 98.1 x 57.7 x 7.0 | <= 256^3 | **PASS** | standards s.1 |
| 47 | P1S volume: plug | 13.4 x 2.4 x 7.6 | <= 256^3 | **PASS** | standards s.1 |
| 48 | STL watertight: tray | True | True | **PASS** | trimesh |
| 49 | Max bridge/overhang span, print orientation: tray | 9.6 mm (2 faces) | <= 10 mm (P1S bridges; no steep overhangs) | **PASS** | trimesh, faces with normal z < -0.7 above the bed (USB window top 9.6; lid counterbore 6.4) |
| 50 | STL watertight: lid | True | True | **PASS** | trimesh |
| 51 | Max bridge/overhang span, print orientation: lid | 6.4 mm (252 faces) | <= 10 mm (P1S bridges; no steep overhangs) | **PASS** | trimesh, faces with normal z < -0.7 above the bed (USB window top 9.6; lid counterbore 6.4) |
| 52 | STL watertight: plug | True | True | **PASS** | trimesh |
| 53 | Max bridge/overhang span, print orientation: plug | 0.0 mm (0 faces) | <= 10 mm (P1S bridges; no steep overhangs) | **PASS** | trimesh, faces with normal z < -0.7 above the bed |
| 54 | Model heights equal their cited source (6 parts) | 6 of 6 equal | model value = cited value for every part | **OPEN** | params_v3 H_CITED vs H_BY_REF; standards s.7 (never invent a component dimension) (OPEN: U5, U6, SW1-3 cite distributor listings (SECONDARY), the PDFs were not read) |
| 55 | J1 USB-C height, flat vs upright | flat 3.30 (ASSUMED): 1.70 mm to lid; upright 11.94 +-0.25 (OPEN): -6.94 mm | >= 0.5 (orientation not decided) | **OPEN** | TYPE-C-31-M-12 datasheet, upright male (brief value, PDF not read here); params_v3 H_SRC J1_UPRIGHT (OPEN: orientation is decision A-087 (Arsany). Flat is ASSUMED; upright does not fit the 7.6 mm inner box. No value is chosen) |

37 PASS, 0 FAIL, 18 OPEN (tail 20 mm variant)

Tail variant: 14 mm (A-071 open)

| # | Check | Value | Need | Result | Source |
|---|---|---|---|---|---|
| 1 | Tail variant 14 mm: electrode copper beyond outer bottom face | 14.00 mm (copper tip y -63.80) | = 14.0 mm (variant) | **PASS** | params_v3 TAIL_VARIANTS; copper from board E1 pad (board_facts.electrode_span), tip margin 4.0 from DXF |
| 2 | Board tail in DXF (input/) matches the variant | DXF 25.00 mm vs variant 25.80 mm (+0.80) | = variant tail | **OPEN** | board DXF = #73; a longer tail for the 20 mm variant is a board outline change for Emil (not in repo) (OPEN: board outline change needed for this variant, Arsany A-071 decides) |
| 3 | Interference tail (14 variant) vs tray and seal plug | 0.000 mm3 | 0 (contact allowed) | **PASS** | boolean intersect: tail solid vs tray and tail_plug |
| 4 | Right-most part (J1 shell) to right wall (X) | 0.30 mm (board edge 0.80) | >= 0.30 (FDM + PCB +-0.2) | **PASS** | params_v3 INNER_X1, DXF outline |
| 5 | Antenna tip to top wall (Y) | 1.00 mm | >= 1.0 [ASSUMED] | **PASS** | DXF MODULE_U1 (overhang derived by Emil); Q10 detuning open |
| 6 | Tail width vs tunnel (per side) | 0.30 mm | >= 0.30 | **PASS** | DXF tail 12.0; JLC outline +-0.2 (layout-brief s.5) |
| 7 | Tail thickness vs tunnel height (per side) | 0.30 mm | >= 0.15 (JLC 1.6 +-10 % = 0.16) | **PASS** | layout-brief s.5 thickness tolerance |
| 8 | Cell cavity (X x Y) inside the inner box | 53.0 x 35.1 | = bay.dims A_eemb603449 (53.0 x 35.1) | **PASS** | pcb-enclosure-bay.md; bay.py |
| 9 | Cell 51 x 34.5 x 6.3 spare in cavity | L 2.0 / W 0.6 / H 0.9 | L>=2.0 W>=0.6 H>=0.9 | **PASS** | bay.dims |
| 10 | Cell cavity height vs inner height (cell only; no assumed part height in this row) | 7.2 vs 7.6 | cavity <= inner | **PASS** | bay.dims bay_h 7.2; INNER_H is a fixed design value |
| 11 | Board to cell cavity gap (X) | 5.0 mm | = 5.0 (gen_pcb CELL_GAP) | **PASS** | DXF CELL_BAY_CAVITY |
| 12 | Tallest part to lid underside (derived from assumed heights) | 0.50 mm (J2, 4.5 ASSUMED) | >= 0.5 (+0.7 mm gasket thickness not counted) | **PASS** | H_BY_REF [ASSUMED]; J2 height needs a datasheet value (Needs Arsany) |
| 13 | Heights with a datasheet page in the model | 1 of 17 (U1 only) | every height in the fit check cites a datasheet, else ASSUMED | **PASS** | params_v3 H_SRC; the other heights are SECONDARY (distributors) or ASSUMED, listed below |
| 14 | J2 at the distributor value 5.5 mm (not used in the model) | -0.50 mm to lid underside (needs INNER_H >= 8.6) | >= 0.5 | **OPEN** | JLCPCB Z-height 5.5 mm and elecfans JST drawing (secondary); JST PDF not readable (OPEN: model keeps 4.5 ASSUMED. If the datasheet says 5.5, INNER_H grows by 1.0 mm (box 98.1 x 57.7 x 12.6). Arsany/Emil decide) |
| 15 | Interference lid vs board+parts | 0.000 mm3 | 0 (contact allowed) | **PASS** | boolean intersect of the CadQuery solids |
| 16 | Interference tray vs board+parts | 0.000 mm3 | 0 (contact allowed) | **PASS** | boolean intersect of the CadQuery solids |
| 17 | Interference plug vs board+parts | 0.000 mm3 | 0 (contact allowed) | **PASS** | boolean intersect of the CadQuery solids |
| 18 | Interference tray vs cell | 0.000 mm3 | 0 (contact allowed) | **PASS** | boolean intersect of the CadQuery solids |
| 19 | Interference lid vs cell | 0.000 mm3 | 0 (contact allowed) | **PASS** | boolean intersect of the CadQuery solids |
| 20 | Interference plug vs tray | 0.000 mm3 | 0 (contact allowed) | **PASS** | boolean intersect of the CadQuery solids |
| 21 | Antenna overhang rect to cell cavity (Emil's 26.2 method) | 26.2 mm | >= 15 | **PASS** | layout-4P2 check_layout.py rect_gap(ant_tip, cell) |
| 22 | Antenna tip line to cell cavity (my 28.4 method) | 27.7 mm | >= 15 | **PASS** | jlc_prep/README s.1 item 2 |
| 23 | Nearest brass insert to antenna (Q9) | 21.2 mm | >= 15 | **PASS** | BOSS_XY, insert hole 3.2 |
| 24 | Wall: Side wall (rim land) | 2.40 mm | >= 1.2 (role rule) | **PASS** | params_v3 |
| 25 | Wall: Tray floor | 1.60 mm | >= 1.2 (role rule) | **PASS** | params_v3 |
| 26 | Wall: Lid under counterbore | 1.80 mm | >= 1.2 (role rule) | **PASS** | params_v3 |
| 27 | Wall: USB pocket remaining wall | 1.20 mm | >= 1.2 (role rule) | **PASS** | params_v3 |
| 28 | Wall: Light collar wall | 1.20 mm | >= 1.2 (role rule) | **PASS** | params_v3 |
| 29 | Wall: Vent cup wall | 1.20 mm | >= 1.2 (role rule) | **PASS** | params_v3 |
| 30 | Wall: Pinhole tube wall | 1.20 mm | >= 1.2 (role rule) | **PASS** | params_v3 |
| 31 | Wall: Boss wall around insert | 1.60 mm | >= 1.2 (role rule) | **PASS** | params_v3 |
| 32 | PETG min feature: vent slot width | 1.00 mm | >= 0.8 (2 lines) | **PASS** | params_v3 PETG_MIN_FEATURE [ASSUMED 0.8] |
| 33 | PETG min feature: pinhole d | 1.80 mm | >= 0.8 (2 lines) | **PASS** | params_v3 PETG_MIN_FEATURE [ASSUMED 0.8] |
| 34 | PETG min feature: light window d | 3.60 mm | >= 0.8 (2 lines) | **PASS** | params_v3 PETG_MIN_FEATURE [ASSUMED 0.8] |
| 35 | PETG min feature: lid screw clearance hole | 2.40 mm | >= 0.8 (2 lines) | **PASS** | params_v3 PETG_MIN_FEATURE [ASSUMED 0.8] |
| 36 | PETG min feature: plug wall (tail tunnel) | 2.40 mm | >= 0.8 (2 lines) | **PASS** | params_v3 PETG_MIN_FEATURE [ASSUMED 0.8] |
| 37 | Seal tunnel clearance per side (thickness) | 0.30 mm | >= 0.30 (PETG/FDM; sealant fills the rest) | **PASS** | params_v3 TUNNEL_H 2.2 [ASSUMED 0.3] |
| 38 | Seal tunnel clearance per side (width) | 0.30 mm | >= 0.30 | **PASS** | params_v3 TUNNEL_W 12.6 |
| 39 | PETG insert boss wall (round the 3.2 hole) | 1.60 mm | >= 1.6 (PETG target; floor 1.2) | **PASS** | params_v3 BOSS_D 6.4; insert datasheet still to check |
| 40 | Boss to outside surface (skin) | 1.20 mm | >= 1.2 | **PASS** | params_v3 BOSS_XY, OUT_Y0/OUT_Y1 |
| 41 | Boss below the cell cavity (bottom row, y gap) | 0.20 mm | >= 0.2 (no overlap; tray vs cell boolean row also checks) | **PASS** | params_v3 BOSS_XY vs CELL_BAY_CAVITY y -42.0 |
| 42 | Lid plate above the film counterbore | 1.80 mm | >= 1.2 | **PASS** | params_v3 LID_T 2.4 |
| 43 | Screw torque limit (informational, not a fit check) | 0.25 N m | insert datasheet governs | **PASS** | ASSUMED; torque is for the bench, see README |
| 44 | P1S volume: tray | 98.1 x 57.7 x 9.2 | <= 256^3 | **PASS** | standards s.1 |
| 45 | P1S volume: lid | 98.1 x 57.7 x 7.0 | <= 256^3 | **PASS** | standards s.1 |
| 46 | P1S volume: plug | 13.4 x 2.4 x 7.6 | <= 256^3 | **PASS** | standards s.1 |
| 47 | STL watertight: tray | True | True | **PASS** | trimesh |
| 48 | Max bridge/overhang span, print orientation: tray | 9.6 mm (2 faces) | <= 10 mm (P1S bridges; no steep overhangs) | **PASS** | trimesh, faces with normal z < -0.7 above the bed (USB window top 9.6; lid counterbore 6.4) |
| 49 | STL watertight: lid | True | True | **PASS** | trimesh |
| 50 | Max bridge/overhang span, print orientation: lid | 6.4 mm (252 faces) | <= 10 mm (P1S bridges; no steep overhangs) | **PASS** | trimesh, faces with normal z < -0.7 above the bed (USB window top 9.6; lid counterbore 6.4) |
| 51 | STL watertight: plug | True | True | **PASS** | trimesh |
| 52 | Max bridge/overhang span, print orientation: plug | 0.0 mm (0 faces) | <= 10 mm (P1S bridges; no steep overhangs) | **PASS** | trimesh, faces with normal z < -0.7 above the bed |

50 PASS, 0 FAIL, 2 OPEN (tail 14 mm variant)

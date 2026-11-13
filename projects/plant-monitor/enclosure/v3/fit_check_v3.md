| # | Check | Value | Need | Result | Source |
|---|---|---|---|---|---|
| 1 | Right-most part (J1 shell) to right wall (X) | 0.30 mm (board edge 0.80) | >= 0.30 (FDM + PCB +-0.2) | **PASS** | params_v3 INNER_X1, DXF outline |
| 2 | Antenna tip to top wall (Y) | 1.00 mm | >= 1.0 [ASSUMED] | **PASS** | DXF MODULE_U1 (overhang derived by Emil); Q10 detuning open |
| 3 | Tail width vs tunnel (per side) | 0.30 mm | >= 0.30 | **PASS** | DXF tail 12.0; JLC outline +-0.2 (layout-brief s.5) |
| 4 | Tail thickness vs tunnel height (per side) | 0.30 mm | >= 0.15 (JLC 1.6 +-10 % = 0.16) | **PASS** | layout-brief s.5 thickness tolerance |
| 5 | Cell cavity (X x Y) inside the inner box | 53.0 x 35.1 | = bay.dims A_eemb603449 (53.0 x 35.1) | **PASS** | pcb-enclosure-bay.md; bay.py |
| 6 | Cell 51 x 34.5 x 6.3 spare in cavity | L 2.0 / W 0.6 / H 0.9 | L>=2.0 W>=0.6 H>=0.9 | **PASS** | bay.dims |
| 7 | Cell cavity height vs inner height (cell only; no assumed part height in this row) | 7.2 vs 7.6 | cavity <= inner | **PASS** | bay.dims bay_h 7.2; INNER_H is a fixed design value |
| 8 | Board to cell cavity gap (X) | 5.0 mm | = 5.0 (gen_pcb CELL_GAP) | **PASS** | DXF CELL_BAY_CAVITY |
| 9 | Tallest part to lid underside (derived from assumed heights) | 0.50 mm (J2, 4.5 ASSUMED) | >= 0.5 (+0.7 mm gasket thickness not counted) | **PASS** | H_BY_REF [ASSUMED]; J2 height needs a datasheet value (Needs Arsany) |
| 10 | Interference lid vs board+parts | 0.000 mm3 | 0 (contact allowed) | **PASS** | boolean intersect of the CadQuery solids |
| 11 | Interference tray vs board+parts | 0.000 mm3 | 0 (contact allowed) | **PASS** | boolean intersect of the CadQuery solids |
| 12 | Interference plug vs board+parts | 0.000 mm3 | 0 (contact allowed) | **PASS** | boolean intersect of the CadQuery solids |
| 13 | Interference tray vs cell | 0.000 mm3 | 0 (contact allowed) | **PASS** | boolean intersect of the CadQuery solids |
| 14 | Interference lid vs cell | 0.000 mm3 | 0 (contact allowed) | **PASS** | boolean intersect of the CadQuery solids |
| 15 | Interference plug vs tray | 0.000 mm3 | 0 (contact allowed) | **PASS** | boolean intersect of the CadQuery solids |
| 16 | Antenna overhang rect to cell cavity (Emil's 26.2 method) | 26.2 mm | >= 15 | **PASS** | layout-4P2 check_layout.py rect_gap(ant_tip, cell) |
| 17 | Antenna tip line to cell cavity (my 28.4 method) | 27.7 mm | >= 15 | **PASS** | jlc_prep/README s.1 item 2 |
| 18 | Nearest brass insert to antenna (Q9) | 21.2 mm | >= 15 | **PASS** | BOSS_XY, insert hole 3.2 |
| 19 | Wall: Side wall (rim land) | 2.40 mm | >= 1.2 (role rule) | **PASS** | params_v3 |
| 20 | Wall: Tray floor | 1.60 mm | >= 1.2 (role rule) | **PASS** | params_v3 |
| 21 | Wall: Lid under counterbore | 1.80 mm | >= 1.2 (role rule) | **PASS** | params_v3 |
| 22 | Wall: USB pocket remaining wall | 1.20 mm | >= 1.2 (role rule) | **PASS** | params_v3 |
| 23 | Wall: Light collar wall | 1.20 mm | >= 1.2 (role rule) | **PASS** | params_v3 |
| 24 | Wall: Vent cup wall | 1.20 mm | >= 1.2 (role rule) | **PASS** | params_v3 |
| 25 | Wall: Pinhole tube wall | 1.20 mm | >= 1.2 (role rule) | **PASS** | params_v3 |
| 26 | Wall: Boss wall around insert | 1.60 mm | >= 1.2 (role rule) | **PASS** | params_v3 |
| 27 | PETG min feature: vent slot width | 1.00 mm | >= 0.8 (2 lines) | **PASS** | params_v3 PETG_MIN_FEATURE [ASSUMED 0.8] |
| 28 | PETG min feature: pinhole d | 1.80 mm | >= 0.8 (2 lines) | **PASS** | params_v3 PETG_MIN_FEATURE [ASSUMED 0.8] |
| 29 | PETG min feature: light window d | 3.60 mm | >= 0.8 (2 lines) | **PASS** | params_v3 PETG_MIN_FEATURE [ASSUMED 0.8] |
| 30 | PETG min feature: lid screw clearance hole | 2.40 mm | >= 0.8 (2 lines) | **PASS** | params_v3 PETG_MIN_FEATURE [ASSUMED 0.8] |
| 31 | PETG min feature: plug wall (tail tunnel) | 2.40 mm | >= 0.8 (2 lines) | **PASS** | params_v3 PETG_MIN_FEATURE [ASSUMED 0.8] |
| 32 | Seal tunnel clearance per side (thickness) | 0.30 mm | >= 0.30 (PETG/FDM; sealant fills the rest) | **PASS** | params_v3 TUNNEL_H 2.2 [ASSUMED 0.3] |
| 33 | Seal tunnel clearance per side (width) | 0.30 mm | >= 0.30 | **PASS** | params_v3 TUNNEL_W 12.6 |
| 34 | PETG insert boss wall (round the 3.2 hole) | 1.60 mm | >= 1.6 (PETG target; floor 1.2) | **PASS** | params_v3 BOSS_D 6.4; insert datasheet still to check |
| 35 | Boss to outside surface (skin) | 1.20 mm | >= 1.2 | **PASS** | params_v3 BOSS_XY, OUT_Y0/OUT_Y1 |
| 36 | Boss below the cell cavity (bottom row, y gap) | 0.20 mm | >= 0.2 (no overlap; tray vs cell boolean row also checks) | **PASS** | params_v3 BOSS_XY vs CELL_BAY_CAVITY y -42.0 |
| 37 | Lid plate above the film counterbore | 1.80 mm | >= 1.2 | **PASS** | params_v3 LID_T 2.4 |
| 38 | Screw torque limit (informational, not a fit check) | 0.25 N m | insert datasheet governs | **PASS** | ASSUMED; torque is for the bench, see README |
| 39 | P1S volume: tray | 98.1 x 57.7 x 9.2 | <= 256^3 | **PASS** | standards s.1 |
| 40 | P1S volume: lid | 98.1 x 57.7 x 7.0 | <= 256^3 | **PASS** | standards s.1 |
| 41 | P1S volume: plug | 13.4 x 2.4 x 7.6 | <= 256^3 | **PASS** | standards s.1 |
| 42 | STL watertight: tray | True | True | **PASS** | trimesh |
| 43 | Max bridge/overhang span, print orientation: tray | 9.6 mm (2 faces) | <= 10 mm (P1S bridges; no steep overhangs) | **PASS** | trimesh, faces with normal z < -0.7 above the bed (USB window top 9.6; lid counterbore 6.4) |
| 44 | STL watertight: lid | True | True | **PASS** | trimesh |
| 45 | Max bridge/overhang span, print orientation: lid | 6.4 mm (252 faces) | <= 10 mm (P1S bridges; no steep overhangs) | **PASS** | trimesh, faces with normal z < -0.7 above the bed (USB window top 9.6; lid counterbore 6.4) |
| 46 | STL watertight: plug | True | True | **PASS** | trimesh |
| 47 | Max bridge/overhang span, print orientation: plug | 0.0 mm (0 faces) | <= 10 mm (P1S bridges; no steep overhangs) | **PASS** | trimesh, faces with normal z < -0.7 above the bed |

47 PASS, 0 FAIL

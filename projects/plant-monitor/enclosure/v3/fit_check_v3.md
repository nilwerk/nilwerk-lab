| # | Check | Value | Need | Result | Source |
|---|---|---|---|---|---|
| 1 | Right-most part (J1 shell) to right wall (X) | 0.30 mm (board edge 0.80) | >= 0.30 (FDM + PCB +-0.2) | **PASS** | params_v3 INNER_X1, DXF outline |
| 2 | Antenna tip to top wall (Y) | 1.00 mm | >= 1.0 [ASSUMED] | **PASS** | DXF MODULE_U1 (overhang derived by Emil); Q10 detuning open |
| 3 | Tail width vs tunnel (per side) | 0.30 mm | >= 0.30 | **PASS** | DXF tail 12.0; JLC outline +-0.2 (layout-brief s.5) |
| 4 | Tail thickness vs tunnel height (per side) | 0.15 mm | >= 0.15 (JLC 1.6 +-10 % = 0.16) | **PASS** | layout-brief s.5 thickness tolerance |
| 5 | Cell cavity (X x Y) inside the inner box | 53.0 x 35.1 | = bay.dims A_eemb603449 (53.0 x 35.1) | **PASS** | pcb-enclosure-bay.md; bay.py |
| 6 | Cell 51 x 34.5 x 6.3 spare in cavity | L 2.0 / W 0.6 / H 0.9 | L>=2.0 W>=0.6 H>=0.9 | **PASS** | bay.dims |
| 7 | Cell cavity height vs inner height | 7.2 vs 7.6 | cavity <= inner | **PASS** | bay.dims bay_h 7.2 |
| 8 | Board to cell cavity gap (X) | 5.0 mm | = 5.0 (gen_pcb CELL_GAP) | **PASS** | DXF CELL_BAY_CAVITY |
| 9 | Tallest part to lid underside | 0.50 mm (J2, 4.5 ASSUMED) | >= 0.5 (+0.7 mm gasket thickness not counted) | **PASS** | H_BY_REF [ASSUMED], board file has no heights |
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
| 21 | Wall: Lid under counterbore | 1.40 mm | >= 1.2 (role rule) | **PASS** | params_v3 |
| 22 | Wall: USB pocket remaining wall | 1.20 mm | >= 1.2 (role rule) | **PASS** | params_v3 |
| 23 | Wall: Light collar wall | 1.20 mm | >= 1.2 (role rule) | **PASS** | params_v3 |
| 24 | Wall: Vent cup wall | 1.20 mm | >= 1.2 (role rule) | **PASS** | params_v3 |
| 25 | Wall: Pinhole tube wall | 1.20 mm | >= 1.2 (role rule) | **PASS** | params_v3 |
| 26 | Wall: Boss wall around insert | 1.20 mm | >= 1.2 (role rule) | **PASS** | params_v3 |
| 27 | P1S volume: tray | 98.1 x 57.5 x 9.2 | <= 256^3 | **PASS** | standards s.1 |
| 28 | P1S volume: lid | 98.1 x 57.5 x 6.6 | <= 256^3 | **PASS** | standards s.1 |
| 29 | P1S volume: plug | 13.4 x 2.4 x 7.6 | <= 256^3 | **PASS** | standards s.1 |
| 30 | STL watertight: tray | True | True | **PASS** | trimesh |
| 31 | Max bridge/overhang span, print orientation: tray | 9.6 mm (2 faces) | <= 10 mm (P1S bridges; no steep overhangs) | **PASS** | trimesh, faces with normal z < -0.7 above the bed (USB window top 9.6; lid counterbore 6.4) |
| 32 | STL watertight: lid | True | True | **PASS** | trimesh |
| 33 | Max bridge/overhang span, print orientation: lid | 6.4 mm (252 faces) | <= 10 mm (P1S bridges; no steep overhangs) | **PASS** | trimesh, faces with normal z < -0.7 above the bed (USB window top 9.6; lid counterbore 6.4) |
| 34 | STL watertight: plug | True | True | **PASS** | trimesh |
| 35 | Max bridge/overhang span, print orientation: plug | 0.0 mm (0 faces) | <= 10 mm (P1S bridges; no steep overhangs) | **PASS** | trimesh, faces with normal z < -0.7 above the bed |

35 PASS, 0 FAIL

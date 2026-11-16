# Plant Monitor v1 demo housing (4.E5)
> **Round 2 (compact, 2026-11-16):** round-1 parameters were overwritten in place in this folder (round-1 source = commit `5f195cf`). The text below describes round 1 (exports in `enclosure/v1_demo/`, unchanged). Round 2 numbers and checks: `enclosure/v1_demo_compact/README.md`.


> **Indoor demo only. Not splash-proof, not IP-rated:** open light window and vents. Keep away from watering, no outdoor, no bathroom.
> **First print = FIT-CHECK part only** until Arsany has measured at least the tallest point above the board and the under-board height (README list items 3 and 4; still open in A-094). All part heights are ASSUMED; the 2 mm figures in A-093 are bare board thickness, not part heights.
> **Never charge unattended inside the closed box.** The TP4056 and the LiPo sit in 1.6 mm PETG, which softens far below cell-fire temperatures; the only vents are over the AHT20.

Yara (3D Product Designer) · 2026-11-14 · branch `agent/mechanical/4.E5-v1-housing`, stacked on `agent/pcb/v1-wiring` (PR #101): **merge #101 first**.
Scope: a simple printable 2-part housing (base + lid) for the **v1 function demo on the 70 x 50 mm perfboard**, Bambu Lab P1S, PETG, 0.4 mm nozzle, no supports.
Enclosure v3 / compact shell (4.E3, v2 custom PCB) is **STOPPED** by the owner on 2026-11-14 and was not touched. Nothing here was printed, sliced or measured on hardware.

**Status of every number.** MEASURED = Arsany (bare L x W x T). WIRING = Emil's typical value in `projects/plant-monitor/v1/WIRING.md`, **UNVERIFIED**. BRIEF = task brief / repo input, no datasheet read. ASSUMED = my assumption with the stated margin. ASSUMED, WIRING and BRIEF values never give a PASS in the fit check.

## What it is
Outer **118.5 x 72.6 x 24.2 mm** (assembled), inner height 21.0 mm. Left: the perfboard on four support pads (5 mm standoff = solder-side room), its two USB-C ports facing two openings in the left wall. Right: a separate LiPo bay (EEMB LP603449, cell lying along Y, lead end down) behind a divider with a U-notch for the lead, and a channel with two S-bend posts as strain relief and a parking space for the mated JST-PH pair. The lid is a hat: its skirt meets the base at the parting plane z = 13.2 mm, which cuts through both USB-C openings, so every opening is a half-slot open to its rim (no bridging). One design touch: 0.6 mm top-edge chamfer on the lid (flag `DESIGN_TOUCH`).

| Need | Feature | Value |
|---|---|---|
| USB-C SuperMini (flash/serial) | wall opening, left | 14 x 8 mm, centre y 39.0, z 13.75 (ASSUMED plug overmold) |
| USB-C TP4056 (charge) | wall opening, left | 14 x 8 mm, centre y 8.5, z 12.55 |
| BOOT / RESET | two pin guide tubes in the lid, hole d 2.2 | at x 9, y 44 / 36; tube end 1.0 mm above the assumed key top; paperclip or SIM tool |
| BH1750 light | window d 5 with collar | at x 49, y 41.5; open hole (`LIGHT_SKIN` = 0) |
| AHT20 air | 4 vent slots 1.6 x 10 in the lid | over x 50.8-63.2, y 10; 21.5 mm from the TP4056, 15 mm from the cell |
| TP4056 charge LEDs | window 14 x 5 in the lid | **position not measured (OPEN)** |
| J1 jumper | hatch 7 x 11 in the lid | above x 5.8, y 27.6; tweezers or fingernail |
| Soil sensor cable | exit slot 9 x 6 in the bottom wall | x 41.4, z 10.2-16.2 |
| LiPo lead | divider U-notch 4 mm + 2 S-bend posts | notch y 16-20, z >= 9.2, open to the top |
| Antenna end (SuperMini, x 27) | no metal, cell or wire in x 27-40 (to the wall); nearest screw 20.5 mm, cell 52.8 mm | plastic only (PETG); the only metal is 5 M2 screws and inserts |

## Parameter table (`params_v1.py`, mirrors the Fusion 360 strategy)
| Name | Value | Status |
|---|---|---|
| perfboard `PB_L x PB_W x PB_T` | 70 x 50 x 2 | MEASURED |
| TP4056 / BH1750 / AHT20 footprint | 28 x 17 / 17 x 14 / 15 x 10 | MEASURED |
| SuperMini | 22.5 x 18 | UNVERIFIED (not measured) |
| LiPo cell / bay cavity | 51 x 34.5 x 6.3 / 53.0 x 35.1 x 7.2 | BRIEF (A-020 bay input, no datasheet read); WIRING quotes 49 x 34 x 6.0 (conflict, the bay covers both) |
| `WALL`, `FLOOR`, `LID_T` | 1.6, 1.6, 1.6 | RULE (>= 1.2, task >= 1.6) |
| `FIT` perfboard pocket per side | 0.4 | RULE (0.2-0.4), printer not calibrated |
| `STANDOFF_H` | 5.0 | ASSUMED (4 mm WIRING + 1.0 margin) |
| component heights above the board | SuperMini 6.8, TP4056 5.6, BH1750 5.7, AHT20 5.5, resistors 7, J1 12, J3 12 | WIRING, UNVERIFIED |
| `LID_MARGIN` | 2.0 (lid underside z 22.6 = board top 8.6 + 12 + 2.0) | ASSUMED margin on unmeasured heights |
| `PLUG_W x PLUG_H` | 14 x 8 | ASSUMED |
| `STRIP_BOT`, `STRIP_TOP` | 11, 8 (soil plug about 10 mm long) | ASSUMED |
| `INSERT_HOLE`, `BOSS_D`, `SCREW_D` | 3.2, 7.2, 2.4 (M2 heat-set insert, M2 x 14 pan head) | ASSUMED insert, nothing ordered |
| `CH_W` lead channel | 7.0 (JST-PH 2-pin about 6 x 4.5) | ASSUMED |

## Fit check and tests
`python fit_check_v1.py [--md out.md]`: **10 PASS / 0 FAIL / 3 NOT MET / 48 OPEN** (round 2; the round-1 counts below were 15 / 0 / 35). PASS only where the input is MEASURED or a RULE (P1S volume, watertight, on the bed, walls, perfboard pocket, pads inside the board, wall requirement). Everything that depends on a part height, a hole position (grid count UNVERIFIED), the SuperMini size, the cell datasheet or an RF distance is OPEN. `python -m pytest -q enclosure_v1_demo/test_v1.py` (from `projects/plant-monitor/mechanical`) runs 25 tests (round 2, including the row-level provenance test).

## Print notes (P1S, PETG, 0.4 mm; not sliced, so no time or gram figure from Bambu Studio)
- **Base:** floor on the bed, open side up. **Lid:** print upside down (the exported STL/3MF is already flipped), top face on the bed: smooth top, posts, collar and ribs grow upward. No supports (checked: only the 0.6 mm bed-edge chamfer is an overhang).
- 0.20 mm layers, 4 wall loops (1.68 mm), infill 20 %, first layer as in the Bambu PETG profile; black, grey or white PETG. Solid-volume upper bound 24.7 cm3 base + 22.2 cm3 lid = 46.9 cm3, about 60 g at 1.27 g/cm3 (an estimate; the real figure comes from the slice).
- Fasteners: 5 x M2 x 14 pan head, 5 x M2 heat-set inserts (hole 3.2 mm, 6 mm deep) in the base bosses; the lid screws down from the top into the base. Parting plane z 13.2. The lid is 24.2 mm high, the base 13.2 mm.
- Assembly: insert the inserts, lay the perfboard (component side up) on the pads against the fins, feed the LiPo lead through the notch, check J1 is open, fit the lid, 5 screws. Programming and charging follow WIRING.md 2.3/2.4 (J1 open, never both USB ports with J1 closed).
- **Charging rule:** charge only supervised, on a non-flammable surface, preferably with the lid off, or at least with the J1 hatch and vents unobstructed; stop if the module or cell is hot or swells. No unattended charging in the closed box until Arsany decides otherwise.
- **Lid off vs lid on** (to be aligned with Emil's flash-procedure fix in #101, branch `agent/pcb/v1-wiring`, once it lands; it had not landed at the time of this round): flashing with J1 open through the jumper hatch, lid on, is the intended path; unplugging the JST pair (J_BAT) needs the lid off, because the mated pair is parked in a channel under the lid. Through the openings with the lid on: J1 hatch, BOOT/RESET pin guides (paperclip), both USB-C ports, light window, vents. Lid off: unplugging or re-seating the JST pair, any wiring change, inserting the cell, checking the lead and strain relief.
- Files: `enclosure/v1_demo/` STEP (assembled position, for Fusion 360), STL + 3MF (print orientation), STEP with reference perfboard, parts and cell; renders in `enclosure/v1_demo/renders/`. Fusion strategy: parameters above = `params_v1.py`; two bodies (base, lid); Arsany would edit opening sizes, `STANDOFF_H`, `LID_MARGIN` and the boss positions; any exported STEP from him becomes the reference.
- Cost (estimate, not for sale): about 60 g PETG at an assumed 20 EUR/kg = about 1.2 EUR, plus 5 screws and inserts (price not checked).

## Arsany must verify (with the printed box and a caliper; fill in the table, send back)
1. Perfboard drops into the pocket without force and without rattle (0.4 mm per side); the hole grid really is 24 x 18 (WIRING open item 4).
2. Both USB-C plugs you use (flash and charge) go in all the way through the 14 x 8 openings; if not, note the plug overmold W x H.
3. Real heights above the perfboard top: SuperMini incl. USB-C, TP4056 incl. USB-C, BH1750, AHT20, J1 with jumper, J3 with Dupont plug; lid must clear all of them (margin 2.0).
4. Under-board height with trimmed pins and wires (standoff 5.0 mm).
5. SuperMini: real length x width, USB-C setback from the board edge (4.5 mm assumed), BOOT/RESET key centres and which is which; does a paperclip reach both keys through the guides?
6. BH1750 chip centre under the window; TP4056 LED positions (move or resize the LED window); J1 shunt reachable through the hatch; AHT20 under the vent slots.
7. Soil plug and cable leave through the exit slot; Dupont plug length (strip 10 mm).
8. LiPo: datasheet dimensions (cell and pack) against the bay 53.0 x 35.1 x 7.2; JST-PH plug size; the lead reaches the board through the notch; the S-bend relieves the plug.
9. Insert and screw: hole 3.2 mm fits your insert; M2 x 14 length is right.
10. Antenna end stays clear: no wire, metal or cell in the keep-out; check Wi-Fi range with the lid on against without (no RF measurement exists).
11. TP4056 USB-C protrusion beyond the PCB edge against the 0.4 mm wall gap (module at x 0, wall at x -0.4): a shell that overhangs even 0.5 mm collides with the wall (WIRING section 6 lists "protrusion").
12. The real LiPo pack as delivered: size incl. protection circuit and plug against the bay, and whether it has solder tabs or a JST plug (A-091 answered: JST-PH 2.0 mm, red +; datasheet vs listing still to compare, see #101 C1).
13. Lead length from the cell to the TP4056 B+/B- pads through notch and lane (doc y 30 to 34): reaches without tension.
14. The soil sensor (95 x 22 x 2 bare board, A-093) sits OUTSIDE the box; only its cable exits through the slot. Confirm it is not meant to sit inside.
15. Screws and M2 heat-set inserts are bought by Arsany; nothing is ordered by the team.

## UNVERIFIED / not done
Nothing printed, sliced or measured; all heights WIRING typical; SuperMini size and all positions from Emil's layout plan; cell dimensions from the A-020 brief, not the datasheet; plug size, insert, screws assumed; open light window and vents are not splash-proof (indoor demo); a closed box warms the AHT20, so v1 temperature is not an ambient reading; no RF effect of the 1.6 mm PETG lid measured; no CE/EMC claim. Prototype 1 to 3 and the pilot path (standard section 10) apply before any batch.

## Run
`pip install cadquery trimesh numpy matplotlib networkx pytest`; `python build_v1.py`; renders (optional, needs `vtk` and a display): `xvfb-run -a -s "-screen 0 1600x1200x24" python render_v1.py`.

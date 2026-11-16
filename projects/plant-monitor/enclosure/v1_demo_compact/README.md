# Plant Monitor v1 demo housing, compact round 2 (4.E5)

> **FIT-CHECK ONLY. Indoor demo, not splash-proof, not IP-rated.** All part heights are WIRING typical values and UNVERIFIED (A-094 items 2 and 4 still open). Nothing here is measured, printed, sliced or RF-tested. The fit check reports 0 FAIL, but that is not a PASS on any height.
> **Never charge unattended inside the closed box.** The LiPo now sits under the board, with the TP4056 and no vent near it.

Yara (3D Product Designer) · 2026-11-16 · task 4.E5 round 2 (EXTRA from Arsany, logged as EXTRA) · branch `agent/mechanical/4.E5-compact`.
**Round 1 parameters were overwritten in place in the source folder** (round-1 source = commit `5f195cf` on main; PR #102 round-1 exports in `enclosure/v1_demo/` are unchanged). Enclosure v3 (4.E3, custom PCB) is STOPPED by the owner (2026-11-14) and was not touched. Source: `projects/plant-monitor/mechanical/enclosure_v1_demo/` (`params_v1.py` is the single source).

## What changed (Arsany's three observations)
| # | Observation | What I did | Result |
|---|---|---|---|
| a | lots of free space | removed the separate LiPo bay, divider, lead channel and the cell lid ribs | footprint 118.5 x 72.6 to **88.5 x 72.6 mm** (-25 %) |
| b | battery could sit under the perfboard | LiPo under the board, cell turned (51 mm along Y), in a floor cradle with stops; lead strain relief and JST parking in the bottom strip | 57 % of the cell is under the board (see the NOT MET list) |
| c | lid about half as tall | **qualified:** only the shell above the seam halves. Shell 5.4 vs 11.0 mm (-51 %); lid print depth unchanged at 15.3 mm (hold-down pins); base 13.2 to 26.0 mm (+97 %); box 24.2 to 31.4 mm (+30 %); footprint -25 % | parting plane above both USB-C openings (openings now fully in the base) |

**The trade-off, stated plainly:** the floor-to-board gap grows from 5.0 to **12.2 mm** (cell cavity 7.2 + solder-side pin tips 4.0 (ASSUMED from WIRING) + margin 1.0 (ASSUMED)). The cradle walls stop at 6.8 mm, below the 7.2 mm cavity: the cavity allows for swell, the walls only locate the 6.3 mm cell. The box is therefore **31.4 mm high** (round 1: 24.2, **+7.2 mm, +30 %**). Footprint -25 %, bounding volume -3 %. If the solder side under the cell is trimmed to 2 mm, the height drops by 2 mm.

## Numbers (mm, CAD frame; doc frame in the source)
| Item | Round 2 | Round 1 | Status |
|---|---|---|---|
| Outer size L x W x H | **88.5 x 72.6 x 31.4** | 118.5 x 72.6 x 24.2 | from geometry |
| Floor to board underside / board top | 12.2 / 15.8 (board underside z 13.8) | 5.0 / 8.6 | 4.0 pin tips WIRING UNVERIFIED |
| Parting plane (base height) | **26.0** (rim 1.05 above SuperMini USB-C top 24.95) | 13.2 | |
| Lid underside / lid plate top | 29.8 / 31.4 | 22.6 / 24.2 | |
| **Lid shell above the seam** | **5.4** | 11.0 | the limit: seam above the USB-C tops; lid underside by the tallest part |
| Lid part depth incl. hold-down pins | 15.3 (pins reach z 16.1) | 15.3 | pins hang into the base |
| Tallest part (J1/J3 12 mm assumed) to lid underside | 2.0 | 2.0 | ASSUMED margin, heights UNVERIFIED |
| Cell (EEMB LP603449, BRIEF) | x 50.0-84.5, y -0.5-50.5, z 1.6-7.9 | bay behind the divider | BRIEF size |
| Cell clearance to antenna keep-out box (x 27-40, y 0-22 doc) | **10.0 mm** = **my own margin** from the box edge (x 50 vs x 40) | n/a | own margin, ASSUMED. WIRING asks 10+ mm beyond the antenna end (UNVERIFIED) |
| Cell to antenna end point (x 27, doc y 2-20) | **23.0 mm** | 52.8 | WIRING '10+ mm' (UNVERIFIED) met. My earlier 20 mm figure was an ASSUMED stricter value, not a WIRING number |
| Cell to USB-C wall | 50.4 mm (no cell under the USB-C openings) | | |
| Board support | pads at x 2-14 and 41-48; **x 48-70 unsupported**. Pad 2 sits 1.0 mm from the keep-out edge (ASSUMED, the WIRING route margin applied to the pad) | pads at 2-14 and 56-68 | see NOT MET |
| Screws | **M2 x 8** (round 1 M2 x 14) | | ASSUMED, nothing ordered |
| BOOT/RESET, BH1750 window, AHT20 vents, TP4056 LED window, J1 hatch | unchanged positions; re-checked against the new lid | | J1 hatch 2 mm clear of the J1 body each side (ASSUMED) |
| USB-C openings | 14 x 8, closed at the top by the 1.05 mm rim: **bridges** 14 mm span | half-slots open to the rim | bridge printability ASSUMED |

## Where the cell does NOT fit (NOT MET, decision for Arsany)
- **The cell cannot lie fully under the board.** Free rectangles under the 70 x 50 board outside the antenna keep-out box (x 27-40, y 0-22): the widest strips are 30 x 50 (x 40-70) and 70 x 28 (y 22-50). The cell needs 34.5 x 51. A brute-force search on a 0.5 mm grid, both orientations, found **0 placements, even with no margin**.
- **Battery placement vs WIRING section 5 (NOT MET, A-100 open):** WIRING puts the battery beside or below the **left** half, outside x 22-40 y 0-25 (doc). Round 2 puts it under the **right** half. This is a deliberate deviation for Arsany to accept or reject.
- **Closest option chosen:** cell turned, right side of the board, 10.0 mm clear of the keep-out box. That 10.0 mm is **my own margin from the box edge**, not the WIRING wording (10+ mm beyond the antenna end); the cell is 23.0 mm from the antenna end point. 57 % lies under the board (x 50-70); the rest overhangs the right edge by 14.5 mm (x 70-84.5). Rejected: the lower band (y 22-56) gives 81 % under the board but touches the keep-out edge and sits 2 mm from the antenna end.
- **No board support under x 50-70** (22 mm of the 2 mm board). The cell runs the full length in Y, so no pad or post can stand there. The lid hold-down pins sit on the free corners only. Arsany checks sag on the printed box.
- **AHT20 sits over the cell** (0 mm in plan; round 1 rule was 15 mm). A charging cell may warm the sensor air. Options: move the AHT20 (a WIRING change, Emil) or accept. Not measured.

## Fit check and tests (exact output)
`python fit_check_v1.py` → **11 PASS / 0 FAIL / 3 NOT MET / 47 OPEN**. Changes from the 14 / 0 / 3 / 44 the Lead expected: the two overhang rows rest on an ASSUMED 0.8 mm threshold and the 'Model-internal' perfboard-vs-base row rests on the ASSUMED 4.0 mm pin tips, so both are OPEN (ASSUMED values never PASS). Round 1 was 15 / 0 / 35.
`python -m pytest -q` from `projects/plant-monitor/mechanical`: **80 passed** before this fix. After the fix only `enclosure_v1_demo/test_v1.py` was rerun: **24 passed**. Full suite not rerun, because it rewrites tracked `out/` exports.

## Print notes (P1S, PETG, 0.4 mm; not sliced)
- **Overhang limit 0.8 mm is ASSUMED** (not a numeric rule in the standard): a print test sets the real limit. Bridges and the 0.6 mm chamfer lip are the only overhangs.
- **Base:** floor on the bed, open side up, 88.5 x 72.6 x 26.0. Pads, cradle and posts are vertical. Bridges: the two USB-C ceilings (14 x 1.6 mm) and the cable slot (9 mm); no support material, test on the first base.
- **Lid:** top face on the bed, 88.5 x 72.6 x 15.3, one 0.6 mm bed-edge chamfer as the only overhang.
- Fasteners: 5 x M2 x 8 pan head, 5 x M2 heat-set inserts (hole 3.2, ASSUMED) in the bosses. Nothing ordered.
- Files: `enclosure_v1_demo_base|lid.stl|3mf` (print orientation), `enclosure_v1_demo_base|lid.step` (assembled position, for Fusion 360), `enclosure_v1_demo_assembly_with_reference_parts.step` (reference perfboard, parts, cell, not printed). Renders in `renders/` (hero, exploded, section, plan), made with VTK under xvfb.

## Arsany must verify (with the printed box and a caliper)
1. **Fit:** the perfboard drops into the pocket (0.4 mm per side). Both USB-C plugs go through the 14 x 8 openings, now fully in the base (the lid no longer has a cut there).
2. **Lid height vs tallest part:** real heights of J1 with jumper and J3 with the Dupont plug above the board top. The lid underside needs 2.0 mm clearance; the shell is 5.4 mm above the seam. Heights in WIRING are typical.
3. **Under-board gap:** pin tips and trimmed wires below the board (assumed 4.0). This sets the 12.2 mm floor gap and the 31.4 mm height. Measure it first (A-094 item 4).
4. **LiPo:** datasheet/pack size against the cradle 53.0 x 35.1 x 7.2 cavity (BRIEF 51 x 34.5 x 6.3); the JST-PH plug and pigtail length to TP4056 B+/B- via the bottom notch and the S-bend posts; the parking zone for the mated pair.
5. **Board support** under x 48-70: does the perfboard sag under the lid pins or a press-fit?
6. **AHT20 over the cell:** decide to move the AHT20 or accept the coupling; check the sensor reading when the cell charges (never unattended).
7. **BOOT/RESET** tubes (end 1 mm above assumed key tops), BH1750 window, vents and TP4056 LED window: re-check against the new lid. LED position still OPEN.
8. **USB-C ceilings** as 14 mm bridges and the cable slot as a 9 mm bridge: print test before a batch.
9. **RF is still unmeasured.** Antenna keep-out: no metal in x 27-40 (only 5 M2 screws and inserts, all 10 mm clear, nearest 15.1 mm); the cell is 10.0 mm clear of the box and 23 mm from the antenna end. No Wi-Fi range test exists; check range with the lid on against off.
10. **Soil cable** exit slot at z 18.3-24.3 (5.5 above the board top, ASSUMED plug height).

## UNVERIFIED / not done
Nothing printed, sliced, measured or RF-tested. All part heights WIRING typical. The cell size is the A-020 brief, no datasheet read in this round. Lead route (about 60 mm to TP4056), JST-PH size, the S-bend and the parking zone are assumed. The renders use the BRIEF cell and WIRING positions. No CE/EMC claim. The first base and lid are prototype 1 under the standard (section 10): a 5-10 unit pilot only after the fit is confirmed.

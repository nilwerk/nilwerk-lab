# 4.E3 JLC order package, 3D side: DRY RUN

Yara (3D designer) · 2026-11-09 · Branch `agent/mechanical/4.E3-jlc-prep` · Plan task 4.E3 (3D side of the 4.P2 board)

**Status: dry run only.** Nothing is ordered, uploaded to JLCPCB, or sent. Emil prepares the order package, Arsany reviews and submits it himself.

**Board status (honest): the board is NOT routed.** It has placed footprints and no tracks, no filled zones, no silkscreen, no mounting holes, no fiducials or panel rails. **9 footprints are placeholders** (see section 3). The 7 in the request does not match the source: `layout-4P2.md` ("Placeholder footprints") names 9 refs, and `design.py` flags 6 with `custom_fp` (SW1-SW3, U5, U6, E1). This package uses the 9 from `layout-4P2.md`. Emil or the Lead should confirm which list is meant.

Board source: branch `agent/pcb/4.P2`, commit `da39d2c` (PR #64, not merged to `main` when this was written). The two files in `input/` are copied unchanged from that commit (`cmp` identical). Re-copy them if Emil changes the board.

## Files

| File | What |
|---|---|
| `input/plant-monitor.kicad_pcb`, `input/plant-monitor-outline.dxf` | board source from `agent/pcb/4.P2` @ `da39d2c`, unchanged |
| `board_step.py` | parses the KiCad board and writes the STEP (`out/plant-monitor-board.step`) |
| `fit_check.py` | fit check against the battery bay, numbers and source lines printed |
| `render_top.py` | 2D top view of the same source, used for the showcase image (`out/board-top-view.png`) |
| `test_jlc_prep.py` | 5 tests (see section 5) |
| `out/plant-monitor-board.step` | the STEP export (3.3 MB, 217 solids) |

## 1. STEP export: outline and placed footprints

What is in the STEP (mm; STEP Y = DXF Y = -KiCad Y, so the top view matches the KiCad screen view):

- **BOARD**: the Edge.Cuts outline (8 segments, body 34.5 x 42.0 + stake tail 12.0 x 25.0, overall 34.5 x 67.0), 1.6 mm thick (`general (thickness 1.6)` in `plant-monitor.kicad_pcb`), 16 via holes 0.3 mm drilled through.
- **FP_<ref>** (46 parts): the copper pads of each placed footprint (184 pads), top layer, **0.035 mm thick**. The 0.035 mm is **not in the repo**: it is the usual nominal value for 1 oz copper (the layout brief says "1 oz outer"). It is only used to give the pads a solid body.
- **VIA_RINGS**: 16 vias x 2 annular rings (0.7 mm pad, 0.3 mm drill; `(size 0.7) (drill 0.3)` in the board file).
- **Not in the STEP**: component bodies (the source has **no component heights and no 3D models**, so a part's height cannot be shown), tracks (none), zones, silkscreen, mask, the battery cell (not board copper), the stake electrodes beyond their pad copper.

Validation (CadQuery 2.8.0 / OCC, run in this session):
- `cadquery.importers.importStep(out/plant-monitor-board.step)` opens without error.
- 217 solids (1 board + 32 via rings + 184 pads), `isValid() = True`.
- Bounding box X 0.0 to 34.5, Y -67.0 to 0.0, Z -0.035 to 1.635 mm.
- Total volume 2807.8 mm3 (sanity: outline area 1749 mm2 x 1.6 mm = 2798 mm3, plus copper).

Findings in the source (not fixed here, the board is Emil's file; for Emil):
1. **R16 pads are rotated twice.** `pcb/gen_pcb.py` writes the footprint angle (90 deg) again on each pad, and KiCad stores pad angles relative to the footprint, so the pads come out at 180 deg. Pad centres are right, but the 0.8 x 0.95 mm pads are 90 deg off from the intended orientation (the pad-to-pad gap along the part changes from 0.85 mm to 0.70 mm). J2 (180 deg) is unaffected because its pads are symmetric. This is my reading of the KiCad file format; no KiCad was available to confirm it.
2. `layout-4P2.md` gives the antenna end to cell cavity distance as 26.2 mm. From the DXF I get **28.4 mm** (antenna edge Y +6.0, X 20.3 to 33.5; cavity corner X -5.0, Y -6.9). The basis of the 26.2 is not stated. Either way the 15 mm rule is met.

## 2. Fit check against the battery bay

Bay numbers: `mechanical/README.md` (lines 21 to 25, EEMB 603449, the selected cell) and `params.py` / `bay.py dims()`. Board numbers: `input/plant-monitor-outline.dxf`. Run `python3 fit_check.py`.

| Check | Value | Margin | Source |
|---|---|---|---|
| Cell cavity L x W (usable, bay) | 53.0 x 35.1 mm | matches | DXF layer `CELL_BAY_CAVITY`; `mechanical/README.md` line 22 |
| Bay module outer L x W x H | 56.2 x 38.3 x 10.4 mm | matches | `mechanical/README.md` line 25; `params.py` line 13 (WALL 1.6) |
| Board width vs cavity width, **only if stacked over the cell** | 34.5 vs 35.1 mm | **0.30 mm per side** | DXF OUTLINE X 0 to 34.5; `README.md` line 22 |
| Cell cavity to board edge, **beside (the layout)** | 5.0 mm | 5.0 mm | `pcb/gen_pcb.py` line 34 `CELL_GAP = 5.0` |
| Bay module outer to board edge, beside | 3.4 mm | +3.4 mm | derived: 5.0 - WALL 1.6 (`params.py` line 13) |
| Antenna end to cell cavity vs 15 mm rule | 28.4 mm | **+13.4 mm** | DXF `MODULE_U1` and `CELL_BAY_CAVITY`; rule `pcb/gen_pcb.py` line 46 (ANT_CLEAR_MM 15) |
| Board thickness vs cavity height (stacked only) | board 1.6 mm, cavity 7.2 mm | **not checked**: component heights are not in the source | `gen_pcb.py` `general (thickness 1.6)`; `README.md` line 22 |
| Enclosure v3 inner cavity for the board | **not set** | **not checked** | `mechanical/README.md` line 40; Q2 (inner size) still open for Yara |

Reading: the board fits **beside** the battery bay with the layout's 5.0 mm gap and 3.4 mm to the bay module outer, and the antenna stays 13.4 mm beyond the 15 mm rule. The board does **not** fit inside the battery bay (its width margin is 0.30 mm per side, and the stacked case needs component heights that are not in the source). **The margin to the enclosure walls cannot be stated yet**: the enclosure's inner size for the electronics is still open (Q2), and the lid and seal wait for the outline.

## 3. Placeholders (what is drawn for real and what is not)

Placeholder geometry (pad pattern and size not from a drawing), from `layout-4P2.md` "What is NOT done":
U1 ESP32-C3-MINI-1 (pad pattern not the datasheet Fig 11-1), J1 USB-C (C165948 drawing not read), J2 JST PH (approximate), SW1, SW2, SW3 (BOOT, RESET, pinhole), U5 AHT20, U6 BH1750, E1 (stake electrodes). That is **9 refs**.

Pin verification: `pin_verified = False` for SW1-SW3, U5, U6 and J1 (`design.py`); not compared with the placed footprints. The other footprints are KiCad-style land patterns written by hand, not compared with the library.

## 4. What the JLCPCB 3D view will show (expected, not checked)

Nothing has been uploaded, so this is what the STEP and the board file imply, not what JLCPCB renders:

- **Will show**: the 1.6 mm board with its real outline (34.5 x 67 mm, body plus stake tail), 16 via holes with rings, copper pads for all 46 placed footprints in their placed positions, and the 9 placeholder footprints as flat pad patterns.
- **Will not show from this package**: component bodies. The JLCPCB viewer normally uses its own component models for LCSC parts. That is **unverified here**, and it can only be checked after an upload, which is Arsany's step. The 9 placeholders may show as pads only or as a generic body, depending on the JLC library.
- **Will not show at all**: routing (none), the cell (not board copper), the lid and seal, the enclosure, silkscreen, mask.
- **DFM view**: not run (no JLC access in this session, no KiCad in this session).

## 5. Tests and checks (run in this session)

- `python3 -m pytest jlc_prep/test_jlc_prep.py`: **5 passed** (source counts 46 / 184 / 16 / 8 segments / 1.6 mm; outline equals the DXF; board size and bay numbers equal the README lines; fit margins; STEP re-opens, 217 solids valid, bounding box).
- `python3 fit_check.py`: 6 PASS, 2 NOT CHECKED (listed in section 2), exit 0.
- KiCad ERC/DRC, the CI `pcb` job, and the 4.P2 `check_layout.py` (18 checks) were **not run here**. They belong to 4.P2 and are cited from its README, not re-run.

## Run

From `projects/plant-monitor/mechanical/`: `pip install cadquery trimesh numpy matplotlib pytest`, then `python3 jlc_prep/board_step.py && python3 jlc_prep/render_top.py && python3 jlc_prep/fit_check.py && python3 -m pytest jlc_prep/test_jlc_prep.py`.

## Open before any order (not Yara's to close)

1. Emil: routing, footprint review of the 9 placeholders against the drawings, R16 pad angle, the 26.2 vs 28.4 mm note.
2. Yara / Arsany: enclosure inner size (Q2), lid and seal, stake size (Q5).
3. Arsany: the JLC order itself, and any upload. Nothing here is ordered or uploaded.

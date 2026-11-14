# JLCPCB Gerber + drill package, board and 2-up panel (Plan 4.P2 EXTRA, branch `agent/pcb/gerber-pkg`)

Emil (PCB Designer). Built 2026-11-12 from the 4.P2 head `3e6370f` (PR #80 + PR #84). PR #84 and PR #90 (panel tabs, AHT20 land pattern) are both merged (#90 as `d3522f7`, an ancestor of this branch); the zips pre-date #90 and are STALE (see the banner).

> **NOT FAB-READY. NOT ORDERED. NOT A RELEASE.** Nothing was uploaded to JLCPCB, nothing was bought, and the 4.P3 gate (Arsany) has not been passed.
> **NOT FOR ORDER: both zips** (`plant-monitor-jlc-panel-2up.zip` and `plant-monitor-jlc-board.zip`). The panel has no breakaway tabs or mouse bites. Hold any order until both zips are regenerated from the current board (PR #90 is already merged; see *Regeneration* below). **C2 is open** until then; these zips are not regenerated yet.
> **STALE (checked 2026-11-14, Emil):** PR #90 is merged and the board changed after these zips were built. `plant-monitor.kicad_pcb` Edge.Cuts is now 34.50 x 67.80 mm (tail 25.8 mm, A-071); the zips hold 34.50 x 67.00 mm (`verify-report.txt` loop 1). The zips and `SHA256SUMS` are **not regenerated**: no `kicad-cli` and no running Docker daemon in this session. Do not use them for anything but history.
> The older set in `../jlcpcb/gerbers/` is **SUPERSEDED** by this folder; do not order from it.
> Open before any order: signal routing is not done (117 unconnected items at all severities on the board; GND pour not filled), 3 power-section connections are open (VBUS J1 A9, CC1 R1, DW_OC Q1 pad 5; see `../layout-4P2.md`), the panel has **no breakaway tabs or mouse bites** (see below), the silkscreen layers are empty, and E1 (soil probe copper) is still a placeholder footprint.
> The fabrication files are correct as **exports of this board state**; they say nothing about whether the board works.

## What is in this folder

| File | What it is |
|---|---|
| `plant-monitor-jlc-board.zip` | **NOT FOR ORDER** until regenerated (PR #90, merged, changed the AHT20 land pattern on this board; the zips pre-date it). Board, 15 files (single board, 2 layers, no inner layers: the stackup has F.Cu and B.Cu only). |
| `plant-monitor-jlc-panel-2up.zip` | **NOT FOR ORDER.** 2-up panel, 83.0 x 79.0 mm, same 15 files (`panel/plant-monitor-panel.kicad_pcb`). **No breakaway tabs or mouse bites** (open point 2). Hold until the panel is regenerated: PR #90 (panel tabs) is merged, but these zips pre-date it, so the zip panel still has no tabs. |
| `NOT-FOR-ORDER.txt` | One-line warning kept next to the zips (they are not renamed, so the hashes hold). |
| `SHA256SUMS` | Hashes of both zips. |
| `build_gerber.sh` | The KiCad 9 export, run in `kicad/kicad:9.0` (the image of CI job `pcb`). DRC exactly as CI, then the exports. |
| `make_panel.py` | Builds `panel/plant-monitor-panel.kicad_pcb` from the board file and the panel geometry in `../jlcpcb/panel.py` (same numbers as the DXF). Copies the board's `.kicad_pro` so the panel uses the same DRC rules. |
| `package_jlc.py` | Renames the KiCad output to the JLCPCB names and writes the zips (fixed timestamps, so the zips are reproducible). |
| `verify_gerber.py` | Independent check of the two zips against the PCB files. Output: `verify-report.txt`. |
| `reports/` | KiCad DRC reports (error level as CI, all severities), drill reports, and the export log. |

### Zip contents (board and panel are the same list)

| JLCPCB name | KiCad file | Layer | Verified |
|---|---|---|---|
| `Gerber_TopLayer.GTL` | `F_Cu` | top copper | parses (gerbonara), 449 objects board / 901 panel |
| `Gerber_BottomLayer.GBL` | `B_Cu` | bottom copper | parses, 116 / 232 objects |
| `Gerber_TopSolderMaskLayer.GTS` | `F_Mask` | top soldermask openings | parses; 210 of 210 F.Cu pads (SMD + thru-hole) have an opening equal to the pad (board), 423 of 423 (panel) |
| `Gerber_BottomSolderMaskLayer.GBS` | `B_Mask` | bottom soldermask openings | parses; 4 of 4 B.Cu pads (board), 8 of 8 (panel) |
| `Gerber_TopPasteMaskLayer.GTP` | `F_Paste` | top paste | parses; 205 of 205 SMD pads have a paste aperture equal to the pad (board), 410 of 410 (panel) |
| `Gerber_BottomPasteMaskLayer.GBP` | `B_Paste` | bottom paste | parses, **0 objects: no bottom SMD pads in this design** (empty by design) |
| `Gerber_TopSilkscreenLayer.GTO` | `F_Silkscreen` | top silkscreen | parses, **0 objects: no silkscreen is drawn yet** (no reference designators, no polarity marks; a gap for assembly, see open points) |
| `Gerber_BottomSilkscreenLayer.GBO` | `B_Silkscreen` | bottom silkscreen | parses, 0 objects (same) |
| `Gerber_BoardOutlineLayer.GKO` | `Edge_Cuts` | board outline | board: 1 closed loop, 8 lines, area 1749.0 mm2, equal to the PCB outline; panel: 3 closed loops (rails 83 x 79, two boards 1749 mm2 each) |
| `Drill_PTH_Through.DRL` | `PTH` | plated holes: 35 x 0.30 mm vias, 4 x 0.6 x 1.7 mm slots (J1 shield) | board 35 round + 4 slots, all 35 positions equal the PCB; panel 70 + 8 slots |
| `Drill_NPTH_Through.DRL` | `NPTH` | non-plated: 2 x 0.65 mm (J1 pegs) | board 2, positions equal; panel 4 x 0.65 + 2 x 2.0 mm tooling holes, positions equal |
| `Drill_PTH_Through_Map.GBR`, `Drill_NPTH_Through_Map.GBR` | `*-drl_map.gbr` | drill maps (gerber X2) | parse (gerbonara) |
| `Drill_Report.rpt` | `*-drill.rpt` | drill report (tool table, counts) | text |
| `Gerber_JobFile.gbrjob` | `*-job.gbrjob` | Gerber job file: **kicad-cli 9.0.9 does produce it** (`pcb export gerbers`); its 9 `Path` entries were renamed to the JLC names, all exist in the zip | JSON parse, 9 of 9 paths exist |

Not in the zip on purpose: `cpl.csv` (placement file, kept in `../jlcpcb/`).

Naming: JLCPCB's suggested naming page (read 2026-11-12) lists `boardname.GTL` style with one drill file. The names used here are the EasyEDA/JLCPCB convention (`Gerber_TopLayer.GTL`, `Drill_PTH_Through.DRL`, `Drill_NPTH_Through.DRL`), which JLCPCB's EasyEDA guide describes. **UNVERIFIED: the upload page has not been opened (no order, no login), so the naming is not checked against the live uploader.**

## Verification output

`verify-report.txt` is the real output of `verify_gerber.py` (59 PASS, 0 FAIL). Re-run on 2026-11-13 (round 2, same zips and `SHA256SUMS`): the PASS/FAIL lines are identical to the committed report, 59 PASS, 0 FAIL, exit 0. The zip hashes match `SHA256SUMS`. Parsers: **gerbonara 1.5.0** for Gerber files and drill maps; **pcb-tools 0.1.6** for the Excellon drill files. Gerbonara 1.5.0 could not read the drill file: KiCad 9 writes slots as `X27.17Y-28.68G85X28.27Y-28.68` (no newline between the two statements), and gerbonara reports `Unknown excellon statement`. That is a gerbonara limitation, not a file error, so the drill files are read by pcb-tools (which reads all 39 PTH hits and the 4 slots). Expected values come from the `.kicad_pcb` files, read by a small S-expression reader in `verify_gerber.py` (not KiCad). Gerber and Excellon y is the negative of KiCad y; the check applies that sign.

Key lines (full output in `verify-report.txt`):

```
PASS  BOARD: 15 of 15 required files present (missing: none)
PASS  BOARD: Edge.Cuts is one closed loop: 8 segments, open ends 0, arcs 0
PASS  BOARD: Edge.Cuts segments equal the PCB outline (8 lines, same endpoints, y sign applied)
PCB file: 35 vias (drill {0.3: 35}), 0 PTH pads round, 4 PTH pads oval (slots), 2 NPTH pads
PASS  BOARD: PTH file holes = PCB vias + plated pads: round {0.3: 35} (PCB {0.3: 35}), slots 4 (PCB 4)
PASS  BOARD: NPTH file holes = PCB np_thru_hole pads: {0.65: 2} (PCB {0.65: 2})
PASS  BOARD: PTH 0.30 mm: 35 of 35 hole positions match the PCB to 0.002 mm
PASS  BOARD: NPTH 0.65 mm: 2 of 2 hole positions match the PCB to 0.002 mm
PASS  BOARD top soldermask: 210 of 210 pads on F.Cu (smd + thru_hole with F.Mask) have an opening equal to the pad, to 0.01 mm; 212 mask flashes in file
PASS  BOARD top paste: 205 of 205 SMD pads have a paste aperture equal to the pad
PASS  BOARD bottom soldermask: 4 of 4 pads on B.Cu (smd + thru_hole with B.Mask) have an opening equal to the pad, to 0.01 mm
PASS  PANEL 2-up: Edge.Cuts = 3 closed loops (expected 3: panel rails + 2 boards), open ends 0, arcs 0
PASS  PANEL 2-up: PTH file holes = PCB vias + plated pads: round {0.3: 70} (PCB {0.3: 70}), slots 8 (PCB 8)
PASS  PANEL 2-up: NPTH file holes = PCB np_thru_hole pads: {0.65: 4, 2.0: 2} (PCB {0.65: 4, 2.0: 2})
PASS  PANEL 2-up fiducial (3.85, -3.85): copper 1.00 mm on F.Cu found; mask opening 2.00 mm found   (and 2 more)
PASS  PANEL 2-up tooling hole (3.00, -39.50): NPTH 2.00 mm in the NPTH drill file found             (and 1 more)
RESULT: ALL CHECKS PASS (0 FAIL)
```

Soldermask spot check, board, top side (10 SMD pads, PCB pad to mask flash, mm): `RF_Module pad 1 (21.000,-2.500) 0.40x0.80 -> mask flash 0.80x0.40`, and pads 2 to 10 the same way. The bottom side has 4 thru-hole pads (the J1 shield slots, with mask openings equal to the pad, 4 of 4); there are no bottom SMD pads. The full list of matches is in `verify-report.txt`.

Two extra checks that prove the verifier can fail: the first run (before the rotation fix) reported 121 mask mismatches on rotated footprints, and the 26 pads of the 90 and 270 degree footprints match only with the rotation sign used in `verify_gerber.py`. Those were verifier errors, fixed and documented in the script; nothing in the board was changed.

## DRC (KiCad 9.0.9, same image as CI)

| Run | Board | Panel |
|---|---|---|
| `pcb drc --severity-error` (CI command) | 0 violations, 0 unconnected at error level, exit 0 | 0 violations, 0 unconnected at error level, exit 0 (with the board's `.kicad_pro` rules) |
| `pcb drc --severity-all` | 62 violations, 117 unconnected items; types: `unconnected_items` 117, `lib_footprint_issues` 46, `via_dangling` 16 (listed in `reports/board-all.rpt`) | 129 violations, 263 unconnected items; `lib_footprint_issues` 97, `via_dangling` 32 (`reports/panel-all.rpt`) |

The 117 unconnected items are the open routing (not a reading error): the board is not routed beyond the power section. The panel count is higher because each copy has its own routing gap. The error-level zero means the CI gate is met; it does not mean the board is routed.

## Open points (what a fab would stop on, and what is UNVERIFIED)

1. **Routing open** (117 unconnected items). No fab order until 4.P2 routing is done (Plan 4.P2 next slice).
2. **Panel has no breakaway tabs or mouse bites.** The two board outlines are separate closed loops and do not touch the rails. A panel built like this does not hold together for assembly. Tab/mouse-bite spec is not read from JLCPCB (UNVERIFIED) and not designed. **Blocker for the panel; the panel zip is NOT FOR ORDER until it is regenerated: PR #90 (panel tabs) is merged, but this zip pre-dates it. Whether the regenerated panel has tabs is not checked here.**
3. **Silkscreen is empty** (0 objects on both sides): no reference designators, polarity or pin-1 marks. Needed for hand checks and for JLC's assembly review. Not designed yet.
4. **Tooling-hole and fiducial positions** (`../jlcpcb/panel.py`): 2 mm NPTH tooling holes at 3.0 mm from the panel edge, 1 mm copper fiducials at 3.85 mm, 2 mm mask opening. The centre of the tooling hole is `[mine, UNVERIFIED]` (the JLC page gives the diameter only). The mask opening is `[mine, UNVERIFIED]`.
5. **Slot pads 0.6 x 1.7 mm (J1 shield)**: slots in the PTH file (4). JLC acceptance is UNVERIFIED (not read on their page for this geometry).
6. **Gerber job file `Revision` field** is `rev?` (KiCad default; no revision set in the project). Set it before any release.
7. **Vias are outside pads** (F12, PASS in the earlier dry-run checklist); vias in pad with filled and capped vias are not priced (UNVERIFIED).
8. **Placeholder footprint E1** (soil probe copper): its copper and mask are the placeholder geometry; the mask and paste checks pass against that placeholder, not against a drawn footprint.
9. **Parsers.** Gerbonara 1.5.0 and pcb-tools 0.1.6 are not JLCPCB's own CAM. The CAM preview on JLCPCB's side has not been seen (UNVERIFIED).
10. **Existing 4.P2 artifacts** (`../jlcpcb/gerbers/plant-monitor-gerber.zip`, `../jlcpcb/README.md`, `../jlcpcb/dry-run-checklist.md` and the other files there) are **not changed** by this package. The checklist items F5 (panel Gerber) and F6 (panel fiducials and tooling holes in the Gerber) are not re-graded here: they are Ines's items and need her re-check of this folder. The old zip has one combined PTH drill file and no drill map or report; this package replaces it for the panel and board once Arsany and Ines accept it.

## Regeneration (C2: OPEN; PR #90 is merged, the regeneration still has to be run with KiCad 9)

Status 2026-11-14: PR #84 and PR #90 are merged (#90 = `d3522f7`, ancestor of this branch). The zips in this folder are **not regenerated**: they are still built from `3e6370f`. Do not claim C2 is done until the steps below have run and the new hashes are in `SHA256SUMS`.

From the repository root, this is the one command (it needs Docker with the `kicad/kicad:9.0` image, which is the CI `pcb` job image, and the host Python 3):

```
G=projects/plant-monitor/pcb/gerber; RAW=$(mktemp -d) && python3 -I $G/make_panel.py projects/plant-monitor/pcb/plant-monitor.kicad_pcb projects/plant-monitor/pcb/jlcpcb $G/panel/plant-monitor-panel.kicad_pcb && docker run --rm --user root -v "$PWD":/work -v "$RAW":/out -w /work/projects/plant-monitor/pcb/gerber kicad/kicad:9.0 bash build_gerber.sh && python3 -I $G/package_jlc.py "$RAW" $G && (cd $G && sha256sum -c SHA256SUMS)
```

- `make_panel.py` builds the panel board from the board file and `jlcpcb/panel.py`; `build_gerber.sh` runs the CI DRC and the KiCad 9 export into `$RAW` (outside the repo); `package_jlc.py` writes both zips **and `SHA256SUMS`** into this folder (the hashes are not edited by hand). The last `sha256sum -c` checks the new hashes.
- Then run the verifier in a scratch venv (`gerbonara==1.5.0`, `pcb-tools==0.1.6`; not installed in the repo): `<venv>/bin/python -I $G/verify_gerber.py $G projects/plant-monitor/pcb > $G/verify-report.txt` from the repository root. Expect 0 FAIL.
- Update the table above (object counts, outline and drill counts) from the new run, and the "Built ... from" line at the top.
- Check the `.gbrjob` `Revision` field (open point 6) before any release.
- The steps are **not run** on this branch: no Docker daemon and no `kicad-cli` in the agent session, (checked again 2026-11-14: `docker info` cannot reach the daemon, `kicad-cli` not installed). PR #90 is merged, so this regeneration is now due.

## Requirement IDs and acceptance (C3, A-089)

- **NFR-08** ("CE/RED-minded design"): acceptance in `projects/plant-monitor/tests/acceptance-matrix.md:55`: PASS if the **PCB review checklist is fully ticked** (pre-certified module, antenna keep-out, ESD on USB lines). Gate 4.P3 (G4a).
- **NFR-09** ("Unit cost low; BOM at 1k pcs"): acceptance in `tests/acceptance-matrix.md:56`: BOM tab has 3-pc and 1k-pc prices for every line, with a written verdict against the 10 EUR target. Gate 2.5 (G2).
- This package is an input to the PCB review checklist (NFR-08) and to the cost view (NFR-09). It does **not** prove either: the checklist is ticked at 4.P3, and the BOM is 2.5's table. The package is not a pass for NFR-08 or NFR-09.
- Not cited here: NFR-12 (deep-sleep limit, A-027). **PENDING A-089, NOT DECIDED.** `tests/acceptance-matrix.md` still carries NFR-12 as accepted by A-027 (deep-sleep <= 50 uA), while Requirements v0.1 has no NFR-12: two sources disagree. A-089 asks Arsany which is right; the recommendation (a) is to cite NFR-08/NFR-09. If he picks (b), the NFR-12 citation goes back into `layout-4P2.md`. The sleep-sum check (`check_netlist.py`) is the NFR-01 evidence either way.

## Superseded set

`../jlcpcb/gerbers/plant-monitor-gerber.zip` (one combined PTH drill file, no drill map or report, 4.P2 slice 2 head `8ad6122`) is **SUPERSEDED** by this folder as of 2026-11-13. Kept for history only. Ines's dry-run items F5 (panel Gerber) and F6 (panel fiducials and tooling holes) are not re-graded here.

## Showcase

`showcase/items/2026-11-13_4.P2-gerber/`: two renders drawn from these zips' Gerber files (copper, drill holes, board outline), not JLCPCB's CAM view. No price and no confidential content.

# Reference projects (Arsany's earlier work, kept in Drive)

Three earlier prototypes the team may learn from and reuse **inside Nilwerk**. They are reference material, not requirements: a rule or number from here never overrides our Requirements, an answered Q-xx or an A-xxx decision.

| Project | Drive folder | For | What it is |
|---|---|---|---|
| `orbit-case` | https://drive.google.com/drive/folders/1eIfytzTBocK0FbMh5q3NQSLn8puYW4YD | Yara | Parametric CadQuery enclosure for an Adafruit CLUE (a desktop gadget). Two shells, M2 self-tapping screws, battery pocket, USB slot, vents. Fitted to the vendor's official STEP model. |
| `Soil Monitor case` | https://drive.google.com/drive/folders/1lEd2SMXyABaUf84RHdu-mm4ChBUrN1wL | Yara | Slim upright soil-monitor stake (CadQuery). A rounded head holds the PCB and a 35 x 55 x 6.5 mm LiPo in layers. A SEN0193 soil blade exits the lower end through an integrated guide channel. About 76 x 86 x 28 mm. |
| `v4_c6_lipo` | https://drive.google.com/drive/folders/1FXh76OPGqxBkrfGh78QNGHLYj-hBONJI | Emil | KiCad project: ESP32-C6 board, MCP73871 LiPo charger with power path, TPS63031 buck-boost, BME680. Includes a generated JLCPCB fab package (Gerbers, BOM, CPL, order notes) and local footprint libraries. |

Access: read-only through the team's Google Drive connector (folder IDs in the links). Do not edit or move files there. Copy only what you need into the repo, under `projects/plant-monitor/` with the source named.

## What looks worth learning or reusing (Nora's reading of the three READMEs, 2026-11-14; to be confirmed by Yara and Emil)

### Yara: `orbit-case` and `Soil Monitor case`
- A repeatable CadQuery pipeline: `*_case.py` (all dimensions) + `check_fit.py` (Boolean checks against the real board model) + `export_case.py` (watertight STL check, coloured STEP assembly, renders). Compare with our `params_v3.py` / `fit_check_v3.py` / `build_v3.py` and keep whichever checks we lack.
- Fitting to the vendor's official STEP model, not to an estimate. We still have ASSUMED component heights (J1, J2): this is the cure.
- The soil-stake concept: probe blade through an integrated guide channel (16 mm long, opening 23.8 x 2.4 mm for a 23 x 1.6 mm blade), battery layered behind the board, an aperture that needs a separate clear non-conductive insert. Close to our probe-through-the-case problem (A-071 tail, seal, light window).
- The honest wording: it says outright what the CAD cannot verify (physical fit, soil retention, cable bend, RF, moisture, printability) and that the unsealed seam means "not waterproof". Our captions should do the same.
- Their print settings used Ultimaker S7 and PLA. **Ours is a Bambu P1S with PETG**: take the method, not the numbers.

### Emil: `v4_c6_lipo`
- Charger power path: charger `OUT` to the system rail, `BAT` to the cell; the VPCC divider senses the 5 V input; `THERM` tied to disable temperature qualification is a stated risk. Compare with our decision to have no power path (A-045) and our TP4056 circuit before assuming either is right.
- A local, datasheet-based footprint (BME680 land pattern) instead of a library part; a footprint README recording the provenance.
- A generated package: JLCPCB BOM (29 rows / 41 placements), CPL with metric coordinates, explicit `Top` side and nonnegative angles (KiCad -90 deg is CPL 270 deg), DNP excluded, BOM and CPL designator sets cross-checked. Reuse the idea (and maybe the script) for our 4.P4 package. Arsany places the order; agents do not.
- Via-in-pad handled with a custom marking layer (`sk.gbr`) plus order notes asking for epoxy fill and copper cap at four named sites only. Our A-069 chose vias out of pads; keep this as the fallback for tight pads.
- A full validation record (ERC, DRC with schematic parity, Gerber analysis, fab release gate, SPICE) with a clear "not production qualified" line, and an explicit list of false positives (the SYS_IN findings) next to the real limitation (no USB ESD). The same pattern showed up in our own skills trial.
- Caution: that project used KiCad 10.0.8; we use KiCad 9. Check file compatibility before copying anything.

## Licence and provenance
- These are Arsany's own projects for Nilwerk use. `v4_c6_lipo` says its source (the v3 board) had **no general reuse licence** and the v4 derivative is within Arsany's project-specific permission. So: internal reference only. Do not publish copied files, schematics or footprints in `showcase/`, the case study or any customer document without asking Arsany.
- Anything adapted from them carries a comment naming the source folder.

## Study results (2026-11-14, Yara and Emil read the Drive files; nothing downloaded was run)

Where this differs from the first reading above, **this section wins**.

### Yara: `orbit-case` and `Soil Monitor case`
- **Our fit check is already ahead of both.** Neither reference has nearest-distance checks; both use a 0.05 mm3 overlap threshold, which is interference, not clearance. The Soil README reads stronger than its code.
- Mistakes in the references (do not copy the patterns): Orbit `check_fit.py` never exits non-zero, so CI cannot gate on it; Soil's light-window probe starts exactly where the cut starts, so it can never fail; Soil's "BME side vent zone" proxy is built but never evaluated; Orbit's README and docstring disagree about supports and the UFP path; both use unpinned or external venv paths; neither models battery swelling.
- What helps our open items: only the 0.4 mm per-side clearance and 16 mm parallel channel length of the Soil probe guide (reference, not a seal; our P1S/PETG numbers come from a test print). The USB-pocket lip has no precedent in either project. The 8.6 mm cavity has none either.
- **Plug side walls are our own arithmetic:** `PLUG_W` 13.4 minus `TUNNEL_W` 12.6, halved, is 0.40 mm per side, matching what print-prep found. Soil's 1.2-1.3 mm guide walls suggest a plug nearer 15.0 mm. That is Yara's proposal and needs a test print before anyone relies on it.
- **Checks to add to `fit_check_v3.py` (none comes from the references):**
  1. Min-distance rows with CadQuery `Shape.distance()`: tail to tunnel, tray to board, boss to board.
  2. A local wall-thickness scan on the STL around the tunnel, plug and USB pocket (our wall rows are parameter arithmetic).
  3. Window probes (from Orbit's `clear()`): a probe volume in front of U6, the U5 vents and the SW3 pinhole must intersect nothing, and the probe must be able to fail.
  4. A USB plug and cable envelope swept out of J1 and intersected with the tray.
  5. A vendor-STEP twin for J1 and J2 with a bounding-box assertion, only once the manufacturer's STEP is obtained. Mark OPEN until then.
- Rules Yara proposes for her playbook (to go through the retro, not applied here): every fit script exits non-zero on failure; assert the bounding box of an imported twin; measure local wall thickness on the mesh; add min-distance rows; make every opening probe able to fail.
- Not opened (binaries): STEP, STL, 3MF, UFP, PNG. No licence text exists in any file she read; the Adafruit STEP licence is unverified. The Soil board outline and component centres come from `v4_c6_lipo`: do not copy.

### Emil: `v4_c6_lipo`
- Not opened: PDF, preview PNG, `.kicad_pcb`, `.kicad_pro`, lib tables, the Gerber zip and the gerbers/drill subfolders, the Espressif libraries and the licence note. Read: README, order notes, both BOMs, both CPLs, `sk.gbr`, the footprint and its README, and the schematic (net extractor written by Emil).
- **Corrections to the first reading:** the v4 `THERM` resistor (R19 10k to GND) mimics a 10k NTC at room temperature; it does not truly disable qualification, although the README says "disables". There is **no generator script** in the folder, only outputs.
- **Charger comparison (question for Theo, not a redesign):** v4 uses MCP73871 with OUT to the system rail (SYS_IN) and BAT to the cell; ours is TP4056 plus an LDO from VBAT with no power path (A-046). While USB is plugged in and the firmware runs, the TP4056 sees the load and its termination threshold (about 46 mA) is below the awake current, so "full" may be delayed (ADR-015, FR-D06). A power path avoids that but puts MCP73871 and TPS63031 quiescent currents on the cell, against our 21.6 uA typical sleep and 25 uA target. Emil read neither datasheet, so this is an open question. Do not copy v4's always-on LED (about 3-4 mA by Emil's estimate).
- **Adopt in `pcb/jlcpcb/make_jlcpcb_package.py`:** group BOM lines by LCSC code (v4 split C66501 over three rows because of "100 nF" vs "0.1 uF"); add CPL assertions (Layer is Top, angle in [0,360), no DNP, BOM-expanded refs equal CPL rows); add an `order-notes.txt` (remark under 200 characters plus a limitations list); write the via-in-pad marking-layer fallback into A-069/F12 of the dry-run checklist; use the "validation + false positives + remaining risks" README layout.
- **Check in the JLC preview:** our CPL has a negative Mid Y (-26.0); v4's Y values are positive.
- **Footprint practice:** write a README beside every local footprint (source, licence, datasheet figure/page, pin-1 check). Our `footprints/SOURCES.md` already covers A-083; add the licence line, document number, revision, figure and page, and the pin-1 check for the AHT20.
- **Do not copy:** KiCad 10 files (schematic version 20260306, `${KICAD10_3DMODEL_DIR}` model path; KiCad 9 cannot read them); unverified stock, lifecycle and "Extended" claims; no USB ESD; THERM bias. The v3 source had no reuse licence, so this is internal reference only. Only the BME680 footprint carries CC BY-SA 4.0.
- Rules Emil proposes for his playbook (retro, not applied here): README beside every local footprint; normalise CPL angles and fail the build if BOM and CPL designators differ; group BOM by LCSC code; keep a limitations and false-positive list next to validation results; record the KiCad version of any reference file before copying.

### For the Monday round (proposed, Nora)
| Who | Task |
|---|---|
| Yara | add checks 1-3 above to `fit_check_v3.py`; decide plug width after a test print (Peter work order); re-measure the USB-pocket lip |
| Emil | BOM grouping and CPL assertions in the package script; `order-notes.txt`; check the negative CPL Y in the JLC preview |
| Theo | review the power-path question (TP4056 termination vs awake current, NFR-01/NFR-12) before 4.P3 |

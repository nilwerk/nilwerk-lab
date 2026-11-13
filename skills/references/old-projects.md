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

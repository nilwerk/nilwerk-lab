# Enclosure v3 (4.E3) - slice 1: battery-bay study (answers A-034 with geometry)

Author: Yara (3D Product Designer) · 2026-11-08 · Scope: battery bay only. Board outline, USB-C cut-out, light window, vents, seal and stake wait for 4.P1 (no PCB outline yet).

## Verdict for Arsany (3 lines)
1. **Geometry: yes, the Jauch LP603443JU fits.** The Jauch cell is not bigger: it is 6 mm shorter, 0.2 mm thicker (6.5 vs 6.3 mm) and smaller in volume (10.1 vs 11.1 cm3 envelope). The real change is the bay cavity height, **7.2 mm (EEMB) to 7.4 mm (Jauch)** (6.5 mm cell + 10 % swelling + 0.2 mm clearance, snapped to whole 0.2 mm layers): the module gets only **+0.2 mm taller** (10.4 to 10.6 mm), the same width and **6 mm shorter** (56.2 to 50.2 mm) than the EEMB bay. Usable cavity values for Emil (4.P2): see [pcb-enclosure-bay.md](../docs/interfaces/pcb-enclosure-bay.md).
2. **Printability is the same for both:** 1.6 mm walls, floor and lid (rule >= 1.2 mm), PETG, 0.4 mm nozzle, no supports, both parts fit the P1S by a wide margin.
3. **Open, not geometry:** the 6.5 mm is the DigiKey figure (Jauch's list says 6.0 mm bare cell: ask Jauch for the pack drawing before the bay is frozen); swelling 10 % and 0.3 mm per side are my assumptions; IEC 62133 = NO on this cell is your call (A-034 note), I do not assess it.

## Comparison (all numbers asserted in `test_bay.py`; mm)
| | EEMB 603449 (A-020 bay) | Jauch LP603443JU (A-034) | Delta |
|---|---|---|---|
| Cell L x W x H (input) | 51.0 x 34.5 x 6.3 | 45.0 x 34.5 x 6.5 | -6.0 / 0 / +0.2 |
| Bay cavity L x W x H (usable, contract for 4.P2: pcb-enclosure-bay.md) | 53.0 x 35.1 x 7.2 | 47.0 x 35.1 x 7.4 | -6.0 / 0 / +0.2 |
| Spare around the cell (L total / W total / H) | 2.0 / 0.6 / 0.9 | 2.0 / 0.6 / 0.9 | same |
| Wall / floor / lid | 1.6 / 1.6 / 1.6 | 1.6 / 1.6 / 1.6 | 0 |
| **Bay module outer L x W x H** | **56.2 x 38.3 x 10.4** | **50.2 x 38.3 x 10.6** | **-6.0 / 0 / +0.2** |
| Print orientation | tray open side up, lid flat | same | |
| Overhangs / supports | none (only the bed face points down; tested) | none | |
| Part volume tray + lid, solid PETG (upper bound) | 8.9 cm3, about 11.3 g | 8.1 cm3, about 10.3 g | -1 g |
| Fits P1S 256^3 | yes | yes | |

How the bay height is built: `cell H x (1 + 10 % swelling) + 0.2 mm`, rounded up to 0.2 mm layers: 6.3 gives 7.13 so 7.2; 6.5 gives 7.35 so 7.4. Plan view: 0.3 mm per side (FDM + cell tolerance), 1.0 mm per end (tabs, wire root). The Jauch cell has zero width margin at 34.5 mm, the 0.3 mm per side is what makes it fit.
If the 6.5 mm were really 6.0 mm (Jauch list), the cavity would be 6.8 mm: height drops by 0.6 mm; change `VARIANTS` in `params.py`.

## Printability
- Wall 1.6 mm = 4 perimeters at 0.42 mm line width (3.8 lines): solid, no gap fill needed; the role rule is >= 1.2 mm (3 perimeters). Floor and lid 1.6 mm = 8 layers at 0.2 mm.
- Wire notch (6 x 3 mm) is a U cut open to the top rim: no bridge. Lid is a flat plate. Test `test_no_supports_needed` checks that no downward-facing face is above the bed.
- Not done: Bambu Studio slice (not available here), so print time is **not run**; the grams above are the solid-volume upper bound, an infill-based figure needs a slice.

## What is NOT in this slice (open)
- Lid retention (M2 screws + heat-set inserts) and the NFR-05 seal: they depend on the board outline (4.P1) and add to the outer size; **the outer size above is the bay module only, not the final enclosure**.
- The bay is a stand-alone module. Whether it sits beside or under the PCB is Emil's 4.P2 decision; stacked, only the +0.2 mm matters, side by side the footprint of Jauch is 6 mm shorter.
- Lead wires: 6 mm notch assumed for the 70 mm bare wires; plug/connector type is open (A-034 note, Molex 78172 inferred, unverified).
- Swelling 10 % is an assumption (no vendor figure); Prototype 1 print + a real cell are needed to confirm (standard section 10).
- No physical print, no fit test; Peter work order for Prototype 1 comes with the full enclosure.

## Files
`params.py` all parameters · `bay.py` CadQuery model (`dims()`, `tray()`, `lid()`) · `build.py` exports to `out/<variant>/` (STEP, STL, 3MF per part) · `render.py` renders to `renders/` · `test_bay.py` 17 tests.
Renders (`renders/`): `*_hero.png`, `*_exploded.png`, `*_section.png` per variant and `compare_section.png`. They are real renders of the exported STL meshes with matplotlib (painter's algorithm, so depth sorting of the amber cell envelope in the exploded view has small artefacts); the sections are exact cuts of the meshes.

Run (Python 3.11+): `pip install cadquery trimesh numpy matplotlib networkx pytest`, then `python build.py && python render.py && python -m pytest test_bay.py`.

## Slice 2 list (open work for 4.E3)
**Fusion 360 strategy (standard section 1a).** CadQuery (`params.py`, `bay.py`) stays the source; the STEP files in `out/` import into Fusion 360. Parameter table = the names and values in `params.py` (WALL, FLOOR, LID 1.6; FDM_CLEAR 0.3 per side; SWELL_FRAC 10 %; Z_CLEAR 0.2; END_CLEAR 1.0 per end; wire notch 6 x 3). Body split: `tray` and `lid` are separate bodies per variant; the cell envelope (`cell_ghost`) is a reference body only, not printed. Features Arsany would edit in Fusion: wire notch position and size, outer fillets, later the lid lip and screw bosses. If he exports a changed STEP, that STEP becomes the reference for the version and any divergence from `params.py` is flagged, not overwritten.

**Deliverables A-G (standard section 9), status after slice 1:**
- A Product concept: open (bay study only).
- B Mechanical architecture: open (needs PCB outline 4.P1/4.P2; side-by-side or stacked is Emil's decision).
- C CAD: partly done (parametric source, STEP/STL/3MF per part, dimensions in the table above; Fusion strategy above; board, USB-C, light window, vents, seal, stake missing).
- D Manufacturing: partly done (material, nozzle, walls, orientation, supports; solid-volume upper bound in g). Open: Bambu Studio slice for print time and real material use, infill and layer settings.
- E Assembly: open (screws, heat-set inserts, hardware list, sequence).
- F Cost and business: open (no unit cost, retail price or margin yet).
- G Quality control: open (only geometry tests; no print, no fit test, no Prototype 1).

**Drive export.** Exports belong in Drive `Plant Monitor/04_Builds/Enclosure/v3`. I cannot upload to Drive from this environment, so this is not done; the files exist only in `out/` and `renders/` in git. Someone with Drive access (Lead or Arsany) must copy them, or it moves to the slice that gets Drive access. The committed `out/` files stay in the repo for now (not deleted).

**CI regeneration (Kai).** Add a CI job that installs cadquery/trimesh/numpy/matplotlib/networkx/pytest, runs `build.py`, `render.py` and `test_bay.py`, and fails if `out/` differs from the committed files (or, once Drive is the home for exports, stops committing binaries). Today CI does not run these tests.

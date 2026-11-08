# Enclosure v3 (4.E3) - slice 1: battery-bay study (answers A-034 with geometry)

Author: Yara (3D Product Designer) · 2026-11-08 · Scope: battery bay only. Board outline, USB-C cut-out, light window, vents, seal and stake wait for 4.P1 (no PCB outline yet).

## Verdict for Arsany (3 lines)
1. **Geometry: yes, the Jauch LP603443JU fits.** Open the bay height from 6.3 to **7.4 mm** (6.5 mm cell + 10 % swelling + 0.2 mm clearance, snapped to whole 0.2 mm layers); the enclosure gets only **+0.2 mm taller** (10.4 to 10.6 mm), the same width and **6 mm shorter** (56.2 to 50.2 mm) than the EEMB bay.
2. **Printability is the same for both:** 1.6 mm walls, floor and lid (rule >= 1.2 mm), PETG, 0.4 mm nozzle, no supports, both parts fit the P1S by a wide margin.
3. **Open, not geometry:** the 6.5 mm is the DigiKey figure (Jauch's list says 6.0 mm bare cell: ask Jauch for the pack drawing before the bay is frozen); swelling 10 % and 0.3 mm per side are my assumptions; IEC 62133 = NO on this cell is your call (A-034 note), I do not assess it.

## Comparison (all numbers asserted in `test_bay.py`; mm)
| | EEMB 603449 (A-020 bay) | Jauch LP603443JU (A-034) | Delta |
|---|---|---|---|
| Cell L x W x H (input) | 51.0 x 34.5 x 6.3 | 45.0 x 34.5 x 6.5 | -6.0 / 0 / +0.2 |
| Bay cavity L x W x H | 53.0 x 35.1 x 7.2 | 47.0 x 35.1 x 7.4 | -6.0 / 0 / +0.2 |
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
CI regeneration is not wired yet (Kai).

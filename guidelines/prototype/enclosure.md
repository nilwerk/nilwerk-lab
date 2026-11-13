# Enclosure
- Lock the PCB outline and mounting holes from the Architect's DXF or STEP before any CAD.
- Every dimension lives in `params`; no hard-coded numbers.
- Clearances: wall at least 1.2 mm; sliding fits 0.2–0.4 mm; screw and insert sizes from measured prints.
- Required features: USB-C cut-out, light window, AHT20 vents with baffles, reset pinhole, seal groove, stake.
- Print rules: no supports if possible; orientation noted; PETG 0.4 mm settings; build-volume check for the P1S (see `team/standards/3d-manufacturing.md`).
- Fit-check table regenerated after every parameter change, attached to the PR.
- Run the tolerance coupon before printing the full part; record measured values in the playbook.
- Gate per prototype: watertight STL, geometry QA, fit check, renders, deliverables A–G.

## Source and print checks (from the 3d-printing agent definition)
- Dimensions come from the manufacturer STEP model, a dimensioned drawing, or a measurement. Record units, frame and revision. Never fit precisely from a screenshot.
- Inspect first: existing source, mesh bounds, connector locations, board thickness, protrusions. Prefer parametric source (CadQuery); an STL is a print mesh, not the source.
- Distinguish CAD-verified from physically tested. Never claim a physical fit from software checks. Check shell-to-board, shell-to-shell, cable and neighbour clearances and report the exact values.
- Print meshes: millimetre scale, non-empty, watertight, plausible extents, inside the P1S build volume. Check plate contact, overhangs and bridges.
- Preparing a slicer job never authorises starting a print. A printer is operated only on a separate request (work order for Peter).
- Use the vendored `cadquery`, `print-prep` and `structural-analysis` skills. `print-prep` machine-fit is Prusa-only; use its mesh metrics only.

## Wall and distance checks (from the 14 Nov skills trial)
- Run `skills/vendor/print-prep` `printability.py` on every STL and 3MF export. List every wall it reports under 0.8 mm and answer each one. Verify the real minimum wall by a section through the mesh, including plug side walls and pocket lips, not only the designed values.
- Add a minimum-distance check (not only an overlap check) between each full-height boss and the board outline, threshold at least 1.0 mm.
- State the print orientation of every part in one unambiguous word ("flat on the 13.4 x 8.6 face", not "standing").
- Every structural number carries ASSUMED or SOURCED on each material value. Torque of 0.25 N m is ASSUMED and looks too high for PETG boss annuli: bench-check it.

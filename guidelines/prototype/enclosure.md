# Enclosure
- Lock the PCB outline and mounting holes from the Architect's DXF or STEP before any CAD.
- Every dimension lives in `params`; no hard-coded numbers.
- Clearances: wall at least 1.2 mm; sliding fits 0.2–0.4 mm; screw and insert sizes from measured prints.
- Required features: USB-C cut-out, light window, AHT20 vents with baffles, reset pinhole, seal groove, stake.
- Print rules: no supports if possible; orientation noted; PETG 0.4 mm settings; build-volume check for the P1S (see `team/standards/3d-manufacturing.md`).
- Fit-check table regenerated after every parameter change, attached to the PR.
- Run the tolerance coupon before printing the full part; record measured values in the playbook.
- Gate per prototype: watertight STL, geometry QA, fit check, renders, deliverables A–G.

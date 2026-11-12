# 4.E3 enclosure v3 slice 4 (EXTRA): compact product shell, one soft skin

**What it shows:** the compact enclosure from the parametric CadQuery model, three views rendered from the exported meshes. **Front:** the lid face with the light window and vents. **Three-quarter:** one continuous soft outline with the USB-C window on the right wall. **Side profile:** the tail as the soil stake, from the 14 mm variant; the soil is schematic, the repo has no soil data.

**Size:** outer 97.3 × 56.9 × 12.2 mm, down from 98.1 × 57.7 × 11.6 mm (footprint −2.2 %). **The height is up 0.6 mm** because the J2 connector height is budgeted at the distributor value (5.5 mm) until the datasheet is read. If the datasheet confirms 4.5 mm, the box is 11.2 mm high and 5.5 % smaller by volume. The open point is the J2 height, not the shape.

- Task: 4.E3 slice 4, EXTRA round requested by Arsany 2026-11-12 · PR: #88 (https://github.com/nilwerk/nilwerk-lab/pull/88), stacked on #83 and #74 (merge order #74, #83, #88) · Persona: Yara (3D Product Designer)
- Checks: fit check 50 PASS / 0 FAIL / 6 OPEN for both tail variants; pytest mechanical folder 45 passed (enclosure v3 suite 18 passed)
- Print: tray floor down, lid outer face down; no support for the shell (largest downward reach 1.4 mm). Plain soft edges, no seams except the lid line.
- Agent minutes: about 12.5 min (start 00:09 CET, last check 00:22 CET; final figure in the Agent Log) · Agent's own human-hour estimate: 14 h (CAD rework, checks, renders, skills search, PR)
- Unverified: the J2 height (the budget is used, not the datasheet value); the tail length (the open tail decision, Arsany has not chosen); no Bambu Studio slice, no print, no seal or splash test, no RF measurement; the renders are a rasterised view of the model, not a photo of a print.

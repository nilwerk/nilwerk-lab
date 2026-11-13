# 4.E3 enclosure v3 slice 4 (EXTRA): compact product shell, one soft skin

**What it shows:** the compact enclosure from the parametric CadQuery model, three views rendered from the exported meshes. **Front:** the lid face with the light window and vents. **Three-quarter:** one continuous soft outline with the USB-C window on the right wall. **Side profile:** the tail as the soil stake, drawn with the 14 mm tail length (approved 2026-11-12; the board change to match is pending with the electronics designer). The soil is schematic; the repo has no soil data.

**Size:** outer 97.3 × 56.9 × 12.2 mm, down from 98.1 × 57.7 × 11.6 mm (footprint −2.2 %). **The height is up 0.6 mm** because the J2 connector is budgeted at its listed height of 5.5 mm (a distributor listing; the manufacturer drawing is still to confirm). The USB-C connector is laid flat (edge mount), the approved orientation; its part is still to be picked.

- Task: 4.E3 slice 4, EXTRA round requested by Arsany 2026-11-12 · PR: #88 (https://github.com/nilwerk/nilwerk-lab/pull/88), stacked on #83 and #74 (merge order #74, #83, #88) · Persona: Yara (3D Product Designer)
- Checks (fix round 2): fit check 40 PASS / 0 FAIL / 19 OPEN for both tail variants; the OPEN rows are values still to confirm. Tests run: `pytest -q` in the mechanical folder 56 passed; `test_v3.py` 29 passed. Exports and renders regenerated for this head.
- Print: tray floor down, lid outer face down; no support for the shell (largest downward reach 1.4 mm). Plain soft edges, no seams except the lid line.
- Agent minutes: about 13.5 min for slice 4 (start 00:09 CET, last check 00:23 CET); the fix round is logged separately in the Agent Log · Agent's own human-hour estimate: 14 h (CAD rework, checks, renders, skills search, PR)
- Unverified: the J2 height (listing value, drawing to confirm); the tail length on the board (14 mm approved, board change pending); the PETG wall over the antenna is accepted as a risk, and its RF effect is not measured; no Bambu Studio slice, no print, no seal or splash test; the renders are a rasterised view of the model, not a photo of a print.

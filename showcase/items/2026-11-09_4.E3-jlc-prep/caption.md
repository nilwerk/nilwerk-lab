# 4.E3 JLC dry run: the 4.P2 board outline and footprints, and where they sit in the battery bay

**What it shows:** a 2D top view drawn from the 4.P2 board file (outline 34.5 x 67 mm with the stake tail, pad copper of the 46 placed footprints, 16 vias, the antenna keep-out and the 15 mm clear box). The dashed box is the battery cell cavity (53.0 x 35.1 mm), beside the board with a 5.0 mm gap. **The board is not routed and 9 footprints are placeholders**, so the image shows positions, not a finished layout.

- Task: 4.E3 (3D side of the JLCPCB package, dry run only) · PR: branch `agent/mechanical/4.E3-jlc-prep` · Persona: Yara (3D designer)
- Source: branch `agent/pcb/4.P2` @ `da39d2c` (PR #64, not yet on main), copied unchanged; render made by `projects/plant-monitor/mechanical/jlc_prep/render_top.py`
- Checks: 5 tests passing; the STEP export (217 solids, 1.6 mm board) re-opens in CadQuery 2.8.0 and is valid; fit margins in `jlc_prep/README.md`
- Agent minutes: about 35 min to the PR (21:16 to 21:51 Berlin, measured on the clock; the Lead's Agent Log has the final figure) · Agent's own human-hour estimate: 6 h
- Unverified: KiCad DRC/ERC not run here; the JLCPCB 3D view has not been seen (nothing uploaded); the 0.035 mm copper thickness is a nominal value, not from the repo; the board has no component heights, so no bodies are in the STEP; two source points for Emil (R16 pad angle, antenna-to-cell distance 26.2 vs 28.4 mm).

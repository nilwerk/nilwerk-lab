# 4.E5: printable housing for the v1 function demo (70 x 50 mm perfboard)

**What it shows:** an exploded render of the parametric CadQuery model of a 2-part PETG housing (base + lid, 118.5 x 72.6 x 24.2 mm) for the v1 demo: the perfboard on standoffs (green boxes = parts, heights ASSUMED), a separate LiPo bay (amber), and a lid with two USB-C openings, BOOT/RESET pin guides, a light window, AHT20 vents and a jumper hatch. Real render of the exported model, not a photo of a print.

- Task: 4.E5 (branch `agent/mechanical/4.E5-v1-housing`, stacked on PR #101: merge #101 first) · PR: PR_LINK · Persona: Yara (3D Product Designer)
- Checks run locally: `pytest -q` in `projects/plant-monitor/mechanical` 76 passed (20 new); fit check 15 PASS / 0 FAIL / 35 OPEN. PASS only on measured inputs and team rules; everything resting on a part height, a position from the wiring plan, the SuperMini size or the cell brief value is OPEN.
- Agent minutes: AGENT_MIN (run clock 18:35 to END CET) · Agent's own human-hour estimate: 9 h (parametric model, fit check, tests, 4 renders, README)
- Unverified: all component heights (WIRING typical values), SuperMini 22.5 x 18 mm, USB-C plug opening 14 x 8 mm, LED positions, hole positions from Emil's layout (grid count unverified), LiPo size (A-020 brief, no datasheet read), insert and screw choice, RF effect of the PETG lid. Not sliced, not printed, no fit test; the first print is Prototype 1 and Arsany measures the list in the README.

# 4.E3 slice 5: status sync after A-087 (USB-C flat), A-071 (14 mm tail), A-084 (RF risk accepted)

**What it shows:** the compact enclosure from the parametric CadQuery model in side profile, the tail drawn as the soil stake at the approved 14 mm length (re-rendered; the earlier picture said "open decision"). The model itself did not change: same outer size 97.3 x 56.9 x 12.2 mm, same STL. What changed is the honesty of the paperwork around it. The USB-C connector (J1) is flat / edge-mount (Arsany, 2026-11-13); its height 3.3 mm is still an assumption and the check row stays OPEN until a datasheet height of the part Emil picks exists. The rejected upright version (11.94 mm) no longer appears as an open question.

- Task: 4.E3 slice 5 (branch `agent/mechanical/4.E3-s5`) · PR: #96 (https://github.com/nilwerk/nilwerk-lab/pull/96) · Persona: Yara (3D Product Designer)
- Checks run locally (GitHub Actions is waived until billing is fixed, A-090, so CI was not run): `pytest -q` in `projects/plant-monitor/mechanical` 56 passed; fit check 40 PASS / 0 FAIL / 19 OPEN for both tail variants, same counts as before.
- Cavity basis: J2 (5.5 mm, a distributor listing) sets the 8.6 mm inner height; J1 flat leaves 2.7 mm of air. The 7.6 mm figure is the old J2 4.5 assumption, kept as reference.
- Agent minutes: see the Agent Log (about 25 min run clock) · Agent's own human-hour estimate: 3 h
- Unverified: J1 height (assumed, part not yet picked); J2 height (listing, drawing not read); RF effect of the 1.6 mm PETG wall (risk accepted for the demo, not measured); the board copy in `input/` still has the 25.0 mm tail; no slice, print, seal or splash test; the render is a rasterised view of the model, not a photo of a print.

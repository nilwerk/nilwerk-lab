# 4.E3 enclosure v3 slice 3: the electrode tail in two lengths (14 and 20 mm), drawn from the parametric model

**What it shows:** the 14 mm and 20 mm tail variants (the open tail decision; Arsany has not chosen): the plan of each (lid off) with the enclosure's outer bottom face (red) and the electrode copper (hatched) reaching 14 or 20 mm beyond it, and a side view comparing both with the wall. Both are drawn from the same parameters as the CAD model. **The board tail for each variant does not exist yet**: the board file has 25.0 mm, so the 14 mm variant needs +0.8 mm and the 20 mm variant +6.8 mm (board change for Emil, open).

- Task: 4.E3 slice 3 · PR: #83 (https://github.com/nilwerk/nilwerk-lab/pull/83) (branch `agent/mechanical/4.E3-s3`, stacked on PR #74) · Persona: Yara (3D Product Designer)
- Checks: fit check 47 PASS / 0 FAIL / 6 OPEN for each variant (fix round); pytest mechanical folder 45 passed (enclosure v3 suite 18 passed)
- Agent minutes: about 12 min (run started 07:46 Berlin, PR opened 07:58; final figure in the Agent Log) · Agent's own human-hour estimate: 6 h
- Unverified: J1, U3 and most other heights are still assumed (only the ESP32-C3-MINI-1 height, 2.4 mm, is read from its datasheet); J2 has a conflict (4.5 assumed vs 5.5 from distributors, OPEN); nothing printed, no Bambu Studio slice, no seal or splash test; the tail length itself is Arsany's decision (still open).

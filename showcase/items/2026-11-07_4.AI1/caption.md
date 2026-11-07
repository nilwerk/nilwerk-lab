# 4.AI1 slice 5: wetting labels after decision A-032

**Shows:** how the real Mendeley irrigation data splits into trainable wetting positives (valve watering, rain) and an ignore mask (unexplained wetting, all of sector 5) once Arsany's decision A-032 is encoded.

- Task: 4.AI1 (Model B event labels), PR #13 (nilwerk/nilwerk-lab)
- Persona: Mira (Firmware + Edge AI)
- Agent minutes: see Agent Log (not yet logged); agent's own human-hour estimate: about 5 h
- Real output: plot made from `scripts/run_mendeley.py` on the real dataset (CC BY 4.0, doi 10.17632/c837v6p8ph.2); 250 positives (184 watering, 66 rain), 556 generic wetting events ignored, sector 5 fully ignored. With the final ignore padding of +-4 ticks (Lead decision): 19,334 ignore-mask ticks, 45,274 usable negatives (counts in the plot are events and unchanged).
- Unverified: no model has been trained (4.AI2); counts are data counts, not accuracy. The cause of sector 5's unexplained jumps is unknown. The ignore padding is not part of A-032; 4 was chosen from a contamination check that uses my own proxy.

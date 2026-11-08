# 4.AI2 slice 1: first honest baselines

**Shows:** the average-interval thirst baseline against a constant, on real Mendeley data, for ticks where the soil is not yet dry (MAE in hours per split).

- Task: 4.AI2 slice 1, branch agent/firmware/4.AI2-s1 (PR opened by the Lead)
- Persona: Mira (Firmware + Edge AI)
- Agent minutes: see Agent Log; agent's own human-hour estimate: about 4 h
- Real output from `scripts/run_baselines.py` on CC BY 4.0 data (doi 10.17632/c837v6p8ph.2); report `ml/reports/4.AI2-s1.md`.
- Unverified: no model is trained; the baseline is not good on train/val; val/test have few segments (noisy); event-detection recall 1.00 is circular (labels and detector share the rise rule); sensor_fault is synthetic-only and not evaluated.

# 4.AI2: first real training run of the wetting model, and an honest "not met"

**What it shows:** the first trained edge-AI model (a 3.7 KB int8 network) next to a simple rise rule, on held-out test days of real irrigation data. The shipped int8 model finds 40 % of the 20 scorable wetting events (8/20, 95 % interval 22-61 %) at 0.52 false alerts per unit-week; the float model finds 35 % at 0.00 (the 5-point gap is one event, i.e. noise, not a gain). The target is 95 % at <= 1 false alert per unit-week, so FR-E02 is **not met**. On the left, the red curve is the rule swept over its threshold: at <= 1 false alert per unit-week it finds 0 % (a degenerate threshold, so "0 %" is a weak baseline), but at 9 false alerts per unit-week it finds 30 %, at 25 it finds 80 %. The right panel shows how wide the uncertainty is with 15 / 20 events.

- Image: `model-b-test-recall.png`, reproducible: `python -I ml/scripts/make_showcase_plot.py ml/reports/model-b-wetting-v0.json ml/reports/rule-sweep.json <out.png>` (the sweep comes from `ml/scripts/rule_sweep.py`).
- Task: 4.AI2. PR: link added by the Lead. Persona: Mira (Firmware + Edge AI).
- Size check: flatbuffer 3,664 B of 30 KB measured on the host; RAM 334 B of 20 KB is an estimate. Latency on the chip is not run.
- Agent minutes: 15.1 (measured, original run 07:45-08:02 Europe/Berlin; the review fix round is logged separately). Own human-hour estimate: about 14 h (pipeline, tests, TFLite int8 export, report, data card).

**Still unverified:** everything on the chip (interpreter RAM, latency, 4.AI3); recall on real watering (labels come from a rise rule, so recall measures agreement with the label); Model A has only its baseline evaluated (the dataset has no 24-72 h dry-downs); sensor-fault class not trained. Data licence CC BY 4.0, credit: Adamo et al. (2026), doi:10.17632/c837v6p8ph.2.

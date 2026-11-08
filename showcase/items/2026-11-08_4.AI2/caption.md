# 4.AI2: first real training run of the wetting model, and an honest "not met"

**What it shows:** the first trained edge-AI model (a 3.7 KB int8 network) next to the simple rule it has to beat, on held-out test days of real irrigation data. At the false-alarm budget the product allows (about 1 per unit-week) the model finds 35 % of the 20 scorable wetting events (95 % interval 18-57 %); the target is 95 %, so the requirement FR-E02 is not met yet. The right panel shows how wide the uncertainty is with 15 / 20 events.

- Image: `model-b-test-recall.png` (generated from `projects/plant-monitor/ml/reports/model-b-wetting-v0.json` by a one-off matplotlib snippet; not committed as a script).
- Task: 4.AI2. PR: link added by the Lead. Persona: Mira (Firmware + Edge AI).
- Size check: flatbuffer 3,664 B of 30 KB measured on the host; RAM 334 B of 20 KB is an estimate. Latency on the chip is not run.
- Agent minutes: about 17 (07:45-08:02 Europe/Berlin; Agent Log will hold the measured value). Own human-hour estimate: about 14 h (pipeline, tests, TFLite int8 export, report, data card).

**Still unverified:** everything on the chip (interpreter RAM, latency, 4.AI3); recall on real watering (labels come from a rise rule, so recall measures agreement with the label); Model A has only its baseline evaluated (the dataset has no 24-72 h dry-downs); sensor-fault class not trained.

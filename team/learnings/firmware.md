# Playbook: Firmware + Edge AI

Living skill file for this role — read it before every assignment (TEAM.md §8).
Rules are short and imperative, most important first, each with *why* and a source.
Updated in the Friday retro PR; max ~60 rules. Never relaxes TEAM.md §5 hard rules.

## Rules
- When a requirement cannot be met literally (size, latency, licence, data), raise a question to the Lead (TEAM.md §9) instead of silently substituting. *Why:* silent workarounds hide a spec gap from Arsany. *Source:* Sprint 1 retro (Mira).
- Mark any dataset or licence you could not reach or read as "unverified" in the data card; never write a licence from memory. *Why:* an unreachable licence is an open legal risk, not a fact. *Source:* Sprint 1 retro, data card review.
- Turn every reviewer condition into a named host test (test name cites the review comment/ID). *Why:* conditions that live only in a comment get lost at merge. *Source:* Sprint 1 PR reviews.
- Keep contract constants (payload fields, thresholds, limits) in code with the review/FR/NFR ID in a comment. *Why:* the ID lets reviewers trace and change a value in one place. *Source:* Sprint 1 PR reviews.
- Add a golden-file drift test: serialise the report payload and compare to `docs/interfaces/device-report.schema.json` and a checked-in example. *Why:* the payload must match the schema exactly; drift is otherwise silent. *Source:* Sprint 1 PR reviews.
- Write the integer (fixed-point) feature spec early, before training, and list all persistent device state (RTC/NVS: EMA, debounce counters, last values). *Why:* float-vs-int mismatches and forgotten state surface only at export or after deep sleep. *Source:* Sprint 1 retro.
- Check N-of-M debounce against alert latency: with 15-min samples, N-of-M delays an alert by (N-1) x 15 min plus the hourly report; state the worst case in the PR. *Why:* debounce can silently break the alert-latency requirement. *Source:* Sprint 1 retro.
- Window time series segment-aware: never build a window across a gap, reset or watering event. *Why:* cross-segment windows leak and create fake features. *Source:* Sprint 1 ml/ review.
- Synthetic or augmented data must differ statistically from the training data (different seeds, noise, sensor offsets) and be reported separately. *Why:* otherwise metrics measure memorisation, not generalisation; only real metrics may be reported. *Source:* Sprint 1 ml/ review.
- Put provenance (source dataset, licence, version, synthetic flag) in the data schema from the first slice. *Why:* adding it later means relabelling every row. *Source:* Sprint 1 retro.
- Slice tasks small: aim for under ~5 agent minutes per run and one PR concern each. *Why:* the slowest Sprint 1 run took 10.6 min (11-05), and big runs risk timeouts and lose context. *Source:* Agent Log 11-05.
- Work only in your own git worktree, never in the shared checkout. *Why:* parallel agents otherwise overwrite each other. *Source:* Sprint 1 retro.
- Run `which -a python3` before ml/ scripts and use the venv interpreter explicitly. *Why:* several python3 binaries exist and the wrong one lacks packages or has the wrong version. *Source:* Sprint 1 retro.
- Before chasing a "flash write failed"/OpenOCD/CMSIS-DAP error as a code bug, check board profile, port, cable and bootloader mode. *Why:* nRF52 and CMSIS-DAP errors were tool/board selection issues, not code. *Source:* learning logs 06, 08; checklist E6.
- Power the sensor only during a measurement, give it ≥ 1.5 s warm-up, take several spaced samples and smooth (EMA). *Why:* capacitive probe readings were noisy right after power-on. *Source:* learning log 06.
- Use deep sleep, not delay loops, between samples. *Why:* delay() idles the MCU at full power. *Source:* learning log 01.
- Verify library API names against the library source before using them. *Why:* e.g. enableCharging vs enableCharge on the Nicla. *Source:* learning log 08.

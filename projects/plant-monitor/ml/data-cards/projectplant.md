# Data card: ProjectPlant (evaluation only)

Status: **not downloaded by this task.**

| Field | Value |
|---|---|
| Role in project | indoor sanity check of Model A/B output; metrics reported separately, never mixed into FR-E01/E02 numbers |
| Source URL | https://github.com/jeffschwane/ProjectPlant |
| Version | record the commit id when fetched |
| Licence line | none published (no LICENSE file, no licence text in README), per concept section 3.3. All rights reserved by default |
| Allowed use for us | evaluation only. Do not copy into our repo, do not redistribute, do not ship |
| Format | UTF-16, wide layout (a column group per day, rows per hour), `--` for missing (one file inspected earlier) |
| Known risks | non-contiguous data; no watering log, so wetting labels are weak; sensor % is not our calibration |

## Download steps (Arsany or Peter)

1. `git clone https://github.com/jeffschwane/ProjectPlant projects/plant-monitor/ml/data/projectplant` (inside the gitignored `data/`; do not add it as a submodule).
2. `git -C projects/plant-monitor/ml/data/projectplant rev-parse HEAD` and write the commit id into this card.
3. Re-check whether a licence was added since 2026-11-03; if so, record it.

# Plant Monitor — project-specific lessons

Facts and lessons that only apply to this project. Generic rules go to `team/learnings/<role>.md`.
Added by the Lead from each day's `Lesson:` notes; reviewed in the Friday retro.

- 2026-11-02 · ESP32-C3-MINI-1 replaces the earlier ESP8266 (Q-02) — old soil-sensor code and calibration values are reference only.

## Sprint 1 (Theo)
- NFR-12 lives in one place only; other docs link to it (it was proposed twice).
- A-025 vs NFR-13 conflict was flagged to the Lead, not edited silently; resolve via Arsany.
- Row-count check: expected rows = reporting interval x window (720 vs 2880 mistake, PR #18).
- Postgres tests run as superuser `postgres`; RLS checked with a normal role.

## Sprint 1 (Ines)
- Open thresholds in the acceptance matrix (plausible ranges etc.) are marked [proposed] until Arsany answers; grep "12 months"/"6 months" style numbers across docs after each decision.
- Postgres/RLS test results: read CI job logs for real counts; skipped jobs show green.

## Sprint 1 (Leo)
- T-13 interface differed from assumptions (param name, security mode, export param); the Architect's file is the source, cite file+line.
- Wireframe/doc tables must scroll horizontally at 390px (overflow-x:auto).

## Sprint 1 (Mira)
- Persistent device state to keep across deep sleep (EMA, debounce counters, last values) must be listed in the edge-AI spec; the model is int8 TFLite Micro, so the feature spec is integer too.
- Alert latency (NFR) depends on 15-min sampling plus hourly Wi-Fi report; N-of-M debounce adds (N-1) x 15 min on top.
- Licences of open datasets that the sandbox cannot reach stay "unverified" in the data card until CI or Arsany confirms.

## Sprint 1 (Emil)
- NFR-10 already existed in the architecture docs; new NFR IDs must be grepped first.
- Battery-life target is the single parameter `NFR01_MONTHS`; power-budget doc tables are generated from the script.
- Strapping pins on ESP32-C3-MINI-1 must match `firmware/main/board.h` and the PR pin table.
- Shop hosts (LCSC/JLCPCB) must be requested before the BOM can be called verified; until then stock/price are `unverified`.

## PR/social examples (moved from the playbook)
- Time numbers: "99 min of agent time on 3-5 Nov, without the lead" (measured, day totals 16.2 + 50.0 + 33.0) next to "about 145 working hours of a human without AI" (agents' own estimate) was easy to read as "X times faster"; the report of 5 Nov also shows 103.1 for sprint to date, a different sum.
- Canon drift: the origin canon said parts were ordered on Wed 4 Nov; the daily reports say Tue 3 Nov. Fixed in `showcase/stories/origin/README.md`.
- Counts grow: Saturday 7 Nov had 7 merges in the morning and 10 by 20:46.
- Outdated simulation: the 1 Nov simulation gave a battery life of 150-226 days; the later calculation gives about 4.5 months typical and 1.4 months worst case. Posts must not repeat the old figure.


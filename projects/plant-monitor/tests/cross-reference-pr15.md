# Cross-reference for Theo: lines in PR #15 that must change to match the acceptance matrix

Author: Ines (QA & Test Engineer) · against PR #15 head `c010fe3` · matrix: `acceptance-matrix.md` (this PR). Nothing in PR #15's branch was edited by me. Line numbers are of `projects/plant-monitor/docs/requirements-v1.0-delta.md` unless another file is named.

| # | File : line | Now | Change to | Why |
|---|---|---|---|---|
| 1 | delta : 28 (NFR-12) | `I_sleep_max = TBD` | keep TBD, add "[proposed 50 µA requirement / 25 µA target, pending A-021; SUPERSEDED: A-027 decided 50 µA, target 25 µA (2026-11-06)]" or leave TBD; matrix carries the proposal | A-021 is open; nobody decides the number |
| 2 | delta : 28 (NFR-12, Test column) | `5.2 / 4.P5` | confirm the task ID with Nora; matrix says `5.2, 5.4` | I cannot see the Plan tab |
| 3 | delta : 29 (NFR-13) | acceptance: "rows older than 12 months are absent after the nightly job" | add "rows younger than 12 months are untouched (boundary: 11 months 29 days kept)" and "the pg_cron job exists and last ran OK" | matrix NFR-13 tests both | SUPERSEDED by A-028 (2026-11-06): raw ~3 months, hourly/daily roll-ups 12 months.
| 4 | delta : 27 (FR-D10) | "dry and wet references reads <= 5 points from 0 and 100" | say "a fresh (not the calibration) dry/wet sample of the same soil type" | otherwise the check is circular: calibration points read 0/100 by construction |
| 5 | delta : 27 (FR-D10) | "repeatable per soil type" | add "points stored per soil type" or drop the per-soil-type storage claim; the schema has only one `cal_dry_raw/cal_wet_raw` per device | `db-schema.sql` lines 100-101 hold one pair; matrix row (d) tests two soil types |
| 6 | delta : 12 (FR-D04) | OK (96 samples) | no change; note the 7-day stretch (672 samples) needs more than one 192-sample report | A-017; `device-report.schema.json` maxItems 192 |
| 7 | delta : 14 (FR-D06) | "[hysteresis proposed]" | replace by "(Arsany A-018, 2026-11-05)" | accepted |
| 8 | delta : 16 (FR-A07) | "3 h 10 min" and "5 points" given as terms | state clear points: dry alert clears at >= dry+5, wet clears at <= wet-5; low battery clears at 3.5 V; mark all accepted (A-018) | matrix tests exactly these; `db-schema.sql` 355/362 implement it |
| 9 | delta : 5 (IDs sentence) | "new IDs continue after the proposed v0.2 ones (FR-D08/D09, FR-H01..H03, NFR-10/11)" | add the numbering map: matrix NFR-10 -> NFR-12; matrix NFR-11 (iOS/Android) -> Sec. 7 constraint, not an NFR; calibration -> FR-D10 | one numbering for all documents |
| 10 | delta : 22 (Sec. 7) | OK | no change | matches matrix row "Sec. 7 constraint" |
| 11 | delta : 19 (NFR-01) | "Criterion: ... derated by 20 %" | no change until A-021 is answered; keep "both capacities stated in the report" | formula still open |
| 12 | `docs/interfaces/device-report.schema.json` : 18 | description says `FR-NEW-CAL` | `FR-D10` | stale placeholder ID |
| 13 | `docs/interfaces/README.md` (G1 table) | hysteresis `[proposed]` | accepted (A-018) | same as 7 |
| 14 | `docs/interfaces/db-schema.sql` : 338 | `[proposed]` on hysteresis 5 points / 100 mV | accepted (A-018) | same |
| 15 | `docs/interfaces/db-schema.test.sql` | covers retention and hysteresis | add the FR-A07 dry/wet clear boundary (29.9 % open, 30.0 % closed; 80.1 % open, 80.0 % closed) if not present; add `trigger = reconnect` 96-sample idempotency case for FR-D04 | matrix tests these |
| 16 | `docs/architecture.md` 10.1 (rows NFR-10, NFR-11, FR-D08/D09, FR-H01..H03) | marked "(new, M)" | mark "proposed, no Arsany answer yet" or ask Arsany; matrix will take them in when accepted | only A-016 items are decided |

Not for you: Plan 4.F3 ("7 days") and 4.F4 ("signed images") text are Nora's to correct.
Ines (QA & Test Engineer)

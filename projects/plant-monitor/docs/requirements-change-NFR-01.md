# Requirements change NFR-01 (ready to paste into Requirements v1.0)

Decision: Arsany, 2026-11-08, binding. Record: `docs/adr/ADR-015-nfr-01-flexed-scenario-based-battery-life.md`. The Google Doc is edited by Nora/Arsany, not by the team agents.

## Replace the NFR-01 row with

**NFR-01 Battery life (scenario-based).** With a fully charged 1S LiPo cell and reporting once per hour (sampling every 15 min), the projected battery life per charge is **at least 3 months in the best case and in the typical case**. The **worst case is acceptable as long as it is more than 1 month**. Projected life = 0.8 x rated (minimum) capacity of the fitted cell / measured average current of the scenario, with no self-discharge term in the pass formula. 6 months is a stretch goal for a later version, information only.

Scenarios: best = strong Wi-Fi, no critical wake; typical = ordinary home Wi-Fi, one critical wake per day, 25 C; worst = weak Wi-Fi with retries, cold (0 to 5 C), every current at its measured maximum.

**Measurable pass/fail:** PASS if best >= 2190 h and typical >= 2190 h and worst > 730 h (1 h = 1 hour, 1 month = 730 h). The test report states rated and derated capacity, average current and life for all three scenarios.

**Test method:** current profiles on the assembled board (task 5.4, measurements M1..M6 of `hardware/power-budget/power-budget.md`) per scenario; arithmetic in the report.

## Remove or reword
Any sentence in v0.1/v1.0 that says "battery life >= 6 months", ">= 3 months" as a single figure, or "Measured average current projects >= 6 months".

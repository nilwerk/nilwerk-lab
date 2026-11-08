# ADR-015: NFR-01 flexed: scenario-based battery life

Status: Accepted (owner decision, Arsany, 2026-11-08, binding) · Date: 2026-11-08 · Deciders: Arsany (decision), Theo (record) · Amends: A-020/A-021 (NFR-01 = 3 months for one figure); the formula of A-021 is unchanged

## Context
NFR-01 was a single pass/fail figure: projected life >= 3 months (2190 h) = 0.8 x rated capacity / average current (A-020/A-021). The power budget (`hardware/power-budget/power-budget.md`) shows the estimate spread: best 12.8, typical 4.5, worst-stack 1.4 months for the BOM cell (603449, 1000 mAh minimum). The worst stack puts every parameter at its worst at once; under the single-figure rule it was a permanent FAIL that nobody could design to (R-02). Arsany decided to flex the requirement by scenario.

## Decision
1. **NFR-01 (new wording):** battery life per charge at hourly reporting is **>= 3 months in the best case and in the typical case**; the **worst case is acceptable as long as it is > 1 month**.
2. **Formula unchanged:** life = 0.8 x RATED (minimum) capacity of the fitted cell / average current, literal, no self-discharge term. 3 months = 2190 h, 1 month = 730 h (`HOURS_PER_MONTH` = 730 in `power_budget.py`). The "+SD" line and the 6-month stretch (4380 h) stay information only.
3. **Scenarios** (same three the power budget already uses, `BEST`/`TYPICAL`/`WORST` in `power_budget.py`; measured values from task 5.4 replace the estimates):
   - **Best:** strong Wi-Fi (fast connect, shortest session seen), hub publish as configured, no critical wake, room temperature.
   - **Typical:** ordinary home Wi-Fi, median session of 20, one critical wake per day, 25 C.
   - **Worst:** weak Wi-Fi (longest observed connect and retries), hub unreachable at every report if the hub is on, cold (0 to 5 C), every current at its measured maximum. A stress bound, not a design point.
4. **Pass/fail:** PASS if best >= 2190 h **and** typical >= 2190 h **and** worst > 730 h. Any one failing is a FAIL; the report states all three numbers.
5. **Cell choice:** the verdict still uses the rated minimum of the cell actually fitted.

## Consequences on existing figures (estimates, unverified currents)
| Cell (minimum mAh) | best | typical | worst | NFR-01 new rule |
|---|---|---|---|---|
| EEMB LP603449 (1000) | 12.8 | 4.5 | 1.4 | PASS (worst margin 1.4x over 1 month) |
| Jauch LP603443JU (850) | 10.8 | 3.8 | 1.2 | PASS (worst margin 1.2x, thin) |
| Jauch LP503030JU (430) | 5.5 | 1.9 | 0.6 | **FAIL** (typical < 3, worst < 1); the flex does not rescue it |
The flex only changes the worst-case row. It does not lower the typical-case bar, so cell sizing (A-034) is not relaxed. The worst case being only 1.2 to 1.4x over the new line means the worst-case measurement in 5.4 must be done honestly; a weaker result than the estimate is a real risk (R-02 stays open).

## Alternatives
- Keep one figure of 3 months: worst stack fails forever, R-02 cannot be closed. Replaced by the owner.
- Flex typical as well (>= 1 month): would accept the 430 mAh cell class; not decided, not proposed.

## Follow-ups (owners)
- Requirements v1.0 NFR-01 text: ready-to-paste block in `docs/requirements-change-NFR-01.md`; Nora/Arsany edit the Google Doc.
- `power_budget.py` / `test_power_budget.py` / generated tables still print "vs 2190 h" PASS/FAIL for the worst rows and assert `WORST < NFR01_HOURS`. The numbers are correct; the verdict column for worst rows must use 730 h. Emil adds `NFR01_WORST_MONTHS = 1.0` and the three-scenario verdict in the next power-budget change (not done here: docs-only round).
- Plan sheet NFR-01 wording and 5.4 description: Nora.

## Notes
Both Lead sessions on 2026-11-08 produced a 4.B2 (branch `agent/cloud/4.B2` and PR #45); A-050 keeps #45. Not relevant to this decision.

## Check of A-045 / A-046 (Emil/Theo, answered by Arsany: drop Q2 and R6, no power path) against NFR-12 and the sleep budget
Docs-only check; Emil edits the schematic. Source of both answers: Needs Arsany sheet (the repo does not yet hold the answers).
- **A-045 (permanent battery divider, Q2 + R6 dropped):** the model already assumes a permanent divider in every scenario (`r_divider_mohm` 4 / 2 / 1 MOhm = 0.93 / 1.85 / 3.7 uA at 3.7 V; worst-case whole-board sleep estimate 31.7 uA includes it). Emil's schematic figure is 2.1 uA divider, 21.6 uA typical whole-board sleep. NFR-12 (<= 50 uA): 21.6 uA passes with 2.3x margin and is under the 25 uA design target. Worst-case estimate 31.7 uA is also < 50 uA. NFR-01: typical sleep rises from the model's 13.2 uA to 21.6 uA = +8.4 uA = +0.2 mAh/day on 5.9 mAh/day; typical life about 4.3 months (from 4.5) at 1000 mAh minimum, still >= 3; worst case unchanged (its 31.7 uA already above 21.6). Conclusion: consistent with NFR-12 and NFR-01. Conditions: (1) the divider must keep IO0 below 3.6 V at 4.2 V (A-045's reason: tap = 4.2 x R_low/(R_low+R_high) <= 3.6 V, ratio <= 0.857) and the ADC reading error from the high source impedance is tested in M7; (2) update `power-budget.md` section 4 sleep rows and the `devkit-order-list.md`/BOM notes (Q2 qty 1 -> 0, R6 removed; the strap pull-up count R3-R6 changes) when Emil commits the schematic; BOM line "Q2 now only battery-divider switch" becomes obsolete.
- **A-046 (no power path, TP4056 sees the board load):** NFR-12 and NFR-01 are measured with USB unplugged and the cell as only source, so neither is affected. Sleep load (about 21.6 uA) is far below the TP4056 termination current (46 mA threshold quoted in A-046; 1/10 of the programmed current), but awake bursts (CPU about 25 mA, Wi-Fi 100 mA average, 276 to 335 mA TX peaks) are above it: charge termination can be delayed or the charge LED stay in "charging" while the board is awake with USB plugged. Not a safety issue for the cell (TP4056 still limits voltage and has its timer), but FR-D06 "LED shows distinct states for charging and full" can fail on the bench if the board is awake. Proposed test addition for FR-D06 (Ines, 5.x): "USB plugged, board running its normal duty cycle: charge completes and the LED shows `full` within the expected time". Note in the user documentation: charge is done when the LED shows full, the board needs a cell fitted.
- Verdict: both answers fit NFR-12 and NFR-01; one test gap (FR-D06 with running firmware) flagged. Nothing in the contracts changes.

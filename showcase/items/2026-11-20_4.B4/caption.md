# 4.B4 Cloud analytics: 30/90-day aggregates, watering events, trend, plant comparison

**What it shows:** the analytics logic behind the premium history view, as pure functions with hand-computed test fixtures. For each plant it gives mean, min and max of soil moisture and battery voltage over 30 or 90 days, the number of watering events (a sharp rise in soil moisture), a trend (last week against first week), and a comparison of plants sorted by name. Free users are refused with `premium_required`.

**Evidence:** `test-output.txt` in this folder (11 tests pass). Fast cloud stages: 56 tests pass (23 edge API, 22 export, 11 analytics). A mutation of the watering rule (strict `>` changed to `>=`) makes 4 analytics tests fail; the code was then restored.

**Task:** 4.B4 (Cloud, analytics, premium; FR-P01, FR-P04).
**Persona:** Cloud AI engineer.
**Time block:** start 19:36 · end 19:39 CET (2026-11-20), about 3 agent minutes for the logic, fixtures and tests; the full round is logged in the Agent Log. Human-engineer estimate: about 4 h.

**Not deployed; no live Supabase; no migration.** No endpoint or edge function exists yet. The `/analytics` contract is in `openapi.yaml` and marked as not built. The watering threshold (10 points) and the 2-hour gap limit are proposals still to confirm. Row-level security and the `is_premium()` check are not exercised against a database in this change.

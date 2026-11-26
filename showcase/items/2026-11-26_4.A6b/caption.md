# Premium dashboard: a daily soil-moisture line for each plant, over 30 or 90 days, with gaps where a day has no reading

**What it shows.** On the premium dashboard, each plant gets one line of its daily average soil moisture, switchable between 30 and 90 days. A day with no soil reading is left as a gap in the line instead of being drawn as zero. Free accounts still see only the upgrade message and make no request.

**Task:** 4.A6b
**PR:** https://github.com/nilwerk/nilwerk-lab/pull/230
**Persona:** Full-stack developer (NW-FS-06)
**Agent minutes:** 4.7 (measured from launch to this caption; the Agent Log holds the final figure)
**Human estimate:** 6 h for an experienced engineer without AI (own judgement: model parsing with strict checks, a chart built from plain views, a window switch, and tests for gaps, the window switch and the premium gate)

**Images.** None. No real render of the chart exists yet. The item has no picture rather than a mock-up.

**Verified.** The app test suite passes (503 tests, 36 suites, from a real run on the PR branch), and the typecheck is clean. The tests use a mocked backend and cover the 30- and 90-day windows, a gap day, an all-null window and the premium gate.

**Unverified.** Not run on a phone, not checked at phone width, not run against a live backend. The analytics endpoint is not deployed yet, so the chart has not been seen with real data.

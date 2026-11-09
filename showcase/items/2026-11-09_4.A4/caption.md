# 4.A4 slice 1: plant list with status chips, plant detail with latest values and 7-day chart

**What it shows:** the app's new plant list (OK, Too dry, Low battery, Offline, No sensor yet, each chip with shape + text + the approved status colours), and a plant detail with the latest reading and a 168-bar hourly chart with dry/wet threshold lines. Real screenshots of the web build at 390 px width against the in-memory mock (`plant-list-dark.png` = dark mode). Removing a plant works too (plant-removal warning, typed name, keep or release sensor), not shown.

- Task: 4.A4 (slice 1) · PR: https://github.com/nilwerk/nilwerk-lab/pull/65 · Persona: Leo (Full-stack Developer)
- Requirements: FR-A06, FR-A02, FR-A08 (plant-removal decision), FR-A07 (thresholds drawn), NFR-06. Tests: 98 passing (60 existing + 38 new), typecheck clean.
- Agent minutes: 6.8 (07:45:30 to 07:52:16, wall clock) · Agent's own human-hour estimate: 9 h
- Unverified: the "latest" values (e.g. Cactus "Soil 12 %", Too dry) are mock fixture numbers, not taken from the chart series, so they can disagree with the bars shown; mock backend only (no Supabase, no real readings: the chart is a synthetic sine wave); never run on a phone, only a headless Chrome web build; screen reader behaviour only checked through accessibility labels in tests; gallery (FR-A05), edit plant, export-before-delete not built (a gate before any real backend).

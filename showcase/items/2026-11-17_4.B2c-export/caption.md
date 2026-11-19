# GET /export edge function: JSON + CSV zip, 7-day photo links, only the caller's rows

**What it shows:** the new `export` edge function (task 4.B2c) answers `GET /export?format=json|csv` for the signed-in user only: a JSON document with a top-level `plants` array (what the app client requires) or a ZIP of 8 CSV files, all retained data (not the 7-day free window), photos as 7-day signed links with an absolute `expires_at` so the app can download them before "delete account" unlocks. Evidence: `test-output.txt` (15 export tests, 68 care-tips tests now all run) and `mutation-output.txt` (every mutant of the export logic is caught by a failing test).

- Task: 4.B2c, persona: Sana (Cloud AI Engineer), branch `agent/cloud-ai/4.B2c-export`. Requirements: NFR-07, FR-A01, NFR-06.
- Also fixed (CI hygiene): `cloud/test.sh` ran only 31 of 68 care-tips tests, now runs all test files; the deno lint findings in the tips tests (require-await, no-explicit-any) are fixed in code and CI lint now covers them.
- Unverified: nothing was deployed and nothing ran against a live Supabase project. Storage signing and hosted Auth are stubbed in the tests; the runtime size/time limit for a large export is unknown.
- Agent minutes and the human-hour estimate: see the PR description.

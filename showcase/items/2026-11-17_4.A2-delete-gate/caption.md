# 4.A2: delete-account screen wired to the API, blocked until the data export has run

**What it shows:** the app's "Delete account" screen now calls the deployed `delete-account` edge function through a small tested client, and the red button stays locked until the user has exported their data (JSON or CSV) and typed DELETE. Even if the button's lock were removed by a bug, a guard in the code refuses the call (shown by a test that removes the lock on purpose). Evidence is test output only, no screenshot and no phone.

- Task: 4.A2 follow-up (branch `agent/fullstack/4.A2-delete-gate`, stacked on PR #114: merge #114 first) · Persona: Leo (Full-stack Developer)
- Requirements: FR-A01, NFR-07, NFR-06
- Checks run locally in `projects/plant-monitor/app`: `npx tsc --noEmit` clean; `npx jest` 14 suites, 190 tests passed. Mutation runs: guard removed -> 5 tests fail; export check removed from the gate -> 7 fail; wrong URL (`/account` instead of `delete-account`) -> 1 fails.
- Real finding: the earlier client called `/functions/v1/account`, which does not exist on the deployed project; fixed to `/functions/v1/delete-account`.
- Unverified: never called against the live project (fake fetch only); no phone test; no "skip export" option because the requirements name none (question for Arsany in the PR).

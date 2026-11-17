# 4.A9: the app can now fetch the real data export and hand the file to the user before delete unlocks

**What it shows:** a real client for `GET /export` (JSON or CSV zip) and a file hand-off: the file is written and checked, the phone's share sheet opens (browser download on web), and the user must confirm "Yes, I saved it". Only then does the delete gate count the export as done (no skip option, owner decision A-106; NFR-07). Evidence is test output only (`test-output.txt`), no screenshot, no phone run.

- Task: 4.A9 · Persona: Leo (Full-stack Developer) · Requirements: NFR-07, FR-A01
- Checks run in `projects/plant-monitor/app`: `npx tsc --noEmit` clean; `npx jest` 18 suites, 220 tests passed. Mutation runs: delete URL back to `/account` -> 2 fail; hand-off skipped -> 3 fail; user confirmation ignored -> 2 fail; file size check removed -> 1 fail; empty export body accepted -> 1 fail.
- Also closes QA notes from PR #117: a test for the real `deleteAccount` adapter, README and caption wording, test count.
- Finding: PR #117 was merged into the #114 branch after #114 had reached main, so its code was never on main; this PR carries it.
- Not verified: the cloud has no export function yet (not in the repo, not deployed), so a real build cannot export and delete stays blocked there; the share sheet was not run on a device. New dependencies: `expo-file-system`, `expo-sharing`.

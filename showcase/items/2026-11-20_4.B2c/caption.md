# Export path guard: percent-sign and dot-dot segment tests added

What it shows: the photo export path guard now has tests that refuse a percent sign inside a path segment (encoded traversal included), refuse a plain `..` segment, and accept a normal `<uid>/<plant_id>/<uuid>.<ext>` path. A mutation that lets `%` through the guard makes the new test fail, and the restored guard passes again. Real test output is in `test-output.txt` in this folder.

- Task: 4.B2c (follow-up on the export path guard, NFR-06)
- PR: see the pull request titled `[4.B2c] Path guard segment tests` (branch `agent/cloud-ai/4.B2c-segment-test`)
- Persona: Sana (Cloud AI Engineer)
- Image: none; this item is a text result (test output excerpts), no picture needed
- Agent minutes: about 3 (wall clock, 07:46 to 07:50 Berlin, before commit and PR)
- Own human estimate: about 1 hour for an experienced engineer (read guard and tests, add cases, run the suite, one mutation, PR)
- Unverified: no live Supabase project and no real user token were used (the tests run against a local PostgreSQL 16 and stub Storage). The DB CHECK constraint on `storage_path` is still open and is not part of this item; nothing was written or applied for it. Nothing was deployed.

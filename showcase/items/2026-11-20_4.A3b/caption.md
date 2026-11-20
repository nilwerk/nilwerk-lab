# The remove-plant screen keeps exactly the photos Storage still holds, and the sensor stays claimed

**What it shows:** a screen-level test drives Remove plant with a partial photo delete. The first attempt leaves 2 of 12 photos in Storage, so the screen says "2 photo(s) could not be deleted". The sensor is still linked and nothing is released. The retry sends only those 2 paths, and one still fails, so the screen narrows to "1 photo(s)". The second retry removes it, and the sensor is still not released. Breaking the screen's leftover handling in either of two places makes the test fail.

- Task: 4.A3b (follow-up to the earlier review finding on the photo leftover path), persona: Leo (Full-stack). PR: [4.A3b] Screen-level leftover test, https://github.com/nilwerk/nilwerk-lab/pull/143
- Requirements: NFR-07 (photo objects removed from storage), FR-A08 and A-022 (remove plant; sensor stays claimed until released). FR-A08 and A-022 are now asserted, not only cited.
- Test output: `test-output.txt` in this folder. Full app suite 25 suites, 354 tests passed; `tsc --noEmit` passed.
- Mutations: `mutation-output.txt` in this folder (excerpt of the failing assertions). M1 = `RemovePlantScreen.tsx` line 38 keeps all photo paths instead of `PlantsError.leftover`; M2 = `RemovePlantScreen.tsx` line 67 no longer narrows the retry notice to `PlantsError.leftover`. Under M1 and under M2 the new test fails; the source was restored after each run.
- Agent minutes: 1.3 min wall clock for this fix round (sandbox clock, start to caption write; jest and mutation runs included); the first round is in the PR's Agent Log.
- Human-hour estimate for an experienced engineer without AI: 1.5 h (read the two screens and the fake, write the screen-level test with the partial-delete fake, two mutation runs, outputs).
- Time: start 2026-11-20 07:50:50 CET · end 2026-11-20 07:52:08 CET · agent minutes 1.3 (wall clock, sandbox) · my estimate for an experienced human engineer: 1.5 h.
- Unverified: no phone or simulator run; no live Supabase or backend. The test uses the in-memory plants fake with a wrapped `removePhotoObjects`, not the real storage service. No image is attached: this item is a test result, not a visual.

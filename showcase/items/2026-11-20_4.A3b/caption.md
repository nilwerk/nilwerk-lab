# The remove-plant screen keeps exactly the photos Storage still holds, and a mutation proves a test catches it

**What it shows:** a screen-level test drives Remove plant with a partial photo delete. The first attempt leaves 2 of 12 photos in Storage, so the screen says "2 photo(s) could not be deleted". The retry sends only those 2 paths, and one still fails, so the screen narrows to "1 photo(s)". The second retry removes it. Breaking the screen's leftover handling in either of two places makes the test fail.

- Task: 4.A3b (follow-up to the PR #139 review finding and Ines's mutation note), persona: Leo (Full-stack).
- PR link: see the PR description (`[4.A3b] Screen-level leftover test`).
- Agent minutes and the human-hour estimate: see the PR description.
- Test output: full app suite 25 suites, 354 tests passed; typecheck (`tsc --noEmit`) passed. The new test passes; under each of the two mutations it fails.
- Unverified: no phone or simulator run; no live Supabase or backend. The test uses the in-memory plants fake with a wrapped `removePhotoObjects`, not the real storage service. No image is attached: this item is a test result, not a visual.

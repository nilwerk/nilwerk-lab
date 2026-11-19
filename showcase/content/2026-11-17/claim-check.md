# Claim sources and fiction-vs-fact (for Theo's fact check and Ines's QA)

Task PR-2026-11-17 · Poppy · as of 17 Nov 2026, 22:35 Berlin (fact-check fixes round 17 Nov, late evening) · repo at origin/main 4b61598 (was 75f09d5 at first draft, 91f9b0e during the fix round; main moved on, claims re-read against the PR comments, not against the baseline). PR/comment ids are for checking only; they never appear on images. Types: measured (test output / CI), observed (a reviewer ran it), decision (human), read-from-source, status (state of the repo). "Comment" = the PR comment id on GitHub (`.../pull/<n>#issuecomment-<id>`). No decision ids, customers, leads, prices or private URLs are used.

## 1. Claim-source table (every fact in the pack)

| # | Claim (as used) | Where used | Type | Source |
|---|---|---|---|---|
| F1 | The sensor is DESIGNED to store a new sample every 15 minutes (900 s, a firmware setting, not observed on a device) and the minimum retry gap is also 900 s (Theo C1: "is designed to") | Ep1, video s2 | read-from-source | #122 Theo review, comment 6942024409 (C1); `projects/plant-monitor/firmware/components/upload/` |
| F2 | The guard drops a batch after 3 rejects (400/413) of the same batch, so one bad batch cannot block the buffer | Ep1, video | read-from-source | `nw_upload.h` lines 12-13 and `NW_UPLOAD_POISON_MAX 3` |
| F3 | It could never fire: the counter was keyed on the newest sample (`last_seq`), which changed every 900 s, so it reset to 1 | Ep1 | observed | #122 comments 6942024409 (Theo C1: found it by reading the code), 6942065917 (Ines B1: only QA reproduced it). Wording: "review found it, QA reproduced it"; "review and QA found it" |
| F4 | QA reproduction: 6 consecutive rejects, buffer grew 4 to 10 samples, guard never fired | Ep1, video s3 | observed | #122 comment 6942065917 ("6 consecutive 400s, ring grows 4 -> 10, batch_dropped never set") |
| F5 | The existing 45 deliberate-bug checks (mutants) did not cover it | Ep1, video s5 | observed | comment 6942065917 ("45/45 mutants killed does not cover this") |
| F6 | After the fix (counter keyed on the oldest sample) the 3rd reject drops the batch; 622 checks, 0 failed; 49/49 mutants killed; pipeline green; fixed and re-checked the same morning | Ep1, video s4-5 | observed + measured | #122 comments 6942150671 (QA PASS at b27b1a4), 6942164501 (pipeline green), commit b27b1a4; `showcase/items/2026-11-17_4.F3-slice2/` (622, 49/49); comment timestamps 07:47Z to 07:54Z |
| F7 | Host tests on a PC only: no real HTTP/TLS/Wi-Fi code, no ESP-IDF build of the component, nothing on hardware | Ep1, video s5 | status | caption of `2026-11-17_4.F3-slice2`; comment 6942150671 note 2 |
| F8 | A PR (#117) was merged into the 4.A4 branch (#114) after #114 had reached main, so the delete-account gate never reached main; it arrived through the 4.A9 PR (#123, merged 17 Nov) | Ep2 | status | `showcase/items/2026-11-17_4.A2-delete-gate/caption.md`, `..._4.A9-export-client/caption.md`; commit 37ea62b "carries #117 content that never reached main"; #123 Theo review comment 6942035178 |
| F9 | The earlier client called `/functions/v1/account`, which does not exist on the deployed project; fixed to `/functions/v1/delete-account` | Ep2 | read-from-source | caption `2026-11-17_4.A2-delete-gate` ("Real finding") |
| F10 | Guard, export check and URL are protected by tests that fail if they are removed | Ep2 | measured | captions 4.A2-delete-gate (5/7/1 tests fail) and 4.A9 (QA mutation table, comment 6942088022) |
| F11 | Never run against the live project or a phone; the cloud has no export function yet (not in the repo, not deployed), so a real build cannot export and delete stays blocked | Ep2, Ep5 | status | caption 4.A9; #123 comments 6942035178 (point 3), 6942088022 (note 4) |
| F12 | With the setup flow on, a never-provisioned unit deep-sleeps with no timer before any sensor is read; the v1 defaults turn the setup flow off. Caveat (Theo C3): "setup closed" means BOOT was not held in the 3 s window after reset; the board sleeps unless setup is started with the BOOT button | Ep3 | read-from-source (not observed on hardware) | `projects/plant-monitor/v1/FIRMWARE-BENCH.md` line 21; #116 Theo comment 6941003808 (C2) |
| F13 | CI had never built the v1 option (only the dev-kit default); now a second build with the v1 defaults runs and greps that the option is on | Ep3 | status | #116 Kai comment 6941098780 (gap), `showcase/items/2026-11-17_ci-v1-and-tips` (merged as #120) |
| F14 | 15/15 host tests pass for the v1 option | Ep3 | measured | #116 QA comment 6941047821, Kai 6941098780; `showcase/items/2026-11-17_4.F1-v1-bench/host-tests-output.txt` |
| F15 | UPDATED, now OK (was stale: "not built for the target"): since #120 CI compiles the v1 defaults for the ESP32-C3 (compile only, `build-v1`, `sdkconfig.v1`, grep; CI run 44040644295 green, Ines 6942113557); never flashed and never run on hardware; the bench steps are unrun and written for a human hardware tester (no name, no pronoun). German: "noch nie auf die echte Platine geflasht oder dort ausgeführt" (not "gebaut") | Ep3, Ep5 | status | `.github/workflows/ci.yml` on main; #120; caption `2026-11-17_4.F1-v1-bench` (predates #120, do not quote it for this) ; FIRMWARE-BENCH.md. **Re-check before 20 Nov and 24 Nov** |
| F16 | QA attacked the care-tips filter with 23 cases: 15 passed, 8 failed (3 false-negation, 3 keyword gaps, 2 malformed forecast) | Ep4 | observed | #118 Ines comment 6941053403 ("Passed (15)", "Failed (8)": N-1 x3, N-2 x3, N-3 x2). 15 + 8 = 23 is my count of her two lists (Theo checked the image grid: 15 ticks + 8 crosses = 23; "23" is not in Ines's text, accepted on her two labelled counts) |
| F17 | After the fix all 8 pass; 68 tests; 66/66 mutants killed | Ep4 | observed | #121 Ines comment 6942110546. Note: `showcase/items/2026-11-17_4.B3-slice1b/caption.md` still says 64 tests / 61 mutants (QA note 5): QA's numbers used |
| F18 | Honest limit: still a deny-list; odd phrasings and hidden characters can slip past in live assistant mode; default mode is rule-based and live mode is not switched on; QA recommends an allow-list first | Ep4 | observed | comment 6942110546 (N-2 residual), #118 Theo comment 6941024128 (TIPS_MODE defaults to rule_based) |
| F19 | The filter is checked on every tip, e.g. never "water now" on soaked soil, never "leave it outside" in frost | Ep4 | read-from-source | caption `2026-11-17_4.B3`; comment 6941053403 ("Leave it outside overnight under frost" removed) |
| F20 | CI ran only 31 of the 68 tests (open note, not used on images) | Ep4 doc only | observed | comment 6942163989 (Kai) |
| F21 | The app cannot yet connect to a real sensor: real BLE provisioning not built; a non-mock build shows "needs the full app build" | Ep5 | read-from-source | `projects/plant-monitor/app/README.md` line 32 |
| F22 | Nothing measured on real hardware yet | Ep5 | status | captions 4.F1-v1-bench, 4.F3-slice2 ("nothing ran on hardware") |
| F23 | Tested on a computer with stand-ins (fakes/mocks) | Ep5 | status | captions 4.A9, 4.A2, 4.B3 ("mock", "fake fetch only", "injected stubs") |
| F24 | The founder approved the care-tip safety limits (frost, heat, rain, reading freshness) FOR THE DEMO on 17 Nov; role only in public text | Ep5 | decision (first-hand verified by Theo in the Needs-Arsany sheet, row status Done) | Theo fact check on #127, comment 6961927275 (F24); earlier second-hand: #121 comment 6941988938 point 5. The approval says "for the demo": wording must carry it |
| F25 | Owner decision: no skip option, the export must really reach the user before delete unlocks | Ep5 | decision | caption 4.A9 ("no skip option, owner decision"), #123 comment 6942035178 point 2 |
| F26 | The crew has eleven AI agents (cover says "AI agents", not "engineers": Poppy and Max are not engineers) (Nora, Theo, Ines, Kai, Mira, Leo, Sana, Emil, Yara, Poppy, Max) | cover | status | `showcase/workflow/team-workflow.md` team table; `team/PERSONAS.md` |
| F27 | A human hardware tester exists and is a real person; AI agents are led and reviewed by humans | all | status | `team/PERSONAS.md` (Peter section), TEAM.md, brand kit section 5 |
| F28 | All five events happened on Tue 17 Nov 2026 | cover, all | status | the PR comment timestamps above (07:47Z to 07:55Z) and merges (git log origin/main) |

Not claimed anywhere: battery life, PCB routed, anything printed/built/measured/ordered, prices, speed-ups, "first/best", customers, leads, any statement that the product is available.

## 2. Fiction vs fact (what is invented and what is not)

| Element | Fiction or fact | Notes |
|---|---|---|
| Every speech bubble, crew chat message and sticky note | FICTION (persona voice by Poppy) | dashed border; no numbers inside |
| Slow-burn between Ines and Mira, "green-light crush", map quarrel, "bouncer vs. crasher", "peacekeeper" | FICTION | drama board, character card; light workplace banter only |
| Hobbies and quirks (sourdough starter, jar of coins, maps, club "Tips", names for green builds, picnics, forks) | FICTION | only in `episodes.md` and persona lines; labelled |
| "Pinned" old map, false moustache, cake emoji, wheat field icon | FICTION (visual jokes) | |
| Characters themselves (Nora ... Max) | REAL AI agents, drawn avatars | avatars are team illustrations, not AI-model images, not photos |
| The five engineering events, all numbers, test results, limits (what does not work) | FACT | table 1 |
| The founder's decisions (F24, F25) | FACT, no quotes | role only ("our founder"), no name in public text unless the owner approves it (post-approval list); no invented words or private life |
| Our hardware tester | REAL HUMAN, role name only | no name (needs their OK), no pronoun, no invented reactions, no private life; Ep3/Ep5 mention only that bench steps are written for the tester. Grep of all texts and images for he/his/him/she/her about real people: clean |
| Illustration of the firmware logic (Ep3) | ILLUSTRATION | labelled "illustration of the logic, not a photo or a bench result" |
| Map in Ep2 | SIMPLIFIED DIAGRAM | labelled "drawn by Poppy, simplified" |
| Video sound | CODE-GENERATED | no AI model, no samples; no voice-over yet |
| "Fixed the same morning" | FACT | F6 timestamps; Berlin time is UTC+1 so still morning |

## 3. Checklist for Theo (technical) and Ines (QA)
- [ ] F1-F28 each match their source (open comment ids); especially F16 (15 + 8 = 23 is a sum of two lists, check it), F24 (second-hand), F12 (read from source, not observed).
- [ ] No number inside a dashed element; every image has the fiction chip, the legend and the human-review line.
- [ ] No name of a real human in public text (founder by role); no pronouns for real people; no A-ids, no prices, no customers.
- [ ] German text (posts.md) checked by Theo/Nora, then Arsany.
- [ ] Look at every PNG at phone size (done by Poppy once: no overflow after fixes) and the MP4 with sound (Poppy could not listen).

## 4. Re-check before posting (C8)
"Not built / not run / not yet" claims are statuses as of 17 Nov 2026 and decay: **before Post 3 (20 Nov)** re-read firmware/CI status (F13, F15: compiled in CI since #120, never flashed); **before Post 5 (24 Nov)** re-read app and cloud status (F11, F21, F22: BLE provisioning, cloud export function, photo download before unlock) and the demo approval (F24). Edit or drop any line that changed.

## 5. Fixes round (Theo C1-C8, Ines QA comment 6961966931)
C1 "designed to" (F1) · C2 attribution (F3; images 02, 09, 10) · C3 BOOT caveat (F12) · C4 F15 updated, German "geflasht" · C5 "for the demo" (F24; Post 5, image 06) · C6 dashed bubbles of images 02, 04, 05, 06 and video frames now carry no number or claim (the facts moved to the green boxes); image 03 step 2 is solid green (real) · C7 "AI agents", no task ids in posts, no invented "asked her to show the log" · C8 note above. Also: no pronouns for the tester, alt text for every image, founder by role, footer wrap fixed, baseline updated.

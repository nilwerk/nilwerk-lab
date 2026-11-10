# Claim check: "We caught a mistake: a test that could not fail" (10 Nov 2026)

As of **Tue 10 Nov 2026, 08:40 Berlin** (all five pull requests were open, CI "Final status" success on each head). Types: M measured (a run, QA re-ran where stated), C calculated, E estimated, D decision, F fact of record. PR numbers and comment ids stay in this file, never on images. Recount on the day of posting. Theo checks technical rows; Theo or Nora the German.

Sources: **#74** enclosure v3 (Yara), architect comment 6761332234, QA comment 6761457290; **#73** PCB slice 2 (Emil), architect 6761331963, QA 6761457035; **#72** firmware glue (Mira), architect 6761337589, QA 6761456810, pipeline 6761744983; **#71** app setup flow (Leo), architect 6761331656, QA 6761456517; **#75** delete-account (Sana), architect 6761332464, QA 6761624064. Comment ids are GitHub issue-comment ids on `nilwerk/nilwerk-lab`. Item captions: branches `agent/*`, `showcase/items/2026-11-10_*`.

| # | Claim (as written) | Type | Source | Note |
|---|---|---|---|---|
| 1 | The enclosure check said PASS on all 35 rows | M | QA 6761457290: "35 PASS, 0 FAIL" as shipped (slice-1 board) | ok |
| 2 | QA re-ran the check against the newest board | M | QA 6761457290, own worktree, #73 board copied over the input | ok |
| 3 | "Our QA agent did not trust the green" / "asked: would it ever say anything else?" | persona framing | paraphrase of QA finding 2 (vacuous rows), not a quote | label stays "paraphrase"; no verbatim speech marks |
| 4 | Four of the 35 checks printed the same answer on the old and the new board (rows 2, 16, 17, 18; 26.2 / 28.4 / 21.2 mm and 1.0 mm gap) | M | QA 6761457290 finding 2: rows 2, 16, 17, 18 "print 1.00 / 26.2 / 28.4 / 21.2 mm identically on both boards" | ok |
| 5 | The antenna overhang was typed in as 6.0 mm (`params_v3.py:19`), the real board file says 4.5 mm | M | QA finding 2; PR #74 body "overhang 4.5"; architect 6761332234 | ok |
| 6 | Real gap above the antenna tip is 2.5 mm, not the assumed 1.0 mm | C | QA finding 2 ("With the real 4.5 mm ... 2.5 mm, not 1.0 (Theo's numbers)"), architect: `INNER_Y1 = OVERHANG + 1.0` | ok; Theo to confirm wording |
| 7 | A real clash between the printed tray and a connector shell: 0.686 mm3; QA run 34 PASS / 1 FAIL | M (QA); author's fix | QA row 11 `0.686 mm3`; PR #74 body: "real J1 shell sticks out 0.5 mm past the board edge into the wall; fixed" | QA did not isolate the part ("J1 candidates"); the author's PR names J1; text says "connector shell" |
| 8 | Fixed: the check reads the board file itself; a new test fails if the stored copy of the board differs from the design; checked by a negative run | F (author) | PR #74 body ("board copy must match SOURCE.txt and `origin/agent/pcb/4.P2-s2` (fails on drift, verified by a negative run)"), commit b98bd69 | negative run is the author's statement, not re-run by QA yet |
| 9 | After the fix 35 PASS / 0 FAIL, 8 tests pass | M (author) | PR #74 body "35 PASS, 0 FAIL; pytest 8 passed"; CI `mechanical` success on b98bd69 | **QA has not re-run after the fix round** (verdict 6761457290 is on the older head a405f53); slides say "author's run" |
| 10 | Inner space 93.3 x 52.7 x 7.6 mm; plan render from the real model | C | PR #74 body; `showcase/items/2026-11-10_4.E3-s2/caption.md`; image regenerated in b98bd69 | heights ASSUMED (caption, architect "ASSUMED heights"); render is matplotlib from the STL, not a photo |
| 11 | Nothing printed, no seal test | F | caption "Unverified"; PR #74 "Not done: print, Bambu slice, seal test" | ok |
| 12 | A placeholder switch would have wired a signal straight to ground | F (author) | PR #73 body "slice-1 switch placeholder shorted signal to GND (terminals A-B and C-D are joined inside the XKB switch)" | "would have": no board was built; the PR says "check with a meter on the first sample" |
| 13 | 16 vias sat inside solder pads, now 0 | M | PR #73 body; QA 6761457035 "Via-in-pad count 0: confirmed", 16 `(via` entries, 0 in pads | ok |
| 14 | The antenna keep-out is checked in CI | F | PR #73 "Layout checks" step in the `pcb` job; pipeline comment on #73 (6761744703) | CI green on b2e211f |
| 15 | The start-up pin cannot be a "hold at power-up" button | F | PR #72 "Findings" 1 ("IO9 is the boot strap; low at reset means ROM download mode"); architect 6761337589 "a real design mismatch" | found while writing, before any board exists; design decision still open (not in this post) |
| 16 | Firmware glue code written without a compiler, compiled in CI after two fixes, nothing ran on a board | F | PR #72 commits 06:51 (uncompiled), 06:56 "fix IDF 5.4 pointer-sign error", 07:01 "larger single-app partition"; CI `firmware` success on c4da8ca; QA 6761456810 | "after two fixes" = two follow-up commits; whether the first CI run failed was not read from the run log |
| 17 | A name was checked trimmed but sent untrimmed; found by deliberately breaking the code (mutation testing) | M | QA 6761456517 mutation table, finding 1; fix commit 07:28 "QA fix: NameStep sends the validated trimmed name" | ok; 6 of 11 QA mutants had survived (not quoted in the post) |
| 18 | Delete-account: all 41 deliberate bugs (mutants) in the suite caught, 13 of them new | M | QA 6761624064 "mutants: 41, survived: 0"; PR #75 "13 new mutants" | 41 = 28 existing + 13 new; 2 further candidates were dropped as equivalent/unreachable (PR body) |
| 19 | Tests use a local PostgreSQL, not real Supabase | F | PR #75 "Not verified: real Supabase ... NOT run"; caption | ok |
| 20 | All five changes have an architect review and a QA verdict on record (one of them a FAIL) | F | the ten comments listed above | ok; #74's FAIL is on the older head |
| 21 | None of the five is merged; five pull requests open; CI green on all five heads | C | `gh api repos/nilwerk/nilwerk-lab/pulls/{71..75}` state open, merged false; check-runs "Final status" success, 10 Nov 08:39 Berlin | **recount on the day**; #74 is a draft PR stacked on #70/#73 |
| 22 | About 100 agent minutes today | E | Lead's rough figure in the task brief of 10 Nov | **not in the Agent Log yet**; replace with the logged sum or cut the tile |
| 23 | Nothing is printed, ordered or run on a board | F | captions and PR bodies (#72, #73, #74) | ok |
| 24 | "A human decides" / "that is Arsany's call" | D | TEAM.md section 4 and 5 (Arsany merges) | ok |

Cut on purpose: any price, the via-in-pad decision option and its cost (a decision for Arsany), decision ids, the button-pin design question and the 5-minute vs 3-minute question (open owner decisions), human-hour estimates (agents' own guesses, not needed here), "first/best/fastest".

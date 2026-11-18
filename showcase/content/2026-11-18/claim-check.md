# Claim check, content pack 2026-11-18 (for Theo's fact check and Ines's QA)

Task PR-2026-11-18 · Poppy (PR & Social) · as of 18 Nov 2026, 08:20 Berlin · repo base origin/main 4b61598; PR heads read: #132 `8a72ff8`, #133 `604ecea`. PR/comment ids are for checking only and never go on an image. Types: measured (test/CI output), observed (a reviewer ran it), read-from-source, status (state of repo/PR), decision. Comment ids are GitHub issue-comment ids on the named PR.

**Not for posting before PR #131 is merged and Arsany approves.**

## 1. Post 1: "delete must first give me ALL my data, photos included" (PR #133, 4.A9b)

| # | Claim (as used) | Type | Source |
|---|---|---|---|
| C1 | The delete button stays locked until the export has run; it opens only when the export is complete | read-from-source + observed | #133 Theo 6971592801 ("Gate semantics"), QA 6971773511 ("Can delete unlock wrongly?": only `complete: true` is JSON after downloads, zero-photo guard, ZIP and confirmed hand-off) |
| C2 | The earlier export only linked the photos (signed URLs, valid 7 days) | read-from-source | `showcase/items/2026-11-18_4.A9b/caption.md` (branch `agent/fullstack/4.A9b-photo-export`); #130 Theo 6961986230 (point 4) |
| C3 | The app now downloads each photo behind the links, packs `export.json` + photos into one ZIP, hands it to the user, then opens delete | read-from-source | caption 4.A9b; Theo 6971592801 |
| C4 | If one photo fails: nothing handed over/saved, delete stays locked, message says how many failed and to try again | observed | QA 6971773511 ("C1 copy: fixed ... Nothing was saved to your device and delete stays locked"; test iterates 7 error cases); caption |
| C5 | A CSV export alone never unlocks delete, because it only links the photos | observed | Theo 6971592801 finding 4; QA 6971773511 (M3/M4/M5/M6 each fail a test) |
| C6 | Photos listed but none saved: export fails; photo URLs must point to the app's own storage host and bucket path; 150 MB cap | observed | QA 6971773511 (C2 guard fixed, size cap 150 MB pre-flight, path pin done) |
| C7 | A review caught an error text saying "your data arrived" when nothing was saved; changed to say what happened | observed | Theo 6971592801 finding 1; QA 6971773511 ("C1 copy: fixed") |
| C8 | 287 app tests pass; 220 on main before (67 new); type check clean | measured | QA 6971773511 (re-run: 21 suites, 287 passed; main: 18 suites, 220); `test-output.txt` in the item |
| C9 | 11 deliberate-bug mutations in the author's run, all caught by failing tests | measured | `mutation-output.txt` in the item: labels a, b, b2, c, d, e, f (round 1) and g, h, i, j (round 2) = 11 (caption says "7 in round 1, 4 more after review") |
| C10 | QA's own mutation rows: 14 rows (M1 to M16, three rows merge M1/M2/M16), none survived | observed | QA 6971773511 table. **Note:** the figure "14/14" is rows of that table; counted by mutation number it is 16 of 16. Say "14 mutation rows" as in the text |
| C11 | CI green at head 604ecea (run 44256542043, 18 Nov 07:11 Berlin) | measured | Kai 6971810146 |
| C12 | Not run on a phone or simulator; not run against a deployed export function; PR #130 (server export) not merged or deployed | status | caption 4.A9b "Unverified"; QA 6971773511 note 2; #130 QA 6962373305 (`list_edge_functions`: no `export`); #130 open at the as-of time |
| C13 | 150 MB cap not measured on a device; archive built in memory so a huge library may run out of memory, failure is safe (delete stays locked) | observed | caption "Unverified"; Theo 6971592801 finding 5; QA 6971773511 note 2 |
| C14 | PR open, not merged (as of 18 Nov 08:20 Berlin) | status | GitHub API `pulls/133`: state open, merged false |
| C15 | "Our reviewing AI agent" = Theo (architecture review); QA agent re-ran tests | read-from-source | #133 comments 6971592801, 6971773511. Roles only in the text |

## 2. Post 2: "one setup code per sensor, never in the repo" (PR #132, 4.F2b)

| # | Claim (as used) | Type | Source |
|---|---|---|---|
| C16 | Each sensor gets its own setup code printed on its label (8 characters, Crockford base32, 40 bits) | read-from-source | `projects/plant-monitor/firmware/tools/nw_sec2_gen.py` docstring and `POP_LEN = 8` (branch `agent/firmware/4.F2b-provision`); Theo 6971619848 ("label `NW1:<hw_id>:<pop>`, 8-char Crockford PoP (40 bit)") |
| C17 | The sensor never stores the label code, only a derived check value (salt + SRP verifier, 3072-bit group, SHA-512, 16-byte salt) | read-from-source | `nw_sec2_gen.py` docstring ("The PoP printed on the unit label is NOT stored on the device"), `SALT_LEN = 16`, `VER_LEN = 384` |
| C18 | The tool writes secrets only outside any git folder, refuses to write inside one, files readable by the owner only (0600), never overwrites a prepared unit | observed | Theo 6971619848 ("Secrets"); QA 6971762756 (hand run: modes `-rw-------`, second `gen` refused, `--out` in repo refused, dir not created) |
| C19 | No per-unit file is committed; the only code-shaped strings in the tree are the public contract example and test values | observed | Theo 6971619848 (`git ls-files` check); QA 6971762756 (`git status --short` clean after runs) |
| C20 | If the setup data is missing, wrong size or all zeros, the sensor does not start Bluetooth setup; no default code anywhere | observed | Theo 6971619848 ("Fail closed", "No default PoP anywhere"); PR #132 body (validator) |
| C21 | The verifier matches an independent library (pysrp 1.0.22) | observed | Theo 6971619848 (match, NG_CUSTOM); QA 6971762756 ("ok matches pysrp ... "), `showcase/items/2026-11-18_4.F2b/caption.md` |
| C22 | 22 of 22 host tests pass (66 s) | measured | QA 6971762756 (`ctest`: 22/22 passed, 66 s); Theo 6971619848 (22/22); PR #132 body |
| C23 | 29 mutants caught in the author's run | measured | PR #132 body ("Host tests 22/22, 29/29 mutants"); caption ("mutation checks (29 mutants) pass") |
| C24 | QA's own mutations: 16 of 17 caught (10 of 11 on the tool + 6 of 6 on the validator); the survivor (`O_EXCL` removed) is an equivalent mutant because a separate "files already exist" check still refuses | observed | QA 6971762756 (10 of 11 killed; 6 of 6 killed). 10+6 = 16 and 11+6 = 17 are my sums |
| C25 | CI green at head 8a72ff8 (run 44256686792, 18 Nov 07:14 Berlin) | measured | Kai 6971809633. **Note:** that run's firmware job built the ESP-IDF firmware, but the item caption and QA still list the ESP-IDF build of the *setup configuration* (`sdkconfig.defaults.setup`) as unverified; the text says only "no board, no real handshake, no flash step, bench procedure not run", and does not claim the setup build |
| C26 | Not verified: no board, no real Bluetooth handshake, no flashing, the hardware tester's bench procedure not run | status | caption 4.F2b "Unverified"; QA 6971762756 ("Not run by me") |
| C27 | Known open risk: the check value is stored unencrypted, so a flash dump allows an offline guess of the 40-bit code; accepted for the prototype and still open; where the code list is kept long term is open | observed | procedure s7 (Q-H6) as quoted in Theo 6971619848 ("open risk ... stated in procedure s7"), N4; QA 6971762756 (C3b NOT DONE, N4 not seen). Owner decision ids are not named in the text |
| C28 | Must merge after PR #129 | status | procedure header "Merge order (hard): #129 first" (QA 6971762756 C4 FIXED); PR #132 body |
| C29 | PR open, not merged (as of 18 Nov 08:20 Berlin) | status | GitHub API `pulls/132`: state open, merged false |

## 3. Rules check

| Check | Result |
|---|---|
| Humans | Roles only: "hardware tester", "our reviewing AI agent", "QA". No human name, no "hardware integrator" (A-095). AI agent names not used |
| Superlatives, "X times faster" | none; no time or human-hour figure used in the posts |
| Status words | "prototype", "not verified", "open, not merged" present in both posts, both languages |
| Numbers only as in the PRs | 287, 220, 67, 11, 14 rows, 150 MB, 7 days, 22/22, 66 s, 29, 16 of 17 (10/11 + 6/6), 8 chars/40 bit, 16-byte salt, 3072-bit: each has a row above |
| Confidential | no price, lead, Needs-Arsany content, A-xxx/Q-xx ids, procurement, private repo URL, secret or real per-unit value; the example code from the contract is NOT quoted |
| Not found in the PRs | "14/14 and 16/17" were requested in the brief: 16/17 = QA's 10/11 + 6/6 on #132 (C24); 14 = rows of QA's table on #133 (C10). 14/14 and 16/17 do not appear literally anywhere, so the text says what each is made of |
| Evidence is test/CI output only | no screenshot or photo exists; no image drafted |

## 4. Re-check on the day of posting

Recount: PR states (#129, #130, #131, #132, #133), CI heads, 287 tests, 22 host tests. Re-read the "Not verified" sentences against the merged state and any hardware or phone run before 20 Nov (nothing in this pack should claim a phone or board run unless a work order result exists).

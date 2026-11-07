# Claim check 2026-11-07 (every number and statement in `posts.md` and the images)

Types: **M** measured/test result, **C** calculated from a datasheet formula, **S** simulated/modelled, **E** estimate, **D** fact of record. Sources are repo paths (private repo, no URLs) plus PR numbers and dates. Checked by Poppy; **Theo to confirm the technical rows marked (T)**.

## Post 1: R9 charger resistor

| # | Claim in post / image | Type | Source | Status |
|---|---|---|---|---|
| 1 | R9 sets the charge current of the 1000 mAh cell | D | `projects/plant-monitor/hardware/bom/bom-draft.md`, section "R9: charger programming resistor" | ok |
| 2 | "First parts-list draft" had R9 = 1.2 kOhm, "about 0.9 A" (image: ~0.9 A, about 0.9C) | C | bom-draft.md row "R9 wrong for a 1000 mAh cell (1.2k = about 0.9 A)"; 0.9 A / 1000 mAh = 0.9C | ok. Poppy re-derived: 1100 / 1.2 kOhm = 917 mA. (T) see note A |
| 3 | The mistake was flagged in review by our reviewing AI agent (Theo) | D | `team/reports/2026-11-06.md`, Extra round, Theo reviews: "R9 charger resistor error"; BOM doc "What changed" table, G2 condition | ok |
| 4 | R9 now 2.4 kOhm = 458 mA = 0.46C | C | bom-draft.md "R9": "R9 = 2.4 kOhm (C22940), 458 mA = 0.46C"; 1100 / 2.4 kOhm = 458.3 mA | ok (T) |
| 5 | Worst case 527 mA with +15 % tolerance | C | bom-draft.md: "+15 % current tolerance ... worst case 527 mA = 0.53C"; 458 x 1.15 = 527 | ok |
| 6 | "gentle 0.5C we want" | D | bom-draft.md: nominal target "about 0.5C of a 1000 mAh cell" (Exact 1100 / 500 mA) | ok |
| 7 | Formula R = 1100 / I is from the charger datasheet | C | bom-draft.md cites "formula from the TP4056 datasheet (section R9)" | (T) see note A |
| 8 | Nothing had been ordered | D | bom-draft.md header: "Nothing was ordered or bought" | ok |
| 9 | PCB agent (Emil) redid the sum | D | commit db782c5 "[2.5] BOM follow-up: R9 ..." (PR #30), persona Emil | ok |
| 10 | Calculated, not yet measured; still has to be checked on a real board (no promise of who or when) | D | bom-draft.md "thermal and cell-temperature behaviour in 4.P1" still open | ok (fix round C3) |
| 11 | "AI agents, led and reviewed by humans" (one wording everywhere; every change is approved by a person) | D | TEAM.md sections 4, 5, 12 (Arsany merges every PR) | ok |
| 12 | "cost one line in a spreadsheet, not a board respin" | D (framing) | no board was ordered (see 8) | ok, rhetorical, no number |
| 13 | (two-layer round) "A tiny part decides how fast the battery charges"; "much gentler charge" (2.4 vs 1.2 kOhm = about half the current) | C | bom-draft.md R9 section; 1100 / 2.4k = 458 mA vs about 0.9 A | ok |
| 14 | "For engineers" paragraph: R9 programs the charge current of the TP4056; 0.53C worst case (527 / 1000) ; open items: thermal and cell-temperature behaviour, datasheet edition | C / D | bom-draft.md "R9" section and open column of the "What changed" table; claim note A | ok (T) |
| 15 | Image intro "Our reviewing AI agent flagged the wrong value"; footer wording "AI agents, led and reviewed by humans" used everywhere (Ines N2) | D | row 3; TEAM.md section 4 | ok |

**Note A (formula confirmed by Ines; Theo keeps sign-off):** the agents' formula is R = 1100 / I. Ines (QA comment on PR #33) read the TP4056 datasheet REV_2.4: IBAT = (VPROG / RPROG) x 1100, so 1.2 kOhm gives 900 mA and 2.2 kOhm gives 425 / 500 / 575 mA (min / typ / max, +-15 %). This matches the figures in the posts (about 0.9 A before, 458 mA after, 527 mA worst case). Earlier worry (vendor tables with about 1200 / R) is resolved by the REV_2.4 reading; datasheet editions differ, so the post says "charger datasheet" and stays **calculated, not measured**. Theo still signs off the technical statements; if any figure changes, edit `build_images.py` and rerun.

## Post 2: row-level security proof

| # | Claim | Type | Source | Status |
|---|---|---|---|---|
| 1 | Test creates user A and B and tries read, change, delete, forged insert | M | `showcase/items/2026-11-07_4.B1/test-output.txt` (RLS isolation section: "read ok", "write ok", "forged inserts refused on all 14 tables") | ok |
| 2 | RLS on all 14 tables | M | test-output.txt: "RLS enabled on all 14 public tables" | ok |
| 3 | A sees 0 foreign rows | M | test-output.txt: "A sees N own, 0 foreign" for 11 tables; 3 service-only tables "A sees 0" | ok |
| 4 | Changes and deletes touch 0 of B's rows; forged inserts rejected (wording per fix round C4: not "every write refused") | M | test-output.txt: 14 lines "A cannot update/delete B rows" + "forged inserts refused on all 14 tables"; final "RLS ISOLATION OK" | ok |
| 5 | Local PostgreSQL 16 | M | test-output.txt: "PostgreSQL 16.15" | ok |
| 6 | Raw readings kept 3 months, hourly roll-ups 12 months | D + M | showcase item caption 4.B1 ("3-month raw / 12-month roll-up retention works"); test-output.txt "RETENTION OK" | ok |
| 7 | Not yet on a real Supabase project; login identity (auth), scheduler and file storage stubbed or skipped locally | D | caption 4.B1 "Unverified"; test-output.txt NOTICEs "pg_cron not available", "storage schema not present" | ok |
| 8 | "backend agent just wrote the first version" | D | task 4.B1, PR #29 (merged), persona Sana (Cloud AI) | ok |
| 9 | 14 tables = "all tables of our own database schema" | M | "RLS enabled on all 14 public tables" (public schema only) | wording fixed in round C4 (no "every table") |
| 10 | Review and approval statement | D | TEAM.md sections 4, 5 | ok |
| 11 | (two-layer round) Image intro and text: "tested all 14 tables of our schema" (Ines N1) | M | test-output.txt "RLS enabled on all 14 public tables" | ok |
| 12 | "For engineers": A sees 0 foreign rows on every table; forged-insert check passes on all 14; retention test covers roll-up and cleanup; schema contract test passes on the migrated database | M | test-output.txt: 14 "read ok" lines, "forged inserts refused on all 14 tables", "apply_retention #1 -> rolled_up 1, raw_deleted 5, hourly_deleted 1", "ALL OK" | ok |
| 13 | Not covered yet: real Supabase auth, pg_cron schedules, storage buckets | D | test-output.txt NOTICEs "pg_cron not available", "storage schema not present"; caption 4.B1 "auth.uid() ... stubbed" | ok |

## Not used, and why

- "24 mutation tests" (Lead's suggestion): could not find this number in the repo; the repo reports "5 mutations caught" for the retention work (`team/reports/2026-11-06.md`) and "mutation-checked" in `projects/plant-monitor/docs/interfaces/README.md`. Add the exact count only after Ines or Theo confirms it.
- "A reviewer agent found a stale 6-month battery target": the repo shows the stale 6-month text was removed after the owner's 3-month decision (commit 3e03dfd, PR #30), not that a reviewer found it. Not claimed as a review catch. Used in the calendar as a myth-versus-proof topic instead.
- Agent minutes and human-hour equivalents: the Agent Log was not readable from this task, so no time figures are in these posts (each would be labelled "estimate").

## Estimated vs measured, at a glance

Post 1: all figures **calculated** (datasheet formula), no bench measurement. Post 2: all figures **measured test results** on a **local** PostgreSQL 16, not on the live system.

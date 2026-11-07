# Claim check 2026-11-07 (every number and statement in `posts.md` and the images)

Types: **M** measured/test result, **C** calculated from a datasheet formula, **S** simulated/modelled, **E** estimate, **D** fact of record. Sources are repo paths (private repo, no URLs) plus PR numbers and dates. Checked by Poppy; **Theo to confirm the technical rows marked (T)**.

## Post 1: R9 charger resistor

| # | Claim in post / image | Type | Source | Status |
|---|---|---|---|---|
| 1 | R9 sets the charge current of the 1000 mAh cell | D | `projects/plant-monitor/hardware/bom/bom-draft.md`, section "R9: charger programming resistor" | ok |
| 2 | First BOM had R9 = 1.2 kOhm, "about 0.9 A" (image: ~0.9 A, about 0.9C) | C | bom-draft.md row "R9 wrong for a 1000 mAh cell (1.2k = about 0.9 A)"; 0.9 A / 1000 mAh = 0.9C | ok. Poppy re-derived: 1100 / 1.2 kOhm = 917 mA. (T) see note A |
| 3 | The mistake was flagged in review | D | `team/reports/2026-11-06.md`, Extra round, Theo reviews: "R9 charger resistor error"; BOM doc "What changed" table, G2 condition | ok |
| 4 | R9 now 2.4 kOhm = 458 mA = 0.46C | C | bom-draft.md "R9": "R9 = 2.4 kOhm (C22940), 458 mA = 0.46C"; 1100 / 2.4 kOhm = 458.3 mA | ok (T) |
| 5 | Worst case 527 mA with +15 % tolerance | C | bom-draft.md: "+15 % current tolerance ... worst case 527 mA = 0.53C"; 458 x 1.15 = 527 | ok |
| 6 | "gentle 0.5C we want" | D | bom-draft.md: nominal target "about 0.5C of a 1000 mAh cell" (Exact 1100 / 500 mA) | ok |
| 7 | Formula R = 1100 / I is from the charger datasheet | C | bom-draft.md cites "formula from the TP4056 datasheet (section R9)" | (T) see note A |
| 8 | Nothing had been ordered | D | bom-draft.md header: "Nothing was ordered or bought" | ok |
| 9 | PCB agent (Emil) redid the sum | D | commit db782c5 "[2.5] BOM follow-up: R9 ..." (PR #30), persona Emil | ok |
| 10 | Not yet measured; hardware integrator will test on the real board | D | bom-draft.md "thermal and cell-temperature behaviour in 4.P1" still open; TEAM.md section 12 | ok |
| 11 | AI agents led and reviewed by a human engineer who approves every change | D | TEAM.md sections 4, 5, 12 (Arsany merges every PR) | ok |
| 12 | "cost one line in a spreadsheet, not a board respin" | D (framing) | no board was ordered (see 8) | ok, rhetorical, no number |

**Note A (open, for Theo):** the agents' formula is R = 1100 / I. Common TP4056 vendor tables read about 1.2 kOhm = 1 A and 2.0 kOhm ~ 0.58 A (roughly 1200 / R), i.e. 2.4 kOhm would be about 0.5 A. Datasheet editions differ. Either reading keeps the new value well below 1C and above the old one by 2x, so the story holds, but the exact figures 458 / 527 mA and "~0.9 A" should be confirmed against the datasheet edition in the BOM before this goes out. If they change, rebuild the image (edit `build_images.py`).

## Post 2: row-level security proof

| # | Claim | Type | Source | Status |
|---|---|---|---|---|
| 1 | Test creates user A and B and tries read, change, delete, forged insert | M | `showcase/items/2026-11-07_4.B1/test-output.txt` (RLS isolation section: "read ok", "write ok", "forged inserts refused on all 14 tables") | ok |
| 2 | RLS on all 14 tables | M | test-output.txt: "RLS enabled on all 14 public tables" | ok |
| 3 | A sees 0 foreign rows | M | test-output.txt: "A sees N own, 0 foreign" for 11 tables; 3 service-only tables "A sees 0" | ok |
| 4 | Every write against B's data refused | M | test-output.txt: 14 lines "A cannot update/delete B rows" + "forged inserts refused on all 14 tables"; final "RLS ISOLATION OK" | ok |
| 5 | Local PostgreSQL 16 | M | test-output.txt: "PostgreSQL 16.15" | ok |
| 6 | Raw readings kept 3 months, hourly roll-ups 12 months | D + M | showcase item caption 4.B1 ("3-month raw / 12-month roll-up retention works"); test-output.txt "RETENTION OK" | ok |
| 7 | Not yet on a real Supabase project; scheduler and storage stubbed locally | D | caption 4.B1 "Unverified"; test-output.txt NOTICEs "pg_cron not available", "storage schema not present" | ok |
| 8 | "backend agent just wrote the first version" | D | task 4.B1, PR #29 (merged), persona Sana (Cloud AI) | ok |
| 9 | 14 tables is "every table in the schema" | M | "RLS enabled on all 14 public tables" (public schema only) | wording: "every table" is safe for the public schema; fine for the post |
| 10 | Review and approval statement | D | TEAM.md sections 4, 5 | ok |

## Not used, and why

- "24 mutation tests" (Lead's suggestion): could not find this number in the repo; the repo reports "5 mutations caught" for the retention work (`team/reports/2026-11-06.md`) and "mutation-checked" in `projects/plant-monitor/docs/interfaces/README.md`. Add the exact count only after Ines or Theo confirms it.
- "A reviewer agent found a stale 6-month battery target": the repo shows the stale 6-month text was removed after the owner's 3-month decision (commit 3e03dfd, PR #30), not that a reviewer found it. Not claimed as a review catch. Used in the calendar as a myth-versus-proof topic instead.
- Agent minutes and human-hour equivalents: the Agent Log was not readable from this task, so no time figures are in these posts (each would be labelled "estimate").

## Estimated vs measured, at a glance

Post 1: all figures **calculated** (datasheet formula), no bench measurement. Post 2: all figures **measured test results** on a **local** PostgreSQL 16, not on the live system.

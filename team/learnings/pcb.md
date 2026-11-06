# Playbook: PCB designer

Living skill file for this role — read it before every assignment (TEAM.md §8).
Rules are short and imperative, most important first, each with *why* and a source.
Updated in the Friday retro PR; max ~60 rules. Never relaxes TEAM.md §5 hard rules.

## Rules
1. Never order anything and never promise a "verified" part list you could not check. Request shop hosts (LCSC/JLCPCB) via the allowlist first; until reachable mark stock/price `unverified`. *Why:* a BOM without live stock is a guess. *Source:* Sprint 1 Agent Log; TEAM.md §5.
2. Check part lifecycle (active / NRND / EOL) as well as stock before putting a part in the BOM. *Why:* in-stock EOL parts break the 1k-pcs plan. *Source:* Sprint 1 Agent Log.
3. Simulate the worst case and attach the plot; each sim is a script with pass/fail limits. *Why:* "did we simulate the worst case?" is the review question. *Source:* role file, Plan 4.P1.
4. Cross-check strapping pins (GPIO2/8/9 on ESP32-C3) against the pin map, pull-ups and attached circuits; keep `board.h` and the PR pin table identical. *Why:* a wrong strap level at reset prevents boot. *Source:* Sprint 1 Agent Log.
5. State what a dev kit can and cannot measure (e.g. module current yes, board leakage/divider/charger no) before using its data in the power budget. *Why:* dev-kit regulators and LEDs distort deep-sleep current. *Source:* Sprint 1 Agent Log.
6. Implement an owner-supplied formula exactly as given; put extras (margins, alternatives) in clearly labelled separate lines. *Why:* silent changes make the owner's number non-reproducible. *Source:* Sprint 1 Agent Log, PR review.
7. Use the single parameter `NFR01_MONTHS` for the battery-life target in every script, table and doc; never hard-code 6. *Why:* the target changed once and must change in one place. *Source:* Sprint 1 PR review.
8. Generate doc tables (power budget, BOM, pin map) from the script and add a drift test that fails when doc and script differ. *Why:* hand-copied tables went stale. *Source:* Sprint 1 PR review.
9. Re-derive any number a reviewer gives you before adopting it; reply with your own calculation. *Why:* reviewer figures can be wrong too. *Source:* Sprint 1 PR review.
10. Derive proposed limits with a stated margin and show the ratios to best/typical/worst case next to the limit. *Why:* a bare limit cannot be judged. *Source:* Sprint 1 PR review.
11. Grep the architecture docs and Requirements for an ID before proposing it (e.g. NFR-10 already existed). *Why:* duplicate IDs create contradictions. *Source:* Sprint 1 PR review.
12. Power budget: current per state × time per hour → mAh/day → months; show >= NFR01_MONTHS or flag it. *Why:* NFR-01 is a headline requirement. *Source:* role file.
13. Read the combined commit status as well as check runs before calling CI green. *Why:* some CI results only appear in the combined status. *Source:* Sprint 1 PR review.
14. Keep the antenna keep-out free and away from the wet-soil end of the stake. *Why:* antenna near wet soil is a listed risk. *Source:* Plan 2.8.
15. Announce every board-outline change to the Lead the same day. *Why:* enclosure v3 is fitted to the outline and must be fixed before the PCB order. *Source:* Plan 4.E3.

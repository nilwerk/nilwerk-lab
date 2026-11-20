# Playbook: PCB (retro S3 proposal, 2026-11-20)

Living skill file for this role (TEAM.md §8). Rules are short and imperative, most important first, each with *Why* and *Source*. Updated in the Friday retro. Never relaxes TEAM.md §5 hard rules.

## Rules
1. Never order, pay or sign up for anything; prepare the cart or list for Arsany. Request LCSC/JLCPCB hosts via the allowlist first; until they are reachable, mark stock and price `unverified`, never "verified".
   *Why:* a BOM without live stock is a guess, and a "verified" claim you could not check is an invented result.
   *Source:* Sprint 1 Agent Log; TEAM.md §5.

2. Plan a PCBA order only after routing, panel and fiducials, footprints (U5/U6 in S2) and the gate review are done. A calendar date alone never sets an order date.
   *Why:* the 12 Nov order was not realistic (board unrouted, simulations open); G4a/4.P4 slipped 2–3 working days.
   *Source:* A-064 (10 Nov report, accepted 10 Nov); 13 Nov lesson.

3. Check part lifecycle (active / NRND / EOL) as well as stock before a part enters the BOM. Put both in the BOM tab and `pcb/bom.csv`, with LCSC number, stock, and price at 3 pcs and 1k pcs.
   *Why:* an in-stock EOL part breaks the 1k-pcs plan.
   *Source:* Sprint 1 Agent Log; role file.

4. Simulate what can be wrong before anything is built. Each simulation is a script with pass/fail limits and writes a PNG plot. Cover LDO dropout at low battery, divider accuracy and leakage, soil front-end response, charger and protection thresholds, and USB inrush.
   *Why:* "Did we simulate the worst case?" is the review question.
   *Source:* role file; Plan 4.P1.

5. Derive every proposed limit with a stated margin. Show the ratio to best, typical and worst case next to the limit.
   *Why:* a bare limit cannot be judged.
   *Source:* Sprint 1 PR review.

6. Implement an owner-supplied formula exactly as given. Put margins and alternatives on clearly labelled separate lines.
   *Why:* silent changes make the owner's number non-reproducible.
   *Source:* Sprint 1 Agent Log, PR review.

7. Re-derive any number a reviewer gives you before adopting it. Reply with your own calculation, and say when the reviewer is right.
   *Why:* reviewer figures can be wrong too.
   *Source:* Sprint 1 PR review.

8. Compute the power budget as current per state × time per hour → mAh/day → months, using one named constant for the battery-life target. Show the result against that target, or flag it as missed.
   *Why:* battery life is a headline requirement, and a hard-coded target goes stale.
   *Source:* role file; Sprint 1 PR review (merged former rules 7 and 12).

9. Generate doc tables (power budget, BOM, pin map) from the script, and add a drift test that fails when doc and script differ.
   *Why:* hand-copied tables went stale.
   *Source:* Sprint 1 PR review.

10. Cross-check strapping pins (ESP32-C3: GPIO2, GPIO8, GPIO9) against the pin map, pull-ups and attached circuits. Keep `firmware/main/board.h` and the PR pin table identical.
    *Why:* a wrong strap level at reset prevents boot.
    *Source:* Sprint 1 Agent Log.

11. Before calling CI green, read the combined commit status and the check runs. If a gate does not run your folder, say so in the PR and in the report.
    *Why:* some results appear only in the combined status, and CI skipped `v1/` (no gate on the wiring spec, 14 Nov).
    *Source:* Sprint 1 PR review; PR #101 (S3, 14 Nov report).

12. State what a dev kit can and cannot measure (module current yes; board leakage, divider, charger no) before its data goes into the power budget.
    *Why:* dev-kit regulators and LEDs distort deep-sleep current.
    *Source:* Sprint 1 Agent Log.

13. Re-derive each programming and sizing resistor in a wiring spec from its datasheet formula, and show the formula next to the value.
    *Why:* the QA note on PR #101 asked to change R_PROG from 1200 to 1100; a wrong charge-set resistor is found only by review.
    *Source:* PR #101 QA (S3, 15 Nov report).

14. Label every unmeasured dimension or value in a spec or enclosure as `ASSUMED`, and name the measurement that closes it. Print or fit-check only on the labelled assumption.
    *Why:* part heights were typical values; a fit-check that reports 0 FAIL is not a PASS on any height.
    *Source:* `projects/plant-monitor/enclosure/v1_demo_compact/README.md`; A-094 items 2 and 4.

15. While an owner measurement is open, continue only the work that does not depend on it. Do not fill in a typical value to unblock a dependent task.
    *Why:* S3 Emil and Yara sat without a task from 17 to 20 Nov; a silent typical would have become a result.
    *Source:* A-094 (issue #109); 17–19 Nov reports; TEAM.md §5 "never invent results".

16. Write owner bench requests as one numbered list, decision-relevant items first. Each item gives the expected value, the stop threshold, and the decision it unlocks. Ask only what the dev kit cannot answer.
    *Why:* A-094 was due 17 Nov, still open on 20 Nov, and blocks two roles; the 15 Nov report had to ask for items 1, 5, 7, 8 first.
    *Source:* A-094; 15 Nov report.

17. In a bench procedure, stop at the stop threshold and report the reading. Do not add a divider or change attenuation at the bench.
    *Why:* a clipped ADC reading at the dry end would be read as a sensor result.
    *Source:* `projects/plant-monitor/v1/FIRMWARE-BENCH.md` step S4 (AOUT above about 2.4 V in air = stop).

18. Announce every board-outline change to the Lead the same day, and update the enclosure fit check with it.
    *Why:* the enclosure is fitted to the outline; a late change breaks the fit before the PCB order.
    *Source:* Plan 4.E3 (stopped 14 Nov; rule still applies to any enclosure fitted to the outline).

19. Export the board outline (DXF and STEP) for the 3D designer with every revision, and state the revision in the PR.
    *Why:* the 3D designer works from the exported outline, not from the KiCad file.
    *Source:* role file.

20. Keep the antenna keep-out free and away from the wet-soil end of the stake. Check it against the Espressif guidelines in the layout PR.
    *Why:* an antenna near wet soil is a listed risk.
    *Source:* Plan 2.8; role file.

21. Keep the layout 2-layer, single-side assembly and within the JLC DFM rules, and state the DFM check result in the PR.
    *Why:* the layout must be buildable at the planned fab house without rework.
    *Source:* role file.

22. Regenerate every generated artifact (e.g. wiring diagram PNGs from `gen_wiring.py`) after each upstream board change, and state the merge order in the PR.
    *Why:* a stale generated picture shows a wiring that no longer exists.
    *Source:* PR #87 review (13 Nov lessons, cross-role with Theo).

23. When a simulation, limit or battery-life figure changes, find every old value across README, captions, posts and specs (grep), and correct or retract it the same day.
    *Why:* a superseded battery-life figure already reached showcase material.
    *Source:* project PR/social examples; PR #88 caption review (13 Nov, cross-role with Ines).

24. Check that a fix is on `main` before writing "merged". Run `git merge-base --is-ancestor <commit> origin/main`.
    *Why:* the #117 fix was merged into another PR's branch after that PR reached main, so it never reached `main`.
    *Source:* 19 Nov report (cross-role with Lead and Sana).

25. Check each new NFR, requirement or architecture ID by grep before proposing it.
    *Why:* duplicate IDs create contradictions.
    *Source:* Sprint 1 PR review.

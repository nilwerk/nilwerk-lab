# Playbook: Mechanical (retro S3 proposal, 2026-11-20)

Living skill file for this role (TEAM.md §8). Rules are short and imperative, most important first, each with *Why* and *Source*. Updated in the Friday retro. Never relaxes TEAM.md §5 hard rules.

## Rules
1. Design only for the in-house Bambu Lab P1S + AMS: 256 × 256 × 256 mm build volume, 0.4 mm nozzle, FDM; never assume moulding or CNC. *Why:* Arsany decided on in-house prototyping and small batches (5–10 units). *Source:* standards/3d-manufacturing.md §1, decided 2026-11-07.

2. Specify PETG only (black, grey, white) for now. If a part needs ASA, TPU, another colour or nozzle, keep the PETG design, state the limit in the design notes and raise a Needs Arsany item with the reason and the cost. *Why:* PETG is the only stock; extra material or a nozzle is a purchase only Arsany approves. *Source:* standards §2; TEAM.md §5.

3. Never invent a dimension. Model a fit only from measured values (caliper on the real part), datasheets, vendor CAD or the PCB export. If a critical height or outline is missing, raise it in Needs Arsany or a work order before finalising CAD. *Why:* a fit built on guessed heights passes on paper and jams on the bench. *Source:* standards §7; 4.E5 PR #102 (part heights were Emil's typical values, UNVERIFIED); Needs Arsany A-094.

4. Label every assumed or unverified number ASSUMED or UNVERIFIED in the source file, the README and the PR body. Such numbers never produce a PASS in a fit check. *Why:* a reviewer must see which numbers are guesses before trusting the geometry. *Source:* PR #102 README ("Status of every number"); Lead 2026-11-19 lessons.

5. Read every PASS row's inputs, not its label. A check that compares a value with itself, or puts a RULE tag on derived geometry, proves nothing. *Why:* the fit check passed while the input was not measured. *Source:* Ines, 4.E5 (report 2026-11-16 lessons).

6. Quote a tolerance with every critical dimension and carry the worst case into the fit check (e.g. 3.26 mm ±0.10 mm → 3.36 mm worst case). *Why:* a nominal value that just clears the bore fails in the worst part of its tolerance. *Source:* Ines QA, 4.E3 J1 (report 2026-11-14).

7. Do not finalise a housing while its heights are open. The first print is a FIT-CHECK part only until the tallest point above the board and the under-board height are measured; say so in the file name and README header. *Why:* the 4.E5 v1 housing was drafted on typical heights and can only be checked on the bench. *Source:* PR #102 README (first print = fit-check only); A-094 (overdue since 17 Nov, blocks Emil and Yara).

8. Make one measurement list per open height, with the exact part, the point to measure and the tool (caliper, ruler, datasheet page). Send it as a Needs Arsany item or work order, not as a general request. *Why:* the 4.E5 list had five separate items that could be answered in one bench session. *Source:* PR #102 README items 3–5; A-094.

9. Before you raise a decision or measurement question, check the item's current state in the repo and in the Needs Arsany list, and check the source of every number you quote. Do not re-ask an answered item; name the open one. *Why:* A-093 was already answered (bare-board sizes) while A-094 (part heights) was still open; an unsourced J1 height was once quoted as a fact. *Source:* report 2026-11-14 lessons (J1 11.94 unsourced); report 2026-11-16 lessons (pad-4 decision already on main); 4.E5 status.

10. Never invent results. If a slice, print, fit test, render or CAD build could not run, say so in the PR and the report, with the reason. *Why:* the owner decides on printing from our reports. *Source:* TEAM.md §5; 4.E5 PR #102 ("Nothing printed, sliced or measured").

11. Give every design note a "Fusion 360 strategy" section: parameter table mirroring `params.py`, body and component split, and the features Arsany would edit in Fusion. When his STEP diverges from `params.py`, flag it; never overwrite it. *Why:* Arsany takes designs into Fusion 360 and needs them to be readable without reverse-engineering. *Source:* standards §1a.

12. Never claim compliance or ratings in a README or caption (CE, EMC, RoHS, IP, NFR). Put the real status at the top: e.g. "indoor demo, not splash-proof, not IP-rated". List compliance as an open item. *Why:* no assessment exists yet, and an unsupported rating is a claim we cannot back. *Source:* standards §10; PR #102 review condition C1.

13. Make the enclosure functional first, then add ONE signature design touch from the standard: a top-edge chamfer or fillet, a softened profile line, a trace-motif relief (2–3 layers deep, ≥ 0.8 mm wide, remaining skin ≥ 1.2 mm), or a black/grey/white colour split. Keep it parametric behind a flag in `params.py` with a test and a render. *Why:* one considered detail reads as design; many read as decoration (standards §4). *Source:* Arsany 2026-11-08, PR #44.

14. Keep every design printable and sealed: walls ≥ 1.2 mm, no new overhangs or supports, reliefs only on non-sealing faces, and bay or PCB dimensions unchanged. Test watertightness and outer size before the design goes in. *Why:* a pretty part that leaks, jams or needs supports fails the P1S standard and NFR-05. *Source:* Arsany 2026-11-08, PR #44; standards §3–4.

15. Keep the antenna keep-out in the model and the README: no metal, carbon, cell, wire or thick wall over the antenna, with the clearance in mm. *Why:* the enclosure can silently reduce Wi-Fi range; the lid material is not RF-tested. *Source:* standards §7; 4.E5 README (antenna keep-out, RF not measured).

16. Put charging and battery safety into the design: for any closed PETG box with a Li-ion cell or charger, write "never charge unattended inside the closed box", give the vent path, and add lid-off steps beside lid-on steps. *Why:* PETG softens far below cell-fire temperatures and a beginner may leave a charge running. *Source:* PR #102 review conditions C2 and C3 (Theo).

17. Write every print work order with the exact file, the 3MF or slicer profile, the material and nozzle, the orientation and what to measure. Mark print time and material use as estimates unless taken from a Bambu Studio slice. *Why:* Arsany or Peter prints from the work order; beginners need exact settings. *Source:* standards §9D, §10.

18. One successful print is not approval: Prototype 1 (fit), Prototype 2 (assembly), Prototype 3 (final material and settings), then a 5–10 unit pilot with a quality inspection. *Why:* a single print proves dimensions for one unit, not repeatable production. *Source:* standards §10.

19. For stacked PRs, name the base PR and the merge order in the title and body. Before you say "merged", check that the commit is an ancestor of `origin/main`. *Why:* a fix merged into another PR's branch after that PR reached main never reached main. *Source:* report 2026-11-19 lessons (#117 and the 4.B2c path guard); PR #102 stacked on #101.

20. Name the head SHA in every review or QA request, and re-run review and QA on every new head. *Why:* a QA round ran on a superseded head and the rule was applied again after each fix. *Source:* report 2026-11-16 lessons (Lead).

21. In fix rounds, write "no geometry change" in the commit message when a fix changes only text, tests or labels, and state the geometry change when there is one. *Why:* the review can then focus on the geometry that actually changed. *Source:* 4.E5 commit history (rounds 2–5 of PR #108).

22. Never overwrite an older version folder in Drive or the repo; export to the next vN. *Why:* older design versions are the record of what was printed and approved. *Source:* TEAM.md §5 (no deletion of design versions); project README.

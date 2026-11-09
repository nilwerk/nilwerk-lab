# 4.P4 prep: a JLCPCB order package that is ready to review, and not ready to order

The team now has a generated order package for the Plant Monitor board: Gerber and drill files from the CI export, a JLCPCB assembly BOM with LCSC numbers, stock and prices read on the day, a pick-and-place file, a dry-run checklist with 40 JLCPCB limits, and a cart list. Nothing was ordered. The checklist says the order is blocked: the board is not routed, the panel is not designed, and 7 footprints are placeholders.

The picture is the real board file at this head (`plant-monitor.kicad_pcb`, drawn by `check_layout.py --render`). It is the same board as the 4.P2 image, because this task adds no layout change.

- Task: 4.P4 prep (dry run), order package for JLCPCB
- PR: link in the PR description (stacked on PR #64, merge #64 first)
- Persona: Emil (PCB Designer, "The simulator")
- Agent minutes: see the Agent Log (measured by the Lead); own measured start-to-end is in the PR report
- Human estimate without AI: about 4 hours for an experienced engineer (own estimate, not measured): the generator, the BOM with live LCSC and JLC data, the checklist against the JLCPCB limits
- Unverified: CPL rotation and origin (JLC preview), JLC fab, PCBA and Extended-part fees, the LiPo cell price and plug, 37 BOM price lines below their first LCSC break, the via-in-pad price option, the panel, and everything that depends on routing and the placeholder footprints

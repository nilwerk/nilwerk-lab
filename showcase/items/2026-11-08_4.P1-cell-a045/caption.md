# 4.P1 round 2: cell identified, NFR-01 re-run, schematic updated (Emil, 2026-11-08)

The owner answered three open points; the schematic, the power budget and the cell sheet were updated the same afternoon. The Amazon listing the owner chose turned out to be the EEMB LP603449-PCM (1100 mAh typical, 1000 mAh minimum, PCM built in), not the Jauch LP503030JU he had searched for; its page text was read (price and delivery could not be read and are marked unverified). Under the relaxed battery rule (best and typical at least 3 months, worst more than 1 month) it passes all three scenarios: 11.0 / 4.3 / 1.36 months. The divider switch (Q2, R6) was removed, the charge resistor was re-checked for this cell (stays 2.4k, 0.46C).

Evidence: no image. Real evidence: `python3 -I projects/plant-monitor/pcb/check_netlist.py` (all checks pass), `python3 -m unittest` in `hardware/power-budget` (28 tests), generated tables in `power-budget.md` section 1 and 12, KiCad ERC in the CI run of the PR (result in the PR comment).

- Task: 4.P1 (with 2.3 power budget)
- PR: https://github.com/nilwerk/nilwerk-lab/pull/41
- Persona: Emil (PCB Designer, "The simulator")
- Agent minutes: see the Agent Log (measured by the Lead); my own start/end are in the PR comment
- Human estimate without AI: about 5-6 hours (the author's own estimate, not measured)
- Unverified: price, delivery, plug pitch and polarity, wire length and tolerances of the cell (page text only, photos not read); all currents in the power budget are still estimates; simulations not run.

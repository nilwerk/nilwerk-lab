# 4.P2 slice 1: the first Plant Monitor board file, placed and checked

The first real board file of the Plant Monitor: a KiCad 9 PCB generated from the schematic data, with all 46 parts placed, the antenna at the board edge inside a copper-free keep-out, the soil electrodes as copper on a tail at the far end, and the LiPo cell bay beside it. KiCad's own design-rule check in CI reports 0 errors (this means only: closed outline, no clearance or keep-out error between placeholder pads; unconnected items are warning-level, not in the error-level report, because the board is unrouted, so this is not a connectivity result). The picture is drawn from the actual `plant-monitor.kicad_pcb` file (not a mock-up); it is not a KiCad screenshot because no KiCad was available in the agent session.

- Task: 4.P2 (PCB layout), slice 1: placement, not routed
- PR: https://github.com/nilwerk/nilwerk-lab/pull/64
- Persona: Emil (PCB Designer, "The simulator")
- Agent minutes: see the Agent Log (measured by the Lead); own measured start-to-end is in the PR report
- Human estimate without AI: about 10 hours for an experienced engineer (my own estimate, not measured): footprints, outline, placement, rules, checks
- Unverified: 7 footprints are placeholders (pad geometry not from the datasheet drawings: ESP32 module, USB-C, JST, switches, AHT20, BH1750, stake); antenna keep-out size and overhang are my assumptions (Espressif datasheet figure not read); the board is not routed; DRC was run at error level only; outline depends on enclosure answers still open (Q1-Q11); cell plug pitch/polarity unverified; no stock or price check.

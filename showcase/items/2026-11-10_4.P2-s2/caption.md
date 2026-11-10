# 4.P2 slice 2: the board with real footprints, vias moved out of pads

The Plant Monitor board file after slice 2: the ESP32-C3 module, USB-C, the cell connector, the three tact switches and the standard parts now use real pad geometry (library or manufacturer drawing) instead of placeholders, the 16 ground vias are no longer inside pads (4 of them are joined to the charger's exposed pad by short GND tracks, the first tracks on the board), and the antenna keep-out check now runs in CI. The picture is drawn from the actual `plant-monitor.kicad_pcb` (not a KiCad screenshot). It is still NOT routed and NOT fab-ready.

- Task: 4.P2 (PCB layout), slice 2
- PR: https://github.com/nilwerk/nilwerk-lab/pull/73
- Persona: Emil (PCB Designer, "The simulator")
- Evidence: KiCad 9 in CI: ERC 0 errors, DRC 0 violations at error level; own layout checks all PASS (0 vias in pads, antenna area 25.7 mm from the cell, rule 15 mm)
- Found on the way: the slice-1 switch placeholder would have shorted signal to GND (terminals A-B and C-D are joined inside the real switch); fixed by the real footprint
- Human estimate without AI: about 8 hours for an experienced engineer (my own estimate, not measured)
- Unverified: AHT20 and BH1750 footprints are still placeholders; J1 and J2 come from the KiCad library, not compared with the vendor drawings; nothing is routed; JLC DFM view not seen; no local KiCad (CI only)

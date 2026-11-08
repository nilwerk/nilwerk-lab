# 4.P1 PCB schematic (Emil, 2026-11-08)

A KiCad 9 schematic for the plant monitor board, generated from a Python data model (no GUI available): ESP32-C3 module, 3.3 V low-Iq LDO, TP4056 charger with cell protection, USB-C with ESD, AHT20, BH1750, capacitive soil front end, battery divider, buttons. Every part carries its LCSC number and footprint and matches the 2.5 BOM (4 declared additions). A netlist check, written separately from the generator, passes; KiCad ERC was NOT run (no KiCad 9 available).

Evidence: no image (the file could not be rendered without KiCad). Real evidence: `projects/plant-monitor/pcb/check_netlist.py` output.

- Task: 4.P1
- PR: https://github.com/nilwerk/nilwerk-lab/pull/41
- Persona: Emil (PCB Designer, "The simulator")
- Agent minutes: 6.3 for the first build (source: measured agent time of the 4.P1 run, reported by the Lead). Excludes review and the fix round after Theo's review, so it is not a speed-up claim.
- Human estimate without AI: about 14-18 hours (the author's own estimate, not measured)
- Unverified: ERC (never opened in KiCad), all simulations (none run; ngspice is not installed), sleep-current values (mostly assumptions), D1/U3/U7 pin maps were cross-checked against the LCSC datasheets in the fix round but the custom footprints (U5, U6, switches, probe) are not drawn yet.

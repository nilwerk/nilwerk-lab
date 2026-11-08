# 4.P1 PCB schematic (Emil, 2026-11-08)

A KiCad 9 schematic for the plant monitor board, generated from a Python data model (no GUI available): ESP32-C3 module, 3.3 V low-Iq LDO, TP4056 charger with cell protection, USB-C with ESD, AHT20, BH1750, capacitive soil front end, battery divider, buttons. Every part carries its LCSC number and footprint and matches the 2.5 BOM (3 declared additions). A netlist check, written separately from the generator, passes; KiCad ERC was NOT run (no KiCad 9 available).

Evidence: no image (the file could not be rendered without KiCad). Real evidence: `projects/plant-monitor/pcb/check_netlist.py` output.

- Agent minutes: about 45 (see report)
- Human estimate without AI: about 14-18 hours
- Unverified: all pin numbers of 7 parts, ERC, sleep-current values (mostly assumptions), the schematic has never been opened in KiCad.

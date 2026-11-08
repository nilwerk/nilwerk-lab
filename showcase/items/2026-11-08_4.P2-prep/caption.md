# 4.P2 prep and BOM sync (Emil, 2026-11-08, extra round)

The hardware BOM now matches the schematic line for line (Q2 gone, R13-R16 in, the decided cell as its own line), the live prices were re-read, and the question "do we still need the second battery protection on a cell that already has one?" has numbers: about 2.2 USD per board at 3 boards, 3 uA of sleep current, and a clear recommendation. For the layout, a brief lists the outline constraints, the antenna rules from Espressif's own guide (15 mm clear all round, cell kept away from the antenna), the JLC rules, and the nine questions the enclosure designer must answer. The LDO-at-low-battery simulation that was "not run" is now run: the 3.3 V rail stays above the module's 3.0 V minimum at the 3.4 V warning point.

Evidence: `python3 -m unittest` in `hardware/bom` (14 tests OK), `python3 -I pcb/check_netlist.py` (all PASS, no declared BOM differences left), `pcb/sim/ldo_dropout.py` (ngspice 42, plot `pcb/sim/ldo_dropout.png`).

- Task: 2.5 / 4.P1 sync and 4.P2 prep
- Branches: `agent/pcb/bom-sync`, `agent/pcb/4.P2-prep`
- Persona: Emil (PCB Designer, "The simulator")
- Agent minutes: see the Agent Log (measured by the Lead)
- Human estimate without AI: about 5 hours (my own estimate, not measured)
- Unverified: cell price, plug and polarity; cell resistance in the dropout model is an assumption; USB-C footprint size not yet read; four simulations still not run; JLC rules re-check on Gerber day.

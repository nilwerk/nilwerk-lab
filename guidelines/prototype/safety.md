# Electrical and battery safety (every prototype)
- ESP32-C3 GPIO is 3.3 V logic. No 5 V signal on a GPIO. Check every board's and part's limits in its official documentation.
- LED polarity and series resistor checked. No load beyond a pin's documented current; use a driver when needed.
- Never connect a LiPo cell directly to a GPIO, the 3.3 V rail or the 5 V rail. Check cell chemistry, cell count, polarity, charger compatibility, protection and the board's power path first.
- Do not assume a charger board can power the project while charging. Read its datasheet. Do not leave a prototype charging unattended or use a damaged, swollen or hot cell.
- First bring-up on USB or another current-limited supply. If a safe wiring detail cannot be established, stop and ask for the exact part information.
- Charger reference designs: inspect the schematic or netlist, not connector labels. A "LOAD" connector may be wired straight to `BAT` and bypass the power path.
- Prototypes stay low-voltage and non-safety-critical. Never described as certified or suitable for medical, vehicle or mains use.
- Hands-on work (flashing, measuring, charging, soldering) is a work order for Peter (TEAM §12).

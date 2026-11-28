# Plant monitor v1 (perfboard function demo) - final BOM as built

Task 6.2. Author: Emil (PCB Designer), 2026-11-28. Branch `agent/pcb/bom-v1-final`.
Scope: the v1 perfboard only (no custom PCB, no v2 parts). Source of the parts: `projects/plant-monitor/v1/WIRING.md` section 1 (parts list) and section 10 (as-built record, owner report 2026-11-28, A-094).

**Status conventions.** `as built` = owner reports it is on the perfboard. `OPEN` = not confirmed yet (identity, count or fit). `UNVERIFIED` = price, stock or supplier not checked (no shop page was opened for this list). No price is verified here; prices are left blank on purpose.
Nothing was ordered or bought. Ordering stays with Arsany.

## 1. Parts used (in the as-built perfboard)

| # | Part | Used for | Qty | Supplier | Unit price | Status |
|---|---|---|---|---|---|---|
| 1 | DUBEUYEW ESP32-C3 SuperMini (ESP32-C3FN4, 4 MB flash, USB-C) | MCU, firmware | 1 | not recorded in repo | UNVERIFIED | as built |
| 2 | TP4056 USB-C charger module, with protection ICs (photo: TP4056 + two 8-pin chips, DW01 + 8205A assumed) | Charges the cell; OUT+/OUT- feed the load | 1 | not recorded in repo | UNVERIFIED | as built; protection variant UNVERIFIED (WIRING 2.1) |
| 3 | 1S LiPo cell, 1000 mAh minimum, built-in protection (PCM), JST-PH 2.0 plug (owner, A-091) | Battery | 1 | Amazon.de per A-034 (ASIN B08FD39Y5R), to confirm for the cell in hand | UNVERIFIED | as built per owner; cell identity EEMB LP603449-PCM is the repo decision (A-034), to confirm against the cell in hand. Max charge current: owner 1000 mA, repo 1100 mA, OPEN (WIRING section 12) |
| 4 | JST-PH 2-pin lead (red/black) | Battery plug J_BAT to TP4056 B+/B- | 1 | not recorded | UNVERIFIED | OPEN: separate pigtail or the AA-holder lead (WIRING section 8 item 7) |
| 5 | BH1750 (GY-302) light breakout, 5 pins | Ambient light, I2C 0x23 | 1 | not recorded | UNVERIFIED | as built |
| 6 | AHT20 temperature and humidity breakout, 4 pins | Air temperature and humidity, I2C 0x38 | 1 | not recorded | UNVERIFIED | as built |
| 7 | Capacitive soil moisture sensor v1.2, 3-pin JST-PH cable | Soil moisture (analog) | 1 | not recorded | UNVERIFIED | as built; cable to the bottom of the box |
| 8 | Perfboard 70 x 50 mm, 2.54 mm pitch, double-sided | Carries all parts | 1 | not recorded | UNVERIFIED | as built |
| 9 | Pin headers (loose strips) | SuperMini, breakouts, J1 (2-pin), J3 (3-pin) | 1 set | own stock (WIRING 1, row 9) | - | as built; count OPEN |
| 10 | Resistor 100 kOhm, 1 %, 2 pcs | Battery divider R1/R2 | 2 | own stock (WIRING 1, row 10) | - | as built per plan; 1 % rating OPEN (WIRING 8 item 8) |
| 11 | Ceramic capacitor 100 nF | ADC filter at GPIO0 (C1, optional) | 1 | own stock | - | OPEN: fitted or not |
| 12 | Slide switch (or jumper shunt) | J1, the 5 V feed disconnect for flashing | 1 | own stock (WIRING 1, row 11) | - | OPEN: which of the two is fitted (WIRING 2.3) |
| 13 | Hook-up wire, 26-30 AWG, insulated | All point-to-point wiring (W01-W23) | UNVERIFIED length | not on hand per WIRING 1 | UNVERIFIED | as built per owner; purchase source and length OPEN |
| 14 | Kapton tape | Insulation under TP4056 and the USB-C overhang | UNVERIFIED | not on hand per WIRING 1 | UNVERIFIED | OPEN: bought or borrowed |
| 15 | Double-sided tape | Mounts the TP4056 module on the perfboard (WIRING 5) | UNVERIFIED | not recorded | UNVERIFIED | OPEN: used or not |

Parts count: 1 + 1 + 1 + 1 + 1 + 1 + 1 + 1 (+ 1 set headers) + 2 resistors + the optional capacitor, switch, wire, tapes.

## 2. Not in the final BOM (not used, or not decided)

| Item | Reason |
|---|---|
| ESP32-C3-DevKitM-1 (2 pcs, `hardware/devkit-order-list.md`) | Not used: the owner built the SuperMini board. The 4.H0 list was for the dev-kit bench, not this build. |
| BH1750 / AHT20 second units, soil sensor spares (3-pack in 4.H0) | Not used on the perfboard; one of each is wired. |
| TP4056 charger, LiPo cell, breakouts from 4.H0 (rows 2-6) | Replaced by the as-built parts above; the 4.H0 prices are not used. |
| WeMos D1 mini (ESP8266) | Not used (WIRING 1). |
| 2-cell AA holder | Not used; must never connect to the TP4056 (WIRING 1). |
| 5.1 kOhm I2C pull-ups (Rp1, Rp2) | Only if the breakouts have none (WIRING 4.3). Not decided: not in the list. Add if the pull-up check says so. |
| 2 kOhm + 330 Ohm R_PROG swap (2.33 kOhm) | Not decided: depends on the open charge-current question (WIRING section 12 item 1). |
| Tactile buttons, female headers (on hand) | Not wired in the as-built plan; on hand, not counted. |
| Jumper shunt | Not on hand (WIRING 1). Slide switch used instead if it is J1. |

## 3. Open before the BOM is final

1. Confirm the cell in hand (identity, JST pitch, polarity by meter) and its max charge current (owner 1000 mA; repo 1100 mA).
2. Confirm the TP4056 module's protection variant and R_PROG marking (WIRING section 12).
3. Confirm the supplier, price and stock for each row (UNVERIFIED for all rows; no shop page was opened for this list).
4. Confirm the counts: header pins, hook-up wire length, Kapton and double-sided tape.
5. Confirm whether the 100 kOhm resistors are 1 % and whether 100 nF, the slide switch and pull-ups are fitted.

_Generated by [Claude Code](https://claude.ai/code)_

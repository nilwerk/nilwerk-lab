# Cell decision after A-034 (battery from DigiKey)

Author: Emil (PCB Designer) · Read live **2026-11-07** (Berlin evening) · Nothing was ordered or bought (hard rule); the cart in section 6 is a list for Arsany to click.

## Decision box for Arsany (neutral)

1. **Jauch LP503030JU (A-034 candidate): does not meet NFR-01 as specified.** 430 mAh minimum gives 1.9 months typical against 3 months; about 668 mAh rated is needed. It fits the bay.
2. **Jauch LP603443JU+PCM+2 wires (DigiKey): meets NFR-01** (3.8 months typical, 850 mAh minimum). It is 6.5 mm thick per DigiKey, 0.2 mm above the 6.3 mm **minimum** bay; enclosure v3 is not built, so this is an input to Yara, not a collision. Its datasheet says **IEC 62133: NO** (UN 38.3 yes); the candidate LP503030JU says IEC 62133-2 yes. **Decision for you:** whether the missing IEC 62133 matters for your use (CE/sale); I do not assess it.
3. **Open for both:** swelling margin; pack drawing (ask Jauch, batterytechnology@jauch.com is on the datasheet, I send nothing); LP603443JU has no NTC and no 2nd IC; DigiKey lists 28 weeks lead time against 516 in stock (ask DigiKey/Jauch before ordering).
4. **Third option:** keep the EEMB 603449 (4.5 months, but no verified source, PCM or price).
5. **Your call:** cell, whether the bay may grow, and the order. I never order.

## Answer first

| Question | Jauch **LP503030JU**+PCM+2IC+NTC (the A-034 candidate) | Jauch **LP603443JU**+PCM+2 wires (found on DigiKey while checking) |
|---|---|---|
| Fits NFR-01 (3 months, rule A-021: 0.8 x **minimum** rated mAh / average current)? | **NO.** 430 mAh minimum gives **1.9 months typical** (best 5.5, worst 0.6). About **668 mAh rated** is needed for the typical case | **YES.** 850 mAh minimum gives **3.8 months typical** (best 10.8, worst 1.2, the worst stack is a stress bound) |
| Fits the A-020 bay 51 x 34.5 x 6.3 mm? | **YES**, with margin: 5.2 x 30 x 30 mm (21 mm spare in length, 4.5 mm in width, 1.1 mm in height) | **Not at the 6.3 mm minimum:** 6.5 mm per DigiKey is 0.2 mm thicker, width 34.5 mm leaves zero margin; length 45 mm fits. The bay (`pcb-enclosure-bay.md`) is a minimum and enclosure v3 is not built, so +0.2 mm is an input to Yara, not a collision. Swelling margin is open for both cells; DigiKey 6.5 mm vs Jauch list 6.0 mm bare cell: ask Jauch for the pack drawing |
| Recommendation | **Does not meet NFR-01 as specified.** It would only reach 3 months with a stack of firmware levers that is not designed yet (typical lever package: 3.06 months, no margin) | **Recommended DigiKey cell, if Yara can take 6.5 mm height and Arsany accepts the open points (IEC 62133 NO, no NTC/2nd IC).** Otherwise ask Jauch for a PCM cell in the 603449 envelope |

So the plain answer to "fits NFR-01 **and** the bay" for the cell named in A-034 is **NO** (bay yes, NFR-01 no).

## 1. Datasheet facts (Jauch, read 2026-11-07)

Source: `https://www.jauch.com/downloadfile/6656dfa0259dd598ff0561692b13c1f98/lp503030ju.pdf` (linked from the DigiKey page; 2 pages, Jauch no. 252538, cell U503030P, 1s1p, version 1.0, 16.05.2024). The PDF is the family sheet for the LP503030JU pack; it has **no dimension drawing and no connector/wire drawing**.

| Item | Value | Where |
|---|---|---|
| Nominal voltage | 3.7 V | datasheet p. 2 |
| Capacity | **450 mAh typical, 430 mAh minimum** (0.2C, 3.0 V discharge) | p. 2 |
| Weight | about 10 g | p. 2 |
| Charge | 4.2 V; standard current 90 mA; **max 430 mA (1.0C)**; 0 to 15 C: max 0.2C; 15 to 45 C: max 1.0C | p. 2 |
| Discharge | cut-off 3.0 V; standard 90 mA; **max 430 mA (1.0C)**; -20 to +60 C; storage -20 to +25 C (max 3 months) | p. 2 |
| PCM | overcharge detect 4.275 +-0.05 V, release 4.075 +-0.05 V; overdischarge detect 3.00 +-0.1 V, release 3.20 +-0.10 V; max continuous current 1.0 to 2.6 A; **2nd protection: 2nd IC** ("2IC"); **NTC 10 kOhm +-1 %, B = 3435** | p. 2 |
| Standards, life | UN 38.3 yes, IEC 62133-2:2017 yes; 300 cycles to about 80 % (0.2C/0.2C, 25 C) | p. 2 |
| Size | **T 5.2 x W 30.0 x L 30.0 mm** | Jauch product list `jauch.com/en-FR/products/battery_technology/getPrm/batteries/` (T, W, L header; not in the datasheet, no second source) |
| Name suffix | "50MM" lead length and "Mol. 78172-3" connector | part name only; DigiKey attribute table collapsed, **wire count, wire gauge, pinout and plug polarity unverified** |
| Lifecycle | Active | DigiKey page |

Two things that matter for us: (a) the overdischarge cut is 3.0 V +-0.1 V, the NFR-01 end point is our 3.4 V warning, so the PCM does not interfere; (b) peak Wi-Fi TX is 276 to 335 mA (ESP32-C3 datasheet Table 5-7), which is 0.64 to 0.78C of the 430 mA discharge limit: allowed, but the cell is small for the load.

## 2. NFR-01 verdict at this cell's minimum capacity

Model `power_budget.py` unchanged, rule A-021 (derating 0.8 x **minimum** rated capacity / average current, no self-discharge term), threshold 2190 h. Numbers are from the script (`CELLS`, generated table in `power-budget.md` section 8; a unit test checks them):

| Cell (minimum mAh) | best | typical | worst | NFR-01 typical | max whole-board sleep that still passes (typical terms) |
|---|---|---|---|---|---|
| Jauch LP503030JU (430) | 5.5 months | **1.9 months** | 0.6 | **FAIL** | **-74 uA: cannot pass even at 0 uA sleep** |
| Jauch LP603443JU (850) | 10.8 | **3.8** | 1.2 | PASS | 80 uA (NFR-12's 50 uA fits) |
| EEMB LP603449 (1000) | 12.8 | 4.5 | 1.4 | PASS | 134 uA |

Rated capacity needed for the typical case: **668 mAh**. The LP503030JU has 430 mAh, i.e. **64 %** of that. All currents in the model are still unverified (only the ESP32-C3 rows were read, power-budget.md section 11); the verdict is only as good as that model, but the gap is 36 %, larger than the model's typical uncertainty.

**Options if this cell is kept (numbers from the model at 430 mAh):**

| Option | Result | Verdict |
|---|---|---|
| All firmware levers together (fast connect + hub every 2nd report + light-sleep warm-up, 3.70 mAh/day) | 3.06 months | passes by 2 %, **no margin**, nothing of it is designed or measured; any single lever missing fails |
| Single levers (e.g. fast connect 2.3 months, hub every 2nd 2.1 months) | 2.0 to 2.5 months | fail |
| Two LP503030JU in parallel (860 mAh minimum, 1s2p) | 3.8 months | needs two cells flat: 2 x 30 mm = 60 mm is longer than the 51 mm bay, stacked 10.4 mm is taller than 6.3 mm: **does not fit the bay**, and a parallel pack with two PCMs needs Jauch's agreement (unverified) |
| Jauch LP603443JU (850 min) | 3.8 months | **best fit of the Jauch list for the bay**, see section 5 |
| Other Jauch sizes from the product list (typical capacity, no minimum or PCM variant read, **unverified** on DigiKey): LP503040JH 600 mAh (5.0 x 30.5 x 42), LP443441JU 630 mAh (4.4 x 35 x 44, 0.5 mm wider than the bay), LP523450JU 950 mAh (5.4 x 34.8 x 52.5, 0.3 mm wider and 1.5 mm longer than the bay) | 600 mAh typical would still be below 668 mAh once the minimum is applied | only the 850 and 950 mAh cells reach the capacity; both need bay changes |
| Relax NFR-01 | not for me to propose; the cell would need 1.9 months to be accepted | Arsany's decision |

## 3. Charger fit (R9) and the NTC

TP4056 datasheet REV_2.4 (read 2026-11-07): R_PROG = 1100 / I_BAT (R in kOhm, I in mA), p. 9. The current board value **R9 = 2.4 kOhm gives 458 mA** (+-15 % per the datasheet electrical table: 527 mA worst case):

| | LP503030JU (430 mAh min) | LP603443JU (850 min) | LP603449 (1000 min) |
|---|---|---|---|
| 458 mA as C-rate | **1.07C, above the 1.0C (430 mA) datasheet maximum**; worst case 1.23C | 0.54C (max 1.0C = 900 mA) | 0.46C |
| Verdict for R9 = 2.4k | **too high, must change** | fine | fine |

For the LP503030JU the right resistor: 0.5C = 215 mA gives R = 1100 / 215 = 5.1 kOhm (E24), **216 mA nominal, 248 mA at +15 %** (0.58C), standard current of the cell 90 mA is 0.2C; **R9 = 5.1 kOhm = the same part as R1/R2, C23186** (Basic). The strict 1.0C limit would allow 3.0 kOhm (367 mA, 422 mA at +15 %) but 0.5C is gentler on a 10 g cell and the USB budget. Datasheet p. 2 also says **0 to 15 C: max 0.2C (86 mA)**: the TP4056 cannot lower the current with temperature, so charging between 0 and 15 C exceeds the cell's own limit; keep charging indoors or accept the deviation (decision for 4.P1). Not applicable to the LP603443JU, whose datasheet has the same 0 to 15 C / 0.2C rule (also exceeded at 0.54C).

**NTC to TP4056 TEMP** (4.P1 checklist item). TP4056 datasheet p. 7 and p. 10 to 11: TEMP is compared with 45 % (hot) and 80 % (cold) of Vcc, divider R1 (Vcc to TEMP) and R2 in parallel with the NTC (TEMP to GND), `R1 = RTL RTH (K2-K1) / ((RTL-RTH) K1 K2)`, `R2 = RTL RTH (K2-K1) / (RTL (K1-K1 K2) - RTH (K2-K1 K2))`, K1 = 0.45, K2 = 0.8. With the cell's 10 kOhm NTC, B = 3435 (B-parameter model, an approximation of Jauch's table, **unverified**), window 0 to 45 C (the cell's charge range): RTL = 28.7 kOhm, RTH = 4.85 kOhm, so **R1 about 5.7 kOhm (E24 5.6 kOhm, C23189 Basic), R2 about 108 kOhm (E24 110 kOhm, C25805, Preferred)**. A 15 to 45 C window is not possible with this topology (the formula gives a negative R2). Without a usable NTC the TEMP pin must be grounded, which disables the temperature sense (p. 10). These values are a proposal for 4.P1 to check in simulation; **the cell's own NTC curve was not read**.

## 4. Connector: Molex 78172-3 against our J2 (JST PH)

- "Molex 78172-3" is read as the **Molex 78172-0003**, Pico-EZmate receptacle crimp housing, **3 circuits, 1.20 mm pitch** (web results; Molex's own page returned an error, **the exact string "78172-3" was not found anywhere**, so this is **unverified** until the cell's datasheet or Jauch confirms it). Three circuits = battery +, battery -, NTC.
- Our board has **J2 = JST S2B-PH-SM4-TB, 2 pins, 2.0 mm**: **not compatible** (different family, pitch and pin count).
- Mating header on the board: **Molex 78171-0003** (Pico-EZmate header, 3 circuits, SMD), LCSC/JLC **C564183** (JLC Extended, stock 22,604, 0.2864 USD at 1, 0.237 at 50, read live; **LCSC describes C564183 as right angle: check the Molex mating drawing and the board edge**), as BOM line **J2b** (alternative to J2). That 78171 header mates with the 78172 housing is the Pico-EZmate family pairing (web results) and **unverified** against a Molex mating drawing. It adds one Extended part to the JLC order (+3.07 USD per order) and removes J2 (also Extended), so the fee count stays the same.
- Alternative without changing the board: a 2 x 3-pin adapter pigtail (Pico-EZmate to JST PH) loses the NTC, so the TP4056 TEMP pin must be grounded and cell temperature protection is lost.
- Polarity: **the pin order of the cell's plug is not in the datasheet**; check against J2b pin 1 on receipt before the first connection (hard hardware rule, a reversed cell destroys the board).

## 5. Price, stock, MOQ (DigiKey, read live 2026-11-07, page text read through a summary tool, re-check in the cart)

| | LP503030JU (A-034 candidate) | LP603443JU+PCM+2 wires 70MM |
|---|---|---|
| DigiKey part number | **3027-LP503030JU+PCM+2IC+NTC+Mol.78172-350MM-ND** | **1908-LP603443JU+PCM+2WIRES70MM-ND** |
| Page | `digikey.de/de/products/detail/jauch-quartz/LP503030JU-PCM-2IC-NTC-MOL.-78172-3-50MM/25623210` (DigiKey Marketplace, sold by Jauch Quartz) | `digikey.com/en/products/detail/jauch-quartz/LP603443JU-PCM-WIRES-70MM/1908-1365-ND/9560987` |
| Price (excl. VAT) | EUR **8.47** at 1, 6.924 at 10, 6.1252 at 50 (EUR 10.0793 at 1 incl. VAT) | USD **11.11** at 1, 9.24 at 10, 8.1244 at 50, 7.6869 at 100, 7.04754 at 297, 6.66886 at 594, 6.60 at 1188 |
| Stock | **85** | **516** |
| Lead time | ships in about 6 days from Jauch | **28 weeks** listed (manufacturer standard lead time; inconsistent with the 516 in stock, ask before ordering) |
| MOQ / pack | not stated, minimum selectable 1; tray | not stated, 1; tray |
| Shipping | free from EUR 66.58 on Jauch Quartz orders | not read |
| Datasheet | `jauch.com/downloadfile/6656dfa0.../lp503030ju.pdf` | `https://www.jauch.com/downloadfile/677e3a8d45c2839aafeab5156381835e3/matd_246512_20200507_850mah_-_lp603443ju_1s1p_2_wire_70mm.pdf` (Jauch no. 246512, **Rev. 1.2, 12/2024**, retrieved 2026-11-07; the older Rev. 1.1 of 10/2022 has the same values): 900 typ / 850 min mAh, charge max 1.0C = 900 mA (0 to 15 C 0.2C, 45 to 50 C 0.5C at 4.1 V), discharge max 900 mA, PCM OC 4.28 +-0.02 V, OD 3.00 +-0.05 V, over-current 3.0 to 6.0 A, **no NTC, no 2nd IC, bare wires**, IEC 62133 **NO**, UN 38.3 yes, about 20 g; DigiKey size 45.0 x 34.5 x 6.5 mm |

## 6. DigiKey cart for Arsany (3 demo units + 2 spare = quantity 5; never ordered by me)

| # | DigiKey part number | Qty | Unit (excl. VAT) | Line |
|---|---|---|---|---|
| 1 (recommended) | 1908-LP603443JU+PCM+2WIRES70MM-ND (Jauch LP603443JU+PCM+2 WIRES 70MM) | 5 | USD 11.11 | **USD 55.55** |
| 2 (only if Arsany insists on the A-034 cell) | 3027-LP503030JU+PCM+2IC+NTC+Mol.78172-350MM-ND | 5 | EUR 8.47 | **EUR 42.35** (EUR 50.40 incl. VAT), below the free-shipping threshold of EUR 66.58 |

Mating parts (not on DigiKey; I did not look up DigiKey numbers for them, **unverified there**):
- for line 1 (bare wires): the board keeps **J2 JST PH**; the mating side is a JST PHR-2 housing (LCSC C157955, 0.0135 USD) with two SPH-002T-P0.5S contacts (LCSC C111515, 0.0086 USD), crimped or bought as a PH pigtail (needs a crimp tool or Peter; polarity by the wire colours of the cell, to be checked);
- for line 2: **no mating part is needed on the cell side** (the Molex plug is on the cell); the board needs **J2b = Molex 78171-0003 (C564183)** in the JLC BOM instead of J2.
The JLC/LCSC items are board-assembly or hand-work parts and are not part of the DigiKey cart.

## 7. One comparison table, then the recommendation

| | EEMB LP603449 (A-020, current B1) | Jauch LP503030JU (A-034) | Jauch LP603443JU |
|---|---|---|---|
| Minimum / typical capacity | 1000 / 1100 mAh | 430 / 450 mAh | 850 / 900 mAh |
| NFR-01 typical (0.8 x min) | **4.5 months PASS** | **1.9 months FAIL** | **3.8 months PASS** |
| Envelope T x W x L | <= 6.3 x 34.5 x 50 mm (fits by definition) | 5.2 x 30 x 30 mm (fits, margins 1.1 / 4.5 / 21 mm) | 6.5 x 34.5 x 45 mm (0.2 mm too thick, zero width margin) |
| Protection | bare cell, **no PCM, no NTC** in the listing | PCM + 2nd IC + 10k NTC | PCM, **no NTC, no 2nd IC** |
| Connector | solder tabs; plug to be specified | Molex 78172-3 plug, 50 mm leads (3 circuits) | bare wires, 70 mm |
| Board change needed | J2 stays; PCM/NTC must be added to the purchase spec | **J2 to Molex 78171-0003 (J2b); R9 2.4k to 5.1k; R1/R2 NTC divider** | J2 stays; R9 2.4k fine; TEMP pin grounded (no NTC) |
| Max charge / discharge | 1100 mA (1C) / 2200 mA | 430 mA / 430 mA | 900 mA / 900 mA |
| Price / stock | none found, **unverified** | EUR 8.47 at 1; 85 in stock; ships in about 6 days | USD 11.11 at 1; 516 in stock; lead time 28 weeks listed |
| Source datasheet | EEMB, read | Jauch, read (no drawing) | Jauch, read |

**Recommendation: choose the Jauch LP603443JU+PCM+2 wires (DigiKey 1908-...-ND) if the bay can take 6.5 x 34.5 x 45 mm (Yara and Arsany to confirm in enclosure v3, A-020 bay is only a note so far).** It is the only DigiKey cell I found that passes NFR-01 and is close to the bay. **IEC 62133 is NO on its datasheet** (UN 38.3 yes); flagged to Arsany as a decision, not assessed here. Its price of the missing NTC is a grounded TEMP pin (no cell temperature protection beyond the PCM; the 4.P1 checklist item). **The LP503030JU does not meet NFR-01 as specified:** it falls short by a wide margin (1.9 against 3 months), needs a different connector, a different charge resistor and a firmware lever package that is neither designed nor measured. If the bay cannot change, the alternative is to ask Jauch (batterytechnology@jauch.com is on their datasheet; I send nothing) for a 603449-size cell with PCM, or keep the EEMB 603449 with a purchase spec (PCM, plug) and a source that I could not verify.

## 7b. Risks per cell (separate lines)

| Risk | LP503030JU | LP603443JU |
|---|---|---|
| NFR-01 | **fails** (1.9 months typical) | passes (3.8) |
| IEC 62133 | yes (62133-2:2017) | **NO** (UN 38.3 yes); decision for Arsany, not assessed |
| Protection | PCM + 2nd IC + NTC | PCM only: **no NTC, no 2nd IC**; TEMP pin grounded |
| Charge below 15 C | max 0.2C (0 to 15 C) cannot be enforced by the TP4056 | same rule, 0.2C = 180 mA, exceeded at R9 = 2.4k (458 mA) |
| Fit | fits with margin | +0.2 mm over the 6.3 mm minimum bay, zero width margin; swelling margin open; DigiKey 6.5 mm vs Jauch list 6.0 mm bare cell: pack drawing needed |
| Supply | 85 in stock, ships in about 6 days | **28 weeks listed vs 516 in stock: ask DigiKey/Jauch before ordering** |
| Connector | Molex 78172-3 inferred, J2b needed, polarity unknown | bare wires, own connector or pigtail |

## 8. Open and unverified

- Exact Jauch connector, wire count and pinout of the LP503030JU (no drawing in the datasheet); Molex 78172-3 = 78172-0003 and its mating header 78171-0003 are inferences.
- LP503030JU size has a single source (Jauch product list); LP603443JU size is the DigiKey attribute (6.5 mm) while Jauch's list shows 6.0 mm for the bare cell: ask Jauch for the pack drawing.
- DigiKey values were read once through a page-summary tool on 2026-11-07; stock and prices move daily, 28-week lead time of the LP603443JU is inconsistent with its stock.
- Model currents are unverified apart from the ESP32-C3 rows; NTC curve is a B-parameter approximation.
- Not done (out of scope): schematic, layout, enclosure.

# JLCPCB quote kit, plant-monitor (price estimate only)

> **QUOTE ONLY. NOT FOR ORDER. NOT A RELEASE. NOT AN ORDER FILE.** The only goal is a JLCPCB price estimate. **Do not press Pay / Place order.** The order gate is **4.P3 (Arsany's review)**, and it has not been passed. Emil (PCB Designer), 2026-11-14, branch `agent/pcb/jlc-quote-kit`. No agent logged in, uploaded, ordered or paid anything.
>
> **UNVERIFIED:** nobody opened the JLCPCB order pages in the agent session (no login, no order). Menu names and option labels below are written from the repo notes and from memory of the site and **may differ today**. Where a label does not match, pick the nearest one and write it in the table at the bottom.

## 1. Which file to upload (all in this folder)

| Step | File | Status |
|---|---|---|
| Gerber | `QUOTE-ONLY_NOT-FOR-ORDER_plant-monitor-board-main1ea7784.zip` | **Fresh.** Made by KiCad 9.0.9 in CI from `main` head `1ea7784` (board 34.50 x 67.80 mm, outline checked in the file). It is the CI `pcb-fab` artifact of run 43587580074, repacked, nothing changed. Single board only |
| BOM | `QUOTE-ONLY_bom-jlc.csv` | 27 lines, 45 parts, LCSC number on every line |
| CPL | `QUOTE-ONLY_cpl-jlc.csv` | 45 parts, all Top. X/Y/rotation equal the fresh CI `cpl.csv` |
| Not used | `../gerbers/*.zip`, `../../gerber/*.zip` | **STALE** (board 34.5 x 67.0 or older). Do not upload them |

There is **no fresh 2-up panel Gerber** in this kit: the panel needs `kicad-cli` in Docker, and the Docker image could not be pulled in the agent session. So the quote uses the **single-board file**. The 2-up panel is only a dimension scenario (section 3).

## 2. Click by click

1. Go to **jlcpcb.com**, log in with your own account. Click **Order Now** (instant quote).
2. **Add Gerber file**: upload the zip. Wait for the preview. Check it shows a **T-shaped** outline, 2 layers. (The board is not a rectangle: 34.5 x 67.8 mm bounding box, a 25.8 mm tail.)
3. Set the PCB options:

| Option | Select |
|---|---|
| Base material / Layers | FR-4, **2** layers |
| Dimensions | should read **34.5 x 67.8 mm** from the file; if it says something else, write it down and stop |
| Different design in panel | 1 |
| PCB thickness | **1.6 mm** |
| Surface finish | **HASL (lead-free)** |
| Copper weight | 1 oz (outer) |
| Via process / covering | default (vias are outside the pads) |
| Mask / silk colour | default |
| Quantity | **Scenario 1: 5**, **scenario 2: 10** boards (see 3) |
| Everything else | default |

4. Turn on **PCB Assembly** (toggle under the options). Select:

| Option | Select |
|---|---|
| Assembly side | **Top side** only (all 45 parts are top) |
| PCBA type | **Economic** if offered for this part list, else **Standard**. Write down which one the page allows |
| PCBA quantity | **2 or 3** boards in scenario 3, otherwise the same as the board quantity. (JLC's smallest PCBA quantity is UNVERIFIED) |
| Tooling holes | default (JLC adds them); if there is a "Confirm Parts Placement" checkbox, tick it so you can look at the placement |

5. **Next**: upload **BOM** and **CPL**. Click **Process BOM & CPL**.
6. On the parts page: every line should match its LCSC number. Count the **Extended** parts (expected 11 unique) and any red/"shortage" line. **Screenshot it.** Do not change a part. Note which lines JLC flags.
7. On the placement page: look at U1, J1, J2, U5, U6, U2 rotation. They are **UNVERIFIED** against JLC's library (A10 in the dry-run checklist). Screenshot. Do not fix anything, this is only an estimate.
8. Reach the **price summary** (before the address/payment step). Copy the numbers into the table in section 5. **Stop there. Do not pay.**

## 3. Scenarios to quote

| # | Scenario | Boards | PCBA | Remarks |
|---|---|---|---|---|
| 1 | Single board, small | 5 | same 5 (or the minimum, write it) | bare board minimum is probably 5 (UNVERIFIED) |
| 2 | Single board | 10 | same 10 | shows how the price per board drops |
| 3 | 2-up panel, 2-3 panels | 2-3 panels = 4-6 boards | 2-3 panels | Panel 83.0 x 79.8 mm (rails 6 mm, 18 breakaway tabs, mouse bites) per `jlcpcb/panel.py`. **No fresh panel Gerber exists**: enter it only as a dimension/panel scenario. If the page demands the file, skip scenario 3 and say so. Whether JLC accepts this panel is UNVERIFIED |

Parts you buy yourself, **not in the JLC BOM, not in the quote**: **B1 LiPo cell** (EEMB LP603449-PCM, Amazon.de ASIN B08FD39Y5R; price/stock/delivery UNVERIFIED, A-034; check JST-PH polarity with a meter before connecting). **E1 soil probe** is bare copper on the board (no part). The USB cable and the enclosure print are also not part of this quote.

## 4. What the quote will and will NOT mean

| Topic | Fact in the repo | Meaning for the quote |
|---|---|---|
| Routing | Board is **UNROUTED**: 0 of 4 signal tracks, GND zone **not filled** (278 power-section track segments only) | The price counts a board that does not work yet. A routed board has more copper but the same size, so the **fab price should barely change**. The Gerber is not what will be built |
| Placeholder footprints | **3** placeholders: E1 (probe copper), U5 AHT20 DFN-6, U6 BH1750 WSOF-6 | U5/U6 are in the BOM and CPL at placeholder pads. Part count and price are fine; JLC's placement preview for them is meaningless |
| Simulations | **4 of 5 not run** (divider, soil front end, charger, USB inrush) | Nothing proves the circuit. The quote says nothing about function |
| Stale zips | Old zips are 34.5 x 67.0 or older. **This kit's zip is fresh** (34.5 x 67.8, main `1ea7784`) | Old zips would give a wrong size. Use only the kit zip |
| CPL rotation/origin | matches the board and CI, **not checked against JLC's library** (A10, F23) | A rotation error shows only in JLC's preview, not in the price |
| Price | JLC numbers are **estimates from the page** | Not binding. Stock and prices change daily. The page may add fees at checkout (tax, customs, DHL) |
| Order gate | **4.P3 review (Arsany)** first, then a regenerated, routed package | **No order from this kit.** A real order needs routing, real footprints, sims, 4.P3 |
| DFM | JLC's engineers may flag issues (tab, J1 slots, thin silk) only after a real order | Not covered by a quote. UNVERIFIED |

## 5. What changes the price

- **Board size / panel size.** 34.5 x 67.8 mm single, or 83.0 x 79.8 mm panel. Larger area costs more per board; more boards share the one-off engineering fee.
- **Unique part count and Extended parts.** 25 unique LCSC numbers, 27 BOM lines, 45 placements. **11 unique Extended parts** (D1, J1, J2, Q1, U1-U7). JLC charges a loading fee per Extended part (amount UNVERIFIED, read it from the page). Basic parts have no such fee.
- **THT / hand-solder.** The only through-hole items are J1's shield legs and pegs (a SMD-type USB-C that JLC may treat as assembled normally; UNVERIFIED). No hand-solder parts, B1 is plugged in by you.
- **Quantity.** One-off set-up and stencil are shared by more boards at 10 than at 5.
- **Surface finish / thickness / colour.** HASL lead-free 1.6 mm is the baseline. Other finishes cost more.
- **Panel with tabs.** Panel by JLC vs by customer may carry an extra fee (UNVERIFIED).
- **Shipping.** Reutlingen, Germany: depends on the service chosen, customs/VAT at the door.

## 6. Paste JLC's numbers here (leave a blank if JLC does not show it)

| Item | Scenario 1 (5) | Scenario 2 (10) | Scenario 3 (2-up, 2-3 panels) |
|---|---|---|---|
| Date/time of quote, currency | | | |
| PCB fabrication | | | |
| Engineering / set-up fee | | | |
| PCBA set-up fee | | | |
| Stencil | | | |
| Parts (LCSC/JLC) | | | |
| Extended-part fees | | | |
| Assembly labour | | | |
| Shipping to Reutlingen (service, days) | | | |
| Tax / customs shown | | | |
| **Total** | | | |
| JLC flags (parts, placement, DFM) | | | |
| Screenshot file names | | | |

Send the filled table (and the screenshots) back to Nora/Emil. Next steps after 4.P3: routing, 3 real footprints, remaining sims, then regenerate the whole package.

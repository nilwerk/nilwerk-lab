# Hardware BOM draft (Plan 2.5, input to 4.P1)

Author: Emil (PCB Designer). Branch `agent/pcb/2.5`. **Draft, nothing ordered.** CSV: [`bom-draft.csv`](bom-draft.csv).
Live data read **2026-11-06 18:36-18:39 CET** from `lcsc.com/product-detail/<C#>.html` (stock, price breaks, SMT label, lifecycle) and `jlcpcb.com/partdetail/<C#>` (library type). Prices are **USD as shown on LCSC**; stock and prices change daily, re-check before any order (A-007 opened the hosts; part codes for AHT20, BH1750, DW01A, 8205A, green LED, JST connector were found via web search and then confirmed on the LCSC page).

## Result in one table

| | 3 boards | 1000 boards | Source / caveat |
|---|---|---|---|
| Component cost per board (23 lines, 41 pieces), USD | **6.63** | **4.04** | sum of the table below. At 3 pcs most passives are priced at LCSC's first break (min. order 20-100 pcs; you pay for the break quantity, not 3 x qty). |
| Same in EUR (assumed 1 USD = 0.90 EUR, **unverified rate**) | 5.97 | 3.64 | rate is my assumption |
| JLC Economic PCBA loading fee, 11 unique Extended parts x 3.07 USD per order | +33.77 USD per order = **+11.26 USD / board** | +0.03 USD / board | $3.07 per unique Extended part, Basic free: figure from a JLCPCB help-page search snippet (Standard PCBA is quoted at $1.53 for every unique part), **not read on a quote**; verify in the JLC cart |
| Components + loading fee per board, USD (EUR) | **17.89 (16.10)** | **4.07 (3.66)** | |
| Target (about 10 EUR) | **missed at 3 pcs** (fee dominates), met by BOM alone | **met for components** | see "Not in these numbers" |

**Not in these numbers (so this is not a full unit cost):** bare PCB, SMT assembly work, stencil/setup, shipping/duty/VAT, LiPo cell (1500-2000 mAh class; cell and enclosure fit still open, section 8 of power-budget.md), enclosure, JLC price at JLC (their own price breaks differ slightly, e.g. ESP32 module 3.0515 at 1-9 pcs on JLC vs 3.0672 on LCSC), pick-and-place failures/attrition. At 1k the ESP32-C3 module is 2.05 USD = 51 % of component cost.

## Lines

Price columns show the break used (`qty+: unit USD`); the full break list is in the CSV. "JLC" = JLCPCB library type on its part page (basic / expand = Extended; I could not read a "Preferred" flag, it showed undefined for all, so no part is claimed Preferred). Lifecycle = LCSC `productCycle`.

| Ref | Function | Qty | LCSC | MPN | LCSC stock | JLC | Lifecycle | 3 pcs unit | 1k unit | USD/board 3 pcs | USD/board 1k |
|---|---|---|---|---|---|---|---|---|---|---|---|
| U1 | ESP32-C3-MINI-1-N4 module (MCU, Wi-Fi/BLE, antenna) | 1 | [C2838502](https://www.lcsc.com/product-detail/C2838502.html) | ESP32-C3-MINI-1-N4 | 12,677 | expand | normal | 1+: 3.0672 | 650+: 2.0536 | 3.067 | 2.054 |
| U2 | 3.3 V LDO, low Iq (XC6220B331MR-G, 8 uA typ per vendor, unverified here) | 1 | [C86534](https://www.lcsc.com/product-detail/C86534.html) | XC6220B331MR-G | 18,103 | expand | normal | 1+: 0.4803 | 1000+: 0.2245 | 0.480 | 0.225 |
| U3 | LiPo charger TP4056 (500 mA programmable) | 1 | [C16581](https://www.lcsc.com/product-detail/C16581.html) | TP4056-42-ESOP8 | 88,050 | expand | normal | 5+: 0.1869 | 500+: 0.1121 | 0.187 | 0.112 |
| U4 | Cell protection DW01A | 1 | [C351410](https://www.lcsc.com/product-detail/C351410.html) | DW01A | 96,060 | expand | normal | 20+: 0.0250 | 600+: 0.0172 | 0.025 | 0.017 |
| Q1 | Dual N-MOSFET 8205A for U4 (TSSOP-8) | 1 | [C5148694](https://www.lcsc.com/product-detail/C5148694.html) | 8205A | 65,190 | expand | normal | 10+: 0.0834 | 1000+: 0.0598 | 0.083 | 0.060 |
| U5 | AHT20 temp/humidity (I2C) | 1 | [C2757850](https://www.lcsc.com/product-detail/C2757850.html) | AHT20 | 33,052 | expand | normal | 1+: 0.8054 | 1000+: 0.4423 | 0.805 | 0.442 |
| U6 | BH1750FVI light (I2C) | 1 | [C78960](https://www.lcsc.com/product-detail/C78960.html) | BH1750FVI-TR | 31,844 | expand | normal | 1+: 0.9295 | 1000+: 0.5019 | 0.929 | 0.502 |
| J1 | USB-C receptacle 16-pin (power only) | 1 | [C165948](https://www.lcsc.com/product-detail/C165948.html) | TYPE-C-31-M-12 | 314,405 | expand | normal | 5+: 0.1887 | 1000+: 0.1051 | 0.189 | 0.105 |
| D1 | USB ESD array USBLC6-2SC6 (NFR-08) | 1 | [C7519](https://www.lcsc.com/product-detail/C7519.html) | USBLC6-2SC6 | 25,630 | expand | normal | 5+: 0.1638 | 500+: 0.0897 | 0.164 | 0.090 |
| J2 | Battery connector JST PH 2-pin SMD | 1 | [C295747](https://www.lcsc.com/product-detail/C295747.html) | S2B-PH-SM4-TB(LF)(SN) | 5,995 | expand | normal | 5+: 0.2284 | 1000+: 0.1392 | 0.228 | 0.139 |
| SW1,SW2,SW3 | Tact switch BOOT, RESET, pinhole factory reset | 3 | [C318884](https://www.lcsc.com/product-detail/C318884.html) | TS-1187A-B-A-B | 740,140 | base | normal | 20+: 0.0208 | 600+: 0.0141 | 0.062 | 0.042 |
| Q2,Q3 | N-MOSFET AO3400A: battery divider switch, soil oscillator gate | 2 | [C20917](https://www.lcsc.com/product-detail/C20917.html) | AO3400A | 546,815 | base | normal | 5+: 0.0899 | 500+: 0.0562 | 0.180 | 0.112 |
| D2 | LED red (CHRG) | 1 | [C2286](https://www.lcsc.com/product-detail/C2286.html) | KT-0603R | 4,250,600 | base | normal | 100+: 0.0077 | 1000+: 0.0059 | 0.008 | 0.006 |
| D3 | LED green (STDBY/status) | 1 | [C12624](https://www.lcsc.com/product-detail/C12624.html) | KT-0603G | 345,900 | expand | normal | 50+: 0.0120 | 500+: 0.0094 | 0.012 | 0.009 |
| R1,R2 | 5.1k 0603 USB-C CC | 2 | [C23186](https://www.lcsc.com/product-detail/C23186.html) | 0603WAF5101T5E | 15,310,100 | base | normal | 100+: 0.0016 | 1000+: 0.0012 | 0.003 | 0.002 |
| R3-R6 | 10k 0603 pull-ups (EN, GPIO8/9 strap, gate) | 4 | [C25804](https://www.lcsc.com/product-detail/C25804.html) | 0603WAF1002T5E | 4,727,900 | base | normal | 100+: 0.0024 | 1000+: 0.0020 | 0.010 | 0.008 |
| R7,R8 | 1M 0603 battery divider (2 MOhm total) | 2 | [C22935](https://www.lcsc.com/product-detail/C22935.html) | 0603WAF1004T5E | 1,547,300 | base | normal | 100+: 0.0018 | 1000+: 0.0014 | 0.004 | 0.003 |
| R9 | 1.2k 0603 TP4056 PROG (~1 A? see note: 1.2k = 1 A; use 2k for 600 mA) | 1 | [C22765](https://www.lcsc.com/product-detail/C22765.html) | 0603WAF1201T5E | 1,512,000 | base | normal | 100+: 0.0035 | 1000+: 0.0027 | 0.004 | 0.003 |
| R10,R11 | 1k 0603 LED series | 2 | [C21190](https://www.lcsc.com/product-detail/C21190.html) | 0603WAF1001T5E | 2,425,400 | base | normal | 100+: 0.0017 | 1000+: 0.0014 | 0.003 | 0.003 |
| C1-C4 | 10 uF 0603 | 4 | [C19702](https://www.lcsc.com/product-detail/C19702.html) | CL10A106KP8NNNC | 1,705,760 | base | normal | 20+: 0.0205 | 4000+: 0.0119 | 0.082 | 0.048 |
| C5-C10 | 100 nF 0603 | 6 | [C14663](https://www.lcsc.com/product-detail/C14663.html) | CC0603KRX7R9BB104 | 7,150 | base | normal | 50+: 0.0102 | 4000+: 0.0059 | 0.061 | 0.035 |
| C11,C12 | 1 uF 0603 | 2 | [C15849](https://www.lcsc.com/product-detail/C15849.html) | CL10A105KB8NNNC | 1,812,550 | base | normal | 50+: 0.0109 | 1500+: 0.0073 | 0.022 | 0.015 |
| C13 | 22 uF 0603 (LDO out / Wi-Fi burst) | 1 | [C59461](https://www.lcsc.com/product-detail/C59461.html) | CL10A226MQ8NRNC | 927,380 | base | normal | 20+: 0.0172 | 600+: 0.0114 | 0.017 | 0.011 |
| | **Total** | | | | | | | | | **6.63** | **4.04** |

## Choices and why

- **U2 LDO XC6220B331MR-G (C86534)**: the power-budget model needs a low-Iq LDO (1-5 uA assumed); ME6211 (C82942, 0.04 USD) is cheaper but its quiescent current is tens of uA (vendor datasheet value from memory, **unverified**) and would break the deep-sleep budget. 700 mA output covers the Wi-Fi TX peaks; dropout at 3.4 V is still to be simulated in 4.P1. The Iq of XC6220 (about 8 uA) is **not verified here**: I did not read the Torex datasheet.
- **U3 TP4056 + U4 DW01A + Q1 8205A**: classic cheap LiPo chain. TP4056 has no power-path, so the load sees the cell during charging; accepted for a sensor node, to be reviewed in 4.P1. The charger-plus-protection drain with USB unplugged (model: 1/4/10 uA) is **unverified**; I did not read those datasheets, 4.P1 must.
- **Q1**: FS8205A (C16052) is **out of stock** (0), so HXY 8205A (C5148694, TSSOP-8, 65,190) is used. Several "8205A" listings are SOT-23-6, not TSSOP-8; check the footprint.
- **J2**: the cheap JST PH connector C173752 is through-hole, which breaks the single-side SMT assembly rule; the SMD version C295747 costs more and has only about 6k in stock.
- **J1 USB-C (C165948, Korean Hroparts TYPE-C-31-M-12)** is the usual 16-pin one; C2765186 (SHOU HAN, 0.0514 at 1k vs 0.1051) would save about 0.05 USD per board, footprint/mechanics unchecked.
- **R9 (TP4056 PROG)** is shown as 1.2k (about 1 A). Charge current for the chosen cell is a 4.P1 decision; value will change (code is a basic 0603 either way).
- **Q2/Q3**: placeholder for the divider switch and the soil-oscillator gate; the soil front end is not designed yet (no sensing IC or comparator included). The capacitive soil probe itself is PCB copper, 0 USD.
- **Excluded by design**: AMS1117-3.3 (C6186, 5 mA Iq class) as in power-budget.md.

## Flags: unverifiable or open

1. **LiPo cell not in the BOM**: no cell chosen; LCSC listings were not checked. Needs Arsany's enclosure/capacity decision.
2. **Unit conversion**: EUR figures use an assumed rate.
3. **JLC extended-part fee** not read from a live quote (needs a JLC login/cart); the 11 x 3.07 USD is the dominant cost at 3 pcs. Options: fewer unique Extended parts (e.g. use only the ESP32 module plus sensors as Extended and move the rest to Basic/Preferred equivalents), or hand-solder at prototype.
4. **JLC stock** was not extracted per part (JLC page carries only a per-variant stock field I could not map reliably); LCSC stock is shown. C14663 (100 nF, Yageo) has only 7,150 in stock, which is just above the 6,000 needed for 1k boards: switch to a second-source 100 nF before 1k.
5. **Lifecycle**: LCSC `productCycle` was "normal" for every selected part; this field is LCSC's sales status, **not** a manufacturer active/NRND/EOL statement. Manufacturer lifecycle (Espressif, ROHM, Aosong, Torex) is **unverified**; the ESP32-C3-MINI-1 and BH1750 are widely used but I did not read a product-status page.
6. **Datasheet-level parameters** of every non-ESP part (Iq, dropout, PROG resistor, thresholds) are unverified; only stock, price, package and library type come from the shops.
7. **Minimum order and packaging**: 3-board prices assume LCSC price tiers; JLC assembly consumes from its own stock and may not need the pack quantity. At 1k, LCSC reel sizes (e.g. 650 for the module, 3000 for LDO/ICs) mean buying whole reels is possible but not required.
8. **AHT20 variants**: LCSC C2757850 (Aosong AHT20, package "SMD") is used; JLC also lists another AHT20 (C503357, DFN-6 3x3) and AHT20-F (C3012622). Pick one footprint in 4.P1 and keep the code consistent with the datasheet pin-out.

Lessons: see the PR comment.

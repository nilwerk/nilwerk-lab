# Task 4.H0 - Dev-kit & sensor parts list (order list for Arsany)

Author: Emil (PCB Designer) - 2026-11-03 - Status: DRAFT, needs Theo (Architect) approval before Arsany sees it.
Needed on bench: 2026-11-05 (firmware 4.F1 starts 11-06). Supports: FR-D01 (all five measurements), FR-D06 (USB-C charging + LED), NFR-01 (battery life, current measurement on dev kit), NFR-02 (sensor accuracy/calibration), NFR-09 (cost reference), Q-02 (ESP32-C3-MINI-1).

## 0. Verification status - read first
The agent session could **not open any shop page** (WebFetch: DNS blocked for berrybase.de, galaxus.de, digikey.de, docs.espressif.com; these hosts must be allowed in the session network settings for a live check). Only web-search result snippets were available.
Therefore: **no price, stock or delivery time below is verified on the shop page.** Values marked `snippet` come from a search-result summary (undated page state, treat as hint). `UNVERIFIED` = no data at all. Nothing is invented; blank = unknown. Before clicking, Arsany (or Emil once hosts are allowed) must confirm price, stock and delivery on the page. Date checked for all rows: 2026-11-03 (search only).

## 1. Order table

Shop A = BerryBase (Germany, ships from DE; usually 1-3 working days - UNVERIFIED). Shop B = alternative.

| # | Part | Exact variant | Qty | Shop / link | Unit price incl. VAT | Total | Delivery | Stock | Checked |
|---|---|---|---|---|---|---|---|---|---|
| 1 | ESP32-C3 dev kit (primary, matches Q-02) | Espressif **ESP32-C3-DevKitM-1** (board carries ESP32-C3-MINI-1; orderable as -N4 / -N4X, N4X = 4 MB flash; MINI-1 variant, not MINI-1U which has u.FL antenna) | 2 | A: BerryBase - search "ESP32-C3-DevKitM-1" https://www.berrybase.de (no product URL found; search found no BerryBase listing) <br> B: Galaxus DE https://www.galaxus.de/en/s1/product/espressif-development-board-esp32-c3-devkitm-1-development-boards-kits-21611156 <br> C: DigiKey https://www.digikey.es/en/products/detail/espressif-systems/ESP32-C3-DEVKITM-1-N4X/25587617 | UNVERIFIED | UNVERIFIED | UNVERIFIED | snippet: some listings show stock (one shows 213 pcs); **Mouser marked Obsolete, GridConnect says discontinued** - check lifecycle | 2026-11-03 |
| 2 | LiPo charger | The DevKitM-1 has **no LiPo charger** (USB-UART only; Espressif guide - not page-verified). Use a separate TP4056-type USB-C charger module **with protection (DW01 + FS8205)**, e.g. BerryBase "TP4056 USB-C Lade-Modul mit Schutz" | 2 | A: BerryBase (search "TP4056 USB-C"); B: Amazon.de/AZ-Delivery same type | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | 2026-11-03 |
| 3 | LiPo cell | 1S 3.7 V, **1000-2000 mAh, JST-PH 2.0 or bare wires** (pick one with protection circuit; connector must match charger/board, see 3.4) | 2 | A: BerryBase (search "LiPo 3.7V 1000mAh"); B: Adafruit-compatible via Pimoroni/Reichelt | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | 2026-11-03 |
| 4 | Temp/humidity | **AHT20 breakout**, I2C, 3.3 V-capable (Adafruit 4566 STEMMA QT, or DFRobot Fermion SEN0527, or Seeed Grove AHT20) | 2 | A: BerryBase Seeed Grove AHT20 https://www.berrybase.de/seeed-grove-i2c-temperatur-und-feuchtigkeitssensor-fuer-industrielle-anwendungen-aht20 <br> B: DigiKey Adafruit 4566 https://www.digikey.bg/en/products/detail/adafruit-industries-llc/4566/12396895 | snippet: 6.40 EUR (Grove, undated; note: Grove cable/connector, needs jumper adaptation) | 12.80 EUR (if 6.40 holds) | UNVERIFIED | snippet: listed | 2026-11-03 |
| 5 | Light | **BH1750 (GY-302) breakout**, I2C | 2 | A: BerryBase https://www.berrybase.de/en/bh1750-digital-light-sensor <br> B: any GY-302 seller (eBay.de/Amazon.de) | snippet: 2.40 EUR | 4.80 EUR | UNVERIFIED | snippet: "immediately available" (undated) | 2026-11-03 |
| 6 | Soil moisture | **Capacitive soil moisture sensor v1.2**, analog, 3.3-5.5 V (check it has the TL555/regulator variant, which works at 3.3 V; "v1.2" boards are often poorly built - buy 2) | 2 (+1 spare = 3) | A: BerryBase "Analoger kapazitiver Bodenfeuchtesensor" art. no. CAP-SHYG (version not stated) - find via berrybase.de search <br> B: https://openelab.io/de/products/soil-moisture-sensor (v1.2) | snippet: 2.60 EUR (CAP-SHYG) | 7.80 EUR for 3 | UNVERIFIED | UNVERIFIED | 2026-11-03 |
| 7 | Breadboard + jumpers | Half-size 400-pt breadboard + 40x M/M and 20x M/F Dupont jumper wires | 2 + 1 set | A: BerryBase (search); B: Amazon.de | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | 2026-11-03 |
| 8 | USB cable | USB-A/C to USB-C data cable (if Arsany has none) | 1 | own stock | - | - | - | - | - |

## 2. Total cost
- **Verified total: not possible** (no page could be opened).
- Snippet-based partial (rows 4, 5, 6): 12.80 + 4.80 + 7.80 = **25.40 EUR** incl. VAT, excluding shipping.
- Rows 1, 2, 3, 7 have no price data. Do not budget from this table; Arsany sees live cart totals on the shop and should compare to a planning ceiling set by Theo/Nora (not set by me, no price basis).

## 3. Compatibility notes
1. **Logic level:** ESP32-C3 GPIO is 3.3 V and not 5 V tolerant. Power all sensors from the dev kit 3V3 pin. AHT20 and BH1750 breakouts: confirm the board has no 5 V-only regulator/level-shifter quirk (Adafruit 4566 and GY-302 run from 3.3 V; GY-302 pull-ups are 3.3 V when powered from 3V3).
2. **I2C addresses:** AHT20 = 0x38 (fixed). BH1750 = 0x23 (ADDR low/floating) or 0x5C (ADDR high). No conflict; both on one bus. Suggested pins (to be fixed by Mira/4.F1 and board.h): SDA = GPIO8, SCL = GPIO9 (the DevKitM-1 uses GPIO8 for the on-board RGB LED and GPIO9 for BOOT - Mira must confirm; alternative GPIO4/GPIO5). Note: several breakouts add their own pull-ups; two breakouts in parallel are fine.
3. **Soil probe ADC:** ESP32-C3 ADC1 channels = GPIO0-GPIO4 (ADC2/GPIO5 is unusable with Wi-Fi active). Use e.g. **GPIO3 (ADC1_CH3)**, probe powered from a GPIO or 3V3, output 0..~3 V analog; set ADC attenuation 11 dB (ESP-IDF 5.x `ADC_ATTEN_DB_12`). Sensor output is nonlinear and board-dependent - per-unit dry/wet calibration is needed (NFR-02). Power the probe from a switched GPIO to save battery in deep sleep (NFR-01). Pin choice is a proposal for Mira/Theo, not a decision.
4. **LiPo polarity warning:** JST-PH/JST-PH-2.0 LiPo cells from different sellers are **wired with opposite polarity** (Adafruit vs. generic). Check the red/black wire against the charger "B+/B-" pads with a multimeter before connecting; a reversed cell can destroy the charger module. Never buy a cell without protection circuit. TP4056 charges to 4.2 V at 1 A default (R_prog 1.2 kOhm) - for a 1000 mAh cell that is 1C, acceptable; use a cell >= 1000 mAh.
5. **Power path:** the DevKitM-1 3V3 LDO input pin "5V" is not meant for 4.2 V LiPo-direct tuning of the regulator drop-out; feed LiPo (via charger OUT+/OUT-) to the 5V pin only after checking the LDO dropout at 3.5-4.2 V (Emil will simulate in 2.3/4.P1; for bench 11-05 powering over USB is the baseline, battery run is secondary). Battery-sense divider is not on the dev kit: add 2x 100 kOhm 1 % resistors (from stock) to a free ADC1 pin (e.g. GPIO2) for FR-D01 battery level.
6. **Module match:** DevKitM-1 uses the ESP32-C3-MINI-1 module (same as the custom board, Q-02); N4/N4X = 4 MB flash, enough for dual-OTA partitioning (FR-D05) - architect to confirm flash size.

## 4. Open points for Theo (approval)
- Approve variant ESP32-C3-DevKitM-1-N4X (or -N4) vs. an alternative with built-in LiPo charger (not researched here; none found in search).
- Lifecycle: Mouser/GridConnect mark the DevKitM-1 obsolete/discontinued; confirm availability in DE before ordering; fallback is ESP32-C3-DevKitC-02 (MINI module variant not verified here).
- Confirm I2C/ADC pin proposals with Mira (4.F1) so the wiring on the bench matches `board.h`.

## 5. For Arsany (after Theo approves)
1. Allow berrybase.de, galaxus.de, digikey.de in the session network (or let Emil re-run the check) - or open each link, confirm "in stock", price and delivery date <= 2026-11-05.
2. Add the rows 1-7 to the cart at one shop if possible (BerryBase for all except dev kit if not listed). Ordering is done by Arsany only.
3. Resistors 2x100 kOhm: check own stock.

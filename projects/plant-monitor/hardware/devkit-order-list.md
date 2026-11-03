# Task 4.H0 - Dev-kit & sensor parts list (order list for Arsany)

Author: Emil (PCB Designer) - 2026-11-03 - Status: REVISED after Theo's review (PR #1): approved with conditions, see section 5 'Check before click'.
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
2. **I2C addresses:** AHT20 = 0x38 (fixed). BH1750 = 0x23 (ADDR low/floating) or 0x5C (ADDR high). No conflict; both on one bus. Several breakouts add their own pull-ups; two breakouts in parallel are fine.
   **I2C pins (proposal, final map is Mira's in `board.h`): SDA = GPIO6, SCL = GPIO7.** Do **not** use GPIO2, GPIO8 or GPIO9: these are the ESP32-C3 strapping pins (from the chip datasheet, my knowledge, not page-verified today); a sensor or pull-up there can disturb boot or force download mode. On the DevKitM-1, GPIO8 also drives the on-board RGB LED and GPIO9 is the BOOT button (per Theo's review and the Espressif board guide; **unverified on the actual board**). The USB-UART bridge uses UART0 (GPIO20/GPIO21 on the C3, **unverified for this board**), so keep those free too. GPIO4/GPIO5 is an acceptable alternative pair (GPIO4 then is no longer free as ADC1 input). Whatever is wired on the bench must match `board.h`.
3. **Soil probe ADC:** ESP32-C3 ADC1 channels = GPIO0-GPIO4 (ADC2/GPIO5 is unusable with Wi-Fi active). Use e.g. **GPIO3 (ADC1_CH3)**, probe powered from a GPIO (suggest GPIO4) or 3V3, output 0..~3 V analog; set ADC attenuation 11 dB (ESP-IDF 5.x `ADC_ATTEN_DB_12`). Sensor output is nonlinear and board-dependent - per-unit dry/wet calibration is needed (NFR-02). Power the probe from a switched GPIO to save battery in deep sleep (NFR-01). Pin choice is a proposal for Mira/Theo, not a decision.
4. **LiPo polarity warning:** JST-PH/JST-PH-2.0 LiPo cells from different sellers are **wired with opposite polarity** (Adafruit vs. generic). Check the red/black wire against the charger "B+/B-" pads with a multimeter before connecting; a reversed cell can destroy the charger module. Never buy a cell without protection circuit. TP4056 charges to 4.2 V at 1 A default (R_prog 1.2 kOhm) - for a 1000 mAh cell that is 1C, acceptable; use a cell >= 1000 mAh.
5. **Power path and battery sense:**
   - **Do not feed the LiPo into the dev kit "5V" pin.** The on-board LDO needs roughly 1 V of headroom, so it drops out well above the cell's empty voltage; in addition the USB-UART bridge, LED and LDO quiescent current dominate the sleep current (LDO/bridge behaviour from my knowledge of the board, not measured).
   - **Bench baseline is USB.** The dev kit therefore **cannot give a valid NFR-01 deep-sleep/battery-life number**; never quote a dev-kit sleep current as the product figure. Valid NFR-01 measurements (task 5.4) need the module powered at 3V3 from a regulated source with the bridge not drawing, or the custom board.
   - **Battery-sense divider** (not on the dev kit): 2x 100 kOhm 1 % (own stock) from the cell/charger OUT+ to GND, midpoint to **GPIO0 (ADC1_CH0)** (alternative GPIO1). **Not GPIO2** (strapping). Midpoint max is about 2.1 V at 4.2 V, within range with 11 dB attenuation. Divider leakage is about 21 uA, which is acceptable on the bench but not for the product (Emil simulates the production divider in 2.3/4.P1). Final pin: Mira, `board.h`.
6. **Module match:** DevKitM-1 uses the ESP32-C3-MINI-1 module (same as the custom board, Q-02); N4/N4X = 4 MB flash, enough for dual-OTA partitioning (FR-D05) - architect to confirm flash size.

## 4. Open points (status after Theo's review)
- Flash size: confirmed by Theo, 4 MB (N4 or N4X) is enough for dual OTA (FR-D05). Closed.
- Pin proposals: replaced by non-strapping pins (sections 3.2, 3.3, 3.5); Mira confirms in `board.h` (4.F1).
- Lifecycle: Mouser/GridConnect mark the DevKitM-1 obsolete/discontinued (from search snippets, unverified). Handled by the check list and fallback in section 5.
- Alternative with built-in LiPo charger: Seeed XIAO ESP32C3 (Theo's note, from his knowledge, unverified). Optional extra for battery tests, not required for the bench, not in the cart.

## 5. For Arsany: check before click
Ordering, payment and terms stay with Arsany. Do not pay until every point holds.
1. **Dev kit (row 1):** the page says `ESP32-C3-DevKitM-1` (N4 or N4X), is **in stock**, is **not** marked discontinued/obsolete/"no longer available", and delivery is **on or before 2026-11-05** (4.F1 starts 11-06).
2. **Module:** photo/description shows **MINI-1 (PCB antenna), not MINI-1U** (u.FL), and pin headers are soldered.
3. **Charger (row 2):** has **DW01 + FS8205** protection and USB-C. **LiPo (row 3):** has a protection circuit, 1000 mAh or larger. **Polarity:** before connecting any cell, check red/black against B+/B- with a multimeter. Charge on a non-flammable surface, attended, for the first cycles.
4. **Breakouts (rows 4, 5):** pin headers included **and soldered**; if you cannot solder, take pre-soldered versions. Adafruit 4566 (STEMMA QT) ships with loose headers and needs a QT-to-male cable; GY-302 usually ships with loose headers; Seeed Grove AHT20 needs the Grove cable cut or an adapter (so Adafruit 4566 or a plain AHT20 breakout is easier).
5. **Soil sensor (row 6):** listing says **v1.2 and 3.3 V-capable** (on-board regulator, TL555 variant). Order 3 as listed.
6. **Resistors:** 2x 100 kOhm 1 % - confirm own stock, else add to the cart.
7. **Cart total <= 80 EUR incl. shipping** (Theo's planning ceiling, a proposal from his knowledge, not a verified price). If the live cart is above, stop and ask Nora before paying.
8. Allow berrybase.de, galaxus.de, digikey.de in the session network (or let Emil re-run the check) if you want a pre-check.

**Fallback (Theo):** if the DevKitM-1 is not orderable in DE at a sane price with delivery in time, buy **ESP32-C3-DevKitC-02** (qty 2) and tell Nora, who tells Mira. It carries an **ESP32-C3-WROOM-02** module, not MINI-1 (different module, antenna layout and pin breakout): fine for firmware bring-up (same silicon), not an exact replica of the production module. **Do not substitute silently**: Mira must know which board arrived so `board.h` matches. No third-party clones with unclear module markings.

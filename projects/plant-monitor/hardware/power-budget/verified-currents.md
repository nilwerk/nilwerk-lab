# Verified currents: ESP32-C3, datasheet vs. power_budget.py (Plan 2.3, what-if)

Author: Emil (PCB Designer). Read 2026-11-06 18:20-18:45 CET. Model `power_budget.py` is **unchanged**; this file lists differences and a what-if (script call at the end).

## What could and could not be read

| Source | Reachable? |
|---|---|
| ESP32-C3 series datasheet PDF (`documentation.espressif.com/esp32-c3_datasheet_en.pdf`, `www.espressif.com/sites/default/files/documentation/...`) | **No.** The proxy returns 403 (CONNECT tunnel failed) for both hosts. Only `docs.espressif.com` is open, and it carries the ESP-IDF programming guide, not the datasheet. |
| ESP-IDF docs on `docs.espressif.com` (ESP32-C3, stable): *Low Power Mode in Wi-Fi Scenarios*, *Low Power Mode in Soc Scenarios*, *Sleep Modes* | Yes. |

So **I could not read datasheet page/section numbers** for deep sleep, light sleep, Wi-Fi TX/RX (the datasheet "Current Consumption" tables in section 5 and the RF-power current table are not available to me). The values below come from the ESP-IDF guide pages (Espressif's own measured values, chip level) and are labelled as such. Datasheet TX/RX stays **unverified**; do not treat the guide numbers as datasheet limits.

## Values read, with location

| Quantity | ESP-IDF guide value | Where (docs.espressif.com/projects/esp-idf/en/stable/esp32c3/...) | Conditions stated |
|---|---|---|---|
| Deep sleep, average | **about 4.8 uA** | `api-guides/low-power-mode/low-power-mode-wifi.html`, section "Deep-sleep Mode + Wi-Fi Scenario", Configuration Performance | recommended deep-sleep configuration, chip-level test setup, not a module with its flash leakage at temperature |
| Light sleep (auto), Wi-Fi connected | average **1.4 mA** (DTIM 1), **0.62 mA** (DTIM 3), **0.31 mA** (DTIM 10); min **0.14 mA**; max 86-87 mA | same page, section "Auto Light-sleep Mode + Wi-Fi Scenario", Configuration Performance | 160 MHz, associated to an AP; includes periodic beacon wake-ups. Not the same as light sleep without Wi-Fi |
| Modem sleep + DFS, Wi-Fi connected, idle | average **10.3-11.4 mA**, min 5.0 mA, max about 81-83 mA | same page, section "Modem-sleep Mode", Configuration Performance | DFS on, DTIM 1/3/10 |
| Modem sleep without DFS, 160 MHz | average **20.7-21.5 mA** (min 20.5 mA), max **83-230 mA** | same table | CPU at 160 MHz fixed |
| Wi-Fi TX / RX current at given rate and power | **not given** in these pages | datasheet only (unreadable) | |
| ESP32-C3-MINI-1 module-level deep sleep / flash standby | **not given**; the *Sleep Modes* page says SPI flash standby is typically below 30 uA and 10-30 uA if left powered | `api-reference/system/sleep_modes.html`, SPI Flash power notes | relevant to the model's worst case |

## Side by side with the model

| Parameter | Model best / typical / worst | Guide value | Difference |
|---|---|---|---|
| `i_mcu_sleep_ua` (deep sleep) | 5 / 5 / 10 uA (tag datasheet-unverified, "about 5 uA") | 4.8 uA | Agrees (-4 %); the worst 10 uA covers module flash leakage, which the guide does not state |
| `i_cpu_ma` (CPU active, radio off) | 15 / 20 / 30 mA | 20.5-21.5 mA (160 MHz, no DFS, Wi-Fi associated, idle) | Typical is 1.5 mA low (7 %); inside best-worst range. Associated Wi-Fi idle is a proxy, not "radio off" |
| `i_rx_ma` | 70 / 85 / 100 mA | Max current in listen/modem-sleep tables 81-87 mA (peak, not a continuous RX figure) | Consistent; says nothing about continuous RX |
| `i_tx_ma` | 200 / 260 / 340 mA | not given | **Unverified**; maximum spikes in the no-DFS tables (192 mA, 230 mA) are for idle Wi-Fi traffic, not for TX at full power |
| Light-sleep lever (`i_warmup_cpu_ma`, order 0.1-1 mA, tag datasheet-unverified) | 0.1-1 mA, warm-up lever only | 0.14 mA min, 0.31-1.4 mA average with Wi-Fi associated | Order of magnitude confirmed; the actual figure with Wi-Fi off and the soil oscillator running must be measured in M3 |

## What-if on the NFR-01 verdict

NFR-01 in the repo is **6 months = 4380 h** (`NFR01_HOURS`); your brief said "3-month", so I show the 3-month column (2190 h) as well. Run with `power_budget.py` functions (`with_()` overrides of the typical/best/worst `Params`, nothing edited); "rated mAh needed" = smallest rated 1S LiPo that reaches the target by the literal rule (0.8 x rated / average current).

| What-if | Case | Whole-board sleep uA | mAh/day | Rated mAh needed, 6 mo | Rated mAh needed, 3 mo | Months @1500 mAh | Months @2000 mAh |
|---|---|---|---|---|---|---|---|
| Baseline (model as is) | best | 8.3 | 2.06 | 470 | 235 | 19.1 | 25.5 |
| | typical | 13.2 | 5.86 | 1336 | 668 | 6.7 | 9.0 |
| | worst | 31.7 | 19.13 | 4364 | 2182 | 2.1 | 2.7 |
| A: deep sleep 4.8 uA | best | 8.1 | 2.06 | 469 | 235 | 19.2 | 25.6 |
| | typical | 13.0 | 5.85 | 1335 | 668 | 6.7 | 9.0 |
| | worst | 26.5 | 19.00 | 4335 | 2168 | 2.1 | 2.8 |
| B: A + CPU 21.5 mA | best | 8.1 | 2.35 | 535 | 268 | 16.8 | 22.4 |
| | typical | 13.0 | 5.97 | 1361 | 681 | 6.6 | 8.8 |
| | worst | 26.5 | 18.15 | 4142 | 2071 | 2.2 | 2.9 |
| C: B + RX 83 mA in all cases | best | 8.1 | 2.54 | 579 | 290 | 15.5 | 20.7 |
| | typical | 13.0 | 5.90 | 1345 | 673 | 6.7 | 8.9 |
| | worst | 26.5 | 16.58 | 3783 | 1891 | 2.4 | 3.2 |
| D: B + soil warm-up in light sleep at 0.31 mA (lever, the guide's DTIM 10 average) | best | 8.1 | 1.78 | 406 | 203 | 22.2 | 29.5 |
| | typical | 13.0 | 5.12 | 1168 | 584 | 7.7 | 10.3 |
| | worst | 26.5 | 17.02 | 3884 | 1942 | 2.3 | 3.1 |

(C overwrites the model's RX in all three cases, so best gets worse and worst better; it only shows sensitivity.)

**Effect on the verdict:** none in kind. With the guide values the typical case moves by less than 2 % (1336 to 1335-1361 mAh rated needed for 6 months), the verdict stays "not provable yet; typical passes with a 1500 mAh-class cell for 6 months (6.6-6.7 months), worst-case stack fails with any plausible cell". For a **3-month** target the typical case needs only about 670-680 mAh rated, the worst stack about 1900-2200 mAh, so a 1500 mAh cell passes typical (13 months) and a 2000 mAh cell passes even the worst stack (2.7-3.2 months) only marginally for the worst. The model's remaining uncertainty is not the sleep or CPU term but the Wi-Fi session time and TX current, which the guide does not give and the datasheet was unreachable for. Deep sleep is a small term anyway (about 0.3 mAh/day of 5.9).

Reproduce (from this folder): import `power_budget as pb`, loop `pb.SCENARIOS`, `q = pb.with_(p, i_mcu_sleep_ua=4.8, i_cpu_ma=21.5)`, then `pb.daily_budget(q)`, `pb.required_rated_mah(q)` and `pb.required_rated_mah(q, hours=2190)`, `pb.life_days(q, 1500) / pb.MONTH_DAYS`.

## Open

- Fetch the datasheet (sections: Current Consumption, RF power consumption in Active mode; Deep-sleep/Light-sleep rows) once `documentation.espressif.com` or `espressif.com` is allowed (add to A-007), then fill the TX/RX rows with page numbers.
- Module-level (MINI-1-N4) deep sleep with the stacked flash: only a measurement (5.4) settles it.

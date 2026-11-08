# Power budget and battery life (task 2.3, NFR-01)

Author: Emil (PCB Designer) · Date: 2026-11-04 · Status: **draft for the G2 review, all inputs are estimates**
Calculator: [`power_budget.py`](power_budget.py) (Python 3.11, stdlib only) · Tests: [`test_power_budget.py`](test_power_budget.py)
Traces to: NFR-01 (best and typical case >= 3 months, worst case > 1 month: relaxed by Arsany 2026-11-08, see section 12 and ADR-015; 3 months was A-020; 6 months is an information-only stretch goal), FR-D01 (15-min sampling), FR-D02 (hourly report), FR-E03/E04 (critical wake, inference), ADR-012 (second MQTT publish), PR #2 items 12 and 19.

**Nothing in this document is a measurement.** Every current and time is either quoted from a repo document, recalled from a datasheet that has not been read (the ESP32-C3 series datasheet was read on 2026-11-07, section 11), or an engineering assumption. Each is tagged in section 4. Task 5.4 replaces them (section 9).

## 1. Result

Headline figures apply **Arsany's NFR-01 rule literally** (PR #2 item 12, acceptance matrix): projected life = **0.8 x rated capacity / average current**, compared per scenario with the **relaxed NFR-01 (Arsany, 2026-11-08, A-034 answer): best and typical case >= 2190 h (3 months), worst case > 730 h (more than 1 month)** (before 2026-11-08 the worst case had to reach 3 months too; section 12). There is **no self-discharge term** in that rule. Self-discharge is shown only as a separately labelled **extra-margin** line ("+SD" / "extra"), never in a verdict.

| Question | Answer (estimates) |
|---|---|
| Average load, typical | **5.9 mAh/day** = 0.244 mA (sleep 0.3, 96 sample wakes 1.8, 24 hourly Wi-Fi sessions + 1 critical wake 3.8) |
| Rated 1S LiPo needed for 3 months (2190 h), typical, per the rule | **about 670 mAh rated** (0.8 x 668 = 534 mAh derated = the 2190 h load) |
| Best / worst case, per the rule | best **about 240 mAh**, worst **about 2180 mAh** (every parameter at its worst at once; a **stress bound** to be measured in 5.4, not a design point) |
| Does a 1500 mAh-class cell make it? (rule) | Typical: **yes, 6.7 months** (1200 mAh derated / 0.244 mA = 4917 h >= 2190 h). A 2000 mAh-class cell: typical **9.0 months**, best 25.5, worst 2.7. **The BOM cell (603449, 1000 mAh minimum): typical 4.5 months = PASS for 3 months with 1.5x margin** (4.9 at 1100 mAh nominal); best 12.8; worst stack 1.4 months (stress bound; **passes the relaxed worst-case rule, > 1 month**) |
| Extra margin line (not the rule): with cell self-discharge, assumed 2 %/month | 1500 mAh: **5.8 months** (still passes 3 months); 2000 mAh: **7.3 months**; 1000 mAh: 4.0 months; rated capacity needed 722 mAh instead of 668 mAh |
| What dominates | Wi-Fi sessions are **65 %** of the budget, sample wakes 30 %, deep sleep only **5 %** |
| Deep-sleep limit for the requirement (PR #2 item 19) | Per the rule, typical Wi-Fi and sampling terms: **500 uA whole board for a 2000 mAh rated cell, 317 uA for 1500 mAh** (with self-discharge: 445 uA and 276 uA). The accepted requirement is **<= 50 uA**, design target <= 25 uA (NFR-12, A-027), far inside these limits; table in section 6 |
| Biggest levers (section 7) | Light sleep during the soil warm-up: **-0.78 mAh/day (-13 %)**; fast connect + hub every 2nd report: **-1.4 mAh/day**; hub unreachable every hour costs **+1.4 mAh/day** |
| Verdict on NFR-01 | **Typical case passes** the 3-month requirement with the 1000 mAh-minimum BOM cell (4.5 months, rated capacity needed about 670 mAh). The worst-case stack (1.4 months at 1000 mAh, 1.36 with the as-built sleep currents, margin 1.36x over the 1-month limit) is a stress bound with every parameter at its worst at once; **under the relaxed rule it passes**, and it is still to be measured in 5.4. Everything hinges on Wi-Fi connect time and current, which only 5.4 can settle, and on the cell that fits the enclosure (section 8). The levers are in section 7 |

**NFR-01 (A-020, relaxed 2026-11-08):** best and typical case 3 months (2190 h), worst case more than 1 month (730 h), all by the literal rule, no self-discharge term; "+SD" and the 6-month stretch goal (4380 h) are information lines only. A LiPo loses roughly 1-3 % per month by itself (assumption, no datasheet); at 2 %/month the typical 1000 mAh cell still reaches 4.0 months, the needed rated capacity rises from 668 to 722 mAh.

Verdict table for the decided cell, EEMB LP603449-PCM from Amazon (A-034 decided 2026-11-08; generated; the verdict uses the 1000 mAh minimum, A-021; the 1100 mAh typical value is information only). "model baseline" = the section 4 parameters; "as-built sleep" = the board after A-045 (sleep currents of `pcb/pinmap-sleep.md`: LDO 8 uA, divider 2.1 uA permanent, section 12):

<!-- BEGIN:cell -->
| cell capacity | sleep basis | case | derated mAh | average uA | life h (rule) | months (rule) | NFR-01 needs | verdict | extra: months incl. SD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1000 mAh minimum (verdict, A-021) | model baseline | best | 800 | 86 | 9317 | 12.8 | >= 2190 h | PASS | 11.0 |
| 1000 mAh minimum (verdict, A-021) | model baseline | typical | 800 | 244 | 3278 | 4.5 | >= 2190 h | PASS | 4.0 |
| 1000 mAh minimum (verdict, A-021) | model baseline | worst | 800 | 797 | 1004 | 1.4 | > 730 h | PASS | 1.3 |
| 1000 mAh minimum (verdict, A-021) | as-built sleep | best | 800 | 99 | 8065 | 11.0 | >= 2190 h | PASS | 9.7 |
| 1000 mAh minimum (verdict, A-021) | as-built sleep | typical | 800 | 252 | 3169 | 4.3 | >= 2190 h | PASS | 3.9 |
| 1000 mAh minimum (verdict, A-021) | as-built sleep | worst | 800 | 805 | 994 | 1.4 | > 730 h | PASS | 1.3 |
| 1100 mAh typical (info only) | model baseline | best | 880 | 86 | 10249 | 14.0 | >= 2190 h | PASS | 11.9 |
| 1100 mAh typical (info only) | model baseline | typical | 880 | 244 | 3606 | 4.9 | >= 2190 h | PASS | 4.4 |
| 1100 mAh typical (info only) | model baseline | worst | 880 | 797 | 1104 | 1.5 | > 730 h | PASS | 1.4 |
| 1100 mAh typical (info only) | as-built sleep | best | 880 | 99 | 8872 | 12.2 | >= 2190 h | PASS | 10.6 |
| 1100 mAh typical (info only) | as-built sleep | typical | 880 | 252 | 3486 | 4.8 | >= 2190 h | PASS | 4.3 |
| 1100 mAh typical (info only) | as-built sleep | worst | 880 | 805 | 1093 | 1.5 | > 730 h | PASS | 1.4 |
<!-- END:cell -->

The **NFR-12 value (50 uA, design target 25 uA) is accepted by Arsany (A-027)**; the derivation behind it is in section 6.

## 2. Inputs and decisions applied

- **Capacity rule (Arsany, PR #2 item 12), applied literally:** use the **rated** capacity of the chosen 1S LiPo with **20 % derating**; projected life = derated capacity / average current >= 2190 h (NFR-01, 3 months); no self-discharge term. Both numbers are stated everywhere (rated and derated = 0.8 x rated).
- **Low-battery warning at 3.4 V** (source: Arsany's answer "ok" to Needs Arsany **A-008.2**, "low-battery 3.4 V", in the PR #2 thread; confirmed by Theo's architect review of this PR; PR #15's schema uses 3400 mV as default). Consequences: (a) the 3 months are counted to the point of the warning, the charge left below 3.4 V is a reserve and is **not** counted; (b) the 20 % derating is taken to cover the capacity that is unusable above 3.4 V, temperature and ageing, and self-discharge (closed, section 1) (`usable_fraction` = 1.0 in the model); 5.4 must check this with a discharge curve at the real load (section 9); (c) with a 3.3 V LDO the headroom at the warning point is only 100 mV, so dropout under Wi-Fi TX peaks must be simulated in 4.P1 (LDO dropout sim, role file) or a lower-dropout/boost-buck path chosen.
- **Scope of the load:** 15-min wake (soil, AHT20, BH1750, battery ADC, both edge-AI models) + hourly Wi-Fi report (cloud POST **and** MQTT publish to the Pi hub, ADR-012) + critical-event Wi-Fi wakes (edge-ai-concept 2.4: at most one per class per 6 h). **Excluded:** BLE setup (setup mode only, ADR-011), OTA downloads, Wi-Fi outage retries, charging losses, USB-powered time. These add load: OTA and outages must be bounded in 4.F (e.g. OTA only above a battery threshold, already in ADR-009; backoff already in architecture section 5).
- NFR-01 = 3 months = **2190 h** (A-020; `NFR01_MONTHS` x 730 h in `power_budget.py`); the 6-month stretch goal is 4380 h, information only.

## 3. Model

Battery-terminal charge per day, 3.3 V rail from an LDO (load current = battery current):

```
sleep   = I_sleep(board) x 24 h
sample  = 96 wakes x [ (t_boot + t_infer + t_store) x I_cpu + t_sense x (I_cpu + I_periph) ]
wifi    = (24 reports + critical wakes) x (t_connect + t_cloud + t_hub / hub_every_n) x I_wifi_avg
I_wifi_avg = f_tx x I_tx + (1 - f_tx) x I_rx
rated capacity needed  C = load(NFR01_HOURS = 2190 h) / 0.8            (Arsany's rule, headline)
extra margin only      C = load(NFR01_HOURS) / (0.8 - self_discharge_per_month x NFR01_MONTHS)
```

Self-discharge is the cell's own loss as a fraction of rated capacity per month; at 2 %/month it would cost 6 % of rated capacity over 3 months and is the reason the extra-margin line needs 1570 mAh where the rule needs 1340 mAh. It is **not** part of the rule (section 1 question). The inference (Invoke) is in the model, but at 1-50 ms it is below 0.5 % of a sample wake; the sample wake is dominated by the 1.5-3 s soil warm-up, during which the baseline keeps the CPU active (20 mA); the light-sleep lever (section 7) changes only that part (`t_warmup_s`, `i_warmup_cpu_ma`). A sample wake and the Wi-Fi session in the same hour are modelled as separate (the Wi-Fi session adds connect time only, boot is already paid).

## 4. Parameters with sources (best / typical / worst)

Status: **Q** = quoted from a repo document (cited), **D?** = recalled from the named datasheet, **not read**, unverified; **DR** = datasheet read on 2026-11-07 (table cited, see section 11); **A** = assumption; **C** = computed.

| Parameter | Best | Typical | Worst | Status and source |
|---|---|---|---|---|
| MCU deep sleep (RTC timer), uA | 5 | 5 | 10 | **DR** ESP32-C3 series datasheet v2.4, Table 5-9 p. 57: deep sleep 5 uA typ; worst adds module-flash leakage (A, module datasheet unread) |
| LDO quiescent, uA | 1 | 2 | 5 | **A** part not chosen (4.P1); needs a low-Iq part, an AMS1117-class LDO (mA) is excluded |
| Charger + protection from BAT, USB unplugged, uA | 1 | 4 | 10 | **A** parts not chosen (4.P1) |
| Battery divider total R, MOhm -> uA at 3.7 V | 4 -> 0.93 | 2 -> 1.85 | 1 -> 3.7 | **C** 3.7 V / R; design choice in 4.P1 (high-side switch gives about 0) |
| AHT20 sleep, uA | 0.25 | 0.25 | 1 | **D?** Aosong AHT20 datasheet (about 0.25 uA) |
| BH1750 power-down, uA | 0.01 | 0.01 | 1 | **D?** ROHM BH1750FVI datasheet (about 0.01 uA) |
| Soil oscillator gate leakage, uA | 0.1 | 0.1 | 1 | **A** |
| **Whole-board deep sleep, uA** | **8.3** | **13.2** | **31.7** | sum of the rows above |
| Wake interval, min | 15 | 15 | 15 | **Q** FR-D01, edge-ai-concept 2.1 |
| Boot from deep sleep, s | 0.15 | 0.30 | 0.60 | **A** |
| Sense (warm-up, samples, AHT20, BH1750, ADC), s | 1.5 | 2.5 | 3.0 | **Q** edge-ai-concept 2.4: warm-up >= 1.5 s, about 2-3 s with samples (estimate) |
| Inference model A + B, s | 0.002 | 0.010 | 0.050 | **Q** edge-ai-concept 2.2/2.3 estimates (<1 ms and a few ms), limit 50 ms (FR-E04) |
| of which pure soil warm-up (CPU can wait), s | 1.0 | 1.5 | 2.0 | **Q** edge-ai-concept 2.4: warm-up >= 1.5 s; best/worst **A** |
| Ring-buffer store, s | 0.02 | 0.05 | 0.10 | **A** |
| CPU active, radio off, mA | 15 | 20 | 30 | **DR** ESP32-C3 datasheet v2.4, Table 5-8 p. 57: CPU running 160 MHz 23 mA (28 mA with peripheral clocks on); model best/typical are below this (what-if in section 11) |
| Soil oscillator + I2C sensors while sensing, mA | 1.5 | 3.5 | 7 | **A** (AHT20 tens of uA and BH1750 about 0.12 mA are **D?**) |
| Reports per day | 24 | 24 | 24 | **Q** FR-D02 |
| Critical Wi-Fi wakes per day | 0 | 1 | 4 | **Q** max 1 per class per 6 h, 4 critical classes (edge-ai-concept 2.4); the three values are **A**; cap is 16/day (section 7 levers) |
| Wi-Fi association + DHCP, s | 1.0 | 2.5 | 6.0 | **A** to be measured; edge-ai-concept 2.4 estimates association + TLS + POST together at 3-10 s |
| SNTP + TLS + POST + response, s | 0.8 | 2.0 | 5.0 | **A** to be measured |
| Hub: TCP + TLS + MQTT + QoS1 publish, s | 0.5 | 1.0 | 3.0 | **Q** ADR-012 assumes +1 s (unmeasured); best/worst **A** |
| Wi-Fi connected RX / listen, mA | 70 | 85 | 100 | **DR** ESP32-C3 datasheet v2.4, Table 5-7 p. 56: RX 84 mA (HT20), 87 mA (HT40), peak; ADR-012 assumes about 100 mA |
| Wi-Fi TX, mA | 200 | 260 | 340 | **DR** ESP32-C3 datasheet v2.4, Table 5-7 p. 56: TX peak 335 (11b @21 dBm), 285 (11g 54M @19 dBm), 276 mA (11n MCS7 @18.5 dBm), 100 % duty; best 200 is below the datasheet at max power |
| TX share of the session | 3 % | 8 % | 15 % | **A** |
| Self-discharge, % per month | 1 | 2 | 3 | **A** commonly quoted 1-3 %, no datasheet; cell not chosen |

All D? values must be re-read from the datasheet by someone with access (Espressif ESP32-C3 series datasheet and ESP32-C3-MINI-1 datasheet; Aosong AHT20; ROHM BH1750FVI) and the exact table number cited before G4a.

## 5. Results

All "rule" figures use 0.8 x rated / average current. "+SD" / "extra" columns add the assumed cell self-discharge (2 %/month typical) and are an **extra-margin line, not the verdict**. Regenerate every block below with `python3 power_budget.py --update-doc power-budget.md`; a unit test fails if they drift from the script.

<!-- BEGIN:scenarios -->
| case | sleep uA | sleep mAh/d | sample mAh/d | Wi-Fi mAh/d | total mAh/d | load 2190 h mAh | rated mAh needed (rule) | extra: rated mAh incl. self-disch. |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| best | 8.3 | 0.20 | 0.73 | 1.13 | 2.06 | 188 | 235 | 244 |
| typical | 13.2 | 0.32 | 1.76 | 3.78 | 5.86 | 534 | 668 | 722 |
| worst | 31.7 | 0.76 | 3.56 | 14.81 | 19.13 | 1746 | 2182 | 2459 |
<!-- END:scenarios -->

Derated capacity = 0.8 x rated.

<!-- BEGIN:life -->
| rated mAh | derated mAh | best (rule) | typical (rule) | worst (rule) | best +SD | typical +SD | worst +SD |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 500 | 400 | 6.4 | 2.2 | 0.7 | 5.9 | 2.1 | 0.7 |
| 750 | 600 | 9.6 | 3.4 | 1.0 | 8.5 | 3.1 | 1.0 |
| 1000 | 800 | 12.8 | 4.5 | 1.4 | 11.0 | 4.0 | 1.3 |
| 1100 | 880 | 14.0 | 4.9 | 1.5 | 11.9 | 4.4 | 1.4 |
| 1500 | 1200 | 19.1 | 6.7 | 2.1 | 15.4 | 5.8 | 1.9 |
| 2000 | 1600 | 25.5 | 9.0 | 2.7 | 19.4 | 7.3 | 2.5 |
| 2500 | 2000 | 31.9 | 11.2 | 3.4 | 22.8 | 8.8 | 3.0 |
| 3000 | 2400 | 38.3 | 13.5 | 4.1 | 25.9 | 10.1 | 3.6 |
<!-- END:life -->

The capacities are generic values, not products. Cell choice is not made here (no datasheet of a specific cell was read).

<!-- BEGIN:sensitivity -->
**Wi-Fi connect time s (t_connect_s)**

| value | board sleep uA | mAh/day | rated mAh needed (rule) | months @1500 mAh (rule) | extra: months @1500 incl. SD |
| --- | --- | --- | --- | --- | --- |
| 1.0 | 13.2 | 4.83 | 550 | 8.2 | 6.8 |
| 2.5 | 13.2 | 5.86 | 668 | 6.7 | 5.8 |
| 4.0 | 13.2 | 6.89 | 786 | 5.7 | 5.0 |
| 6.0 | 13.2 | 8.26 | 943 | 4.8 | 4.3 |
| 10.0 | 13.2 | 11.01 | 1256 | 3.6 | 3.3 |

**Deep-sleep current uA (MCU term; whole board = this + 8.2)**

| value | board sleep uA | mAh/day | rated mAh needed (rule) | months @1500 mAh (rule) | extra: months @1500 incl. SD |
| --- | --- | --- | --- | --- | --- |
| 5 | 13.2 | 5.86 | 668 | 6.7 | 5.8 |
| 10 | 18.2 | 5.98 | 682 | 6.6 | 5.7 |
| 25 | 33.2 | 6.34 | 723 | 6.2 | 5.4 |
| 50 | 58.2 | 6.94 | 791 | 5.7 | 5.0 |
| 100 | 108.2 | 8.14 | 928 | 4.8 | 4.3 |

**TX current mA (i_tx_ma)**

| value | board sleep uA | mAh/day | rated mAh needed (rule) | months @1500 mAh (rule) | extra: months @1500 incl. SD |
| --- | --- | --- | --- | --- | --- |
| 200 | 13.2 | 5.67 | 647 | 7.0 | 5.9 |
| 260 | 13.2 | 5.86 | 668 | 6.7 | 5.8 |
| 340 | 13.2 | 6.10 | 696 | 6.5 | 5.6 |
<!-- END:sensitivity -->

Reading: connect time is the strongest lever (each extra second costs about 0.7 mAh/day, 12 % of the budget); TX current barely matters because TX is a small share of the session; deep sleep matters only when it grows by a factor of 5 or more. Best/typical/worst of all parameters together are in the scenario table.

## 6. Deep-sleep current limit for the requirement (for Theo, PR #2 item 19)

Definition to put in the requirement: **whole-board deep-sleep current measured at the battery terminal, USB unplugged, cell at 3.7 V, all sensors fitted and in their low-power state, soil oscillator off, radio off, RTC timer running.** Limit = the largest value for which the chosen cell still reaches NFR01_HOURS (2190 h) with the other terms as in the scenario.

**Derivation of NFR-12 (nothing fixed beforehand; accepted by Arsany, A-027).** Step 1: the largest sleep current for which the **1000 mAh minimum** cell still reaches 2190 h with the typical sample and Wi-Fi terms: `limit = (0.8 x C / 91.25 d - (sample + Wi-Fi mAh/day)) / 24 h` = **134 uA** (`max_sleep_current_ua()`). Step 2: a margin of 0.4, so that the sleep limit leaves room for the other terms, rounded down to a multiple of 25 uA (`nfr12_limit_ua()`): floor(53.8 / 25) x 25 = **50 uA**; it is 1.6x the worst sleep estimate (31.7 uA) and 3.8x the typical (13.2 uA). Design target 25 uA. 100 uA is only the absolute ceiling the budget would tolerate with every other term typical, and is not recommended. The limit does **not** prove NFR-01; NFR-01 is decided by the measured hourly average current (Wi-Fi is 65 %) and the named cell. In the worst-case stack no sleep current reaches 2190 h (the limit is negative), which again shows that stack is a stress bound.

<!-- BEGIN:nfr12 -->
| case (other terms as in the case) | board sleep estimate uA | max sleep uA for 1000 mAh rated, 2190 h | limit / estimate |
| --- | --- | --- | --- |
| best | 8.3 | 288 | 34.7 |
| typical | 13.2 | 134 | 10.2 |
| worst | 31.7 | -400 | n/a (cannot reach) |
| **NFR-12 limit** = floor(0.4 x typical limit to 25 uA) |  | **50** | 3.8 |
<!-- END:nfr12 -->


Deep-sleep limit (whole board) that still reaches NFR-01 (3 months), uA (negative = cannot reach even at 0 uA). Rule columns use Arsany's formula; "+SD" columns are the extra-margin line.

<!-- BEGIN:sleep_limit -->
| rated mAh | best (rule) | typical (rule) | worst (rule) | best +SD | typical +SD | worst +SD |
| --- | --- | --- | --- | --- | --- | --- |
| 500 | 105 | -48 | -583 | 98 | -62 | -603 |
| 750 | 196 | 43 | -491 | 186 | 23 | -522 |
| 1000 | 288 | 134 | -400 | 274 | 107 | -441 |
| 1100 | 324 | 171 | -364 | 309 | 141 | -409 |
| 1500 | 470 | 317 | -217 | 450 | 276 | -279 |
| 2000 | 653 | 500 | -35 | 626 | 445 | -117 |
| 2500 | 836 | 682 | 148 | 801 | 614 | 45 |
| 3000 | 1018 | 865 | 331 | 977 | 783 | 207 |
<!-- END:sleep_limit -->

**Single source for NFR-12: the derivation at the top of this section (1000 mAh minimum cell, 134 uA limit, 50 uA); the figures in this paragraph are the older 6-month derivation, kept only for reference.** Theo's independent derivation (review of this PR) gave the same limits for the earlier 6-month target: 134 uA / 43 uA (rule) and 80 uA / 2 uA (+SD) for 2000 / 1500 mAh typical; for the current 3 months the limits are 500 / 317 uA (rule) and 445 / 276 uA (+SD). Proposal (Theo accepted the numbers in his review, the requirement text is his):
- **Requirement value: whole-board deep sleep <= 50 uA**, design target <= 25 uA (estimate 13 uA, section 4). It is 3.8x the typical estimate and above the worst-case estimate (31.7 uA), and below the rule limit for a 2000 mAh cell (134 uA). The requirement text must state that this limit does **not** prove NFR-01; NFR-01 is decided by the measured hourly average current (Wi-Fi is 65 %) and the named cell capacity.
- Formula (rule): `limit = (0.8 x C / 182.5 d - (sample + Wi-Fi mAh/day)) / 24 h`, implemented as `max_sleep_current_ua()`.
- **Wi-Fi session, stated honestly:** the typical session in this model is **5.5 s at about 99 mA average** (2.5 s connect + 2.0 s cloud + 1.0 s hub), not 3.5 s. A session of **<= 3.5 s** is a **firmware design target, not the typical case**, and needs two levers together (fast connect to 1.0 s, hub publish every 2nd report; section 7). Whether it becomes a requirement waits for measurement M4 in 5.4; it is not to be written into the requirements before that.

## 7. What-if levers (TYPICAL as base)

<!-- BEGIN:levers -->
| lever | mAh/day | Wi-Fi session s | rated mAh needed (rule) | extra: incl. self-disch. |
| --- | --- | --- | --- | --- |
| base (typical) | 5.86 | 5.5 | 668 | 722 |
| light sleep during the soil warm-up (CPU 0.5 mA instead of 20 mA for 1.5 s, assumption) | 5.08 | 5.5 | 579 | 626 |
| hub publish every 2nd report (ADR-012 fallback) | 5.51 | 5.0 | 629 | 680 |
| no hub publish at all (cloud only) | 5.17 | 4.5 | 590 | 637 |
| fast connect: cached BSSID/channel + static IP (connect 1.0 s) | 4.83 | 4.0 | 550 | 595 |
| fast connect + hub every 2nd report (session 3.5 s) | 4.48 | 3.5 | 511 | 553 |
| fast connect + hub every 2nd + light-sleep warm-up | 3.70 | 3.5 | 422 | 456 |
| hub unreachable every hour: 3 s timeout (Theo's review of ADR-012), hub tried every report | 7.23 | 7.5 | 825 | 892 |
| hub unreachable, plus 1 s mDNS fallback lookup (assumption) | 7.92 | 8.5 | 903 | 977 |
| hub unreachable, back-off: hub tried every 4th report only | 5.69 | 5.2 | 648 | 701 |
| 30-min sampling (O-1 fallback) | 4.98 | 5.5 | 568 | 614 |
| critical wakes at the rate-limit cap (16/day) | 8.13 | 5.5 | 927 | 1002 |
| no critical wakes | 5.71 | 5.5 | 651 | 704 |
<!-- END:levers -->

- **Light sleep during the soil warm-up** is the largest single lever on the sample-wake side: the baseline holds the CPU active (20 mA) for the 1.5 s warm-up of every one of the 96 daily wakes. With the CPU in light sleep (assumed 0.5 mA including the RTC and timer; the true value is unverified and is measured in M3), the sample term falls from 1.76 to 0.98 mAh/day, **-0.78 mAh/day, 13 % of the total**. Cost: firmware must keep the soil oscillator supply and the I2C sensors alive across light sleep and wake on a timer (Mira's call); sensors are on their own supply gate. Together with fast connect and hub every 2nd report the typical load falls to 3.7 mAh/day.
- **Hub unreachable** (home-network hub down, common): the 1 s publish becomes a 3 s timeout every hour (Theo's review of ADR-012), costing **+1.4 mAh/day (+23 %)** in this model (7.2 vs 5.9; the model charges the session average of 99 mA for the longer time, a slight over-estimate as no TX happens while waiting; at 85 mA it is +1.1). A 1 s mDNS fallback lookup (assumption) takes it to +2.1 mAh/day. Theo's review quoted "about +0.2 mAh/day"; I cannot reproduce that figure (3 s x 85 mA x 24 h = 1.7 mAh/day in total for the timeouts), so I report my number and ask Theo to check. **Back-off** (try the hub only every 4th report after failures) brings it to 5.7 mAh/day, i.e. below the base case: firmware should back off when the hub fails (Mira, ADR-012 follow-up).
- The second MQTT publish (ADR-012) costs 0.69 mAh/day in this model (5.86 vs 5.17), 12 % of the budget; ADR-012 estimated 0.67 mAh/day, so the two agree (both unmeasured).
- The 30-min sampling fallback does **not** change FR-E03 as it would double the latency to about 30 min, so it conflicts with the owner-confirmed wording; prefer the Wi-Fi levers (fast connect, hub every 2nd report) and the light-sleep warm-up. Critical wakes at the rate cap cost 39 % more than the base case, so the cap (or a daily limit) is a battery decision for Mira/Theo.

## 8. Cell and bay (A-020 answered, A-034 decided 2026-11-08)

**Decided cell (A-034, Arsany 2026-11-08): EEMB LP603449-PCM, Amazon.de ASIN B08FD39Y5R** (1100 mAh typical / 1000 mAh minimum per the listing bullet, PCM built in, JST plug, no NTC mentioned, 51 x 34.5 x 6.3 mm; facts and what is unverified: [`../bom/cell-decision-A034.md`](../bom/cell-decision-A034.md)). It is the cell the A-020 bay was drawn for. The candidate table below is regenerated with it first; the Jauch cells stay as information.

The cell is the **603449 LiPo, 3.7 V, 1100 mAh typical / 1000 mAh minimum, about 22 g, 51 x 34.5 x 6.3 mm (L x W x H)** (A-020). The EEMB LP603449 datasheet (read 2026-11-07, see `../bom/bom-draft.md`) gives <= 50 x 34.5 x 6.3 mm, 1000 mAh minimum, 1C maximum charge, bare cell with solder tabs; protection circuit and connector depend on the purchase spec. The envelope is recorded as the bay input for the PCB outline and enclosure v3 in [`../../docs/interfaces/pcb-enclosure-bay.md`](../../docs/interfaces/pcb-enclosure-bay.md).

Capacity check against section 5: the typical case needs about 670 mAh rated by the rule and the 1000 mAh minimum gives 4.5 months, so the cell is sufficient with a factor 1.5; the worst-case stack (about 2180 mAh needed) cannot be met by any cell that fits this bay, so the levers in section 7 and the measurements in section 9 matter more than capacity.

**A-034 (battery from DigiKey): candidates against NFR-01** (generated; details, datasheet pages and options in [`../bom/cell-decision-A034.md`](../bom/cell-decision-A034.md)). The Jauch LP503030JU candidate has only 430 mAh minimum and **fails** NFR-01 even under the relaxed rule (typical 1.9 months, worst 0.6 months); "fits" compares the envelope with the A-020 bay and ignores swelling and wire clearance.

<!-- BEGIN:cells -->
| cell | typ mAh | MIN mAh | T x W x L mm | fits 51 x 34.5 x 6.3 | months best | months typical | months worst | NFR-01 (best, typ >= 3; worst > 1) | max sleep uA (typical terms) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EEMB LP603449-PCM, Amazon B08FD39Y5R (A-034 decided) | 1100 | 1000 | 6.3 x 34.5 x 51 | yes | 11.0 | 4.3 | 1.4 | PASS | 134 |
| Jauch LP503030JU+PCM+2IC+NTC (A-034 candidate) | 450 | 430 | 5.2 x 30 x 30 | yes | 4.8 | 1.9 | 0.6 | FAIL: typical, worst | -74 |
| Jauch LP603443JU+PCM+2 wires (DigiKey alternative) | 900 | 850 | 6.5 x 34.5 x 45 | no, thicker: input to Yara | 9.4 | 3.7 | 1.2 | PASS | 80 |
<!-- END:cells -->


## 9. To be measured in 5.4 (dev kit, then PCB) to replace estimates

Needs hands on hardware: Peter does these via a work order; the work order text is Emil's to draft once the dev-kit list is fixed. Equipment: a current meter that resolves 1 uA in deep sleep and records mA bursts (source-measure unit or a power profiler; choice and any purchase are Arsany's), a bench supply or a charged cell, and the same firmware as the field build.

| # | Measure | On | Replaces | Pass/fail use |
|---|---|---|---|---|
| M1 | Deep-sleep current at 3.7 V, USB unplugged, sensors fitted, 10 min settle, mean over 60 s | dev kit, then PCB | section 4 sleep rows | <= 50 uA (section 6) |
| M2 | Same, at 3.3 V, 4.2 V and 3.0 V; at 0 C / 25 C / 40 C if a chamber is available | PCB | temperature and divider terms | trend only |
| M3 | Current trace of one sample wake (boot, warm-up, AHT20, BH1750, inference): duration and charge in mA*s; once with CPU busy-wait and once with light sleep during warm-up (current in light sleep) | dev kit | t_boot, t_sense, I_cpu, I_periph | charge per wake |
| M4 | Current trace of one hourly session: association, DHCP, SNTP, cloud TLS + POST, hub TLS + MQTT: time per phase, average mA, TX peak mA; 20 sessions, median and worst | dev kit on the real router | t_connect, t_cloud, t_hub, I_rx, I_tx, f_tx | charge per session |
| M5 | Same with static IP and cached BSSID/channel; with hub publish every 2nd report; with the hub switched off (timeout length, charge, mDNS fallback) | dev kit | lever table | decides fallback |
| M6 | Charge of a critical-event wake | dev kit | critical wakes | rate cap |
| M7 | Battery sense divider leakage and ADC reading at 3.4 / 3.7 / 4.2 V | PCB | divider term, 3.4 V warning accuracy | warning within tolerance (to be set by Theo) |
| M8 | LDO dropout and output sag during Wi-Fi TX at 3.4 V and 3.0 V, with the cell's internal resistance | PCB (and ngspice before layout) | headroom at the 3.4 V warning | no brown-out reset at 3.4 V |
| M9 | Discharge of a real cell at the measured average load down to 3.4 V (accelerated with a higher duty if needed, stated) | cell + PCB | `usable_fraction` and the 20 % derating | capacity above 3.4 V >= 0.8 x rated |
| M10 | Self-discharge of the chosen cell over 4 weeks (or the maker's datasheet figure with citation) | cell | self-discharge row | <= 2 %/month |
| M11 | OTA download charge, 1.5 MB slot (architecture), once | dev kit | excluded OTA load | add to the budget per OTA |

After M1-M6 the script is run with the measured values (edit `TYPICAL`, tag each field "measured, <date>, <file>") and the table in section 5 is regenerated.

## 10. Open points

- **Closed:** self-discharge in the NFR-01 rule: no (A-020, acceptance matrix); NFR-01 is relaxed (best and typical >= 3 months, worst > 1 month, Arsany 2026-11-08) and the decided 1000 mAh-minimum cell passes all three scenarios (section 12).
- **Needs Yara / Arsany:** only Yara's usable bay inside enclosure v3 (swelling and wire clearance) is still open, see [`../../docs/interfaces/pcb-enclosure-bay.md`](../../docs/interfaces/pcb-enclosure-bay.md); cell purchase and any order (Arsany orders, hard rule); a current meter for 5.4 (purchase is Arsany's).
- **Datasheet tags:** the four ESP32-C3 rows are now **DR** (section 11). Still D?: Aosong AHT20, ROHM BH1750FVI, ESP32-C3-MINI-1 module datasheet (flash leakage).

## 11. Update 2026-11-07 (2.5 follow-up): datasheet read, cell 1000 mAh minimum

Source read: ESP32-C3 Series Datasheet v2.4, `https://documentation.espressif.com/esp32-c3_datasheet_en.pdf` (HTTP 200, 900 kB, PDF creation date 2026-05-06), Tables 5-7, 5-8, 5-9 on pp. 56-57. Full comparison and what-if: [`verified-currents.md`](verified-currents.md). **Model values are unchanged**; only the tags changed.

What the datasheet says against the model: deep sleep 5 uA agrees; CPU 160 MHz is 23-28 mA (model 15/20/30: best and typical too low); RX 84-87 mA peak (model best 70 too low); TX 276-335 mA peak at maximum power and 100 % duty (model best 200 too low). Replacing best/typical/worst by the datasheet values (CPU 23/23/28, RX 84/84/87, TX 276/285/335) moves the typical case from 4.49 to 4.29 months at **1000 mAh rated** (4.94 to 4.72 at 1100 mAh, 6.74 to 6.44 at 1500 mAh), and the rated capacity needed for 3 months from 668 to 699 mAh (for 6 months 1336 to 1398 mAh, information).

**The cell in the BOM (LP603449-class, 1000 mAh minimum, reference EEMB datasheet) passes NFR-01 (3 months, A-020) in the typical case by the literal rule**: 4.5 months at 1000 mAh (4.3 with the datasheet currents), about 1.4-1.5x margin; 4.9 at the 1100 mAh nominal. Rated capacity needed is about 670 mAh (700 with the datasheet currents). The worst-case stack (every parameter at its worst at once) gives 1.4 months at 1000 mAh; that is a stress bound to be measured in 5.4, not a design point. It misses the 6-month stretch goal (information only); the section 7 lever package would give about 7.1 months.
- **For Theo:** the deep-sleep limit in section 6 as a requirement (the Wi-Fi-session figure is a design target only, 5.5 s typical); whether the 3 months are counted to the 3.4 V warning (assumed here); please check the hub-unreachable figure (+1.4 vs your +0.2 mAh/day).
- **For Mira (firmware):** fast Wi-Fi connect (cached channel/BSSID, static IP or DHCP lease reuse), SNTP not on every session, hub publish every 2nd report if needed, hub back-off when unreachable, light sleep during the soil warm-up, critical-wake cap per day; each is a lever in section 7.
- **For me, next in 4.P1/4.P3:** pick a low-Iq LDO and charger/protection (sum of their quiescent currents goes in section 4), battery divider with a switch, and the LDO dropout simulation at 3.4 V.

## 12. Update 2026-11-08: A-034 decided, NFR-01 relaxed, board as built after A-045

**Decisions (Arsany, 2026-11-08):** (1) A-034: he buys the EEMB LP603449-PCM from Amazon.de (ASIN B08FD39Y5R). (2) NFR-01 is relaxed: **best and typical case >= 3 months, worst case more than 1 month** ("best case >= 3 months, worst cases accepted as long as they are more than 1 month"). I keep the typical case at 3 months (he named best and worst only; the stricter reading costs nothing for this cell: 4.3 months). If he meant no typical threshold, the verdicts do not change. The Requirements doc (Google Doc) and the acceptance matrix (NFR-01 row, line 118) still say 3 months for every case; they are the Lead's to update, not edited here. (3) A-045 Option A (permanent battery divider R7/R8, no Q2/R6) and A-046 Option A (no power path) were approved for the schematic.

**Scenario definitions (the three columns of section 4, unchanged):**
- **best:** datasheet-typical or better for every term, the firmware levers not used; 15-min wake, 24 reports/day, no critical wakes, Wi-Fi association 1.0 s, cloud 0.8 s, hub 0.5 s, TX share 3 %.
- **typical:** the planning case: association 2.5 s, cloud 2.0 s, hub 1.0 s, 1 critical wake per day, TX share 8 %, TX 260 mA.
- **worst:** every parameter at its worst at once (association 6 s, cloud 5 s, hub 3 s, 4 critical wakes per day, TX 340 mA, TX share 15 %, sleep terms at their worst). It is a stress bound that is very unlikely to occur together; the new rule asks only that it still lasts more than 1 month.

**As-built sleep (after A-045):** the schematic has the divider R7 + R8 = 2 MOhm permanently on VBAT (4.2 V / 2 MOhm = 2.1 uA, BAT_SENS never above 2.1 V), XC6220 8 uA (datasheet), charger + protection + leakage as in `pcb/pinmap-sleep.md`: typical **21.6 uA**, worst **39.6 uA** (NFR-12: target 25, limit 50 uA). Section 4 still holds the older assumptions (13.2 / 31.7 uA); open point 10 of the PCB README said the budget would be updated, and the "as-built sleep" rows above do that without touching the baseline rows. The effect is small: typical 4.49 to 4.34 months, worst 1.37 to 1.36.

**Verdict, EEMB LP603449-PCM, 1000 mAh minimum, rule 0.8 x C / I_avg (generated table in section 1):**

| Scenario | Months (as-built sleep) | Needs | Verdict |
|---|---|---|---|
| best | 11.0 | >= 3 | PASS |
| typical | 4.3 | >= 3 | PASS (1.45x margin) |
| worst | 1.36 | > 1 | PASS (1.36x margin over 730 h) |

The cell does **not** fail the relaxed rule. With the extra self-discharge line (2 %/month, not part of the rule) the worst case is 1.3 months, still above 1. All inputs are still unmeasured (section 9, M1 to M9 decide); the 1.36 months worst case has the least margin and is the number to watch in 5.4.

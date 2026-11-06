# Power budget and battery life (task 2.3, NFR-01)

Author: Emil (PCB Designer) · Date: 2026-11-04, **re-run 2026-11-06 with the A-020 / A-021 decisions** · Status: **draft for the G2 review, all inputs are estimates**
Calculator: [`power_budget.py`](power_budget.py) (Python 3.11, stdlib only) · Tests: [`test_power_budget.py`](test_power_budget.py)
Traces to: NFR-01 (relaxed from 6 to **3 months**, A-020), FR-D01 (15-min sampling), FR-D02 (hourly report), FR-E03/E04 (critical wake, inference), ADR-012 (second MQTT publish), PR #2 items 12 and 19, A-020, A-021.

**Nothing in this document is a measurement.** Every current and time is either quoted from a repo document, recalled from a datasheet that the session could not open (espressif.com returns a proxy 403), or an engineering assumption. Each is tagged in section 4. Task 5.4 replaces them (section 9). **All currents and times in the tables are unverified datasheet recollections or assumptions; none was read from a datasheet or measured.**

## 1. Result

**Decisions applied (Arsany's answers).** **A-020:** the cell is the **603449 LiPo, 3.7 V, 1100 mAh typical / 1000 mAh minimum, about 22 g, 51 x 34.5 x 6.3 mm (L x W x H)** (maker figures as given, no datasheet read here), and a battery life of **up to 3 months is acceptable**, so **NFR-01 is relaxed from 6 to 3 months: 2190 h threshold instead of 4380 h** (`NFR01_MONTHS = 3` in the script; the formula is unchanged). **A-021:** the verdict uses the **literal rule with the derated rated capacity**: projected life = **0.8 x rated capacity / measured average current >= 2190 h**, with **no self-discharge term**; the verdict uses the **1000 mAh minimum**. Self-discharge appears only as a separately labelled extra-margin line ("+SD" / "extra").

| Question | Answer (estimates, all inputs unverified) |
|---|---|
| Average load, typical | **5.9 mAh/day** = 0.244 mA (sleep 0.3, 96 sample wakes 1.8, 24 hourly Wi-Fi sessions + 1 critical wake 3.8) |
| **NFR-01 verdict, 603449 at 1000 mAh minimum (rule)** | Typical: **PASS, 4.5 months** (800 mAh derated / 0.244 mA = 3278 h >= 2190 h). Best 12.8 months. Worst-case stack: **FAIL, 1.4 months** (1004 h, every parameter at its worst at once; a stress bound, not a design point). At the 1100 mAh typical capacity (information only): typical 4.9 months |
| Rated capacity needed for 3 months (2190 h), per the rule | Typical **about 670 mAh rated** (0.8 x 668 = 534 mAh derated = the 2190 h load); best **about 240 mAh**; worst **about 2180 mAh**. The 1000 mAh minimum cell covers the typical case with a factor 1.5 |
| Extra margin line (not the rule): with cell self-discharge, assumed 2 %/month | 1000 mAh: **4.0 months** (still passes); rated capacity needed 722 mAh instead of 668 mAh |
| What dominates | Wi-Fi sessions are **65 %** of the budget, sample wakes 30 %, deep sleep only **5 %** |
| Deep-sleep limit for the requirement (PR #2 item 19) | Per the rule, typical Wi-Fi and sampling terms, 1000 mAh minimum cell: **134 uA whole board** (with self-discharge: 107 uA). **Recommended NFR-12: <= 50 uA** (0.4 x 134 rounded down to a multiple of 25 uA; 1.6x the worst sleep estimate, 3.8x typical), design target <= 25 uA; 100 uA is only the absolute ceiling; derivation in section 6. **Needs Arsany's approval** |
| Cases that still pass at 1000 mAh (rule) | Hub unreachable every hour (needs 825 mAh rated), critical wakes at the cap of 16/day (927 mAh): both pass, the second only barely; see section 7 |
| Biggest levers (section 7) | Light sleep during the soil warm-up: **-0.78 mAh/day (-13 %)**; fast connect + hub every 2nd report: **-1.4 mAh/day**; hub unreachable every hour costs **+1.4 mAh/day** |
| Verdict on NFR-01 | **Not provable yet.** By the rule the typical case passes with the 1000 mAh minimum cell (4.5 months >= 3 months); the worst-case stack fails (1.4 months). Everything hinges on Wi-Fi connect time and current, which only 5.4 can settle. All currents are unverified datasheet recollections or assumptions. The levers are in section 7 |

Verdict table for the A-020 cell (generated):

<!-- BEGIN:cell -->
| cell capacity | case | derated mAh | average uA | life h (rule) | months (rule) | vs 2190 h | extra: months incl. SD |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1000 mAh minimum (verdict, A-021) | best | 800 | 86 | 9317 | 12.8 | PASS | 11.0 |
| 1000 mAh minimum (verdict, A-021) | typical | 800 | 244 | 3278 | 4.5 | PASS | 4.0 |
| 1000 mAh minimum (verdict, A-021) | worst | 800 | 797 | 1004 | 1.4 | FAIL | 1.3 |
| 1100 mAh typical (info only) | best | 880 | 86 | 10249 | 14.0 | PASS | 11.9 |
| 1100 mAh typical (info only) | typical | 880 | 244 | 3606 | 4.9 | PASS | 4.4 |
| 1100 mAh typical (info only) | worst | 880 | 797 | 1104 | 1.5 | FAIL | 1.4 |
<!-- END:cell -->

**Open for Arsany: the NFR-12 value** (section 6). The 50 uA value stays valid after the re-run: it is 0.4 x the 134 uA limit rounded down to 25 uA. Recommendation: approve **50 uA** (limit) and keep **25 uA** as design target. 100 uA is only the absolute ceiling the budget allows and is not recommended.

## 2. Inputs and decisions applied

- **Capacity rule (Arsany, PR #2 item 12; A-021 confirmed), applied literally:** use the **rated** capacity of the chosen 1S LiPo with **20 % derating**; projected life = derated capacity / average current >= 2190 h (3 months, A-020); no self-discharge term. The verdict uses the **1000 mAh minimum** of the 603449 cell, the 1100 mAh typical value is shown for information. Both numbers are stated everywhere (rated and derated = 0.8 x rated).
- **Low-battery warning at 3.4 V** (source: Arsany's answer "ok" to Needs Arsany **A-008.2**, "low-battery 3.4 V", in the PR #2 thread; confirmed by Theo's architect review of this PR; PR #15's schema uses 3400 mV as default). Consequences: (a) the 3 months are counted to the point of the warning, the charge left below 3.4 V is a reserve and is **not** counted; (b) the 20 % derating is taken to cover the capacity that is unusable above 3.4 V, temperature and ageing, and self-discharge (A-021: no separate term) (`usable_fraction` = 1.0 in the model); 5.4 must check this with a discharge curve at the real load (section 9); (c) with a 3.3 V LDO the headroom at the warning point is only 100 mV, so dropout under Wi-Fi TX peaks must be simulated in 4.P1 (LDO dropout sim, role file) or a lower-dropout/boost-buck path chosen.
- **Scope of the load:** 15-min wake (soil, AHT20, BH1750, battery ADC, both edge-AI models) + hourly Wi-Fi report (cloud POST **and** MQTT publish to the Pi hub, ADR-012) + critical-event Wi-Fi wakes (edge-ai-concept 2.4: at most one per class per 6 h). **Excluded:** BLE setup (setup mode only, ADR-011), OTA downloads, Wi-Fi outage retries, charging losses, USB-powered time. These add load: OTA and outages must be bounded in 4.F (e.g. OTA only above a battery threshold, already in ADR-009; backoff already in architecture section 5).
- 3 months = **2190 h** (NFR01_MONTHS x 730 h; relaxed from 6 months = 4380 h by A-020), i.e. 91.25 days.

## 3. Model

Battery-terminal charge per day, 3.3 V rail from an LDO (load current = battery current):

```
sleep   = I_sleep(board) x 24 h
sample  = 96 wakes x [ (t_boot + t_infer + t_store) x I_cpu + t_sense x (I_cpu + I_periph) ]
wifi    = (24 reports + critical wakes) x (t_connect + t_cloud + t_hub / hub_every_n) x I_wifi_avg
I_wifi_avg = f_tx x I_tx + (1 - f_tx) x I_rx
rated capacity needed  C = load(2190 h) / 0.8            (Arsany's rule, headline)
extra margin only      C = load(2190 h) / (0.8 - self_discharge_per_month x 3)
```

Self-discharge is the cell's own loss as a fraction of rated capacity per month; at 2 %/month it would cost 6 % of rated capacity over 3 months and is the reason the extra-margin line needs 722 mAh where the rule needs 668 mAh. It is **not** part of the rule (A-021). The inference (Invoke) is in the model, but at 1-50 ms it is below 0.5 % of a sample wake; the sample wake is dominated by the 1.5-3 s soil warm-up, during which the baseline keeps the CPU active (20 mA); the light-sleep lever (section 7) changes only that part (`t_warmup_s`, `i_warmup_cpu_ma`). A sample wake and the Wi-Fi session in the same hour are modelled as separate (the Wi-Fi session adds connect time only, boot is already paid).

## 4. Parameters with sources (best / typical / worst)

Status: **Q** = quoted from a repo document (cited), **D?** = recalled from the named datasheet, **not read** in this session, unverified; **A** = assumption; **C** = computed.

| Parameter | Best | Typical | Worst | Status and source |
|---|---|---|---|---|
| MCU deep sleep (RTC timer), uA | 5 | 5 | 10 | **D?** ESP32-C3 series datasheet, low-power current table (about 5 uA); worst adds module-flash leakage (A) |
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
| CPU active, radio off, mA | 15 | 20 | 30 | **D?** ESP32-C3 series datasheet, active current at 160 MHz (about 20 mA) |
| Soil oscillator + I2C sensors while sensing, mA | 1.5 | 3.5 | 7 | **A** (AHT20 tens of uA and BH1750 about 0.12 mA are **D?**) |
| Reports per day | 24 | 24 | 24 | **Q** FR-D02 |
| Critical Wi-Fi wakes per day | 0 | 1 | 4 | **Q** max 1 per class per 6 h, 4 critical classes (edge-ai-concept 2.4); the three values are **A**; cap is 16/day (section 7 levers) |
| Wi-Fi association + DHCP, s | 1.0 | 2.5 | 6.0 | **A** to be measured; edge-ai-concept 2.4 estimates association + TLS + POST together at 3-10 s |
| SNTP + TLS + POST + response, s | 0.8 | 2.0 | 5.0 | **A** to be measured |
| Hub: TCP + TLS + MQTT + QoS1 publish, s | 0.5 | 1.0 | 3.0 | **Q** ADR-012 assumes +1 s (unmeasured); best/worst **A** |
| Wi-Fi connected RX / listen, mA | 70 | 85 | 100 | **D?** ESP32-C3 series datasheet, Wi-Fi RX (order of 80-100 mA); ADR-012 assumes about 100 mA |
| Wi-Fi TX, mA | 200 | 260 | 340 | **D?** ESP32-C3 series datasheet, TX by rate and power (order of 200-340 mA) |
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
<!-- END:life -->

The capacities are generic values, not products. Cell choice is not made here (no datasheet of a specific cell was read).

<!-- BEGIN:sensitivity -->
**Wi-Fi connect time s (t_connect_s)**

| value | board sleep uA | mAh/day | rated mAh needed (rule) | months @1000 mAh (rule) | extra: months @1000 incl. SD |
| --- | --- | --- | --- | --- | --- |
| 1.0 | 13.2 | 4.83 | 550 | 5.5 | 4.8 |
| 2.5 | 13.2 | 5.86 | 668 | 4.5 | 4.0 |
| 4.0 | 13.2 | 6.89 | 786 | 3.8 | 3.5 |
| 6.0 | 13.2 | 8.26 | 943 | 3.2 | 2.9 |
| 10.0 | 13.2 | 11.01 | 1256 | 2.4 | 2.3 |

**Deep-sleep current uA (MCU term; whole board = this + 8.2)**

| value | board sleep uA | mAh/day | rated mAh needed (rule) | months @1000 mAh (rule) | extra: months @1000 incl. SD |
| --- | --- | --- | --- | --- | --- |
| 5 | 13.2 | 5.86 | 668 | 4.5 | 4.0 |
| 10 | 18.2 | 5.98 | 682 | 4.4 | 4.0 |
| 25 | 33.2 | 6.34 | 723 | 4.2 | 3.8 |
| 50 | 58.2 | 6.94 | 791 | 3.8 | 3.5 |
| 100 | 108.2 | 8.14 | 928 | 3.2 | 3.0 |

**TX current mA (i_tx_ma)**

| value | board sleep uA | mAh/day | rated mAh needed (rule) | months @1000 mAh (rule) | extra: months @1000 incl. SD |
| --- | --- | --- | --- | --- | --- |
| 200 | 13.2 | 5.67 | 647 | 4.6 | 4.2 |
| 260 | 13.2 | 5.86 | 668 | 4.5 | 4.0 |
| 340 | 13.2 | 6.10 | 696 | 4.3 | 3.9 |
<!-- END:sensitivity -->

Reading: connect time is the strongest lever (each extra second costs about 0.7 mAh/day, 12 % of the budget); TX current barely matters because TX is a small share of the session; deep sleep matters only when it grows by a factor of 5 or more. Best/typical/worst of all parameters together are in the scenario table.

## 6. Deep-sleep current limit for the requirement: derived NFR-12 (for Theo and Arsany)

Definition to put in the requirement: **whole-board deep-sleep current measured at the battery terminal, USB unplugged, cell at 3.7 V, all sensors fitted and in their low-power state, soil oscillator off, radio off, RTC timer running.** The ID is **NFR-12** (NFR-10 is provisioning security); the matrix row is renumbered accordingly and keeps 50 uA.

**Derivation (nothing fixed beforehand).** Step 1: the largest sleep current for which the **1000 mAh minimum** cell still reaches 2190 h, with the typical sample and Wi-Fi terms: `limit = (0.8 x C / 91.25 d - (sample + Wi-Fi mAh/day)) / 24 h` = **134 uA** (`max_sleep_current_ua()`). Step 2: apply a margin of 0.4 so that the sleep limit leaves room for the other terms, and round down to a multiple of 25 uA: **50 uA** (`nfr12_limit_ua()`). 50 uA is 3.8x the typical estimate (13.2 uA) and 1.6x the worst-case estimate (31.7 uA), well below the rule limit of 134 uA. 100 uA (`NFR12_CEILING_UA`) is the absolute ceiling the budget would tolerate and is not recommended.

<!-- BEGIN:nfr12 -->
| case (other terms as in the case) | board sleep estimate uA | max sleep uA for 1000 mAh rated, 2190 h | limit / estimate |
| --- | --- | --- | --- |
| best | 8.3 | 288 | 34.7 |
| typical | 13.2 | 134 | 10.2 |
| worst | 31.7 | -400 | n/a (cannot reach) |
| **proposed NFR-12 limit** = floor(0.4 x typical limit to 25 uA) |  | **50** | 3.8 |
<!-- END:nfr12 -->

**Recommended NFR-12: whole-board deep sleep <= 50 uA, design target <= 25 uA. Pending Arsany's approval.** The requirement text must state that this limit does **not** prove NFR-01; NFR-01 is decided by the measured hourly average current (Wi-Fi is 65 %) and the named cell capacity. 50 uA keeps the earlier proposal while 100 uA would only pass with every other term at its typical value. The limit is a ceiling, not the expected value: at the 13 uA estimate deep sleep is 5 % of the load, and a board at exactly 50 uA would use 1.2 mAh/day (versus 0.3 at the estimate).

Deep-sleep limit by rated capacity (negative = cannot reach even at 0 uA). Rule columns use Arsany's formula; "+SD" columns are the extra-margin line.

<!-- BEGIN:sleep_limit -->
| rated mAh | best (rule) | typical (rule) | worst (rule) | best +SD | typical +SD | worst +SD |
| --- | --- | --- | --- | --- | --- | --- |
| 500 | 105 | -48 | -583 | 98 | -62 | -603 |
| 750 | 196 | 43 | -491 | 186 | 23 | -522 |
| 1000 | 288 | 134 | -400 | 274 | 107 | -441 |
| 1100 | 324 | 171 | -364 | 309 | 141 | -409 |
| 1500 | 470 | 317 | -217 | 450 | 276 | -279 |
| 2000 | 653 | 500 | -35 | 626 | 445 | -117 |
<!-- END:sleep_limit -->

- Formula (rule): `limit = (0.8 x C / 91.25 d - (sample + Wi-Fi mAh/day)) / 24 h`.
- **Wi-Fi session, stated honestly:** the typical session in this model is **5.5 s at about 99 mA average** (2.5 s connect + 2.0 s cloud + 1.0 s hub), not 3.5 s. A session of **<= 3.5 s** is a **firmware design target, not the typical case**, and needs two levers together (fast connect to 1.0 s, hub publish every 2nd report; section 7). Whether it becomes a requirement waits for measurement M4 in 5.4; it is not to be written into the requirements before that.

## 7. What-if levers (TYPICAL as base)

<!-- BEGIN:levers -->
| lever | mAh/day | Wi-Fi session s | rated mAh needed (rule) | extra: incl. self-disch. |
| --- | --- | --- | --- | --- |
| best | 8.3 | 288 | 34.7 |
| typical | 13.2 | 134 | 10.2 |
| worst | 31.7 | -400 | n/a (cannot reach) |
| **proposed NFR-12 limit** = floor(0.4 x typical limit to 25 uA) |  | **50** | 3.8 |
<!-- END:levers -->

- **Light sleep during the soil warm-up** is the largest single lever on the sample-wake side: the baseline holds the CPU active (20 mA) for the 1.5 s warm-up of every one of the 96 daily wakes. With the CPU in light sleep (assumed 0.5 mA including the RTC and timer; the true value is unverified and is measured in M3), the sample term falls from 1.76 to 0.98 mAh/day, **-0.78 mAh/day, 13 % of the total**. Cost: firmware must keep the soil oscillator supply and the I2C sensors alive across light sleep and wake on a timer (Mira's call); sensors are on their own supply gate. Together with fast connect and hub every 2nd report the typical load falls to 3.7 mAh/day.
- **Hub unreachable** (home-network hub down, common): the 1 s publish becomes a 3 s timeout every hour (Theo's review of ADR-012), costing **+1.4 mAh/day (+23 %)** in this model (7.2 vs 5.9; the model charges the session average of 99 mA for the longer time, a slight over-estimate as no TX happens while waiting; at 85 mA it is +1.1). A 1 s mDNS fallback lookup (assumption) takes it to +2.1 mAh/day. Theo's review quoted "about +0.2 mAh/day"; I cannot reproduce that figure (3 s x 85 mA x 24 h = 1.7 mAh/day in total for the timeouts), so I report my number and ask Theo to check. **Back-off** (try the hub only every 4th report after failures) brings it to 5.7 mAh/day, i.e. below the base case: firmware should back off when the hub fails (Mira, ADR-012 follow-up).
- The second MQTT publish (ADR-012) costs 0.69 mAh/day in this model (5.86 vs 5.17), 12 % of the budget; ADR-012 estimated 0.67 mAh/day, so the two agree (both unmeasured).
- The 30-min sampling fallback does **not** change FR-E03 as it would double the latency to about 30 min, so it conflicts with the owner-confirmed wording; prefer the Wi-Fi levers (fast connect, hub every 2nd report) and the light-sleep warm-up. Critical wakes at the rate cap cost 39 % more than the base case, so the cap (or a daily limit) is a battery decision for Mira/Theo.

## 8. Cell and bay (A-020 answered)

The question of section 8 in the first version is answered by A-020: **603449 LiPo, 3.7 V, 1100 mAh typical / 1000 mAh minimum, about 22 g, 51 x 34.5 x 6.3 mm (L x W x H)** (maker figures as given by Arsany; naming convention 6.0 mm x 34 mm x 49 mm nominal plus tolerances, **unverified from memory**; I did not read a cell datasheet). The envelope 51 x 34.5 x 6.3 mm is recorded as the bay input in `projects/plant-monitor/docs/interfaces/pcb-enclosure-bay.md` for the PCB outline (4.P2) and enclosure v3 (4.E3). Still open from the cell datasheet: protection circuit, connector and wire length, maximum charge/discharge current (Wi-Fi TX peaks of 340 mA are a 0.34 C pulse, expected harmless but unverified), swelling allowance (Yara sets the clearance), and whether the cell is delivered with a protection board.

Capacity check against section 5: the typical case needs about 670 mAh rated by the rule, the 1000 mAh minimum gives 4.5 months, so the cell is sufficient with a factor 1.5; the worst-case stack (2180 mAh needed) cannot be met by any cell that fits this bay, so the levers in section 7 and the measurements in section 9 matter more than capacity.

## 9. To be measured in 5.4 (dev kit, then PCB) to replace estimates

Needs hands on hardware: Peter does these via a work order; the work order text is Emil's to draft once the dev-kit list is fixed. Equipment: a current meter that resolves 1 uA in deep sleep and records mA bursts (source-measure unit or a power profiler; choice and any purchase are Arsany's), a bench supply or a charged cell, and the same firmware as the field build.

| # | Measure | On | Replaces | Pass/fail use |
|---|---|---|---|---|
| M1 | Deep-sleep current at 3.7 V, USB unplugged, sensors fitted, 10 min settle, mean over 60 s | dev kit, then PCB | section 4 sleep rows | <= NFR-12 limit (proposed 50 uA, section 6) |
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

- **Needs Arsany (question):** approve the derived NFR-12 whole-board deep-sleep limit of **50 uA** (design target 25 uA) or choose another value (section 6; 100 uA is the absolute ceiling). Recommendation: 50 uA.
- **Answered, applied:** A-020 (cell 603449, 3-month life acceptable, NFR-01 relaxed to 2190 h) and A-021 (literal rule, derated rated capacity, 1000 mAh minimum, no self-discharge term). The acceptance matrix row NFR-01 still says 6 months / 4380 h and must be updated by the Lead/Theo.
- **Needs Arsany / Peter:** a current meter for 5.4 (purchase is Arsany's); ordering the cell (Arsany orders, hard rule).
- **Needs a person with network access:** read the five datasheet tables behind the D? rows (and the 603449 cell datasheet) and replace the tags with section and table numbers. **All currents here remain unverified datasheet values.**
- **For Theo:** the NFR-12 text (section 6) (matrix row renumbered to NFR-12); whether the 3 months are counted to the 3.4 V warning (assumed here); please check the hub-unreachable figure (+1.4 vs your +0.2 mAh/day).
- **For Yara:** bay 51 x 34.5 x 6.3 mm plus swelling clearance (`docs/interfaces/pcb-enclosure-bay.md`).
- **For Mira (firmware):** fast Wi-Fi connect (cached channel/BSSID, static IP or DHCP lease reuse), SNTP not on every session, hub publish every 2nd report if needed, hub back-off when unreachable, light sleep during the soil warm-up, critical-wake cap per day; each is a lever in section 7.
- **For me, next in 4.P1/4.P3:** pick a low-Iq LDO and charger/protection (sum of their quiescent currents goes in section 4), battery divider with a switch, and the LDO dropout simulation at 3.4 V. The PCB outline must leave room for the cell bay or the cell sits outside the board; I announce any outline change to the Lead.

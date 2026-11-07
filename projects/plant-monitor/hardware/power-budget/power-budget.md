# Power budget and battery life (task 2.3, NFR-01)

Author: Emil (PCB Designer) · Date: 2026-11-04 · Status: **draft for the G2 review, all inputs are estimates**
Calculator: [`power_budget.py`](power_budget.py) (Python 3.11, stdlib only) · Tests: [`test_power_budget.py`](test_power_budget.py)
Traces to: NFR-01 (6 months), FR-D01 (15-min sampling), FR-D02 (hourly report), FR-E03/E04 (critical wake, inference), ADR-012 (second MQTT publish), PR #2 items 12 and 19.

**Nothing in this document is a measurement.** Every current and time is either quoted from a repo document, recalled from a datasheet that the session could not open (espressif.com returns a proxy 403), or an engineering assumption. Each is tagged in section 4. Task 5.4 replaces them (section 9).

## 1. Result

Headline figures apply **Arsany's NFR-01 rule literally** (PR #2 item 12, acceptance matrix): projected life = **0.8 x rated capacity / average current >= 4380 h**. There is **no self-discharge term** in that rule. Self-discharge is shown only as a separately labelled **extra-margin** line ("+SD" / "extra"), never in a verdict.

| Question | Answer (estimates) |
|---|---|
| Average load, typical | **5.9 mAh/day** = 0.244 mA (sleep 0.3, 96 sample wakes 1.8, 24 hourly Wi-Fi sessions + 1 critical wake 3.8) |
| Rated 1S LiPo needed for 6 months (4380 h), typical, per the rule | **about 1340 mAh rated** (0.8 x 1336 = 1069 mAh derated = the 4380 h load) |
| Best / worst case, per the rule | best **about 470 mAh**, worst **about 4360 mAh** (every parameter at its worst at once; a stress bound, not a design point) |
| Does a 1500 mAh-class cell make it? (rule) | Typical: **yes, 6.7 months** (1200 mAh derated / 0.244 mA = 4915 h >= 4380 h). A 2000 mAh-class cell: typical **9.0 months**, best 25.5, worst 2.7 |
| Extra margin line (not the rule): with cell self-discharge, assumed 2 %/month | 1500 mAh: **5.8 months** (would fail); 2000 mAh: **7.3 months**; rated capacity needed 1572 mAh instead of 1336 mAh |
| What dominates | Wi-Fi sessions are **65 %** of the budget, sample wakes 30 %, deep sleep only **5 %** |
| Deep-sleep limit for the requirement (PR #2 item 19) | Per the rule, typical Wi-Fi and sampling terms: **134 uA whole board for a 2000 mAh rated cell, 43 uA for 1500 mAh** (with self-discharge: 80 uA and 2 uA). Proposed requirement value: **<= 50 uA**, design target <= 25 uA; table in section 6 |
| Biggest levers (section 7) | Light sleep during the soil warm-up: **-0.78 mAh/day (-13 %)**; fast connect + hub every 2nd report: **-1.4 mAh/day**; hub unreachable every hour costs **+1.4 mAh/day** |
| Verdict on NFR-01 | **Not provable yet.** By the rule the typical case passes with a 1500 mAh-class cell (6.7 months) and with margin at 2000 mAh; the worst-case stack fails with any plausible cell. Everything hinges on Wi-Fi connect time and current, which only 5.4 can settle, and on the cell that fits the enclosure (section 8, unanswered). The levers are in section 7 |

**Question for Arsany (for the Lead to log in Needs Arsany; also in the PR comment).** Your NFR-01 rule has no self-discharge term, and I now apply it that way. A LiPo does lose roughly 1-3 % of its charge per month by itself (assumption, no cell chosen; the figure is not from a datasheet). Taking 2 %/month, a 1500 mAh cell drops from **6.7 months (your rule: pass)** to **5.8 months (fail)**. Do you want (a) the rule exactly as written (the 20 % derating is meant to cover self-discharge, temperature and ageing), or (b) self-discharge as an additional term, which pushes the needed cell from about 1340 to about 1570 mAh rated? Until you decide, (a) is the verdict and (b) is the extra-margin line.

## 2. Inputs and decisions applied

- **Capacity rule (Arsany, PR #2 item 12), applied literally:** use the **rated** capacity of the chosen 1S LiPo with **20 % derating**; projected life = derated capacity / average current >= 4380 h; no self-discharge term. Both numbers are stated everywhere (rated and derated = 0.8 x rated).
- **Low-battery warning at 3.4 V** (source: Arsany's answer "ok" to Needs Arsany **A-008.2**, "low-battery 3.4 V", in the PR #2 thread; confirmed by Theo's architect review of this PR; PR #15's schema uses 3400 mV as default). Consequences: (a) the 6 months are counted to the point of the warning, the charge left below 3.4 V is a reserve and is **not** counted; (b) the 20 % derating is taken to cover the capacity that is unusable above 3.4 V, temperature and ageing, and (see section 1 question) self-discharge (`usable_fraction` = 1.0 in the model); 5.4 must check this with a discharge curve at the real load (section 9); (c) with a 3.3 V LDO the headroom at the warning point is only 100 mV, so dropout under Wi-Fi TX peaks must be simulated in 4.P1 (LDO dropout sim, role file) or a lower-dropout/boost-buck path chosen.
- **Scope of the load:** 15-min wake (soil, AHT20, BH1750, battery ADC, both edge-AI models) + hourly Wi-Fi report (cloud POST **and** MQTT publish to the Pi hub, ADR-012) + critical-event Wi-Fi wakes (edge-ai-concept 2.4: at most one per class per 6 h). **Excluded:** BLE setup (setup mode only, ADR-011), OTA downloads, Wi-Fi outage retries, charging losses, USB-powered time. These add load: OTA and outages must be bounded in 4.F (e.g. OTA only above a battery threshold, already in ADR-009; backoff already in architecture section 5).
- 6 months = **4380 h** (the NFR-01 arithmetic in the acceptance matrix, PR #2), i.e. 182.5 days.

## 3. Model

Battery-terminal charge per day, 3.3 V rail from an LDO (load current = battery current):

```
sleep   = I_sleep(board) x 24 h
sample  = 96 wakes x [ (t_boot + t_infer + t_store) x I_cpu + t_sense x (I_cpu + I_periph) ]
wifi    = (24 reports + critical wakes) x (t_connect + t_cloud + t_hub / hub_every_n) x I_wifi_avg
I_wifi_avg = f_tx x I_tx + (1 - f_tx) x I_rx
rated capacity needed  C = load(4380 h) / 0.8            (Arsany's rule, headline)
extra margin only      C = load(4380 h) / (0.8 - self_discharge_per_month x 6)
```

Self-discharge is the cell's own loss as a fraction of rated capacity per month; at 2 %/month it would cost 12 % of rated capacity over 6 months and is the reason the extra-margin line needs 1570 mAh where the rule needs 1340 mAh. It is **not** part of the rule (section 1 question). The inference (Invoke) is in the model, but at 1-50 ms it is below 0.5 % of a sample wake; the sample wake is dominated by the 1.5-3 s soil warm-up, during which the baseline keeps the CPU active (20 mA); the light-sleep lever (section 7) changes only that part (`t_warmup_s`, `i_warmup_cpu_ma`). A sample wake and the Wi-Fi session in the same hour are modelled as separate (the Wi-Fi session adds connect time only, boot is already paid).

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
| case | sleep uA | sleep mAh/d | sample mAh/d | Wi-Fi mAh/d | total mAh/d | load 4380 h mAh | rated mAh needed (rule) | extra: rated mAh incl. self-disch. |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| best | 8.3 | 0.20 | 0.73 | 1.13 | 2.06 | 376 | 470 | 508 |
| typical | 13.2 | 0.32 | 1.76 | 3.78 | 5.86 | 1069 | 1336 | 1572 |
| worst | 31.7 | 0.76 | 3.56 | 14.81 | 19.13 | 3491 | 4364 | 5631 |
<!-- END:scenarios -->

Derated capacity = 0.8 x rated.

<!-- BEGIN:life -->
| rated mAh | derated mAh | best (rule) | typical (rule) | worst (rule) | best +SD | typical +SD | worst +SD |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 500 | 400 | 6.4 | 2.2 | 0.7 | 5.9 | 2.1 | 0.7 |
| 750 | 600 | 9.6 | 3.4 | 1.0 | 8.5 | 3.1 | 1.0 |
| 1000 | 800 | 12.8 | 4.5 | 1.4 | 11.0 | 4.0 | 1.3 |
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
| 1.0 | 13.2 | 4.83 | 1101 | 8.2 | 6.8 |
| 2.5 | 13.2 | 5.86 | 1336 | 6.7 | 5.8 |
| 4.0 | 13.2 | 6.89 | 1571 | 5.7 | 5.0 |
| 6.0 | 13.2 | 8.26 | 1885 | 4.8 | 4.3 |
| 10.0 | 13.2 | 11.01 | 2512 | 3.6 | 3.3 |

**Deep-sleep current uA (MCU term; whole board = this + 8.2)**

| value | board sleep uA | mAh/day | rated mAh needed (rule) | months @1500 mAh (rule) | extra: months @1500 incl. SD |
| --- | --- | --- | --- | --- | --- |
| 5 | 13.2 | 5.86 | 1336 | 6.7 | 5.8 |
| 10 | 18.2 | 5.98 | 1363 | 6.6 | 5.7 |
| 25 | 33.2 | 6.34 | 1446 | 6.2 | 5.4 |
| 50 | 58.2 | 6.94 | 1582 | 5.7 | 5.0 |
| 100 | 108.2 | 8.14 | 1856 | 4.8 | 4.3 |

**TX current mA (i_tx_ma)**

| value | board sleep uA | mAh/day | rated mAh needed (rule) | months @1500 mAh (rule) | extra: months @1500 incl. SD |
| --- | --- | --- | --- | --- | --- |
| 200 | 13.2 | 5.67 | 1294 | 7.0 | 5.9 |
| 260 | 13.2 | 5.86 | 1336 | 6.7 | 5.8 |
| 340 | 13.2 | 6.10 | 1392 | 6.5 | 5.6 |
<!-- END:sensitivity -->

Reading: connect time is the strongest lever (each extra second costs about 0.7 mAh/day, 12 % of the budget); TX current barely matters because TX is a small share of the session; deep sleep matters only when it grows by a factor of 5 or more. Best/typical/worst of all parameters together are in the scenario table.

## 6. Deep-sleep current limit for the requirement (for Theo, PR #2 item 19)

Definition to put in the requirement: **whole-board deep-sleep current measured at the battery terminal, USB unplugged, cell at 3.7 V, all sensors fitted and in their low-power state, soil oscillator off, radio off, RTC timer running.** Limit = the largest value for which the chosen cell still reaches 4380 h with the other terms as in the scenario.

Deep-sleep limit (whole board) that still reaches 6 months, uA (negative = cannot reach even at 0 uA). Rule columns use Arsany's formula; "+SD" columns are the extra-margin line.

<!-- BEGIN:sleep_limit -->
| rated mAh | best (rule) | typical (rule) | worst (rule) | best +SD | typical +SD | worst +SD |
| --- | --- | --- | --- | --- | --- | --- |
| 500 | 14 | -140 | -674 | 7 | -153 | -695 |
| 750 | 59 | -94 | -628 | 49 | -114 | -659 |
| 1000 | 105 | -48 | -583 | 91 | -76 | -624 |
| 1500 | 196 | 43 | -491 | 176 | 2 | -553 |
| 2000 | 288 | 134 | -400 | 260 | 80 | -482 |
| 2500 | 379 | 226 | -309 | 345 | 157 | -411 |
| 3000 | 470 | 317 | -217 | 429 | 235 | -341 |
<!-- END:sleep_limit -->

Theo's independent derivation (review of this PR) gives the same limits: 134 uA / 43 uA (rule) and 80 uA / 2 uA (+SD) for 2000 / 1500 mAh typical. Proposal (Theo accepted the numbers in his review, the requirement text is his):
- **Requirement value: whole-board deep sleep <= 50 uA**, design target <= 25 uA (estimate 13 uA, section 4). It is 3.8x the typical estimate and above the worst-case estimate (31.7 uA), and below the rule limit for a 2000 mAh cell (134 uA). The requirement text must state that this limit does **not** prove NFR-01; NFR-01 is decided by the measured hourly average current (Wi-Fi is 65 %) and the named cell capacity.
- Formula (rule): `limit = (0.8 x C / 182.5 d - (sample + Wi-Fi mAh/day)) / 24 h`, implemented as `max_sleep_current_ua()`.
- **Wi-Fi session, stated honestly:** the typical session in this model is **5.5 s at about 99 mA average** (2.5 s connect + 2.0 s cloud + 1.0 s hub), not 3.5 s. A session of **<= 3.5 s** is a **firmware design target, not the typical case**, and needs two levers together (fast connect to 1.0 s, hub publish every 2nd report; section 7). Whether it becomes a requirement waits for measurement M4 in 5.4; it is not to be written into the requirements before that.

## 7. What-if levers (TYPICAL as base)

<!-- BEGIN:levers -->
| lever | mAh/day | Wi-Fi session s | rated mAh needed (rule) | extra: incl. self-disch. |
| --- | --- | --- | --- | --- |
| base (typical) | 5.86 | 5.5 | 1336 | 1572 |
| light sleep during the soil warm-up (CPU 0.5 mA instead of 20 mA for 1.5 s, assumption) | 5.08 | 5.5 | 1158 | 1363 |
| hub publish every 2nd report (ADR-012 fallback) | 5.51 | 5.0 | 1258 | 1480 |
| no hub publish at all (cloud only) | 5.17 | 4.5 | 1179 | 1387 |
| fast connect: cached BSSID/channel + static IP (connect 1.0 s) | 4.83 | 4.0 | 1101 | 1295 |
| fast connect + hub every 2nd report (session 3.5 s) | 4.48 | 3.5 | 1022 | 1203 |
| fast connect + hub every 2nd + light-sleep warm-up | 3.70 | 3.5 | 845 | 994 |
| hub unreachable every hour: 3 s timeout (Theo's review of ADR-012), hub tried every report | 7.23 | 7.5 | 1650 | 1941 |
| hub unreachable, plus 1 s mDNS fallback lookup (assumption) | 7.92 | 8.5 | 1807 | 2125 |
| hub unreachable, back-off: hub tried every 4th report only | 5.69 | 5.2 | 1297 | 1526 |
| 30-min sampling (O-1 fallback) | 4.98 | 5.5 | 1136 | 1336 |
| critical wakes at the rate-limit cap (16/day) | 8.13 | 5.5 | 1854 | 2181 |
| no critical wakes | 5.71 | 5.5 | 1302 | 1531 |
<!-- END:levers -->

- **Light sleep during the soil warm-up** is the largest single lever on the sample-wake side: the baseline holds the CPU active (20 mA) for the 1.5 s warm-up of every one of the 96 daily wakes. With the CPU in light sleep (assumed 0.5 mA including the RTC and timer; the true value is unverified and is measured in M3), the sample term falls from 1.76 to 0.98 mAh/day, **-0.78 mAh/day, 13 % of the total**. Cost: firmware must keep the soil oscillator supply and the I2C sensors alive across light sleep and wake on a timer (Mira's call); sensors are on their own supply gate. Together with fast connect and hub every 2nd report the typical load falls to 3.7 mAh/day.
- **Hub unreachable** (home-network hub down, common): the 1 s publish becomes a 3 s timeout every hour (Theo's review of ADR-012), costing **+1.4 mAh/day (+23 %)** in this model (7.2 vs 5.9; the model charges the session average of 99 mA for the longer time, a slight over-estimate as no TX happens while waiting; at 85 mA it is +1.1). A 1 s mDNS fallback lookup (assumption) takes it to +2.1 mAh/day. Theo's review quoted "about +0.2 mAh/day"; I cannot reproduce that figure (3 s x 85 mA x 24 h = 1.7 mAh/day in total for the timeouts), so I report my number and ask Theo to check. **Back-off** (try the hub only every 4th report after failures) brings it to 5.7 mAh/day, i.e. below the base case: firmware should back off when the hub fails (Mira, ADR-012 follow-up).
- The second MQTT publish (ADR-012) costs 0.69 mAh/day in this model (5.86 vs 5.17), 12 % of the budget; ADR-012 estimated 0.67 mAh/day, so the two agree (both unmeasured).
- The 30-min sampling fallback does **not** change FR-E03 as it would double the latency to about 30 min, so it conflicts with the owner-confirmed wording; prefer the Wi-Fi levers (fast connect, hub every 2nd report) and the light-sleep warm-up. Critical wakes at the rate cap cost 39 % more than the base case, so the cap (or a daily limit) is a battery decision for Mira/Theo.

## 8. Which LiPo capacities fit enclosure v2

**Not answerable from the repo.** `projects/plant-monitor/mechanical/` holds only `.gitkeep`; enclosure v1/v2 live in Drive (`04_Builds/Enclosure/v1, v2`), which I could not reach, and WO-002 (#9) has no dimensions yet. I did not invent any. What is needed from Yara (or Arsany from the v2 STEP):

1. Free battery bay inside enclosure v2: length x width x height in mm, including any cut-outs, and the PCB outline once 4.P2 fixes it (any outline change is announced to the Lead, playbook rule).
2. Required clearance for the cell (swelling and wiring allowance; value to be set by Yara, not by me).

Method then: pouch LiPo cells are usually coded by their envelope, for example `603450` = 6.0 mm x 34 mm x 50 mm (thickness x width x length, in mm; naming convention, **unverified from memory**). Take the maximum envelope that fits, find cells in that envelope on the shop pages (capacity, protection circuit, connector from the datasheet), and compare the **rated** capacity with section 5: **by Arsany's rule a rated capacity of about 1340 mAh is needed for the typical case (about 1570 mAh if self-discharge is added, section 1 question); 2000 mAh gives a large margin (9.0 months by the rule)**. If the bay cannot hold that, the levers in section 7 must bring the requirement down to what the bay holds. Cell candidates for the BOM are for 2.5 / 4.H0 (Arsany orders).

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

- **Needs Arsany (question):** self-discharge in the NFR-01 rule, yes or no (section 1); his answer decides whether the 1500 mAh typical verdict is 6.7 months (pass) or 5.8 months (fail).
- **Needs Arsany / Yara:** enclosure v2 battery bay dimensions (section 8); cell choice and any order (Arsany orders, hard rule); a current meter for 5.4 (purchase is Arsany's).
- **Datasheet tags:** the four ESP32-C3 rows are now **DR** (section 11). Still D?: Aosong AHT20, ROHM BH1750FVI, ESP32-C3-MINI-1 module datasheet (flash leakage).

## 11. Update 2026-11-07 (2.5 follow-up): datasheet read, cell 1000 mAh minimum

Source read: ESP32-C3 Series Datasheet v2.4, `https://documentation.espressif.com/esp32-c3_datasheet_en.pdf` (HTTP 200, 900 kB, PDF creation date 2026-05-06), Tables 5-7, 5-8, 5-9 on pp. 56-57. Full comparison and what-if: [`verified-currents.md`](verified-currents.md). **Model values are unchanged**; only the tags changed.

What the datasheet says against the model: deep sleep 5 uA agrees; CPU 160 MHz is 23-28 mA (model 15/20/30: best and typical too low); RX 84-87 mA peak (model best 70 too low); TX 276-335 mA peak at maximum power and 100 % duty (model best 200 too low). Replacing best/typical/worst by the datasheet values (CPU 23/23/28, RX 84/84/87, TX 276/285/335) moves the typical case from 4.49 to 4.29 months at **1000 mAh rated** (4.94 to 4.72 at 1100 mAh, 6.74 to 6.44 at 1500 mAh), and rated capacity needed for 6 months from 1336 to 1398 mAh.

**The cell in the BOM (LP603449-class, 1000 mAh minimum, reference EEMB datasheet) does not meet NFR-01 in the typical case by Arsany's rule**: 4.5 months at 1000 mAh (4.9 at the 1100 mAh nominal). With the section 7 lever package (typical 3.7 mAh/day, not yet designed into firmware) the 1000 mAh cell would reach about 7.1 months (800 mAh / 3.7 mAh/day). Decision for Arsany: larger cell, lever package committed to firmware, or NFR-01 relaxed.
- **For Theo:** the deep-sleep limit in section 6 as a requirement (the Wi-Fi-session figure is a design target only, 5.5 s typical); whether the 6 months are counted to the 3.4 V warning (assumed here); please check the hub-unreachable figure (+1.4 vs your +0.2 mAh/day).
- **For Mira (firmware):** fast Wi-Fi connect (cached channel/BSSID, static IP or DHCP lease reuse), SNTP not on every session, hub publish every 2nd report if needed, hub back-off when unreachable, light sleep during the soil warm-up, critical-wake cap per day; each is a lever in section 7.
- **For me, next in 4.P1/4.P3:** pick a low-Iq LDO and charger/protection (sum of their quiescent currents goes in section 4), battery divider with a switch, and the LDO dropout simulation at 3.4 V.

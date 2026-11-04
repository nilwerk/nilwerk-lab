# Power budget and battery life (task 2.3, NFR-01)

Author: Emil (PCB Designer) · Date: 2026-11-04 · Status: **draft for the G2 review, all inputs are estimates**
Calculator: [`power_budget.py`](power_budget.py) (Python 3.11, stdlib only) · Tests: [`test_power_budget.py`](test_power_budget.py)
Traces to: NFR-01 (6 months), FR-D01 (15-min sampling), FR-D02 (hourly report), FR-E03/E04 (critical wake, inference), ADR-012 (second MQTT publish), PR #2 items 12 and 19.

**Nothing in this document is a measurement.** Every current and time is either quoted from a repo document, recalled from a datasheet that the session could not open (espressif.com returns a proxy 403), or an engineering assumption. Each is tagged in section 4. Task 5.4 replaces them (section 9).

## 1. Result

| Question | Answer (estimates) |
|---|---|
| Average load, typical | **5.9 mAh/day** (sleep 0.3, 96 sample wakes 1.8, 24 hourly Wi-Fi sessions + 1 critical wake 3.8) |
| Rated 1S LiPo needed for 6 months (4380 h), typical | **about 1570 mAh rated** (1260 mAh after 20 % derating covers 1070 mAh load plus self-discharge) |
| Best / worst case | best **about 510 mAh**, worst **about 5600 mAh** (every parameter at its worst at once; a stress bound, not a design point) |
| Does a 1500 mAh-class cell make it? | Typical: **no, 5.8 months**. A 2000 mAh-class cell: typical **7.3 months**, best 19, worst 2.5 |
| What dominates | Wi-Fi sessions are **65 %** of the budget, sample wakes 30 %, deep sleep only **5 %** |
| Deep-sleep limit for the requirement (PR #2 item 19) | **80 uA whole board for a 2000 mAh rated cell** with typical Wi-Fi and sampling terms; table in section 6. Proposed requirement value: **<= 50 uA**, design target <= 25 uA |
| Verdict on NFR-01 | **Not provable yet.** Typical meets it with a 2000 mAh-class cell; the worst-case stack does not meet it with any cell that is plausible for the enclosure. The result hinges on Wi-Fi connect time and current, which only 5.4 can settle. Fallbacks are in section 8 |

## 2. Inputs and decisions applied

- **Capacity rule (Arsany, PR #2 item 12):** use the **rated** capacity of the chosen 1S LiPo with **20 % derating**; both numbers are stated everywhere (rated and derated = 0.8 x rated).
- **Low-battery warning at 3.4 V** (Arsany, as given in the task brief; I did not find it in the PR #2 comments I could read). Consequences: (a) the 6 months are counted to the point of the warning, the charge left below 3.4 V is a reserve and is **not** counted; (b) the 20 % derating is taken to cover the capacity that is unusable above 3.4 V, temperature and ageing (`usable_fraction` = 1.0 in the model); 5.4 must check this with a discharge curve at the real load (section 9); (c) with a 3.3 V LDO the headroom at the warning point is only 100 mV, so dropout under Wi-Fi TX peaks must be simulated in 4.P1 (LDO dropout sim, role file) or a lower-dropout/boost-buck path chosen.
- **Scope of the load:** 15-min wake (soil, AHT20, BH1750, battery ADC, both edge-AI models) + hourly Wi-Fi report (cloud POST **and** MQTT publish to the Pi hub, ADR-012) + critical-event Wi-Fi wakes (edge-ai-concept 2.4: at most one per class per 6 h). **Excluded:** BLE setup (setup mode only, ADR-011), OTA downloads, Wi-Fi outage retries, charging losses, USB-powered time. These add load: OTA and outages must be bounded in 4.F (e.g. OTA only above a battery threshold, already in ADR-009; backoff already in architecture section 5).
- 6 months = **4380 h** (the NFR-01 arithmetic in the acceptance matrix, PR #2), i.e. 182.5 days.

## 3. Model

Battery-terminal charge per day, 3.3 V rail from an LDO (load current = battery current):

```
sleep   = I_sleep(board) x 24 h
sample  = 96 wakes x [ (t_boot + t_infer + t_store) x I_cpu + t_sense x (I_cpu + I_periph) ]
wifi    = (24 reports + critical wakes) x (t_connect + t_cloud + t_hub / hub_every_n) x I_wifi_avg
I_wifi_avg = f_tx x I_tx + (1 - f_tx) x I_rx
rated capacity needed  C = load(4380 h) / (0.8 - self_discharge_per_month x 6)
```

Self-discharge is the cell's own loss as a fraction of rated capacity per month; at 2 %/month it costs 12 % of rated capacity over 6 months and is the reason a 1070 mAh load needs 1570 mAh, not 1340 mAh. The inference (Invoke) is in the model, but at 1-50 ms it is below 0.5 % of a sample wake; the sample wake is dominated by the 1.5-3 s soil warm-up. A sample wake and the Wi-Fi session in the same hour are modelled as separate (the Wi-Fi session adds connect time only, boot is already paid).

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

### Scenario results

| case | sleep uA | sleep mAh/d | sample mAh/d | Wi-Fi mAh/d | total mAh/d | load 4380 h mAh | rated mAh (no self-disch.) | rated mAh needed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| best | 8.3 | 0.20 | 0.73 | 1.13 | 2.06 | 376 | 470 | 508 |
| typical | 13.2 | 0.32 | 1.76 | 3.78 | 5.86 | 1069 | 1336 | 1572 |
| worst | 31.7 | 0.76 | 3.56 | 14.81 | 19.13 | 3491 | 4364 | 5631 |

"rated mAh (no self-disch.)" = load / 0.8 only; "needed" also covers cell self-discharge. Derated capacity = 0.8 x rated.

### Life in months per rated capacity (derated 80 %, self-discharge included)

| rated mAh | derated mAh | best | typical | worst |
| --- | --- | --- | --- | --- |
| 500 | 400 | 5.9 | 2.1 | 0.7 |
| 750 | 600 | 8.5 | 3.1 | 1.0 |
| 1000 | 800 | 11.0 | 4.0 | 1.3 |
| 1500 | 1200 | 15.4 | 5.8 | 1.9 |
| 2000 | 1600 | 19.4 | 7.3 | 2.5 |
| 2500 | 2000 | 22.8 | 8.8 | 3.0 |
| 3000 | 2400 | 25.9 | 10.1 | 3.6 |

The capacities are generic values, not products. Cell choice is not made here (no datasheet of a specific cell was read).

### Sensitivity, one parameter at a time around TYPICAL

**Wi-Fi connect time (t_connect_s), s**

| value | board sleep uA | mAh/day | rated mAh needed | months @1500 mAh |
| --- | --- | --- | --- | --- |
| 1.0 | 13.2 | 4.83 | 1295 | 6.8 |
| 2.5 | 13.2 | 5.86 | 1572 | 5.8 |
| 4.0 | 13.2 | 6.89 | 1849 | 5.0 |
| 6.0 | 13.2 | 8.26 | 2218 | 4.3 |
| 10.0 | 13.2 | 11.01 | 2956 | 3.3 |

**Deep-sleep current, MCU term in uA (whole board = this + 8.2)**

| value | board sleep uA | mAh/day | rated mAh needed | months @1500 mAh |
| --- | --- | --- | --- | --- |
| 5 | 13.2 | 5.86 | 1572 | 5.8 |
| 10 | 18.2 | 5.98 | 1604 | 5.7 |
| 25 | 33.2 | 6.34 | 1701 | 5.4 |
| 50 | 58.2 | 6.94 | 1862 | 5.0 |
| 100 | 108.2 | 8.14 | 2184 | 4.3 |

**TX current (i_tx_ma), mA**

| value | board sleep uA | mAh/day | rated mAh needed | months @1500 mAh |
| --- | --- | --- | --- | --- |
| 200 | 13.2 | 5.67 | 1523 | 5.9 |
| 260 | 13.2 | 5.86 | 1572 | 5.8 |
| 340 | 13.2 | 6.10 | 1638 | 5.6 |

Reading: connect time is the strongest lever (each extra second costs about 0.7 mAh/day, 12 % of the budget); TX current barely matters because TX is a small share of the session; deep sleep matters only when it grows by a factor of 5 or more. Best/typical/worst of all parameters together are in the scenario table.

## 6. Deep-sleep current limit for the requirement (for Theo, PR #2 item 19)

Definition to put in the requirement: **whole-board deep-sleep current measured at the battery terminal, USB unplugged, cell at 3.7 V, all sensors fitted and in their low-power state, soil oscillator off, radio off, RTC timer running.** Limit = the largest value for which the chosen cell still reaches 4380 h with the other terms as in the scenario.

Deep-sleep limit (whole board) that still reaches 6 months, uA (negative = cannot reach even at 0 uA):

| rated mAh | other terms best | other terms typical | other terms worst |
| --- | --- | --- | --- |
| 500 | 7 | -153 | -695 |
| 750 | 49 | -114 | -659 |
| 1000 | 91 | -76 | -624 |
| 1500 | 176 | 2 | -553 |
| 2000 | 260 | 80 | -482 |
| 2500 | 345 | 157 | -411 |
| 3000 | 429 | 235 | -341 |

Proposal for Theo (he decides):
- **Hard limit** = the "typical" column for the chosen cell, e.g. **80 uA for a 2000 mAh rated cell**. Formula: `limit = ((0.8 - 0.02 x 6) x C / 182.5 d - (sample + Wi-Fi mAh/day)) / 24 h`, implemented as `max_sleep_current_ua()`.
- **Requirement value: whole-board deep sleep <= 50 uA**, design target <= 25 uA (the estimate is 13 uA, section 4; the target keeps a factor of about 2 for parts not chosen yet). 50 uA leaves 30 uA headroom under the 80 uA hard limit for the 2000 mAh case.
- The limit is only meaningful together with the Wi-Fi budget: at 1500 mAh the typical column leaves essentially **0 uA**, so a 1500 mAh cell passes NFR-01 only if Wi-Fi time is cut (section 8). The requirement should therefore name the cell capacity it assumes, or be paired with a Wi-Fi-session limit (proposal: **cloud + hub session <= 3.5 s and <= 100 mA average**, i.e. the typical row; to be confirmed after 5.4).

## 7. What-if levers (TYPICAL as base)

| lever | mAh/day | rated mAh needed |
| --- | --- | --- |
| base (typical) | 5.86 | 1572 |
| hub publish every 2nd report (ADR-012 fallback) | 5.51 | 1480 |
| no hub publish at all (cloud only) | 5.17 | 1387 |
| fast connect: cached BSSID/channel + static IP (connect 1.0 s) | 4.83 | 1295 |
| 30-min sampling (O-1 fallback) | 4.98 | 1336 |
| critical wakes at the rate-limit cap (16/day) | 8.13 | 2181 |
| no critical wakes | 5.71 | 1531 |

The second MQTT publish (ADR-012) costs 0.69 mAh/day in this model (5.86 vs 5.17), 12 % of the budget; ADR-012 estimated 0.67 mAh/day, so the two agree (both unmeasured). The 30-min sampling fallback does **not** change FR-E03 as it would double the latency to about 30 min, so it conflicts with the owner-confirmed wording; prefer the Wi-Fi levers (fast connect, hub every 2nd report). Critical wakes at the rate cap cost 39 % more than the base case, so the cap (or a daily limit) is a battery decision for Mira/Theo.

## 8. Which LiPo capacities fit enclosure v2

**Not answerable from the repo.** `projects/plant-monitor/mechanical/` holds only `.gitkeep`; enclosure v1/v2 live in Drive (`04_Builds/Enclosure/v1, v2`), which I could not reach, and WO-002 (#9) has no dimensions yet. I did not invent any. What is needed from Yara (or Arsany from the v2 STEP):

1. Free battery bay inside enclosure v2: length x width x height in mm, including any cut-outs, and the PCB outline once 4.P2 fixes it (any outline change is announced to the Lead, playbook rule).
2. Required clearance for the cell (swelling and wiring allowance; value to be set by Yara, not by me).

Method then: pouch LiPo cells are usually coded by their envelope, for example `603450` = 6.0 mm x 34 mm x 50 mm (thickness x width x length, in mm; naming convention, **unverified from memory**). Take the maximum envelope that fits, find cells in that envelope on the shop pages (capacity, protection circuit, connector from the datasheet), and compare the **rated** capacity with section 5: **a cell with rated capacity >= 1600 mAh is needed for the typical case, >= 2000 mAh for a margin**. If the bay cannot hold that, the levers in section 7 must bring the requirement down to what the bay holds. Cell candidates for the BOM are for 2.5 / 4.H0 (Arsany orders).

## 9. To be measured in 5.4 (dev kit, then PCB) to replace estimates

Needs hands on hardware: Peter does these via a work order; the work order text is Emil's to draft once the dev-kit list is fixed. Equipment: a current meter that resolves 1 uA in deep sleep and records mA bursts (source-measure unit or a power profiler; choice and any purchase are Arsany's), a bench supply or a charged cell, and the same firmware as the field build.

| # | Measure | On | Replaces | Pass/fail use |
|---|---|---|---|---|
| M1 | Deep-sleep current at 3.7 V, USB unplugged, sensors fitted, 10 min settle, mean over 60 s | dev kit, then PCB | section 4 sleep rows | <= 50 uA (section 6) |
| M2 | Same, at 3.3 V, 4.2 V and 3.0 V; at 0 C / 25 C / 40 C if a chamber is available | PCB | temperature and divider terms | trend only |
| M3 | Current trace of one sample wake (boot, warm-up, AHT20, BH1750, inference): duration and charge in mA*s | dev kit | t_boot, t_sense, I_cpu, I_periph | charge per wake |
| M4 | Current trace of one hourly session: association, DHCP, SNTP, cloud TLS + POST, hub TLS + MQTT: time per phase, average mA, TX peak mA; 20 sessions, median and worst | dev kit on the real router | t_connect, t_cloud, t_hub, I_rx, I_tx, f_tx | charge per session |
| M5 | Same with static IP and cached BSSID/channel; with hub publish every 2nd report | dev kit | lever table | decides fallback |
| M6 | Charge of a critical-event wake | dev kit | critical wakes | rate cap |
| M7 | Battery sense divider leakage and ADC reading at 3.4 / 3.7 / 4.2 V | PCB | divider term, 3.4 V warning accuracy | warning within tolerance (to be set by Theo) |
| M8 | LDO dropout and output sag during Wi-Fi TX at 3.4 V and 3.0 V, with the cell's internal resistance | PCB (and ngspice before layout) | headroom at the 3.4 V warning | no brown-out reset at 3.4 V |
| M9 | Discharge of a real cell at the measured average load down to 3.4 V (accelerated with a higher duty if needed, stated) | cell + PCB | `usable_fraction` and the 20 % derating | capacity above 3.4 V >= 0.8 x rated |
| M10 | Self-discharge of the chosen cell over 4 weeks (or the maker's datasheet figure with citation) | cell | self-discharge row | <= 2 %/month |
| M11 | OTA download charge, 1.5 MB slot (architecture), once | dev kit | excluded OTA load | add to the budget per OTA |

After M1-M6 the script is run with the measured values (edit `TYPICAL`, tag each field "measured, <date>, <file>") and the table in section 5 is regenerated.

## 10. Open points

- **Needs Arsany / Yara:** enclosure v2 battery bay dimensions (section 8); cell choice and any order (Arsany orders, hard rule); a current meter for 5.4 (purchase is Arsany's).
- **Needs a person with network access:** read the five datasheet tables behind the D? rows and replace the tags with section and table numbers.
- **For Theo:** the deep-sleep limit and Wi-Fi-session limit in section 6 as a requirement; whether the 6 months are counted to the 3.4 V warning (assumed here).
- **For Mira (firmware):** fast Wi-Fi connect (cached channel/BSSID, static IP or DHCP lease reuse), SNTP not on every session, hub publish every 2nd report if needed, critical-wake cap per day; each is a lever in section 7.
- **For me, next in 4.P1/4.P3:** pick a low-Iq LDO and charger/protection (sum of their quiescent currents goes in section 4), battery divider with a switch, and the LDO dropout simulation at 3.4 V.

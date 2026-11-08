# Edge AI concept and dataset plan (task 2.7)

Author: Mira (Firmware + Edge AI) · Status: draft for G2 review, owner answers of PR #4 recorded (rev 2) · Date: 2026-11-03
Traces to: Requirements v0.1 section 5 and FR-E01..FR-E04; also FR-D02, FR-D04, FR-D05, FR-A07, UC-08, NFR-01.
Scope approved in Q-16: thirst forecast, watering/rain event detection, sensor-fault detection.

No model has been trained and no dataset has been downloaded for this note. Every number marked **target** is a requirement or a proposal. Every number marked **estimate** is a calculation to be replaced by a measurement in 4.AI2/4.AI3. Nothing here is a result.

## 1. Summary

- Two small int8 TFLite Micro models run every 15 min on the ESP32-C3 with Wi-Fi off:
  **Model A** (thirst forecast, regression) and **Model B** (event and fault classifier).
- Both consume calibrated **relative moisture (0-100 %)** and its slopes, never raw ADC counts. This closes most of the domain gap to public data.
- Training data: Mendeley precision-irrigation dataset (primary), ISMN (secondary, in scope for research/demo only), synthetic faults, our own cloud data later. ISMN as a secondary source (research and demo use only, owner decision, see 3.2). ProjectPlant is evaluation-only.
- Evaluation: blocked split by calendar weeks with a 3-day gap (no leakage across the 72 h horizon), plus held-out sector/station. Baseline is the average watering interval.
- Fallback if accuracy is weak: closed-form drying-curve extrapolation for A, deterministic rules for faults in B, coarse "water in" buckets in the app, retraining on our own cloud data and shipping via OTA (FR-D05).

## 2. Models

### 2.1 Shared device-side feature pipeline (runs in plain C, not in the model)

| Item | Definition |
|---|---|
| Wake cadence | every 15 min (deep sleep between, NFR-01); Wi-Fi stays off |
| Sensor read | moisture raw, averaged over several spaced samples after warm-up (playbook rule), then EMA |
| Relative moisture `m` | `100 * (raw - dry) / (wet - dry)` clipped to [-10, 110] then stored 0-100 as uint8; dry/wet points come from the per-device calibration (NFR-02) |
| History kept | last 96 samples of `m` (24 h at 15 min) = 96 B, plus temperature and light as uint8 at the same cadence = 192 B. Fits easily in RTC memory (survives deep sleep) |
| Derived | slope of `m` over 1 h, 6 h, 24 h (percentage points per hour, least squares over the window), time since last detected wetting event, hour of day as sin/cos |

Slopes over 1 h / 6 h / 24 h and time of day are the features the Requirements already name (section 5).

### 2.2 Model A: thirst forecast (FR-E01, UC-08)

| Item | Definition |
|---|---|
| Question | Hours until `m` falls to this plant's dry threshold `T` |
| Inputs (14 floats, quantised to int8) | `m_now`, slope 1 h, slope 6 h, slope 24 h, min and max of `m` over 24 h, temperature now, temperature mean 24 h, log light mean 6 h, sin(hour), cos(hour), `T` (dry threshold in relative units, default 25), hours since last wetting event (capped 72), soil type code (1 value; house / pot / garden-like, from FR-A04) |
| Window | 24 h history summarised into the features above. The model itself sees one feature vector, not a sequence |
| Output | one value, hours to threshold, clipped to [0, 72]. 72 h is the FR-E01 horizon; beyond it the app shows "> 3 days" |
| Architecture (proposal) | MLP 14 -> 24 -> 12 -> 1, ReLU, int8 post-training quantisation with a representative dataset |
| Label | For each 15-min tick `t`: first future time `t'` where `m` < `T` and no wetting event occurred in `(t, t']`; label = `t' - t` in hours. Ticks where a wetting event occurs before the threshold is reached are **censored** and excluded from the metric (the watering interval is what the baseline predicts, so they are reported separately). Ticks with no crossing within 72 h get label 72 |
| Size budget | about 14*24 + 24*12 + 12 + biases = under 700 weights, **estimate** about 1 KB of weights, 3-5 KB flatbuffer. Far below the 30 KB limit |
| RAM budget | tensor arena **estimate** under 2 KB; with history buffers and interpreter state still far below 20 KB |
| Latency | about 700 MACs, **estimate** well under 1 ms on a 160 MHz RISC-V core; limit 50 ms. To be measured on the board (FR-E04) |
| Metric | Mean absolute error in hours on held-out ticks whose true label is within 72 h; also reported per horizon bucket (0-12, 12-24, 24-48, 48-72 h) and as MAE by soil type |
| Target | MAE <= 12 h overall (FR-E01) **and** MAE below the baseline. Internal target (confirmed by Arsany): at least 20 % lower MAE than baseline, so "beats" is not a coin toss |
| Baseline | "Average watering interval": per sector or plant, mean time between wetting events in the training weeks; prediction at time `t` = max(0, mean interval - time since last wetting event), clipped to 72 h. Evaluated on exactly the same ticks as the model |

### 2.3 Model B: event and fault classifier (FR-E02, FR-E03, FR-A07)

| Item | Definition |
|---|---|
| Question | What is happening to the soil/sensor right now? |
| Classes (6) | 0 normal; 1 wetting (watering or rain, merged because FR-E02 asks for "watering/rain" and the device cannot tell them apart); 2 drying unusually fast (heat, sun); 3 waterlogged; 4 sensor out of soil; 5 sensor fault (flatline, spike, dropout) |
| Inputs | Window of the last 24 ticks (6 h) with 4 channels per tick: `m` minus `m` 15 min ago, `m` minus `m` 1 h ago, temperature minus 24 h mean, light (log). Plus 3 scalars: `m_now`, slope 24 h, hours since last wetting. 24 x 4 + 3 = 99 int8 inputs |
| Output | softmax over 6 classes. Decision rule depends on the class (see 2.4): **fast path** for wetting, out of soil and sensor fault (one tick, `p >= p_fast`, `p_fast` chosen on validation, starting value 0.9); **debounce** only for the weak classes fast drying and waterlogged (`p >= 0.8` in 2 of 3 consecutive ticks) |
| Architecture (proposal) | 1D conv (8 filters, kernel 3, stride 2) -> conv (16, 3, stride 2) -> global average pool -> dense 6, plus the scalars concatenated before the dense layer. About 2-3 k weights |
| Label definition | **Wetting**: Mendeley's 789 validated irrigation events (start time to end plus 30 min), ISMN rain/irrigation-flagged rises where precipitation is available. **Fast drying**: slope 6 h below the 5th percentile of the training distribution while temperature or light is above its 75th percentile; derived label, flagged as weak. **Waterlogged**: `m` above 95 for at least 6 h (drainage-limited); derived label, weak. **Out of soil**: synthetic only (3.4). **Fault**: Mendeley raw-layer readings that are flatlined (identical value for at least 2 h while neighbours vary), spikes (jump larger than 40 points that reverts within 30 min) and dropouts (missing records), plus synthetic injections |
| Size budget | **estimate** 4-8 KB flatbuffer, limit 30 KB |
| RAM budget | **estimate** arena 4-8 KB (largest activation 12 x 8 int8 plus scratch), limit 20 KB total |
| Latency | **estimate** about 30-60 k MACs, a few ms at 160 MHz without FPU or SIMD; limit 50 ms. Measure on the board |
| Metrics | Per class recall and precision; confusion matrix; false-alert rate per unit-week at the decision actually used per class (single tick for the fast-path classes, debounced for the weak ones) |
| Targets | Wetting recall >= 95 %, fault recall >= 90 % on held-out public data (FR-E02). False alerts: FR-E02 allows at most 1 per week per unit. At 672 ticks per week this means a per-tick false-positive rate below about 0.15 % at the decision threshold. For the fast-path classes there is no debounce to lean on, so this budget is carried by `p_fast` alone: `p_fast` is raised on validation until the held-out normal data meets it, and the recall cost of that is reported. On-unit confirmation needs the bench (4.AI3) |
| Baseline | Rule detector: wetting if `m` rises by at least 8 points within 1 h; fault if the value is constant for 2 h or jumps more than 40 points in one tick; no rule for fast drying or waterlogging beyond fixed thresholds. The model must match or beat the rules on recall at equal false-alert rate; otherwise the rules ship (section 7) |

**Delta as built (task 4.AI2, review C4; the table above is the plan, this is what exists).** The first trained Model B differs from the specification above and the contract change is recorded here, not silent:

| Item | Concept 2.3 | Built in 4.AI2 | Reason |
|---|---|---|---|
| Classes | 6 | 2 (normal, wetting) | only wetting has real labels (A-032); fault and out-of-soil have no real positives; fast drying and waterlogged are weak labels outside the FR-E02 claim |
| Inputs | 24 ticks x 4 channels + 3 scalars = 99 int8 | 8 ticks x 2 channels (moisture only: `m` minus `m` 15 min ago, `m` minus `m` 1 h ago) + 2 scalars (`m_now`, slope over the window) = 18 int8 | moisture only in this slice (temperature, light and hours-since-wetting not used; the sensor has no light in public data, see data card) |
| Window | 24 ticks (6 h) | 8 ticks (2 h) | a window needs consecutive valid samples; with 12 consecutive valid samples 15 of 32 val and 20 of 40 test positives stay scorable; a 28-tick context would keep only 11 val / 12 test |
| Network | 1D conv, dense 6 | MLP 18 -> 16 -> 8 -> 2 | fewer TFLM ops, 3,664 B flatbuffer |
| FR-E02 | recall >= 95 % at <= 1 FA/unit-week | not met: int8 40 % test (8/20, 0.52 FA/wk); float 35 % | see `ml/reports/model-b-wetting-v0.md`; labels are circular, scorable positives few |

Next slice (gap-tolerant windows, pooled event-level cross-validation) may move the window or the input count again; any change updates this table.

### 2.4 Cross-cutting

- **Critical events** (confirmed by Arsany, PR #4, open item 8). A critical event wakes Wi-Fi at once and sends an immediate report (FR-E03, FR-A07). Everything else rides along with the hourly report (FR-D02). When Wi-Fi is down, results are stored with the readings (FR-D04). The set, so that FR-A07 is testable:

  | Model B class | Critical? | Condition | Decision path | App alert |
  |---|---|---|---|---|
  | 0 normal | no | n/a | n/a | none |
  | 1 wetting | **only if unexpected**, defined as: `m` after the rise is >= 95, **or** the rise starts while `m` was already >= 80 (watering a wet pot / flood / leak). A normal watering of a dry plant (`m` before < 80 and after < 95) is **not** critical | single tick | `wetting_unexpected` |
  | 1 wetting (normal) | no | any other rise | single tick (still detected at once, to reset "hours since last wetting") | none; shown as "watered" in the next hourly report |
  | 2 drying unusually fast | no | n/a | debounce 2 of 3 | none; hint in care tips |
  | 3 waterlogged | yes | `m` >= 95 for >= 6 h (class 3) | debounce 2 of 3 | `waterlogged` |
  | 4 sensor out of soil | yes | class 4 | single tick | `sensor_out_of_soil` |
  | 5 sensor fault | yes | class 5 (flatline, spike, dropout) | single tick | `sensor_fault` |

  Rate limit (confirmed): at most one critical wake per class per 6 h per unit, so a repeating fault cannot drain the battery (NFR-01); further occurrences go into the hourly report. The alert names above are still proposals; Theo defines the final enums in the device report schema. FR-A07 test: feed a scripted `m` sequence per row, assert alert yes/no and alert name. "Unexpected" is thus a numeric condition, not a judgement.
- **FR-E03 latency (worst case, arithmetic).** FR-E03: phone alert <= 15 min after the event. The device only looks every 15 min, so the budget is consumed by the tick spacing alone.
  - Debounce 2 of 3 as first written: event just after tick `k`; first observed at tick `k+1` (<= 15 min); confirmed at `k+2` (<= 30 min); plus connect and send. **Worst case about 30 min + connect. This breaks FR-E03, so the single-tick fast path above is required** for wetting, out of soil and fault. Debounce is kept only for fast drying and waterlogged, which are slow phenomena and are **not** claimed to meet FR-E03 (waterlogged is defined over >= 6 h anyway). Confirmed by Arsany (item 7): FR-E03 applies to the fast-path classes (wetting, out of soil, sensor fault) only.
  - Fast path: event just after tick `k` -> observed at tick `k+1`: <= 15 min. Then, per wake, estimates to be measured in 4.AI3: sensor warm-up and samples about 2-3 s, feature and Invoke() a few ms, Wi-Fi association plus TLS plus POST about 3-10 s. **Worst case about 15 min + 5-13 s (estimate).**
  - So **<= 15 min cannot be met literally** if the event starts right after a tick, by those few seconds, with a 15-min cadence. **Decided by Arsany (PR #4, item 7):** FR-E03 is relaxed to "<= 15 min after the first tick that observes the event" for wetting, out of soil and sensor fault (about 15 min + 15 s measured from the event). The FR-E03 test uses exactly this wording: the clock starts at the first tick where the event is observed. The 10-min tick alternative costs about 50 % more wake-ups and fails NFR-01 margins; not adopted. **The Requirements text still says "<= 15 min after the event" and must be corrected before v1.0** (Lead / Requirements owner); until then this note and the test are the reference.
  - Note that a wetting ramp may be only partly visible at the first tick; the fast path acts on the first tick where `p >= p_fast`, so the latency is counted from the first tick that shows the rise, and the recall number in 2.3 must be measured for that first tick.
- **Model update** ships as a separate OTA image part with rollback (FR-D05). Model version goes into the report.
- **Size counting rule** (adopted from the Architect's review of PR #4; QA's FR-E04 row uses the same rule):
  - **Flash < 30 KB** = the model flatbuffer (weights + graph), per model. This is what FR-E04 and the OTA model part (FR-D05) measure.
  - **RAM < 20 KB** = the tensor arena **plus** all model-specific persistent buffers the AI path adds: MicroInterpreter instance, input/output buffers, and the feature history ring (96 B + 192 B). RTC-resident history counts too. It does **not** include the general firmware heap (Wi-Fi, BLE, TLS). The budget is per inference path; if A and B share one arena (sequential use), count the larger arena plus both persistent parts, and say so in the size report.
  - **Interpreter and op kernels** (TFLite Micro code) are **counted separately** and reported, not against 30 KB. The size report states firmware image size with and without the AI component so the OTA slot budget (about 1.5 MB per slot) stays honest. Only the ops actually used get registered (`MicroMutableOpResolver`: fully connected, conv2d, mean, softmax, reshape).
  - **< 50 ms** = wall-clock of one `Invoke()` on the real board at 160 MHz, measured, per model.
- **Power**: inference time is small next to sensor warm-up (>= 1.5 s) and the Wi-Fi wake. Current per state is to be stated in 4.AI3's PR; no number is claimed here.

## 3. Datasets

Licence rows say how each licence was checked. The session network blocked `data.mendeley.com`, `ismn.bafg.de` and direct GitHub API access, so two licences could not be read on their own pages by the team. For both, the owner has since quoted the terms (below); these quotes are **quoted by Arsany, not verified by the team**.

### 3.1 Mendeley: Soil Moisture, Irrigation Actuator and Weather Dataset (primary)

| Item | Detail |
|---|---|
| Source | https://data.mendeley.com/datasets/c837v6p8ph (version 2: https://data.mendeley.com/datasets/c837v6p8ph/2), DOI 10.17632/c837v6p8ph.2 |
| Licence | **Partially verified.** (a) CC BY 4.0 per Requirements v0.1 and per a third-party project citing this DOI; **the CC BY 4.0 line itself has still not been read from the Mendeley page** (host blocked; the search snippet did not show it). (b) Arsany quoted the Mendeley terms of use (PR #4, quoted by Arsany, not verified by the team): "We hereby grant to you a non-exclusive, personal, non-transferable license, in accordance with these Terms of Use, to [download, install and use the Software]". Owner's reading: usable for our research and demo products. Attribution is required if CC BY 4.0 holds; cite DOI and authors in the data card. **Action remains: someone with network access reads the licence line on the dataset page before any release (open item 2)** |
| Content | IoT farm in Arnesano (Lecce), Apulia, Italy; season Feb-Sep 2025; five sectors, including a potted-tomato sector; three layers (raw, processed, analysis-ready). From the page description: raw layer 486,894 sensor measurements and 3,055,944 valve-state records; processed layer 789 reconstructed irrigation/fertigation events and five per-sector series on a 10-min grid with 33,259 rows each; ERA5 reanalysis weather. Version 2 is dated 2026-09-14 per the search result; pin the version |
| Size | ZIP size **not found** (not shown in search results). Per-sector series are 33,259 rows, so analysis-ready tables are small; the raw valve records are the large part. Check on download; fetch only the layers we need |
| Use | Model A (drying curves, 789 events define the watering interval baseline), Model B (wetting labels; fault labels from raw-layer anomalies; fast-drying and waterlogged derived labels) |
| Risks | (1) Drip-irrigated farm sectors, not houseplants; intervals are short and regular, so the baseline may look strong or weak for the wrong reason. (2) Moisture units and sensor depth not confirmed from the page (unit, depth and calibration to be read from the data description); relative scaling handles offsets, not different physics. (3) One season, one site, so held-out days still share climate; seasonal drift is not tested. (4) Fault labels are derived from raw-vs-processed differences and will be noisy. (5) Valve telemetry is not available on our device; must not leak into features |

### 3.2 ISMN: International Soil Moisture Network (secondary source; research and demo use only, owner decision)

| Item | Detail |
|---|---|
| Source | https://ismn.bafg.de ; terms at https://ismn.bafg.de/terms-and-conditions |
| Licence | **Not an open licence.** A search summary of the Terms and Conditions page reports: registration required before download, **use restricted to research, commercial use prohibited**, citation of the ISMN papers required; individual networks may add their own conditions. Not read by the team (host blocked). **Owner decision (Arsany, PR #4, item 1/2):** ISMN may be used because we are research only and build demo products. He quoted the terms (quoted by Arsany, not verified by the team): "The copyright is always with the respective ISMN agency." Requirements v0.1 lists ISMN as an open source ("free account") without this restriction; the Requirements text should say "research/demo use, terms apply" |
| Constraints (binding on this plan) | (1) **No redistribution of ISMN data**: nothing from ISMN is committed to the repo, shipped to customers or included in a demo package; only the data card and the manual fetch steps are committed. (2) **No commercial reuse of any model trained on ISMN** without re-checking the terms first; models whose training set includes ISMN are labelled as such in the model card and report. (3) Cite the ISMN papers and the data agencies as the terms require. (4) Keep a Mendeley-only variant of each model reproducible, so a commercial path never depends on ISMN |
| Content | About 3,000 stations (figure from Requirements v0.1; not re-verified), mostly hourly, soil moisture at several depths, soil temperature, some precipitation |
| Size | Depends on the stations chosen; selection is made in the portal. Plan: 20-40 stations, surface layer (0-5 cm), 2-3 years, expected tens of MB. Not downloaded |
| Use | Drying curves by soil type and rain-driven wetting events for Model A and B (garden/balcony cases). Hourly resolution only, so Model B channels beyond 1 h are used when training on ISMN. Secondary: it adds garden/balcony and rain cases, but no FR-E target is defined on it alone |
| Risks | (1) **Licence**: terms not read by the team; see constraints above, especially commercial reuse of trained models. (2) Free account must be created by Arsany; agents may not sign up or accept terms (TEAM.md section 5). (3) Volumetric soil moisture of field stations, not pot substrates. (4) Hourly data cannot support 15-min targets. (5) Raw data must not be redistributed or committed |

**Needs Arsany (the only action; A-xxx to be created by the Lead):** register the free account at ismn.bafg.de himself and download the station selection (or hand the files over to CI storage outside the repo). Agents do not register, accept terms or handle credentials. Everything else in this concept proceeds on Mendeley first; ISMN training runs start once the data is available and never gate a FR-E target.

### 3.3 ProjectPlant (evaluation only)

| Item | Detail |
|---|---|
| Source | https://github.com/jeffschwane/ProjectPlant (cloned read-only for inspection) |
| Licence | **None published**: no LICENSE file in the repository root, README has no licence text. All rights reserved by default. Evaluation only; do not copy into our repo, do not redistribute, do not ship. A `data_card.md` links to it and records the commit id instead |
| Content | Capstone project: houseplant sensors (Flower Care-type, hourly light, soil humidity %, temperature, EC) in a Brooklyn apartment from 2020-05-15. Repo holds 4 CSVs of roughly 0.45-0.57 MB each (about 2 MB). Format seen in the one file inspected: UTF-16, wide layout (one column group per day, one row per hour), `--` for missing values. Whether the four files are four sensors or four export dates was not verified |
| Use | Indoor sanity check of Model A and B outputs on real pot data: does the forecast stay plausible, do wetting events fire on visible rises. Metrics from it are reported separately and never mixed into the FR-E01/E02 numbers |
| Risks | No licence; non-contiguous data (README says readings were overwritten between syncs); sensor-reported % is not our calibration; no ground-truth watering log, so wetting labels would be inferred from rises (weak). Our "percent" may need a per-file min/max normalisation |

### 3.4 Synthetic augmentation

- **Sensor pulled out of soil**: replace `m` with a fast decay to the dry-air reading (relative value near 0), temperature drifting towards air, noise at sensor floor. Several decay speeds and noise levels.
- **Calibration offsets/gains**: shift dry/wet points by up to +/-10 points before normalisation to teach robustness to NFR-02-sized errors (target accuracy +/-5 points).
- **Faults**: inject flatlines, single-tick spikes, dropouts (missing then held value) into otherwise normal windows.
- Synthetic data trains but is **never** in the test set for FR-E02 numbers; synthetic-only test results are reported under their own label.
- Licence: generated by us; no restriction.

### 3.5 Our own data (not a dataset yet)

The cloud keeps raw device data (Requirements section 5). From the first units in week 2, this is the only data from the real probe and pot. Use it for the week-4 check and for retraining; never mix it silently into the held-out public numbers.

## 4. Preprocessing plan (feeds task 4.AI1)

Python 3.11 in `projects/plant-monitor/ml/`, with a data card per dataset (TEAM.md section 6).

```
ml/
  data/<dataset>/DATA_CARD.md    source, version/DOI, retrieval date, licence line + how verified, SHA-256, rows, known issues
  scripts/fetch_mendeley.py      version-pinned download + checksum (run in CI, because the sandbox cannot download; Lead to flag)
  scripts/fetch_ismn.md          manual steps for Arsany (account); no credentials, no ISMN data in repo
  src/prep.py                    steps below
  src/features.py                the same feature code as the device, kept in sync by a golden-vector test
```

Steps:

1. **Fetch** with pinned version and checksum. Raw data stays out of git (`.gitignore`); only the data cards, scripts and small test fixtures are committed.
2. **Align to the device clock**: resample to a 15-min grid, causally (value at tick = last observation at or before the tick, no interpolation across gaps longer than 1 h; those ticks are masked). Mendeley's 10-min grid is resampled this way; ISMN hourly is kept hourly and flagged.
3. **Relative moisture**: per sector/sensor, map the 2nd and 98th percentile of the training weeks to 0 and 100, then clip. Percentiles come from training weeks only. Store the mapping in the data card. Augment with random dry/wet offsets (3.4).
4. **Events**: build the watering event table (Mendeley's 789 events as ground truth; ISMN rises where flagged). Compute the baseline mean interval from training weeks only.
5. **Features**: the device pipeline of 2.1, implemented once in `features.py` and mirrored in C. A golden-vector test compares both on the same sample sequence (Ines to review).
6. **Labels**: as defined in 2.2 and 2.3, with censoring and masks written as explicit columns.
7. **Faults**: derive from raw layer (flatline/spike/dropout rules in 2.3); inspect 50 random labelled windows by hand and record the count of wrong labels in the data card.
8. **Export**: parquet files per split; class counts and tick counts per split printed in the data card.

## 5. Evaluation split

- **Held-out days, not random rows.** Split by calendar week: every fifth week is test, the week after each test week is validation; the rest is train. Ticks within 3 days (72 h horizon) of a boundary are dropped from the neighbouring set to prevent leakage via the forecast window.
- **Held-out sector.** Second test: train on four sectors, test on the potted-tomato sector (closest to our case) and vice versa. Report both; the potted-tomato number is the one used in the G2/G4 narrative.
- **Held-out stations** for ISMN: whole stations, never mixed.
- **ProjectPlant** and later **our own units**: evaluation only, reported separately.
- Normalisation constants, thresholds and baseline interval come from the training weeks only.
- The test set is opened once per model version, after hyper-parameters are fixed on validation. Metrics stored in `ml/reports/<model>-<version>.json` with the commit id.
- Quantisation check: report float and int8 metrics side by side; accept int8 only if MAE worsens by no more than 0.5 h (A) or recall by no more than 1 point (B).

## 6. Requirement coverage

| ID | How the concept meets it | Evidence planned |
|---|---|---|
| FR-E01 | Model A vs average-interval baseline, MAE <= 12 h up to 72 h on held-out public data | `ml/reports`, test 5.8 |
| FR-E02 | Model B recall targets on held-out data; debounce for <= 1 false alert per week per unit | `ml/reports`, unit test on bench (4.AI3, Arsany) |
| FR-E03 | Fast path (single tick) for wetting, out of soil and fault; relaxed (owner-confirmed) to <= 15 min after the first tick that observes the event, see 2.4 and open item 7. Requirements text to be corrected before v1.0 | firmware test 5.8 with the relaxed wording; latency measured in 4.AI3 |
| FR-E04 | Budgets in 2.2 and 2.3 are estimates; flatbuffer size, arena size and latency measured on the board | size report in CI; bench procedure in `tests/procedures/` for Arsany |
| FR-D02, FR-D04 | Forecast rides on hourly report; results buffered offline | firmware tests |
| FR-D05 | Model delivered as OTA part with rollback | firmware tests |
| FR-A07, UC-08 | App alerts read the critical-event table in 2.4 (confirmed); "water in ~X days" reads Model A | scripted-sequence test per table row; app tests |

## 7. Risks and fallback

| Risk | Signal | Fallback |
|---|---|---|
| Model A does not beat the baseline or misses 12 h MAE because farm data differs from pots | validation MAE above baseline | (1) Closed-form drying-curve extrapolation on the device: fit exponential decay to the last 24 h of `m`, solve for crossing of `T`; no model, near zero flash. (2) Per-plant adaptive interval learned from the unit's own watering history. (3) Cloud-side forecast (Sana) with more data, device sends events only. (4) App shows buckets (< 12 h, 1 d, 2 d, 3 d, > 3 d) if exact hours are too noisy. Report honestly which fallback shipped |
| Model B misses wetting >= 95 % or fault >= 90 % | recall below target on test | Ship the rule detector for faults and wetting (it is deterministic and tiny), keep the model only for fast-drying and waterlogging if it adds value. Tune thresholds on validation, not on test |
| Too many false alerts on our units | more than 1 per week in week 4 | Raise `p_fast` and the debounce of the weak classes (3 of 4),  per-device quiet period after a wetting event |
| Domain gap to real pots and our probe | week-4 check on 3 units deviates | Retrain with own cloud data and ship by OTA (FR-D05); recalibrate dry/wet points |
| ISMN terms turn out to forbid our use, or the account is not available | terms read by the team, or Arsany cannot register | Drop ISMN from training. FR-E targets are defined on "held-out public data", which Mendeley alone provides, so nothing gates on it. Any model already trained on ISMN is withdrawn from demos until re-checked |
| Model trained on ISMN reused commercially | any move from demo to product | Re-check ISMN terms first; fall back to the Mendeley-only variant (3.2 constraint 4) |
| Mendeley licence differs from CC BY 4.0 on the page (grant text quoted by Arsany is consistent with research/demo use, the CC BY line is unread) | licence line read | Stop, raise a Question; do not release until resolved |
| Labels are weak (derived fast-drying, waterlogged, faults) | hand check shows many wrong labels | Report their metrics as "weak-label" only; keep FR-E02 claims to wetting and fault classes |
| Fixed-point mismatch between Python and C features | golden-vector test fails | Port the feature code first, test before training |
| Interpreter flash cost larger than expected | size report | Trim ops, or ask the Architect to widen the budget with evidence |

## 8. Open items and decisions for G2

Owner answers from Arsany's inline comment on PR #4 are recorded below (quotes are as given by him, not verified by the team).

1. **ISMN: answered, may be used for research/demo only.** Arsany: "we can use it, as we are research only, demo products"; terms quoted by him: "The copyright is always with the respective ISMN agency." Constraints in 3.2 apply (no redistribution, no commercial reuse of trained models without re-checking). His only action: register the free account himself. Open follow-up: correct the Requirements text.
2. **Licences: partially verified.** Mendeley grant text quoted by Arsany (3.1); the CC BY 4.0 line itself is still not read from the page, and the ISMN terms page is not read by the team. Someone with unrestricted network access (Lead, CI or Arsany): read the Mendeley licence line and record the ZIP size.
3. Size counting rule: confirmed by Theo in the PR #4 review, written into 2.4; **confirmed by Arsany (ok)**.
4. Dry threshold `T` default (25 relative points) agreed with the care-tips rules (Sana, FR-P02): **confirmed by Arsany (ok)**. Sana to keep app and device aligned.
5. Internal targets (20 % lower MAE than baseline; int8 degradation limits, section 5): **confirmed by Arsany (ok)**.
6. Data for tasks: 4.AI1 uses sections 4 and 5; 4.AI2 uses sections 2 and 7; 4.AI3 and the bench procedure use FR-E03/E04. **Confirmed by Arsany (ok)**.
7. **FR-E03: confirmed.** Arsany answered "yes to both": FR-E03 reads "<= 15 min after the first tick that observes the event", and applies to the fast-path classes (wetting, out of soil, sensor fault) only. The test uses this wording. **Requirements text still needs correction before v1.0.**
8. **Critical-event set, "unexpected wetting" rule and rate limit (one critical wake per class per 6 h): confirmed by Arsany (ok).** [proposed] tags removed in 2.4; the alert names remain Theo's to finalise in the schema.

## 9. A-047 plan (Arsany, 2026-11-08): continue Model B time-boxed, ship the rule detector for alerts

Status: **plan only, no training work started** (Mira, 2026-11-08). Source: Arsany answered A-047 with "approve Theo's recommendation". Reading of the answer:

- **Model B continues, time-boxed, WITHOUT more tuning on this split.** The Mendeley train/val/test split, the A-032 labels, the ignore pad (4), window features, seed 0 as the reported seed and the decision rule (`p_fast` chosen on VAL only) stay as they are in `ml/reports/model-b-wetting-v0.md`. No re-tuning of `p_fast`, the rule threshold, the architecture or the window on val/test to improve the numbers. Steps 1 and 2 change how events are counted and how uncertainty is measured; they do not search for a better model on the same split.
- **The debounced rule detector ships on device for alerts**, labelled **"not FR-E02 compliant"** everywhere it is described (firmware README, PR text, app/alert copy notes, release notes, acceptance matrix row). Reason: the measured model and rule both miss FR-E02 (int8 wetting recall 40 % on TEST at 0.52 false alerts per unit-week; rule 80 % at 25 per unit-week, see `ml/reports/model-b-wetting-v0.md`).
- **Waiver versus a second data source stays a G5 decision for Arsany.** Nothing in this plan marks FR-E02 as met or waived.

The four steps below are independent boxes of **at most 1 working day each**. Order: A first (device value, no dependency), 1 then 2 (data side), 3 needs the bench. A box that hits its stop criterion is closed with the evidence it has; it is not extended without a new answer from Arsany.

### Step A: debounced rule detector on device (alerts), 4.AI3 / 4.F* slice
| Item | Content |
|---|---|
| Goal | Port `features.EventTracker` plus an N-of-M debounce to plain C in `firmware/components/edge_ai/`, emit the wetting alert through the existing critical-event path (2.4, one critical wake per class per 6 h) |
| Fixed before any measurement | Rule = rise >= 8 points within 1 h (concept 2.3 baseline row), debounce **2 of 3** ticks, per-device quiet period after a wetting event as in section 7. These are written down now so they are not tuned on the evaluation split |
| Done when | Host unit tests pass (golden vectors Python vs C, debounce edge cases, quiet period, state kept across deep sleep: counters and last values in RTC/NVS); worst-case alert latency stated in the PR; every user-visible string and doc line carries "not FR-E02 compliant" |
| Latency note | 2-of-3 adds up to 30 min after the first observing tick on top of the hourly report path, so this alert **does not meet FR-E03 either** (<= 15 min); say so in the same label. A single-tick variant would meet FR-E03 but raises false alerts (rule at 8 points per hour: 24.89 per unit-week on TEST) |
| Stop criterion | 1 day. Stop and report if the debounced rule does not fit the 30 KB / 20 KB budget with the model removed, or if the C port cannot reproduce the Python outputs bit-exactly on the golden vectors |
| Evidence that ends the box | Host test output, flash/RAM size line, golden-vector pass, label present in the PR diff. Real alert rate on units is NOT claimed; it comes from the bench in step 3 |

### Step 1: gap-tolerant windows (4.AI2 slice 2)
| Item | Content |
|---|---|
| Goal | Today a window needs 12 consecutive valid samples, so only 15 of 32 (val) and 20 of 40 (test) positives are scorable. Allow short gaps inside a window (a validity flag per tick plus carry-forward of the last valid value, maximum gap length fixed up front, proposed 2 ticks) so more of the real positives are counted |
| Fixed before any measurement | Maximum gap length and fill rule (carry-forward, with the gap flag as an input) written into the report header before running; one setting, no sweep over gap lengths |
| Rule for the metric | Same A-032 mask, via the single helper `ml/src/evaluate.py::wetting_usable`; scorable = usable AND a (gap-tolerant) window exists. Report scorable counts next to the data card counts |
| Stop criterion | 1 day. Stop if scorable positives on VAL + TEST together stay below 50 of 72 (today 35 of 72), because then the interval width does not improve enough to matter |
| Evidence that ends the box | New scorable counts per split, one retrain at the frozen settings, per-class table in the same format as v0 with Wilson intervals. No claim about FR-E02 from this step alone |

### Step 2: pooled event-level cross-validation (4.AI2 slice 3)
| Item | Content |
|---|---|
| Goal | Replace three single-split numbers (15 / 20 positives) by one pooled estimate: leave-segment-out folds (segments, never ticks, never across a sector boundary), all held-out positives pooled across folds, event-level counting (one onset = one event, as `evaluate.wetting_precision_recall`), model and rule at their frozen settings, no per-fold tuning of `p_fast` beyond the VAL rule already in `choose_p_fast` applied to the training part of each fold |
| Report | Pooled wetting recall with Wilson 95 % interval, false alerts per unit-week, the rule curve at equal false-alert rate (the full sweep, as in `rule_sweep.py`), and the 2-of-3 debounced rule from step A replayed offline (replay only, parameters unchanged), **single-tick versus 2-of-3 side by side** (Theo C2): recall (Wilson 95 % interval) and false alerts per unit-week for both, same folds, same events, one table. If 2-of-3 gives **less than a halving** of the false alerts per unit-week, the report says in one sentence that its extra latency (up to 2 ticks late, section 9 Step A) is not buying anything. No tuning of N-of-M on the split. Unit-week is defined below |
| Stop criterion | 1 day. Stop and report if the folds cannot be built with at least 3 held-out segments with positives each |
| Evidence that ends the box (decision rule written now) | (a) Pooled recall at <= 1 false alert per unit-week has an interval whose **upper bound is below 95 %**: FR-E02 is not reachable on this data; stop Model B work on Mendeley, hand the evidence to G5 (waiver or second data source). (b) The interval is too wide to say (width > 25 points): same hand-off, stating that this dataset cannot decide it. (c) Upper bound >= 95 % and lower bound above the rule at equal false-alert rate: record it, continue to step 3, still no tuning. (d) Upper bound >= 95 % but the lower bound is NOT above the rule at equal false-alert rate (Theo C2 gap): outcome is **"undecided -> G5"**; hand the evidence to G5 (waiver or second data source, Arsany) and do not continue to step 3 on the strength of this step. In every case the box closes after this report |

**Unit-week for the Mendeley data (used in Step 2 rule (a) and in every FA/unit-week number).** One unit = one probe series (one plant/sector) at 15-min ticks, so **1 unit-week = 672 scored negative ticks** (`TICKS_PER_WEEK = 672`, `ml/src/train.py:39`; the existing figure is `false_alerts / (negative_ticks / 672)`, `train.py:138`). Conversion: a segment with `n_neg` scorable negative ticks contributes `n_neg / 672` unit-weeks, summed over all held-out segments and folds; only usable (A-032 mask, `evaluate.wetting_usable`) AND scorable ticks count, so gaps, ignore ticks and unscorable windows add no unit-weeks (a segment with a 3-day hole counts 4 days, not 7). The false-alert numerator is **ticks** for the v0 tick-level numbers and **events** (one onset = one alert, refractory as in `evaluate.wetting_precision_recall`) for Step 2; each table says which. The two are not comparable (the 24.89 per unit-week above is tick-level). Caveat: sectors that share weather/irrigation are not independent units; unit-weeks are an exposure measure, not an independent-sample count, so the interval on the false-alert rate is not claimed to be a Wilson-type bound.

### Step 3: real watering recall on bench data (4.AI3, needs Peter / Arsany)
| Item | Content |
|---|---|
| Goal | Labels on the real data are circular (the onset label is itself a rise rule), so recall there measures agreement with the label. The honest number needs real waterings with a hand-kept log (time, amount, probe) on our own units |
| Inputs | A bench procedure and a work order drafted by Mira, checked by Theo, issued by Nora (TEAM.md section 12); firmware from step A on units; at least 3 units, at least 30 logged waterings in total, plus a no-watering period for false alerts (the 48 h x 3 units soak of the acceptance matrix row FR-E02 is the minimum) |
| Stop criterion | 1 day of Mira's analysis once the logs exist; the bench itself is Peter's time box. Stop waiting after 7 days without logs and report the gap to Arsany |
| Evidence that ends the box | Table: logged waterings, alerts raised, matched (tolerance one tick), missed, false alerts per unit-week, with intervals; reported for the rule (step A) and, if it was part of step 2 (c), the model. Statement that the on-chip latency and RAM numbers were taken on the board (or "not run") |

### What this plan does not do
- It does not train anything today and does not change any metric in the v0 report.
- It does not mark FR-E02 as met, waived or accepted. The traceability row says "NOT MET"; the G5 choice between a written waiver and a second data source (ISMN or our own) stays with Arsany and uses the evidence from steps 2 and 3.
- It does not change requirements. Theo (delta review, C1): the acceptance matrix rows FR-E02 and FR-E03 now carry the shipped-alert label (added in this branch, Theo checks the wording); both rows stay NOT MET until G5. Ines carries the same label into the test report.

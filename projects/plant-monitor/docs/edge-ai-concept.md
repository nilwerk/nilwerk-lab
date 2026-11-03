# Edge AI concept and dataset plan (task 2.7)

Author: Mira (Firmware + Edge AI) · Status: draft for G2 review · Date: 2026-11-03
Traces to: Requirements v0.1 section 5 and FR-E01..FR-E04; also FR-D02, FR-D04, FR-D05, FR-A07, UC-08, NFR-01.
Scope approved in Q-16: thirst forecast, watering/rain event detection, sensor-fault detection.

No model has been trained and no dataset has been downloaded for this note. Every number marked **target** is a requirement or a proposal. Every number marked **estimate** is a calculation to be replaced by a measurement in 4.AI2/4.AI3. Nothing here is a result.

## 1. Summary

- Two small int8 TFLite Micro models run every 15 min on the ESP32-C3 with Wi-Fi off:
  **Model A** (thirst forecast, regression) and **Model B** (event and fault classifier).
- Both consume calibrated **relative moisture (0-100 %)** and its slopes, never raw ADC counts. This closes most of the domain gap to public data.
- Training data: Mendeley precision-irrigation dataset (primary), synthetic faults, our own cloud data later. ISMN is research-only per its terms (unverified) and is **not part of the plan**, see 3.2. ProjectPlant is evaluation-only.
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
| Target | MAE <= 12 h overall (FR-E01) **and** MAE below the baseline. Proposed stricter internal target: at least 20 % lower MAE than baseline, so "beats" is not a coin toss |
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

### 2.4 Cross-cutting

- **Critical events** [proposed, for Arsany / G1 to confirm]. A critical event wakes Wi-Fi at once and sends an immediate report (FR-E03, FR-A07). Everything else rides along with the hourly report (FR-D02). When Wi-Fi is down, results are stored with the readings (FR-D04). The set, so that FR-A07 is testable:

  | Model B class | Critical? [proposed] | Condition | Decision path | App alert |
  |---|---|---|---|---|
  | 0 normal | no | n/a | n/a | none |
  | 1 wetting | **only if unexpected**, defined as: `m` after the rise is >= 95, **or** the rise starts while `m` was already >= 80 (watering a wet pot / flood / leak). A normal watering of a dry plant (`m` before < 80 and after < 95) is **not** critical | single tick | `wetting_unexpected` |
  | 1 wetting (normal) | no | any other rise | single tick (still detected at once, to reset "hours since last wetting") | none; shown as "watered" in the next hourly report |
  | 2 drying unusually fast | no | n/a | debounce 2 of 3 | none; hint in care tips |
  | 3 waterlogged | yes | `m` >= 95 for >= 6 h (class 3) | debounce 2 of 3 | `waterlogged` |
  | 4 sensor out of soil | yes | class 4 | single tick | `sensor_out_of_soil` |
  | 5 sensor fault | yes | class 5 (flatline, spike, dropout) | single tick | `sensor_fault` |

  Rate limit [proposed]: at most one critical wake per class per 6 h per unit, so a repeating fault cannot drain the battery (NFR-01); further occurrences go into the hourly report. The alert names above are proposals; Theo defines the final enums in the device report schema. FR-A07 test: feed a scripted `m` sequence per row, assert alert yes/no and alert name. "Unexpected" is thus a numeric condition, not a judgement.
- **FR-E03 latency (worst case, arithmetic).** FR-E03: phone alert <= 15 min after the event. The device only looks every 15 min, so the budget is consumed by the tick spacing alone.
  - Debounce 2 of 3 as first written: event just after tick `k`; first observed at tick `k+1` (<= 15 min); confirmed at `k+2` (<= 30 min); plus connect and send. **Worst case about 30 min + connect. This breaks FR-E03, so the single-tick fast path above is required** for wetting, out of soil and fault. Debounce is kept only for fast drying and waterlogged, which are slow phenomena and are **not** claimed to meet FR-E03 (waterlogged is defined over >= 6 h anyway). To be confirmed by Arsany: FR-E03 applies to the fast-path classes only.
  - Fast path: event just after tick `k` -> observed at tick `k+1`: <= 15 min. Then, per wake, estimates to be measured in 4.AI3: sensor warm-up and samples about 2-3 s, feature and Invoke() a few ms, Wi-Fi association plus TLS plus POST about 3-10 s. **Worst case about 15 min + 5-13 s (estimate).**
  - So **<= 15 min cannot be met literally** if the event starts right after a tick, by those few seconds, with a 15-min cadence. Raised as a Question (open item 7): relax FR-E03 to "<= 15 min after the first tick that observes the event" (equivalent to about 15 min + 15 s), or to "<= 16 min". The alternative, a 10-min tick, costs about 50 % more wake-ups and fails NFR-01 margins; not proposed. Not a silent change: until Arsany answers, the test for FR-E03 uses the strict 15-min limit and is expected to fail by the connect time in the worst case.
  - Note that a wetting ramp may be only partly visible at the first tick; the fast path acts on the first tick where `p >= p_fast`, so the latency is counted from the first tick that shows the rise, and the recall number in 2.3 must be measured for that first tick.
- **Model update** ships as a separate OTA image part with rollback (FR-D05). Model version goes into the report.
- **Size counting rule** (adopted from the Architect's review of PR #4; QA's FR-E04 row uses the same rule):
  - **Flash < 30 KB** = the model flatbuffer (weights + graph), per model. This is what FR-E04 and the OTA model part (FR-D05) measure.
  - **RAM < 20 KB** = the tensor arena **plus** all model-specific persistent buffers the AI path adds: MicroInterpreter instance, input/output buffers, and the feature history ring (96 B + 192 B). RTC-resident history counts too. It does **not** include the general firmware heap (Wi-Fi, BLE, TLS). The budget is per inference path; if A and B share one arena (sequential use), count the larger arena plus both persistent parts, and say so in the size report.
  - **Interpreter and op kernels** (TFLite Micro code) are **counted separately** and reported, not against 30 KB. The size report states firmware image size with and without the AI component so the OTA slot budget (about 1.5 MB per slot) stays honest. Only the ops actually used get registered (`MicroMutableOpResolver`: fully connected, conv2d, mean, softmax, reshape).
  - **< 50 ms** = wall-clock of one `Invoke()` on the real board at 160 MHz, measured, per model.
- **Power**: inference time is small next to sensor warm-up (>= 1.5 s) and the Wi-Fi wake. Current per state is to be stated in 4.AI3's PR; no number is claimed here.

## 3. Datasets

Licence rows say how each licence was checked. The session network blocked `data.mendeley.com`, `ismn.bafg.de` and direct GitHub API access, so two licences could not be read on their own pages.

### 3.1 Mendeley: Soil Moisture, Irrigation Actuator and Weather Dataset (primary)

| Item | Detail |
|---|---|
| Source | https://data.mendeley.com/datasets/c837v6p8ph (version 2: https://data.mendeley.com/datasets/c837v6p8ph/2), DOI 10.17632/c837v6p8ph.2 |
| Licence | **CC BY 4.0 per Requirements v0.1 and per a third-party project citing this DOI. Not verified on the Mendeley page** (host blocked in this session; the search snippet of the page did not show the licence line). **Action: open the page and read the licence line before any download or release.** Attribution is required; cite DOI and authors in the data card |
| Content | IoT farm in Arnesano (Lecce), Apulia, Italy; season Feb-Sep 2025; five sectors, including a potted-tomato sector; three layers (raw, processed, analysis-ready). From the page description: raw layer 486,894 sensor measurements and 3,055,944 valve-state records; processed layer 789 reconstructed irrigation/fertigation events and five per-sector series on a 10-min grid with 33,259 rows each; ERA5 reanalysis weather. Version 2 is dated 2026-09-14 per the search result; pin the version |
| Size | ZIP size **not found** (not shown in search results). Per-sector series are 33,259 rows, so analysis-ready tables are small; the raw valve records are the large part. Check on download; fetch only the layers we need |
| Use | Model A (drying curves, 789 events define the watering interval baseline), Model B (wetting labels; fault labels from raw-layer anomalies; fast-drying and waterlogged derived labels) |
| Risks | (1) Drip-irrigated farm sectors, not houseplants; intervals are short and regular, so the baseline may look strong or weak for the wrong reason. (2) Moisture units and sensor depth not confirmed from the page (unit, depth and calibration to be read from the data description); relative scaling handles offsets, not different physics. (3) One season, one site, so held-out days still share climate; seasonal drift is not tested. (4) Fault labels are derived from raw-vs-processed differences and will be noisy. (5) Valve telemetry is not available on our device; must not leak into features |

### 3.2 ISMN: International Soil Moisture Network (research-only per its terms (unverified); **not used in the plan**)

| Item | Detail |
|---|---|
| Source | https://ismn.bafg.de ; terms at https://ismn.bafg.de/terms-and-conditions |
| Licence | **Treated as research-only and not usable commercially per its terms, which we have not read.** Not an open licence. Not verified on the page itself (host blocked). Note that Requirements v0.1 lists ISMN as an open source ("free account") and does not mention this restriction, so the Requirements text and this finding disagree (Question raised, open item 1). A search summary of the Terms and Conditions page reports: registration required before download, **use restricted to research, commercial use prohibited**, citation of the ISMN papers required. Individual networks may add their own conditions. We cannot claim an open licence for ISMN |
| Content | About 3,000 stations (figure from Requirements v0.1; not re-verified), mostly hourly, soil moisture at several depths, soil temperature, some precipitation |
| Size | Depends on the stations chosen; selection is made in the portal. Plan: 20-40 stations, surface layer (0-5 cm), 2-3 years, expected tens of MB. Not downloaded |
| Use | Drying curves by soil type and rain-driven wetting events for Model A and B (garden/balcony cases). Hourly resolution only, so Model B channels beyond 1 h are used when training on ISMN |
| Risks | (1) **Licence**: a model trained on research-only data and shipped in a commercial-style demo product may breach the terms. Needs a decision (below). (2) Free account must be created by Arsany; agents may not sign up or accept terms (TEAM.md section 5). (3) Volumetric soil moisture of field stations, not pot substrates. (4) Hourly data cannot support 15-min targets. (5) Raw data must not be redistributed or committed |

**Needs Arsany (A-xxx to be created by the Lead):** (a) decide whether ISMN may be used at all, given the research-only wording; (b) if yes, register a free account at ismn.bafg.de, read the terms himself, and tell us whether training a shipped model is allowed. Recommendation: **plan without ISMN**. Use Mendeley, synthetic data and (from week 2) our own cloud data. **Plan without ISMN:** no task, target or schedule in this concept depends on it. At most it is an optional offline experiment that does not gate any FR-E target, and no model whose training set includes it is shipped unless Arsany has read the terms and confirmed in writing that training a shipped model is allowed.

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
  scripts/fetch_ismn.md          manual steps for Arsany (account); no credentials in repo
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
- **Held-out stations** for ISMN, if it is used at all: whole stations, never mixed.
- **ProjectPlant** and later **our own units**: evaluation only, reported separately.
- Normalisation constants, thresholds and baseline interval come from the training weeks only.
- The test set is opened once per model version, after hyper-parameters are fixed on validation. Metrics stored in `ml/reports/<model>-<version>.json` with the commit id.
- Quantisation check: report float and int8 metrics side by side; accept int8 only if MAE worsens by no more than 0.5 h (A) or recall by no more than 1 point (B).

## 6. Requirement coverage

| ID | How the concept meets it | Evidence planned |
|---|---|---|
| FR-E01 | Model A vs average-interval baseline, MAE <= 12 h up to 72 h on held-out public data | `ml/reports`, test 5.8 |
| FR-E02 | Model B recall targets on held-out data; debounce for <= 1 false alert per week per unit | `ml/reports`, unit test on bench (4.AI3, Arsany) |
| FR-E03 | Fast path (single tick) for wetting, out of soil and fault; worst case about 15 min + connect time, see 2.4 and open item 7 | firmware test 5.8 with strict 15-min limit; latency measured in 4.AI3 |
| FR-E04 | Budgets in 2.2 and 2.3 are estimates; flatbuffer size, arena size and latency measured on the board | size report in CI; bench procedure in `tests/procedures/` for Arsany |
| FR-D02, FR-D04 | Forecast rides on hourly report; results buffered offline | firmware tests |
| FR-D05 | Model delivered as OTA part with rollback | firmware tests |
| FR-A07, UC-08 | App alerts read the critical-event table in 2.4 [proposed]; "water in ~X days" reads Model A | scripted-sequence test per table row; app tests |

## 7. Risks and fallback

| Risk | Signal | Fallback |
|---|---|---|
| Model A does not beat the baseline or misses 12 h MAE because farm data differs from pots | validation MAE above baseline | (1) Closed-form drying-curve extrapolation on the device: fit exponential decay to the last 24 h of `m`, solve for crossing of `T`; no model, near zero flash. (2) Per-plant adaptive interval learned from the unit's own watering history. (3) Cloud-side forecast (Sana) with more data, device sends events only. (4) App shows buckets (< 12 h, 1 d, 2 d, 3 d, > 3 d) if exact hours are too noisy. Report honestly which fallback shipped |
| Model B misses wetting >= 95 % or fault >= 90 % | recall below target on test | Ship the rule detector for faults and wetting (it is deterministic and tiny), keep the model only for fast-drying and waterlogging if it adds value. Tune thresholds on validation, not on test |
| Too many false alerts on our units | more than 1 per week in week 4 | Raise `p_fast` and the debounce of the weak classes (3 of 4),  per-device quiet period after a wetting event |
| Domain gap to real pots and our probe | week-4 check on 3 units deviates | Retrain with own cloud data and ship by OTA (FR-D05); recalibrate dry/wet points |
| ISMN not allowed | Arsany decision or terms | Skip it. FR-E targets are defined on "held-out public data", which Mendeley alone provides; say so at G2 |
| Mendeley licence differs from CC BY 4.0 on the page | licence line read | Stop, raise a Question; do not train or ship until resolved |
| Labels are weak (derived fast-drying, waterlogged, faults) | hand check shows many wrong labels | Report their metrics as "weak-label" only; keep FR-E02 claims to wetting and fault classes |
| Fixed-point mismatch between Python and C features | golden-vector test fails | Port the feature code first, test before training |
| Interpreter flash cost larger than expected | size report | Trim ops, or ask the Architect to widen the budget with evidence |

## 8. Open items and decisions for G2

1. **Question for Arsany** (also: Requirements text to be corrected): ISMN is listed as an open source in Requirements v0.1, but its terms are reported (unverified) as research-only, no commercial use. Decide whether ISMN may be used at all and have the Requirements corrected. Recommendation: plan without it (3.2).
2. Someone with unrestricted network access (Lead, CI or Arsany): read the licence line on the Mendeley page and the ISMN terms page, and record the ZIP size. Until then the "CC BY 4.0" in this note is only as good as the Requirements document.
3. Size counting rule: confirmed by Theo in the PR #4 review and written into 2.4. No open question.
4. Confirm the dry threshold `T` default (25 relative points) with the care-tips rules (Sana, FR-P02) so the app and the device agree on "dry".
5. Confirm proposed internal targets: 20 % lower MAE than baseline; int8 degradation limits (section 5).
6. Data for tasks: 4.AI1 uses sections 4 and 5; 4.AI2 uses sections 2 and 7; 4.AI3 and the bench procedure use FR-E03/E04.
7. **Question for Arsany (FR-E03):** with a 15-min wake cadence, a phone alert within 15 min of an event cannot hold literally, because the event can start right after a tick (2.4). Relax FR-E03 to "<= 15 min after the first tick that observes the event" (about 15 min + 15 s), or to "<= 16 min"? And confirm that FR-E03 applies to the fast-path classes (wetting, out of soil, sensor fault), not to waterlogged and fast drying. Recommendation: yes to both.
8. **Arsany / G1:** confirm the critical-event set and the "unexpected wetting" rule in 2.4 (all marked [proposed]), and the one-wake-per-class-per-6-h rate limit.

# Data card: Mendeley Soil Moisture, Irrigation Actuator and Weather Dataset

Status: **downloaded and inspected on 2026-11-06 (A-007 resolved).** Loader: `src/loaders.py`; counts reproduced by
`scripts/run_mendeley.py`; fetch: `scripts/fetch_mendeley.sh`. Training (task 4.AI2, 2026-11-08) is documented in the section "Training and evaluation (4.AI2)" below; all other numbers are data
counts, not results.

| Field | Value |
|---|---|
| Role in project | primary (Model A drying curves, Model B wetting labels) |
| Source URL | https://data.mendeley.com/datasets/c837v6p8ph/2 (version 2) |
| Version / DOI | v2, DOI 10.17632/c837v6p8ph.2, published 2026-09-14 (dataset page JSON-LD `datePublished`) |
| Retrieval date | 2026-11-06 |
| Licence | **verified on the dataset page**: heading "Licence", button text `CC BY 4.0`; page metadata `license.url = http://creativecommons.org/licenses/by/4.0`, `license.text = "CC BY 4.0"`. The ZIP README says "**License:** CC BY 4.0 ... See `LICENSE.txt`" but `LICENSE.txt` is NOT in the 31-file ZIP I downloaded (unverified why; the page line is the authority). Arsany's earlier quote of the Mendeley platform terms (personal, non-exclusive licence) concerns the platform, not this dataset licence: still open for Arsany/legal if redistribution of derived data is planned |
| Allowed use for us | CC BY 4.0 permits use and redistribution with attribution. Attribution required: Adamo, Colizzi, Dimauro, Guerriero, Lomonte (2026), Mendeley Data V2, doi:10.17632/c837v6p8ph.2. The in-ZIP README citation block still reads "[TO BE COMPLETED - authors]" (use the page citation). Still keep raw files out of git (size and our own policy). Legal review of commercial product use not done: unverified |
| Files used | ZIP `c837v6p8ph-2.zip`, 44,483,799 B, SHA-256 `a6043b8e44db7adfdfc5a7f5ff8157a0ed38d29a861a1555dcd73d0cec9853e8` (download URL redirects to `prod-dcd-datasets-cache-zipfiles.s3.eu-west-1.amazonaws.com`; both hosts reachable) |
| Layer used | `02_processed_data/merged/dataset_zone_{1..5}.csv` (10-min grid, raw soil moisture) + `irrigation_events/final_irrigation_events.csv` (read for checks only). NOT the authors' `preprocessed/` layer (their cleaning, interpolation and row-counted 24 h targets) |
| Rows / span / cadence | Grid: 33,259 rows per sector, 2025-02-09 .. 2025-09-27 (local). Probe readings present in 10,100 - 12,166 of those rows per sector (about 30 %; gaps kept as empty cells); dense only Aug-Sep (about 4,000 readings/month vs 100-1,000 in Feb-Jul) |
| Time zone | DATA_DICTIONARY: all timestamps Europe/Rome local naive. Checked on weather: ERA5 radiation and temperature peak at hour 13 local in Jun-Aug, consistent with local time. Probe and valve clocks assumed identical (unverified). Loader converts to UTC |
| Moisture unit, sensor depth | "relative probe output on a 0-100 scale" (DATA_DICTIONARY). Probe model and **depth are not stated anywhere in README or DATA_DICTIONARY: unknown** |
| Site | Arnesano (Lecce), 5 sectors: open-field tomato x2, potted tomato, zucchini, blueberry; sector-to-crop mapping per README (not re-checked here). One season, one site, drip-irrigated farm, not household pots |

## Canonical mapping (loaders.load_mendeley)

| Canonical column | Source column | Note |
|---|---|---|
| plant | `mendeley_s<sector>` | one probe per sector = one "device" |
| time | `ts` | local -> UTC |
| moisture_raw | `soil_moisture` | values outside [0,100] dropped (error codes: negatives down to -50, up to 717), not clipped |
| irrigation | `irrigation_duration_minutes` | reconstructed from valve events (standard irrigation and fertigation). Labelling ground truth only, never a feature |
| rain | `weather_rain` | ERA5 reanalysis, farm-wide mm, not an in-plot gauge: weak |
| temperature | `weather_temp` | ERA5 air temp, only for out-of-soil fault drift |
| source | `mendeley` | |

Quality gate: a sector with more than 50 % exactly-0 valid readings is excluded (dead/saturated probe).

## Counts (real data, `scripts/run_mendeley.py`, seed 0, no synthetic faults)

| Sector | Probe rows | Valid [0,100] | Dropped out-of-scale | Zero share | First (UTC) | Last (UTC) | Valve bins >0 | Rain bins >0 | Status |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 10,743 | 8,159 | 2,584 | 0.01 % | 2025-02-10 13:00 | 2025-09-05 23:40 | 227 | 716 | used (negatives after 5 Sep: probe out of range) |
| 2 | 10,475 | 10,472 | 3 | 0.01 % | 2025-02-10 12:50 | 2025-09-24 14:10 | 346 | 973 | used |
| 3 | 10,100 | 9,930 | 170 | **86.0 %** | 2025-02-10 12:50 | 2025-09-24 14:10 | 89 | 826 | **excluded** (dead probe) |
| 4 | 10,922 | 10,767 | 155 | 0.03 % | 2025-02-10 12:50 | 2025-09-24 14:10 | 636 | 828 | used |
| 5 | 12,166 | 11,860 | 306 | 4.7 % | 2025-02-10 13:00 | 2025-09-24 14:10 | 211 | 1,127 | used, noisy (see hand-check) |

- Rows into the pipeline: 41,258 valid readings, 4 devices, 2025-02-10 12:50 .. 2025-09-24 14:10 UTC.
- 15-min ticks after the global-week split and leakage gap (72 h): train 46,715 / val 8,832 / test 9,311 (masked ticks: 24,609 / 4,147 / 3,646, i.e. gaps > 1 h).
- Events (all splits): watering 219, rain 125, generic wetting 556 (of 900). Per sector (rain/watering/wetting): s1 7/41/100, s2 29/52/80, s4 30/91/133, s5 59/35/243. The authors list 789 valve events (87/195/72/289/146 per sector); our 219 "watering" are those where the rise in the probe coincides with a valve signal.
- Baseline mean watering interval (train, per segment): 12.6 h.
- Model-A labels (train/val/test): feature-valid ticks 8,330 / 1,387 / 2,305; y_mask 7,598 / 2,021 / 2,391; weak labels fast_drying 0 / 49 / 14, waterlogged 0 / 0 / 0. **Train has zero fast-drying positives** (threshold p5 = -17 per 6 h, temp p75 = 20 C from a cold-weather-heavy train set): that weak label cannot be trained on this split as is. Open question for Theo/Lead.
- Dry/wet calibration (2nd/98th percentile of train raw): s1 19..67, s2 15..60, s4 55..99, s5 0..99. Sector 5 range 0..99 means the probe swings across the whole scale.

## 50-window hand-check (label sanity)

File: `mendeley-handcheck-50.csv` (30 event ticks stratified from all 900 events with seed 0 + 20 random quiet ticks). Columns give m now, m 3 h before/after, valve and rain flags. **Method limit:** the verdicts are rule-based triage from the numbers (no plots were looked at); a human eye on plots is still open.

| Result | Count |
|---|---|
| ok (watering with valve within 45 min: 5/5; rain with ERA5 rain: 3/3; quiet window without movement: 12/20) | 20 |
| unexplained wetting (rise >= 10 points in 30 min, no valve and no rain) | 22 (all of the 22 sampled generic wetting events) |
| check (quiet tick but m moves >= 10 points in 3 h, or valve open without event, or m clipped at 0) | 8 |

Reading: labels that carry a valve or rain signal are consistent. **62 % of all events (556/900) are unexplained "wetting"**, concentrated in sector 5 (243 of 337 events), whose probe jumps 30-40 points within an hour without a recorded valve (probe noise, unrecorded irrigation, or rain on an uncovered plot: cause unverified). Do not use generic wetting as ground truth for Model B without a stricter rule or dropping sector 5. Per-sector cleanliness was not measured (50 samples are too few). Rain labels use farm-wide ERA5 and 3 of 3 sampled were coincident, but sample is tiny. Flat low readings (s2 raw 16 for days, s1 raw 23, m 2-9 %) could be real dry soil or a stalled probe: undetectable here; the flatline fault class on real data is not validated.

## Model B event labels after decision A-032 (month x sector)

Decision A-032 (Arsany, approved 2026-11-06), implemented in `src/labels.py::label_wetting_classes` (FR-E02, FR-E01):
- **Wetting positives** = valve-coincident watering + rain-coincident events only. **Generic/unexplained wetting** (no valve, no rain) is an **ignore mask**: neither positive nor negative. Ignore ticks must be dropped from the training loss and from the positive/negative counts of every evaluation metric (only a separate 'unexplained wetting' report may use them); `label_wetting_classes` only sets the columns, consumers select `pos | neg`. The mask covers each generic onset +-4 ticks (+-1 h, `IGNORE_PAD_TICKS = 4`, Lead decision on Theo C1, see sensitivity below).
- **Sector 5 is excluded** from wetting positives and from FR-E02 evidence: all of its ticks are ignore-mask (its 35 watering + 59 rain events are not positives either). Positives are therefore 219 + 125 = 344 minus sector 5's 94 = **250** (184 watering + 66 rain).
- **FR-E02 claims cover wetting + sensor fault only.** Fast-drying and waterlogged stay weak labels, shown in the last two columns and **not** an FR-E02 claim. **No threshold re-tuning** after seeing zero train fast-drying positives: percentile constants are frozen (`FROZEN_WEAK_LABEL_RULE`, guarded by tests).
- Real data, `scripts/run_mendeley.py`, seed 0, no synthetic faults, all splits pooled, months in UTC. Counts are data counts, not results. Ticks are 15-min ticks of the pipeline (masked ticks included).
- Weak labels are not masked by sector: all 49 val fast-drying ticks sit in sector 5 (Aug) and the 14 test ones in sector 4 (Jul); train has 0. Waterlogged is 0 everywhere. Sensor-fault classes have 0 real positives (faults are synthetic only; not injected here).
- **No fast-drying metric may be reported from val:** all 49 val fast-drying ticks lie in excluded sector 5, so they are outside any FR-E02 claim; fast-drying and waterlogged labels stay outside every FR-E02 claim.

Per-split positive counts (real data, seed 0, pad 4; **sector 5: all ticks ignore-mask, no positives**):

| Split | Pos: watering | Pos: rain | Generic wetting events (ignored) | Ignore-mask ticks | Negative ticks |
|---|---|---|---|---|---|
| train | 126 | 52 | 386 | 13,871 | 32,666 |
| val | 24 | 8 | 75 | 2,646 | 6,154 |
| test | 34 | 6 | 95 | 2,817 | 6,454 |
| total | 184 | 66 | 556 | 19,334 | 45,274 |

(Generic events include sector 5's 243; sector 5's explained events are not positives.) Val has only 32 and test 40 positives: any per-split metric is very noisy.

**Ignore-pad sensitivity (Theo C1), `IGNORE_PAD_TICKS` 2 vs 4: decision taken, pad 4.** Contaminated negative = negative tick within 2 h after a generic onset whose m is still >= 10 points above the pre-onset value (m two ticks before the onset); this is my own proxy, not ground truth. Pad 2: 46,526 negatives, 1,174 contaminated (2.52 %). Pad 4: 45,274 negatives, 681 contaminated (1.50 %). Pad 4 costs 1,252 negatives (2.7 %) and removes 493 contaminated ones. The Lead chose 4 because the contamination drop outweighs the small loss of negatives; all tables in this section and the counts above are regenerated at pad 4 (`scripts/run_mendeley.py`).

| Month | Sector | Ticks | Pos: watering (valve) | Pos: rain | Generic wetting events | Ignore-mask ticks | Negative ticks | Weak fast-drying | Weak waterlogged |
|---|---|---|---|---|---|---|---|---|---|
| 2025-02 | s1 | 1772 | 0 | 1 | 4 | 36 | 1735 | 0 | 0 |
| 2025-02 | s2 | 1772 | 6 | 7 | 12 | 108 | 1651 | 0 | 0 |
| 2025-02 | s4 | 1772 | 0 | 1 | 2 | 18 | 1753 | 0 | 0 |
| 2025-02 | s5 | 1772 | 0 | 0 | 1 | 1772 | 0 | 0 | 0 |
| 2025-03 | s1 | 2112 | 1 | 3 | 4 | 36 | 2072 | 0 | 0 |
| 2025-03 | s2 | 2112 | 11 | 12 | 15 | 135 | 1954 | 0 | 0 |
| 2025-03 | s4 | 2112 | 2 | 3 | 2 | 18 | 2089 | 0 | 0 |
| 2025-03 | s5 | 2112 | 0 | 0 | 35 | 2112 | 0 | 0 | 0 |
| 2025-04 | s1 | 2016 | 1 | 1 | 6 | 54 | 1960 | 0 | 0 |
| 2025-04 | s2 | 2016 | 13 | 4 | 17 | 153 | 1846 | 0 | 0 |
| 2025-04 | s4 | 2016 | 5 | 4 | 12 | 108 | 1899 | 0 | 0 |
| 2025-04 | s5 | 2016 | 0 | 0 | 14 | 2016 | 0 | 0 | 0 |
| 2025-05 | s1 | 2208 | 9 | 2 | 15 | 135 | 2062 | 0 | 0 |
| 2025-05 | s2 | 2208 | 10 | 6 | 22 | 198 | 1994 | 0 | 0 |
| 2025-05 | s4 | 2208 | 4 | 0 | 9 | 81 | 2123 | 0 | 0 |
| 2025-05 | s5 | 2208 | 0 | 0 | 24 | 2208 | 0 | 0 | 0 |
| 2025-06 | s1 | 2208 | 21 | 0 | 50 | 450 | 1737 | 0 | 0 |
| 2025-06 | s2 | 2208 | 12 | 0 | 5 | 45 | 2151 | 0 | 0 |
| 2025-06 | s4 | 2208 | 35 | 1 | 22 | 198 | 1974 | 0 | 0 |
| 2025-06 | s5 | 2208 | 0 | 0 | 21 | 2208 | 0 | 0 | 0 |
| 2025-07 | s1 | 2400 | 9 | 0 | 21 | 189 | 2202 | 0 | 0 |
| 2025-07 | s2 | 2400 | 0 | 0 | 6 | 54 | 2346 | 0 | 0 |
| 2025-07 | s4 | 2400 | 31 | 3 | 41 | 369 | 1997 | 14 | 0 |
| 2025-07 | s5 | 2400 | 0 | 0 | 72 | 2400 | 0 | 0 | 0 |
| 2025-08 | s1 | 2112 | 0 | 0 | 0 | 0 | 2112 | 0 | 0 |
| 2025-08 | s2 | 2112 | 0 | 0 | 3 | 27 | 2085 | 0 | 0 |
| 2025-08 | s4 | 2112 | 14 | 15 | 40 | 360 | 1723 | 0 | 0 |
| 2025-08 | s5 | 2112 | 0 | 0 | 73 | 2112 | 0 | 49 | 0 |
| 2025-09 | s1 | 479 | 0 | 0 | 0 | 0 | 479 | 0 | 0 |
| 2025-09 | s2 | 1689 | 0 | 0 | 0 | 0 | 1689 | 0 | 0 |
| 2025-09 | s4 | 1689 | 0 | 3 | 5 | 45 | 1641 | 0 | 0 |
| 2025-09 | s5 | 1689 | 0 | 0 | 3 | 1689 | 0 | 0 | 0 |
| **Total** | s1,s2,s4,s5 | **64858** | **184** | **66** | **556** | **19334** | **45274** | **63** | **0** |

## Training and evaluation (4.AI2, 2026-11-08)

Code: `src/train.py`, `scripts/train_all.py <raw_dir> <out_dir>` (needs `requirements-train.txt`: TensorFlow 2.21 CPU). Outputs committed: `reports/model-b-wetting-v0.md|json`, `models/model_b_wetting_int8.tflite`, `reports/size_report.json`. Re-run on the same ZIP (checksum above) reproduces the .tflite byte for byte (compared on two runs). Real rows only (`inject=False`): no synthetic data in any metric. Report header carries the commit of the code.

How this dataset is used, and what limits it:
- **Model B wetting (2 classes: normal / wetting).** Positives and ignore mask exactly per A-032 (pad 4, sector 5 ignored). Input = last 8 ticks (2 h) of moisture differences plus `m_now` and slope: 18 int8 values; valve, rain and weather columns are never inputs. Splits and calibration as in `prep.preprocess`; `p_fast` chosen on val only.
- **Scorable positives:** of 32 val / 40 test positives only **15 / 20** have 12 consecutive valid samples before them (probe gaps; train 68 of 178). The other positives are in no metric. Window 8 instead of concept 24 ticks: a 28-tick context would keep only 11 / 12.
- **Result (seed 0, float, TEST):** wetting recall 35 % (95 % interval 18-57 %), precision 100 % (7 of 7 alerts), 0 false alerts per unit-week; VAL recall 27 %, precision 67 %. Rule baseline (8 pts/h): TEST recall 80 %, precision 14 %, 25 false alerts per unit-week. Over 5 seeds TEST recall is 10-45 %. **FR-E02 (recall >= 95 %, <= 1 false alert per unit-week) is not met.** Full per-class tables: `reports/model-b-wetting-v0.md`.
- **Labels are circular:** the onset label is a rise rule (>= 10 points / 2 ticks), so recall is agreement with that label, not proof of detecting watering.
- **Model A:** only the average-interval baseline is evaluated. Uncensored metric ticks are 3-11 % of ticks (train 1,280, val 748 of 8,832, test 1,000 of 9,311); labels sit almost entirely in 0-12 h (val 744, test 899; 48-72 h: 0 and 0), median label 0 h, and the "always predict the median" reference beats the baseline on val (0.53 h vs 3.46 h MAE). This site (drip irrigation every ~12 h) has almost no 24-72 h dry-downs, so **FR-E01 cannot be assessed on this dataset**; it needs a pot-like source (ISMN is research/demo only) or our own units.
- **Not trained / not claimed:** sensor fault and out-of-soil (no real positives), fast drying, waterlogged (weak labels; 0 train positives; percentile constants stay frozen).
- **Size (FR-E04):** int8 flatbuffer 3,664 B of 30 KB (measured on host); RAM estimate 334 B (activation tensors 46 B + feature ring 288 B) of 20 KB, an estimate: interpreter overhead and latency on the ESP32-C3 are not run (4.AI3).

## Credits (CC BY 4.0 attribution, review C5)
The int8 model `ml/models/` (4.AI2) is trained on this dataset. Any app, documentation or release credits list that ships it must carry: "Soil Moisture, Irrigation Actuator and Weather Dataset" by Adamo, Colizzi, Dimauro, Guerriero, Lomonte et al. (2026), Mendeley Data V2, doi:10.17632/c837v6p8ph.2, licensed CC BY 4.0 (http://creativecommons.org/licenses/by/4.0). Models trained on it were changed from the original (windowed, labelled, quantised): state that. Open for the Lead: put this line into the app/docs credits list. The legal review of commercial use is still not done (unverified).

## Known risks
- Drip-irrigated farm, not pots; one season, one site; probe depth unknown; valve telemetry must never be a feature; fault labels are derived and noisy; recording is dense only in Aug-Sep so train/val/test are mostly late-summer vs spring-sparse; ERA5 rain/temperature are site-wide proxies.
- Time zone of probe/valve clocks assumed equal to the weather clock.

## Re-download
`scripts/fetch_mendeley.sh` (curl the ZIP, verify SHA-256, unzip without the two 396 MB raw valve files). Raw files live in `ml/data/raw/` (gitignored via `ml/.gitignore` `data/`), not committed.

Checksums of the files the loader reads (SHA-256):
```
994ae706bf45d83bccfbc77c97977bccf44f7bef939d468d9c1458c680ed2bd3  merged/dataset_zone_1.csv
28cb63167aa3648a8b360fe33c8bcf2d54e42b33454557b4cb47ead541d0c4e5  merged/dataset_zone_2.csv
a8d198e01256660f8b43603d2df829382345c640a1d1da497f638a232c612372  merged/dataset_zone_3.csv
503952454fec2358eb99470ea74e3d7971ddb5d047b6257dbb16f96ad3d41cae  merged/dataset_zone_4.csv
c632e23027bee549e55b84d326cd27577ab92b0cf6265f3dfb5549f225e2c37c  merged/dataset_zone_5.csv
d178704cb38ea086e41dc1091c4bb87846bb316efa66ace70d35f5619a2a4381  irrigation_events/final_irrigation_events.csv
```

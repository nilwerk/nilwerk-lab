# Data card: Mendeley Soil Moisture, Irrigation Actuator and Weather Dataset

Status: **downloaded and inspected on 2026-11-06 (A-007 resolved).** Loader: `src/loaders.py`; counts reproduced by
`scripts/run_mendeley.py`; fetch: `scripts/fetch_mendeley.sh`. No model has been trained; all numbers below are data
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

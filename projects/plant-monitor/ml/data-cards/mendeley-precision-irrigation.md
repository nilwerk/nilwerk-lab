# Data card: Mendeley Soil Moisture, Irrigation Actuator and Weather Dataset

Status: **not downloaded; nothing here has been verified against the files.**

| Field | Value |
|---|---|
| Role in project | primary (Model A drying curves, Model B wetting labels) |
| Source URL | https://data.mendeley.com/datasets/c837v6p8ph/2 (version 2) |
| Version / DOI | v2, DOI 10.17632/c837v6p8ph.2 (v2 date 2026-09-14 per a search result: unverified) |
| Retrieval date | not retrieved |
| Licence line | CC BY 4.0 per Requirements v0.1 and a third-party citation: **unverified**, line not read from the page. Arsany quoted the Mendeley terms-of-use grant ("non-exclusive, personal, non-transferable license ...") in PR #4: quoted, not verified by the team |
| Allowed use for us | research and demo (owner reading); attribution with DOI and authors if CC BY 4.0 holds. Re-check before any release |
| Redistribution | treat as not allowed until the licence line is read; raw files stay out of git |
| Files and SHA-256 | to fill in after download (`sha256sum *`) |
| Rows / span / cadence | per page description (unverified): Arnesano (Lecce), Feb-Sep 2025, five sectors, 10-min grid, 33,259 rows per sector series, 789 irrigation events, ERA5 weather |
| Moisture unit, sensor depth | unknown, read from the dataset description |
| Mapping to canonical frame | to write after the files are inspected |
| Known risks | drip-irrigated farm, not pots; one season, one site; valve telemetry must never be a feature; fault labels are derived and noisy |

## Download steps (Arsany or Peter, normal internet access)

1. Open https://data.mendeley.com/datasets/c837v6p8ph/2 in a browser.
2. Read the licence line on the page (near "Licence" / "Data Files") and write the exact text into the Licence row above. If it is not CC BY 4.0, stop and tell Nora (raise a Question).
3. Use "Download All" (ZIP). Note the ZIP size in the card. If it is very large, download only the analysis-ready layer and the irrigation-event table.
4. Create the directory `projects/plant-monitor/ml/data/mendeley/` (it is gitignored) and unzip there.
5. In that directory run `sha256sum $(find . -type f) > SHA256SUMS.txt` and paste the file list, sizes and hashes into this card.
6. Open the data description file in the ZIP and write moisture unit, sensor depth and column names into this card.
7. Hand the card back (PR or issue comment). Do not commit anything under `data/`.

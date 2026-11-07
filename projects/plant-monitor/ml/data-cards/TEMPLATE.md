# Data card: <dataset name>

| Field | Value |
|---|---|
| Role in project | primary / secondary / evaluation only |
| Source URL | |
| Version / DOI | (pin it) |
| Retrieval date | YYYY-MM-DD |
| Retrieved by | name (not an agent unless it ran the fetch itself) |
| Licence line | exact text |
| How the licence was verified | read on the page (URL + date) / quoted by <person> / **unverified** |
| Allowed use for us | |
| Redistribution | allowed / forbidden |
| Files and SHA-256 | file, bytes, sha256 |
| Rows / span / cadence | |
| Moisture unit, sensor depth, soil type | (from the data description) |
| Mapping to canonical frame | plant / time / moisture_raw / irrigation / rain columns |
| Dry/wet mapping | 2nd / 98th percentile of training weeks per plant, values stored in `_calibration` output |
| Split | counts from `prep.split_counts` |
| Hand check of 50 labelled windows | wrong labels: n / 50 (concept section 4 step 7) |
| Known issues | |
| Citation | |

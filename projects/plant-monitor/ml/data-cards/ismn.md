# Data card: ISMN (International Soil Moisture Network)

Status: **not downloaded. Research and demo use only (owner decision, Arsany, PR #4).**

| Field | Value |
|---|---|
| Role in project | secondary (garden/balcony drying curves and rain wetting); never gates a FR-E target |
| Source URL | https://ismn.bafg.de ; terms: https://ismn.bafg.de/terms-and-conditions |
| Version / DOI | none; record station list and download date |
| Licence line | not an open licence. Search summary (unverified): registration required, research use only, commercial use prohibited, citation of the ISMN papers required, networks may add conditions. Arsany quoted: "The copyright is always with the respective ISMN agency." |
| How verified | **unverified**: terms page not read by the team |
| Allowed use for us | research and demo only. No commercial reuse of any model trained on it without re-checking the terms; label such models "trained with ISMN data" |
| Redistribution | **forbidden.** No ISMN data, extracts, fixtures or plots of raw series in the repo, a PR, a demo package or a Drive folder shared with customers. Only this card and the steps are committed |
| Cadence | mostly hourly; keep hourly and flag it, do not pretend 15-min |
| Known risks | field stations, not pots; hourly cannot support 15-min targets |

## Download steps (Arsany only: agents and Peter do not register or accept terms)

1. Register the free account at https://ismn.bafg.de yourself and read the Terms and Conditions; write the key restrictions into the Licence rows above.
2. In the data portal pick 20 to 40 stations, surface layer (0 to 5 cm), 2 to 3 years, soil moisture (plus precipitation if offered). Prefer whole stations; they are split by station, never mixed across train and test.
3. Download as the portal offers (CSV or STM format). Save the station list.
4. Put the files in `projects/plant-monitor/ml/data/ismn/` (gitignored) on your machine or on private CI storage outside the repo.
5. Run `sha256sum` on the files and fill in the card. Cite the ISMN papers and data agencies as the terms require.

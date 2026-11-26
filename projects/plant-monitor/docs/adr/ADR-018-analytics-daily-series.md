# ADR-018: Per-plant daily series in GET /analytics (4.B4b)

Status: Proposed (contract only; nothing is built) · Date: 2026-11-24 · Deciders: Arsany (owner; decision A-131, approved 2026-11-24); Theo (architect, contract) · Amends: `docs/interfaces/openapi.yaml` (`/analytics`, one new optional field marked `[proposed, 4.B4b: not built yet]`). No migration, no database change.

## Context
FR-P01 asks for 30/90-day history with trends, watering events and a comparison. The 4.B4 contract (`/analytics`, built in 4.B4 slice 2) returns only aggregates per plant: `reading_count`, `soil_pct` and `battery_mv` as mean/min/max, `watering_events` and the first-week/last-week `trend`. The app screen (4.A6) therefore draws a range bar and a two-bar graph; it cannot draw the 30/90-day line chart, because no value per day exists in the response (`docs/traceability.md`, FR-P01 row for 4.A6). Owner decision A-131 approved adding a daily series.

## Decision
1. **Add `daily` to each item of `plants` in the 200 response of GET `/analytics`.** It is an array with one item per calendar day of the window.
2. **Item shape** (JSON, snake_case like the rest of the endpoint):

   | field | type | meaning |
   |---|---|---|
   | `date` | string, `YYYY-MM-DD` | The calendar day, in **UTC**. No existing rule sets another zone: `readings.ts` is stored as `timestamptz` and the window maths in `cloud/analytics/aggregate.ts` is UTC milliseconds. The plant owner's local zone is not stored anywhere, so it is not used. **[proposed, A-140]** UTC days are awaiting the owner's confirmation. |
   | `soil_pct_mean` | number or null | Mean of `moisture_pct` of the plausible readings of that plant on that day. `null` when the day has no plausible reading with a soil value. |
   | `battery_mv_mean` | number or null | Mean of `vbat_mv`, same rule. |
   | `reading_count` | integer >= 0 | Plausible readings of that plant on that day (same rule as the existing `reading_count`). 0 for an empty day. |

3. **Days covered.** The window of N days (30 or 90) is the N UTC calendar dates ending with today (UTC), oldest first. Today is partial. Every one of these days lies inside the existing rolling window (`now - N days` to `now`), so the series reads no row the aggregates do not already read. The array has exactly N items, so at most 90. **Empty days are included** (both means null, `reading_count` 0), so the chart can show gaps and the client never has to infer missing dates.
4. **Same filters as the aggregates:** only `plausible` rows, only the plant's own rows, same window. The per-day `reading_count` values add up to the plant's `reading_count` except for readings in the part of the first rolling-window day before the first listed date (see open point 1). **[proposed, A-140]** This "counts may not add up" rule is awaiting the owner's confirmation.
5. **Additive, not breaking.** `daily` is a new optional property; existing clients ignore unknown fields. It is not added to `required` until it is built (4.B4b part 2), so the built-status checks of `cloud/test/openapi_check.py` stay valid. Once built, the field becomes `required` in a follow-up contract edit in the same PR as the code (playbook rule 4).
6. **Gate unchanged.** Premium only (FR-P04, ADR-008): `public.is_premium()` is called as the user first and a free user gets 403 `premium_required` before any reading is read. Own rows only (NFR-06): every query runs as the user under RLS (`owner_id = auth.uid()`). No parameter can name another user or plant.

## Requirements served
FR-P01 (the 30/90-day line chart needs one value per day), FR-P04 (premium gate unchanged, still before any read), NFR-06 (own rows only, RLS as the user). Owner decision A-131.

## Size and cost
- **Rows read stay the same.** The handler already pages all of the user's readings in the window under RLS; the series is computed from those rows in memory. No new query, no new index, no migration.
- **Response grows by at most 90 items x 4 values per plant** (date string, two means, one count). With the 30/90 choice per request, one plant adds at most about 90 x ~75 bytes, roughly 7 KB of JSON before compression. For a household with a handful of plants this is tens of KB. Supabase edge-function and egress free-tier limits are not materially affected; no new pay-per-use item is introduced (playbook rule 9). The `/analytics` response stays `Cache-Control: no-store`.
- CPU: one pass over the already loaded samples to bucket them by UTC date, O(rows). The size of the loaded row set (about 4 per hour per plant at the default 15 min sample and 1 h report interval, so up to a few thousand rows per plant for 90 days) is not changed by this ADR.

## Privacy and RLS
No new data is exposed: the means and counts are derived from rows the caller already owns and may already read through the aggregates. No raw reading, device id or other user's value is added. RLS is the only read path and is unchanged; the premium gate runs before it. A free or foreign token receives the same errors as today (403, 401).

## Alternatives rejected
- **Server-side chart image:** rejected. It fixes the look in the server, cannot follow the app theme (ADR-014 palette, dark mode), cannot be made accessible (no values for a screen reader or a value label), and moves rendering cost to an edge function. FR-P01 asks for data, not a picture.
- **Raw readings to the client:** rejected. Up to a few thousand rows per plant per request is a much larger payload than 90 items, the client would have to repeat the plausibility filter and the day bucketing (a second copy of a rule, playbook rule 2), and it widens what a premium client downloads without a requirement for it.
- **Client-side bucketing of a hourly series:** same problem as raw readings, rejected.

## Consequences
- **The client must treat `null` as a gap**, not as 0. A day with `reading_count` 0 draws no point and breaks the line; it is not "dry" and not "empty battery". The app model (`analyticsModel.ts`) must validate the array (length equals `window_days`, dates ascending and consecutive, counts non-negative) and reject a malformed series as it does other contract violations.
- **Absent versus malformed (architect rule, amended 2026-11-26 with the 4.A6b fix round).** A response with no `daily` key on a plant (an older backend, or a rolled-back function) is not a contract violation for the client's other data: the plant's aggregates are shown, and the chart is replaced by a "not available yet" notice. A `daily` value that is present but malformed (not an array, wrong length, non-consecutive dates, a bad value) still rejects the whole response, as above. The server contract is unchanged: `daily` stays in `required` for the built endpoint, so a missing key is a deploy or version fault to fix on the server, not something the client should rely on.
- A day with readings but no soil value (sensor fault) has `reading_count` > 0 and `soil_pct_mean` null. The chart shows a gap for soil on that day.
- Today's point is a partial day and can move between requests. The client may mark it.
- Display in the owner's local time is the client's concern; the series is UTC. Near midnight the local day and the UTC day differ (see open point 2).
- Traceability: `docs/traceability.md` carries a row for FR-P01 / FR-P04 at status "contract proposed".
- Nothing here is built, deployed or tested. The live `analytics` function does not return `daily` until 4.B4b part 2 is merged and deployed.

## Checker gap
The openapi checker (`cloud/test/openapi_check.py`) does not guard the proposed marker or the `daily` item shape today. Part 2 must add those checks (test 18).

## Open points
Both points below are open as owner decision A-140 (recommendation: accept both). A-131 itself, adding the daily series, is approved.

1. **Row of the first day.** The rolling window starts at `now - N days`, so the aggregates include readings from the part of the day before the first listed date; the series does not list that day. The sum of daily counts can therefore be smaller than `reading_count`. The alternative (aligning the aggregates to calendar days) would change decided 4.B4 behaviour and is not proposed. Recommendation: accept, and do not assert equality in tests.
2. **Local-time days.** UTC buckets split a Berlin evening watering across two dates around 00:00 UTC (01:00 or 02:00 local). Recommendation: UTC for v1; a later optional `tz` query parameter would be a new contract change with its own ADR (no requirement asks for it now).
3. **Unit of the means.** `soil_pct_mean` is relative 0-100 as in `readings.moisture_pct`; no new unit.

## Implementation notes for Sana (4.B4b part 2; no code in this ADR)
- **Where.** A pure function next to `cloud/analytics/aggregate.ts`, for example `dailySeries(samples, nowMs, windowDays)`; no database, network or clock (`nowMs` is passed in, as in `aggregatePlant`). Reuse `samplesInWindow` so the plausible and window filters exist once. `aggregatePlant` adds `daily` to `PlantAnalytics`; `handleAnalytics` maps it to snake_case in `_shared/analytics.ts` (`readingFromRow` is unchanged).
- **Day rule.** Bucket by the UTC date of the reading time; build the list of N dates from `nowMs` backwards by whole UTC days; fill empty days; means are `null` when no value, never 0 or NaN.
- **Gate stays first.** `public.is_premium()` is still called before any read; the series is computed only after the gate and only from rows read under RLS as the user. Do not add a second read path.
- **Fixtures.** Hand-computed in the test file (playbook rule 16): write the expected dates and means by hand from a few readings; never derive them by calling the function under test. Choose a fixed `nowMs` (for example 2026-11-24T10:00:00Z) so the date list is a literal.
- **Tests (minimum list).**
  1. Length equals the window (30 and 90), dates ascending, consecutive, last date is the UTC date of `nowMs`.
  2. Two readings on one day: hand-computed soil and battery means and count.
  3. A day with no readings: both means `null`, count 0, item still present.
  4. Day with readings but all soil values null: soil mean null, battery mean set, count > 0.
  5. Implausible rows and other plants' rows are excluded.
  6. UTC boundary: a reading at 23:59:59Z and one at 00:00:00Z fall on different dates.
  7. A reading older than the window or after `nowMs` is not in any item.
  8. Plant with no readings: N items, all null, all 0.
  9. Handler: free user gets 403 and the fake reads are not called (existing gate test extended); 200 response contains `daily` in snake_case; cross-user isolation fixture shows no other user's day values.
  10. Rounding: means are not rounded by the function; the expected value is hand-written (for example soil 40 and 41 gives 40.5) and compared exactly or with a stated tolerance.
  11. 0 versus null: a day whose soil readings are all 0 has `soil_pct_mean` 0, not null; an empty day has null and count 0.
  12. Rows between the rolling window start (`now - N days`) and the first listed date: they count in `reading_count` but in no daily item (open point 1).
  13. `nowMs` exactly at 00:00:00.000Z: today is that date with a single-instant day; a row exactly at `nowMs` is included; a row 1 ms later is not.
  14. Month, year and leap-day boundaries: a window crossing 28/29 Feb (leap year 2028 and a non-leap year), 31 Dec to 1 Jan and a 30/31-day month end lists the correct consecutive dates.
  15. A 90-day window with more than 1000 rows (3 or more pages) gives the same day values as the same rows in one page.
  16. A row with null `plantId` or an unparseable `ts` is in no item.
  17. App side: `analyticsModel.ts` validation (length equals `window_days`, ascending consecutive dates, counts non-negative, null kept as null) accepts a good series and rejects each malformed one.
  18. `cloud/test/openapi_check.py` (part 2 must add this): the checker today does NOT guard the `daily` marker or the item shape; it only checks the built marker and the required plant fields. Part 2 changes the marker to built, adds `daily` to `required`, checks the four item fields are produced in the code and that the array has at most 90 items.
- Update the contract text in the same PR for any edge case found (playbook rule 4), and move the traceability row to its built status.

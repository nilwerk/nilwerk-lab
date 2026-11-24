// Tests for the per-plant daily series (task 4.B4b part 2, ADR-018; FR-P01 line chart, FR-P04, NFR-06; owner decision A-131).
// Run: node --experimental-strip-types --test cloud/analytics/test/daily.test.ts   (no DB, no network)
// Every expected value is written by hand from the fixture below, with the arithmetic in the comment. The function under test is never used
// to build an expectation (not even the date list: the 30 dates are a literal, the 90 are checked with Date.UTC arithmetic).
import { test } from "node:test";
import assert from "node:assert/strict";
import { aggregatePlant, dailySeriesForPlant, type AnalyticsReading, type DailyPoint } from "../aggregate.ts";

const NOW_MS = Date.parse("2026-11-24T10:00:00Z");
// 30-day window = the 30 UTC dates 2026-10-26 .. 2026-11-24 (Oct 26-31 = 6 dates, Nov 1-24 = 24 dates). Rolling window start: 2026-10-25T10:00Z.
// 90-day window = 90 UTC dates 2026-08-27 .. 2026-11-24 (Aug 27-31 = 5, Sep = 30, Oct = 31, Nov 1-24 = 24; 5+30+31+24 = 90). Rolling start: 2026-08-26T10:00Z.
const DATES_30 = [
  "2026-10-26", "2026-10-27", "2026-10-28", "2026-10-29", "2026-10-30", "2026-10-31",
  "2026-11-01", "2026-11-02", "2026-11-03", "2026-11-04", "2026-11-05", "2026-11-06", "2026-11-07", "2026-11-08", "2026-11-09", "2026-11-10",
  "2026-11-11", "2026-11-12", "2026-11-13", "2026-11-14", "2026-11-15", "2026-11-16", "2026-11-17", "2026-11-18", "2026-11-19", "2026-11-20",
  "2026-11-21", "2026-11-22", "2026-11-23", "2026-11-24",
];

const r = (plantId: string | null, ts: string, moisturePct: number | null, vbatMv: number | null, plausible = true): AnalyticsReading =>
  ({ plantId, ts, moisturePct, vbatMv, plausible });

const EMPTY: Omit<DailyPoint, "date"> = { soilPctMean: null, batteryMvMean: null, readingCount: 0 };

// Plant "a". Days that have readings (all other days are empty):
const A: AnalyticsReading[] = [
  r("a", "2026-10-25T09:00:00Z", 77, 3777),  // before the rolling window start (10:00): in no item, in no aggregate
  r("a", "2026-10-25T15:00:00Z", 99, 3999),  // inside the rolling window but before the first listed date (Oct 26): in the aggregates, in no 30-day item
  r("a", "2026-10-26T00:00:00Z", 10, 4000),  // FIRST day of the 30-day window, 00:00:00 sharp
  r("a", "2026-10-26T23:00:00Z", 20, 3990),
  r("a", "2026-11-17T06:00:00Z", 40, 3900),  // soil 40, battery 3900
  r("a", "2026-11-17T18:00:00Z", null, 3800),// no soil value: the soil mean is over ONE value (40), not (40 + 0) / 2
  r("a", "2026-11-18T01:00:00Z", 10, 3000),
  r("a", "2026-11-18T02:00:00Z", 20, 3000),
  r("a", "2026-11-18T03:00:00Z", 25, 3000),
  r("a", "2026-11-19T23:59:59Z", 30, 3500),  // UTC midnight boundary, last second of Nov 19
  r("a", "2026-11-20T00:00:00Z", 70, 3400),  // first second of Nov 20
  r("a", "2026-11-20T12:00:00Z", 80, 3300),
  r("a", "2026-11-22T12:00:00Z", null, 3700),// battery-only day
  r("a", "2026-11-22T13:00:00Z", null, 3600),
  r("a", "2026-11-24T07:00:00Z", 0, 1, false),   // implausible: excluded
  r("b", "2026-11-24T07:30:00Z", 100, 4200),     // another plant: excluded
  r(null, "2026-11-24T07:45:00Z", 100, 4200),    // no plant: excluded
  r("a", "2026-11-24T08:00:00Z", 40, 3900),
  r("a", "2026-11-24T09:30:00Z", 50, 3880),
  r("a", "2026-11-24T10:00:00Z", 60, 3860),      // exactly nowMs: included (the window is inclusive at the end, like the aggregates)
  r("a", "2026-11-24T10:00:01Z", 99, 1),         // one second in the future: excluded
  r("a", "not-a-date", 99, 1),                   // unparseable time: dropped
];

const day = (daily: DailyPoint[], date: string) => daily.find((d) => d.date === date);

test("1: 30-day window has exactly 30 items, dates ascending and consecutive, the last one is the UTC date of nowMs", () => {
  const d = dailySeriesForPlant(A, "a", NOW_MS, 30);
  assert.equal(d.length, 30);
  assert.deepEqual(d.map((x) => x.date), DATES_30);
  assert.equal(d[d.length - 1].date, "2026-11-24");
  assert.deepEqual(Object.keys(d[0]).sort(), ["batteryMvMean", "date", "readingCount", "soilPctMean"]);
});

test("2: a day with readings: Nov 24 (today, partial) = 40, 50, 60 -> soil (40+50+60)/3 = 50, battery (3900+3880+3860)/3 = 11640/3 = 3880, count 3", () => {
  // 07:00 implausible, 07:30 plant b, 07:45 no plant, 10:00:01 future: none of them counts.
  assert.deepEqual(day(dailySeriesForPlant(A, "a", NOW_MS, 30), "2026-11-24"),
    { date: "2026-11-24", soilPctMean: 50, batteryMvMean: 3880, readingCount: 3 });
});

test("2b: soil mean is over the soil values only: Nov 17 = (40, null) -> soil 40 (not 20), battery (3900+3800)/2 = 3850, count 2", () => {
  assert.deepEqual(day(dailySeriesForPlant(A, "a", NOW_MS, 30), "2026-11-17"),
    { date: "2026-11-17", soilPctMean: 40, batteryMvMean: 3850, readingCount: 2 });
});

test("2c: non-integer mean: Nov 18 = 10, 20, 25 -> soil 55/3, battery (3000 x 3)/3 = 3000, count 3", () => {
  assert.deepEqual(day(dailySeriesForPlant(A, "a", NOW_MS, 30), "2026-11-18"),
    { date: "2026-11-18", soilPctMean: 55 / 3, batteryMvMean: 3000, readingCount: 3 });
});

test("3: an empty day (gap) is present with null means and count 0: Nov 21 and Nov 23 have no reading", () => {
  const d = dailySeriesForPlant(A, "a", NOW_MS, 30);
  assert.deepEqual(day(d, "2026-11-21"), { date: "2026-11-21", ...EMPTY });
  assert.deepEqual(day(d, "2026-11-23"), { date: "2026-11-23", ...EMPTY });
  // every date except the 7 populated ones is empty: 30 - 7 = 23 empty items
  const populated = new Set(["2026-10-26", "2026-11-17", "2026-11-18", "2026-11-19", "2026-11-20", "2026-11-22", "2026-11-24"]);
  const empties = d.filter((x) => !populated.has(x.date));
  assert.equal(empties.length, 23);
  for (const e of empties) assert.deepEqual({ soilPctMean: e.soilPctMean, batteryMvMean: e.batteryMvMean, readingCount: e.readingCount }, EMPTY, e.date);
});

test("4: a day with only battery values: Nov 22 = (null, 3700), (null, 3600) -> soil null, battery (3700+3600)/2 = 3650, count 2", () => {
  assert.deepEqual(day(dailySeriesForPlant(A, "a", NOW_MS, 30), "2026-11-22"),
    { date: "2026-11-22", soilPctMean: null, batteryMvMean: 3650, readingCount: 2 });
});

test("5: first day of the window: Oct 26 = 10 (00:00:00) and 20 (23:00) -> soil 15, battery (4000+3990)/2 = 3995, count 2; the Oct 25 rows are in no item", () => {
  const d = dailySeriesForPlant(A, "a", NOW_MS, 30);
  assert.deepEqual(d[0], { date: "2026-10-26", soilPctMean: 15, batteryMvMean: 3995, readingCount: 2 });
  assert.ok(!d.some((x) => x.date === "2026-10-25"));
  // total of all items: Oct 26 (2) + Nov 17 (2) + Nov 18 (3) + Nov 19 (1) + Nov 20 (2) + Nov 22 (2) + Nov 24 (3) = 15
  assert.equal(d.reduce((n, x) => n + x.readingCount, 0), 15);
});

test("5b: last day of the window is today (UTC) and holds the readings up to nowMs", () => {
  const d = dailySeriesForPlant(A, "a", NOW_MS, 30);
  assert.equal(d[29].date, "2026-11-24");
  assert.equal(d[29].readingCount, 3);
});

test("6: UTC midnight boundary: 23:59:59Z on Nov 19 and 00:00:00Z on Nov 20 land on different days", () => {
  const d = dailySeriesForPlant(A, "a", NOW_MS, 30);
  // Nov 19: only 23:59:59 -> soil 30, battery 3500, count 1.  Nov 20: 00:00:00 (70, 3400) and 12:00 (80, 3300) -> soil 150/2 = 75, battery 6700/2 = 3350, count 2.
  assert.deepEqual(day(d, "2026-11-19"), { date: "2026-11-19", soilPctMean: 30, batteryMvMean: 3500, readingCount: 1 });
  assert.deepEqual(day(d, "2026-11-20"), { date: "2026-11-20", soilPctMean: 75, batteryMvMean: 3350, readingCount: 2 });
});

test("6b: a local-time bucketing would move these: 23:30Z (Berlin 00:30 next day) stays on its UTC date", () => {
  const rows = [r("a", "2026-11-23T23:30:00Z", 10, 3000), r("a", "2026-11-24T00:30:00Z", 20, 3100)];
  const d = dailySeriesForPlant(rows, "a", NOW_MS, 30);
  assert.deepEqual(day(d, "2026-11-23"), { date: "2026-11-23", soilPctMean: 10, batteryMvMean: 3000, readingCount: 1 });
  assert.deepEqual(day(d, "2026-11-24"), { date: "2026-11-24", soilPctMean: 20, batteryMvMean: 3100, readingCount: 1 });
});

test("7: rows older than the window, before the first listed date, or after nowMs are in no item (Oct 25 15:00, Oct 25 09:00, 10:00:01 today)", () => {
  const d = dailySeriesForPlant(A, "a", NOW_MS, 30);
  assert.ok(!d.some((x) => x.soilPctMean === 99 || x.soilPctMean === 77 || x.batteryMvMean === 3999 || x.batteryMvMean === 3777 || x.batteryMvMean === 1));
  // ADR-018 open point 1: the Oct 25 15:00 row is in the aggregate (rolling window starts Oct 25 10:00) but in no daily item, so the sums differ: 16 vs 15.
  assert.equal(aggregatePlant({ id: "a", name: "A" }, A, NOW_MS, 30).readingCount, 16);
  assert.equal(d.reduce((n, x) => n + x.readingCount, 0), 15);
});

test("8: a plant with no readings (or only other plants' readings): 30 items, all null, all 0", () => {
  for (const rows of [[], A]) {
    const d = dailySeriesForPlant(rows, "nobody", NOW_MS, 30);
    assert.equal(d.length, 30);
    assert.deepEqual(d.map((x) => x.date), DATES_30);
    for (const x of d) assert.deepEqual({ soilPctMean: x.soilPctMean, batteryMvMean: x.batteryMvMean, readingCount: x.readingCount }, EMPTY, x.date);
  }
});

test("9: 90-day window: 90 items from 2026-08-27 to 2026-11-24, one UTC day apart; rows keep their day", () => {
  const rows = [...A, r("a", "2026-08-26T23:59:59Z", 1, 1), r("a", "2026-08-27T00:00:00Z", 5, 4100)];
  const d = dailySeriesForPlant(rows, "a", NOW_MS, 90);
  assert.equal(d.length, 90);
  assert.equal(d[0].date, "2026-08-27"); assert.equal(d[89].date, "2026-11-24");
  // independent date arithmetic: item i is 2026-08-27 + i days (Date.UTC rolls the month over)
  d.forEach((x, i) => assert.equal(x.date, new Date(Date.UTC(2026, 7, 27 + i)).toISOString().slice(0, 10), `item ${i}`));
  // first day: only the 00:00:00 row (5, 4100); the 23:59:59 row of Aug 26 is before the first listed date: in no item
  assert.deepEqual(d[0], { date: "2026-08-27", soilPctMean: 5, batteryMvMean: 4100, readingCount: 1 });
  assert.ok(!d.some((x) => x.date === "2026-08-26"));
  // Oct 25 is a listed day in the 90-day window and both its rows (09:00 and 15:00) are inside: Oct 25 has two rows -> soil (77+99)/2 = 88, battery (3777+3999)/2 = 3888
  assert.deepEqual(day(d, "2026-10-25"), { date: "2026-10-25", soilPctMean: 88, batteryMvMean: 3888, readingCount: 2 });
});

test("10: size bound: at most 90 items x 4 values per plant, for both windows", () => {
  for (const w of [30, 90]) {
    const d = dailySeriesForPlant(A, "a", NOW_MS, w);
    assert.equal(d.length, w);
    assert.ok(d.length <= 90);
    assert.ok(d.every((x) => Object.keys(x).length === 4));
  }
});

test("11: aggregatePlant carries the same series (the 30-day aggregate fields are unchanged)", () => {
  const p = aggregatePlant({ id: "a", name: "A" }, A, NOW_MS, 30);
  assert.deepEqual(p.daily, dailySeriesForPlant(A, "a", NOW_MS, 30));
  assert.equal(p.daily.length, 30);
});

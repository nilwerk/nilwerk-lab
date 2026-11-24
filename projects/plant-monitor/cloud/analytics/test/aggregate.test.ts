// Tests for the analytics aggregates (task 4.B3-4.B4 family; FR-P01, FR-P04).
// Run: node --experimental-strip-types --test cloud/analytics/test/aggregate.test.ts   (no DB, no network)
// Expected values are written by hand from the fixture below (sums and counts listed in comments), not produced by the code under test.
import { test } from "node:test";
import assert from "node:assert/strict";
import { aggregatePlant, analyticsForPlants, comparePlants, type AnalyticsReading } from "../aggregate.ts";

const NOW = "2026-11-20T00:00:00Z";
const NOW_MS = Date.parse(NOW);
// 30-day window starts 2026-10-21T00:00Z, 90-day window starts 2026-08-22T00:00Z. First week of 30-day: Oct 21-27.

const r = (plantId: string | null, ts: string, moisturePct: number | null, vbatMv: number | null, plausible = true): AnalyticsReading =>
  ({ plantId, ts, moisturePct, vbatMv, plausible });

// Plant "a" (Basil) fixture. Ages are relative to NOW.
const BASIL: AnalyticsReading[] = [
  r("a", "2026-09-21T00:00:00Z", 20, 3950),  // -60 d: only in the 90-day window
  r("a", "2026-10-20T00:00:00Z", 10, 3000),  // -31 d: only in the 90-day window
  r("a", "2026-10-22T00:00:00Z", 40, 3900),  // -29 d: first week of 30-day
  r("a", "2026-10-26T00:00:00Z", 38, 3880),  // -25 d: first week of 30-day
  r("a", "2026-10-31T00:00:00Z", 30, 3850),  // -20 d
  r("a", "2026-11-08T00:00:00Z", 30, 3820),  // -12 d
  r("a", "2026-11-08T03:00:00Z", 50, 3815),  // 3 h after the previous: gap > 2 h, a +20 rise is NOT a watering
  r("a", "2026-11-10T00:00:00Z", 30, 3800),  // -10 d
  r("a", "2026-11-10T00:15:00Z", 40, 3805),  // +15 min: rise of exactly 10 IS a watering (A-115: 10 points or more): WATERING EVENT
  r("a", "2026-11-14T00:00:00Z", 35, 3740),  // -6 d: last week
  r("a", "2026-11-17T00:00:00Z", 30, 3760),  // -3 d: last week
  r("a", "2026-11-17T00:15:00Z", 31, 3758),  // +1
  r("a", "2026-11-17T00:30:00Z", 45, 3755),  // +14 from 31: WATERING EVENT 1
  r("a", "2026-11-17T00:45:00Z", 44, 3750),  // drop
  r("a", "2026-11-19T00:00:00Z", 40, 3720),  // -1 d: last week
  r("a", "2026-11-19T01:00:00Z", 52, 3715),  // +12 from 40 within 1 h: WATERING EVENT 2
  r("a", "2026-11-20T01:00:00Z", 99, 3000),  // one hour in the future: excluded everywhere
];

test("30-day aggregates of Basil: 14 readings in window, soil and battery mean/min/max, 3 events, trend", () => {
  const got = aggregatePlant({ id: "a", name: "Basil" }, BASIL, NOW_MS, 30);
  // soil: 40,38,30,30,50,30,40,35,30,31,45,44,40,52 -> sum 535, n 14
  // battery: 3900,3880,3850,3820,3815,3800,3805,3740,3760,3758,3755,3750,3720,3715 -> sum 53068, n 14
  assert.equal(got.readingCount, 14);
  assert.deepEqual(got.soilPct, { mean: 535 / 14, min: 30, max: 52 });
  assert.deepEqual(got.batteryMv, { mean: 53068 / 14, min: 3715, max: 3900 });
  assert.equal(got.wateringEvents, 3);   // hand count: +10 (00:15 on Nov 10, exactly 10 counts), +14 (Nov 17), +12 (Nov 19); the 3 h gap +20 does not
  // first week (Oct 21-27): 40, 38 -> 39. last week (Nov 13-20): 35,30,31,45,44,40,52 -> sum 277, n 7 -> 277/7
  assert.equal(got.trend.firstWeekMean, 39);
  assert.ok(Math.abs(got.trend.lastWeekMean! - 277 / 7) < 1e-9);
  assert.ok(Math.abs(got.trend.soilChangePct! - 4 / 7) < 1e-9);
});

test("90-day aggregates of Basil: 16 readings; first week empty so trend is null", () => {
  const got = aggregatePlant({ id: "a", name: "Basil" }, BASIL, NOW_MS, 90);
  // soil: the 14 above plus 20 and 10 -> sum 565, n 16, min 10, max 52
  // battery: the 14 above plus 3950 and 3000 -> sum 60018, n 16, min 3000, max 3950
  assert.equal(got.readingCount, 16);
  assert.deepEqual(got.soilPct, { mean: 565 / 16, min: 10, max: 52 });
  assert.deepEqual(got.batteryMv, { mean: 60018 / 16, min: 3000, max: 3950 });
  assert.equal(got.wateringEvents, 3);
  assert.equal(got.trend.soilChangePct, null);
  assert.equal(got.trend.firstWeekMean, null);
  assert.ok(Math.abs(got.trend.lastWeekMean! - 277 / 7) < 1e-9);
});

test("A-115 boundary: rise of exactly 10 points is an event, 9.9 is not", () => {
  const at = (v: number) => [r("a", "2026-11-10T00:00:00Z", 30, null), r("a", "2026-11-10T00:15:00Z", v, null)];
  assert.equal(aggregatePlant({ id: "a", name: "Basil" }, at(40), NOW_MS, 30).wateringEvents, 1);   // 40 - 30 = 10 -> counts
  assert.equal(aggregatePlant({ id: "a", name: "Basil" }, at(39.9), NOW_MS, 30).wateringEvents, 0); // 9.9 -> does not
});

test("A-115 boundary: exactly 2 h apart still joins, 2 h 1 s apart does not (rise +20 in both)", () => {
  const gap = (second: string) => [r("a", "2026-11-10T00:00:00Z", 30, null), r("a", second, 50, null)];
  assert.equal(aggregatePlant({ id: "a", name: "Basil" }, gap("2026-11-10T02:00:00Z"), NOW_MS, 30).wateringEvents, 1);  // 7,200,000 ms: allowed
  assert.equal(aggregatePlant({ id: "a", name: "Basil" }, gap("2026-11-10T02:00:01Z"), NOW_MS, 30).wateringEvents, 0);  // 7,201,000 ms: too far
});

test("A-115 both limits at once: exactly 10 points across exactly 2 h is an event", () => {
  const both = [r("a", "2026-11-10T00:00:00Z", 30, null), r("a", "2026-11-10T02:00:00Z", 40, null)];
  assert.equal(aggregatePlant({ id: "a", name: "Basil" }, both, NOW_MS, 30).wateringEvents, 1);
});

test("watering threshold: a rise of 10.5 is an event", () => {
  const rise: AnalyticsReading[] = [r("a", "2026-11-10T00:00:00Z", 30, null), r("a", "2026-11-10T00:15:00Z", 40.5, null)];
  assert.equal(aggregatePlant({ id: "a", name: "Basil" }, rise, NOW_MS, 30).wateringEvents, 1);
});

test("one reading: mean = min = max, no events, trend null", () => {
  const aloe: AnalyticsReading[] = [
    r("c", "2026-11-18T00:00:00Z", 25, 3600),       // -2 d, plausible
    r("c", "2026-11-18T01:00:00Z", 99, 3000, false), // implausible: excluded from every aggregate
  ];
  const got = aggregatePlant({ id: "c", name: "Aloe" }, aloe, NOW_MS, 30);
  assert.equal(got.readingCount, 1);
  assert.deepEqual(got.soilPct, { mean: 25, min: 25, max: 25 });
  assert.deepEqual(got.batteryMv, { mean: 3600, min: 3600, max: 3600 });
  assert.equal(got.wateringEvents, 0);
  assert.deepEqual(got.trend, { soilChangePct: null, firstWeekMean: null, lastWeekMean: 25 });
});

test("plant with no readings: explicit zeros and nulls, no crash", () => {
  const got = aggregatePlant({ id: "d", name: "Ficus" }, BASIL, NOW_MS, 30);
  assert.deepEqual(got, {
    plantId: "d", name: "Ficus", windowDays: 30, readingCount: 0, soilPct: null, batteryMv: null, wateringEvents: 0,
    trend: { soilChangePct: null, firstWeekMean: null, lastWeekMean: null },
  });
});

test("empty readings list and empty plant list: no crash", () => {
  assert.equal(aggregatePlant({ id: "a", name: "Basil" }, [], NOW_MS, 90).readingCount, 0);
  assert.deepEqual(comparePlants([], BASIL, NOW_MS, 30), []);
});

test("gaps: a single week of readings with an empty first week gives a null trend; readings with unparseable time are dropped", () => {
  const lastWeekOnly: AnalyticsReading[] = [
    r("e", "2026-11-18T00:00:00Z", 30, 3700),
    r("e", "not-a-date", 90, 3700),
  ];
  const got = aggregatePlant({ id: "e", name: "Elm" }, lastWeekOnly, NOW_MS, 30);
  assert.equal(got.readingCount, 1);
  assert.equal(got.trend.soilChangePct, null);
  assert.equal(got.trend.lastWeekMean, 30);
});

test("battery-only reading: soil stays null, battery is reported", () => {
  const got = aggregatePlant({ id: "f", name: "Fern" }, [r("f", "2026-11-18T00:00:00Z", null, 3500)], NOW_MS, 30);
  assert.equal(got.soilPct, null);
  assert.deepEqual(got.batteryMv, { mean: 3500, min: 3500, max: 3500 });
  assert.equal(got.wateringEvents, 0);
});

test("comparison: sorted by name, same numbers as the single-plant call, unknown plants' readings ignored", () => {
  const readings = [...BASIL, r("zz", "2026-11-18T00:00:00Z", 90, 3600)];
  const plants = [{ id: "d", name: "Ficus" }, { id: "a", name: "Basil" }, { id: "c", name: "Aloe" }];
  const got = comparePlants(plants, readings, NOW_MS, 30);
  assert.deepEqual(got.map((p) => p.name), ["Aloe", "Basil", "Ficus"]);
  assert.equal(got[0].readingCount, 0); // Aloe has no readings in this fixture
  assert.deepEqual(got[1], aggregatePlant({ id: "a", name: "Basil" }, readings, NOW_MS, 30));
  assert.equal(got[2].readingCount, 0);
});

test("premium gate (FR-P04): free users get premium_required for 30 and 90 days; invalid windows are refused", () => {
  const base = { plants: [{ id: "a", name: "Basil" }], readings: BASIL, nowMs: NOW_MS };
  assert.deepEqual(analyticsForPlants({ ...base, isPremium: false, windowDays: 30 }), { ok: false, error: "premium_required" });
  assert.deepEqual(analyticsForPlants({ ...base, isPremium: false, windowDays: 90 }), { ok: false, error: "premium_required" });
  assert.deepEqual(analyticsForPlants({ ...base, isPremium: true, windowDays: 7 }), { ok: false, error: "invalid_window" });
  const premium = analyticsForPlants({ ...base, isPremium: true, windowDays: 30 });
  assert.equal(premium.ok, true);
  if (premium.ok) {
    assert.equal(premium.windowDays, 30);
    assert.equal(premium.plants[0].wateringEvents, 3);
  }
});

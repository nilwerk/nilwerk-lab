// Hourly grid boundaries (4.A4 slice 2, acceptance 3): empty, one reading, 24 readings, a gap in time. Plus window edges.
// Requirements: FR-A06 (168 hourly points on the detail), FR-D02 (one report per hour = 24 per day), FR-D04 (a missing hour is a gap, not zero).
import { HOURS, hasAnyReading, hourlyGrid } from '../plants/hourly';
import type { HourlyPoint } from '../plants/types';

const H = 3600_000;
const NOW = new Date('2026-11-09T12:30:00Z'); // current UTC hour = 12:00
const END = Date.parse('2026-11-09T12:00:00Z');
/** a readings_hourly row that started `hoursAgo` hours before the current hour (negative = in the future) */
const row = (hoursAgo: number, v = 40): HourlyPoint => ({
  hour: new Date(END - hoursAgo * H).toISOString(), n: 4, moistureAvg: v, moistureMin: v - 1, moistureMax: v + 1,
  tempAvg: 20.5, rhAvg: 50, luxAvg: 900, vbatMinMv: 3600,
});
const isGap = (p: HourlyPoint) => p.n === null && p.moistureAvg === null && p.tempAvg === null && p.rhAvg === null && p.luxAvg === null && p.vbatMinMv === null;
/** indexes of the grid (0 = oldest, 167 = current hour) that hold a value */
const filledIdx = (pts: HourlyPoint[]) => pts.flatMap((p, i) => (isGap(p) ? [] : [i]));

describe('hourly grid (FR-A06, FR-D02, FR-D04)', () => {
  test('always 168 points, oldest first, the last one is the current UTC hour', () => {
    const g = hourlyGrid([], NOW);
    expect(g).toHaveLength(HOURS);
    expect(HOURS).toBe(168);
    expect(g[HOURS - 1].hour).toBe('2026-11-09T12:00:00.000Z');
    expect(g[0].hour).toBe('2026-11-02T13:00:00.000Z');
    for (let i = 1; i < g.length; i++) expect(Date.parse(g[i].hour) - Date.parse(g[i - 1].hour)).toBe(H);
  });

  test('boundary: EMPTY (no report in 7 days) = 168 gaps, every field null, no reading', () => {
    const g = hourlyGrid([], NOW);
    expect(g.every(isGap)).toBe(true);
    expect(hasAnyReading(g)).toBe(false);
  });

  test('boundary: ONE reading = exactly one value, at its hour, 167 gaps', () => {
    const g = hourlyGrid([row(0, 33)], NOW);
    expect(filledIdx(g)).toEqual([HOURS - 1]);
    expect(g[HOURS - 1]).toMatchObject({ moistureAvg: 33, n: 4, tempAvg: 20.5, vbatMinMv: 3600 });
    expect(hasAnyReading(g)).toBe(true);
  });

  test('boundary: 24 READINGS (one per hour, FR-D02) = 24 values in the newest day, 144 gaps', () => {
    const rows = Array.from({ length: 24 }, (_, i) => row(i, 30 + i));
    const g = hourlyGrid(rows, NOW);
    expect(filledIdx(g)).toEqual(Array.from({ length: 24 }, (_, i) => HOURS - 24 + i));
    expect(g.filter(isGap)).toHaveLength(144);
    expect(g[HOURS - 1].moistureAvg).toBe(30);
    expect(g[HOURS - 24].moistureAvg).toBe(53);
  });

  test('boundary: a full day with one missing report (FR-D02 23 +/- 1) = 23 values and one gap in the middle', () => {
    const rows = Array.from({ length: 24 }, (_, i) => row(i)).filter((r) => r.hour !== new Date(END - 10 * H).toISOString());
    const g = hourlyGrid(rows, NOW);
    expect(filledIdx(g)).toHaveLength(23);
    expect(isGap(g[HOURS - 1 - 10])).toBe(true);
    expect(isGap(g[HOURS - 1 - 9])).toBe(false);
  });

  test('boundary: a GAP IN TIME (offline hours) keeps the time axis: exact gap positions', () => {
    // reports 0..4 h ago and 10..12 h ago; hours 5..9 ago and 13 h ago onward are offline
    const rows = [0, 1, 2, 3, 4, 10, 11, 12].map((h) => row(h));
    const g = hourlyGrid(rows, NOW);
    const expectedGapHoursAgo = [5, 6, 7, 8, 9, ...Array.from({ length: HOURS - 13 }, (_, i) => 13 + i)];
    const gapIdx = g.flatMap((p, i) => (isGap(p) ? [i] : []));
    expect(gapIdx).toEqual(expectedGapHoursAgo.map((h) => HOURS - 1 - h).sort((a, b) => a - b));
    expect(g.length).toBe(HOURS); // no shortening of the series
  });

  test('a full week of reports = no gap', () => {
    const g = hourlyGrid(Array.from({ length: HOURS }, (_, i) => row(i)), NOW);
    expect(g.some(isGap)).toBe(false);
  });

  test('window edge: the oldest slot (167 h ago) is kept, 168 h ago and future rows are ignored', () => {
    const g = hourlyGrid([row(167, 11), row(168, 99), row(-1, 98)], NOW);
    expect(filledIdx(g)).toEqual([0]);
    expect(g[0].moistureAvg).toBe(11);
  });

  test('the current hour is the floor of now: 12:00 and 12:59 give the same grid', () => {
    const rows = [row(0, 40), row(1, 41)];
    expect(hourlyGrid(rows, new Date('2026-11-09T12:59:59Z'))).toEqual(hourlyGrid(rows, new Date('2026-11-09T12:00:00Z')));
  });
});

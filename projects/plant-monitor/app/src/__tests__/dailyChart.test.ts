// Geometry of the daily line chart (task 4.A6b, FR-P01; ADR-018): null days are gaps (no point, line broken, never 0 or interpolated),
// the y scale is fixed 0 to 100 soil percent, and reading counts never become a plotted value. Expectations are hand-written.
import { dailyChartGeometry, dailyChartSummary } from '../analytics/dailyChart';
import type { DailyPoint } from '../analytics/analyticsModel';

const d = (i: number, soilPctMean: number | null, readingCount = 1): DailyPoint =>
  ({ date: `2026-11-${String(i + 1).padStart(2, '0')}`, soilPctMean, batteryMvMean: null, readingCount });

describe('dailyChartGeometry (FR-P01)', () => {
  test('x spans 0 to 1 over the days, y is 1 at 0 % and 0 at 100 %', () => {
    const g = dailyChartGeometry([d(0, 0), d(1, 50), d(2, 100)]);
    expect(g.points).toEqual([{ index: 0, x: 0, y: 1 }, { index: 1, x: 0.5, y: 0.5 }, { index: 2, x: 1, y: 0 }]);
    expect(g.segments).toEqual([[g.points[0], g.points[1]], [g.points[1], g.points[2]]]);
  });

  test('a null day has no point and breaks the line: no segment is drawn across it (no interpolation)', () => {
    const g = dailyChartGeometry([d(0, 40), d(1, 40), d(2, null), d(3, 40), d(4, 40)]);
    expect(g.points.map((p) => p.index)).toEqual([0, 1, 3, 4]);
    expect(g.segments.map(([a, b]) => [a.index, b.index])).toEqual([[0, 1], [3, 4]]);
  });

  test('a single valued day between two gaps is a lone point with no segment', () => {
    const g = dailyChartGeometry([d(0, null), d(1, 30), d(2, null)]);
    expect(g.points).toEqual([{ index: 1, x: 0.5, y: 0.7 }]);
    expect(g.segments).toEqual([]);
  });

  test('a real 0 % is a point at the bottom, not a gap', () => {
    expect(dailyChartGeometry([d(0, 0)]).points).toEqual([{ index: 0, x: 0.5, y: 1 }]);
  });

  test('reading counts do not change the geometry', () => {
    const a = dailyChartGeometry([d(0, 40, 1), d(1, 40, 1)]);
    const b = dailyChartGeometry([d(0, 40, 99), d(1, 40, 0)]);
    expect(b).toEqual(a);
  });

  test('summary counts days with and without a mean value, and the first and last date', () => {
    expect(dailyChartSummary([d(0, 40), d(1, null), d(2, 0)])).toEqual({ days: 3, withValue: 2, gaps: 1, first: '2026-11-01', last: '2026-11-03' });
    expect(dailyChartSummary([])).toEqual({ days: 0, withValue: 0, gaps: 0, first: null, last: null });
  });
});

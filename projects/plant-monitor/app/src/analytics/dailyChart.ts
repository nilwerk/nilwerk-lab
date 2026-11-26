// Geometry of the per-plant daily line chart (task 4.A6b, FR-P01; owner decision A-131, ADR-018). Pure functions, no React, unit-tested directly.
// Rules: a day with a null soil mean is a GAP: no dot, and the line is broken there (never drawn as 0, never interpolated across).
// reading_count is never a plotted value. The y scale is fixed 0 to 100 soil percent, so charts of different plants are comparable.
import type { DailyPoint } from './analyticsModel';

export interface ChartPoint { index: number; x: number; y: number }  // x, y are fractions of the plot box (0 = left/top)

export interface DailyChartGeometry {
  points: ChartPoint[];                 // one per day with a soil mean, oldest first
  segments: [ChartPoint, ChartPoint][]; // only between two neighbouring days that both have a value
}

const clamp01 = (f: number): number => Math.min(1, Math.max(0, f));

export function dailyChartGeometry(daily: DailyPoint[]): DailyChartGeometry {
  const n = daily.length;
  const points: ChartPoint[] = [];
  const at = new Map<number, ChartPoint>();
  daily.forEach((d, index) => {
    if (d.soilPctMean === null) return;
    const x = n > 1 ? index / (n - 1) : 0.5;
    const p = { index, x, y: 1 - clamp01(d.soilPctMean / 100) };
    points.push(p);
    at.set(index, p);
  });
  const segments: [ChartPoint, ChartPoint][] = [];
  for (let i = 0; i + 1 < n; i++) {
    const a = at.get(i), b = at.get(i + 1);
    if (a && b) segments.push([a, b]);
  }
  return { points, segments };
}

export interface DailyChartSummary { days: number; withValue: number; gaps: number; first: string | null; last: string | null }

export function dailyChartSummary(daily: DailyPoint[]): DailyChartSummary {
  const withValue = daily.filter((d) => d.soilPctMean !== null).length;
  return {
    days: daily.length,
    withValue,
    gaps: daily.length - withValue,
    first: daily.length ? daily[0].date : null,
    last: daily.length ? daily[daily.length - 1].date : null,
  };
}

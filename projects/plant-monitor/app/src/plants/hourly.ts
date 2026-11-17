// 7-day hourly grid (FR-A06: 168 hourly points; FR-D02: one report per hour, so 24 readings per day; a missing hour has no row in readings_hourly, so it is a gap).
// Pure functions, no React Native import, so the boundary tests run in Jest without a device.
import type { HourlyPoint } from './types';

export const HOURS = 168;
const HOUR_MS = 3600_000;

const gap = (hour: string): HourlyPoint => ({ hour, n: null, moistureAvg: null, moistureMin: null, moistureMax: null, tempAvg: null, rhAvg: null, luxAvg: null, vbatMinMv: null });

/**
 * Fills the 7-day grid: 168 points, oldest first, the last one is the current UTC hour.
 * readings_hourly has no row for an hour without reports, so a missing hour becomes a gap (all null).
 * Rows outside the window (older than 168 h, or in the future) are ignored. Rows are keyed by their hour, so a row must start on the hour (DB check).
 */
export function hourlyGrid(rows: HourlyPoint[], now: Date): HourlyPoint[] {
  const end = Math.floor(now.getTime() / HOUR_MS) * HOUR_MS;
  const byHour = new Map<number, HourlyPoint>();
  for (const r of rows) {
    const ms = Date.parse(r.hour);
    if (Number.isFinite(ms)) byHour.set(ms, r);
  }
  const out: HourlyPoint[] = [];
  for (let i = HOURS - 1; i >= 0; i--) {
    const ms = end - i * HOUR_MS;
    const iso = new Date(ms).toISOString();
    const r = byHour.get(ms);
    out.push(r ? { ...r, hour: iso } : gap(iso));
  }
  return out;
}

/** True when at least one hour in the grid has a report. Empty and all-gap series show the empty state. */
export const hasAnyReading = (points: HourlyPoint[]) => points.some((p) => p.n !== null);

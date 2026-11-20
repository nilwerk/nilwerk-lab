// Alert rules (FR-A07 push alerts, FR-D06 low battery). PURE: no I/O, no clock except the `now` argument.
// Mirrors the server rules so the app shows what the server would open:
//   cloud/supabase/migrations/20261116000007_evaluate_alerts_batch.sql (too dry, too wet, low battery, clear rules)
//   cloud/supabase/migrations/20261107000001_core_schema.sql scan_offline (offline: last report older than 3 h 10 min)
// Not here: edge-AI events (wetting, out of soil, sensor fault). Those come from the events table (FR-E03) in a later slice.
// Push delivery is NOT built: this only decides which alerts the alerts screen lists (MOCK data in the mock build).
import type { AlertKind, PlantSummary } from './types';

/** Kinds this slice decides. */
export type RuleAlertKind = Extract<AlertKind, 'too_dry' | 'too_wet' | 'low_battery' | 'device_offline'>;

// ---- thresholds (constants with their source) -------------------------------------------------
// Dry / wet thresholds are per plant (PlantSummary.dryThresholdPct / wetThresholdPct, default 25 / 85).
// Source: Requirements FR-A07, G1 answer; accepted A-008.3 (2026-11-03). Calibrated relative moisture, per soil type later.

/** Low battery opens below this (FR-D06, G1: 3.4 V). Device default devices.low_battery_mv = 3400. Accepted A-008. */
export const LOW_BATTERY_MV = 3400;
/** Low battery clears at threshold + 100 mV (= 3.5 V). Accepted A-018 (2026-11-05). */
export const BATTERY_CLEAR_MV = 100;
/** Too dry clears at dry threshold + 5 points (30 % with the 25 % default). TO CONFIRM: the 5-point reading is "my reading" in the acceptance matrix; Theo to state the wording. */
export const DRY_CLEAR_POINTS = 5;
/** Too wet clears at wet threshold - 5 points (80 % with the 85 % default). TO CONFIRM: same reading as DRY_CLEAR_POINTS. */
export const WET_CLEAR_POINTS = 5;
/** Offline when the last report is older than 3 missed hourly reports + 10 min grace = 190 min. Accepted A-008 point 21 and A-018 (2026-11-05). */
export const OFFLINE_AFTER_MIN = 190;
/** Battery values outside (0, 5000] mV are corrupt ADC reads and ignored (QA note 1, migration 20261116000007). */
export const MAX_PLAUSIBLE_VBAT_MV = 5000;

/** One reading point, oldest or newest first. For the app this is an hourly point (moistureAvg, vbatMinMv) plus the latest report. */
export interface AlertPoint {
  ts: string;
  moisturePct: number | null;
  vbatMv: number | null;
}

export interface AlertInput {
  now: Date;
  /** false = plant without a sensor: no alerts at all */
  hasSensor: boolean;
  dryThresholdPct: number;
  wetThresholdPct: number;
  lowBatteryMv?: number;
  /** ISO time of the last report; null = never reported (server rule: no offline alert without last_seen_at) */
  lastSeenAt: string | null;
  points: AlertPoint[];
}

export interface RuleAlert {
  kind: RuleAlertKind;
  /** too_dry / too_wet: latest soil %; low_battery: latest mV; device_offline: minutes since last report */
  value: number;
  /** the threshold it was compared with (dry %, wet %, mV, or OFFLINE_AFTER_MIN) */
  threshold: number;
}

const ORDER: RuleAlertKind[] = ['device_offline', 'too_dry', 'too_wet', 'low_battery'];

/**
 * Alerts open for one plant right now. Moisture and battery are replayed oldest to newest, so an alert
 * stays open between the opening threshold and the clear margin (hysteresis), like the server's
 * "open once until cleared" rule. Returned in the order of ORDER (offline first, as in status.ts).
 */
export function evaluateAlerts(input: AlertInput): RuleAlert[] {
  if (!input.hasSensor) return [];
  const low = input.lowBatteryMv ?? LOW_BATTERY_MV;
  const pts = [...input.points].sort((a, b) => Date.parse(a.ts) - Date.parse(b.ts));
  let dryOpen = false;
  let wetOpen = false;
  let batOpen = false;
  let lastMoisture: number | null = null;
  let lastVbat: number | null = null;
  for (const p of pts) {
    if (p.moisturePct !== null) {
      const m = p.moisturePct;
      lastMoisture = m;
      if (m < input.dryThresholdPct) dryOpen = true;
      else if (m >= input.dryThresholdPct + DRY_CLEAR_POINTS) dryOpen = false;
      if (m > input.wetThresholdPct) wetOpen = true;
      else if (m <= input.wetThresholdPct - WET_CLEAR_POINTS) wetOpen = false;
    }
    if (p.vbatMv !== null && p.vbatMv > 0 && p.vbatMv <= MAX_PLAUSIBLE_VBAT_MV) {
      const v = p.vbatMv;
      lastVbat = v;
      if (v < low) batOpen = true;
      else if (v >= low + BATTERY_CLEAR_MV) batOpen = false;
    }
  }
  const out: RuleAlert[] = [];
  if (input.lastSeenAt !== null) {
    const ageMin = (input.now.getTime() - Date.parse(input.lastSeenAt)) / 60000;
    if (ageMin > OFFLINE_AFTER_MIN) out.push({ kind: 'device_offline', value: Math.floor(ageMin), threshold: OFFLINE_AFTER_MIN });
  }
  if (dryOpen && lastMoisture !== null) out.push({ kind: 'too_dry', value: lastMoisture, threshold: input.dryThresholdPct });
  if (wetOpen && lastMoisture !== null) out.push({ kind: 'too_wet', value: lastMoisture, threshold: input.wetThresholdPct });
  if (batOpen && lastVbat !== null) out.push({ kind: 'low_battery', value: lastVbat, threshold: low });
  return out.sort((a, b) => ORDER.indexOf(a.kind) - ORDER.indexOf(b.kind));
}

/** Convenience for the screen: the plant's thresholds and sensor state, its hourly points and its latest report. */
export function alertsForPlant(
  plant: Pick<PlantSummary, 'deviceId' | 'dryThresholdPct' | 'wetThresholdPct' | 'lastSeenAt' | 'latest'>,
  hourly: { hour: string; moistureAvg: number | null; vbatMinMv: number | null }[],
  now: Date,
): RuleAlert[] {
  // an hourly bucket starts at or before the newest report it holds, so a bucket that starts after the latest
  // report is not real data for this moment (the mock grid can do that for the current hour) and is dropped
  const latestMs = plant.latest ? Date.parse(plant.latest.ts) : Infinity;
  const points: AlertPoint[] = hourly
    .filter((h) => Date.parse(h.hour) <= latestMs)
    .map((h) => ({ ts: h.hour, moisturePct: h.moistureAvg, vbatMv: h.vbatMinMv }));
  // the latest report is part of the recent readings even when its hour is not rolled up yet
  if (plant.latest) points.push({ ts: plant.latest.ts, moisturePct: plant.latest.moisturePct, vbatMv: plant.latest.vbatMv });
  return evaluateAlerts({
    now, hasSensor: plant.deviceId !== null, dryThresholdPct: plant.dryThresholdPct, wetThresholdPct: plant.wetThresholdPct,
    lastSeenAt: plant.lastSeenAt, points,
  });
}

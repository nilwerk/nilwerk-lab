// Plant status chips (FR-A06 list + status; FR-A07 kinds only as chip source, alerts UI is 4.A5). Colours/labels come from theme.ts statusMeta.
import type { PlantStatus } from '../../theme';
import type { AlertKind, PlantSummary } from './types';

export type ChipKind = PlantStatus | 'noSensor';

const KIND_TO_STATUS: Record<AlertKind, PlantStatus | null> = {
  device_offline: 'offline',
  sensor_fault: 'error',
  sensor_out_of_soil: 'error',
  too_dry: 'dry',
  too_wet: 'wet',
  waterlogged: 'wet',
  low_battery: 'lowBattery',
  wetting_unexpected: null, // informational event, not a state
};
// most urgent first: an offline sensor makes the moisture value stale, so it leads
const ORDER: PlantStatus[] = ['offline', 'error', 'dry', 'wet', 'lowBattery'];

/** All chips for a plant, most urgent first. No open alert = a single OK chip. No sensor = a single "No sensor yet" chip. */
export function plantChips(p: Pick<PlantSummary, 'deviceId' | 'openAlerts'>): ChipKind[] {
  if (!p.deviceId) return ['noSensor'];
  const set = new Set<PlantStatus>();
  for (const k of p.openAlerts) { const s = KIND_TO_STATUS[k]; if (s) set.add(s); }
  const out = ORDER.filter((s) => set.has(s));
  return out.length ? out : ['ok'];
}

/** Relative age for "Updated ..." as a catalogue key + params. */
export function ageParts(iso: string | null, now: Date): { key: string; n?: number } {
  if (!iso) return { key: 'plant.updated.never' };
  const min = Math.floor((now.getTime() - new Date(iso).getTime()) / 60000);
  if (min < 1) return { key: 'plant.updated.now' };
  if (min < 60) return { key: 'plant.updated.min', n: min };
  if (min < 1440) return { key: 'plant.updated.hours', n: Math.floor(min / 60) };
  return { key: 'plant.updated.days', n: Math.floor(min / 1440) };
}

/** Badge count for the Alerts tab: plants with a state other than OK or "no sensor". Pure, computed from the loaded list. */
export function countOpenAlertPlants(plants: Array<Pick<PlantSummary, 'deviceId' | 'openAlerts'>>): number {
  return plants.filter((p) => plantChips(p).some((c) => c !== 'ok' && c !== 'noSensor')).length;
}

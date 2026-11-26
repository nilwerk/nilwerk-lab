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

/** Counts for the "needs attention" strip on My plants. Computed on the client from the plant list the screen already loads (no endpoint). A plant counts once per state. */
export function attentionCounts(plants: Array<Pick<PlantSummary, 'deviceId' | 'openAlerts'>>): { dry: number; wet: number; lowBattery: number } {
  const n = { dry: 0, wet: 0, lowBattery: 0 };
  for (const p of plants) {
    const chips = plantChips(p);
    if (chips.includes('dry')) n.dry += 1;
    if (chips.includes('wet')) n.wet += 1;
    if (chips.includes('lowBattery')) n.lowBattery += 1;
  }
  return n;
}

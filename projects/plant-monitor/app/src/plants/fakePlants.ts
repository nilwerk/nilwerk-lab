// In-memory PlantsService: the "mocked backend" for tests and for running the app without a server (EXPO_PUBLIC_MOCK_AUTH=1).
// Fixture = the five plants of wireframe S20. Readings are synthetic (deterministic sine), NOT measured data.
import { PlantsError, type HourlyPoint, type PlantDetail, type PlantSummary, type PlantsService } from './types';

export interface FakePlantsOptions {
  now?: () => Date;
  plants?: PlantSummary[];
  /** hourly series per plant id; default = generated 168 points */
  hourly?: Record<string, HourlyPoint[]>;
  failList?: boolean;
  failDelete?: boolean;
  failRelease?: boolean;
}

const HOUR = 3600_000;

/** 168 hourly means ending at `now` (7 days), wave around `mid` with the given amplitude; every `gapEvery`-th hour is a gap if set. */
export function syntheticHourly(now: Date, mid: number, amp: number, gapFrom?: number): HourlyPoint[] {
  const end = Math.floor(now.getTime() / HOUR) * HOUR;
  const out: HourlyPoint[] = [];
  for (let i = 167; i >= 0; i--) {
    const hour = new Date(end - i * HOUR).toISOString();
    const gap = gapFrom !== undefined && i < gapFrom;
    out.push({ hour, moisturePct: gap ? null : Math.round((mid + amp * Math.sin((167 - i) / 10)) * 10) / 10 });
  }
  return out;
}

export function sampleFixture(now: Date): { plants: PlantSummary[]; hourly: Record<string, HourlyPoint[]> } {
  const ago = (min: number) => new Date(now.getTime() - min * 60000).toISOString();
  const mk = (id: string, name: string, area: string, dev: string | null, alerts: PlantSummary['openAlerts'], m: number | null, ageMin: number, vbat: number): PlantSummary => ({
    id, name, area, deviceId: dev, deviceName: dev ? `NW-${dev}` : null, lastSeenAt: dev ? ago(ageMin) : null, openAlerts: alerts,
    dryThresholdPct: 25, wetThresholdPct: 85,
    latest: dev && m !== null ? { ts: ago(ageMin), moisturePct: m, tempC: 21.4, rhPct: 48, lux: 1240, vbatMv: vbat } : null,
  });
  const plants = [
    mk('p-basil', 'Basil', 'Kitchen window', 'd4e5f6', [], 38, 14, 3820),
    mk('p-cactus', 'Cactus', 'Balcony', 'a1b2c3', ['too_dry'], 12, 22, 3700),
    mk('p-fern', 'Fern', 'Bedroom', 'b2c3d4', ['low_battery'], 52, 9, 3350),
    mk('p-orchid', 'Orchid', 'Living room', 'c3d4e5', ['device_offline'], 44, 300, 3600),
    mk('p-rubber', 'Rubber tree', 'Office', null, [], null, 0, 0),
  ];
  const hourly = {
    'p-basil': syntheticHourly(now, 50, 12),
    'p-cactus': syntheticHourly(now, 20, 8),
    'p-fern': syntheticHourly(now, 55, 10),
    'p-orchid': syntheticHourly(now, 45, 6, 168 - 163), // gap for the last ~5 h (offline)
    'p-rubber': [],
  };
  return { plants, hourly };
}

export function createFakePlants(opts: FakePlantsOptions = {}): PlantsService & { plants: PlantSummary[]; released: string[]; deleted: string[]; options: FakePlantsOptions } {
  const now = opts.now ?? (() => new Date());
  const fx = opts.plants ? { plants: opts.plants, hourly: opts.hourly ?? {} } : sampleFixture(now());
  const plants = [...fx.plants];
  const released: string[] = [];
  const deleted: string[] = [];
  const find = (id: string) => { const p = plants.find((x) => x.id === id); if (!p) throw new PlantsError('not_found'); return p; };
  return {
    plants, released, deleted, options: opts,
    async listPlants() { if (opts.failList) throw new PlantsError('network'); return plants.map((p) => ({ ...p })); },
    async getPlantDetail(id): Promise<PlantDetail> { if (opts.failList) throw new PlantsError('network'); const p = find(id); return { plant: { ...p }, hourly: fx.hourly[id] ?? [] }; },
    async deletePlant(id) {
      if (opts.failDelete) throw new PlantsError('network');
      const p = find(id);
      plants.splice(plants.indexOf(p), 1); // sensor stays claimed, only plant_id is cleared (A-022): the fake keeps no device table
      deleted.push(id);
      return { photoPaths: [`${id}/photo-1.jpg`] };
    },
    async releaseDevice(deviceId) { if (opts.failRelease) throw new PlantsError('network'); released.push(deviceId); },
  };
}

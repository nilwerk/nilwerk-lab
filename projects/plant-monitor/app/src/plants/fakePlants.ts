// In-memory PlantsService: the "mocked backend" for tests and for running the app without a server (EXPO_PUBLIC_MOCK_AUTH=1).
// Fixture = the five plants of wireframe S20. Readings and photos are synthetic (deterministic), NOT measured data. No network.
import { PlantsError, type ExportResult, type HourlyPoint, type PlantDetail, type PlantPhoto, type PlantSummary, type PlantsService } from './types';
import { hourlyGrid } from './hourly';

export interface FakePlantsOptions {
  now?: () => Date;
  plants?: PlantSummary[];
  /** readings_hourly rows per plant id (rows only, offline hours absent); the service fills the grid. Default = synthetic 7 days. */
  hourly?: Record<string, HourlyPoint[]>;
  /** plant_images per plant id; default = synthetic photos for two fixture plants */
  photos?: Record<string, PlantPhoto[]>;
  failList?: boolean;
  failDelete?: boolean;
  failRelease?: boolean;
  failExport?: boolean;
  failPhotoRemoval?: boolean;
}

const HOUR = 3600_000;
const DAY = 24 * HOUR;

/** readings_hourly rows for the last 7 days ending at `now`, wave around `mid`; the first `gapFrom` hours (newest) have no row (offline). */
export function syntheticRows(now: Date, mid: number, amp: number, gapFrom = 0): HourlyPoint[] {
  const end = Math.floor(now.getTime() / HOUR) * HOUR;
  const out: HourlyPoint[] = [];
  for (let i = 167; i >= 0; i--) {
    if (i < gapFrom) continue;
    const v = Math.round((mid + amp * Math.sin((167 - i) / 10)) * 10) / 10;
    out.push({
      hour: new Date(end - i * HOUR).toISOString(), n: 4,
      moistureAvg: v, moistureMin: Math.round((v - 1) * 10) / 10, moistureMax: Math.round((v + 1) * 10) / 10,
      tempAvg: 21.2, rhAvg: 49, luxAvg: 1100, vbatMinMv: 3600,
    });
  }
  return out;
}

/** 168 hourly points (grid) ending at `now`, gaps as null. */
export function syntheticHourly(now: Date, mid: number, amp: number, gapFrom?: number): HourlyPoint[] {
  return hourlyGrid(syntheticRows(now, mid, amp, gapFrom), now);
}

/** Dated synthetic photos for one plant, newest first, one every two days. */
export function syntheticPhotos(plantId: string, now: Date, count: number): PlantPhoto[] {
  return Array.from({ length: count }, (_, i) => ({
    id: `${plantId}-ph${i + 1}`, plantId, takenAt: new Date(now.getTime() - i * 2 * DAY).toISOString(),
    storagePath: `mock-owner/${plantId}/${plantId}-ph${i + 1}.jpg`,
  }));
}

export function sampleFixture(now: Date): { plants: PlantSummary[]; hourly: Record<string, HourlyPoint[]>; photos: Record<string, PlantPhoto[]> } {
  const ago = (min: number) => new Date(now.getTime() - min * 60000).toISOString();
  const mk = (id: string, name: string, locationType: PlantSummary['locationType'], area: string, soilType: PlantSummary['soilType'], dev: string | null, alerts: PlantSummary['openAlerts'], m: number | null, ageMin: number, vbat: number): PlantSummary => ({
    id, name, locationType, area, soilType, deviceId: dev, deviceName: dev ? `NW-${dev}` : null, lastSeenAt: dev ? ago(ageMin) : null, openAlerts: alerts,
    dryThresholdPct: 25, wetThresholdPct: 85,
    latest: dev && m !== null ? { ts: ago(ageMin), moisturePct: m, tempC: 21.4, rhPct: 48, lux: 1240, vbatMv: vbat } : null,
  });
  const plants = [
    mk('p-basil', 'Basil', 'house', 'Kitchen window', 'potting', 'd4e5f6', [], 38, 14, 3820),
    mk('p-cactus', 'Cactus', 'balcony', 'Balcony', 'sand', 'a1b2c3', ['too_dry'], 12, 22, 3700),
    mk('p-fern', 'Fern', 'house', 'Bedroom', 'peat', 'b2c3d4', ['low_battery'], 52, 9, 3350),
    mk('p-orchid', 'Orchid', 'house', 'Living room', 'potting', 'c3d4e5', ['device_offline'], 44, 300, 3600),
    mk('p-rubber', 'Rubber tree', 'house', 'Office', 'garden', null, [], null, 0, 0),
  ];
  const hourly = {
    'p-basil': syntheticRows(now, 50, 12),
    'p-cactus': syntheticRows(now, 20, 8),
    'p-fern': syntheticRows(now, 55, 10),
    'p-orchid': syntheticRows(now, 45, 6, 5), // no rows for the last 5 h (offline)
    'p-rubber': [],
  };
  const photos = { 'p-basil': syntheticPhotos('p-basil', now, 12), 'p-fern': syntheticPhotos('p-fern', now, 3) };
  return { plants, hourly, photos };
}

export function createFakePlants(opts: FakePlantsOptions = {}): PlantsService & { plants: PlantSummary[]; released: string[]; deleted: string[]; exports: ExportResult[]; removedObjects: string[]; options: FakePlantsOptions } {
  const now = opts.now ?? (() => new Date());
  const fx = opts.plants
    ? { plants: opts.plants, hourly: opts.hourly ?? {}, photos: opts.photos ?? {} }
    : (() => { const base = sampleFixture(now()); return { plants: base.plants, hourly: { ...base.hourly, ...opts.hourly }, photos: { ...base.photos, ...opts.photos } }; })();
  const plants = [...fx.plants];
  const hourlyRows: Record<string, HourlyPoint[]> = { ...fx.hourly };
  const photos: Record<string, PlantPhoto[]> = { ...fx.photos };
  const released: string[] = [];
  const deleted: string[] = [];
  const exports: ExportResult[] = [];
  const removedObjects: string[] = [];
  const find = (id: string) => { const p = plants.find((x) => x.id === id); if (!p) throw new PlantsError('not_found'); return p; };
  return {
    plants, released, deleted, exports, removedObjects, options: opts,
    async listPlants() { if (opts.failList) throw new PlantsError('network'); return plants.map((p) => ({ ...p })); },
    async getPlantDetail(id): Promise<PlantDetail> {
      if (opts.failList) throw new PlantsError('network');
      const p = find(id);
      return { plant: { ...p }, hourly: hourlyGrid(hourlyRows[id] ?? [], now()) };
    },
    async listPhotos(id) { if (opts.failList) throw new PlantsError('network'); find(id); return (photos[id] ?? []).map((x) => ({ ...x })); },
    async deletePlant(id) {
      if (opts.failDelete) throw new PlantsError('network');
      const p = find(id);
      const paths = (photos[id] ?? []).map((x) => x.storagePath);
      plants.splice(plants.indexOf(p), 1); // sensor stays claimed, only plant_id is cleared (A-022): the fake keeps no device table
      delete hourlyRows[id]; delete photos[id];
      deleted.push(id);
      return { photoPaths: paths };
    },
    async removePhotoObjects(paths) { if (opts.failPhotoRemoval) throw new PlantsError('network'); removedObjects.push(...paths); },
    async releaseDevice(deviceId) { if (opts.failRelease) throw new PlantsError('network'); released.push(deviceId); },
    async exportData(format) {
      if (opts.failExport) throw new PlantsError('network');
      const stamp = now().toISOString().slice(0, 10);
      const r: ExportResult = {
        format, fileName: `plant-monitor-export-${stamp}.${format === 'json' ? 'json' : 'zip'}`,
        contentType: format === 'json' ? 'application/json' : 'application/zip',
        plantCount: plants.length, photoCount: Object.values(photos).reduce((n, list) => n + list.length, 0),
      };
      exports.push(r);
      return { ...r };
    },
  };
}

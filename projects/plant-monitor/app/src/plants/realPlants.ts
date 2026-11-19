// PlantsService for real builds (EXPO_PUBLIC_MOCK_AUTH unset, Supabase configured). Real: listPlants, getPlantDetail (with the 168-hour grid, null gaps),
// listPhotos, deletePlant, removePhotoObjects, exportData. NOT real: releaseDevice (POST /device-release, still "not configured").
// Requirements: FR-A06, FR-A04 (fields read back), FR-A05, FR-A08, NFR-06, NFR-07. Never run against a backend or on a phone.
// `exported` semantics: exportData resolves ONLY after the file hand-off succeeded (written, shared, user confirmed), so the delete gate cannot open on a
// fetch that never reached the user. Any failure rejects with PlantsError('network') and leaves the gate closed.
import { PlantsError, type AlertKind, type ExportResult, type HourlyPoint, type PlantDetail, type PlantPhoto, type PlantSummary, type PlantsService } from './types';
import { LOCATION_TYPES, SOIL_TYPES, type LocationType, type SoilType } from '../provisioning/types';
import { unconfiguredPlants } from './unconfiguredPlants';
import { hourlyGrid, HOURS } from './hourly';
import { isPhotoPath } from './photoPath';
import { removeObjects, rpc, selectAll, type RestDeps } from './plantsRest';
import { ExportApiError, fetchExport, type ExportFormat } from '../export/exportClient';
import { HandOffError, type FileHandOff } from '../export/fileHandOff';

export interface RealPlantsDeps {
  baseUrl: string;
  publishableKey: string;
  getAccessToken: () => Promise<string | null>;
  handOff: FileHandOff;
  now?: () => Date;
  fetchImpl?: typeof fetch;
}

const fileName = (format: ExportFormat, now: Date) => `plant-monitor-export-${now.toISOString().slice(0, 10)}.${format === 'json' ? 'json' : 'zip'}`;

const ALERTS: readonly string[] = ['too_dry', 'too_wet', 'low_battery', 'device_offline', 'wetting_unexpected', 'waterlogged', 'sensor_out_of_soil', 'sensor_fault'];
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const bad = (m: string) => new PlantsError('unknown', m);
const num = (v: unknown): number | null => (typeof v === 'number' && Number.isFinite(v) ? v : null);
const str = (v: unknown): string | null => (typeof v === 'string' ? v : null);

/** plant_status row -> PlantSummary. A row without id, name or a valid location/soil is an error, never a half-filled plant. */
export function toSummary(r: Record<string, unknown>): PlantSummary {
  const id = str(r.plant_id), name = str(r.name);
  if (!id || !name) throw bad('plant row without id or name');
  if (!(LOCATION_TYPES as readonly unknown[]).includes(r.location_type) || !(SOIL_TYPES as readonly unknown[]).includes(r.soil_type)) throw bad('plant row with unknown location or soil type');
  const ts = str(r.reading_ts);
  return {
    id, name, locationType: r.location_type as LocationType, area: str(r.area), soilType: r.soil_type as SoilType,
    deviceId: str(r.device_id), deviceName: str(r.device_name), lastSeenAt: str(r.last_seen_at),
    openAlerts: (Array.isArray(r.open_alerts) ? r.open_alerts : []).filter((k): k is AlertKind => typeof k === 'string' && ALERTS.includes(k)),
    dryThresholdPct: num(r.dry_threshold_pct) ?? 25, wetThresholdPct: num(r.wet_threshold_pct) ?? 85,
    latest: ts ? { ts, moisturePct: num(r.moisture_pct), tempC: num(r.temp_c), rhPct: num(r.rh_pct), lux: num(r.lux), vbatMv: num(r.vbat_mv) } : null,
  };
}

function toHourly(r: Record<string, unknown>): HourlyPoint | null {
  const hour = str(r.hour);
  if (!hour || !Number.isFinite(Date.parse(hour))) return null;
  return { hour, n: num(r.n), moistureAvg: num(r.moisture_avg), moistureMin: num(r.moisture_min), moistureMax: num(r.moisture_max), tempAvg: num(r.temp_avg), rhAvg: num(r.rh_avg), luxAvg: num(r.lux_avg), vbatMinMv: num(r.vbat_min_mv) };
}

export function createRealPlants(d: RealPlantsDeps): PlantsService {
  const rest: RestDeps = { baseUrl: d.baseUrl, publishableKey: d.publishableKey, getAccessToken: d.getAccessToken, fetchImpl: d.fetchImpl };
  const now = () => (d.now ?? (() => new Date()))();
  const checkId = (id: string) => { if (!UUID.test(id)) throw new PlantsError('not_found'); };
  const detailCols = 'plant_id,name,location_type,area,soil_type,device_id,device_name,last_seen_at,open_alerts,dry_threshold_pct,wet_threshold_pct,reading_ts,moisture_pct,temp_c,rh_pct,lux,vbat_mv';
  return {
    ...unconfiguredPlants(),
    async listPlants() {
      return (await selectAll(rest, `plant_status?select=${detailCols}&order=name.asc,plant_id.asc`)).map(toSummary);
    },
    async getPlantDetail(plantId) {
      checkId(plantId);
      const rows = await selectAll(rest, `plant_status?select=${detailCols}&plant_id=eq.${plantId}`);
      if (rows.length === 0) throw new PlantsError('not_found');
      const at = now();
      const start = new Date(Math.floor(at.getTime() / 3600_000) * 3600_000 - (HOURS - 1) * 3600_000).toISOString();
      const hourly = (await selectAll(rest, `readings_hourly?select=hour,n,moisture_avg,moisture_min,moisture_max,temp_avg,rh_avg,lux_avg,vbat_min_mv&plant_id=eq.${plantId}&hour=gte.${encodeURIComponent(start)}&order=hour.asc`))
        .map(toHourly).filter((p): p is HourlyPoint => p !== null);
      const detail: PlantDetail = { plant: toSummary(rows[0]), hourly: hourlyGrid(hourly, at) };
      return detail;
    },
    async listPhotos(plantId): Promise<PlantPhoto[]> {
      checkId(plantId);
      return (await selectAll(rest, `plant_images?select=id,plant_id,taken_at,storage_path&plant_id=eq.${plantId}&order=taken_at.asc,id.asc`)).map((r) => {
        const id = str(r.id), pid = str(r.plant_id), takenAt = str(r.taken_at), storagePath = str(r.storage_path);
        if (!id || !pid || !takenAt || !storagePath) throw bad('photo row incomplete');
        return { id, plantId: pid, takenAt, storagePath };
      });
    },
    async deletePlant(plantId) {
      checkId(plantId);
      const res = (await rpc(rest, 'delete_plant', { p_plant: plantId })) as { photo_paths?: unknown } | null;
      // the plant is already gone when this answer arrives; a malformed list must not look like "no photos" (NFR-07), so it is an error the caller can see
      if (!res || !Array.isArray(res.photo_paths) || !res.photo_paths.every((p) => typeof p === 'string')) throw bad('delete_plant answer without photo_paths');
      return { photoPaths: res.photo_paths as string[] };
    },
    async removePhotoObjects(paths) {
      if (paths.length === 0) return;
      // refuse to send anything that is not '<uid>/<plant>/<file>' to Storage: one bad path fails the whole call, nothing is removed
      if (!paths.every((p) => isPhotoPath(p))) throw bad('photo path outside the <uid>/<plant_id>/<file> layout');
      for (let i = 0; i < paths.length; i += 100) await removeObjects(rest, 'plant-photos', paths.slice(i, i + 100));
    },
    async exportData(format): Promise<ExportResult> {
      const token = await d.getAccessToken().catch(() => null);
      let payload;
      try {
        payload = await fetchExport({ baseUrl: d.baseUrl, publishableKey: d.publishableKey, accessToken: token ?? '', format, fetchImpl: d.fetchImpl });
      } catch (e) {
        throw new PlantsError(e instanceof ExportApiError && e.code === 'unauthorized' ? 'unknown' : 'network', e instanceof Error ? e.message : undefined);
      }
      const name = fileName(format, now());
      try {
        await d.handOff({ fileName: name, contentType: payload.contentType, bytes: payload.bytes });
      } catch (e) {
        throw new PlantsError('unknown', e instanceof HandOffError ? e.message : 'export hand-off failed');
      }
      return { format, fileName: name, contentType: payload.contentType, plantCount: payload.plantCount, photoCount: payload.photoCount };
    },
  };
}

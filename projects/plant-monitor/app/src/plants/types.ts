// Plants contract used by the UI. Two sides: fakePlants.ts (mock, tests + EXPO_PUBLIC_MOCK_AUTH=1) and, later, a real Supabase client (NOT built in 4.A4).
// Shapes mirror docs/interfaces/db-schema.sql: view plant_status (L356), table readings_hourly (L214), table plant_images (L162), rpc delete_plant (L447), GET /export and POST /device-release (openapi.yaml).
// Requirements: FR-A06 (list with status, detail with latest values + 7-day chart and hourly table), FR-A04 (location type, room, soil type shown), FR-A05 (unlimited dated photos), FR-A02 (no cap), FR-A08 + A-022 (remove plant, release sensor), NFR-06 (own rows only), NFR-07 (export before delete, delete all data).
import type { LocationType, SoilType } from '../provisioning/types';

/** alerts.kind values (db-schema.sql L277). Alerts themselves are 4.A5; here they only drive the status chips. */
export type AlertKind =
  | 'too_dry' | 'too_wet' | 'low_battery' | 'device_offline'
  | 'wetting_unexpected' | 'waterlogged' | 'sensor_out_of_soil' | 'sensor_fault';

export interface LatestReading {
  /** ISO time of the last plausible report (plant_status.reading_ts) */
  ts: string;
  moisturePct: number | null;
  tempC: number | null;
  rhPct: number | null;
  lux: number | null;
  vbatMv: number | null;
}

/** One row of plant_status. deviceId null = plant without a sensor. locationType / soilType / area are the FR-A04 fields. */
export interface PlantSummary {
  id: string;
  name: string;
  locationType: LocationType;
  area: string | null;
  soilType: SoilType;
  deviceId: string | null;
  deviceName: string | null;
  lastSeenAt: string | null;
  openAlerts: AlertKind[];
  dryThresholdPct: number;
  wetThresholdPct: number;
  latest: LatestReading | null;
}

/**
 * One hourly point, field names from readings_hourly (db-schema.sql L214, camelCase here).
 * readings_hourly has NO row for an offline hour, so the service returns the full 168-hour grid
 * (hourlyGrid in hourly.ts): a missing hour is a point with every field null (a gap, FR-A06).
 */
export interface HourlyPoint {
  /** start of the UTC hour, ISO */
  hour: string;
  /** plausible 15-min samples in the hour (1-4); null = gap */
  n: number | null;
  moistureAvg: number | null;
  moistureMin: number | null;
  moistureMax: number | null;
  tempAvg: number | null;
  rhAvg: number | null;
  luxAvg: number | null;
  vbatMinMv: number | null;
}

export interface PlantDetail {
  plant: PlantSummary;
  /** always 168 points, oldest first, ending at the current UTC hour */
  hourly: HourlyPoint[];
}

/** One row of plant_images (db-schema.sql L162). The photo bytes live in bucket 'plant-photos' under storagePath. */
export interface PlantPhoto {
  id: string;
  plantId: string;
  /** ISO time, the date shown in the gallery */
  takenAt: string;
  storagePath: string;
}

/** Result of an export run (GET /export?format=json|csv, openapi.yaml). The file itself is handed to the user by src/export/fileHandOff.ts BEFORE exportData resolves (4.A9), so a resolved export means the user received it. */
export interface ExportResult {
  format: 'json' | 'csv';
  fileName: string;
  contentType: string;
  /** null when the format does not carry the number (CSV zip has no photo list) */
  plantCount: number | null;
  photoCount: number | null;
}

export type PlantsErrorCode = 'not_found' | 'network' | 'not_configured' | 'unknown';
export class PlantsError extends Error {
  code: PlantsErrorCode;
  constructor(code: PlantsErrorCode, message?: string) { super(message ?? code); this.name = 'PlantsError'; this.code = code; }
}

export interface PlantsService {
  /** select from plant_status, own rows under RLS. No limit (FR-A02). */
  listPlants(): Promise<PlantSummary[]>;
  /** latest values + hourly grid of the last 7 days (free-user window, FR-A06). */
  getPlantDetail(plantId: string): Promise<PlantDetail>;
  /** select from plant_images of one plant, no limit (FR-A05). Order as stored; the gallery sorts. */
  listPhotos(plantId: string): Promise<PlantPhoto[]>;
  /** rpc delete_plant(p_plant) (A-022). Returns the storage paths the caller must remove. The sensor stays claimed. */
  deletePlant(plantId: string): Promise<{ photoPaths: string[] }>;
  /** Storage: remove the photo objects returned by deletePlant (NFR-07; SQL cannot remove storage objects). */
  removePhotoObjects(paths: string[]): Promise<void>;
  /** POST /device-release (A-022 / FR-A08). */
  releaseDevice(deviceId: string): Promise<void>;
  /** GET /export?format=json|csv (openapi.yaml). Account-wide, because the endpoint has no plant_id parameter. The app must run it before any delete (A-022, NFR-07). */
  exportData(format: 'json' | 'csv'): Promise<ExportResult>;
}

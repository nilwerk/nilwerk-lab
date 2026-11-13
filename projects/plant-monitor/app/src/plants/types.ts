// Plants contract used by the UI. Two sides: fakePlants.ts (mock, tests + EXPO_PUBLIC_MOCK_AUTH=1) and, later, a real Supabase client (NOT built in 4.A4).
// Shapes mirror docs/interfaces/db-schema.sql: view plant_status (L356), table readings_hourly (L214), rpc delete_plant (L447), POST /device-release (openapi.yaml).
// Requirements: FR-A06 (list with status, detail with latest values + 7-day chart), FR-A02 (no cap), FR-A08 + A-022 (remove plant, release sensor), NFR-06 (own rows only).

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

/** One row of plant_status. deviceId null = plant without a sensor. */
export interface PlantSummary {
  id: string;
  name: string;
  area: string | null;
  deviceId: string | null;
  deviceName: string | null;
  lastSeenAt: string | null;
  openAlerts: AlertKind[];
  dryThresholdPct: number;
  wetThresholdPct: number;
  latest: LatestReading | null;
}

/** One hourly mean (readings_hourly.moisture_avg). null = gap (device offline).
 *  The real readings_hourly has NO row for an offline hour and moisture_avg is nullable: the real client must fill the 168-hour grid itself (missing hour -> null). The mock only emits explicit nulls. */
export interface HourlyPoint { hour: string; moisturePct: number | null }

export interface PlantDetail { plant: PlantSummary; hourly: HourlyPoint[] }

export type PlantsErrorCode = 'not_found' | 'network' | 'not_configured' | 'unknown';
export class PlantsError extends Error {
  code: PlantsErrorCode;
  constructor(code: PlantsErrorCode, message?: string) { super(message ?? code); this.name = 'PlantsError'; this.code = code; }
}

export interface PlantsService {
  /** select from plant_status, own rows under RLS. No limit (FR-A02). */
  listPlants(): Promise<PlantSummary[]>;
  /** latest values + hourly means of the last 7 days (free-user window, FR-A06). */
  getPlantDetail(plantId: string): Promise<PlantDetail>;
  /** rpc delete_plant(p_plant) (A-022). Returns the storage paths the caller must remove. The sensor stays claimed. */
  deletePlant(plantId: string): Promise<{ photoPaths: string[] }>;
  /** POST /device-release (A-022 / FR-A08). */
  releaseDevice(deviceId: string): Promise<void>;
}

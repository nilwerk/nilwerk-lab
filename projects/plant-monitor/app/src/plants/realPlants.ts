// PlantsService for real builds (EXPO_PUBLIC_MOCK_AUTH unset, Supabase configured). Only exportData is real in this slice (4.A9); every other call
// still says "not configured" (4.A4 is mock-only for lists, detail, photos, delete). Requirements: NFR-07, FR-A01.
// `exported` semantics: exportData resolves ONLY after the file hand-off succeeded (written, shared, user confirmed), so the delete gate cannot open on a
// fetch that never reached the user. Any failure rejects with PlantsError('network') and leaves the gate closed.
import { PlantsError, type ExportResult, type PlantsService } from './types';
import { unconfiguredPlants } from './unconfiguredPlants';
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

export function createRealPlants(d: RealPlantsDeps): PlantsService {
  return {
    ...unconfiguredPlants(),
    async exportData(format): Promise<ExportResult> {
      const token = await d.getAccessToken().catch(() => null);
      let payload;
      try {
        payload = await fetchExport({ baseUrl: d.baseUrl, publishableKey: d.publishableKey, accessToken: token ?? '', format, fetchImpl: d.fetchImpl });
      } catch (e) {
        throw new PlantsError(e instanceof ExportApiError && e.code === 'unauthorized' ? 'unknown' : 'network', e instanceof Error ? e.message : undefined);
      }
      const name = fileName(format, (d.now ?? (() => new Date()))());
      try {
        await d.handOff({ fileName: name, contentType: payload.contentType, bytes: payload.bytes });
      } catch (e) {
        throw new PlantsError('unknown', e instanceof HandOffError ? e.message : 'export hand-off failed');
      }
      return { format, fileName: name, contentType: payload.contentType, plantCount: payload.plantCount, photoCount: payload.photoCount };
    },
  };
}

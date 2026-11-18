// PlantsService for real builds (EXPO_PUBLIC_MOCK_AUTH unset, Supabase configured). Only exportData is real in this slice (4.A9); every other call
// still says "not configured" (4.A4 is mock-only for lists, detail, photos, delete). Requirements: NFR-07, FR-A01.
// A-107 (Arsany, option b): for JSON the app also downloads every photo behind the signed URLs into ONE archive (export.json + photos/*) and hands over that archive.
// If any photo fails, nothing is handed over and exportData rejects (photos_failed / photos_expired / photos_rejected / photos_none / photos_too_large / photos_archive), so the gate stays closed. CSV is handed over as before but is never `complete`.
// `exported` semantics: exportData resolves ONLY after the file hand-off succeeded (written, shared, user confirmed), so the delete gate cannot open on a
// fetch that never reached the user. Any failure rejects with PlantsError('network') and leaves the gate closed.
import { PlantsError, type ExportResult, type PlantsService } from './types';
import { unconfiguredPlants } from './unconfiguredPlants';
import { ExportApiError, fetchExport, type ExportFormat } from '../export/exportClient';
import { HandOffError, type FileHandOff } from '../export/fileHandOff';
import { PhotoExportError, downloadPhotos, readPhotoRefs } from '../export/photoExport';
import { buildStoredZip } from '../export/zip';

export interface RealPlantsDeps {
  baseUrl: string;
  publishableKey: string;
  getAccessToken: () => Promise<string | null>;
  handOff: FileHandOff;
  now?: () => Date;
  fetchImpl?: typeof fetch;
  /** photo downloads; defaults to fetchImpl. Separate so tests can see what is fetched from where. */
  photoFetchImpl?: typeof fetch;
}

const fileName = (now: Date) => `plant-monitor-export-${now.toISOString().slice(0, 10)}.zip`; // json: export.json + photos/, csv: the tables

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
      const now = d.now ?? (() => new Date());
      const name = fileName(now());
      let bytes = payload.bytes;
      let photoCount: number | null = null;
      let photosMissing = 0;
      if (format === 'json') {
        const refs = readPhotoRefs(payload.bytes);
        if (!refs) throw new PlantsError('photos_failed', 'export has no photo list', { failed: 0, total: 0 }); // cannot prove the copy is complete
        try {
          const got = await downloadPhotos(refs, { baseUrl: d.baseUrl, fetchImpl: d.photoFetchImpl ?? d.fetchImpl, now });
          // C2 (Theo): photos listed but not one saved = nothing to give the user; a systematic signing/path bug would otherwise unlock delete. `url:null` is "missing, not blocking" only when >= 1 photo was saved or the list is empty.
          if (got.total > 0 && got.saved.length === 0) throw new PlantsError('photos_none', 'photos listed but none could be saved', { failed: got.total, total: got.total });
          bytes = buildStoredZip([{ name: 'export.json', bytes: payload.bytes }, ...got.saved.map((s) => ({ name: s.entryName, bytes: s.bytes }))], now());
          photoCount = got.saved.length; photosMissing = got.missing;
        } catch (e) {
          if (e instanceof PlantsError) throw e;
          if (!(e instanceof PhotoExportError)) throw new PlantsError('photos_archive', 'photo archive failed'); // e.g. archive too large / out of memory: not a per-photo failure, no counts
          throw new PlantsError(e.reason === 'expired' ? 'photos_expired' : e.reason === 'rejected_host' ? 'photos_rejected' : e.reason === 'too_large' ? 'photos_too_large' : 'photos_failed', e.message, { failed: e.failed, total: e.total });
        }
      }
      try {
        await d.handOff({ fileName: name, contentType: 'application/zip', bytes });
      } catch (e) {
        throw new PlantsError('unknown', e instanceof HandOffError ? e.message : 'export hand-off failed');
      }
      return { format, fileName: name, contentType: 'application/zip', plantCount: payload.plantCount, photoCount, complete: format === 'json', photosMissing };
    },
  };
}

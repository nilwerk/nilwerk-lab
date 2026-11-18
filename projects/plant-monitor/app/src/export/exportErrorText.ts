// User-facing text for a failed or incomplete export (A-107, NFR-07). Honest about what happened: when the photos failed the JSON DID arrive but the copy is incomplete, and delete stays locked.
// The screen passes its own catalogue keys (generic error, ready line) so the string test can see them.
import { t } from '../i18n';
import { PlantsError, type ExportResult } from '../plants/types';

export function exportErrorText(e: unknown, genericKey: string): string {
  if (e instanceof PlantsError) {
    if (e.code === 'photos_expired') return t('export.photos.expired');
    if (e.code === 'photos_rejected') return t('export.photos.rejected');
    if (e.code === 'photos_failed') return e.total ? t('export.photos.failed', { failed: e.failed ?? 0, total: e.total }) : t('export.photos.noList');
  }
  return t(genericKey);
}

/** The info line after a finished export. An incomplete one (CSV) says plainly that delete stays locked. */
export function exportDoneText(r: ExportResult, readyKey: string): string {
  if (!r.complete) return t('export.csvIncomplete', { fileName: r.fileName });
  const base = t(readyKey, { fileName: r.fileName, photoCount: r.photoCount ?? 0 });
  return r.photosMissing > 0 ? `${base} ${t('export.photos.missing', { n: r.photosMissing })}` : base;
}

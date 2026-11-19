// Photo object path contract (db-schema.sql L169, plant_images.storage_path; Storage policy photos_own: first folder = auth.uid()).
// A photo lives at '<uid>/<plant_id>/<uuid>.<ext>': EXACTLY 3 segments. The cloud export (isSafePhotoPath in cloud/supabase/functions/_shared/export.ts) signs only such paths,
// so an upload with any other layout would be missing from the export (NFR-07). Requirements: FR-A05, NFR-06, NFR-07.
const SEG = /^[A-Za-z0-9._-]+$/;
const EXT = /^(jpg|jpeg|png|webp|heic)$/;

/** Shape check, same rule as the cloud guard minus the uid match (the app knows the uid only at call time). */
export function isPhotoPath(path: unknown, uid?: string): path is string {
  if (typeof path !== 'string' || path.includes('..') || path.startsWith('/') || path.includes('\\')) return false;
  const seg = path.split('/');
  return seg.length === 3 && seg.every((x) => SEG.test(x) && x !== '.') && (uid === undefined || seg[0] === uid);
}

/** Builds the upload path. Throws on anything that would not pass isPhotoPath (a wrong layout must never reach Storage). Upload itself is NOT built yet (needs expo-image-picker, dev build). */
export function buildPhotoPath(uid: string, plantId: string, uuid: string, ext: string): string {
  const e = ext.replace(/^\./, '').toLowerCase();
  const p = `${uid}/${plantId}/${uuid}.${e}`;
  if (!EXT.test(e) || !isPhotoPath(p, uid)) throw new Error('invalid photo path');
  return p;
}

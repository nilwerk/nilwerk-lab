// Download the plant photos behind the signed URLs of the JSON export into the export archive, BEFORE the delete gate may open.
// Requirements: NFR-07 (the user holds a complete copy before everything is deleted), FR-A01, FR-A05 (photos). Decision A-107 (Arsany, option b): the app downloads the photos, the export JSON only links them.
// Contract: docs/interfaces/openapi.yaml /export: photos:[{plant_id, taken_at, url}], signed Storage URLs valid 7 days [proposed]. The export function (PR #130, 4.B2c) additionally sends
// id, expires_at (absolute) and file per photo, and url:null when the Storage object is missing; those extras are OPTIONAL here, so the client also works against the bare openapi shape.
// Security: a photo URL is fetched only if it is https (http only for a localhost dev backend), has exactly the host of the configured Supabase URL, no userinfo, and a /storage/v1/object/sign/plant-photos/ path.
// Anything else is rejected WITHOUT a request (a tampered or wrong document must not make the app call arbitrary hosts). No Authorization header is sent: the signed URL carries its own token.
// Failure semantics: every photo is tried; if one fails the whole step throws PhotoExportError and nothing is handed over, so the gate stays closed (all-or-nothing).
// A `url: null` photo has no object in Storage (nothing to lose), so it is counted as `missing` and reported, not a download failure, ONLY when at least one photo was saved or the list is empty;
// if the list has photos and none was saved the caller treats the export as failed (a systematic signing bug must not unlock delete with zero photos saved; Theo C2).
// Size cap: the archive is built in memory, so the summed Content-Length of the photos is checked before each body is read (MAX_PHOTO_BYTES); over the cap -> 'too_large', nothing is handed over.
export type PhotoFailure = 'rejected_host' | 'expired' | 'network' | 'http' | 'bad_content' | 'bad_entry' | 'too_large';

/** in-app export cap for all photos together (in memory, about 2x while zipping). Conservative for a small phone; a streaming writer is a follow-up. */
export const MAX_PHOTO_BYTES = 150 * 1024 * 1024;

export class PhotoExportError extends Error {
  /** most serious reason first: rejected_host > expired > others */
  reason: PhotoFailure;
  failed: number;
  total: number;
  constructor(reason: PhotoFailure, failed: number, total: number) {
    super(`photo export: ${failed} of ${total} photos failed (${reason})`);
    this.name = 'PhotoExportError'; this.reason = reason; this.failed = failed; this.total = total;
  }
}

export interface PhotoRef { id: string | null; plantId: string | null; takenAt: string | null; url: string | null; expiresAt: string | null; file: string | null; bad: boolean }
export interface SavedPhoto { entryName: string; bytes: Uint8Array }

/** Reads the photo list of the export JSON. Returns null when the document has no `photos` array (an export without the list cannot prove completeness). */
export function readPhotoRefs(jsonBytes: Uint8Array): PhotoRef[] | null {
  let doc: { photos?: unknown };
  try { doc = JSON.parse(new TextDecoder().decode(jsonBytes)); } catch { return null; }
  if (!doc || !Array.isArray(doc.photos)) return null;
  const s = (x: unknown) => (typeof x === 'string' && x.length > 0 ? x : null);
  return doc.photos.map((p: unknown) => {
    const o = (p && typeof p === 'object' ? p : {}) as Record<string, unknown>;
    // url must be a string or an explicit null; a missing/garbled url is a bad entry (we cannot tell whether a photo exists)
    const bad = !(typeof o.url === 'string' || o.url === null);
    return { id: s(o.id), plantId: s(o.plant_id), takenAt: s(o.taken_at), url: s(o.url), expiresAt: s(o.expires_at), file: s(o.file), bad };
  });
}

/** true only for an https (or localhost http) URL on exactly the Supabase host, with a Storage signed-object path and no credentials. */
export function isExpectedPhotoUrl(url: string, baseUrl: string): boolean {
  let u: URL; let b: URL;
  try { u = new URL(url); b = new URL(baseUrl); } catch { return false; }
  const local = b.hostname === 'localhost' || b.hostname === '127.0.0.1' || b.hostname === '10.0.2.2';
  if (u.protocol !== 'https:' && !(local && u.protocol === 'http:' && b.protocol === 'http:')) return false;
  if (u.host !== b.host || u.username || u.password) return false;
  return u.pathname.startsWith('/storage/v1/object/sign/plant-photos/');
}

const safe = (s: string) => s.replace(/[^A-Za-z0-9._-]/g, '_').replace(/^\.+/, '_').slice(0, 80);
export const photoEntryName = (p: PhotoRef, index: number): string => {
  const base = p.file ? safe(p.file.split('/').pop() ?? '') : '';
  return `photos/${safe(p.id ?? `photo-${index + 1}`)}${base ? `_${base}` : ''}`;
};

export interface DownloadOptions {
  baseUrl: string;
  fetchImpl?: typeof fetch;
  now?: () => Date;
  concurrency?: number;
  timeoutMs?: number;
  /** cap on the summed size of all photos; default MAX_PHOTO_BYTES */
  maxTotalBytes?: number;
}
export interface DownloadResult { saved: SavedPhoto[]; missing: number; total: number }

const RANK: Record<PhotoFailure, number> = { too_large: -1, rejected_host: 0, expired: 1, bad_entry: 2, bad_content: 3, http: 4, network: 5 };

async function fetchOne(p: PhotoRef, i: number, o: Required<Pick<DownloadOptions, 'baseUrl' | 'timeoutMs'>> & { fetchImpl: typeof fetch; now: Date; budget: { left: number } }): Promise<SavedPhoto | PhotoFailure> {
  if (p.bad || !p.url) return 'bad_entry';
  if (!isExpectedPhotoUrl(p.url, o.baseUrl)) return 'rejected_host';
  const exp = p.expiresAt ? Date.parse(p.expiresAt) : NaN;
  if (!Number.isNaN(exp) && exp <= o.now.getTime()) return 'expired';
  let res: Response;
  try {
    const signal = typeof AbortSignal !== 'undefined' && typeof AbortSignal.timeout === 'function' ? AbortSignal.timeout(o.timeoutMs) : undefined;
    res = await o.fetchImpl(p.url, { method: 'GET', redirect: 'error', signal });
  } catch { return 'network'; }
  if (res.url && !isExpectedPhotoUrl(res.url, o.baseUrl)) return 'rejected_host'; // a redirect to another host
  if (res.status === 400 || res.status === 401 || res.status === 403) return 'expired'; // Storage answers an expired or invalid signed token this way
  if (res.status !== 200) return 'http';
  const ct = (res.headers.get('content-type') ?? '').toLowerCase();
  if (!ct.startsWith('image/')) return 'bad_content'; // e.g. a JSON error body or an HTML page with status 200 is not a photo
  const len = Number(res.headers.get('content-length'));
  if (Number.isFinite(len) && len > 0) { o.budget.left -= len; if (o.budget.left < 0) return 'too_large'; } // pre-flight: refuse before the body is read into memory
  let bytes: Uint8Array;
  try { bytes = new Uint8Array(await res.arrayBuffer()); } catch { return 'network'; }
  if (bytes.length === 0) return 'bad_content';
  if (!(Number.isFinite(len) && len > 0)) { o.budget.left -= bytes.length; if (o.budget.left < 0) return 'too_large'; } // no Content-Length: count what arrived
  const declared = Number(res.headers.get('content-length'));
  if (Number.isFinite(declared) && declared > 0 && declared !== bytes.length) return 'network'; // cut off
  return { entryName: photoEntryName(p, i), bytes };
}

export async function downloadPhotos(refs: PhotoRef[], opts: DownloadOptions): Promise<DownloadResult> {
  const o = { baseUrl: opts.baseUrl, fetchImpl: opts.fetchImpl ?? fetch, now: (opts.now ?? (() => new Date()))(), timeoutMs: opts.timeoutMs ?? 60_000, budget: { left: opts.maxTotalBytes ?? MAX_PHOTO_BYTES } };
  const todo = refs.map((p, i) => ({ p, i })).filter(({ p }) => p.bad || p.url !== null);
  const missing = refs.length - todo.length;
  const results: (SavedPhoto | PhotoFailure)[] = new Array(todo.length);
  let next = 0;
  const worker = async () => { while (next < todo.length) { const k = next++; results[k] = await fetchOne(todo[k].p, todo[k].i, o); } };
  await Promise.all(Array.from({ length: Math.max(1, Math.min(opts.concurrency ?? 4, todo.length)) }, worker));
  const fails = results.filter((r): r is PhotoFailure => typeof r === 'string');
  if (fails.length > 0) throw new PhotoExportError(fails.sort((a, b) => RANK[a] - RANK[b])[0], fails.length, refs.length);
  const names = new Set<string>();
  const saved = (results as SavedPhoto[]).map((s) => { let n = s.entryName; for (let k = 2; names.has(n); k++) n = `${s.entryName}-${k}`; names.add(n); return { ...s, entryName: n }; });
  return { saved, missing, total: refs.length };
}

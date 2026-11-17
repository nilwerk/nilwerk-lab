// Client for GET /export?format=json|csv (docs/interfaces/openapi.yaml /export). Requirements: NFR-07 (export before delete), FR-A01 (account data).
// CONTRACT STATUS: the OpenAPI path /export exists, but NO edge function for it is in cloud/supabase/functions and none is deployed on nilwerk-cloud
// (checked read-only 2026-11-17: only claim-token, ingest, device-claim, delete-account). This client assumes the route /functions/v1/export (same naming as
// delete-account) and returns the raw bytes; the file is handed to the user by fileHandOff.ts. Until the function exists every call ends in 'server'/'unknown', delete stays blocked.
export type ExportFormat = 'json' | 'csv';
export type ExportApiErrorCode = 'unauthorized' | 'network' | 'bad_request' | 'server' | 'unknown';

export class ExportApiError extends Error {
  code: ExportApiErrorCode;
  status?: number;
  constructor(code: ExportApiErrorCode, status?: number) {
    super(status ? `GET /export: ${code} (${status})` : `GET /export: ${code}`);
    this.name = 'ExportApiError';
    this.code = code;
    this.status = status;
  }
}

export interface ExportRequest {
  baseUrl: string;
  publishableKey: string;
  accessToken: string;
  format: ExportFormat;
  fetchImpl?: typeof fetch;
}

export interface ExportPayload {
  format: ExportFormat;
  contentType: string;
  bytes: Uint8Array;
  /** JSON only: counts read from the document. CSV (zip) has no photo list, so null. */
  plantCount: number | null;
  photoCount: number | null;
}

export const exportUrl = (baseUrl: string, format: ExportFormat): string => `${baseUrl.replace(/\/+$/, '')}/functions/v1/export?format=${format}`;

const EXPECTED: Record<ExportFormat, string> = { json: 'application/json', csv: 'application/zip' };

/** Resolves with the bytes only on a 200 with the expected content type and a non-empty body. An empty or wrong-type 200 is NOT an export (data-loss guard). */
export async function fetchExport({ baseUrl, publishableKey, accessToken, format, fetchImpl = fetch }: ExportRequest): Promise<ExportPayload> {
  if (!accessToken) throw new ExportApiError('unauthorized');
  let res: Response;
  try {
    res = await fetchImpl(exportUrl(baseUrl, format), { method: 'GET', headers: { Authorization: `Bearer ${accessToken}`, apikey: publishableKey } });
  } catch {
    throw new ExportApiError('network');
  }
  if (res.status === 401) throw new ExportApiError('unauthorized', 401);
  if (res.status === 400 || res.status === 405) throw new ExportApiError('bad_request', res.status);
  if (res.status >= 500) throw new ExportApiError('server', res.status);
  if (res.status !== 200) throw new ExportApiError('unknown', res.status);
  const contentType = res.headers.get('content-type') ?? '';
  if (!contentType.toLowerCase().startsWith(EXPECTED[format])) throw new ExportApiError('unknown', 200);
  let bytes: Uint8Array;
  try { bytes = new Uint8Array(await res.arrayBuffer()); } catch { throw new ExportApiError('network'); }
  if (bytes.length === 0) throw new ExportApiError('unknown', 200);
  if (format === 'csv') return { format, contentType: EXPECTED.csv, bytes, plantCount: null, photoCount: null };
  let doc: { plants?: unknown; photos?: unknown };
  try { doc = JSON.parse(new TextDecoder().decode(bytes)); } catch { throw new ExportApiError('unknown', 200); }
  if (!doc || typeof doc !== 'object' || !Array.isArray(doc.plants)) throw new ExportApiError('unknown', 200);
  return { format, contentType: EXPECTED.json, bytes, plantCount: doc.plants.length, photoCount: Array.isArray(doc.photos) ? doc.photos.length : 0 };
}

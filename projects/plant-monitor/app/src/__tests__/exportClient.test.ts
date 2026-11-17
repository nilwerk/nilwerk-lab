// GET /export client (NFR-07, FR-A01). Fake fetch only; never called against the live project.
import { ExportApiError, exportUrl, fetchExport } from '../export/exportClient';

const base = { baseUrl: 'https://x.supabase.co/', publishableKey: 'pub', accessToken: 'jwt' };
const res = (status: number, body: string | Uint8Array, ct: string) => ({ status, headers: { get: (h: string) => (h.toLowerCase() === 'content-type' ? ct : null) }, arrayBuffer: async () => (typeof body === 'string' ? new TextEncoder().encode(body) : body).buffer.slice(0) }) as unknown as Response;
const doc = JSON.stringify({ plants: [{}, {}], photos: [{}, {}, {}] });

describe('fetchExport', () => {
  test('GET /functions/v1/export?format=json with bearer + apikey; counts come from the document', async () => {
    const f = jest.fn().mockResolvedValue(res(200, doc, 'application/json; charset=utf-8'));
    const p = await fetchExport({ ...base, format: 'json', fetchImpl: f });
    expect(f).toHaveBeenCalledWith('https://x.supabase.co/functions/v1/export?format=json', { method: 'GET', headers: { Authorization: 'Bearer jwt', apikey: 'pub' } });
    expect(exportUrl('https://x.supabase.co//', 'csv')).toBe('https://x.supabase.co/functions/v1/export?format=csv');
    expect([p.plantCount, p.photoCount, p.contentType]).toEqual([2, 3, 'application/json']);
  });
  test('csv returns the zip bytes untouched, counts null', async () => {
    const zip = new Uint8Array([0x50, 0x4b, 3, 4]);
    const p = await fetchExport({ ...base, format: 'csv', fetchImpl: jest.fn().mockResolvedValue(res(200, zip, 'application/zip')) });
    expect(Array.from(p.bytes)).toEqual([0x50, 0x4b, 3, 4]);
    expect([p.plantCount, p.photoCount]).toEqual([null, null]);
  });
  test.each([[401, 'unauthorized'], [400, 'bad_request'], [405, 'bad_request'], [500, 'server'], [404, 'unknown'], [204, 'unknown']])('status %i -> %s', async (status, code) => {
    await expect(fetchExport({ ...base, format: 'json', fetchImpl: jest.fn().mockResolvedValue(res(status, doc, 'application/json')) })).rejects.toMatchObject({ code });
  });
  test('a 200 that is not a real export is rejected: empty body, wrong type, not JSON, no plants array', async () => {
    const run = (body: string, ct: string) => fetchExport({ ...base, format: 'json', fetchImpl: jest.fn().mockResolvedValue(res(200, body, ct)) });
    await expect(run('', 'application/json')).rejects.toBeInstanceOf(ExportApiError);
    await expect(run(doc, 'text/html')).rejects.toBeInstanceOf(ExportApiError);
    await expect(run('not json', 'application/json')).rejects.toBeInstanceOf(ExportApiError);
    await expect(run('{"photos":[]}', 'application/json')).rejects.toBeInstanceOf(ExportApiError);
  });
  test('an empty csv zip body is rejected', async () => {
    await expect(fetchExport({ ...base, format: 'csv', fetchImpl: jest.fn().mockResolvedValue(res(200, new Uint8Array(), 'application/zip')) })).rejects.toMatchObject({ code: 'unknown' });
  });
  test('fetch failure -> network; no token -> unauthorized without calling fetch', async () => {
    await expect(fetchExport({ ...base, format: 'json', fetchImpl: jest.fn().mockRejectedValue(new TypeError('x')) })).rejects.toMatchObject({ code: 'network' });
    const f = jest.fn();
    await expect(fetchExport({ ...base, accessToken: '', format: 'json', fetchImpl: f })).rejects.toMatchObject({ code: 'unauthorized' });
    expect(f).not.toHaveBeenCalled();
  });
});

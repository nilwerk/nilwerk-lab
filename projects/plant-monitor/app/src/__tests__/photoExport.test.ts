// Photo download into the export archive (A-107, NFR-07, FR-A05). Fake fetch only; nothing here touches a real Supabase project.
import { PhotoExportError, downloadPhotos, isExpectedPhotoUrl, photoEntryName, readPhotoRefs, type PhotoRef } from '../export/photoExport';

const BASE = 'https://abc.supabase.co';
const sign = (n: number, host = 'abc.supabase.co') => `https://${host}/storage/v1/object/sign/plant-photos/u1/${n}.jpg?token=t${n}`;
const NOW = new Date('2026-11-18T10:00:00Z');
const ref = (n: number, o: Partial<PhotoRef> = {}): PhotoRef => ({ id: `id${n}`, plantId: 'p1', takenAt: '2026-11-01T00:00:00Z', url: sign(n), expiresAt: '2026-11-24T10:00:00Z', file: `${n}.jpg`, bad: false, ...o });
const img = (status = 200, ct = 'image/jpeg', body: Uint8Array = new Uint8Array([1, 2, 3]), extra: Record<string, string> = {}, url = '') => ({ status, url, headers: { get: (h: string) => (h.toLowerCase() === 'content-type' ? ct : extra[h.toLowerCase()] ?? null) }, arrayBuffer: async () => body.buffer.slice(0) }) as unknown as Response;
const run = (refs: PhotoRef[], f: jest.Mock) => downloadPhotos(refs, { baseUrl: BASE, fetchImpl: f as unknown as typeof fetch, now: () => NOW });
const failure = async (refs: PhotoRef[], f: jest.Mock) => { try { await run(refs, f); } catch (e) { return e as PhotoExportError; } throw new Error('expected failure'); };

describe('isExpectedPhotoUrl (host check)', () => {
  test.each([
    [sign(1), true],
    ['https://abc.supabase.co/storage/v1/object/sign/plant-photos/x.jpg?token=1', true],
    ['https://evil.example/storage/v1/object/sign/plant-photos/x.jpg', false],
    ['https://abc.supabase.co.evil.example/storage/v1/object/sign/x', false],
    ['https://abc.supabase.co@evil.example/storage/v1/object/sign/x', false],
    ['https://user:pw@abc.supabase.co/storage/v1/object/sign/x', false],
    ['http://abc.supabase.co/storage/v1/object/sign/x', false],
    ['https://abc.supabase.co/rest/v1/profiles', false],
    ['https://abc.supabase.co:8443/storage/v1/object/sign/x', false],
    ['not a url', false],
    ['file:///etc/passwd', false],
  ])('%s -> %s', (u, ok) => expect(isExpectedPhotoUrl(u, BASE)).toBe(ok));
  test('plain http is accepted only for a localhost dev backend', () => {
    expect(isExpectedPhotoUrl('http://127.0.0.1:54321/storage/v1/object/sign/x', 'http://127.0.0.1:54321')).toBe(true);
    expect(isExpectedPhotoUrl('http://127.0.0.1:54321/storage/v1/object/sign/x', 'https://abc.supabase.co')).toBe(false);
  });
});

describe('readPhotoRefs', () => {
  const enc = (o: unknown) => new TextEncoder().encode(JSON.stringify(o));
  test('reads the #130 shape and the bare openapi shape (id/expires_at/file optional)', () => {
    const r = readPhotoRefs(enc({ photos: [{ id: 'a', plant_id: 'p', taken_at: 't', url: 'u', expires_at: 'e', file: 'x.jpg' }, { plant_id: 'p', taken_at: 't', url: 'u2' }, { plant_id: 'p', url: null }] }))!;
    expect(r.map((x) => [x.id, x.url, x.bad])).toEqual([['a', 'u', false], [null, 'u2', false], [null, null, false]]);
  });
  test('no photos array, or not JSON -> null (completeness cannot be proven)', () => {
    expect(readPhotoRefs(enc({ plants: [] }))).toBeNull();
    expect(readPhotoRefs(new TextEncoder().encode('nope'))).toBeNull();
  });
  test('an entry without a url key is a bad entry', () => expect(readPhotoRefs(enc({ photos: [{ plant_id: 'p' }] }))![0].bad).toBe(true));
});

describe('downloadPhotos', () => {
  test('saves every photo; GET without Authorization; names are unique and cannot escape photos/', async () => {
    const f = jest.fn().mockImplementation(async () => img());
    const r = await run([ref(1), ref(2, { id: 'same', file: '../../etc/passwd' }), ref(3, { id: 'same', file: '../../etc/passwd' })], f);
    expect(f).toHaveBeenCalledTimes(3);
    for (const c of f.mock.calls) { expect(c[1].method).toBe('GET'); expect(c[1].headers).toBeUndefined(); expect(c[1].redirect).toBe('error'); }
    const names = r.saved.map((s) => s.entryName);
    expect(new Set(names).size).toBe(3);
    expect(names.every((n) => n.startsWith('photos/') && !n.slice(7).includes('/') && !n.includes('..'))).toBe(true);
    expect(r.missing).toBe(0);
  });
  test('wrong host: rejected WITHOUT any request (also when only one of many is bad)', async () => {
    const f = jest.fn().mockImplementation(async () => img());
    const e = await failure([ref(1, { url: sign(1, 'evil.example') })], f);
    expect([e.reason, e.failed, e.total]).toEqual(['rejected_host', 1, 1]);
    expect(f).not.toHaveBeenCalled();
    const f2 = jest.fn().mockImplementation(async () => img());
    const e2 = await failure([ref(1), ref(2, { url: 'https://abc.supabase.co.evil.example/storage/v1/object/sign/x' }), ref(3)], f2);
    expect(e2.reason).toBe('rejected_host');
    expect(f2.mock.calls.map((c) => c[0])).not.toContain('https://abc.supabase.co.evil.example/storage/v1/object/sign/x');
  });
  test('a redirect to another host is refused (final url checked)', async () => {
    const f = jest.fn().mockResolvedValue(img(200, 'image/jpeg', new Uint8Array([1]), {}, 'https://evil.example/x.jpg'));
    expect((await failure([ref(1)], f)).reason).toBe('rejected_host');
  });
  test('expired by expires_at: clear reason, no request', async () => {
    const f = jest.fn();
    const e = await failure([ref(1, { expiresAt: '2026-11-18T09:59:59Z' })], f);
    expect(e.reason).toBe('expired'); expect(f).not.toHaveBeenCalled();
  });
  test('expires_at exactly now counts as expired; one second ahead is fine', async () => {
    expect((await failure([ref(1, { expiresAt: NOW.toISOString() })], jest.fn())).reason).toBe('expired');
    await expect(run([ref(1, { expiresAt: '2026-11-18T10:00:01Z' })], jest.fn().mockResolvedValue(img()))).resolves.toBeTruthy();
  });
  test.each([400, 401, 403])('Storage answers %i for a dead signed token -> expired', async (s) => {
    expect((await failure([ref(1)], jest.fn().mockResolvedValue(img(s, 'application/json')))).reason).toBe('expired');
  });
  test('500 -> http; fetch throws -> network; 200 JSON error body -> bad_content; empty body -> bad_content; cut-off body -> network', async () => {
    expect((await failure([ref(1)], jest.fn().mockResolvedValue(img(500)))).reason).toBe('http');
    expect((await failure([ref(1)], jest.fn().mockRejectedValue(new Error('offline')))).reason).toBe('network');
    expect((await failure([ref(1)], jest.fn().mockResolvedValue(img(200, 'application/json')))).reason).toBe('bad_content');
    expect((await failure([ref(1)], jest.fn().mockResolvedValue(img(200, 'image/jpeg', new Uint8Array(0))))).reason).toBe('bad_content');
    expect((await failure([ref(1)], jest.fn().mockResolvedValue(img(200, 'image/jpeg', new Uint8Array([1, 2]), { 'content-length': '10' })))).reason).toBe('network');
  });
  test('partial failure is all-or-nothing and counts honestly (2 of 4 failed)', async () => {
    const f = jest.fn().mockImplementation(async (u: string) => (/\/(2|4)\.jpg/.test(u) ? img(500) : img()));
    const e = await failure([ref(1), ref(2), ref(3), ref(4)], f);
    expect([e.reason, e.failed, e.total]).toEqual(['http', 2, 4]);
  });
  test('most serious reason wins: expired beats network', async () => {
    const f = jest.fn().mockImplementation(async (u: string) => { if (u.includes('/1.jpg')) throw new Error('x'); return img(403); });
    expect((await failure([ref(1), ref(2)], f)).reason).toBe('expired');
  });
  test('url null (object missing on the server) is counted as missing, not a failure and not fetched', async () => {
    const f = jest.fn().mockImplementation(async () => img());
    const r = await run([ref(1), ref(2, { url: null, expiresAt: null })], f);
    expect([r.saved.length, r.missing, r.total]).toEqual([1, 1, 2]);
    expect(f).toHaveBeenCalledTimes(1);
  });
  test('a malformed entry (no url key) fails the export instead of being skipped', async () => {
    expect((await failure([ref(1, { bad: true, url: null })], jest.fn())).reason).toBe('bad_entry');
  });
  test('zero photos is a valid complete export', async () => {
    const r = await run([], jest.fn());
    expect([r.saved.length, r.missing, r.total]).toEqual([0, 0, 0]);
  });
  test('photoEntryName works without id/file (bare openapi shape)', () => expect(photoEntryName(ref(1, { id: null, file: null }), 4)).toBe('photos/photo-5'));
});

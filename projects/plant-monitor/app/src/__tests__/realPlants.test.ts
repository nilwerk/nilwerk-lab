// Real PlantsService export + gate (4.A9, NFR-07, FR-A01, A-106). Replaces the two test.todo items from the #114 gates.
import { createRealPlants } from '../plants/realPlants';
import { PlantsError } from '../plants/types';
import { unconfiguredPlants } from '../plants/unconfiguredPlants';
import { canDelete } from '../export/exportGate';
import { handOffFile, HandOffError, type HandOffDeps } from '../export/fileHandOff';

const photoUrl = (n: number) => `https://x.supabase.co/storage/v1/object/sign/plant-photos/u1/${n}.jpg?token=t${n}`;
const doc = (photos: unknown[]) => JSON.stringify({ plants: [{}], photos });
const jsonRes = (body: string) => ({ status: 200, headers: { get: () => 'application/json' }, arrayBuffer: async () => new TextEncoder().encode(body).buffer }) as unknown as Response;
const photoRes = (status = 200) => ({ status, url: '', headers: { get: (h: string) => (h.toLowerCase() === 'content-type' ? 'image/jpeg' : null) }, arrayBuffer: async () => new Uint8Array([0xff, 0xd8, 1, 2, 3]).buffer }) as unknown as Response;
const two = [{ id: 'a', plant_id: 'p', taken_at: 't', url: photoUrl(1), expires_at: '2099-01-01T00:00:00Z', file: '1.jpg' }, { id: 'b', plant_id: 'p', taken_at: 't', url: photoUrl(2), expires_at: '2099-01-01T00:00:00Z', file: '2.jpg' }];
/** one fetch for the export call and the photo downloads, routed by URL like the real backend would */
const router = (photos: unknown[], photo: (u: string) => Response | Promise<Response> = () => photoRes()) => jest.fn().mockImplementation(async (u: string) => (u.includes('/functions/v1/export') ? jsonRes(doc(photos)) : photo(u)));
const mk = (o: { handOff?: (f: any) => Promise<void>; fetchImpl?: any; token?: string | null } = {}) => {
  const handOff = jest.fn(o.handOff ?? (async () => undefined));
  const svc = createRealPlants({ baseUrl: 'https://x.supabase.co', publishableKey: 'p', getAccessToken: async () => (o.token === undefined ? 'jwt' : o.token), handOff, now: () => new Date('2026-11-17T10:00:00Z'), fetchImpl: o.fetchImpl ?? router(two) });
  return { svc, handOff };
};
// what the screens do: exported = exportData resolved
const screenExported = async (svc: ReturnType<typeof mk>['svc']) => svc.exportData('json').then(() => true, () => false);

describe('real exportData hands the file over before it resolves', () => {
  test('resolves with metadata after the hand-off got the exact bytes and name', async () => {
    const { svc, handOff } = mk();
    const r = await svc.exportData('json');
    expect(handOff).toHaveBeenCalledTimes(1);
    expect(handOff.mock.calls[0][0]).toMatchObject({ fileName: 'plant-monitor-export-2026-11-17.zip', contentType: 'application/zip' });
    expect(handOff.mock.calls[0][0].bytes.length).toBeGreaterThan(0);
    expect(r).toMatchObject({ format: 'json', fileName: 'plant-monitor-export-2026-11-17.zip', plantCount: 1, photoCount: 2 });
  });
  test('exported is NOT set when the hand-off fails (fetch ok, file never reached the user)', async () => {
    const { svc } = mk({ handOff: async () => { throw new HandOffError('not_confirmed'); } });
    expect(await screenExported(svc)).toBe(false);
    const gate = { exported: await screenExported(svc), typed: 'Basil', expected: 'Basil' };
    expect(canDelete(gate)).toBe(false);
  });
  test('hand-off is not called when the fetch fails; no token -> no fetch, no hand-off', async () => {
    const a = mk({ fetchImpl: jest.fn().mockResolvedValue({ status: 500, headers: { get: () => null }, arrayBuffer: async () => new ArrayBuffer(0) }) });
    await expect(a.svc.exportData('json')).rejects.toBeInstanceOf(PlantsError);
    expect(a.handOff).not.toHaveBeenCalled();
    const f = jest.fn();
    const b = mk({ token: null, fetchImpl: f });
    expect(await screenExported(b.svc)).toBe(false);
    expect(f).not.toHaveBeenCalled(); expect(b.handOff).not.toHaveBeenCalled();
  });
  test('end to end with the real handOffFile and a share sheet the user dismisses: gate stays closed', async () => {
    const deps: HandOffDeps = { write: async (f) => ({ uri: 'u', size: f.bytes.length }), isShareAvailable: async () => true, share: async () => undefined, confirmSaved: async () => false };
    const svc = createRealPlants({ baseUrl: 'https://x.supabase.co', publishableKey: 'p', getAccessToken: async () => 'jwt', handOff: (f) => handOffFile(f, deps), fetchImpl: router(two) });
    expect(await screenExported(svc)).toBe(false);
  });
  test('only releaseDevice is still not_configured (POST /device-release is a later slice)', async () => {
    const { svc } = mk();
    await expect(svc.releaseDevice('x')).rejects.toMatchObject({ code: 'not_configured' });
  });
});

// ---- A-107 (4.A9b): the photos go into the archive BEFORE the gate opens. These tests go through the real createRealPlants caller path
// (export fetch -> photo fetch -> zip -> hand-off), so removing a step in realPlants.ts, not only in a helper, makes them fail. See showcase/items/2026-11-18_4.A9b/mutation-output.txt.
import { readZip } from './zipUtil';
describe('photos are downloaded into the archive before exportData resolves (A-107, NFR-07)', () => {
  test('hand-off gets ONE zip with the untouched export.json and every photo; result is complete', async () => {
    const f = router(two);
    const { svc, handOff } = mk({ fetchImpl: f });
    const r = await svc.exportData('json');
    const file = handOff.mock.calls[0][0];
    expect(file).toMatchObject({ fileName: 'plant-monitor-export-2026-11-17.zip', contentType: 'application/zip' });
    const z = readZip(file.bytes);
    expect(Object.keys(z).sort()).toEqual(['export.json', 'photos/a_1.jpg', 'photos/b_2.jpg']);
    expect(JSON.parse(new TextDecoder().decode(z['export.json'])).photos).toHaveLength(2);
    expect(Array.from(z['photos/a_1.jpg'])).toEqual([0xff, 0xd8, 1, 2, 3]);
    expect(r).toMatchObject({ complete: true, photoCount: 2, photosMissing: 0 });
    expect(f.mock.calls.map((c) => c[0])).toEqual(expect.arrayContaining([photoUrl(1), photoUrl(2)]));
  });
  test('one photo fails (500): exportData rejects photos_failed 1 of 2, the hand-off is NEVER called, the gate stays closed', async () => {
    const { svc, handOff } = mk({ fetchImpl: router(two, (u) => photoRes(u.includes('/2.jpg') ? 500 : 200)) });
    await expect(svc.exportData('json')).rejects.toMatchObject({ code: 'photos_failed', failed: 1, total: 2 });
    expect(handOff).not.toHaveBeenCalled();
    expect(canDelete({ exported: await screenExported(svc), typed: 'Basil', expected: 'Basil' })).toBe(false);
  });
  test('network drop during photos -> photos_failed, nothing handed over', async () => {
    const { svc, handOff } = mk({ fetchImpl: router(two, (u) => { if (u.includes('/1.jpg')) throw new Error('offline'); return photoRes(); }) });
    await expect(svc.exportData('json')).rejects.toMatchObject({ code: 'photos_failed' });
    expect(handOff).not.toHaveBeenCalled();
  });
  test('expired links (date in the past, no photo request made) -> photos_expired', async () => {
    const old = two.map((p) => ({ ...p, expires_at: '2026-11-16T00:00:00Z' }));
    const f = router(old);
    const { svc, handOff } = mk({ fetchImpl: f });
    await expect(svc.exportData('json')).rejects.toMatchObject({ code: 'photos_expired' });
    expect(handOff).not.toHaveBeenCalled();
    expect(f.mock.calls.filter((c) => !String(c[0]).includes('/functions/v1/export'))).toHaveLength(0);
  });
  test('expired links reported by Storage (400) -> photos_expired', async () => {
    const { svc } = mk({ fetchImpl: router(two, () => photoRes(400)) });
    await expect(svc.exportData('json')).rejects.toMatchObject({ code: 'photos_expired' });
  });
  test('a URL on another host is never fetched and the export is rejected (photos_rejected)', async () => {
    const evil = [two[0], { ...two[1], url: 'https://evil.example/storage/v1/object/sign/plant-photos/u1/2.jpg?token=x' }];
    const f = router(evil);
    const { svc, handOff } = mk({ fetchImpl: f });
    await expect(svc.exportData('json')).rejects.toMatchObject({ code: 'photos_rejected' });
    expect(f.mock.calls.map((c) => String(c[0])).some((u) => u.includes('evil.example'))).toBe(false);
    expect(handOff).not.toHaveBeenCalled();
  });
  test('export JSON without a photos list cannot prove completeness: rejected, nothing handed over', async () => {
    const f = jest.fn().mockResolvedValue(jsonRes('{"plants":[{}]}'));
    const { svc, handOff } = mk({ fetchImpl: f });
    // exportClient accepts a doc without `photos` (counts 0); the photo step must not
    await expect(svc.exportData('json')).rejects.toMatchObject({ code: 'photos_failed' });
    expect(handOff).not.toHaveBeenCalled();
  });
  test('hand-off failing AFTER all photos were saved still keeps the gate closed (user never confirmed)', async () => {
    const { svc } = mk({ fetchImpl: router(two), handOff: async () => { throw new HandOffError('not_confirmed'); } });
    expect(await screenExported(svc)).toBe(false);
  });
  test('a photo whose url is null (object missing) is reported, not fatal; the rest is archived', async () => {
    const f = router([two[0], { id: 'c', plant_id: 'p', taken_at: 't', url: null, expires_at: null, file: '3.jpg' }]);
    const { svc, handOff } = mk({ fetchImpl: f });
    const r = await svc.exportData('json');
    expect(r).toMatchObject({ complete: true, photoCount: 1, photosMissing: 1 });
    expect(Object.keys(readZip(handOff.mock.calls[0][0].bytes)).sort()).toEqual(['export.json', 'photos/a_1.jpg']);
  });
  test('C2: photos listed but every url is null (nothing saved) -> photos_none, nothing handed over, gate closed', async () => {
    const nulls = [0, 1].map((i) => ({ id: `n${i}`, plant_id: 'p', taken_at: 't', url: null, expires_at: null, file: `${i}.jpg` }));
    const { svc, handOff } = mk({ fetchImpl: router(nulls) });
    await expect(svc.exportData('json')).rejects.toMatchObject({ code: 'photos_none', total: 2 });
    expect(handOff).not.toHaveBeenCalled();
    expect(await screenExported(svc)).toBe(false);
  });
  test('C2: an EMPTY photo list is fine (nothing to lose): complete with 0 photos', async () => {
    const { svc, handOff } = mk({ fetchImpl: router([]) });
    expect(await svc.exportData('json')).toMatchObject({ complete: true, photoCount: 0, photosMissing: 0 });
    expect(handOff).toHaveBeenCalledTimes(1);
  });
  test('C1: a non-photo error (zip writer: archive too large / OOM) is photos_archive with NO counts, never "0 of N failed"', async () => {
    const zip = jest.spyOn(require('../export/zip'), 'buildStoredZip').mockImplementation(() => { throw new Error('archive too large'); });
    try {
      const { svc, handOff } = mk();
      const e = await svc.exportData('json').catch((x) => x);
      expect(e).toMatchObject({ code: 'photos_archive' });
      expect(e.failed).toBeUndefined();
      expect(handOff).not.toHaveBeenCalled();
    } finally { zip.mockRestore(); }
  });
  test('size cap through the real caller: photos over the cap -> photos_too_large, nothing handed over', async () => {
    const big = (u: string) => ({ ...photoRes(), headers: { get: (h: string) => (h.toLowerCase() === 'content-type' ? 'image/jpeg' : h.toLowerCase() === 'content-length' ? String(200 * 1024 * 1024) : null) } }) as unknown as Response;
    const { svc, handOff } = mk({ fetchImpl: router(two, big) });
    await expect(svc.exportData('json')).rejects.toMatchObject({ code: 'photos_too_large' });
    expect(handOff).not.toHaveBeenCalled();
  });
  test('CSV is handed over but is never complete (no photos inside): it cannot open the gate', async () => {
    const f = jest.fn().mockResolvedValue({ status: 200, headers: { get: () => 'application/zip' }, arrayBuffer: async () => new Uint8Array([80, 75, 3, 4]).buffer });
    const { svc, handOff } = mk({ fetchImpl: f });
    const r = await svc.exportData('csv');
    expect(handOff).toHaveBeenCalledTimes(1);
    expect(r).toMatchObject({ complete: false, photoCount: null });
  });
});

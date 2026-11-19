// Real PlantsService read path + delete + photo objects (4.A4c). Fake fetch only: NOT run against a backend or a phone.
// FR-A06 (list, detail, 168 hourly points, gaps), FR-A04 (fields read back), FR-A05 (no cap, paged), FR-A08 + NFR-07 (delete_plant, photo objects), NFR-06.
import { createRealPlants } from '../plants/realPlants';
import { PlantsError } from '../plants/types';
import { buildPhotoPath, isPhotoPath } from '../plants/photoPath';
import { UID as FUID, PL as FPL, GOOD_PATHS, BAD_PATHS } from './photoPathFixtures';

const NOW = new Date('2026-11-19T10:30:00Z');
const UID = '11111111-1111-4111-8111-111111111111';
const P1 = '22222222-2222-4222-8222-222222222222';
const U1 = '33333333-3333-4333-8333-333333333333';
const row = (o: Record<string, unknown> = {}) => ({ plant_id: P1, name: 'Basil', location_type: 'house', area: 'Kitchen', soil_type: 'potting', device_id: 'd1', device_name: 'Nil-A1B2C3', last_seen_at: '2026-11-19T10:00:00Z', open_alerts: ['too_dry'], dry_threshold_pct: 30, wet_threshold_pct: 80, reading_ts: '2026-11-19T10:00:00Z', moisture_pct: 22.5, temp_c: 21, rh_pct: 50, lux: 900, vbat_mv: 3700, ...o });
const hr = (iso: string, m: number) => ({ hour: iso, n: 4, moisture_avg: m, moisture_min: m - 1, moisture_max: m + 1, temp_avg: 20, rh_avg: 50, lux_avg: 100, vbat_min_mv: 3600 });
const res = (status: number, body: unknown) => ({ status, json: async () => body }) as unknown as Response;
type Handler = (url: string, init: RequestInit) => Response | Promise<Response>;
const mk = (h: Handler, token: string | null = 'jwt') => {
  const f = jest.fn(async (u: any, i: any) => h(String(u), i));
  const svc = createRealPlants({ baseUrl: 'https://x.supabase.co/', publishableKey: 'pub', getAccessToken: async () => token, handOff: async () => undefined, now: () => NOW, fetchImpl: f as any });
  return { svc, f };
};

describe('listPlants', () => {
  test('maps plant_status rows (FR-A04 fields, alerts, latest), sends the user JWT + key, own rows via RLS only', async () => {
    const { svc, f } = mk(() => res(200, [row(), row({ plant_id: U1, name: 'Fern', device_id: null, reading_ts: null, open_alerts: null, location_type: 'garden', soil_type: 'peat', area: null })]));
    const l = await svc.listPlants();
    expect(l).toHaveLength(2);
    expect(l[0]).toMatchObject({ id: P1, name: 'Basil', locationType: 'house', area: 'Kitchen', soilType: 'potting', openAlerts: ['too_dry'], dryThresholdPct: 30, latest: { moisturePct: 22.5, vbatMv: 3700 } });
    expect(l[1]).toMatchObject({ deviceId: null, latest: null, openAlerts: [], area: null, locationType: 'garden', soilType: 'peat' });
    const [url, init] = f.mock.calls[0] as [string, any];
    expect(url).toMatch(/^https:\/\/x\.supabase\.co\/rest\/v1\/plant_status\?/);
    expect(init.headers).toMatchObject({ Authorization: 'Bearer jwt', apikey: 'pub' });
  });
  test('empty account -> empty list (not an error)', async () => { expect(await mk(() => res(200, [])).svc.listPlants()).toEqual([]); });
  test('more than 1000 plants are paged, no cap (FR-A02)', async () => {
    const page = (n: number, off: number) => Array.from({ length: n }, (_, i) => row({ plant_id: `00000000-0000-4000-8000-${String(off + i).padStart(12, '0')}`, name: `P${off + i}` }));
    const { svc, f } = mk((_u, i) => res(200, (i.headers as any).Range === '0-999' ? page(1000, 0) : page(5, 1000)));
    expect(await svc.listPlants()).toHaveLength(1005);
    expect(f).toHaveBeenCalledTimes(2);
  });
  test('errors: network, 500, 401, non-array body, bad row, no token', async () => {
    await expect(mk(() => { throw new TypeError('Network request failed'); }).svc.listPlants()).rejects.toMatchObject({ code: 'network' });
    await expect(mk(() => res(500, {})).svc.listPlants()).rejects.toMatchObject({ code: 'network' });
    await expect(mk(() => res(401, { code: 'PGRST301' })).svc.listPlants()).rejects.toMatchObject({ code: 'unknown' });
    await expect(mk(() => res(200, { message: 'x' })).svc.listPlants()).rejects.toMatchObject({ code: 'unknown' });
    await expect(mk(() => res(200, [row({ location_type: 'moon' })])).svc.listPlants()).rejects.toMatchObject({ code: 'unknown' });
    const none = mk(() => res(200, []), null);
    await expect(none.svc.listPlants()).rejects.toBeInstanceOf(PlantsError);
    expect(none.f).not.toHaveBeenCalled();
  });
});

describe('getPlantDetail: 168-hour grid with null gaps (C3)', () => {
  const det = (hourly: unknown[], plants: unknown[] = [row()]) => mk((u) => res(200, u.includes('readings_hourly') ? hourly : plants));
  test('missing hours yield 168 points with null gaps; present hours keep their values; oldest first, last = current UTC hour', async () => {
    const { svc } = det([hr('2026-11-19T10:00:00Z', 40), hr('2026-11-19T07:00:00Z', 35), hr('2026-11-12T11:00:00Z', 50)]);
    const d = await svc.getPlantDetail(P1);
    expect(d.hourly).toHaveLength(168);
    expect(d.hourly[167].hour).toBe('2026-11-19T10:00:00.000Z');
    expect(d.hourly[0].hour).toBe('2026-11-12T11:00:00.000Z');
    expect(d.hourly[167]).toMatchObject({ moistureAvg: 40, n: 4 });
    expect(d.hourly[164]).toMatchObject({ moistureAvg: 35 });
    expect(d.hourly[0]).toMatchObject({ moistureAvg: 50 });
    expect(d.hourly[166]).toMatchObject({ n: null, moistureAvg: null, tempAvg: null, vbatMinMv: null });
    expect(d.hourly.filter((p) => p.n === null)).toHaveLength(165);
  });
  test('no readings at all -> 168 gaps; a sensor-less plant still returns detail', async () => {
    const d = await det([], [row({ device_id: null, reading_ts: null })]).svc.getPlantDetail(P1);
    expect(d.hourly).toHaveLength(168);
    expect(d.hourly.every((p) => p.n === null)).toBe(true);
    expect(d.plant.latest).toBeNull();
  });
  test('row outside the window or malformed is ignored; null fields inside a row stay null (sensor failed)', async () => {
    const { svc } = det([hr('2026-11-12T10:00:00Z', 1), { ...hr('2026-11-19T09:00:00Z', 30), temp_avg: null }, { hour: 'garbage', n: 1 }]);
    const d = await svc.getPlantDetail(P1);
    expect(d.hourly).toHaveLength(168);
    expect(d.hourly.filter((p) => p.n !== null)).toHaveLength(1);
    expect(d.hourly[166]).toMatchObject({ n: 4, moistureAvg: 30, tempAvg: null });
  });
  test('queries only this plant, from the window start (7 days, FR-A06)', async () => {
    const { svc, f } = det([]);
    await svc.getPlantDetail(P1);
    const urls = f.mock.calls.map((c) => decodeURIComponent(String(c[0])));
    expect(urls.some((u) => u.includes(`plant_status`) && u.includes(`plant_id=eq.${P1}`))).toBe(true);
    expect(urls.some((u) => u.includes('readings_hourly') && u.includes(`plant_id=eq.${P1}`) && u.includes('hour=gte.2026-11-12T11:00:00.000Z'))).toBe(true);
  });
  test('unknown or foreign plant (RLS returns no row) and a non-uuid id -> not_found, no hourly query for the id', async () => {
    await expect(det([], []).svc.getPlantDetail(P1)).rejects.toMatchObject({ code: 'not_found' });
    const { svc, f } = det([]);
    await expect(svc.getPlantDetail("x&select=*")).rejects.toMatchObject({ code: 'not_found' });
    expect(f).not.toHaveBeenCalled();
  });
  test('network error on the hourly call fails the whole detail (no half grid)', async () => {
    const { svc } = mk((u) => { if (u.includes('readings_hourly')) throw new TypeError('x'); return res(200, [row()]); });
    await expect(svc.getPlantDetail(P1)).rejects.toMatchObject({ code: 'network' });
  });
});

describe('listPhotos (FR-A05)', () => {
  test('maps rows, oldest first query, empty list ok, bad row rejects', async () => {
    const { svc, f } = mk(() => res(200, [{ id: 'i1', plant_id: P1, taken_at: '2026-11-01T00:00:00Z', storage_path: `${UID}/${P1}/a.jpg` }]));
    expect(await svc.listPhotos(P1)).toEqual([{ id: 'i1', plantId: P1, takenAt: '2026-11-01T00:00:00Z', storagePath: `${UID}/${P1}/a.jpg` }]);
    expect(String(f.mock.calls[0][0])).toContain('order=taken_at.asc');
    expect(await mk(() => res(200, [])).svc.listPhotos(P1)).toEqual([]);
    await expect(mk(() => res(200, [{ id: 'i1' }])).svc.listPhotos(P1)).rejects.toMatchObject({ code: 'unknown' });
  });
});

describe('deletePlant + removePhotoObjects (C2, FR-A08, NFR-07)', () => {
  const paths = [`${UID}/${P1}/a.jpg`, `${UID}/${P1}/b.png`];
  test('deletePlant calls rpc delete_plant with p_plant and returns the photo paths', async () => {
    const { svc, f } = mk(() => res(200, { plant_id: P1, photo_paths: paths, deleted: {} }));
    expect(await svc.deletePlant(P1)).toEqual({ photoPaths: paths });
    const [url, init] = f.mock.calls[0] as [string, any];
    expect(url).toBe('https://x.supabase.co/rest/v1/rpc/delete_plant');
    expect(init.method).toBe('POST'); expect(JSON.parse(init.body)).toEqual({ p_plant: P1 });
  });
  test('deletePlant errors: foreign plant (P0002) -> not_found; network; answer without photo_paths is an error, not "no photos"', async () => {
    await expect(mk(() => res(404, { code: 'P0002', message: 'plant not found' })).svc.deletePlant(P1)).rejects.toMatchObject({ code: 'not_found' });
    await expect(mk(() => res(400, { code: 'P0002' })).svc.deletePlant(P1)).rejects.toMatchObject({ code: 'not_found' });
    await expect(mk(() => { throw new TypeError('x'); }).svc.deletePlant(P1)).rejects.toMatchObject({ code: 'network' });
    await expect(mk(() => res(200, { plant_id: P1 })).svc.deletePlant(P1)).rejects.toMatchObject({ code: 'unknown' });
    await expect(mk(() => res(200, { photo_paths: [1] })).svc.deletePlant(P1)).rejects.toMatchObject({ code: 'unknown' });
  });
  test('deletePlant removes nothing from storage by itself (cleanup is a separate step)', async () => {
    const { svc, f } = mk(() => res(200, { photo_paths: paths }));
    await svc.deletePlant(P1);
    expect(f.mock.calls.some((c) => String(c[0]).includes('/storage/'))).toBe(false);
  });
  test('removePhotoObjects removes every returned path from bucket plant-photos', async () => {
    const { svc, f } = mk(() => res(200, paths.map((name) => ({ name }))));
    await svc.removePhotoObjects(paths);
    const [url, init] = f.mock.calls[0] as [string, any];
    expect(url).toBe('https://x.supabase.co/storage/v1/object/plant-photos');
    expect(init.method).toBe('DELETE'); expect(JSON.parse(init.body)).toEqual({ prefixes: paths });
  });
  test('150 paths go in two calls of 100 + 50; every path is sent exactly once', async () => {
    const many = Array.from({ length: 150 }, (_, i) => `${UID}/${P1}/f${i}.jpg`);
    const { svc, f } = mk(() => res(200, []));
    await svc.removePhotoObjects(many);
    const sent = f.mock.calls.flatMap((c) => JSON.parse((c[1] as any).body).prefixes);
    expect(f).toHaveBeenCalledTimes(2); expect(sent).toEqual(many);
  });
  test('empty list -> no call; storage failure rejects with every path as leftover (retry keeps the full list)', async () => {
    const e = mk(() => res(200, [])); await e.svc.removePhotoObjects([]); expect(e.f).not.toHaveBeenCalled();
    await expect(mk(() => res(500, {})).svc.removePhotoObjects(paths)).rejects.toMatchObject({ code: 'network', leftover: paths });
    await expect(mk(() => { throw new TypeError('x'); }).svc.removePhotoObjects(paths)).rejects.toMatchObject({ code: 'network', leftover: paths });
  });
  test('mixed batch (C1): well-formed paths are removed, the malformed one is reported as leftover, retry with the leftover only never touches the good ones', async () => {
    const odd = `${UID}/${P1}/sub/legacy.jpg`;
    const { svc, f } = mk(() => res(200, []));
    await expect(svc.removePhotoObjects([paths[0], odd, paths[1]])).rejects.toMatchObject({ code: 'unknown', leftover: [odd] });
    expect(f).toHaveBeenCalledTimes(1);
    expect(JSON.parse((f.mock.calls[0][1] as any).body).prefixes).toEqual(paths);
    // second chunk fails: the removed first chunk is not in leftover
    const many = Array.from({ length: 150 }, (_, i) => `${UID}/${P1}/f${i}.jpg`);
    let n = 0;
    const g = mk(() => (n++ === 0 ? res(200, []) : res(500, {})));
    await expect(g.svc.removePhotoObjects([...many, odd])).rejects.toMatchObject({ code: 'network', leftover: [...many.slice(100), odd] });
  });
  test('only malformed paths: nothing is sent, all are leftover', async () => {
    const odd = `${UID}/../x/a.jpg`;
    const { svc, f } = mk(() => res(200, []));
    await expect(svc.removePhotoObjects([odd])).rejects.toMatchObject({ leftover: [odd] });
    expect(f).not.toHaveBeenCalled();
  });
});

describe('photo path contract <uid>/<plant_id>/<uuid>.<ext> (shared fixtures)', () => {
  test('every good fixture passes for its uid, every bad one fails', () => {
    for (const [why, p] of GOOD_PATHS) expect(isPhotoPath(p, FUID)).toBe(true);
    for (const [why, p] of BAD_PATHS) expect([why, isPhotoPath(p, FUID)]).toEqual([why, false]);
  });
  test('builder produces exactly 3 segments and rejects what the guard rejects', () => {
    const p = buildPhotoPath(UID, P1, U1, '.JPG');
    expect(p).toBe(`${UID}/${P1}/${U1}.jpg`);
    expect(isPhotoPath(p, UID)).toBe(true);
    expect(isPhotoPath(p, U1)).toBe(false);
    expect(() => buildPhotoPath(UID, P1, U1, 'exe')).toThrow();
    expect(() => buildPhotoPath(UID, `${P1}/x`, U1, 'jpg')).toThrow();
  });
});

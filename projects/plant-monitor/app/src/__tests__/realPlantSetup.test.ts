// Real PlantSetupService (4.A4c): plants insert + devices.plant_id link, through a fake fetch. No network, no backend.
import { createRealPlantSetup, noPhotoSource, unconfiguredPlantSetup } from '../provisioning/realPlantSetup';
import { PlantSetupError, type PlantDetails } from '../provisioning/types';

const BASE = 'https://proj.example.test';
const KEY = 'pub-key';
const TOKEN = 'user-jwt';
const USER = '11111111-1111-4111-8111-111111111111';
const DEVICE = '22222222-2222-4222-8222-222222222222';
const PLANT = '33333333-3333-4333-8333-333333333333';
const details: PlantDetails = { name: '  Basil  ', location: 'balcony', area: 'Kitchen window', soil: 'garden', species: '', city: ' Berlin ' };

const res = (status: number, body: unknown) => ({ status, json: async () => body }) as unknown as Response;
type Route = (url: string, init: RequestInit) => Response | Promise<Response> | never;
/** routes by method + path; anything else fails the test */
const backend = (routes: Record<string, Route>) => jest.fn(async (url: string, init: RequestInit) => {
  const u = new URL(url);
  const key = `${init.method ?? 'GET'} ${u.pathname}`;
  const r = routes[key];
  if (!r) throw new Error(`unexpected call ${key}`);
  return r(url, init);
});
const okInsert: Route = () => res(201, [{ id: PLANT, owner_id: USER, name: 'Basil' }]);
const okLink: Route = () => res(200, [{ id: DEVICE, plant_id: PLANT }]);
const mk = (fetchImpl: jest.Mock, o: { token?: string | null; userId?: string | null } = {}) => createRealPlantSetup({
  baseUrl: `${BASE}/`, publishableKey: KEY,
  getAccessToken: async () => (o.token === undefined ? TOKEN : o.token),
  getUserId: async () => (o.userId === undefined ? USER : o.userId),
  fetchImpl: fetchImpl as unknown as typeof fetch,
});
const bodyOf = (call: unknown[]) => JSON.parse(String((call[1] as RequestInit).body));

describe('createPlant: happy path', () => {
  test('inserts the plant as the signed-in owner, then links the device to it, and returns the new id', async () => {
    const f = backend({ 'POST /rest/v1/plants': okInsert, [`PATCH /rest/v1/devices`]: okLink });
    const { plantId } = await mk(f).createPlant(DEVICE, details, null);
    expect(plantId).toBe(PLANT);
    expect(f).toHaveBeenCalledTimes(2);
    const [insUrl, insInit] = f.mock.calls[0] as [string, RequestInit];
    expect(insUrl).toBe(`${BASE}/rest/v1/plants`);
    expect(insInit.headers).toMatchObject({ apikey: KEY, Authorization: `Bearer ${TOKEN}`, Prefer: 'return=representation' });
    expect(bodyOf(f.mock.calls[0])).toEqual({ owner_id: USER, name: 'Basil', location_type: 'balcony', area: 'Kitchen window', soil_type: 'garden', species: null, city: 'Berlin' });
    const [linkUrl, linkInit] = f.mock.calls[1] as [string, RequestInit];
    expect(linkUrl).toBe(`${BASE}/rest/v1/devices?id=eq.${DEVICE}`);
    expect(linkInit.method).toBe('PATCH');
    expect(bodyOf(f.mock.calls[1])).toEqual({ plant_id: PLANT });
  });

  test('an empty area stays null, not an empty string', async () => {
    const f = backend({ 'POST /rest/v1/plants': okInsert, 'PATCH /rest/v1/devices': okLink });
    await mk(f).createPlant(DEVICE, { ...details, area: '  ' }, null);
    expect(bodyOf(f.mock.calls[0]).area).toBeNull();
  });
});

describe('createPlant: failures never report a saved plant', () => {
  test('plant insert refused (403): throws, and the device is not touched', async () => {
    const f = backend({ 'POST /rest/v1/plants': () => res(403, { code: '42501' }) });
    await expect(mk(f).createPlant(DEVICE, details, null)).rejects.toBeInstanceOf(PlantSetupError);
    expect(f).toHaveBeenCalledTimes(1);
  });

  test('insert answers without an id: throws, nothing linked', async () => {
    const f = backend({ 'POST /rest/v1/plants': () => res(201, []) });
    await expect(mk(f).createPlant(DEVICE, details, null)).rejects.toBeInstanceOf(PlantSetupError);
    expect(f).toHaveBeenCalledTimes(1);
  });

  test('device not visible under RLS (PATCH answers []): throws and removes the new plant again', async () => {
    const f = backend({ 'POST /rest/v1/plants': okInsert, 'PATCH /rest/v1/devices': () => res(200, []), 'DELETE /rest/v1/plants': () => res(204, null) });
    await expect(mk(f).createPlant(DEVICE, details, null)).rejects.toBeInstanceOf(PlantSetupError);
    const del = f.mock.calls.find((c) => (c[1] as RequestInit).method === 'DELETE');
    expect(del?.[0]).toBe(`${BASE}/rest/v1/plants?id=eq.${PLANT}`);
  });

  test('link fails with a network error: throws and still tries the clean-up', async () => {
    const f = jest.fn(async (url: string, init: RequestInit) => {
      if (init.method === 'PATCH') throw new TypeError('network down');
      if (init.method === 'DELETE') return res(204, null);
      return res(201, [{ id: PLANT }]);
    });
    await expect(mk(f).createPlant(DEVICE, details, null)).rejects.toBeInstanceOf(PlantSetupError);
    expect(f.mock.calls.some((c) => (c[1] as RequestInit).method === 'DELETE')).toBe(true);
  });

  test('clean-up also fails: still throws PlantSetupError (the orphan is a known gap, see the PR)', async () => {
    const f = backend({ 'POST /rest/v1/plants': okInsert, 'PATCH /rest/v1/devices': () => res(500, {}), 'DELETE /rest/v1/plants': () => res(500, {}) });
    await expect(mk(f).createPlant(DEVICE, details, null)).rejects.toBeInstanceOf(PlantSetupError);
  });
});

describe('createPlant: refusals before any request', () => {
  test('a photo is refused, never dropped silently', async () => {
    const f = jest.fn();
    await expect(mk(f).createPlant(DEVICE, details, 'file:///p.jpg')).rejects.toMatchObject({ message: 'photo_unsupported' });
    expect(f).not.toHaveBeenCalled();
  });

  test('a device id that is not a uuid (e.g. the fake "device-1") is refused', async () => {
    const f = jest.fn();
    await expect(mk(f).createPlant('device-1', details, null)).rejects.toBeInstanceOf(PlantSetupError);
    expect(f).not.toHaveBeenCalled();
  });

  test('signed out (no user id) is refused', async () => {
    const f = jest.fn();
    await expect(mk(f, { userId: null }).createPlant(DEVICE, details, null)).rejects.toMatchObject({ message: 'not_signed_in' });
    expect(f).not.toHaveBeenCalled();
  });

  test('no access token: no request leaves the phone', async () => {
    const f = jest.fn();
    await expect(mk(f, { token: null }).createPlant(DEVICE, details, null)).rejects.toBeInstanceOf(PlantSetupError);
    expect(f).not.toHaveBeenCalled();
  });
});

describe('unconfigured build and photo source', () => {
  test('unconfiguredPlantSetup says not_configured and never pretends to save', async () => {
    await expect(unconfiguredPlantSetup.createPlant(DEVICE, details, null)).rejects.toMatchObject({ message: 'not_configured' });
  });
  test('noPhotoSource reports unsupported and returns no photo', async () => {
    expect(noPhotoSource.supported).toBe(false);
    expect(await noPhotoSource.takePhoto()).toBeNull();
    expect(await noPhotoSource.pickFromLibrary()).toBeNull();
  });
});

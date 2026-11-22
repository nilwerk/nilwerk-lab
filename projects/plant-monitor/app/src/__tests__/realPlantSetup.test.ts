// Real PlantSetupService (4.A4c): read the sensor's plant, then one RPC (plant insert + device link, atomic). Through a fake fetch. No network, no backend.
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
const mk = (fetchImpl: jest.Mock, o: { token?: string | null; userId?: string | null } = {}) => createRealPlantSetup({
  baseUrl: `${BASE}/`, publishableKey: KEY,
  getAccessToken: async () => (o.token === undefined ? TOKEN : o.token),
  getUserId: async () => (o.userId === undefined ? USER : o.userId),
  fetchImpl: fetchImpl as unknown as typeof fetch,
});
const bodyOf = (call: unknown[]) => JSON.parse(String((call[1] as RequestInit).body));

const RPC = `${BASE}/rest/v1/rpc/create_plant_and_link_device`;
const DEVICE_ROW = (plant: string | null) => res(200, [{ plant_id: plant }]);
const getDevice = (plant: string | null): Route => () => DEVICE_ROW(plant);
const rpcOk: Route = () => res(200, PLANT);
const isRpc = (c: unknown[]) => String(c[0]) === RPC;
const rpcBody = (f: jest.Mock) => bodyOf(f.mock.calls.find(isRpc) as unknown[]);

describe('createPlant: happy path (one atomic RPC after a read)', () => {
  test('reads the sensor, then calls create_plant_and_link_device once with the owner-trimmed fields', async () => {
    const f = backend({ [`GET /rest/v1/devices`]: getDevice(null), 'POST /rest/v1/rpc/create_plant_and_link_device': rpcOk });
    const out = await mk(f).createPlant(DEVICE, details, null);
    expect(out).toEqual({ status: 'saved', plantId: PLANT });
    expect(f).toHaveBeenCalledTimes(2);
    const [getUrl] = f.mock.calls[0] as [string, RequestInit];
    expect(getUrl).toBe(`${BASE}/rest/v1/devices?select=plant_id&id=eq.${DEVICE}`);
    const [rpcUrl, rpcInit] = f.mock.calls[1] as [string, RequestInit];
    expect(rpcUrl).toBe(RPC);
    expect(rpcInit.method).toBe('POST');
    expect(rpcInit.headers).toMatchObject({ apikey: KEY, Authorization: `Bearer ${TOKEN}` });
    expect(rpcBody(f)).toEqual({ p_device: DEVICE, p_name: 'Basil', p_location_type: 'balcony', p_area: 'Kitchen window', p_soil_type: 'garden', p_species: null, p_city: 'Berlin', p_move: false });
  });

  test('an empty area stays null, not an empty string', async () => {
    const f = backend({ 'GET /rest/v1/devices': getDevice(null), 'POST /rest/v1/rpc/create_plant_and_link_device': rpcOk });
    await mk(f).createPlant(DEVICE, { ...details, area: '  ' }, null);
    expect(rpcBody(f).p_area).toBeNull();
  });
});

describe('createPlant: a sensor that already has a plant is never moved silently', () => {
  test('returns already_linked and writes nothing (no RPC, no PATCH)', async () => {
    const OTHER = '44444444-4444-4444-8444-444444444444';
    const f = backend({ 'GET /rest/v1/devices': getDevice(OTHER) });
    await expect(mk(f).createPlant(DEVICE, details, null)).resolves.toEqual({ status: 'already_linked' });
    expect(f).toHaveBeenCalledTimes(1);
    expect(f.mock.calls.some(isRpc)).toBe(false);
  });

  test('with moveFromCurrent: calls the RPC with p_move true (the user chose to move)', async () => {
    const OTHER = '44444444-4444-4444-8444-444444444444';
    const f = backend({ 'GET /rest/v1/devices': getDevice(OTHER), 'POST /rest/v1/rpc/create_plant_and_link_device': rpcOk });
    await expect(mk(f).createPlant(DEVICE, details, null, { moveFromCurrent: true })).resolves.toEqual({ status: 'saved', plantId: PLANT });
    expect(rpcBody(f).p_move).toBe(true);
  });
});

describe('createPlant: failures never report a saved plant', () => {
  test('device not visible under RLS (GET answers []): throws, no RPC', async () => {
    const f = backend({ 'GET /rest/v1/devices': () => res(200, []) });
    await expect(mk(f).createPlant(DEVICE, details, null)).rejects.toMatchObject({ message: 'device_not_found' });
    expect(f.mock.calls.some(isRpc)).toBe(false);
  });

  test('RPC refused (403): throws; one statement, so there is nothing to clean up', async () => {
    const f = backend({ 'GET /rest/v1/devices': getDevice(null), 'POST /rest/v1/rpc/create_plant_and_link_device': () => res(403, { code: '42501' }) });
    await expect(mk(f).createPlant(DEVICE, details, null)).rejects.toBeInstanceOf(PlantSetupError);
    expect(f).toHaveBeenCalledTimes(2);
  });

  test('RPC network error: throws', async () => {
    const f = jest.fn(async (url: string, init: RequestInit) => {
      if (init.method === 'GET') return DEVICE_ROW(null);
      throw new TypeError('network down');
    });
    await expect(mk(f).createPlant(DEVICE, details, null)).rejects.toBeInstanceOf(PlantSetupError);
  });

  test('RPC answers something that is not a plant id: throws', async () => {
    const f = backend({ 'GET /rest/v1/devices': getDevice(null), 'POST /rest/v1/rpc/create_plant_and_link_device': () => res(200, { id: PLANT }) });
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

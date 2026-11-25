// espAdapter + claimApi glue against a mocked library / fake fetch (no native module, no network). 4.A3b slice 1.
import { PermissionsAndroid, Platform } from 'react-native';
import { createEspAdapter } from '../provisioning/espAdapter';
import { createFetchClaimApi, ClaimApiError } from '../provisioning/claimApi';
import { ProvisioningError } from '../provisioning/types';

type Lib = Parameters<typeof createEspAdapter>[0] extends (() => infer L) | undefined ? L : never;

function mockLib() {
  const calls: unknown[][] = [];
  class ESPDevice {
    name: string; transport: string; security: number;
    constructor(o: { name: string; transport: string; security: number }) { this.name = o.name; this.transport = o.transport; this.security = o.security; }
    async connect(...a: unknown[]) { calls.push(['connect', this.name, ...a]); }
    async getPrimaryServiceUuid() { return 'B53672DD-5227-40A0-8B6F-6F836F8A584C'.toLowerCase(); }
    async scanWifiList() { return [{ ssid: 'A', rssi: -50, auth: 0 }, { ssid: 'B', rssi: -60, auth: 3 }]; }
    async sendData(p: string, d: string) { calls.push(['sendData', p, d]); return '{"v":1}'; }
    async provision(s: string, p: string) { calls.push(['provision', s, p]); return { status: 'ok' }; }
    disconnect() { calls.push(['disconnect', this.name]); }
  }
  const lib = {
    ESPDevice, ESPTransport: { ble: 'ble', softap: 'softap' }, ESPSecurity: { unsecure: 0, secure: 1, secure2: 2 },
    ESPProvisionManager: { searchESPDevices: async (...a: unknown[]) => { calls.push(['search', ...a]); return [new ESPDevice({ name: 'NW-d4e5f6', transport: 'ble', security: 2 })]; } },
  } as unknown as Lib;
  return { lib, calls };
}

describe('espAdapter', () => {
  const origOS = Platform.OS;
  afterEach(() => { Object.defineProperty(Platform, 'OS', { get: () => origOS, configurable: true }); jest.restoreAllMocks(); });

  test('search uses BLE + security 2 + the name prefix and reports the primary service UUID', async () => {
    const m = mockLib();
    const a = createEspAdapter(() => m.lib);
    expect(await a.search('NW-')).toEqual([{ name: 'NW-d4e5f6', serviceUuid: 'b53672dd-5227-40a0-8b6f-6f836f8a584c' }]);
    expect(m.calls[0]).toEqual(['search', 'NW-', 'ble', 2]);
  });
  test('connect passes PoP and SRP user name (security 2 needs both); wifi, sendData, provision, disconnect delegate', async () => {
    const m = mockLib();
    const a = createEspAdapter(() => m.lib);
    await a.search('NW-');
    await a.connect('NW-d4e5f6', '7KQ2M9XD', 'wifiprov');
    expect(m.calls).toContainEqual(['connect', 'NW-d4e5f6', '7KQ2M9XD', null, 'wifiprov']);
    expect(await a.scanWifi()).toEqual([{ ssid: 'A', rssi: -50, secure: false }, { ssid: 'B', rssi: -60, secure: true }]);
    await a.sendData('nw-claim', '{}'); await a.provision('HomeNet', 'pw-12345678'); await a.disconnect();
    expect(m.calls).toContainEqual(['sendData', 'nw-claim', '{}']);
    expect(m.calls).toContainEqual(['provision', 'HomeNet', 'pw-12345678']);
    expect(m.calls).toContainEqual(['disconnect', 'NW-d4e5f6']);
  });
  test('calls before connect fail with not_found; a missing native module (Expo Go / web) is not_available', async () => {
    const a = createEspAdapter(() => mockLib().lib);
    await expect(a.scanWifi()).rejects.toMatchObject({ code: 'not_found' });
    const b = createEspAdapter(() => { throw new Error('native module missing'); });
    await expect(b.ensureReady()).rejects.toBeInstanceOf(ProvisioningError);
    await expect(b.ensureReady()).rejects.toMatchObject({ code: 'not_available' });
  });
  test('Android 12+ asks BLUETOOTH_SCAN + CONNECT, denial is permission_denied; Android 11 asks location', async () => {
    Object.defineProperty(Platform, 'OS', { get: () => 'android', configurable: true });
    const spy = jest.spyOn(PermissionsAndroid, 'requestMultiple').mockResolvedValue({ 'android.permission.BLUETOOTH_SCAN': 'granted', 'android.permission.BLUETOOTH_CONNECT': 'denied' } as never);
    const ver = jest.spyOn(Platform, 'Version', 'get').mockReturnValue(34);
    const a = createEspAdapter(() => mockLib().lib);
    await expect(a.ensureReady()).rejects.toMatchObject({ code: 'permission_denied' });
    expect(spy.mock.calls[0][0]).toEqual(['android.permission.BLUETOOTH_SCAN', 'android.permission.BLUETOOTH_CONNECT']);
    ver.mockReturnValue(30);
    spy.mockResolvedValue({ 'android.permission.ACCESS_FINE_LOCATION': 'granted' } as never);
    await expect(a.ensureReady()).resolves.toBeUndefined();
    expect(spy.mock.calls[1][0]).toEqual(['android.permission.ACCESS_FINE_LOCATION']);
  });
});

// onDisconnected: the drop watch used after a successful apply (bleProvisioning.ts). Its own small fake device, so the mock above stays as it is.
describe('espAdapter onDisconnected wiring', () => {
  type Cb = () => void;
  class WatchDevice {
    static last: WatchDevice | null = null;
    name: string;
    removed = 0;
    private listeners: Cb[] = [];
    constructor(o: { name: string }) { this.name = o.name; WatchDevice.last = this; }
    async connect() { /* connected */ }
    disconnect() { /* dropped */ }
    onDisconnected(cb: Cb) { this.listeners.push(cb); return () => { this.removed += 1; }; }
    fireDisconnect() { this.listeners.forEach((cb) => cb()); }
  }
  const watchLib = { ESPDevice: WatchDevice, ESPTransport: { ble: 'ble' }, ESPSecurity: { secure2: 2 }, ESPProvisionManager: { searchESPDevices: async () => [] } } as unknown as Lib;

  test('before connect there is no device: the subscription is a no-op and never calls back', () => {
    const a = createEspAdapter(() => watchLib);
    const cb = jest.fn();
    const unsub = a.onDisconnected!(cb);
    expect(() => unsub()).not.toThrow();
    expect(cb).not.toHaveBeenCalled();
  });
  test('after connect the callback is registered on the connected device; unsubscribe releases it', async () => {
    const a = createEspAdapter(() => watchLib);
    await a.connect('NW-d4e5f6', 'POP', 'wifiprov');
    const dev = WatchDevice.last!;
    const cb = jest.fn();
    const unsub = a.onDisconnected!(cb);
    dev.fireDisconnect();
    expect(cb).toHaveBeenCalledTimes(1);
    unsub();
    expect(dev.removed).toBe(1);
  });
  test('after disconnect() there is no device again: the subscription is a no-op', async () => {
    const a = createEspAdapter(() => watchLib);
    await a.connect('NW-d4e5f6', 'POP', 'wifiprov');
    await a.disconnect();
    const cb = jest.fn();
    expect(() => a.onDisconnected!(cb)()).not.toThrow();
    expect(cb).not.toHaveBeenCalled();
  });
});

describe('createFetchClaimApi', () => {
  const TOKEN = 'k3J9aBcDeFgHiJkLmNoPqr';
  const res = (status: number, body?: unknown) => ({ status, ok: status >= 200 && status < 300, json: async () => body }) as Response;
  const mk = (f: jest.Mock, token: string | null = 'jwt-1') => createFetchClaimApi({ baseUrl: 'https://x.supabase.co/', publishableKey: 'sb_publishable_x', getAccessToken: async () => token, fetchImpl: f as never });

  test('POST /claim-token with the user JWT and publishable key, returns the token', async () => {
    const f = jest.fn().mockResolvedValue(res(201, { claim_token: TOKEN, expires_at: 'x' }));
    expect((await mk(f).issueClaimToken()).token).toBe(TOKEN);
    expect(f.mock.calls[0][0]).toBe('https://x.supabase.co/functions/v1/claim-token');
    expect(f.mock.calls[0][1]).toMatchObject({ method: 'POST', headers: { apikey: 'sb_publishable_x', Authorization: 'Bearer jwt-1' } });
  });
  test('errors: signed out, 401, 429, 500, network, malformed token; the token never appears in an error', async () => {
    await expect(mk(jest.fn(), null).issueClaimToken()).rejects.toMatchObject({ code: 'unauthorized' });
    for (const [status, c] of [[401, 'unauthorized'], [429, 'rate_limited'], [500, 'server']] as const) await expect(mk(jest.fn().mockResolvedValue(res(status))).issueClaimToken()).rejects.toMatchObject({ code: c });
    await expect(mk(jest.fn().mockRejectedValue(new TypeError('Network request failed'))).issueClaimToken()).rejects.toMatchObject({ code: 'network' });
    const bad = mk(jest.fn().mockResolvedValue(res(201, { claim_token: 'too-short' })));
    await expect(bad.issueClaimToken()).rejects.toBeInstanceOf(ClaimApiError);
    await expect(bad.issueClaimToken()).rejects.not.toThrow(/too-short/);
  });
  test('issue time comes from the server: expires_at minus 15 min; unusable expires_at falls back to the phone clock minus 2 min', async () => {
    const now = Date.now();
    const exp = new Date(now + 15 * 60_000 - 3000).toISOString(); // server clock 3 s "behind" the phone: the server value wins
    const a = await mk(jest.fn().mockResolvedValue(res(201, { claim_token: TOKEN, expires_at: exp }))).issueClaimToken();
    expect(a.issuedAtMs).toBe(Date.parse(exp) - 15 * 60_000);
    for (const bad of ['x', undefined, '1999-01-01T00:00:00Z']) {
      const b = await mk(jest.fn().mockResolvedValue(res(201, { claim_token: TOKEN, expires_at: bad }))).issueClaimToken();
      expect(Math.abs(b.issuedAtMs - (Date.now() - 2 * 60_000))).toBeLessThan(2000);
    }
  });
  test('findClaimedDevice accepts only a row claimed at or after sinceMs (stale / null / garbage claimed_at never confirm)', async () => {
    const since = Date.parse('2026-11-17T10:00:00Z');
    const row = (claimed_at: unknown) => [{ id: 'dev-9', hw_id: 'nw-a1b2c3d4e5f6', claimed_at }];
    const find = (rows: unknown[]) => mk(jest.fn().mockResolvedValue(res(200, rows))).findClaimedDevice('NW-d4e5f6', since);
    expect(await find(row('2026-11-01T08:00:00Z'))).toBeNull(); // mutation check: dropping the claimed_at filter makes this return the old row
    expect(await find(row('2026-11-17T09:59:59Z'))).toBeNull();
    expect(await find(row(null))).toBeNull();
    expect(await find(row('not a date'))).toBeNull();
    expect(await find(row(undefined))).toBeNull();
    expect(await find(row('2026-11-17T10:00:00Z'))).toEqual({ deviceId: 'dev-9', hwId: 'nw-a1b2c3d4e5f6' });
    expect(await find([{ id: 'dev-9', hw_id: 'nw-a1b2c3d4e5f6', claimed_at: '2026-11-01T08:00:00Z' }, { id: 'dev-10', hw_id: 'nw-a1b2c3d4e5f6', claimed_at: '2026-11-17T10:05:00Z' }])).toMatchObject({ deviceId: 'dev-10' });
  });
  test('findClaimedDevice queries the user\'s own rows by the 6-hex suffix and checks the suffix again client side', async () => {
    const f = jest.fn().mockResolvedValue(res(200, [{ id: 'other', hw_id: 'nw-a1b2c3999999', claimed_at: '2026-11-17T10:00:00Z' }, { id: 'dev-9', hw_id: 'nw-a1b2c3d4e5f6', claimed_at: '2026-11-17T10:00:00Z' }]));
    expect(await mk(f).findClaimedDevice('NW-d4e5f6', 0)).toEqual({ deviceId: 'dev-9', hwId: 'nw-a1b2c3d4e5f6' });
    expect(String(f.mock.calls[0][0])).toContain('/rest/v1/devices?select=id,hw_id,claimed_at&hw_id=like.*d4e5f6');
    expect(await mk(jest.fn().mockResolvedValue(res(200, []))).findClaimedDevice('NW-d4e5f6', 0)).toBeNull();
    expect(await mk(jest.fn()).findClaimedDevice('NW-zzzzzz', 0)).toBeNull();
  });
});

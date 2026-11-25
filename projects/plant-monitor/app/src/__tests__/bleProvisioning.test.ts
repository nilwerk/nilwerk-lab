// Real ProvisioningService logic against a scripted fake adapter + fake cloud (no Bluetooth, no network). Contract: docs/interfaces/ble-provisioning.md.
// Requirements: FR-A03, FR-D03, FR-D07, NFR-06. NOT a hardware test: test 5.5 on a real phone is still open.
import { claimedSince } from '../provisioning/claimApi';
import { createBleProvisioning, classifyBleError, NW_PROV_SERVICE_UUID, NW_SRP_USERNAME } from '../provisioning/bleProvisioning';
import type { BleAdapter, BleDevice, BleWifi } from '../provisioning/bleAdapter';
import { ClaimApiError, type ClaimApi } from '../provisioning/claimApi';
import { ProvisioningError, type LinkState, type ProvisioningErrorCode } from '../provisioning/types';

const TOKEN = 'k3J9aBcDeFgHiJkLmNoPqr'; // 22 chars base64url, fake
const NAME = 'NW-d4e5f6';
const POP = '7KQ2M9XD';
const SECRET_WIFI = 'correct-horse';

interface Script { statuses: (object | Error)[]; applyError?: Error; claimReply?: string; connectError?: Error; devices?: BleDevice[]; devicesAfterFail?: BleDevice[]; wifi?: BleWifi[]; /** the sensor drops the BLE link right after the apply */ drop?: boolean }

function makeAdapter(sc: Script) {
  const calls: string[] = [];
  const sent: { endpoint: string; body: string }[] = [];
  let st = 0;
  let searched = 0;
  const listeners = new Set<() => void>();
  const adapter: BleAdapter = {
    onDisconnected(cb) { calls.push('watch'); listeners.add(cb); return () => { calls.push('unwatch'); listeners.delete(cb); }; },
    async ensureReady() { calls.push('ready'); },
    async search() { calls.push('search'); searched += 1; return searched > 1 && sc.devicesAfterFail ? sc.devicesAfterFail : (sc.devices ?? [{ name: NAME, serviceUuid: NW_PROV_SERVICE_UUID }]); },
    async connect(name, pop, user) { calls.push(`connect:${name}:${pop}:${user}`); if (sc.connectError) throw sc.connectError; },
    async scanWifi() { calls.push('scanWifi'); return sc.wifi ?? []; },
    async sendData(endpoint, body) {
      calls.push(`send:${endpoint}`); sent.push({ endpoint, body });
      if (endpoint === 'nw-claim') return sc.claimReply ?? '{"v":1,"ok":true}';
      const next = sc.statuses[Math.min(st++, sc.statuses.length - 1)];
      if (next instanceof Error) throw next;
      return JSON.stringify({ v: 1, reason: null, ...next });
    },
    async provision(ssid, pass) {
      calls.push(`provision:${ssid}:${pass}`);
      if (sc.applyError) throw sc.applyError;
      if (sc.drop) [...listeners].forEach((cb) => cb());
    },
    async disconnect() { calls.push('disconnect'); },
  };
  return { adapter, calls, sent };
}

function makeClaim(over: Partial<ClaimApi> = {}) {
  const calls: string[] = [];
  const claim: ClaimApi = {
    async issueClaimToken() { calls.push('token'); return { token: TOKEN, issuedAtMs: 1000 }; },
    async findClaimedDevice(n) { calls.push(`find:${n}`); return { deviceId: 'dev-1', hwId: 'nw-a1b2c3d4e5f6' }; },
    ...over,
  };
  return { claim, calls };
}

async function setup(sc: Script, claimOver: Partial<ClaimApi> = {}, deps: { maxLinkMs?: number; confirmTries?: number } = {}) {
  const a = makeAdapter(sc);
  const c = makeClaim(claimOver);
  const slept: number[] = [];
  const svc = createBleProvisioning({ adapter: a.adapter, claim: c.claim, sleep: async (ms) => { slept.push(ms); }, ...deps });
  await svc.scan();
  await svc.connect(NAME, POP);
  return { svc, a, c, slept };
}
const REQ = { ssid: 'HomeNet-2G', passphrase: SECRET_WIFI, name: 'Basil on the sill' };
const code = async (p: Promise<unknown>): Promise<ProvisioningErrorCode | 'resolved'> => p.then(() => 'resolved' as const, (e) => (e instanceof ProvisioningError ? e.code : 'not-a-ProvisioningError' as never));

describe('scan: filtered by service UUID and name', () => {
  test('keeps NW-xxxxxx with our UUID or no UUID (iOS), drops other UUIDs and malformed names, dedupes', async () => {
    const { adapter } = makeAdapter({ statuses: [], devices: [
      { name: 'NW-d4e5f6', serviceUuid: NW_PROV_SERVICE_UUID.toUpperCase() },
      { name: 'NW-d4e5f6', serviceUuid: NW_PROV_SERVICE_UUID },
      { name: 'NW-aaaaaa' },
      { name: 'NW-bbbbbb', serviceUuid: '021a9004-0382-4aea-bff4-6b3f1c5adfb4' }, // other ESP provisioning device
      { name: 'NW-xyz' }, { name: 'PROV_123' },
    ] });
    const svc = createBleProvisioning({ adapter, claim: makeClaim().claim });
    expect((await svc.scan()).map((d) => d.name)).toEqual(['NW-aaaaaa', 'NW-d4e5f6']);
  });
  test('permission / bluetooth / missing native module map to the setup error states', async () => {
    for (const [raised, expected] of [
      [new ProvisioningError('permission_denied'), 'permission_denied'], [new ProvisioningError('bluetooth_off'), 'bluetooth_off'],
      [new ProvisioningError('not_available'), 'not_available'],
    ] as const) {
      const a = makeAdapter({ statuses: [] }); a.adapter.ensureReady = async () => { throw raised; };
      expect(await code(createBleProvisioning({ adapter: a.adapter, claim: makeClaim().claim }).scan())).toBe(expected);
    }
    const a = makeAdapter({ statuses: [] }); a.adapter.search = async () => { throw new Error('Bluetooth is powered off'); };
    expect(await code(createBleProvisioning({ adapter: a.adapter, claim: makeClaim().claim }).scan())).toBe('bluetooth_off');
  });
});

describe('connect: security 2 with the label secret', () => {
  test('passes name, PoP and the SRP user name to the adapter; the PoP is not used anywhere else', async () => {
    const { a } = await setup({ statuses: [] });
    expect(a.calls).toContain(`connect:${NAME}:${POP}:${NW_SRP_USERNAME}`);
  });
  test('a wrong secret is wrong_code while the device still advertises', async () => {
    const a = makeAdapter({ statuses: [], connectError: new Error('Security session failed: proof of possession mismatch') });
    const svc = createBleProvisioning({ adapter: a.adapter, claim: makeClaim().claim });
    expect(await code(svc.connect(NAME, 'AAAAAAAA'))).toBe('wrong_code');
  });
  test('5-wrong-secrets rule is the device\'s: when it stops advertising after a failed handshake the app reports setup_closed', async () => {
    const a = makeAdapter({ statuses: [], connectError: new Error('handshake failed'), devicesAfterFail: [] });
    const svc = createBleProvisioning({ adapter: a.adapter, claim: makeClaim().claim });
    await svc.scan();
    expect(await code(svc.connect(NAME, 'AAAAAAAA'))).toBe('setup_closed');
  });
  test('malformed name and library errors', async () => {
    const a = makeAdapter({ statuses: [] });
    const svc = createBleProvisioning({ adapter: a.adapter, claim: makeClaim().claim });
    expect(await code(svc.connect('PROV_1', POP))).toBe('not_found');
    expect(a.calls.some((c) => c.startsWith('connect'))).toBe(false);
    a.adapter.connect = async () => { throw new Error('Bluetooth permission denied'); };
    expect(await code(svc.connect(NAME, POP))).toBe('permission_denied');
    a.adapter.connect = async () => { throw new Error('device not found'); };
    expect(await code(svc.connect(NAME, POP))).toBe('not_found');
    a.adapter.connect = async () => { throw new Error('???'); };
    expect(await code(svc.connect(NAME, POP))).toBe('unknown');
  });
  test('scanWifi and provision need a connected device; disconnect forgets it', async () => {
    const { svc } = await setup({ statuses: [] });
    await svc.disconnect();
    expect(await code(svc.scanWifi())).toBe('not_found');
    expect(await code(svc.provision(REQ, () => undefined))).toBe('not_found');
  });
});

describe('scanWifi', () => {
  test('bars from RSSI, open networks, strongest duplicate wins, empty SSIDs dropped', async () => {
    const { svc } = await setup({ statuses: [], wifi: [
      { ssid: 'Cafe', rssi: -85, secure: false }, { ssid: 'HomeNet-2G', rssi: -80, secure: true }, { ssid: 'HomeNet-2G', rssi: -50, secure: true }, { ssid: '', rssi: -40, secure: true }, { ssid: 'Mid', rssi: -70, secure: true },
    ] });
    expect(await svc.scanWifi()).toEqual([{ ssid: 'HomeNet-2G', bars: 3, secure: true }, { ssid: 'Mid', bars: 2, secure: true }, { ssid: 'Cafe', bars: 1, secure: false }]);
  });
});

describe('provision: claim token handoff and nw-status', () => {
  test('happy path: token, then nw-claim, then apply; states in order; devices row confirmed', async () => {
    const { svc, a, c } = await setup({ statuses: [{ state: 'wifi_connecting' }, { state: 'claiming' }, { state: 'claimed' }] });
    const seen: LinkState[] = [];
    const r = await svc.provision(REQ, (s) => seen.push(s));
    expect(r).toEqual({ deviceId: 'dev-1', hwId: 'nw-a1b2c3d4e5f6' });
    expect(seen).toEqual(['wifi_connecting', 'claiming', 'claimed']);
    // order: cloud token -> nw-claim -> prov-config/apply -> cloud check (no BLE request after the apply)
    const order = [...c.calls.filter((x) => x === 'token'), ...a.calls.filter((x) => /^(send:nw-claim|provision:|send:nw-status)/.test(x))];
    expect(order).toEqual(['token', 'send:nw-claim', `provision:HomeNet-2G:${SECRET_WIFI}`]);
    expect(c.calls).toContain(`find:${NAME}`);
  });
  test('after a successful apply nothing more is sent to the sensor: the library would start a new handshake (lib-2.4.4 session = null)', async () => {
    const { svc, a } = await setup({ statuses: [{ state: 'claimed' }] });
    await svc.provision(REQ, () => undefined);
    const afterApply = a.calls.slice(a.calls.findIndex((x) => x.startsWith('provision:')) + 1);
    expect(afterApply.filter((x) => x.startsWith('send:'))).toEqual([]);
  });
  test('the drop watch is released on success and on failure', async () => {
    const ok = await setup({ statuses: [] });
    await ok.svc.provision(REQ, () => undefined);
    expect(ok.a.calls.filter((x) => x === 'watch')).toEqual(['watch']);
    expect(ok.a.calls.at(-1)).toBe('unwatch');
    const bad = await setup({ statuses: [{ state: 'idle' }], applyError: new Error('Wi-Fi authentication failed') });
    await code(bad.svc.provision(REQ, () => undefined));
    expect(bad.a.calls.at(-1)).toBe('unwatch');
  });
  test('nw-claim body is exactly {v,name,claim_token}; the Wi-Fi passphrase and the PoP never go into it', async () => {
    const { svc, a } = await setup({ statuses: [{ state: 'claimed' }] });
    await svc.provision(REQ, () => undefined);
    const claimMsg = a.sent.find((s) => s.endpoint === 'nw-claim')!;
    expect(JSON.parse(claimMsg.body)).toEqual({ v: 1, name: 'Basil on the sill', claim_token: TOKEN });
    for (const s of a.sent) { expect(s.body).not.toContain(SECRET_WIFI); expect(s.body).not.toContain(POP); }
  });
  test('the Wi-Fi passphrase and PoP are never passed to the cloud API', async () => {
    const seenArgs: unknown[] = [];
    const { svc } = await setup({ statuses: [{ state: 'claimed' }] }, { issueClaimToken: async () => { seenArgs.push('t'); return { token: TOKEN, issuedAtMs: 1000 }; }, findClaimedDevice: async (...x) => { seenArgs.push(...x); return { deviceId: 'd', hwId: 'nw-a1b2c3d4e5f6' }; } });
    await svc.provision(REQ, () => undefined);
    expect(JSON.stringify(seenArgs)).not.toContain(SECRET_WIFI);
    expect(JSON.stringify(seenArgs)).not.toContain(POP);
  });

  const wifiCases: [string, ProvisioningErrorCode][] = [['auth', 'wifi_auth'], ['no_ap', 'wifi_no_ap'], ['timeout', 'wifi_timeout'], ['weird', 'wifi_timeout']];
  // the status endpoint is only read when the apply itself was refused (the library keeps its session then); after a successful apply it is not read at all
  test.each(wifiCases)('nw-status wifi_failed reason %s -> %s', async (reason, expected) => {
    const { svc, c } = await setup({ statuses: [{ state: 'wifi_connecting' }, { state: 'wifi_failed', reason }], applyError: new Error('apply refused') });
    expect(await code(svc.provision(REQ, () => undefined))).toBe(expected);
    expect(c.calls.some((x) => x.startsWith('find'))).toBe(false); // never "claimed" without the cloud check
  });
  const claimCases: [string, ProvisioningErrorCode][] = [['claim_token_invalid', 'claim_token_invalid'], ['device_owned', 'device_owned'], ['network', 'claim_network'], ['server', 'claim_server'], ['weird', 'claim_server']];
  test.each(claimCases)('nw-status claim_failed reason %s -> %s', async (reason, expected) => {
    const { svc } = await setup({ statuses: [{ state: 'claiming' }, { state: 'claim_failed', reason }], applyError: new Error('apply refused') });
    expect(await code(svc.provision(REQ, () => undefined))).toBe(expected);
  });

  test('cloud /claim-token errors: network -> claim_network, 429 or 5xx -> claim_server, signed out -> unknown; the sensor is never touched', async () => {
    for (const [err, expected] of [['network', 'claim_network'], ['rate_limited', 'claim_server'], ['server', 'claim_server'], ['unauthorized', 'unknown']] as const) {
      const { svc, a } = await setup({ statuses: [] }, { issueClaimToken: async () => { throw new ClaimApiError(err); } });
      expect(await code(svc.provision(REQ, () => undefined))).toBe(expected);
      expect(a.calls.some((x) => x.startsWith('send:') || x.startsWith('provision'))).toBe(false);
    }
  });
  test('a malformed token from the cloud is not sent to the sensor', async () => {
    const { svc, a } = await setup({ statuses: [] }, { issueClaimToken: async () => ({ token: 'short', issuedAtMs: 1000 }) });
    expect(await code(svc.provision(REQ, () => undefined))).toBe('claim_server');
    expect(a.sent).toEqual([]);
  });
  test('nw-claim answered ok:false or garbage stops before the Wi-Fi is applied (claim_rejected, not unknown)', async () => {
    for (const reply of ['{"v":1,"ok":false,"error":"bad_request"}', 'not json']) {
      const { svc, a } = await setup({ statuses: [], claimReply: reply });
      expect(await code(svc.provision(REQ, () => undefined))).toBe('claim_rejected');
      expect(a.calls.some((x) => x.startsWith('provision'))).toBe(false);
    }
  });
  test('applied, but no devices row in the cloud -> link_lost, never "claimed" and no Wi-Fi wording', async () => {
    const { svc } = await setup({ statuses: [{ state: 'claimed' }] }, { findClaimedDevice: async () => null }, { confirmTries: 3 });
    const seen: LinkState[] = [];
    expect(await code(svc.provision(REQ, (s) => seen.push(s)))).toBe('link_lost');
    expect(seen).not.toContain('claimed');
  });
  test('C3 re-setup: BLE drops, the cloud only has the OLD row (claimed before this token) -> link_lost, never "claimed"', async () => {
    const ISSUED = Date.parse('2026-11-17T10:00:00Z');
    const rows = [{ deviceId: 'old', hwId: 'nw-a1b2c3d4e5f6', claimedAt: '2026-11-01T08:00:00Z' }];
    // same filter the real ClaimApi applies, over a fixed table, so the service wiring (sinceMs from the token) is what is tested
    const find = async (_n: string, since: number) => { const r = rows.find((x) => claimedSince(x.claimedAt, since)); return r ? { deviceId: r.deviceId, hwId: r.hwId } : null; };
    const stale = await setup({ statuses: [], drop: true }, { issueClaimToken: async () => ({ token: TOKEN, issuedAtMs: ISSUED }), findClaimedDevice: find }, { confirmTries: 3 });
    const seen: LinkState[] = [];
    expect(await code(stale.svc.provision(REQ, (s) => seen.push(s)))).toBe('link_lost');
    expect(seen).not.toContain('claimed');
    // the device then really re-claims: claimed_at moves past the token issue time -> now it is confirmed
    rows[0].claimedAt = '2026-11-17T10:00:07Z';
    const fresh = await setup({ statuses: [], drop: true },{ issueClaimToken: async () => ({ token: TOKEN, issuedAtMs: ISSUED }), findClaimedDevice: find });
    expect(await code(fresh.svc.provision(REQ, () => undefined))).toBe('resolved');
  });
  test('the issue time of the token is what the cloud check receives', async () => {
    let got = -1;
    const { svc } = await setup({ statuses: [{ state: 'claimed' }] }, { issueClaimToken: async () => ({ token: TOKEN, issuedAtMs: 4242 }), findClaimedDevice: async (_n, since) => { got = since; return { deviceId: 'd', hwId: 'nw-a1b2c3d4e5f6' }; } });
    await svc.provision(REQ, () => undefined);
    expect(got).toBe(4242);
  });
  test('BLE drops after the apply (the sensor turns BLE off once claimed): the cloud decides; a drop with no cloud row is link_lost, never a Wi-Fi error', async () => {
    const ok = await setup({ statuses: [], drop: true });
    expect(await code(ok.svc.provision(REQ, () => undefined))).toBe('resolved');
    const bad = await setup({ statuses: [], drop: true }, { findClaimedDevice: async () => null }, { maxLinkMs: 3000 });
    expect(await code(bad.svc.provision(REQ, () => undefined))).toBe('link_lost');
    // no drop and no row after the apply: link_lost too (one outcome), after the whole link budget of cloud checks (3 s / 1 s = 3 tries here)
    let finds = 0;
    const noDrop = await setup({ statuses: [] }, { findClaimedDevice: async () => { finds += 1; return null; } }, { maxLinkMs: 3000 });
    expect(await code(noDrop.svc.provision(REQ, () => undefined))).toBe('link_lost');
    expect(finds).toBe(3);
  });
  test('apply refused and the sensor stays wifi_connecting: wifi_timeout, polled once a second; stuck claiming: claim_network', async () => {
    const a = await setup({ statuses: [{ state: 'wifi_connecting' }], applyError: new Error('apply refused') }, {}, { maxLinkMs: 3000 });
    expect(await code(a.svc.provision(REQ, () => undefined))).toBe('wifi_timeout');
    expect(a.slept.slice(0, 3)).toEqual([1000, 1000, 1000]);
    const b = await setup({ statuses: [{ state: 'claiming' }], applyError: new Error('apply refused') }, {}, { maxLinkMs: 3000 });
    expect(await code(b.svc.provision(REQ, () => undefined))).toBe('claim_network');
  });
  test('a drop while the apply-refused status is polled is link_lost, not claim_network or wifi_timeout (library text with code E_DEVICE_DISCONNECTED)', async () => {
    const libText = Object.assign(new Error('Request to send data to device failed: Device is not connected. Custom endpoint requests require an active provisioning session; if this happens after provision(), the device firmware may have already closed the session or disconnected the transport.'), { code: 'E_DEVICE_DISCONNECTED' });
    const { svc } = await setup({ statuses: [libText], applyError: new Error('apply refused') }, { findClaimedDevice: async () => null }, { confirmTries: 2 });
    expect(await code(svc.provision(REQ, () => undefined))).toBe('link_lost');
  });
  test('apply refused, then the link drops: the cloud window is the link budget (maxLinkMs / pollMs tries), not the 8 default', async () => {
    const libText = Object.assign(new Error('Request to send data to device failed: Device is not connected. Custom endpoint requests require an active provisioning session.'), { code: 'E_DEVICE_DISCONNECTED' });
    let finds = 0;
    const { svc } = await setup({ statuses: [libText], applyError: new Error('apply refused') }, { findClaimedDevice: async () => { finds += 1; return null; } }, { maxLinkMs: 5000 });
    expect(await code(svc.provision(REQ, () => undefined))).toBe('link_lost');
    expect(finds).toBe(5); // 5000 ms / 1000 ms, the same budget as the applied path
  });
  test('provision() itself rejects with E_DEVICE_DISCONNECTED: the drop flag is set, polling is skipped, the cloud decides -> link_lost', async () => {
    const dropped = Object.assign(new Error('Device is not connected.'), { code: 'E_DEVICE_DISCONNECTED' });
    const { svc, a } = await setup({ statuses: [{ state: 'wifi_connecting' }], applyError: dropped }, { findClaimedDevice: async () => null }, { confirmTries: 2 });
    expect(await code(svc.provision(REQ, () => undefined))).toBe('link_lost');
    expect(a.calls.some((x) => x.startsWith('send:nw-status'))).toBe(false);
  });
  test('provision() rejects with the drop and the cloud has the row -> resolved (device claimed, then turned BLE off)', async () => {
    const dropped = Object.assign(new Error('Device is not connected.'), { code: 'E_DEVICE_DISCONNECTED' });
    const { svc } = await setup({ statuses: [], applyError: dropped });
    expect(await code(svc.provision(REQ, () => undefined))).toBe('resolved');
  });
  test('apply rejected and status unreadable: library message decides (auth / no AP / unknown -> timeout)', async () => {
    for (const [msg, expected] of [['Wi-Fi authentication failed', 'wifi_auth'], ['AP not found', 'wifi_no_ap'], ['Provisioning timed out', 'wifi_timeout'], ['boom', 'wifi_timeout']] as const) {
      const { svc } = await setup({ statuses: [new Error('no session')], applyError: new Error(msg) });
      expect(await code(svc.provision(REQ, () => undefined))).toBe(expected);
    }
  });
  test('apply rejected while status still reads idle: the apply error is reported, no endless wait', async () => {
    const { svc } = await setup({ statuses: [{ state: 'idle' }], applyError: new Error('Wi-Fi authentication failed') });
    expect(await code(svc.provision(REQ, () => undefined))).toBe('wifi_auth');
  });
});

describe('classifyBleError', () => {
  test.each<[unknown, ProvisioningErrorCode]>([
    [new Error("The package 'react-native-esp-idf-provisioning' doesn't seem to be linked. You are not using Expo Go"), 'not_available'],
    [new Error('Bluetooth is turned off: adapter powered off'), 'bluetooth_off'],
    [new Error('Missing BLUETOOTH_SCAN permission'), 'permission_denied'],
    [new Error('Failed to establish security session'), 'wrong_code'],
    [Object.assign(new Error('x'), { code: 'E_DEVICE_DISCONNECTED' }), 'not_found'],
    [Object.assign(new Error('Request to send data to device failed: Device is not connected. Custom endpoint requests require an active provisioning session; the device firmware may have already closed the session or disconnected the transport.'), { code: 'E_DEVICE_DISCONNECTED' }), 'not_found'],
    ['plain string', 'unknown'],
  ])('%p -> %s', (e, expected) => expect(classifyBleError(e)).toBe(expected));
});

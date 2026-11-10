// Provisioning contract: label parsing, the fake's behaviour against ble-provisioning.md, and the setup state machine (FR-A03, FR-D03, A-023).
import { parseLabel, advertisedName } from '../provisioning/label';
import { createFakeProvisioning, FAKE_LABEL, FAKE_SENSOR, FAKE_WIFI } from '../provisioning/fakeProvisioning';
import { ProvisioningError, LOCATION_TYPES, SOIL_TYPES } from '../provisioning/types';
import { initialSetup, setupReducer, elapsedSeconds, formatClock, STEP_NUMBER, type SetupState, type SetupAction } from '../screens/setup/setupState';
import { validateDeviceName, validateSsid, validatePlantName, validateArea, validateCity, validateSpecies, validateWifiPassword } from '../validation';
import fs from 'fs';
import path from 'path';

describe('label', () => {
  test('parses NW1:<hw_id>:<pop>, forgiving about case and spaces', () => {
    expect(parseLabel(FAKE_LABEL)).toEqual({ hwId: 'nw-a1b2c3d4e5f6', pop: '7KQ2M9XD' });
    expect(parseLabel(' nw1:NW-A1B2C3D4E5F6:7kq2m9xd ')).toEqual({ hwId: 'nw-a1b2c3d4e5f6', pop: '7KQ2M9XD' });
  });
  test('rejects wrong shapes', () => {
    for (const bad of ['', 'NW1', 'NW2:nw-a1b2c3d4e5f6:7KQ2M9XD', 'NW1:nw-d4e5f6:7KQ2M9XD', 'NW1:nw-a1b2c3d4e5f6:7KQ2M9X', 'NW1:nw-a1b2c3d4e5f6:7KQ2M9XU', 'NW1:nw-a1b2c3d4e5f6:7KQ2M9XD:x']) expect(parseLabel(bad)).toBeNull();
  });
  test('advertised name is NW- plus the last 6 hex', () => expect(advertisedName('nw-a1b2c3d4e5f6')).toBe('NW-d4e5f6'));
});

describe('fake ProvisioningService', () => {
  const name = advertisedName(FAKE_SENSOR.hwId);
  test('happy path scan, connect, wifi scan, provision reports nw-status states in order', async () => {
    const { service, state } = createFakeProvisioning();
    expect((await service.scan()).map((d) => d.name)).toEqual([name]);
    await service.connect(name, FAKE_SENSOR.pop);
    expect((await service.scanWifi()).map((n) => n.ssid)).toContain(FAKE_WIFI.ssid);
    const seen: string[] = [];
    const r = await service.provision({ ssid: FAKE_WIFI.ssid, passphrase: FAKE_WIFI.password, name: 'Basil on the sill' }, (s) => seen.push(s));
    expect(seen).toEqual(['wifi_connecting', 'claiming', 'claimed']);
    expect(r.hwId).toBe(FAKE_SENSOR.hwId);
    expect(state.provisioned[0].name).toBe('Basil on the sill');
  });
  test('5 wrong codes close setup mode (ble-provisioning.md section 1)', async () => {
    const { service } = createFakeProvisioning();
    for (let i = 0; i < 4; i++) await expect(service.connect(name, 'WRONGPOP')).rejects.toMatchObject({ code: 'wrong_code' });
    await expect(service.connect(name, 'WRONGPOP')).rejects.toMatchObject({ code: 'setup_closed' });
    await expect(service.connect(name, FAKE_SENSOR.pop)).rejects.toMatchObject({ code: 'setup_closed' });
    expect(await service.scan()).toEqual([]);
  });
  test('wifi_failed reasons and device_owned', async () => {
    const a = createFakeProvisioning(); await a.service.connect(name, FAKE_SENSOR.pop);
    await expect(a.service.provision({ ssid: FAKE_WIFI.ssid, passphrase: 'bad', name: 'x' }, () => undefined)).rejects.toMatchObject({ code: 'wifi_auth' });
    await expect(a.service.provision({ ssid: 'Nowhere', passphrase: 'bad', name: 'x' }, () => undefined)).rejects.toMatchObject({ code: 'wifi_no_ap' });
    const b = createFakeProvisioning({ sensors: [{ ...FAKE_SENSOR, owned: true }] }); await b.service.connect(name, FAKE_SENSOR.pop);
    await expect(b.service.provision({ ssid: FAKE_WIFI.ssid, passphrase: FAKE_WIFI.password, name: 'x' }, () => undefined)).rejects.toBeInstanceOf(ProvisioningError);
  });
  test('the contract has no hub endpoint (A-023, hub pairing is v1.1)', () => {
    const src = fs.readFileSync(path.resolve(__dirname, '../provisioning/types.ts'), 'utf8');
    expect(src).not.toMatch(/\bpairHub\b|\bhubHost\b|\bconnectHub\b/);
    expect(Object.keys(createFakeProvisioning().service).sort()).toEqual(['connect', 'disconnect', 'provision', 'scan', 'scanWifi']);
  });
});

describe('setup state machine', () => {
  const run = (actions: SetupAction[], s: SetupState = initialSetup(0)) => actions.reduce(setupReducer, s);
  test('FR-A03 order: ready, connect, wifi, name, linking, photo, details, done (no hub step)', () => {
    let s = initialSetup(1000);
    const order: string[] = [s.step];
    for (const a of [
      { type: 'chooseDevice', deviceName: 'NW-d4e5f6' }, { type: 'connected' }, { type: 'wifiChosen', ssid: 'Home', passphrase: 'pw' }, { type: 'startLink', sensorName: ' Basil ' },
      { type: 'linked', deviceId: 'd1' }, { type: 'photo', uri: null }, { type: 'saved', plantName: 'Basil', now: 161000 },
    ] as SetupAction[]) { s = setupReducer(s, a); order.push(s.step); }
    expect(order).toEqual(['ready', 'connect', 'wifi', 'name', 'linking', 'photo', 'details', 'done']);
    expect(s.sensorName).toBe('Basil');
    expect(elapsedSeconds(s, 999999)).toBe(160);
    expect(Math.max(...Object.values(STEP_NUMBER))).toBe(5);
  });
  test('the Wi-Fi password is dropped from state once the sensor has it', () => {
    const s = run([{ type: 'chooseDevice', deviceName: 'N' }, { type: 'connected' }, { type: 'wifiChosen', ssid: 'Home', passphrase: 'secret' }, { type: 'startLink', sensorName: 'a' }, { type: 'linked', deviceId: 'd' }]);
    expect(s.passphrase).toBe('');
  });
  test('out-of-order actions are ignored', () => {
    const s = initialSetup(0);
    expect(setupReducer(s, { type: 'linked', deviceId: 'x' })).toBe(s);
    expect(setupReducer(s, { type: 'saved', plantName: 'x', now: 5 })).toBe(s);
  });
  test('link errors: re-enter keeps the network, other network clears it, retry keeps the name', () => {
    const base = run([{ type: 'chooseDevice', deviceName: 'N' }, { type: 'connected' }, { type: 'wifiChosen', ssid: 'Home', passphrase: 'bad' }, { type: 'startLink', sensorName: 'Basil' }, { type: 'linkFailed', error: 'wifi_auth' }]);
    expect(base.step).toBe('linkError');
    expect(setupReducer(base, { type: 'reenterWifi' })).toMatchObject({ step: 'wifi', ssid: 'Home', passphrase: '' });
    expect(setupReducer(base, { type: 'chooseOtherWifi' })).toMatchObject({ step: 'wifi', ssid: '' });
    expect(setupReducer(base, { type: 'retryLink' })).toMatchObject({ step: 'linking', sensorName: 'Basil' });
  });
  test('clock format', () => { expect(formatClock(0)).toBe('0:00'); expect(formatClock(161)).toBe('2:41'); });
});

describe('setup validation (FR-A03, FR-A04)', () => {
  test('required fields and limits', () => {
    expect(validateDeviceName(' ')).not.toBeNull(); expect(validateDeviceName('a'.repeat(81))).not.toBeNull(); expect(validateDeviceName('a'.repeat(80))).toBeNull();
    // 4.F2 contract check: 80 code points (emoji = 1), control characters refused as bad_request on the device
    expect(validateDeviceName('\u{1F331}'.repeat(80))).toBeNull(); expect(validateDeviceName('\u{1F331}'.repeat(81))).not.toBeNull();
    expect(validateDeviceName('a\nb')).toEqual({ key: 'validation.deviceName.control' });
    expect(validateSsid('')).not.toBeNull(); expect(validateSsid('é'.repeat(17))).not.toBeNull(); expect(validateSsid('Home')).toBeNull();
    expect(validatePlantName('')).not.toBeNull(); expect(validateArea('')).not.toBeNull(); expect(validateCity('')).not.toBeNull();
    expect(validateSpecies('')).toBeNull(); expect(validateSpecies('x'.repeat(121))).not.toBeNull();
  });
  test('Wi-Fi password: 8-63 chars for WPA2, empty only for open networks (PR #56 C2)', () => {
    expect(validateWifiPassword('')?.key).toBe('validation.wifiPassword.required');
    expect(validateWifiPassword('x'.repeat(7))?.key).toBe('validation.wifiPassword.length');
    expect(validateWifiPassword('x'.repeat(8))).toBeNull();
    expect(validateWifiPassword('x'.repeat(63))).toBeNull();
    expect(validateWifiPassword('x'.repeat(64))?.key).toBe('validation.wifiPassword.length');
    expect(validateWifiPassword('        ')).toBeNull(); // 8 spaces are a legal passphrase, not trimmed
    expect(validateWifiPassword('', false)).toBeNull();
    expect(validateWifiPassword('secret-pass', false)?.key).toBe('validation.wifiPassword.open');
  });
  test('location and soil lists match db-schema.sql', () => {
    const sql = fs.readFileSync(path.resolve(__dirname, '../../../docs/interfaces/db-schema.sql'), 'utf8');
    for (const v of [...LOCATION_TYPES, ...SOIL_TYPES]) expect(sql).toContain(`'${v}'`);
  });
});

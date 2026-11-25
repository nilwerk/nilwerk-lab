// In-memory ProvisioningService / PlantSetupService / PhotoSource for tests and the web mock (EXPO_PUBLIC_MOCK_AUTH=1). No Bluetooth involved.
// Behaviour follows ble-provisioning.md: 5 wrong PoPs close setup mode; wifi_failed / claim_failed reasons; owned device -> device_owned.
import { advertisedName } from './label';
import {
  PlantSetupError, ProvisioningError, type DiscoveredDevice, type LinkState, type PhotoSource, type PlantDetails, type PlantSetupService,
  type ProvisioningService, type SetupServices, type WifiNetwork,
} from './types';

export interface FakeSensor { hwId: string; pop: string; /** already claimed by someone else */ owned?: boolean }

export interface FakeProvisioningOptions {
  sensors?: FakeSensor[];
  networks?: (WifiNetwork & { password?: string })[];
  /** Bluetooth permission refused / adapter off / no implementation */
  failScan?: 'permission_denied' | 'bluetooth_off' | 'not_available';
  /** error to throw once at the claim stage, e.g. 'claim_network' */
  claimFailsOnce?: 'claim_network' | 'claim_server' | 'claim_token_invalid' | 'claim_rejected';
}

export const FAKE_SENSOR: FakeSensor = { hwId: 'nw-a1b2c3d4e5f6', pop: '7KQ2M9XD' };
export const FAKE_LABEL = `NW1:${FAKE_SENSOR.hwId}:${FAKE_SENSOR.pop}`;
export const FAKE_WIFI = { ssid: 'HomeNet-2G', password: 'correct-horse' };

export function createFakeProvisioning(opts: FakeProvisioningOptions = {}) {
  const sensors = opts.sensors ?? [FAKE_SENSOR];
  const networks = opts.networks ?? [
    { ssid: FAKE_WIFI.ssid, bars: 3, secure: true, password: FAKE_WIFI.password },
    { ssid: 'Neighbour_5G', bars: 2, secure: true, password: 'x' },
  ];
  const state = { failedHandshakes: 0, closed: false, connected: null as FakeSensor | null, provisioned: [] as { hwId: string; ssid: string; name: string }[], claimFailsOnce: opts.claimFailsOnce };
  const byName = (n: string) => sensors.find((s) => advertisedName(s.hwId) === n);

  const service: ProvisioningService = {
    async scan(): Promise<DiscoveredDevice[]> {
      if (opts.failScan) throw new ProvisioningError(opts.failScan);
      if (state.closed) return [];
      return sensors.map((s, i) => ({ name: advertisedName(s.hwId), bars: (3 - (i % 3)) as 1 | 2 | 3 }));
    },
    async connect(deviceName, pop) {
      if (state.closed) throw new ProvisioningError('setup_closed');
      const s = byName(deviceName);
      if (!s) throw new ProvisioningError('not_found');
      if (s.pop !== pop) {
        state.failedHandshakes += 1;
        if (state.failedHandshakes >= 5) { state.closed = true; throw new ProvisioningError('setup_closed'); }
        throw new ProvisioningError('wrong_code');
      }
      state.connected = s;
    },
    async scanWifi() {
      if (!state.connected) throw new ProvisioningError('not_found');
      return networks.map(({ ssid, bars, secure }) => ({ ssid, bars, secure }));
    },
    async provision(req, onState: (s: LinkState) => void) {
      const s = state.connected;
      if (!s) throw new ProvisioningError('not_found');
      onState('wifi_connecting');
      const net = networks.find((n) => n.ssid === req.ssid);
      if (!net) throw new ProvisioningError('wifi_no_ap');
      if (net.secure && net.password !== req.passphrase) throw new ProvisioningError('wifi_auth');
      onState('claiming');
      if (s.owned) throw new ProvisioningError('device_owned');
      if (state.claimFailsOnce) { const c = state.claimFailsOnce; state.claimFailsOnce = undefined; throw new ProvisioningError(c); }
      state.provisioned.push({ hwId: s.hwId, ssid: req.ssid, name: req.name });
      onState('claimed');
      return { deviceId: `device-${state.provisioned.length}`, hwId: s.hwId };
    },
    async disconnect() { state.connected = null; },
  };
  return { service, state };
}

export function createFakePlants(opts: { failNext?: boolean; linked?: boolean; commitThenLose?: boolean; unreadable?: boolean } = {}) {
  const created: { deviceId: string; details: PlantDetails; photoUri: string | null }[] = [];
  /** device ids whose sensor was moved from another plant (the user chose move) */
  const moved: string[] = [];
  const o = opts;
  let linkedNow = false;   // a save committed on the fake "server"
  const service: PlantSetupService = {
    async currentPlant() {
      if (o.unreadable) throw new PlantSetupError();
      if (linkedNow) return `plant-${created.length}`;   // the plant a committed save linked (ids differ, so a move is visible)
      return o.linked ? 'plant-current' : null;
    },
    async createPlant(deviceId, details, photoUri, call) {
      if (o.failNext) { o.failNext = false; throw new PlantSetupError(); }
      const move = call?.moveFromCurrent === true;
      if ((o.linked || linkedNow) && !move) return { status: 'already_linked' };   // nothing is written
      created.push({ deviceId, details, photoUri });
      if (move && o.linked) moved.push(deviceId);
      if (move) o.linked = false;
      linkedNow = true;
      // the server committed, but the answer was lost on the way back
      if (o.commitThenLose) { o.commitThenLose = false; throw new PlantSetupError(); }
      return { status: 'saved', plantId: `plant-${created.length}` };
    },
  };
  return { service, created, moved, options: o };
}

export function createFakePhotos(result: string | null = 'file:///fake/basil.jpg'): PhotoSource & { calls: string[] } {
  const calls: string[] = [];
  return { calls, async takePhoto() { calls.push('take'); return result; }, async pickFromLibrary() { calls.push('pick'); return result; } };
}

/** Everything wired for tests / web mock. */
export function createFakeSetup(opts: FakeProvisioningOptions = {}) {
  const prov = createFakeProvisioning(opts);
  const plants = createFakePlants();
  const photos = createFakePhotos();
  const services: SetupServices = { provisioning: prov.service, plants: plants.service, photos };
  return { services, prov, plants, photos };
}

/** Used when no BLE implementation exists in the build: every call says so, the UI shows a plain message. */
export function unavailableProvisioning(): ProvisioningService {
  const no = async (): Promise<never> => { throw new ProvisioningError('not_available'); };
  return { scan: no, connect: no, scanWifi: no, provision: no, disconnect: async () => undefined };
}

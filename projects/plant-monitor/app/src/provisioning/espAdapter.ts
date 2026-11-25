// BleAdapter on @orbital-systems/react-native-esp-idf-provisioning 0.7.1 (needs an Expo dev build: native module, not in Expo Go or on web).
// Glue only, one library call per method; behaviour is in bleProvisioning.ts. The library is required lazily so web / Jest / Expo Go can load the app.
import { PermissionsAndroid, Platform } from 'react-native';
import type { BleAdapter, BleDevice, BleWifi } from './bleAdapter';
import { ProvisioningError } from './types';

type Lib = typeof import('@orbital-systems/react-native-esp-idf-provisioning');
type EspDevice = InstanceType<Lib['ESPDevice']>;

export function createEspAdapter(loadLib: () => Lib = () => require('@orbital-systems/react-native-esp-idf-provisioning')): BleAdapter {
  let lib: Lib | null = null;
  const L = (): Lib => {
    if (!lib) { try { lib = loadLib(); } catch { throw new ProvisioningError('not_available'); } }
    return lib;
  };
  const found = new Map<string, EspDevice>();
  let current: EspDevice | null = null;
  const cur = (): EspDevice => { if (!current) throw new ProvisioningError('not_found'); return current; };

  return {
    async ensureReady() {
      L();
      if (Platform.OS === 'android') {
        const P = PermissionsAndroid.PERMISSIONS;
        const wanted = Number(Platform.Version) >= 31 ? [P.BLUETOOTH_SCAN, P.BLUETOOTH_CONNECT] : [P.ACCESS_FINE_LOCATION];
        const res = await PermissionsAndroid.requestMultiple(wanted);
        if (wanted.some((p) => res[p] !== PermissionsAndroid.RESULTS.GRANTED)) throw new ProvisioningError('permission_denied');
      }
      // iOS asks for Bluetooth on first scan (NSBluetoothAlwaysUsageDescription added by the config plugin). Adapter-off is detected from the library error text.
    },
    async search(prefix): Promise<BleDevice[]> {
      const { ESPProvisionManager, ESPTransport, ESPSecurity } = L();
      const devices = await ESPProvisionManager.searchESPDevices(prefix, ESPTransport.ble, ESPSecurity.secure2);
      found.clear();
      const out: BleDevice[] = [];
      for (const dev of devices ?? []) {
        found.set(dev.name, dev);
        const serviceUuid = await dev.getPrimaryServiceUuid().catch(() => undefined); // Android only; iOS returns undefined
        out.push({ name: dev.name, serviceUuid: serviceUuid ?? undefined });
      }
      return out;
    },
    async connect(name, pop, srpUsername) {
      const { ESPDevice, ESPTransport, ESPSecurity } = L();
      const dev = found.get(name) ?? new ESPDevice({ name, transport: ESPTransport.ble, security: ESPSecurity.secure2 });
      current = null;
      await dev.connect(pop, null, srpUsername);
      current = dev;
    },
    async scanWifi(): Promise<BleWifi[]> {
      const list = await cur().scanWifiList();
      return list.map((n) => ({ ssid: n.ssid, rssi: n.rssi, secure: n.auth !== 0 }));
    },
    sendData: (endpoint, body) => cur().sendData(endpoint, body),
    async provision(ssid, passphrase) { await cur().provision(ssid, passphrase); },
    async disconnect() { const d = current; current = null; if (d) d.disconnect(); },
    onDisconnected(callback) { return current ? current.onDisconnected(callback) : () => undefined; },
  };
}

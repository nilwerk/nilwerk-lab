// Thin seam between the provisioning logic (bleProvisioning.ts) and the native BLE library. Everything that touches Bluetooth goes through this
// interface, so the logic is unit-tested with a fake adapter and the library glue (espAdapter.ts) stays a few lines per call.
// Errors: ensureReady throws ProvisioningError ('permission_denied' | 'bluetooth_off' | 'not_available'); every other method rejects with whatever the
// library threw, and bleProvisioning.ts classifies it (classifyBleError).

export interface BleDevice {
  /** advertised name, NW-<last 6 hex of hw_id> */
  name: string;
  /** primary service UUID from the advertisement when the platform exposes it (Android). iOS: undefined. */
  serviceUuid?: string;
}
export interface BleWifi { ssid: string; /** dBm */ rssi: number; /** false = open network */ secure: boolean }

export interface BleAdapter {
  /** Ask for Bluetooth permissions and check the adapter is on. */
  ensureReady(): Promise<void>;
  /** Scan for devices whose name starts with `namePrefix` (the library filters by name prefix, not by service UUID). */
  search(namePrefix: string): Promise<BleDevice[]>;
  /** Connect and run the protocomm security-2 (SRP6a) handshake. The PoP is the SRP password and is never sent. */
  connect(name: string, pop: string, srpUsername: string): Promise<void>;
  /** prov-scan over the open session. */
  scanWifi(): Promise<BleWifi[]>;
  /** Custom endpoint request (UTF-8 JSON out, UTF-8 JSON back), e.g. 'nw-claim', 'nw-status'. */
  sendData(endpoint: string, body: string): Promise<string>;
  /** prov-config (SSID + passphrase) and apply. The library cannot split config and apply, so nw-claim is sent before this call. */
  provision(ssid: string, passphrase: string): Promise<void>;
  disconnect(): Promise<void>;
  /** Called when the sensor drops the BLE link without us asking. Returns an unsubscribe function. Optional: without it no drop is seen. */
  onDisconnected?(callback: () => void): () => void;
}

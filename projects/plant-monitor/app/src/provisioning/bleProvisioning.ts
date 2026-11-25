// Real ProvisioningService (task 4.A3b slice 1). All Bluetooth goes through a BleAdapter; the cloud through a ClaimApi. Logic here is pure and unit-tested.
// Contract: docs/interfaces/ble-provisioning.md (service UUID, security 2, nw-claim, nw-status, sequence section 3). Requirements: FR-A03, FR-D03, FR-D07, NFR-06.
// NOT verified on any hardware. Session lifetime after apply was read from the Android SDK source (esp-idf-provisioning-android lib-2.4.4); the iOS SDK was not readable.
import type { BleAdapter, BleDevice } from './bleAdapter';
import { isClaimToken, ClaimApiError, type ClaimApi } from './claimApi';
import { advertisedName } from './label';
import { ProvisioningError, type DiscoveredDevice, type LinkState, type ProvisioningErrorCode, type ProvisioningService, type WifiNetwork } from './types';

/** ble-provisioning.md section 1 (NW_PROV_SERVICE_UUID in firmware nw_prov_proto.h). */
export const NW_PROV_SERVICE_UUID = 'b53672dd-5227-40a0-8b6f-6f836f8a584c';
export const NW_NAME_PREFIX = 'NW-';
/** SRP6a user name for security 2. UNVERIFIED / PROPOSED: the contract does not name one; "wifiprov" is the ESP-IDF esp_prov default. The factory step that
 *  creates the per-unit salt + verifier must use the same string (that tool is not in the repo). Needs a decision by the Architect / firmware (see PR). */
export const NW_SRP_USERNAME = 'wifiprov';

export interface BleProvisioningDeps {
  adapter: BleAdapter;
  claim: ClaimApi;
  sleep?: (ms: number) => Promise<void>;
  /** nw-status poll interval, contract: 1 s */
  pollMs?: number;
  /** give up on Wi-Fi join + claim after this long. UNVERIFIED budget: the device does not enforce its 300 s cut-off during a join or claim call. */
  maxLinkMs?: number;
  /** how long to wait for the devices row after the device said claimed (or dropped BLE) */
  confirmTries?: number;
}

const NAME_RE = /^NW-[0-9a-f]{6}$/i;
const defaultSleep = (ms: number) => new Promise<void>((r) => setTimeout(r, ms));

/** Maps a raw library / adapter error to the setup error states. Message texts of the native library are UNVERIFIED (not run on a phone), so the match is loose. */
export function classifyBleError(e: unknown): ProvisioningErrorCode {
  if (e instanceof ProvisioningError) return e.code;
  const msg = e instanceof Error ? e.message : String(e);
  const code = (e as { code?: string } | null)?.code ?? '';
  if (/doesn't seem to be linked|not using Expo Go|TurboModule/i.test(msg)) return 'not_available';
  if (/bluetooth.*(off|disabled|not enabled|powered)|powered ?off/i.test(msg)) return 'bluetooth_off';
  if (/permission|not authori[sz]ed|unauthori[sz]ed/i.test(msg)) return 'permission_denied';
  // Checked before the handshake words: the library's "not connected" text also says "session", and a dropped link is not a wrong PoP
  if (code === 'E_DEVICE_DISCONNECTED') return 'not_found';
  if (/proof of possession|handshake|security|session|srp|authenticat|invalid (pop|password)/i.test(msg) && !/wi-?fi/i.test(msg)) return 'wrong_code';
  if (/disconnect/i.test(msg) || code === 'E_DEVICE_DISCONNECTED') return 'not_found';
  if (/not found|no .*device|timed? ?out|timeout/i.test(msg)) return 'not_found';
  return 'unknown';
}

/** A BLE link drop, by the library's code or its text. Used for the drop flag, so every drop path sets the same flag. */
function isLinkDrop(e: unknown): boolean {
  const msg = e instanceof Error ? e.message : String(e);
  return (e as { code?: string } | null)?.code === 'E_DEVICE_DISCONNECTED' || /disconnect/i.test(msg);
}

/** Loose mapping of a failed provision() call when nw-status cannot be read. */
function classifyWifiError(e: unknown): ProvisioningErrorCode {
  const msg = e instanceof Error ? e.message : String(e);
  if (/auth|password|passphrase/i.test(msg)) return 'wifi_auth';
  if (/ap not found|no ap|network not found|not found/i.test(msg)) return 'wifi_no_ap';
  if (/time/i.test(msg)) return 'wifi_timeout';
  const c = classifyBleError(e);
  return c === 'unknown' ? 'wifi_timeout' : c;
}

type Status = { state?: unknown; reason?: unknown };
const WIFI_REASON: Record<string, ProvisioningErrorCode> = { auth: 'wifi_auth', no_ap: 'wifi_no_ap', timeout: 'wifi_timeout' };
const CLAIM_REASON: Record<string, ProvisioningErrorCode> = { claim_token_invalid: 'claim_token_invalid', device_owned: 'device_owned', network: 'claim_network', server: 'claim_server' };

function parseStatus(raw: string): Status | null {
  try { const j = JSON.parse(raw) as Status & { v?: unknown }; return j && typeof j === 'object' && j.v === 1 && typeof j.state === 'string' ? j : null; } catch { return null; }
}

function barsFor(rssi: number): 1 | 2 | 3 { return rssi >= -60 ? 3 : rssi >= -75 ? 2 : 1; }

export function createBleProvisioning(d: BleProvisioningDeps): ProvisioningService {
  const sleep = d.sleep ?? defaultSleep;
  const pollMs = d.pollMs ?? 1000;
  const maxLinkMs = d.maxLinkMs ?? 90_000;
  const confirmTries = d.confirmTries ?? 8;
  let connected: string | null = null;

  const sendJson = async (endpoint: string, body: unknown): Promise<unknown> => {
    const raw = await d.adapter.sendData(endpoint, JSON.stringify(body));
    try { return JSON.parse(raw); } catch { return null; }
  };
  const confirmInCloud = async (name: string, sinceMs: number, tries = confirmTries): Promise<{ deviceId: string; hwId: string } | null> => {
    for (let i = 0; i < tries; i++) {
      const hit = await d.claim.findClaimedDevice(name, sinceMs).catch(() => null);
      if (hit) return hit;
      await sleep(pollMs);
    }
    return null;
  };

  return {
    async scan() {
      try { await d.adapter.ensureReady(); } catch (e) { throw new ProvisioningError(classifyBleError(e)); }
      let found: BleDevice[];
      try { found = await d.adapter.search(NW_NAME_PREFIX); } catch (e) { throw new ProvisioningError(classifyBleError(e)); }
      // Only sensors that advertise our service UUID (where the platform tells us) and a well-formed NW-xxxxxx name.
      const seen = new Set<string>();
      const out: DiscoveredDevice[] = [];
      for (const dev of found) {
        if (!NAME_RE.test(dev.name) || seen.has(dev.name)) continue;
        if (dev.serviceUuid && dev.serviceUuid.toLowerCase() !== NW_PROV_SERVICE_UUID) continue;
        seen.add(dev.name);
        out.push({ name: dev.name, bars: 2 }); // the library does not report signal strength for devices: fixed 2 bars (UNVERIFIED limitation)
      }
      return out.sort((a, b) => a.name.localeCompare(b.name));
    },

    async connect(deviceName, pop) {
      if (!NAME_RE.test(deviceName)) throw new ProvisioningError('not_found');
      connected = null;
      try {
        await d.adapter.connect(deviceName, pop, NW_SRP_USERNAME);
      } catch (e) {
        let code = classifyBleError(e);
        if (code === 'wrong_code') {
          // The device, not the app, counts the 5 failed handshakes. If it stopped advertising after this failure, setup mode is closed.
          const still = await d.adapter.search(NW_NAME_PREFIX).then((l) => l.some((x) => x.name === deviceName), () => true);
          if (!still) code = 'setup_closed';
        }
        throw new ProvisioningError(code);
      }
      connected = deviceName;
    },

    async scanWifi() {
      if (!connected) throw new ProvisioningError('not_found');
      let list;
      try { list = await d.adapter.scanWifi(); } catch (e) { throw new ProvisioningError(classifyBleError(e)); }
      const best = new Map<string, WifiNetwork>();
      for (const n of list) {
        if (!n.ssid) continue;
        const cand: WifiNetwork = { ssid: n.ssid, bars: barsFor(n.rssi), secure: n.secure };
        const cur = best.get(n.ssid);
        if (!cur || cand.bars > cur.bars) best.set(n.ssid, cand);
      }
      return [...best.values()].sort((a, b) => b.bars - a.bars || a.ssid.localeCompare(b.ssid));
    },

    async provision(req, onState: (s: LinkState) => void) {
      const name = connected;
      if (!name) throw new ProvisioningError('not_found');
      onState('wifi_connecting');

      // 1. claim token from the cloud (user JWT). Never logged.
      let token: string; let issuedAtMs: number;
      try { ({ token, issuedAtMs } = await d.claim.issueClaimToken()); } catch (e) {
        const c = e instanceof ClaimApiError ? e.code : 'network';
        throw new ProvisioningError(c === 'network' ? 'claim_network' : c === 'unauthorized' ? 'unknown' : 'claim_server');
      }
      if (!isClaimToken(token)) throw new ProvisioningError('claim_server');

      // 2. nw-claim (encrypted by the session). The device keeps it until the apply below.
      let reply: unknown;
      try { reply = await sendJson('nw-claim', { v: 1, name: req.name, claim_token: token }); } catch (e) { throw new ProvisioningError(classifyBleError(e)); }
      // Any reply other than {ok:true} is the sensor refusing the claim (e.g. {"ok":false,"error":"bad_request"}), not an unknown app error.
      if (!reply || (reply as { ok?: unknown }).ok !== true) throw new ProvisioningError('claim_rejected');

      // 3. prov-config + apply. Device joins Wi-Fi and calls POST /device-claim itself; the passphrase goes only to the sensor.
      // From here on a BLE drop is watched. The sensor turns BLE off once it has claimed, so a drop alone is not a failure; it only matters if the cloud
      // does not confirm the link afterwards (link_lost, not a Wi-Fi error).
      let dropped = false;
      const stopWatching = d.adapter.onDisconnected?.(() => { dropped = true; }) ?? (() => undefined);
      try {
        let applyError: unknown = null;
        try { await d.adapter.provision(req.ssid, req.passphrase); } catch (e) { applyError = e; if (isLinkDrop(e)) dropped = true; }

        if (applyError === null) {
          // Applied. The library has dropped its security session on success (esp-idf-provisioning-android lib-2.4.4, ESPDevice.java:1189 "session = null"),
          // so the next custom-endpoint request would run a new SRP handshake that the device rejects by dropping the link. Nothing more is sent over BLE:
          // the cloud decides, and the window is the whole link budget because the sensor still has to join Wi-Fi and claim.
          // One outcome for "applied, not confirmed": the app cannot tell from here whether the link dropped, so it does not blame Wi-Fi or the server.
          onState('claiming');
          const hit = await confirmInCloud(name, issuedAtMs, Math.ceil(maxLinkMs / pollMs));
          if (!hit) throw new ProvisioningError('link_lost');
          onState('claimed');
          return hit;
        }

        // Apply refused. The library keeps its session on failure, so nw-status can still be read for the device's own reason.
        // A drop already seen (from provision() or the drop watch) ends the polling: the link is gone, so ask the cloud.
        let sawClaiming = false;
        let waited = 0;
        let lastWasDisconnect = false;
        while (!dropped && waited <= maxLinkMs) {
          let status: Status | null = null;
          try { status = parseStatus(await d.adapter.sendData('nw-status', '')); lastWasDisconnect = false; } catch (e) { if (isLinkDrop(e)) dropped = true; lastWasDisconnect = dropped || classifyBleError(e) === 'not_found'; }
          if (status) {
            const state = status.state as string;
            const reason = typeof status.reason === 'string' ? status.reason : '';
            if (state === 'wifi_failed') throw new ProvisioningError(WIFI_REASON[reason] ?? 'wifi_timeout');
            if (state === 'claim_failed') throw new ProvisioningError(CLAIM_REASON[reason] ?? 'claim_server');
            if (state === 'idle') throw new ProvisioningError(classifyWifiError(applyError)); // apply never started on the device
            if (state === 'claiming') { sawClaiming = true; onState('claiming'); }
            if (state === 'claimed') { sawClaiming = true; onState('claiming'); break; }
          } else if (!lastWasDisconnect) {
            // the status endpoint is not readable: fall back to the library's own error text for the apply
            throw new ProvisioningError(classifyWifiError(applyError));
          } else {
            // BLE dropped: the device turns BLE off after "claimed", so ask the cloud instead of failing outright
            sawClaiming = true; onState('claiming'); break;
          }
          await sleep(pollMs); waited += pollMs;
        }
        if (!dropped && waited > maxLinkMs) throw new ProvisioningError(sawClaiming ? 'claim_network' : 'wifi_timeout');

        // 5. a devices row claimed AFTER the token was issued (a row of an earlier setup of the same sensor does not count) must be visible under RLS before we say "claimed" (contract section 3 step 5)
        // Once a drop was seen, the cloud window is the same link budget as the applied path (the sensor may still be joining Wi-Fi and claiming).
        const hit = await confirmInCloud(name, issuedAtMs, dropped ? Math.ceil(maxLinkMs / pollMs) : confirmTries);
        if (!hit) throw new ProvisioningError(dropped ? 'link_lost' : 'claim_network');
        onState('claimed');
        return hit;
      } finally {
        stopWatching();
      }
    },

    async disconnect() { connected = null; await d.adapter.disconnect().catch(() => undefined); },
  };
}

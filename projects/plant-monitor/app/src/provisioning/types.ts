// Device setup contract used by the UI (task 4.A3, FR-A03 / FR-D03). Two implementations: fakeProvisioning.ts (tests, web mock) and
// bleProvisioning.ts (4.A3b slice 1: real BLE on @orbital-systems/react-native-esp-idf-provisioning via espAdapter.ts; needs an Expo dev build, not Expo Go).
// Mirrors docs/interfaces/ble-provisioning.md (sequence section 3, nw-claim, nw-status) and openapi.yaml /claim-token + /device-claim.
// A-023: hub pairing (S17, nw-hub) is v1.1 and deliberately NOT part of this contract.

export interface DiscoveredDevice { /** advertised name, NW-<last 6 hex of hw_id> */ name: string; /** signal strength 1..3 bars */ bars: 1 | 2 | 3 }
export interface WifiNetwork { ssid: string; bars: 1 | 2 | 3; secure: boolean }
/** nw-status states the UI shows while linking (ble-provisioning.md section 2). */
export type LinkState = 'wifi_connecting' | 'claiming' | 'claimed';
export interface ProvisionRequest { ssid: string; passphrase: string; /** device name, 1-80 chars (nw-claim) */ name: string }
export interface ProvisionResult { deviceId: string; hwId: string }

export type ProvisioningErrorCode =
  | 'not_available'       // no BLE implementation in this build (Expo Go / web without mock)
  | 'permission_denied'   // Bluetooth (+ location on Android) refused
  | 'bluetooth_off'
  | 'not_found'           // nothing advertising NW-*, or the device left setup mode
  | 'wrong_code'          // PoP rejected by the SRP6a handshake; 5 tries then setup_closed
  | 'setup_closed'        // 5 failures or 5 minutes: press the pinhole button again
  | 'wifi_auth' | 'wifi_no_ap' | 'wifi_timeout'          // nw-status wifi_failed reasons
  | 'device_owned' | 'claim_token_invalid' | 'claim_network' | 'claim_server' // nw-status claim_failed reasons
  | 'claim_rejected'      // the sensor answered nw-claim with something other than {ok:true} (e.g. {"ok":false,"error":"bad_request"})
  | 'link_lost'           // the BLE link dropped after the Wi-Fi details were applied and the server had not confirmed the link (not a Wi-Fi error)
  | 'unknown';            // genuinely unclassified failures only

export class ProvisioningError extends Error {
  code: ProvisioningErrorCode;
  constructor(code: ProvisioningErrorCode, message?: string) { super(message ?? code); this.name = 'ProvisioningError'; this.code = code; }
}

export interface ProvisioningService {
  /** Scan for advertising NW-* sensors (setup mode). Asks Bluetooth permission on first use. */
  scan(): Promise<DiscoveredDevice[]>;
  /** SRP6a security-2 handshake with the PoP from the label (the PoP is never sent). */
  connect(deviceName: string, pop: string): Promise<void>;
  /** prov-scan over the open session. */
  scanWifi(): Promise<WifiNetwork[]>;
  /** POST /claim-token, then prov-config (SSID + passphrase) + nw-claim, then follow nw-status. The passphrase goes only to the sensor, never to the cloud. */
  provision(req: ProvisionRequest, onState: (s: LinkState) => void): Promise<ProvisionResult>;
  /** Leave the session (user cancelled). */
  disconnect(): Promise<void>;
}

export const LOCATION_TYPES = ['house', 'balcony', 'garden', 'farm', 'greenhouse'] as const;
export const SOIL_TYPES = ['potting', 'garden', 'sand', 'clay', 'peat', 'other'] as const; // [proposed] list from db-schema.sql plants.soil_type
export type LocationType = typeof LOCATION_TYPES[number];
export type SoilType = typeof SOIL_TYPES[number];

/** The six FR-A04 fields (species optional). */
export interface PlantDetails { name: string; location: LocationType; area: string; soil: SoilType; species: string; city: string }

export class PlantSetupError extends Error { constructor(message = 'plant_save_failed') { super(message); this.name = 'PlantSetupError'; } }

/** saved: the plant and the device link were written in one call. already_linked: the sensor has a plant; NOTHING was written (no silent move). */
export type PlantSaveResult = { status: 'saved'; plantId: string } | { status: 'already_linked' };

export interface PlantSetupService {
  /** Insert the plant and point devices.plant_id at it, in ONE server call (all or nothing). Photo is refused in the real build (not dropped).
   *  A sensor that already has a plant is only moved when moveFromCurrent is true; otherwise the answer is already_linked and nothing is written. */
  createPlant(deviceId: string, details: PlantDetails, photoUri: string | null, opts?: { moveFromCurrent?: boolean }): Promise<PlantSaveResult>;
  /** Read-only: the plant the sensor is on now (null = none). Used after a failed save, because the save may have committed. Throws if it cannot be read. */
  currentPlant(deviceId: string): Promise<string | null>;
}

/** Camera / library. Real one (expo-image-picker) arrives with the dev build; null = user cancelled. */
/** supported=false: this build cannot take a photo yet; the photo step then offers only Skip (4.A4c). Default true. */
export interface PhotoSource { takePhoto(): Promise<string | null>; pickFromLibrary(): Promise<string | null>; supported?: boolean }

export interface SetupServices { provisioning: ProvisioningService; plants: PlantSetupService; photos: PhotoSource }

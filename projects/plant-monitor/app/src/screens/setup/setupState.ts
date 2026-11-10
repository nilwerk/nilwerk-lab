// Pure state machine of the device setup flow (FR-A03 order: find sensor, connect, Wi-Fi, name, photo, plant details, done).
// No hub step: hub pairing S17 is v1.1 (A-023). No BLE here, so every transition is unit-testable.
import type { ProvisioningErrorCode } from '../../provisioning/types';

export type SetupStep = 'ready' | 'connect' | 'wifi' | 'name' | 'linking' | 'linkError' | 'photo' | 'details' | 'done';
export const STEP_NUMBER: Record<SetupStep, number> = { ready: 1, connect: 1, wifi: 2, name: 3, linking: 3, linkError: 3, photo: 4, details: 5, done: 5 };
export const STEP_COUNT = 5;
/** NFR-03: set up in at most 3 minutes. */
export const TARGET_SECONDS = 180;

export interface SetupState {
  step: SetupStep;
  startedAt: number;
  finishedAt: number | null;
  deviceName: string | null;
  ssid: string;
  passphrase: string;
  sensorName: string;
  deviceId: string | null;
  photoUri: string | null;
  plantName: string | null;
  error: ProvisioningErrorCode | null;
}

export const initialSetup = (now: number): SetupState => ({ step: 'ready', startedAt: now, finishedAt: null, deviceName: null, ssid: '', passphrase: '', sensorName: '', deviceId: null, photoUri: null, plantName: null, error: null });

export type SetupAction =
  | { type: 'chooseDevice'; deviceName: string }
  | { type: 'connected' }
  | { type: 'wifiChosen'; ssid: string; passphrase: string }
  | { type: 'startLink'; sensorName: string }
  | { type: 'linked'; deviceId: string }
  | { type: 'linkFailed'; error: ProvisioningErrorCode }
  | { type: 'reenterWifi' }       // keep the network, ask for the password again
  | { type: 'chooseOtherWifi' }
  | { type: 'retryLink' }
  | { type: 'restart'; now: number }
  | { type: 'photo'; uri: string | null }
  | { type: 'backToPhoto' }
  | { type: 'saved'; plantName: string; now: number };

export function setupReducer(s: SetupState, a: SetupAction): SetupState {
  switch (a.type) {
    case 'chooseDevice': return s.step === 'ready' ? { ...s, step: 'connect', deviceName: a.deviceName, error: null } : s;
    case 'connected': return s.step === 'connect' ? { ...s, step: 'wifi' } : s;
    case 'wifiChosen': return s.step === 'wifi' ? { ...s, step: 'name', ssid: a.ssid, passphrase: a.passphrase } : s;
    case 'startLink': return s.step === 'name' ? { ...s, step: 'linking', sensorName: a.sensorName.trim(), error: null } : s;
    case 'linked': return s.step === 'linking' ? { ...s, step: 'photo', deviceId: a.deviceId, passphrase: '' } : s; // drop the Wi-Fi password as soon as the sensor has it
    case 'linkFailed': return s.step === 'linking' ? { ...s, step: 'linkError', error: a.error } : s;
    case 'reenterWifi': return s.step === 'linkError' ? { ...s, step: 'wifi', passphrase: '', error: null } : s;
    case 'chooseOtherWifi': return s.step === 'linkError' ? { ...s, step: 'wifi', ssid: '', passphrase: '', error: null } : s;
    case 'retryLink': return s.step === 'linkError' ? { ...s, step: 'linking', error: null } : s;
    case 'restart': return initialSetup(a.now);
    case 'photo': return s.step === 'photo' ? { ...s, step: 'details', photoUri: a.uri } : s;
    case 'backToPhoto': return s.step === 'details' ? { ...s, step: 'photo' } : s;
    case 'saved': return s.step === 'details' ? { ...s, step: 'done', plantName: a.plantName, finishedAt: a.now } : s;
    default: return s;
  }
}

export const elapsedSeconds = (s: SetupState, now: number): number => Math.max(0, Math.floor(((s.finishedAt ?? now) - s.startedAt) / 1000));
export const formatClock = (sec: number): string => `${Math.floor(sec / 60)}:${String(sec % 60).padStart(2, '0')}`;

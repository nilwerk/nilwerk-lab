// A-024: string catalogue. Every t('...') key used in src/ and App.tsx exists in en.json; wireframe keys survive; placeholders work.
import fs from 'fs';
import path from 'path';
import en from '../../strings/en.json';
import { t, hasKey, allKeys } from '../i18n';
import { LOCATION_TYPES, SOIL_TYPES } from '../provisioning/types';

const root = path.resolve(__dirname, '../..');
const files = (dir: string): string[] => fs.readdirSync(dir, { withFileTypes: true }).flatMap((e) => (e.isDirectory() ? (e.name === '__tests__' ? [] : files(path.join(dir, e.name))) : /\.tsx?$/.test(e.name) ? [path.join(dir, e.name)] : []));

describe('string catalogue (A-024)', () => {
  test('app name is Plant Monitor', () => expect(t('app.name')).toBe('Plant Monitor'));
  test('placeholders are filled, unknown key is visible', () => {
    expect(t('plant.remove.title', { plantName: 'Basil' })).toBe('Remove Basil?');
    expect(t('validation.password.short', { min: 8 })).toBe('Use at least 8 characters.');
    expect(t('no.such.key')).toBe('no.such.key');
  });
  test('every key used in code exists', () => {
    const used = new Set<string>();
    for (const f of [...files(path.join(root, 'src')), path.join(root, 'App.tsx')]) {
      const src = fs.readFileSync(f, 'utf8');
      for (const m of src.matchAll(/\bt\(\s*'([\w.]+)'/g)) used.add(m[1]);
      for (const m of src.matchAll(/(?:label|labelKey)[:=]\s*\{?\s*t?\(?'([\w.]+)'/g)) used.add(m[1]);
      for (const m of src.matchAll(/'((?:auth|validation|profile|deleteAccount|premium|common|a11y|welcome|app|plants|plant|nav|status|setup|legal)\.[\w.]+)'/g)) used.add(m[1]);
    }
    const missing = [...used].filter((k) => !hasKey(k));
    expect(missing).toEqual([]);
    expect(used.size).toBeGreaterThan(30);
  });
  test('dynamic setup keys exist (error codes, link errors, location and soil lists)', () => {
    const codes = ['permission_denied', 'bluetooth_off', 'not_available', 'wrong_code', 'setup_closed', 'not_found', 'unknown'];
    for (const c of codes) expect(hasKey(`setup.error.${c}`)).toBe(true);
    for (const c of ['wifi_auth', 'wifi_no_ap', 'wifi_timeout', 'device_owned', 'claim_network', 'claim_server', 'claim_token_invalid', 'claim_rejected', 'link_lost', 'unknown']) expect(hasKey(`setup.linkError.${c}`)).toBe(true);
    expect(hasKey('setup.linkError.lost.title')).toBe(true);
    for (const l of LOCATION_TYPES) expect(hasKey(`setup.location.${l}`)).toBe(true);
    for (const l of SOIL_TYPES) expect(hasKey(`setup.soil.${l}`)).toBe(true);
  });
  test('status keys from the brand set exist', () => {
    for (const k of ['ok', 'dry', 'wet', 'lowBattery', 'offline', 'error']) expect(hasKey(`status.${k}`)).toBe(true);
  });
  test('A-024 premium wording: activated by Nilwerk + contact link', () => {
    expect(t('premium.cta')).toBe('Get Premium');
    expect(t('premium.activatedByNilwerk')).toMatch(/activated by Nilwerk/);
    expect(t('premium.contactUs')).toBe('Contact us');
  });
  test('all values are non-empty strings, no stray braces other than placeholders', () => {
    for (const k of allKeys()) {
      const v = (en as unknown as Record<string, string>)[k];
      expect(typeof v).toBe('string');
      expect(v.trim()).not.toBe('');
      expect(v.replace(/\{\w+\}/g, '')).not.toMatch(/[{}]/);
    }
  });
});

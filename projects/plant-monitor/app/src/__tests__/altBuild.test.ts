// #238 alternative build: gallery day groups (hand-written example) and the badge label of the Alerts tab.
import { dayGroups } from '../screens/PlantGalleryScreen';
import { countOpenAlertPlants } from '../plants/status';
import { t } from '../i18n';
import type { PlantPhoto } from '../plants/types';

const photo = (id: string, takenAt: string): PlantPhoto => ({ id, takenAt } as PlantPhoto);

describe('gallery day groups (hand-written example)', () => {
  // newest first, as sorted: two photos on 25 Nov, one on 24 Nov (local day of the stamp; noon UTC keeps the day in every zone)
  const sorted = [photo('a', '2026-11-25T12:00:00.000Z'), photo('b', '2026-11-25T09:00:00.000Z'), photo('c', '2026-11-24T12:00:00.000Z')];
  test('groups in order: 25 Nov has a and b, 24 Nov has c', () => {
    const groups = dayGroups(sorted);
    expect(groups.map((g) => g.photos.map((p) => p.id))).toEqual([['a', 'b'], ['c']]);
    expect(groups.map((g) => g.day)).toEqual(['25 Nov 2026', '24 Nov 2026']);
  });
  test('no photos, no groups', () => {
    expect(dayGroups([])).toEqual([]);
  });
});

describe('Alerts tab label', () => {
  test('with open alerts the tab reads the count', () => {
    expect(t('nav.alertsBadge', { label: t('nav.alerts'), n: 2 })).toBe('Alerts, 2 open');
  });
});

describe('cached Alerts badge count (hand-computed example)', () => {
  // Fixture by hand: Basil OK, Cactus too dry, Fern low battery, Orchid offline, Rubber tree no sensor.
  // Plants with a state other than OK or no sensor: Cactus, Fern, Orchid = 3.
  const plants = [
    { deviceId: 'd1', openAlerts: [] },
    { deviceId: 'd2', openAlerts: ['too_dry'] },
    { deviceId: 'd3', openAlerts: ['low_battery'] },
    { deviceId: 'd4', openAlerts: ['device_offline'] },
    { deviceId: null, openAlerts: [] },
  ] as Array<{ deviceId: string | null; openAlerts: never[] | ['too_dry'] | ['low_battery'] | ['device_offline'] }>;
  test('three plants have an open state', () => {
    expect(countOpenAlertPlants(plants)).toBe(3);
  });
  test('no plants, or only OK and no-sensor plants, give 0', () => {
    expect(countOpenAlertPlants([])).toBe(0);
    expect(countOpenAlertPlants([{ deviceId: 'd1', openAlerts: [] }, { deviceId: null, openAlerts: [] }])).toBe(0);
  });
});

describe('plan prices (strings only)', () => {
  test('Free 0 and Premium 7.99 come from strings/en.json', () => {
    expect(t('profile.price.free')).toBe('Free: 0');
    expect(t('profile.price.premium')).toBe('Premium: 7.99');
  });
});

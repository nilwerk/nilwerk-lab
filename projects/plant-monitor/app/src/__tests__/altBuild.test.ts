// #238 alternative build: gallery day groups (hand-written example) and the badge label of the Alerts tab.
import { dayGroups } from '../screens/PlantGalleryScreen';
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

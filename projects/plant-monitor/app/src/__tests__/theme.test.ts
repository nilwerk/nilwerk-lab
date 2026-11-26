// NFR-03 / accessibility: AA contrast (4.5:1) for every text/background pair the screens use, computed from theme.ts in both schemes.
import { colors, minTouchTarget, statusMeta, getTheme, statusStyle, type PlantStatus } from '../../theme';

import { contrast } from './contrastUtil';

describe.each(['light', 'dark'] as const)('contrast (%s)', (s) => {
  const c = colors[s];
  const pairs: Array<[string, string, string]> = [
    ['ink on bg', c.ink, c.bg], ['ink on surface', c.ink, c.surface], ['muted on bg', c.muted, c.bg], ['muted on surface', c.muted, c.surface],
    ['accentInk on accent (primary button)', c.accentInk, c.accent], ['dangerInk on danger (delete button)', c.dangerInk, c.danger],
    ['accent on bg (ghost button)', c.accent, c.bg], ['danger on bg (field error)', c.danger, c.bg], ['danger on surface', c.danger, c.surface],
    ['danger on dangerSoft (error notice)', c.danger, c.dangerSoft], ['ok on okSoft (info notice)', c.ok, c.okSoft],
  ];
  test.each(pairs)('%s >= 4.5', (_n, fg, bg) => expect(contrast(fg, bg)).toBeGreaterThanOrEqual(4.5));
  // WCAG 2.2 SC 1.4.11: borders that identify inputs, radio choices and secondary buttons need 3:1 against bg and surface.
  test('control borders are at least 3:1 on bg and surface', () => {
    for (const bg of [c.bg, c.surface]) expect(contrast(c.control, bg)).toBeGreaterThanOrEqual(3);
  });
  test('every status colour is AA on bg, surface and its soft background', () => {
    for (const k of Object.keys(statusMeta) as PlantStatus[]) {
      const st = statusStyle(k, s);
      for (const bg of [c.bg, c.surface, st.background]) expect(contrast(st.color, bg)).toBeGreaterThanOrEqual(4.5);
    }
  });
});

// 48 dp is the Android minimum (developer.android.com accessibility guide); 44 pt is the iOS minimum. 48 satisfies both.
test('touch target token is at least 48', () => expect(minTouchTarget).toBeGreaterThanOrEqual(48));
test('getTheme falls back to light for unknown scheme', () => expect(getTheme(null).name).toBe('light'));

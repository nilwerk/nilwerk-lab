// NFR-03 / accessibility: AA contrast (4.5:1) for every text/background pair the screens use, computed from theme.ts in both schemes.
import { colors, minTouchTarget, statusMeta, getTheme, statusStyle, type PlantStatus } from '../../theme';

const lum = (hex: string) => {
  const c = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255).map((v) => (v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4));
  return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
};
export const contrast = (a: string, b: string) => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return (x + 0.05) / (y + 0.05); };

describe.each(['light', 'dark'] as const)('contrast (%s)', (s) => {
  const c = colors[s];
  const pairs: Array<[string, string, string]> = [
    ['ink on bg', c.ink, c.bg], ['ink on surface', c.ink, c.surface], ['muted on bg', c.muted, c.bg], ['muted on surface', c.muted, c.surface],
    ['accentInk on accent (primary button)', c.accentInk, c.accent], ['dangerInk on danger (delete button)', c.dangerInk, c.danger],
    ['accent on bg (ghost button)', c.accent, c.bg], ['danger on bg (field error)', c.danger, c.bg], ['danger on surface', c.danger, c.surface],
    ['danger on dangerSoft (error notice)', c.danger, c.dangerSoft], ['ok on okSoft (info notice)', c.ok, c.okSoft],
  ];
  test.each(pairs)('%s >= 4.5', (_n, fg, bg) => expect(contrast(fg, bg)).toBeGreaterThanOrEqual(4.5));
  test('every status colour is AA on bg, surface and its soft background', () => {
    for (const k of Object.keys(statusMeta) as PlantStatus[]) {
      const st = statusStyle(k, s);
      for (const bg of [c.bg, c.surface, st.background]) expect(contrast(st.color, bg)).toBeGreaterThanOrEqual(4.5);
    }
  });
});

test('touch target token is at least 44', () => expect(minTouchTarget).toBeGreaterThanOrEqual(44));
test('getTheme falls back to light for unknown scheme', () => expect(getTheme(null).name).toBe('light'));

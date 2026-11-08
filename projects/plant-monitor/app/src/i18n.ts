// String catalogue access (A-024: English only, every UI string lives in strings/en.json; de.json can follow with the same keys).
import en from '../strings/en.json';

type Params = Record<string, string | number>;
const catalogue = en as Record<string, unknown>;

export function hasKey(key: string): boolean {
  return typeof catalogue[key] === 'string';
}

/** Look up a string and fill {placeholders}. Unknown key returns the key itself so a gap is visible, never blank. */
export function t(key: string, params?: Params): string {
  const raw = catalogue[key];
  if (typeof raw !== 'string') return key;
  if (!params) return raw;
  return raw.replace(/\{(\w+)\}/g, (m, name: string) => (name in params ? String(params[name]) : m));
}

export function allKeys(): string[] {
  return Object.keys(catalogue).filter((k) => !k.startsWith('_'));
}

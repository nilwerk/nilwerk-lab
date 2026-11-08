// Session storage for supabase-js. SecureStore limits a value to about 2 KB and a session JWT can exceed that,
// so values are split into chunks. Web falls back to localStorage. (NFR-07: tokens never leave the device's secure storage.)

export interface KeyValueStore {
  getItem(key: string): Promise<string | null>;
  setItem(key: string, value: string): Promise<void>;
  removeItem(key: string): Promise<void>;
}

export const CHUNK_SIZE = 1800;

/** Wraps a small-value store so that arbitrarily long values work. */
export function chunked(base: KeyValueStore, chunkSize: number = CHUNK_SIZE): KeyValueStore {
  const countKey = (k: string) => `${k}.n`;
  const partKey = (k: string, i: number) => `${k}.${i}`;
  const clear = async (key: string) => {
    const n = Number(await base.getItem(countKey(key))) || 0;
    for (let i = 0; i < n; i++) await base.removeItem(partKey(key, i));
    await base.removeItem(countKey(key));
  };
  return {
    async getItem(key) {
      const n = Number(await base.getItem(countKey(key)));
      if (!n) return null;
      let out = '';
      for (let i = 0; i < n; i++) {
        const part = await base.getItem(partKey(key, i));
        if (part === null) return null; // torn write: treat as no session
        out += part;
      }
      return out;
    },
    async setItem(key, value) {
      await clear(key);
      const parts = Math.max(1, Math.ceil(value.length / chunkSize));
      for (let i = 0; i < parts; i++) await base.setItem(partKey(key, i), value.slice(i * chunkSize, (i + 1) * chunkSize));
      await base.setItem(countKey(key), String(parts));
    },
    removeItem: clear,
  };
}

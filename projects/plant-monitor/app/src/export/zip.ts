// Minimal ZIP writer (method 0 = stored, no compression), so the export archive needs no dependency. Requirements: NFR-07 (the user holds a complete copy), A-107 (photos go into the export archive).
// Limits: ZIP32 (each file and the archive < 4 GiB, < 65535 entries); throws when exceeded instead of writing a corrupt archive. Photos are already compressed (JPEG/HEIC), so storing loses little.
export interface ZipEntry { name: string; bytes: Uint8Array }

const CRC_TABLE = (() => {
  const t = new Uint32Array(256);
  for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; t[n] = c >>> 0; }
  return t;
})();

export function crc32(bytes: Uint8Array): number {
  let c = 0xffffffff;
  for (let i = 0; i < bytes.length; i++) c = CRC_TABLE[(c ^ bytes[i]) & 0xff] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
}

const LIMIT = 0xffffffff;

export function buildStoredZip(entries: ZipEntry[], when: Date = new Date()): Uint8Array {
  if (entries.length === 0 || entries.length >= 0xffff) throw new Error('zip: bad entry count');
  const enc = new TextEncoder();
  const dosTime = (when.getUTCHours() << 11) | (when.getUTCMinutes() << 5) | (when.getUTCSeconds() >> 1);
  const dosDate = (Math.max(0, when.getUTCFullYear() - 1980) << 9) | ((when.getUTCMonth() + 1) << 5) | when.getUTCDate();
  const names = entries.map((e) => enc.encode(e.name));
  let total = 22;
  entries.forEach((e, i) => { total += 30 + names[i].length + e.bytes.length + 46 + names[i].length; });
  if (total > LIMIT) throw new Error('zip: archive too large');
  const out = new Uint8Array(total);
  const v = new DataView(out.buffer);
  let p = 0;
  const offsets: number[] = [];
  const crcs = entries.map((e) => crc32(e.bytes));
  entries.forEach((e, i) => {
    offsets.push(p);
    v.setUint32(p, 0x04034b50, true); v.setUint16(p + 4, 20, true); v.setUint16(p + 6, 0x0800, true); // UTF-8 names
    v.setUint16(p + 8, 0, true); v.setUint16(p + 10, dosTime, true); v.setUint16(p + 12, dosDate, true);
    v.setUint32(p + 14, crcs[i], true); v.setUint32(p + 18, e.bytes.length, true); v.setUint32(p + 22, e.bytes.length, true);
    v.setUint16(p + 26, names[i].length, true); v.setUint16(p + 28, 0, true);
    out.set(names[i], p + 30); out.set(e.bytes, p + 30 + names[i].length);
    p += 30 + names[i].length + e.bytes.length;
  });
  const cdStart = p;
  entries.forEach((e, i) => {
    v.setUint32(p, 0x02014b50, true); v.setUint16(p + 4, 20, true); v.setUint16(p + 6, 20, true); v.setUint16(p + 8, 0x0800, true);
    v.setUint16(p + 10, 0, true); v.setUint16(p + 12, dosTime, true); v.setUint16(p + 14, dosDate, true);
    v.setUint32(p + 16, crcs[i], true); v.setUint32(p + 20, e.bytes.length, true); v.setUint32(p + 24, e.bytes.length, true);
    v.setUint16(p + 28, names[i].length, true); // extra, comment, disk, attrs stay 0
    v.setUint32(p + 42, offsets[i], true);
    out.set(names[i], p + 46);
    p += 46 + names[i].length;
  });
  v.setUint32(p, 0x06054b50, true); v.setUint16(p + 8, entries.length, true); v.setUint16(p + 10, entries.length, true);
  v.setUint32(p + 12, p - cdStart, true); v.setUint32(p + 16, cdStart, true);
  return out;
}

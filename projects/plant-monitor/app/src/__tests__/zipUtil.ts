// Test helper: reads a stored ZIP back (central directory), verifying CRC-32, so tests check the real archive bytes instead of trusting the writer.
import { crc32 } from '../export/zip';
export function readZip(z: Uint8Array): Record<string, Uint8Array> {
  const v = new DataView(z.buffer, z.byteOffset, z.byteLength);
  const eocd = z.byteLength - 22;
  if (v.getUint32(eocd, true) !== 0x06054b50) throw new Error('no EOCD');
  const n = v.getUint16(eocd + 10, true);
  let p = v.getUint32(eocd + 16, true);
  const out: Record<string, Uint8Array> = {};
  for (let i = 0; i < n; i++) {
    if (v.getUint32(p, true) !== 0x02014b50) throw new Error('bad central header');
    const crc = v.getUint32(p + 16, true), size = v.getUint32(p + 24, true), nl = v.getUint16(p + 28, true), off = v.getUint32(p + 42, true);
    const name = new TextDecoder().decode(z.subarray(p + 46, p + 46 + nl));
    if (v.getUint32(off, true) !== 0x04034b50) throw new Error('bad local header');
    const start = off + 30 + v.getUint16(off + 26, true) + v.getUint16(off + 28, true);
    const data = z.slice(start, start + size);
    if (crc32(data) !== crc) throw new Error(`crc mismatch ${name}`);
    out[name] = data; p += 46 + nl;
  }
  return out;
}

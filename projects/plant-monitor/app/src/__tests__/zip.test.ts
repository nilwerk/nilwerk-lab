// Stored-ZIP writer (NFR-07, A-107). Checked with our own reader (CRC) AND, when available, the system `unzip -t` / python zipfile.
import { execFileSync } from 'child_process';
import fs from 'fs';
import os from 'os';
import path from 'path';
import { buildStoredZip, crc32 } from '../export/zip';
import { readZip } from './zipUtil';

const b = (s: string) => new TextEncoder().encode(s);
test('crc32 of "123456789" is the standard check value', () => expect(crc32(b('123456789'))).toBe(0xcbf43926));
test('round trip: names and bytes survive, including UTF-8 names and an empty-looking small file', () => {
  const z = buildStoredZip([{ name: 'export.json', bytes: b('{"a":1}') }, { name: 'photos/ü_1.jpg', bytes: new Uint8Array([0xff, 0xd8, 0, 1, 2]) }]);
  const r = readZip(z);
  expect(Object.keys(r)).toEqual(['export.json', 'photos/ü_1.jpg']);
  expect(Array.from(r['photos/ü_1.jpg'])).toEqual([0xff, 0xd8, 0, 1, 2]);
});
test('rejects an empty entry list', () => expect(() => buildStoredZip([])).toThrow());
test('an independent unzip accepts the archive (python zipfile testzip)', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'zipchk-'));
  const f = path.join(dir, 'a.zip');
  fs.writeFileSync(f, buildStoredZip([{ name: 'export.json', bytes: b('{"plants":[]}') }, { name: 'photos/p1.jpg', bytes: new Uint8Array(70000).map((_, i) => i % 251) }]));
  let out = '';
  try { out = execFileSync('python3', ['-I', '-c', 'import sys,zipfile;z=zipfile.ZipFile(sys.argv[1]);print(z.testzip(), sorted(z.namelist()))', f], { encoding: 'utf8' }); }
  catch (e) { if ((e as NodeJS.ErrnoException).code === 'ENOENT') return; throw e; }
  expect(out.trim()).toBe("None ['export.json', 'photos/p1.jpg']");
});

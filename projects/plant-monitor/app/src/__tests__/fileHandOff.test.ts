// File hand-off (NFR-07, A-106: delete only after the user really received the export). Fake platform deps.
import { HandOffError, handOffFile, type ExportFile, type HandOffDeps } from '../export/fileHandOff';

const file: ExportFile = { fileName: 'e.json', contentType: 'application/json', bytes: new Uint8Array([1, 2, 3]) };
const deps = (o: Partial<HandOffDeps> = {}): HandOffDeps & { calls: string[] } => {
  const calls: string[] = [];
  return { calls,
    write: async () => { calls.push('write'); return { uri: 'file:///c/e.json', size: 3 }; },
    isShareAvailable: async () => true,
    share: async () => { calls.push('share'); },
    confirmSaved: async () => { calls.push('confirm'); return true; },
    ...o };
};
const code = (p: Promise<void>) => p.then(() => 'ok', (e) => (e instanceof HandOffError ? e.code : 'other'));

describe('handOffFile', () => {
  test('success only after write, share and the user confirming, in that order', async () => {
    const d = deps();
    await expect(handOffFile(file, d)).resolves.toBeUndefined();
    expect(d.calls).toEqual(['write', 'share', 'confirm']);
  });
  test('write failure, size mismatch (truncated file) and empty bytes -> write_failed, nothing shared', async () => {
    const a = deps({ write: async () => { throw new Error('disk full'); } });
    const b = deps({ write: async () => ({ uri: 'u', size: 2 }) });
    expect(await code(handOffFile(file, a))).toBe('write_failed');
    expect(await code(handOffFile(file, b))).toBe('write_failed');
    expect(await code(handOffFile({ ...file, bytes: new Uint8Array() }, deps()))).toBe('write_failed');
    expect(a.calls).toEqual([]); expect(b.calls).toEqual([]);
  });
  test('no share sheet available -> unavailable (never counts as exported)', async () => {
    const d = deps({ isShareAvailable: async () => false });
    expect(await code(handOffFile(file, d))).toBe('unavailable');
    expect(d.calls).toEqual(['write']);
  });
  test('share sheet error -> share_failed, user is not asked to confirm', async () => {
    const d = deps({ share: async () => { throw new Error('x'); } });
    expect(await code(handOffFile(file, d))).toBe('share_failed');
    expect(d.calls).toEqual(['write']);
  });
  test('user says "not yet" or the dialog throws -> not_confirmed', async () => {
    expect(await code(handOffFile(file, deps({ confirmSaved: async () => false })))).toBe('not_confirmed');
    expect(await code(handOffFile(file, deps({ confirmSaved: async () => { throw new Error('x'); } })))).toBe('not_confirmed');
  });
});

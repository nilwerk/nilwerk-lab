// File hand-off for the data export. Requirements: NFR-07 (export first, delete removes all data), FR-A01.
// Owner decision A-106 (2026-11-17): no skip option; delete stays blocked until the user really received the export.
// A share sheet resolving does NOT prove the file was saved (the user can dismiss it, Android always resolves), so the hand-off has 4 steps and
// succeeds only if all pass: (1) write the file and read its size back, (2) open the share sheet / download, (3) the user confirms "I saved it".
// `exported` in the UI is set only when handOffFile resolves. Pure logic with injected platform deps, tested in __tests__/fileHandOff.test.ts;
// the real deps (expo-file-system, expo-sharing, Alert / window) are in handOffDeps.ts.
export interface ExportFile { fileName: string; contentType: string; bytes: Uint8Array }

export type HandOffErrorCode = 'write_failed' | 'unavailable' | 'share_failed' | 'not_confirmed';
export class HandOffError extends Error {
  code: HandOffErrorCode;
  constructor(code: HandOffErrorCode) { super(`export hand-off: ${code}`); this.name = 'HandOffError'; this.code = code; }
}

export interface HandOffDeps {
  /** writes the bytes to a temp file and returns its uri and the size read back from disk */
  write(file: ExportFile): Promise<{ uri: string; size: number }>;
  isShareAvailable(): Promise<boolean>;
  /** opens the share sheet (native) or starts the browser download (web) */
  share(uri: string, file: ExportFile): Promise<void>;
  /** asks the user "did you save the file?"; true = yes */
  confirmSaved(fileName: string): Promise<boolean>;
}

export type FileHandOff = (file: ExportFile) => Promise<void>;

export async function handOffFile(file: ExportFile, deps: HandOffDeps): Promise<void> {
  if (file.bytes.length === 0) throw new HandOffError('write_failed');
  let written: { uri: string; size: number };
  try { written = await deps.write(file); } catch { throw new HandOffError('write_failed'); }
  if (written.size !== file.bytes.length) throw new HandOffError('write_failed');
  let available = false;
  try { available = await deps.isShareAvailable(); } catch { available = false; }
  if (!available) throw new HandOffError('unavailable');
  try { await deps.share(written.uri, file); } catch { throw new HandOffError('share_failed'); }
  let saved = false;
  try { saved = await deps.confirmSaved(file.fileName); } catch { saved = false; }
  if (!saved) throw new HandOffError('not_confirmed');
}

export const createFileHandOff = (deps: HandOffDeps): FileHandOff => (file) => handOffFile(file, deps);

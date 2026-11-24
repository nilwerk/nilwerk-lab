// Copy action for the key and the setup text (task 4.A8, FR-P03). No extra native module: on web the browser clipboard, on a phone the system share sheet
// (which offers "Copy"). A dedicated clipboard module would need a new dependency and a dev-build rebuild; not added in this slice.
import { Platform, Share } from 'react-native';

export type CopyText = (text: string) => Promise<void>;

export const copyText: CopyText = async (text) => {
  const clip = Platform.OS === 'web' ? (globalThis as { navigator?: { clipboard?: { writeText(s: string): Promise<void> } } }).navigator?.clipboard : undefined;
  if (clip) { await clip.writeText(text); return; }
  await Share.share({ message: text });
};

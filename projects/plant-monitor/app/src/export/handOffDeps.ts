// Real platform deps for fileHandOff.ts. Native: expo-file-system (cache dir) + expo-sharing (share sheet) + Alert. Web: Blob download + window.confirm.
// NOT run on a phone in the agent session (no device): only type-checked; the logic around it is unit-tested with fakes.
import { Alert, Platform } from 'react-native';
import { File, Paths } from 'expo-file-system';
import * as Sharing from 'expo-sharing';
import { t } from '../i18n';
import type { HandOffDeps } from './fileHandOff';

const nativeDeps: HandOffDeps = {
  async write(file) {
    const f = new File(Paths.cache, file.fileName);
    if (f.exists) f.delete();
    f.create();
    await f.write(file.bytes);
    return { uri: f.uri, size: f.size ?? 0 };
  },
  isShareAvailable: () => Sharing.isAvailableAsync(),
  share: (uri, file) => Sharing.shareAsync(uri, { mimeType: file.contentType, dialogTitle: file.fileName }),
  confirmSaved: (fileName) => new Promise((resolve) => {
    Alert.alert(t('export.confirm.title'), t('export.confirm.body', { fileName }), [
      { text: t('export.confirm.no'), style: 'cancel', onPress: () => resolve(false) },
      { text: t('export.confirm.yes'), onPress: () => resolve(true) },
    ], { cancelable: false });
  }),
};

const webDeps: HandOffDeps = {
  async write(file) {
    const blob = new Blob([file.bytes as BlobPart], { type: file.contentType });
    return { uri: URL.createObjectURL(blob), size: blob.size };
  },
  isShareAvailable: async () => typeof document !== 'undefined',
  async share(uri, file) {
    const a = document.createElement('a');
    a.href = uri; a.download = file.fileName;
    document.body.appendChild(a); a.click(); a.remove();
  },
  confirmSaved: async (fileName) => globalThis.confirm?.(t('export.confirm.body', { fileName })) === true,
};

export const platformHandOffDeps: HandOffDeps = Platform.OS === 'web' ? webDeps : nativeDeps;

// S04 Delete account. Requirements: FR-A01 (delete account, 0 rows remain), NFR-07 (all personal data removed).
// Calls DELETE /account {confirm:"DELETE"} (docs/interfaces/openapi.yaml). Plant removal with export warning is A-022 and is NOT here.
import React, { useState } from 'react';
import { Body, Button, Field, Notice, Screen } from '../ui/primitives';
import { t } from '../i18n';
import { useAuth } from '../auth/AuthContext';
import { validateDeleteConfirm } from '../validation';

export function DeleteAccountScreen({ onCancel }: { onCancel: () => void }) {
  const { service } = useAuth();
  const [typed, setTyped] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const ok = validateDeleteConfirm(typed) === null;

  const run = async () => {
    if (!ok) return;
    setBusy(true); setError(null);
    try {
      await service.deleteAccount(); // session ends -> AuthProvider shows the welcome screen
    } catch {
      setError(t('deleteAccount.error'));
      setBusy(false);
    }
  };

  return (
    <Screen title={t('deleteAccount.title')} onBack={onCancel}>
      <Body>{t('deleteAccount.warning')}</Body>
      <Body muted>{t('deleteAccount.exportHint')}</Body>
      {error ? <Notice kind="error" text={error} /> : null}
      <Field label={t('deleteAccount.confirmLabel')} value={typed} onChangeText={setTyped} autoCapitalize="characters" autoCorrect={false} />
      <Button label={t('deleteAccount.confirm')} variant="danger" onPress={run} disabled={!ok} busy={busy} />
      <Button label={t('common.cancel')} variant="secondary" onPress={onCancel} />
    </Screen>
  );
}

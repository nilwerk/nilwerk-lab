// S04 Delete account. Requirements: FR-A01 (delete account, 0 rows remain), NFR-07 (all personal data removed; export first: openapi.yaml /account says the app does it, the server does not enforce it).
// Calls DELETE /account {confirm:"DELETE"} through AuthService.deleteAccount (src/account/accountApi.ts -> edge function delete-account, docs/interfaces/openapi.yaml).
// Gate: the delete runs only after a successful export (JSON or CSV) AND the typed word DELETE (src/export/exportGate.ts). There is no skip (see exportGate.ts).
// User-visible states: idle, exporting, export failed, export ready, deleting, success (session ends -> welcome screen), 401 (session expired), network, server/other error.
import React, { useRef, useState } from 'react';
import { Body, Button, Field, Notice, Screen } from '../ui/primitives';
import { t } from '../i18n';
import { useAuth } from '../auth/AuthContext';
import { usePlants } from '../plants/PlantsContext';
import { exportDoneText, exportErrorText } from '../export/exportErrorText';
import type { ExportResult } from '../plants/types';
import { AuthError } from '../auth/types';
import { DeleteGateError, canDelete, deleteAccountGated } from '../export/exportGate';

/** `afterUncertain`: an earlier attempt in this screen ended in network/server/unknown, so the delete may have partly or fully run (the function releases devices and deletes photos before the auth user). A 401 then can mean "already erased", not "session expired". */
export const deleteErrorKey = (e: unknown, afterUncertain = false): string => {
  if (e instanceof DeleteGateError) return 'deleteAccount.error.gate';
  const code = e instanceof AuthError ? e.code : 'unknown';
  if (code === 'unauthorized') return afterUncertain ? 'deleteAccount.error.unauthorizedAfterError' : 'deleteAccount.error.unauthorized';
  return code === 'network' ? 'deleteAccount.error.network' : 'deleteAccount.error';
};

export function DeleteAccountScreen({ onCancel }: { onCancel: () => void }) {
  const { service } = useAuth();
  const plants = usePlants();
  const [typed, setTyped] = useState('');
  const [busy, setBusy] = useState(false);
  const [exporting, setExporting] = useState<'json' | 'csv' | null>(null);
  const [exported, setExported] = useState<ExportResult | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const uncertain = useRef(false); // an attempt failed in a way that may have deleted data
  const gate = { exported: exported?.complete === true, typed, expected: t('deleteAccount.confirmWord') };
  const allowed = canDelete(gate);

  const runExport = async (format: 'json' | 'csv') => {
    setExporting(format); setExportError(null);
    try { setExported(await plants.exportData(format)); }
    catch (e) { setExported(null); setExportError(exportErrorText(e, 'deleteAccount.exportError')); }
    finally { setExporting(null); }
  };
  const run = async () => {
    setBusy(true); setError(null);
    try {
      await deleteAccountGated(gate, () => service.deleteAccount()); // success ends the session -> AuthProvider shows the welcome screen
    } catch (e) {
      const code = e instanceof AuthError ? e.code : 'unknown';
      setError(t(deleteErrorKey(e, uncertain.current)));
      if (code !== 'unauthorized' && !(e instanceof DeleteGateError)) uncertain.current = true;
      setBusy(false);
    }
  };

  return (
    <Screen title={t('deleteAccount.title')} onBack={onCancel}>
      <Body>{t('deleteAccount.warning')}</Body>
      <Body muted>{t('deleteAccount.exportHint')}</Body>
      <Button label={t('deleteAccount.exportJson')} variant="secondary" disabled={exporting !== null || busy} busy={exporting === 'json'} onPress={() => runExport('json')} />
      <Button label={t('deleteAccount.exportCsv')} variant="secondary" disabled={exporting !== null || busy} busy={exporting === 'csv'} onPress={() => runExport('csv')} />
      {exported ? <Notice kind="info" text={exportDoneText(exported, 'deleteAccount.exported')} /> : null}
      {exportError ? <Notice kind="error" text={exportError} /> : null}
      {!exported?.complete ? <Body muted>{t('deleteAccount.exportRequired')}</Body> : null}
      {error ? <Notice kind="error" text={error} /> : null}
      <Field label={t('deleteAccount.confirmLabel')} value={typed} onChangeText={setTyped} autoCapitalize="characters" autoCorrect={false} />
      <Button label={t('deleteAccount.confirm')} variant="danger" onPress={run} disabled={!allowed} busy={busy} />
      <Button label={t('common.cancel')} variant="secondary" onPress={onCancel} />
    </Screen>
  );
}

// S24b Remove plant (export first, warning, typed confirmation) and S24c (keep or release the sensor).
// Requirements: FR-A08, A-022 (delete_plant, sensor stays claimed until released), NFR-07 (readings and photos deleted; export before delete, photo objects removed from storage).
// Export gate: GET /export (all of the user's data, openapi.yaml) must have succeeded before the delete button can be pressed (src/export/exportGate.ts).
import React, { useState } from 'react';
import { Body, Button, Field, Notice, Screen } from '../ui/primitives';
import { t } from '../i18n';
import { usePlants } from '../plants/PlantsContext';
import { exportDoneText, exportErrorText } from '../export/exportErrorText';
import { PlantsError, type ExportResult, type PlantSummary } from '../plants/types';
import { canDelete } from '../export/exportGate';

export interface RemoveOutcome { plantName: string; deviceId: string | null; sensorName: string | null; orphanPhotoPaths: string[] }

export function RemovePlantScreen({ plant, onCancel, onRemoved }: { plant: PlantSummary; onCancel: () => void; onRemoved: (r: RemoveOutcome) => void }) {
  const svc = usePlants();
  const [typed, setTyped] = useState('');
  const [busy, setBusy] = useState(false);
  const [exporting, setExporting] = useState<'json' | 'csv' | null>(null);
  const [exported, setExported] = useState<ExportResult | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const allowed = canDelete({ exported: exported?.complete === true, typed, expected: plant.name });

  const runExport = async (format: 'json' | 'csv') => {
    setExporting(format); setExportError(null);
    try { setExported(await svc.exportData(format)); }
    catch (e) { setExported(null); setExportError(exportErrorText(e, 'plant.remove.exportError')); }
    finally { setExporting(null); }
  };
  const remove = async () => {
    if (!allowed) return;
    setBusy(true); setError(null);
    let photoPaths: string[];
    try { ({ photoPaths } = await svc.deletePlant(plant.id)); }
    catch { setError(t('plant.remove.error')); setBusy(false); return; }
    // NFR-07: the caller removes the photo objects (SQL cannot). A failure here keeps the paths on the next screen for a retry.
    const orphanPhotoPaths: string[] = [];
    try { await svc.removePhotoObjects(photoPaths); } catch (e) { orphanPhotoPaths.push(...(e instanceof PlantsError && e.leftover ? e.leftover : photoPaths)); }
    onRemoved({ plantName: plant.name, deviceId: plant.deviceId, sensorName: plant.deviceName, orphanPhotoPaths });
  };

  return (
    <Screen title={t('plant.remove.title', { plantName: plant.name })}>
      <Body>{t('plant.remove.warning')}</Body>
      <Body muted>{t('plant.remove.exportHint')}</Body>
      <Button label={t('plant.remove.exportJson')} variant="secondary" disabled={exporting !== null} busy={exporting === 'json'} onPress={() => runExport('json')} />
      <Button label={t('plant.remove.exportCsv')} variant="secondary" disabled={exporting !== null} busy={exporting === 'csv'} onPress={() => runExport('csv')} />
      {exported ? <Notice kind="info" text={exportDoneText(exported, 'plant.remove.exported')} /> : null}
      {exportError ? <Notice kind="error" text={exportError} /> : null}
      <Field label={t('plant.remove.confirmLabel')} value={typed} onChangeText={setTyped} autoCapitalize="none" autoCorrect={false} />
      {error ? <Notice kind="error" text={error} /> : null}
      {!exported?.complete ? <Body muted>{t('plant.remove.exportRequired')}</Body> : null}
      <Button label={t('plant.remove.confirm')} variant="danger" disabled={!allowed} busy={busy} onPress={remove} />
      <Button label={t('plant.remove.cancel')} variant="secondary" onPress={onCancel} />
    </Screen>
  );
}

export function PlantRemovedScreen({ plantName, deviceId, sensorName, orphanPhotoPaths, onDone }: { plantName: string; deviceId: string | null; sensorName: string | null; orphanPhotoPaths: string[]; onDone: () => void }) {
  const svc = usePlants();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [orphans, setOrphans] = useState(orphanPhotoPaths);
  const retryPhotos = async () => {
    setBusy(true); setError(null);
    try { await svc.removePhotoObjects(orphans); setOrphans([]); }
    catch (e) { if (e instanceof PlantsError && e.leftover) setOrphans(e.leftover); setError(t('plant.removed.photosError')); }
    setBusy(false);
  };
  const release = async () => {
    if (!deviceId) return;
    setBusy(true); setError(null);
    try { await svc.releaseDevice(deviceId); onDone(); } catch { setError(t('plant.removed.releaseError')); setBusy(false); }
  };
  return (
    <Screen title={t('plant.removed.title', { plantName })}>
      {orphans.length > 0 ? (
        <>
          <Notice kind="error" text={t('plant.removed.photosLeft', { n: orphans.length })} />
          <Button label={t('plant.removed.retryPhotos')} variant="secondary" busy={busy} onPress={retryPhotos} />
        </>
      ) : null}
      {deviceId ? (
        <>
          <Body>{t('plant.removed.body', { sensorName: sensorName ?? '' })}</Body>
          {error ? <Notice kind="error" text={error} /> : null}
          <Button label={t('plant.removed.keepSensor')} variant="secondary" onPress={onDone} />
          <Button label={t('plant.removed.releaseSensor')} variant="danger" busy={busy} onPress={release} />
          <Body muted>{t('plant.removed.releaseHint')}</Body>
        </>
      ) : (
        <>
          <Body>{t('plant.removed.noSensor')}</Body>
          {error ? <Notice kind="error" text={error} /> : null}
          <Button label={t('plant.removed.done')} onPress={onDone} />
        </>
      )}
    </Screen>
  );
}

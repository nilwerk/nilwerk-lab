// S24b Remove plant (warning + typed confirmation) and S24c (keep or release the sensor). Requirements: FR-A08, A-022 (delete_plant, sensor stays claimed until released), NFR-07 (readings/photos deleted).
// Not built: "Export first" (GET /export + share sheet) - see README gaps.
import React, { useState } from 'react';
import { Body, Button, Field, Notice, Screen } from '../ui/primitives';
import { t } from '../i18n';
import { usePlants } from '../plants/PlantsContext';
import type { PlantSummary } from '../plants/types';

export function RemovePlantScreen({ plant, onCancel, onRemoved }: { plant: PlantSummary; onCancel: () => void; onRemoved: () => void }) {
  const svc = usePlants();
  const [typed, setTyped] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const ok = typed.trim() === plant.name;
  const remove = async () => {
    if (!ok) return;
    setBusy(true); setError(null);
    try { await svc.deletePlant(plant.id); onRemoved(); } catch { setError(t('plant.remove.error')); setBusy(false); }
  };
  return (
    <Screen title={t('plant.remove.title', { plantName: plant.name })}>
      <Body>{t('plant.remove.warning')}</Body>
      <Field label={t('plant.remove.confirmLabel')} value={typed} onChangeText={setTyped} autoCapitalize="none" autoCorrect={false} />
      {error ? <Notice kind="error" text={error} /> : null}
      <Button label={t('plant.remove.confirm')} variant="danger" disabled={!ok} busy={busy} onPress={remove} />
      <Button label={t('plant.remove.cancel')} variant="secondary" onPress={onCancel} />
    </Screen>
  );
}

export function PlantRemovedScreen({ plantName, deviceId, sensorName, onDone }: { plantName: string; deviceId: string | null; sensorName: string | null; onDone: () => void }) {
  const svc = usePlants();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const release = async () => {
    if (!deviceId) return;
    setBusy(true); setError(null);
    try { await svc.releaseDevice(deviceId); onDone(); } catch { setError(t('plant.removed.releaseError')); setBusy(false); }
  };
  return (
    <Screen title={t('plant.removed.title', { plantName })}>
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
          <Button label={t('plant.removed.done')} onPress={onDone} />
        </>
      )}
    </Screen>
  );
}

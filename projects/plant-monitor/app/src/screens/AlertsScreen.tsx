// S30 Alerts list (4.A5; S31 alert detail is not built). Requirements: FR-A07 (alerts for too dry, too wet, low battery, offline; push delivery is NOT built), FR-D06 (low battery 3.4 V), FR-A06 (reached from the plant list).
// Rules: src/plants/alerts.ts (pure, unit-tested). Data: the plants service, so in the mock build every plant, reading and alert is MOCK (the shell shows app.mockBanner).
import React, { useCallback, useEffect, useState } from 'react';
import { Body, Button, Notice, Screen } from '../ui/primitives';
import { StatusChip } from '../ui/StatusChip';
import { Card, EmptyState } from '../ui/kit';
import { Stack, Type } from '../ui/layout';
import { t } from '../i18n';
import { usePlants } from '../plants/PlantsContext';
import { alertsForPlant, type RuleAlert } from '../plants/alerts';
import type { ChipKind } from '../plants/status';
import { PlantsError } from '../plants/types';

interface Row { plantId: string; plantName: string; alert: RuleAlert }

const CHIP: Record<RuleAlert['kind'], ChipKind> = { device_offline: 'offline', too_dry: 'dry', too_wet: 'wet', low_battery: 'lowBattery' };

/** The sentence under the chip, as a catalogue key with values filled in. */
export function alertCopy(a: RuleAlert): string {
  switch (a.kind) {
    case 'too_dry': return t('alerts.text.too_dry', { value: a.value.toFixed(1), threshold: a.threshold });
    case 'too_wet': return t('alerts.text.too_wet', { value: a.value.toFixed(1), threshold: a.threshold });
    case 'low_battery': return t('alerts.text.low_battery', { value: (a.value / 1000).toFixed(2), threshold: (a.threshold / 1000).toFixed(2) });
    case 'device_offline': return t('alerts.text.device_offline', { hours: Math.floor(a.value / 60), minutes: a.value % 60 });
  }
}

export function AlertsScreen({ onBack, onCount }: { onBack: () => void; onCount?: (n: number) => void }) {
  const svc = usePlants();
  const [rows, setRows] = useState<Row[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const plants = await svc.listPlants();
      const now = new Date();
      // plants without a sensor cannot raise alerts (alertsForPlant returns none), so they are not fetched
      const details = await Promise.all(plants.filter((p) => p.deviceId !== null).map((p) => svc.getPlantDetail(p.id)));
      const next = details.flatMap((d) => alertsForPlant(d.plant, d.hourly, now).map((alert) => ({ plantId: d.plant.id, plantName: d.plant.name, alert })));
      setRows(next);
      onCount?.(new Set(next.map((r) => r.plantId)).size);
    } catch (e) {
      setError(t(e instanceof PlantsError && e.code === 'not_configured' ? 'plants.error.notConnected' : 'alerts.error.load'));
    }
  }, [svc, onCount]);
  useEffect(() => { load(); }, [load]);

  return (
    <Screen title={t('alerts.title')} onBack={onBack}>
      <Body muted>{t('alerts.intro')}</Body>
      {error ? <Notice kind="error" text={error} /> : null}
      {error ? <Button label={t('common.tryAgain')} variant="secondary" onPress={load} /> : null}
      {rows === null && !error ? <Body muted>{t('common.loading')}</Body> : null}
      {rows && rows.length === 0 ? (
        <EmptyState title={t('alerts.empty.title')} body={t('alerts.empty.body')} />
      ) : null}
      <Stack>
        {rows?.map((r) => (
          <Card key={`${r.plantId}-${r.alert.kind}`}>
            <Type variant="h3" header>{r.plantName}</Type>
            <StatusChip kind={CHIP[r.alert.kind]} />
            <Type>{alertCopy(r.alert)}</Type>
          </Card>
        ))}
      </Stack>
      {rows && rows.length > 0 ? <Button label={t('alerts.refresh')} variant="ghost" onPress={load} /> : null}
    </Screen>
  );
}

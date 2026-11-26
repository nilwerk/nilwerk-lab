// S20 Plant list. Requirements: FR-A06 (list with status chips), FR-A02 (no cap on plants/devices), NFR-06 (own rows only under RLS).
// "+ Add" / "Add your first sensor" (S10, FR-A03) is 4.A3 and not wired here.
// "View alerts" opens the alerts list (4.A5, FR-A07); it is the only way to reach alerts for now.
import React, { useCallback, useEffect, useState } from 'react';
import { Pressable } from 'react-native';
import { Body, Button, Notice, Screen } from '../ui/primitives';
import { StatusChip } from '../ui/StatusChip';
import { Card, Caption, EmptyState } from '../ui/kit';
import { Row, Column, Type } from '../ui/kit';
import { t } from '../i18n';
import { usePlants } from '../plants/PlantsContext';
import { countOpenAlertPlants, plantChips } from '../plants/status';
import { PlantsError, type PlantSummary } from '../plants/types';

export const loadErrorKey = (e: unknown) => (e instanceof PlantsError && e.code === 'not_configured' ? 'plants.error.notConnected' : 'plants.error.load');

export function PlantsScreen({ onOpen, onAlerts, onCount }: { onOpen: (plantId: string) => void; onAlerts: () => void; onCount?: (n: number) => void }) {
  const svc = usePlants();
  const [plants, setPlants] = useState<PlantSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try { const ps = await svc.listPlants(); setPlants(ps); onCount?.(countOpenAlertPlants(ps)); } catch (e) { setError(t(loadErrorKey(e))); }
  }, [svc, onCount]);
  useEffect(() => { load(); }, [load]);

  return (
    <Screen fade title={t('plants.title')}>
      {error ? <Notice kind="error" text={error} /> : null}
      {error ? <Button label={t('common.tryAgain')} variant="secondary" onPress={load} /> : null}
      {plants === null && !error ? <Body muted>{t('common.loading')}</Body> : null}
      {plants && plants.length === 0 ? <EmptyState title={t('plants.empty.title')} body={t('plants.empty.body')} /> : null}
      {plants && plants.length > 0 ? <Button label={t('plants.alerts.button')} variant="secondary" onPress={onAlerts} /> : null}
      <Column>{plants?.map((p) => <PlantRow key={p.id} plant={p} onOpen={() => onOpen(p.id)} />)}</Column>
      {plants && plants.length > 0 ? <Button label={t('plants.refresh')} variant="ghost" onPress={load} /> : null}
    </Screen>
  );
}

function PlantRow({ plant, onOpen }: { plant: PlantSummary; onOpen: () => void }) {
  const chips = plantChips(plant);
  const m = plant.latest?.moisturePct;
  const value = m === null || m === undefined ? t('plants.noValue') : t('plants.soilValue', { value: Math.round(m) });
  const statusText = chips.map((c) => t(c === 'noSensor' ? 'status.noSensor' : `status.${c}`)).join(', ');
  const label = plant.area
    ? t('plants.row.a11y', { name: plant.name, area: plant.area, status: statusText, value })
    : t('plants.row.a11yNoArea', { name: plant.name, status: statusText, value });
  return (
    <Pressable accessibilityRole="button" accessibilityLabel={label} onPress={onOpen}>
      <Card>
        <Row between align="flex-start" gap="md">
          <Column gap="xs">
            <Type variant="h3" flex>{plant.name}</Type>
            <Caption>{plant.area ?? t('plants.noArea')}</Caption>
          </Column>
          <Type variant="bodyStrong">{value}</Type>
        </Row>
        <Row wrap>{chips.map((c) => <StatusChip key={c} kind={c} />)}</Row>
      </Card>
    </Pressable>
  );
}

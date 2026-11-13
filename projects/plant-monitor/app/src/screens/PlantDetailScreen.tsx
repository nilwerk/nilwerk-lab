// S21 Plant detail. Requirements: FR-A06 (latest values = last report, 7-day hourly chart), FR-A08 (entry to remove, A-022), FR-A07 (dry/wet thresholds drawn on the chart), NFR-06.
// Photos / hourly table / care tips rows (S22, S23, S42) are later slices.
import React, { useCallback, useEffect, useState } from 'react';
import { Text, View } from 'react-native';
import { Body, Button, Notice, Screen } from '../ui/primitives';
import { StatusChip } from '../ui/StatusChip';
import { MoistureChart } from '../ui/MoistureChart';
import { useTheme } from '../ui/useTheme';
import { t } from '../i18n';
import { usePlants } from '../plants/PlantsContext';
import { ageParts, plantChips } from '../plants/status';
import { PlantsError, type PlantDetail } from '../plants/types';

const fmt = (v: number | null | undefined, digits: number) => (v === null || v === undefined ? null : v.toFixed(digits));

export function PlantDetailScreen({ plantId, onBack, onRemove, now = () => new Date() }: { plantId: string; onBack: () => void; onRemove: (d: PlantDetail) => void; now?: () => Date }) {
  const th = useTheme();
  const svc = usePlants();
  const [detail, setDetail] = useState<PlantDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try { setDetail(await svc.getPlantDetail(plantId)); }
    catch (e) { setError(t(e instanceof PlantsError && e.code === 'not_found' ? 'plant.error.notFound' : 'plant.error.load')); }
  }, [svc, plantId]);
  useEffect(() => { load(); }, [load]);

  const p = detail?.plant;
  const l = p?.latest;
  const age = ageParts(l?.ts ?? p?.lastSeenAt ?? null, now());
  const cell = (labelKey: string, valueKey: string, v: string | null) => (
    <View key={labelKey} style={{ flexBasis: '47%', flexGrow: 1, padding: th.spacing.md, borderRadius: th.radius.md, borderWidth: 1, borderColor: th.color.line, backgroundColor: th.color.surface }}>
      <Text style={{ color: th.color.muted, ...th.type.caption }}>{t(labelKey)}</Text>
      <Text style={{ color: th.color.ink, ...th.type.h2 }}>{v === null ? t('plant.latest.none') : t(valueKey, { value: v })}</Text>
    </View>
  );

  return (
    <Screen title={p?.name ?? t('plants.title')} onBack={onBack}>
      {error ? <Notice kind="error" text={error} /> : null}
      {error ? <Button label={t('common.tryAgain')} variant="secondary" onPress={load} /> : null}
      {!detail && !error ? <Body muted>{t('common.loading')}</Body> : null}
      {p ? (
        <>
          <Body muted>{p.area ?? t('plants.noArea')}</Body>
          <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: th.spacing.sm }}>{plantChips(p).map((c) => <StatusChip key={c} kind={c} />)}</View>
          <Text style={{ color: th.color.muted, ...th.type.caption }}>{t(age.key, age.n === undefined ? undefined : { n: age.n })}</Text>
          <Text accessibilityRole="header" style={{ color: th.color.ink, ...th.type.h3 }}>{t('plant.latest.title')}</Text>
          <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: th.spacing.sm }}>
            {cell('plant.latest.soil', 'plant.latest.soilValue', fmt(l?.moisturePct, 0))}
            {cell('plant.latest.temp', 'plant.latest.tempValue', fmt(l?.tempC, 1))}
            {cell('plant.latest.humidity', 'plant.latest.humidityValue', fmt(l?.rhPct, 0))}
            {cell('plant.latest.light', 'plant.latest.lightValue', fmt(l?.lux, 0))}
            {cell('plant.latest.battery', 'plant.latest.batteryValue', l?.vbatMv == null ? null : (l.vbatMv / 1000).toFixed(2))}
          </View>
          <MoistureChart points={detail.hourly} dry={p.dryThresholdPct} wet={p.wetThresholdPct} />
          <Button label={t('plant.remove.button')} variant="danger" onPress={() => onRemove(detail)} />
        </>
      ) : null}
    </Screen>
  );
}

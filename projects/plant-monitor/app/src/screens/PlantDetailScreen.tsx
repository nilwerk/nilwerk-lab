// S21 Plant detail. Requirements: FR-A06 (latest values = last report, 7-day hourly chart and hourly table), FR-A04 (location type, room, soil type shown), FR-A05 (entry to the photo gallery), FR-A08 (entry to remove, A-022), FR-A07 (dry/wet thresholds drawn on the chart), NFR-06.
// Care tips rows (S42) are a later slice.
import React, { useCallback, useEffect, useState } from 'react';
import { Text, View } from 'react-native';
import { Body, Button, Notice, Screen } from '../ui/primitives';
import { StatusChip } from '../ui/StatusChip';
import { MoistureChart } from '../ui/MoistureChart';
import { HourlyTable } from '../ui/HourlyTable';
import { PlantMeta } from '../ui/PlantMeta';
import { Card, Caption, SectionTitle } from '../ui/kit';
import { useTheme } from '../ui/useTheme';
import { t } from '../i18n';
import { usePlants } from '../plants/PlantsContext';
import { ageParts, plantChips } from '../plants/status';
import { PlantsError, type PlantDetail, type PlantSummary } from '../plants/types';

const fmt = (v: number | null | undefined, digits: number) => (v === null || v === undefined ? null : v.toFixed(digits));

export function PlantDetailScreen({ plantId, onBack, onRemove, onGallery, now = () => new Date() }: { plantId: string; onBack: () => void; onRemove: (d: PlantDetail) => void; onGallery: (p: PlantSummary) => void; now?: () => Date }) {
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
    <Card key={labelKey}>
      <Caption>{t(labelKey)}</Caption>
      <Text style={{ color: th.color.ink, ...th.type.h2 }}>{v === null ? t('plant.latest.none') : t(valueKey, { value: v })}</Text>
    </Card>
  );

  return (
    <Screen title={p?.name ?? t('plants.title')} onBack={onBack}>
      {error ? <Notice kind="error" text={error} /> : null}
      {error ? <Button label={t('common.tryAgain')} variant="secondary" onPress={load} /> : null}
      {!detail && !error ? <Body muted>{t('common.loading')}</Body> : null}
      {p ? (
        <>
          <PlantMeta plant={p} />
          <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: th.spacing.sm }}>{plantChips(p).map((c) => <StatusChip key={c} kind={c} />)}</View>
          <Text style={{ color: th.color.muted, ...th.type.caption }}>{t(age.key, age.n === undefined ? undefined : { n: age.n })}</Text>
          <SectionTitle>{t('plant.latest.title')}</SectionTitle>
          <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: th.spacing.sm }}>
            {cell('plant.latest.soil', 'plant.latest.soilValue', fmt(l?.moisturePct, 0))}
            {cell('plant.latest.temp', 'plant.latest.tempValue', fmt(l?.tempC, 1))}
            {cell('plant.latest.humidity', 'plant.latest.humidityValue', fmt(l?.rhPct, 0))}
            {cell('plant.latest.light', 'plant.latest.lightValue', fmt(l?.lux, 0))}
            {cell('plant.latest.battery', 'plant.latest.batteryValue', l?.vbatMv == null ? null : (l.vbatMv / 1000).toFixed(2))}
          </View>
          <MoistureChart points={detail.hourly} dry={p.dryThresholdPct} wet={p.wetThresholdPct} />
          <HourlyTable points={detail.hourly} />
          <Button label={t('plant.photos.button')} variant="secondary" onPress={() => onGallery(p)} />
          <Button label={t('plant.remove.button')} variant="danger" onPress={() => onRemove(detail)} />
        </>
      ) : null}
    </Screen>
  );
}

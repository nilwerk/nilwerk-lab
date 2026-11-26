// S20 Plant list. Requirements: FR-A06 (list with status chips), FR-A02 (no cap on plants/devices), NFR-06 (own rows only under RLS).
// "+ Add" / "Add your first sensor" (S10, FR-A03) is 4.A3 and not wired here.
// "View alerts" opens the alerts list (4.A5, FR-A07); it is the only way to reach alerts for now.
import React, { useCallback, useEffect, useState } from 'react';
import { Pressable, Text, View } from 'react-native';
import { Body, Button, Notice, Screen } from '../ui/primitives';
import { StatusChip } from '../ui/StatusChip';
import { useTheme } from '../ui/useTheme';
import { t } from '../i18n';
import { usePlants } from '../plants/PlantsContext';
import { attentionCounts, plantChips } from '../plants/status';
import { PlantsError, type PlantSummary } from '../plants/types';

export const loadErrorKey = (e: unknown) => (e instanceof PlantsError && e.code === 'not_configured' ? 'plants.error.notConnected' : 'plants.error.load');

/** Lists longer than this keep the title at the top while scrolling (v3, sticky title). */
const LONG_LIST = 4;
export const isLongList = (n: number) => n > LONG_LIST;

export function PlantsScreen({ onOpen, onAlerts, onAddSensor }: { onOpen: (plantId: string) => void; onAlerts: () => void; onAddSensor: () => void }) {
  const th = useTheme();
  const svc = usePlants();
  const [plants, setPlants] = useState<PlantSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [howOpen, setHowOpen] = useState(false);

  const load = useCallback(async () => {
    setError(null);
    try { setPlants(await svc.listPlants()); } catch (e) { setError(t(loadErrorKey(e))); }
  }, [svc]);
  useEffect(() => { load(); }, [load]);

  // Counts come from the plant list this screen already loaded (no endpoint). Shown only when at least one count is above zero.
  const counts = plants ? attentionCounts(plants) : null;
  const needsAttention = counts !== null && counts.dry + counts.wet + counts.lowBattery > 0;

  return (
    <Screen title={t('plants.title')} stickyTitle={!!plants && isLongList(plants.length)}>
      {error ? <Notice kind="error" text={error} /> : null}
      {error ? <Button label={t('common.tryAgain')} variant="secondary" onPress={load} /> : null}
      {plants === null && !error ? <Body muted>{t('common.loading')}</Body> : null}
      {counts && needsAttention ? (
        <View accessibilityRole="summary" style={{ padding: th.spacing.md, gap: th.spacing.xs, borderRadius: th.radius.lg, borderWidth: 1, borderColor: th.color.line, backgroundColor: th.color.surface }}>
          <Text style={{ color: th.color.muted, ...th.type.caption }}>{t('plants.attention.title')}</Text>
          <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: th.spacing.sm }}>
            {counts.dry > 0 ? <Text style={{ color: th.color.ink, ...th.type.bodyStrong }}>{t('plants.attention.dry', { n: counts.dry })}</Text> : null}
            {counts.wet > 0 ? <Text style={{ color: th.color.ink, ...th.type.bodyStrong }}>{t('plants.attention.wet', { n: counts.wet })}</Text> : null}
            {counts.lowBattery > 0 ? <Text style={{ color: th.color.ink, ...th.type.bodyStrong }}>{t('plants.attention.lowBattery', { n: counts.lowBattery })}</Text> : null}
          </View>
        </View>
      ) : null}
      {plants && plants.length === 0 ? (
        <View style={{ gap: th.spacing.md }}>
          <Text accessibilityRole="header" style={{ color: th.color.ink, ...th.type.h3 }}>{t('plants.empty.title')}</Text>
          <Body muted>{t('plants.empty.body')}</Body>
          <Button label={t('plants.empty.addFirst')} variant="primary" onPress={onAddSensor} />
          <Button label={howOpen ? t('plants.empty.howHide') : t('plants.empty.howLink')} variant="ghost" onPress={() => setHowOpen((v) => !v)} />
          {howOpen ? (
            <View style={{ gap: th.spacing.sm, padding: th.spacing.md, borderRadius: th.radius.md, backgroundColor: th.color.surface, borderWidth: 1, borderColor: th.color.line }}>
              <Body>{t('plants.empty.how1')}</Body>
              <Body>{t('plants.empty.how2')}</Body>
              <Body>{t('plants.empty.how3')}</Body>
            </View>
          ) : null}
        </View>
      ) : null}
      {plants && plants.length > 0 ? <Button label={t('plants.alerts.button')} variant="secondary" onPress={onAlerts} /> : null}
      {plants?.map((p) => <PlantRow key={p.id} plant={p} onOpen={() => onOpen(p.id)} />)}
      {plants && plants.length > 0 ? <Button label={t('plants.refresh')} variant="ghost" onPress={load} /> : null}
    </Screen>
  );
}

function PlantRow({ plant, onOpen }: { plant: PlantSummary; onOpen: () => void }) {
  const th = useTheme();
  const chips = plantChips(plant);
  const m = plant.latest?.moisturePct;
  const value = m === null || m === undefined ? t('plants.noValue') : t('plants.soilValue', { value: Math.round(m) });
  const statusText = chips.map((c) => t(c === 'noSensor' ? 'status.noSensor' : `status.${c}`)).join(', ');
  const label = plant.area
    ? t('plants.row.a11y', { name: plant.name, area: plant.area, status: statusText, value })
    : t('plants.row.a11yNoArea', { name: plant.name, status: statusText, value });
  return (
    <Pressable accessibilityRole="button" accessibilityLabel={label} onPress={onOpen}
      style={{ minHeight: th.minTouchTarget, padding: th.spacing.lg, gap: th.spacing.sm, borderRadius: th.radius.lg, borderWidth: 1, borderColor: th.color.line, backgroundColor: th.color.surface }}>
      <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', gap: th.spacing.md }}>
        <View style={{ flex: 1 }}>
          <Text style={{ color: th.color.ink, ...th.type.h3 }}>{plant.name}</Text>
          <Text style={{ color: th.color.muted, ...th.type.caption }}>{plant.area ?? t('plants.noArea')}</Text>
        </View>
        <Text style={{ color: th.color.ink, ...th.type.bodyStrong }}>{value}</Text>
      </View>
      <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: th.spacing.sm }}>{chips.map((c) => <StatusChip key={c} kind={c} />)}</View>
    </Pressable>
  );
}

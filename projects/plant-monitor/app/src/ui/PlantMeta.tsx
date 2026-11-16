// Plant metadata shown on the detail (S21) and gallery (S23) screens: location type, room or area, soil type. Requirement: FR-A04 (edit fields), shown here read-only.
import React from 'react';
import { Text, View } from 'react-native';
import { useTheme } from './useTheme';
import { t } from '../i18n';
import type { PlantSummary } from '../plants/types';

export function PlantMeta({ plant }: { plant: Pick<PlantSummary, 'locationType' | 'area' | 'soilType'> }) {
  const th = useTheme();
  const row = (labelKey: string, value: string, testID: string) => (
    <View key={labelKey} testID={testID} style={{ flexBasis: '47%', flexGrow: 1, padding: th.spacing.md, borderRadius: th.radius.md, borderWidth: 1, borderColor: th.color.line, backgroundColor: th.color.surface }}>
      <Text style={{ color: th.color.muted, ...th.type.caption }}>{t(labelKey)}</Text>
      <Text style={{ color: th.color.ink, ...th.type.bodyStrong }}>{value}</Text>
    </View>
  );
  return (
    <View accessibilityLabel={t('plant.meta.a11y', { location: t(`setup.location.${plant.locationType}`), room: plant.area ?? t('plants.noArea'), soil: t(`setup.soil.${plant.soilType}`) })}
      style={{ flexDirection: 'row', flexWrap: 'wrap', gap: th.spacing.sm }}>
      {row('plant.meta.location', t(`setup.location.${plant.locationType}`), 'plant-meta-location')}
      {row('plant.meta.room', plant.area ?? t('plants.noArea'), 'plant-meta-room')}
      {row('plant.meta.soil', t(`setup.soil.${plant.soilType}`), 'plant-meta-soil')}
    </View>
  );
}

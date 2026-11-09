// Status chip: shape glyph + text label + colour (never colour alone). Colours and label keys from theme.ts statusMeta (A-040).
import React from 'react';
import { Text, View } from 'react-native';
import { statusStyle } from '../../theme';
import type { ChipKind } from '../plants/status';
import { useColorScheme } from 'react-native';
import { useTheme } from './useTheme';
import { t } from '../i18n';

const GLYPH: Record<string, string> = { circle: '●', triangle: '▲', diamond: '◆', square: '■', ring: '○', cross: '✕' };

export function StatusChip({ kind }: { kind: ChipKind }) {
  const th = useTheme();
  const scheme = useColorScheme();
  const st = statusStyle(kind === 'noSensor' ? 'offline' : kind, scheme);
  const label = kind === 'noSensor' ? t('status.noSensor') : t(st.labelKey);
  return (
    <View
      accessible
      accessibilityLabel={t('a11y.chip', { status: label })}
      style={{ flexDirection: 'row', alignItems: 'center', gap: th.spacing.xs, alignSelf: 'flex-start', paddingHorizontal: th.spacing.sm, paddingVertical: th.spacing.xs, borderRadius: th.radius.pill, backgroundColor: st.background }}
    >
      <Text accessibilityElementsHidden importantForAccessibility="no" style={{ color: st.color, ...th.type.caption }}>{GLYPH[st.shape]}</Text>
      <Text style={{ color: st.color, ...th.type.caption, fontFamily: th.fontFamily.bodyStrong }}>{label}</Text>
    </View>
  );
}

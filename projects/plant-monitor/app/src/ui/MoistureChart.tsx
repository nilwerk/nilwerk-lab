// 7-day hourly soil-moisture chart (FR-A06: up to 168 hourly points). Plain Views (one bar per hour), no chart/SVG dependency.
// Gaps (null) stay empty. Dashed-style threshold lines mark dry/wet (FR-A07 thresholds are data, read from the plant). Summary is announced as text.
import React from 'react';
import { Text, View } from 'react-native';
import { useTheme } from './useTheme';
import { t } from '../i18n';
import type { HourlyPoint } from '../plants/types';

export const CHART_HEIGHT = 120;

export function chartSummary(points: HourlyPoint[]) {
  const vals = points.map((p) => p.moisturePct).filter((v): v is number => v !== null);
  if (!vals.length) return null;
  const last = [...points].reverse().find((p) => p.moisturePct !== null)!.moisturePct as number;
  return { count: vals.length, min: Math.min(...vals), max: Math.max(...vals), last };
}

export function MoistureChart({ points, dry, wet }: { points: HourlyPoint[]; dry: number; wet: number }) {
  const th = useTheme();
  const s = chartSummary(points);
  if (!s) return <Text style={{ color: th.color.muted, ...th.type.body }}>{t('plant.chart.empty')}</Text>;
  const y = (pct: number) => (Math.max(0, Math.min(100, pct)) / 100) * CHART_HEIGHT;
  const line = (pct: number, testID: string) => (
    <View testID={testID} pointerEvents="none" style={{ position: 'absolute', left: 0, right: 0, bottom: y(pct), borderTopWidth: 1, borderStyle: 'dashed', borderColor: th.color.muted }} />
  );
  return (
    <View style={{ gap: th.spacing.sm }}>
      <Text accessibilityRole="header" style={{ color: th.color.ink, ...th.type.h3 }}>{t('plant.chart.title')}</Text>
      <View
        testID="moisture-chart"
        accessible
        accessibilityRole="image"
        accessibilityLabel={t('plant.chart.a11y', { points: s.count, min: Math.round(s.min), max: Math.round(s.max), last: Math.round(s.last) })}
        style={{ height: CHART_HEIGHT, flexDirection: 'row', alignItems: 'flex-end', backgroundColor: th.color.surface, borderRadius: th.radius.md, borderWidth: 1, borderColor: th.color.line, overflow: 'hidden' }}
      >
        {points.map((p) => (
          <View key={p.hour} style={{ flex: 1, height: CHART_HEIGHT, justifyContent: 'flex-end' }}>
            {p.moisturePct === null ? null : (
              <View testID="chart-bar" style={{ height: Math.max(1, y(p.moisturePct)), backgroundColor: p.moisturePct < dry ? th.color.dry : p.moisturePct > wet ? th.color.wet : th.color.accent }} />
            )}
          </View>
        ))}
        {line(dry, 'chart-dry-line')}
        {line(wet, 'chart-wet-line')}
      </View>
      <Text style={{ color: th.color.muted, ...th.type.caption }}>{t('plant.chart.thresholds', { dry, wet })}</Text>
      <Text style={{ color: th.color.muted, ...th.type.caption }}>{t('plant.chart.premiumHint')}</Text>
    </View>
  );
}

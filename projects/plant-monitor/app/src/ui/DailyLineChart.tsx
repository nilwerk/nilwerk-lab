// Per-plant daily soil-moisture line chart (task 4.A6b, FR-P01; ADR-018). Plain Views, no chart/SVG dependency, as MoistureChart.tsx.
// Null days are gaps: no dot and the line stops (not 0, not interpolated). Readings per day are never drawn; only the day mean is.
// The chart is announced as one text summary (days with a value, days without). Width is measured with onLayout; no line is drawn before that.
import React, { useState } from 'react';
import { Text, View, type LayoutChangeEvent } from 'react-native';
import { useTheme } from './useTheme';
import { t } from '../i18n';
import type { DailyPoint } from '../analytics/analyticsModel';
import { dailyChartGeometry, dailyChartSummary } from '../analytics/dailyChart';

export const DAILY_CHART_HEIGHT = 160;
const DOT = 6;
const LINE = 2;

export function DailyLineChart({ daily }: { daily: DailyPoint[] }) {
  const th = useTheme();
  const [width, setWidth] = useState(0);
  const s = dailyChartSummary(daily);
  const cap = { color: th.color.muted, ...th.type.caption } as const;
  if (s.withValue === 0) return <Text style={{ color: th.color.muted, ...th.type.body }}>{t('dashboard.daily.noValues', { days: s.days })}</Text>;

  const g = dailyChartGeometry(daily);
  const onLayout = (e: LayoutChangeEvent) => setWidth(e.nativeEvent.layout.width);
  const px = (p: { x: number; y: number }) => ({ x: p.x * width, y: p.y * DAILY_CHART_HEIGHT });

  return (
    <View style={{ gap: th.spacing.xs }}>
      <View
        testID="daily-chart"
        accessible
        accessibilityRole="image"
        accessibilityLabel={t('dashboard.daily.a11y', { days: s.days, first: s.first ?? '', last: s.last ?? '', withValue: s.withValue, gaps: s.gaps })}
        onLayout={onLayout}
        style={{ height: DAILY_CHART_HEIGHT, borderRadius: th.radius.md, borderWidth: 1, borderColor: th.color.line, backgroundColor: th.color.surface, overflow: 'hidden' }}
      >
        <View pointerEvents="none" style={{ position: 'absolute', left: 0, right: 0, top: DAILY_CHART_HEIGHT / 2, borderTopWidth: 1, borderStyle: 'dashed', borderColor: th.color.line }} />
        {width > 0 ? g.segments.map(([a, b]) => {
          const p1 = px(a), p2 = px(b);
          const dx = p2.x - p1.x, dy = p2.y - p1.y;
          const len = Math.hypot(dx, dy);
          const angle = Math.atan2(dy, dx) * (180 / Math.PI);
          return (
            <View key={`s${a.index}`} testID="daily-segment" pointerEvents="none"
              style={{ position: 'absolute', width: len, height: LINE, left: (p1.x + p2.x) / 2 - len / 2, top: (p1.y + p2.y) / 2 - LINE / 2,
                backgroundColor: th.color.accent, transform: [{ rotate: `${angle}deg` }] }} />
          );
        }) : null}
        {width > 0 ? g.points.map((p) => {
          const q = px(p);
          return (
            <View key={`p${p.index}`} testID="daily-dot" pointerEvents="none"
              style={{ position: 'absolute', width: DOT, height: DOT, borderRadius: DOT / 2, left: q.x - DOT / 2, top: q.y - DOT / 2, backgroundColor: th.color.accent }} />
          );
        }) : null}
      </View>
      <Text style={cap}>{t('dashboard.daily.scale', { first: s.first ?? '', last: s.last ?? '' })}</Text>
    </View>
  );
}

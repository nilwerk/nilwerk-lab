// Hourly data table (S22 content, shown on the plant detail). Requirements: FR-A06 (7-day hourly readings, 168 rows), FR-D02 (one report per hour, so 24 rows per day with a report),
// FR-A06 and the readings_hourly design (a missing hour is shown as a gap, not as zero). Columns are the readings_hourly fields of the contract (db-schema.sql L214): moisture_avg, temp_avg, rh_avg, lux_avg, vbat_min_mv.
// Newest first. Gap = em dash. Empty series (no report in 7 days) shows the empty text instead of 168 gaps. Plain Views in a horizontal ScrollView, so it fits 390 px.
import React from 'react';
import { ScrollView, Text, View } from 'react-native';
import { useTheme } from './useTheme';
import { t } from '../i18n';
import { fmtHour } from '../plants/format';
import { hasAnyReading } from '../plants/hourly';
import type { HourlyPoint } from '../plants/types';

const dash = (v: number | null, digits: number) => (v === null ? t('hourly.gap') : v.toFixed(digits));

/** Cell texts for one hourly point, in column order (no units: the header carries them). */
export function hourlyCells(p: HourlyPoint): string[] {
  return [
    fmtHour(p.hour),
    dash(p.moistureAvg, 0),
    dash(p.tempAvg, 1),
    dash(p.rhAvg, 0),
    dash(p.luxAvg, 0),
    p.vbatMinMv === null ? t('hourly.gap') : (p.vbatMinMv / 1000).toFixed(2),
  ];
}

export function HourlyTable({ points }: { points: HourlyPoint[] }) {
  const th = useTheme();
  if (!hasAnyReading(points)) return <Text style={{ color: th.color.muted, ...th.type.body }}>{t('hourly.empty')}</Text>;
  const gaps = points.filter((p) => p.n === null).length;
  const headers = [t('hourly.col.time'), t('hourly.col.soil'), t('hourly.col.temp'), t('hourly.col.rh'), t('hourly.col.light'), t('hourly.col.battery')];
  const cell = (text: string, key: string, head = false) => (
    <Text key={key} numberOfLines={1} style={{ width: 84, color: head ? th.color.muted : th.color.ink, ...(head ? th.type.caption : th.type.body), paddingHorizontal: th.spacing.xs }}>{text}</Text>
  );
  const newestFirst = [...points].reverse();
  return (
    <View style={{ gap: th.spacing.sm }}>
      <Text accessibilityRole="header" style={{ color: th.color.ink, ...th.type.h3 }}>{t('hourly.title')}</Text>
      <ScrollView horizontal accessible accessibilityLabel={t('hourly.a11y', { rows: points.length, gaps })} style={{ borderRadius: th.radius.md, borderWidth: 1, borderColor: th.color.line, backgroundColor: th.color.surface }}>
        <View>
          <View testID="hourly-head" style={{ flexDirection: 'row', paddingVertical: th.spacing.xs, borderBottomWidth: 1, borderColor: th.color.line }}>
            {headers.map((h, i) => cell(h, `h${i}`, true))}
          </View>
          {newestFirst.map((p) => (
            <View key={p.hour} testID="hourly-row" style={{ flexDirection: 'row', paddingVertical: th.spacing.xs, borderBottomWidth: 1, borderColor: th.color.line }}>
              {hourlyCells(p).map((c, i) => cell(c, `${p.hour}-${i}`))}
            </View>
          ))}
        </View>
      </ScrollView>
    </View>
  );
}

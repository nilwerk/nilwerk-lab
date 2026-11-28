// S41 Premium dashboard (task 4.A6, daily line chart 4.A6b). Requirements: FR-P01 (30- and 90-day line chart from the daily series (4.A6b),
// aggregates, trends, watering events, plant comparison), FR-P04 (premium only: the plan is read first and free accounts never trigger the analytics call; the server still answers 403 premium_required and that shows the upgrade state too), NFR-06 (own plants only).
import React, { useCallback, useEffect, useState } from 'react';
import { View } from 'react-native';
import { Body, Button, Notice, Screen } from '../ui/primitives';
import { DailyLineChart } from '../ui/DailyLineChart';
import { BarRow, Caption, Card, ListItem, RangeMeter, SectionTitle, Stack, StatusWord, WrapRow } from '../ui/kit';
import { t } from '../i18n';
import { useAuth } from '../auth/AuthContext';
import type { AnalyticsService } from '../analytics/analyticsApi';
import { AnalyticsError } from '../analytics/analyticsApi';
import { ANALYTICS_WINDOWS, fmtPct, fmtSigned, fmtVolt, windowIsEmpty, type AnalyticsResponse, type AnalyticsWindow, type PlantAnalytics } from '../analytics/analyticsModel';

type Plan = 'checking' | 'premium' | 'free' | 'planError';
type Data = { status: 'idle' } | { status: 'loading' } | { status: 'error' } | { status: 'ready'; byWindow: Record<AnalyticsWindow, AnalyticsResponse> };

const clampPct = (n: number): number => Math.min(100, Math.max(0, n));

/** FR-P01 trend graph: first-week mean against last-week mean. Both values come from the response (no daily series is invented). */
function TrendGraph({ first, last, label }: { first: number; last: number; label: string }) {
  return (
    <View accessibilityRole="image" accessibilityLabel={label}>
      <Stack gap="xs">
        <BarRow label={t('dashboard.trend.first')} value={first} valueText={`${fmtPct(first)} %`} />
        <BarRow label={t('dashboard.trend.last')} value={last} valueText={`${fmtPct(last)} %`} />
      </Stack>
    </View>
  );
}

/** The trend is shown only when all three values are present (null weeks come from plants with gaps). */
function completeTrend(tr: PlantAnalytics['trend']): { change: number; first: number; last: number } | null {
  const { soilChangePct: change, firstWeekMean: first, lastWeekMean: last } = tr;
  return change !== null && first !== null && last !== null ? { change, first, last } : null;
}

function PlantRow({ p, windowDays }: { p: PlantAnalytics; windowDays: AnalyticsWindow }) {
  const trend = completeTrend(p.trend);
  return (
    <ListItem testID={`plant-row-${p.plantId}`}>
      <SectionTitle>{p.name}</SectionTitle>
      <Caption>{t('dashboard.plant.readings', { count: p.readingCount })}</Caption>
      {p.soilPct ? (
        <>
          <Body>{t('dashboard.plant.soil', { mean: fmtPct(p.soilPct.mean), min: fmtPct(p.soilPct.min), max: fmtPct(p.soilPct.max) })}</Body>
          <RangeMeter min={p.soilPct.min} max={p.soilPct.max} mean={p.soilPct.mean}
            label={t('dashboard.range.label', { min: fmtPct(p.soilPct.min), max: fmtPct(p.soilPct.max), mean: fmtPct(p.soilPct.mean) })} />
        </>
      ) : <Body muted>{t('dashboard.plant.noSoil')}</Body>}
      {p.batteryMv ? <Body>{t('dashboard.plant.battery', { mean: fmtVolt(p.batteryMv.mean), min: fmtVolt(p.batteryMv.min), max: fmtVolt(p.batteryMv.max) })}</Body> : null}
      <Body>{t('dashboard.plant.watering', { count: p.wateringEvents })}</Body>
      {trend ? (
        <>
          <Body>{t('dashboard.plant.trend', { change: fmtSigned(trend.change), first: fmtPct(trend.first), last: fmtPct(trend.last) })}</Body>
          <TrendGraph first={trend.first} last={trend.last}
            label={t('dashboard.trend.label', { first: fmtPct(trend.first), last: fmtPct(trend.last) })} />
        </>
      ) : <Body muted>{t('dashboard.plant.noTrend')}</Body>}
    </ListItem>
  );
}

/** FR-P01 (4.A6b): one line chart per plant of the 30- or 90-day window, switched with the buttons. Both windows were already fetched; no request is added. */
function DailySection({ byWindow }: { byWindow: Record<AnalyticsWindow, AnalyticsResponse> }) {
  const [days, setDays] = useState<AnalyticsWindow>(30);
  const data = byWindow[days];
  return (
    <Card>
      <SectionTitle>{t('dashboard.daily.title')}</SectionTitle>
      <Body muted>{t('dashboard.daily.intro')}</Body>
      <WrapRow>
        {ANALYTICS_WINDOWS.map((w) => (
          <Button key={w} label={t('dashboard.daily.switch', { days: w })} variant={w === days ? 'primary' : 'secondary'} onPress={() => setDays(w)} />
        ))}
      </WrapRow>
      {data.plants.length === 0 ? <Body muted>{t('dashboard.noPlants')}</Body>
        : windowIsEmpty(data) ? <Body muted>{t('dashboard.noReadings')}</Body>
        : data.plants.map((p) => (
          <ListItem key={p.plantId}>
            <Caption>{p.name}</Caption>
            {p.daily === null ? <Body muted>{t('dashboard.daily.notAvailable')}</Body> : <DailyLineChart daily={p.daily} />}
          </ListItem>
        ))}
    </Card>
  );
}

function WindowSection({ data }: { data: AnalyticsResponse }) {
  const title = t('dashboard.window.title', { days: data.windowDays });
  return (
    <Card>
      <SectionTitle>{title}</SectionTitle>
      {data.plants.length === 0 ? <Body muted>{t('dashboard.noPlants')}</Body>
        : windowIsEmpty(data) ? <Body muted>{t('dashboard.noReadings')}</Body>
        : data.plants.map((p) => <PlantRow key={p.plantId} p={p} windowDays={data.windowDays} />)}
    </Card>
  );
}

/** FR-P04: the plan comes from the server (profiles.is_premium via getProfile); nothing is fetched until it says premium. */
export function PremiumDashboardScreen({ analytics, onBack, onPremium }: { analytics: AnalyticsService; onBack: () => void; onPremium: () => void }) {
  const { service } = useAuth();
  const [plan, setPlan] = useState<Plan>('checking');
  const [data, setData] = useState<Data>({ status: 'idle' });

  const load = useCallback(async () => {
    setData({ status: 'loading' });
    try {
      const [a, b] = await Promise.all(ANALYTICS_WINDOWS.map((w) => analytics.fetchWindow(w)));
      setData({ status: 'ready', byWindow: { 30: a, 90: b } });
    } catch (e) {
      if (e instanceof AnalyticsError && e.code === 'premium_required') { setPlan('free'); setData({ status: 'idle' }); return; }
      setData({ status: 'error' });
    }
  }, [analytics]);

  const checkPlan = useCallback(async () => {
    setPlan('checking');
    try {
      const p = await service.getProfile();
      if (p.isPremium) { setPlan('premium'); await load(); } else { setPlan('free'); }
    } catch {
      setPlan('planError');
    }
  }, [service, load]);

  useEffect(() => { checkPlan(); }, [checkPlan]);

  const title = t('dashboard.title');
  if (plan === 'checking') return <Screen title={title} onBack={onBack}><Body muted>{t('common.loading')}</Body></Screen>;
  if (plan === 'planError') return (
    <Screen title={title} onBack={onBack}>
      <Notice kind="error" text={t('dashboard.profileError')} />
      <Button label={t('common.tryAgain')} variant="secondary" onPress={checkPlan} />
    </Screen>
  );
  if (plan === 'free') return (
    <Screen title={title} onBack={onBack}>
      <Card>
        <SectionTitle>{t('dashboard.upgrade.title')}</SectionTitle>
        <Body>{t('dashboard.upgrade.body')}</Body>
        <Button label={t('profile.whatIsPremium')} variant="secondary" onPress={onPremium} />
      </Card>
    </Screen>
  );

  return (
    <Screen title={title} onBack={onBack}>
      <Body muted>{t('dashboard.intro')}</Body>
      {data.status === 'loading' || data.status === 'idle' ? <Body muted>{t('dashboard.loading')}</Body> : null}
      {data.status === 'error' ? (
        <>
          <Notice kind="error" text={t('dashboard.error')} />
          <Button label={t('common.tryAgain')} variant="secondary" onPress={load} />
        </>
      ) : null}
      {data.status === 'ready' ? <DailySection byWindow={data.byWindow} /> : null}
      {data.status === 'ready' ? ANALYTICS_WINDOWS.map((w) => <WindowSection key={w} data={data.byWindow[w]} />) : null}
    </Screen>
  );
}

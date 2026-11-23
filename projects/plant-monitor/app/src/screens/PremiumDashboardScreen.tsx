// S41 Premium dashboard (task 4.A6). Requirements: FR-P01 (30- and 90-day aggregates, trends, watering events, plant comparison),
// FR-P04 (premium only: the plan is read first and free accounts never trigger the analytics call; the server still answers 403 premium_required and that shows the upgrade state too), NFR-06 (own plants only).
import React, { useCallback, useEffect, useState } from 'react';
import { Text, View } from 'react-native';
import { Body, Button, Notice, Screen } from '../ui/primitives';
import { useTheme } from '../ui/useTheme';
import { t } from '../i18n';
import { useAuth } from '../auth/AuthContext';
import type { AnalyticsService } from '../analytics/analyticsApi';
import { AnalyticsError } from '../analytics/analyticsApi';
import { ANALYTICS_WINDOWS, fmtPct, fmtSigned, fmtVolt, windowIsEmpty, type AnalyticsResponse, type AnalyticsWindow, type PlantAnalytics } from '../analytics/analyticsModel';

type Plan = 'checking' | 'premium' | 'free' | 'planError';
type Data = { status: 'idle' } | { status: 'loading' } | { status: 'error' } | { status: 'ready'; byWindow: Record<AnalyticsWindow, AnalyticsResponse> };

/** Bar for the soil mean on a 0-100 scale; the width comes from the response value only. */
function SoilBar({ mean, label }: { mean: number; label: string }) {
  const th = useTheme();
  const pct = Math.min(100, Math.max(0, mean));
  return (
    <View accessibilityRole="progressbar" accessibilityLabel={label} accessibilityValue={{ min: 0, max: 100, now: Math.round(pct) }}
      style={{ height: 8, borderRadius: 4, backgroundColor: th.color.line, overflow: 'hidden' }}>
      <View style={{ width: `${pct}%`, height: 8, backgroundColor: th.color.accent }} />
    </View>
  );
}

function PlantRow({ p, windowDays }: { p: PlantAnalytics; windowDays: AnalyticsWindow }) {
  const th = useTheme();
  const cap = { color: th.color.muted, ...th.type.caption } as const;
  return (
    <View accessibilityLabel={`${p.name} ${windowDays}`} style={{ gap: th.spacing.xs, paddingVertical: th.spacing.sm, borderTopWidth: 1, borderColor: th.color.line }}>
      <Text style={{ color: th.color.ink, ...th.type.bodyStrong }}>{p.name}</Text>
      <Text style={cap}>{t('dashboard.plant.readings', { count: p.readingCount })}</Text>
      {p.soilPct ? (
        <>
          <Body>{t('dashboard.plant.soil', { mean: fmtPct(p.soilPct.mean), min: fmtPct(p.soilPct.min), max: fmtPct(p.soilPct.max) })}</Body>
          <SoilBar mean={p.soilPct.mean} label={t('dashboard.plant.soil', { mean: fmtPct(p.soilPct.mean), min: fmtPct(p.soilPct.min), max: fmtPct(p.soilPct.max) })} />
        </>
      ) : <Body muted>{t('dashboard.plant.noSoil')}</Body>}
      {p.batteryMv ? <Body>{t('dashboard.plant.battery', { mean: fmtVolt(p.batteryMv.mean), min: fmtVolt(p.batteryMv.min), max: fmtVolt(p.batteryMv.max) })}</Body> : null}
      <Body>{t('dashboard.plant.watering', { count: p.wateringEvents })}</Body>
      {p.trend.soilChangePct !== null && p.trend.firstWeekMean !== null && p.trend.lastWeekMean !== null ? (
        <Body>{t('dashboard.plant.trend', { change: fmtSigned(p.trend.soilChangePct), first: fmtPct(p.trend.firstWeekMean), last: fmtPct(p.trend.lastWeekMean) })}</Body>
      ) : <Body muted>{t('dashboard.plant.noTrend')}</Body>}
    </View>
  );
}

function WindowSection({ data }: { data: AnalyticsResponse }) {
  const th = useTheme();
  const title = t('dashboard.window.title', { days: data.windowDays });
  return (
    <View accessibilityLabel={title} style={{ gap: th.spacing.sm }}>
      <Text accessibilityRole="header" style={{ color: th.color.ink, ...th.type.h2 }}>{title}</Text>
      {data.plants.length === 0 ? <Body muted>{t('dashboard.noPlants')}</Body>
        : windowIsEmpty(data) ? <Body muted>{t('dashboard.noReadings')}</Body>
        : data.plants.map((p) => <PlantRow key={p.plantId} p={p} windowDays={data.windowDays} />)}
    </View>
  );
}

/** FR-P04: the plan comes from the server (profiles.is_premium via getProfile); nothing is fetched until it says premium. */
export function PremiumDashboardScreen({ analytics, onBack, onPremium }: { analytics: AnalyticsService; onBack: () => void; onPremium: () => void }) {
  const th = useTheme();
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
      <View accessibilityLabel={t('dashboard.upgrade.title')} style={{ gap: th.spacing.sm }}>
        <Text style={{ color: th.color.ink, ...th.type.h2 }}>{t('dashboard.upgrade.title')}</Text>
        <Body>{t('dashboard.upgrade.body')}</Body>
        <Button label={t('profile.whatIsPremium')} variant="secondary" onPress={onPremium} />
      </View>
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
      {data.status === 'ready' ? ANALYTICS_WINDOWS.map((w) => <WindowSection key={w} data={data.byWindow[w]} />) : null}
    </Screen>
  );
}

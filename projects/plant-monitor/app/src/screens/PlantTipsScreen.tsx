// Care tips screen (task 4.A7, no wireframe code yet). Requirements: FR-P02 (shows only the stored tips of this plant that the server
// guardrailed, with their text as stored; no tip text is written here), FR-P04 (premium only: the plan is read first and free accounts never
// trigger a tips read; the table policy also returns no rows to them), NFR-06 (own plant only; the read runs as the user under RLS).
import React, { useCallback, useEffect, useState } from 'react';
import { Text, View } from 'react-native';
import { Body, Button, Notice, Screen } from '../ui/primitives';
import { useTheme } from '../ui/useTheme';
import { t } from '../i18n';
import { useAuth } from '../auth/AuthContext';
import type { TipsService } from '../tips/tipsApi';
import type { PlantTips, Tip } from '../tips/tipsModel';

type Plan = 'checking' | 'premium' | 'free' | 'planError';
type Data = { status: 'idle' } | { status: 'loading' } | { status: 'error' } | { status: 'ready'; tips: PlantTips | null };

/** One stored tip: its category (a fixed label) and its text exactly as the server returned it. */
function TipRow({ tip }: { tip: Tip }) {
  const th = useTheme();
  return (
    <View style={{ gap: th.spacing.xs, paddingVertical: th.spacing.sm, borderTopWidth: 1, borderColor: th.color.line }}>
      <Text style={{ color: th.color.muted, ...th.type.caption }}>{t(`tips.category.${tip.category}`)}</Text>
      <Body>{tip.text}</Body>
    </View>
  );
}

/** FR-P02: the plan comes from the server (profiles.is_premium via getProfile); nothing is read until it says premium. */
export function PlantTipsScreen({ tips, plantId, plantName, onBack, onPremium }: { tips: TipsService; plantId: string; plantName: string; onBack: () => void; onPremium: () => void }) {
  const th = useTheme();
  const { service } = useAuth();
  const [plan, setPlan] = useState<Plan>('checking');
  const [data, setData] = useState<Data>({ status: 'idle' });

  const load = useCallback(async () => {
    setData({ status: 'loading' });
    try {
      setData({ status: 'ready', tips: await tips.fetchPlantTips(plantId) });
    } catch {
      setData({ status: 'error' });
    }
  }, [tips, plantId]);

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

  const title = t('tips.title');
  if (plan === 'checking') return <Screen title={title} onBack={onBack}><Body muted>{t('common.loading')}</Body></Screen>;
  if (plan === 'planError') return (
    <Screen title={title} onBack={onBack}>
      <Notice kind="error" text={t('tips.profileError')} />
      <Button label={t('common.tryAgain')} variant="secondary" onPress={checkPlan} />
    </Screen>
  );
  if (plan === 'free') return (
    <Screen title={title} onBack={onBack}>
      <View accessibilityLabel={t('tips.upgrade.title')} style={{ gap: th.spacing.sm }}>
        <Text style={{ color: th.color.ink, ...th.type.h2 }}>{t('tips.upgrade.title')}</Text>
        <Body>{t('tips.upgrade.body')}</Body>
        <Button label={t('profile.whatIsPremium')} variant="secondary" onPress={onPremium} />
      </View>
    </Screen>
  );

  return (
    <Screen title={title} onBack={onBack}>
      <Body muted>{t('tips.intro', { plantName })}</Body>
      {data.status === 'loading' || data.status === 'idle' ? <Body muted>{t('tips.loading')}</Body> : null}
      {data.status === 'error' ? (
        <>
          <Notice kind="error" text={t('tips.error')} />
          <Button label={t('common.tryAgain')} variant="secondary" onPress={load} />
        </>
      ) : null}
      {data.status === 'ready' && (data.tips === null || data.tips.items.length === 0) ? <Body muted>{t('tips.empty')}</Body> : null}
      {data.status === 'ready' && data.tips && data.tips.items.length > 0 ? (
        <View accessibilityLabel={t('tips.title')} style={{ gap: th.spacing.xs }}>
          {data.tips.items.map((tip) => <TipRow key={tip.id} tip={tip} />)}
          <Body muted>{t('tips.generated', { date: data.tips.generatedAt.slice(0, 10) })}</Body>
        </View>
      ) : null}
    </Screen>
  );
}

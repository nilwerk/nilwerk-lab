// Bottom tab bar (#238 decision: three tabs, Plants, Alerts with a badge, Profile). Labels come from nav.* (strings/en.json).
import React from 'react';
import { Pressable, Text, View } from 'react-native';
import { useTheme } from './useTheme';
import { t } from '../i18n';

export type Tab = 'plants' | 'alerts' | 'profile';
const TABS: Tab[] = ['plants', 'alerts', 'profile'];

export function TabBar({ active, onSelect, openAlerts = 0 }: { active: Tab; onSelect: (tab: Tab) => void; openAlerts?: number }) {
  const th = useTheme();
  return (
    <View accessibilityRole="tablist" accessibilityLabel={t('a11y.tabs')} style={{ flexDirection: 'row', borderTopWidth: 1, borderColor: th.color.line, backgroundColor: th.color.surface }}>
      {TABS.map((tab) => {
        const on = tab === active;
        const badge = tab === 'alerts' && openAlerts > 0;
        return (
          <Pressable key={tab} accessibilityRole="tab" accessibilityLabel={badge ? t('nav.alertsBadge', { label: t('nav.alerts'), n: openAlerts }) : t(`nav.${tab}`)}
            accessibilityState={{ selected: on }} onPress={() => onSelect(tab)}
            style={{ flex: 1, minHeight: th.minTouchTarget, alignItems: 'center', justifyContent: 'center', borderTopWidth: 3, borderColor: on ? th.color.accent : 'transparent' }}>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: th.spacing.xs }}>
              <Text style={{ color: on ? th.color.ink : th.color.muted, ...(on ? th.type.bodyStrong : th.type.body) }}>{t(`nav.${tab}`)}</Text>
              {badge ? (
                <View accessible={false} style={{ minWidth: 22, paddingHorizontal: th.spacing.xs, borderRadius: th.radius.pill, backgroundColor: th.color.danger, alignItems: 'center' }}>
                  <Text style={{ color: th.color.dangerInk, ...th.type.caption }}>{String(openAlerts)}</Text>
                </View>
              ) : null}
            </View>
          </Pressable>
        );
      })}
    </View>
  );
}

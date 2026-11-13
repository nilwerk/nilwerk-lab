// Bottom tab bar (wireframe navigation map). Alerts and Insights tabs arrive with 4.A5 / later; only Plants and Profile exist now.
import React from 'react';
import { Pressable, Text, View } from 'react-native';
import { useTheme } from './useTheme';
import { t } from '../i18n';

export type Tab = 'plants' | 'profile';
const TABS: Tab[] = ['plants', 'profile'];

export function TabBar({ active, onSelect }: { active: Tab; onSelect: (tab: Tab) => void }) {
  const th = useTheme();
  return (
    <View accessibilityRole="tablist" accessibilityLabel={t('a11y.tabs')} style={{ flexDirection: 'row', borderTopWidth: 1, borderColor: th.color.line, backgroundColor: th.color.surface }}>
      {TABS.map((tab) => {
        const on = tab === active;
        return (
          <Pressable key={tab} accessibilityRole="tab" accessibilityLabel={t(`nav.${tab}`)} accessibilityState={{ selected: on }} onPress={() => onSelect(tab)}
            style={{ flex: 1, minHeight: th.minTouchTarget, alignItems: 'center', justifyContent: 'center', borderTopWidth: 3, borderColor: on ? th.color.accent : 'transparent' }}>
            <Text style={{ color: on ? th.color.accent : th.color.muted, ...(on ? th.type.bodyStrong : th.type.body) }}>{t(`nav.${tab}`)}</Text>
          </Pressable>
        );
      })}
    </View>
  );
}

// Shared screen kit: the one set of building blocks every screen uses (cards, section titles, captions, value rows,
// status words, empty states, bottom sheet). Colours and sizes come only from theme tokens (theme.ts); text only from t().
// Rules kept here: minimum target 48 px (th.minTouchTarget), control borders use th.color.control (3:1), the accent is a fill
// only (text is always ink, muted or a status colour).
import React from 'react';
import { Modal, Pressable, ScrollView, Text, View } from 'react-native';
import { Button } from './primitives';
import { useTheme } from './useTheme';
import { t } from '../i18n';

/** Rounded surface card for one object on the screen (radius xl, no border). */
export function Card({ children, testID }: { children: React.ReactNode; testID?: string }) {
  const th = useTheme();
  return (
    <View testID={testID} style={{ padding: th.spacing.lg, gap: th.spacing.sm, borderRadius: th.radius.xl, backgroundColor: th.color.surface }}>{children}</View>
  );
}

/** Section heading inside a screen (h3, ink, header role). */
export function SectionTitle({ children }: { children: React.ReactNode }) {
  const th = useTheme();
  return <Text accessibilityRole="header" style={{ color: th.color.ink, ...th.type.h3 }}>{children}</Text>;
}

/** Secondary line of text (muted caption). */
export function Caption({ children }: { children: React.ReactNode }) {
  const th = useTheme();
  return <Text style={{ color: th.color.muted, ...th.type.caption }}>{children}</Text>;
}

/** A status word with its colour: Good uses the ok colour, Low uses the low-battery colour (both pass 4.5:1 on bg and surface). */
export function StatusWord({ state }: { state: 'good' | 'low' }) {
  const th = useTheme();
  return <Text style={{ color: state === 'low' ? th.color.low : th.color.ok, ...th.type.caption }}>{t(state === 'low' ? 'sheet.low' : 'sheet.good')}</Text>;
}

/** One reading or setting: label on the left, value on the right, optional status word, a hairline below (not the last row). */
export function ValueRow({ label, value, state, last }: { label: string; value: string | null; state?: 'good' | 'low' | null; last?: boolean }) {
  const th = useTheme();
  return (
    <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', minHeight: th.minTouchTarget, borderBottomWidth: last ? 0 : 1, borderColor: th.color.line }}>
      <Text style={{ color: th.color.muted, ...th.type.body }}>{label}</Text>
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: th.spacing.sm }}>
        {value === null && state ? null : <Text style={{ color: th.color.ink, ...th.type.bodyStrong }}>{value ?? t('plant.latest.none')}</Text>}
        {state ? <StatusWord state={state} /> : null}
      </View>
    </View>
  );
}

/** Empty state: a title, one line of help, and at most one primary action. */
export function EmptyState({ title, body, action, onAction }: { title: string; body: string; action?: string; onAction?: () => void }) {
  const th = useTheme();
  return (
    <View style={{ gap: th.spacing.md }}>
      <Text accessibilityRole="header" style={{ color: th.color.ink, ...th.type.h3 }}>{title}</Text>
      <Text style={{ color: th.color.muted, ...th.type.body }}>{body}</Text>
      {action && onAction ? <Button label={action} variant="primary" onPress={onAction} /> : null}
    </View>
  );
}

/** Bottom sheet: slides up over the screen; the backdrop and the Close button both close it. Not used by a screen in this branch yet. */
export function BottomSheet({ visible, title, closeLabel, onClose, children }: { visible: boolean; title: string; closeLabel: string; onClose: () => void; children: React.ReactNode }) {
  const th = useTheme();
  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose}>
      <View style={{ flex: 1, justifyContent: 'flex-end', backgroundColor: 'rgba(0,0,0,0.35)' }}>
        <Pressable accessibilityRole="button" accessibilityLabel={closeLabel} onPress={onClose} style={{ flex: 1 }} />
        <View accessibilityViewIsModal style={{ maxHeight: '85%', borderTopLeftRadius: th.radius.xl, borderTopRightRadius: th.radius.xl, backgroundColor: th.color.bg, padding: th.spacing.lg, gap: th.spacing.md }}>
          <View style={{ alignSelf: 'center', width: 40, height: 4, borderRadius: th.radius.pill, backgroundColor: th.color.control }} />
          <Text accessibilityRole="header" style={{ color: th.color.ink, ...th.type.h2 }}>{title}</Text>
          <ScrollView contentContainerStyle={{ gap: th.spacing.lg, paddingBottom: th.spacing.md }}>{children}</ScrollView>
          <Button label={closeLabel} variant="secondary" onPress={onClose} />
        </View>
      </View>
    </Modal>
  );
}

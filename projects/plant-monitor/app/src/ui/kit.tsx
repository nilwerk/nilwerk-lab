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
      <View style={{ flex: 1, justifyContent: 'flex-end', backgroundColor: th.color.scrim }}>
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

export { BackButton } from './primitives';

/** Column of cards or rows with the shared gap (no per-screen layout styles). */
export function Stack({ children, gap = 'sm' }: { children: React.ReactNode; gap?: 'xs' | 'sm' | 'md' | 'lg' }) {
  const th = useTheme();
  return <View style={{ gap: th.spacing[gap] }}>{children}</View>;
}

/** Horizontal row that wraps (buttons, chips, small tiles). */
export function WrapRow({ children, gap = 'sm' }: { children: React.ReactNode; gap?: 'xs' | 'sm' | 'md' }) {
  const th = useTheme();
  return <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: th.spacing[gap] }}>{children}</View>;
}

/** One horizontal bar with its label and a value written out (0 to 100 scale). Values come from the caller. */
export function BarRow({ label, value, valueText }: { label: string; value: number; valueText: string }) {
  const th = useTheme();
  const pct = Math.min(100, Math.max(0, value));
  return (
    <View style={{ flexDirection: 'row', alignItems: 'center', gap: th.spacing.sm }}>
      <View style={{ width: 84 }}><Caption>{label}</Caption></View>
      <View style={{ flex: 1, height: 8, borderRadius: th.radius.sm, backgroundColor: th.color.line, overflow: 'hidden' }}>
        <View style={{ width: `${pct}%`, height: 8, backgroundColor: th.color.ink }} />
      </View>
      <View style={{ width: 56, alignItems: 'flex-end' }}><Text style={{ color: th.color.ink, ...th.type.caption }}>{valueText}</Text></View>
    </View>
  );
}

/** Min to max range with the mean marked, on a 0 to 100 scale. Accessible as an image with the given label. */
export function RangeMeter({ min, max, mean, label }: { min: number; max: number; mean: number; label: string }) {
  const th = useTheme();
  const clamp = (n: number) => Math.min(100, Math.max(0, n));
  const lo = clamp(min), hi = clamp(max), mid = clamp(mean);
  return (
    <View accessibilityRole="image" accessibilityLabel={label} style={{ height: 10, borderRadius: th.radius.sm, backgroundColor: th.color.line, overflow: 'hidden' }}>
      <View style={{ position: 'absolute', left: `${lo}%`, width: `${Math.max(0, hi - lo)}%`, top: 0, bottom: 0, backgroundColor: th.color.accentSoft }} />
      <View style={{ position: 'absolute', left: `${mid}%`, width: 3, marginLeft: -1, top: 0, bottom: 0, backgroundColor: th.color.ink }} />
    </View>
  );
}

/** A divided list item: a top hairline, then its children. */
export function ListItem({ children, testID }: { children: React.ReactNode; testID?: string }) {
  const th = useTheme();
  return <View testID={testID} style={{ gap: th.spacing.xs, paddingVertical: th.spacing.sm, borderTopWidth: 1, borderColor: th.color.line }}>{children}</View>;
}

// Layout blocks for the screens (moved here from ui/layout.tsx on Lena's review). Values come from theme tokens only.
export type Gap = 'xs' | 'sm' | 'md' | 'lg' | 'xl' | 'xxl' | 'xxxl';
type TypeVariant = 'display' | 'h1' | 'h2' | 'h3' | 'body' | 'bodyStrong' | 'caption' | 'label' | 'number';
type Tone = 'ink' | 'muted' | 'ok' | 'low' | 'danger' | 'wet' | 'dry';

/** A column of children with one spacing token between them (named Column: the kit has its own Stack). */
export function Column({ gap = 'sm', children, testID, accessibilityLabel, accessibilityRole }: { gap?: Gap; children: React.ReactNode; testID?: string; accessibilityLabel?: string; accessibilityRole?: 'radiogroup' | 'image' }) {
  const th = useTheme();
  return <View testID={testID} accessibilityLabel={accessibilityLabel} accessibilityRole={accessibilityRole} style={{ gap: th.spacing[gap] }}>{children}</View>;
}

/** A row of children with one spacing token between them; wrap for chips and grids. */
export function Row({ gap = 'sm', wrap, align = 'center', between, children, testID, accessibilityLabel }: { gap?: Gap; wrap?: boolean; align?: 'center' | 'flex-start'; between?: boolean; children: React.ReactNode; testID?: string; accessibilityLabel?: string }) {
  const th = useTheme();
  return (
    <View testID={testID} accessibilityLabel={accessibilityLabel} style={{ flexDirection: 'row', flexWrap: wrap ? 'wrap' : 'nowrap', alignItems: align, justifyContent: between ? 'space-between' : undefined, gap: th.spacing[gap] }}>
      {children}
    </View>
  );
}

/** Text with a type token and a colour token. `header` marks a heading; `mono` switches to the mono face (keys, codes). */
export function Type({ variant = 'body', tone = 'ink', mono, header, center, right, children, testID, accessibilityLabel, selectable, flex, width }: {
  variant?: TypeVariant; tone?: Tone; mono?: boolean; header?: boolean; center?: boolean; right?: boolean; children: React.ReactNode;
  testID?: string; accessibilityLabel?: string; selectable?: boolean; flex?: boolean; width?: number;
}) {
  const th = useTheme();
  const font = mono ? { fontFamily: th.fontFamily.mono } : {};
  return (
    <Text testID={testID} accessibilityLabel={accessibilityLabel} accessibilityRole={header ? 'header' : undefined} selectable={selectable}
      style={{ color: th.color[tone], ...th.type[variant], ...font, textAlign: center ? 'center' : right ? 'right' : undefined, flexGrow: flex ? 1 : undefined, width }}>
      {children}
    </Text>
  );
}

/** One line of a list: a hairline below it, except the last one. Minimum height is the touch target. */
export function ListRow({ last, children, testID, accessibilityLabel, padded }: { last?: boolean; children: React.ReactNode; testID?: string; accessibilityLabel?: string; padded?: boolean }) {
  const th = useTheme();
  return (
    <View testID={testID} accessibilityLabel={accessibilityLabel}
      style={{ minHeight: th.minTouchTarget, justifyContent: 'center', paddingVertical: padded ? th.spacing.sm : 0, borderBottomWidth: last ? 0 : 1, borderColor: th.color.line }}>
      {children}
    </View>
  );
}

/** A bordered grid cell with a basis (for a three-per-row grid). */
export function GridCell({ basis = '30%', children, testID, accessibilityLabel }: { basis?: `${number}%`; children: React.ReactNode; testID?: string; accessibilityLabel?: string }) {
  const th = useTheme();
  return (
    <View testID={testID} accessible={accessibilityLabel !== undefined} accessibilityLabel={accessibilityLabel}
      style={{ flexBasis: basis, flexGrow: 0, flexShrink: 0, gap: th.spacing.xs }}>
      {children}
    </View>
  );
}

/** A square surface for a photo or a placeholder tile. */
export function Frame({ children }: { children?: React.ReactNode }) {
  const th = useTheme();
  return (
    <View style={{ aspectRatio: 1, borderRadius: th.radius.md, borderWidth: 1, borderColor: th.color.line, backgroundColor: th.color.surface, alignItems: 'center', justifyContent: 'center', overflow: 'hidden' }}>
      {children}
    </View>
  );
}

/** Bar meter: a track with a fill of `percent` (0 to 100, clamped). Shows the value as text elsewhere; the bar is decoration. */

/** Bar meter: a track with a fill of `percent` (0 to 100, clamped). The value is written as text elsewhere; the bar is decoration. */
export function BarMeter({ percent, tone = 'accent' }: { percent: number; tone?: 'accent' | 'wet' | 'dry' }) {
  const th = useTheme();
  const p = Math.min(100, Math.max(0, percent));
  return (
    <View testID="bar-fill-track" style={{ flex: 1, height: 8, borderRadius: th.radius.sm, backgroundColor: th.color.line, overflow: 'hidden' }}>
      <View testID="bar-fill" style={{ width: `${p}%`, height: 8, backgroundColor: th.color[tone] }} />
    </View>
  );
}

export { FadeIn } from './primitives';

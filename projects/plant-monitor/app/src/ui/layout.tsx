// Layout building blocks for the screens (task: apply the alternative design to the app screens, PR for agent/ux/alt-build).
// Screens use these instead of inline style objects: spacing, type, colour and sizes come only from theme.ts tokens, text only from t().
// Kept beside kit.tsx (owned by the UX designer) so the shared kit file is not edited here. Rules: every touch target is at least
// th.minTouchTarget (48 px); control borders use th.color.control (3:1 on the surface); the accent is a fill only, text is ink, muted or a status colour.
import React from 'react';
import { Image, Pressable, Text, View, type ImageSourcePropType } from 'react-native';
import { useTheme } from './useTheme';
import { t } from '../i18n';
import type { spacing as spacingTokens } from '../../theme';

export type Gap = keyof typeof spacingTokens;
type TypeVariant = 'display' | 'h1' | 'h2' | 'h3' | 'body' | 'bodyStrong' | 'caption' | 'label' | 'number';
type Tone = 'ink' | 'muted' | 'ok' | 'low' | 'danger' | 'accent' | 'wet' | 'dry';

/** A column of children with one spacing token between them. */
export function Stack({ gap = 'sm', children, testID, accessibilityLabel, accessibilityRole }: { gap?: Gap; children: React.ReactNode; testID?: string; accessibilityLabel?: string; accessibilityRole?: 'radiogroup' | 'image' }) {
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
export function BarMeter({ percent, tone = 'accent' }: { percent: number; tone?: 'accent' | 'wet' | 'dry' }) {
  const th = useTheme();
  const p = Math.min(100, Math.max(0, percent));
  return (
    <View style={{ flex: 1, height: 8, borderRadius: 4, backgroundColor: th.color.line, overflow: 'hidden' }}>
      <View testID="bar-fill" style={{ width: `${p}%`, height: 8, backgroundColor: th.color[tone] }} />
    </View>
  );
}

/** Range meter on a 0 to 100 scale: the span from lo to hi is filled and the mean is a marker. Values are clamped for drawing only. */
export function RangeMeter({ lo, hi, mark, label }: { lo: number; hi: number; mark: number; label: string }) {
  const th = useTheme();
  const c = (n: number) => Math.min(100, Math.max(0, n));
  return (
    <View accessibilityRole="image" accessibilityLabel={label} style={{ height: 10, borderRadius: 5, backgroundColor: th.color.line, overflow: 'hidden' }}>
      <View style={{ position: 'absolute', left: `${c(lo)}%`, width: `${Math.max(0, c(hi) - c(lo))}%`, top: 0, bottom: 0, backgroundColor: th.color.accentSoft }} />
      <View style={{ position: 'absolute', left: `${c(mark)}%`, width: 3, marginLeft: -1, top: 0, bottom: 0, backgroundColor: th.color.accent }} />
    </View>
  );
}

/** Back control for the fixed header: a 48 by 48 px target with a control border and a chevron. The label is the screen-reader name. */
export function BackArrow({ onPress }: { onPress: () => void }) {
  const th = useTheme();
  return (
    <Pressable accessibilityRole="button" accessibilityLabel={t('a11y.back')} onPress={onPress}
      style={{ width: th.minTouchTarget, height: th.minTouchTarget, alignItems: 'center', justifyContent: 'center', borderRadius: th.radius.pill, borderWidth: 1, borderColor: th.color.control, backgroundColor: th.color.surface }}>
      <Text style={{ color: th.color.ink, ...th.type.h2 }}>{'‹'}</Text>
    </Pressable>
  );
}

/** The app logo, centred, at a fixed size with the theme radius. The label is the screen-reader name. */
export function Logo({ source, label }: { source: ImageSourcePropType; label: string }) {
  const th = useTheme();
  return (
    <View style={{ alignItems: 'center' }}>
      <Image source={source} accessibilityLabel={label} style={{ width: LOGO_SIZE, height: LOGO_SIZE, borderRadius: th.radius.lg }} />
    </View>
  );
}
const LOGO_SIZE = 96;

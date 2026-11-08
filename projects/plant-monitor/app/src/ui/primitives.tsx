// Small themed building blocks. Colours/spacing only from theme.ts tokens, text only via t() (playbook: no inline values, no inline strings).
import React from 'react';
import { Pressable, ScrollView, Text, TextInput, View, type TextInputProps } from 'react-native';
import { useTheme } from './useTheme';
import { t } from '../i18n';

export function Screen({ title, children, onBack }: { title: string; children: React.ReactNode; onBack?: () => void }) {
  const th = useTheme();
  return (
    <View style={{ flex: 1, backgroundColor: th.color.bg }} accessibilityLabel={t('a11y.screenTitle', { title })}>
      <ScrollView contentContainerStyle={{ padding: th.spacing.lg, gap: th.spacing.lg }} keyboardShouldPersistTaps="handled">
        {onBack ? <Button label={t('common.back')} a11yLabel={t('a11y.back')} variant="ghost" onPress={onBack} /> : null}
        <Text accessibilityRole="header" style={{ color: th.color.ink, ...th.type.h1 }}>{title}</Text>
        {children}
      </ScrollView>
    </View>
  );
}

export function Body({ children, muted }: { children: React.ReactNode; muted?: boolean }) {
  const th = useTheme();
  return <Text style={{ color: muted ? th.color.muted : th.color.ink, ...th.type.body }}>{children}</Text>;
}

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger';

export function Button({ label, onPress, variant = 'primary', disabled, busy, a11yLabel }: {
  label: string; onPress: () => void; variant?: Variant; disabled?: boolean; busy?: boolean; a11yLabel?: string;
}) {
  const th = useTheme();
  const c = th.color;
  const look = {
    primary: { bg: c.accent, fg: c.accentInk, border: c.accent },
    danger: { bg: c.danger, fg: c.dangerInk, border: c.danger },
    secondary: { bg: c.surface, fg: c.ink, border: c.line },
    ghost: { bg: 'transparent', fg: c.accent, border: 'transparent' },
  }[variant];
  const off = disabled || busy;
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={a11yLabel ?? label}
      accessibilityState={{ disabled: !!off, busy: !!busy }}
      disabled={off}
      onPress={onPress}
      style={{
        minHeight: th.minTouchTarget, justifyContent: 'center', alignItems: 'center', paddingHorizontal: th.spacing.lg,
        borderRadius: th.radius.md, borderWidth: 1, backgroundColor: look.bg, borderColor: look.border, opacity: off ? 0.55 : 1,
      }}
    >
      <Text style={{ color: look.fg, ...th.type.bodyStrong }}>{busy ? t('common.loading') : label}</Text>
    </Pressable>
  );
}

export function Field({ label, error, ...input }: { label: string; error?: string | null } & TextInputProps) {
  const th = useTheme();
  return (
    <View style={{ gap: th.spacing.xs }}>
      <Text style={{ color: th.color.muted, ...th.type.caption }}>{label}</Text>
      <TextInput
        accessibilityLabel={label}
        placeholderTextColor={th.color.muted}
        {...input}
        style={{
          minHeight: th.minTouchTarget, paddingHorizontal: th.spacing.md, borderRadius: th.radius.md, borderWidth: 1,
          borderColor: error ? th.color.danger : th.color.line, backgroundColor: th.color.surface, color: th.color.ink, ...th.type.body,
        }}
      />
      {error ? <Text accessibilityRole="alert" style={{ color: th.color.danger, ...th.type.caption }}>{error}</Text> : null}
    </View>
  );
}

/** Error / info banner. Always text (never colour alone). */
export function Notice({ text, kind }: { text: string; kind: 'error' | 'info' }) {
  const th = useTheme();
  const bad = kind === 'error';
  return (
    <View accessibilityRole={bad ? 'alert' : undefined} style={{ padding: th.spacing.md, borderRadius: th.radius.md, backgroundColor: bad ? th.color.dangerSoft : th.color.okSoft }}>
      <Text style={{ color: bad ? th.color.danger : th.color.ok, ...th.type.bodyStrong }}>{text}</Text>
    </View>
  );
}

/** One option of a single-choice group (radio). Selected state is announced and also drawn with a check mark, not colour alone. */
export function Choice({ label, a11yLabel, selected, onPress }: { label: string; a11yLabel?: string; selected: boolean; onPress: () => void }) {
  const th = useTheme();
  return (
    <Pressable
      accessibilityRole="radio"
      accessibilityLabel={a11yLabel ?? label}
      accessibilityState={{ selected }}
      onPress={onPress}
      style={{ minHeight: th.minTouchTarget, justifyContent: 'center', paddingHorizontal: th.spacing.md, borderRadius: th.radius.md, borderWidth: selected ? 2 : 1, borderColor: selected ? th.color.accent : th.color.line, backgroundColor: selected ? th.color.accentSoft : th.color.surface }}
    >
      <Text style={{ color: th.color.ink, ...(selected ? th.type.bodyStrong : th.type.body) }}>{selected ? `✓ ${label}` : label}</Text>
    </Pressable>
  );
}

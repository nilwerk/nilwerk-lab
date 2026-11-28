// S03 Profile. Requirements: FR-A01 (profile, sign out, entry to delete), FR-P04 (plan mirrors profiles.is_premium; the server decides; the premium dashboard and Connect-your-AI (FR-P03) entries show only for premium),
// NFR-06 (reads/writes only the caller's own profiles row under RLS).
import React, { useCallback, useEffect, useState } from 'react';
import { Pressable, Text } from 'react-native';
import { Body, Button, Field, Notice, Screen } from '../ui/primitives';
import { Card, Caption } from '../ui/kit';
import { Column, Row } from '../ui/kit';
import { useTheme } from '../ui/useTheme';
import { LegalLine } from '../ui/LegalLine';
import { t } from '../i18n';
import { useAuth } from '../auth/AuthContext';
import type { Profile } from '../auth/types';
import { validateDisplayName } from '../validation';

export function ProfileScreen({ onPremium, onDelete, onAddSensor, onDashboard, onConnectAi, contactEmail }: { onPremium: () => void; onDelete: () => void; onAddSensor: () => void; onDashboard: () => void; onConnectAi: () => void; contactEmail: string }) {
  const { service, state } = useAuth();
  const th = useTheme();
  const [profile, setProfile] = useState<Profile | null>(null);
  // The display name is read-only text until the edit icon is tapped (owner feedback 28 Nov). name is the draft in edit mode only.
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setError(null);
    try {
      const p = await service.getProfile();
      setProfile(p);
      setName(p.displayName ?? '');
    } catch {
      setError(t('profile.error.load'));
    }
  }, [service]);
  useEffect(() => { load(); }, [load]);

  const startEdit = () => { setName(profile?.displayName ?? ''); setError(null); setSaved(false); setEditing(true); };
  const cancelEdit = () => { setName(profile?.displayName ?? ''); setError(null); setEditing(false); };

  const nameErr = validateDisplayName(name);
  const save = async () => {
    if (nameErr) return;
    setBusy(true); setSaved(false); setError(null);
    try {
      await service.updateDisplayName(name);
      setProfile((p) => (p ? { ...p, displayName: name.trim() || null } : p));
      setEditing(false);
      setSaved(true);
    } catch {
      setError(t('profile.error.save'));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Screen title={t('profile.title')}>
      {error ? <Notice kind="error" text={error} /> : null}
      <Card>
        <Caption>{t('profile.email')}</Caption>
        <Body>{state.user?.email ?? ''}</Body>
      </Card>
      <Card>
        <Caption>{t('profile.plan')}</Caption>
        <Body>{profile ? t(profile.isPremium ? 'profile.plan.premium' : 'profile.plan.free') : t('common.loading')}</Body>
        {/* only the current tier and its price here; the full comparison is on the Premium screen. Values are in strings/en.json only. */}
        {profile ? <Caption>{t(profile.isPremium ? 'profile.price.premium' : 'profile.price.free')}</Caption> : null}
        {profile && !profile.isPremium ? <Button label={t('profile.whatIsPremium')} variant="ghost" onPress={onPremium} /> : null}
        {profile && profile.isPremium ? <Button label={t('profile.dashboard')} variant="secondary" onPress={onDashboard} /> : null}
        {profile && profile.isPremium ? <Button label={t('profile.connectAi')} variant="secondary" onPress={onConnectAi} /> : null}
      </Card>
      <Card>
        <Row between align="flex-start" gap="md">
          <Column gap="xs">
            <Caption>{t('profile.displayName')}</Caption>
            <Body>{profile ? (profile.displayName ?? t('profile.displayName.none')) : t('common.loading')}</Body>
          </Column>
          {!editing && profile ? (
            <Pressable accessibilityRole="button" accessibilityLabel={t('profile.displayName.edit')} onPress={startEdit}
              hitSlop={8} style={{ width: th.minTouchTarget, height: th.minTouchTarget, alignItems: 'center', justifyContent: 'center' }}>
              <Text accessibilityElementsHidden importantForAccessibility="no" style={{ color: th.color.accent, ...th.type.h3 }}>{'\u270E'}</Text>
            </Pressable>
          ) : null}
        </Row>
        {editing ? (
          <>
            <Field label={t('profile.displayName')} value={name} onChangeText={(v) => { setName(v); setSaved(false); }} error={nameErr ? t(nameErr.key, nameErr.params) : null} />
            <Row gap="sm" wrap>
              <Button label={t('profile.displayName.save')} variant="secondary" onPress={save} busy={busy} disabled={!profile || !!nameErr} />
              <Button label={t('common.cancel')} variant="ghost" onPress={cancelEdit} disabled={busy} />
            </Row>
          </>
        ) : null}
      </Card>
      {saved ? <Notice kind="info" text={t('profile.displayName.saved')} /> : null}
      <Button label={t('setup.addSensor')} onPress={onAddSensor} />
      <Body muted>{t('profile.plantsSoon')}</Body>
      <Button label={t('profile.signOut')} variant="secondary" onPress={() => { service.signOut().catch(() => setError(t('auth.error.unknown'))); }} />
      <Button label={t('profile.deleteAccount')} variant="ghost" onPress={onDelete} />
      <LegalLine contactEmail={contactEmail} />
    </Screen>
  );
}

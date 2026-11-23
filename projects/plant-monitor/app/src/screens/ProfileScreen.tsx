// S03 Profile. Requirements: FR-A01 (profile, sign out, entry to delete), FR-P04 (plan mirrors profiles.is_premium; the server decides; the premium dashboard entry shows only for premium),
// NFR-06 (reads/writes only the caller's own profiles row under RLS).
import React, { useCallback, useEffect, useState } from 'react';
import { Text, View } from 'react-native';
import { Body, Button, Field, Notice, Screen } from '../ui/primitives';
import { useTheme } from '../ui/useTheme';
import { LegalLine } from '../ui/LegalLine';
import { t } from '../i18n';
import { useAuth } from '../auth/AuthContext';
import type { Profile } from '../auth/types';
import { validateDisplayName } from '../validation';

export function ProfileScreen({ onPremium, onDelete, onAddSensor, onDashboard, contactEmail }: { onPremium: () => void; onDelete: () => void; onAddSensor: () => void; onDashboard: () => void; contactEmail: string }) {
  const th = useTheme();
  const { service, state } = useAuth();
  const [profile, setProfile] = useState<Profile | null>(null);
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

  const nameErr = validateDisplayName(name);
  const save = async () => {
    if (nameErr) return;
    setBusy(true); setSaved(false); setError(null);
    try {
      await service.updateDisplayName(name);
      setProfile((p) => (p ? { ...p, displayName: name.trim() || null } : p));
      setSaved(true);
    } catch {
      setError(t('profile.error.save'));
    } finally {
      setBusy(false);
    }
  };

  const row = { gap: th.spacing.xs } as const;
  return (
    <Screen title={t('profile.title')}>
      {error ? <Notice kind="error" text={error} /> : null}
      <View style={row}>
        <Text style={{ color: th.color.muted, ...th.type.caption }}>{t('profile.email')}</Text>
        <Body>{state.user?.email ?? ''}</Body>
      </View>
      <View style={row}>
        <Text style={{ color: th.color.muted, ...th.type.caption }}>{t('profile.plan')}</Text>
        <Body>{profile ? t(profile.isPremium ? 'profile.plan.premium' : 'profile.plan.free') : t('common.loading')}</Body>
        {profile && !profile.isPremium ? <Button label={t('profile.whatIsPremium')} variant="ghost" onPress={onPremium} /> : null}
        {profile && profile.isPremium ? <Button label={t('profile.dashboard')} variant="secondary" onPress={onDashboard} /> : null}
      </View>
      <Field label={t('profile.displayName')} value={name} onChangeText={(v) => { setName(v); setSaved(false); }} error={nameErr ? t(nameErr.key, nameErr.params) : null} />
      <Button label={t('profile.displayName.save')} variant="secondary" onPress={save} busy={busy} disabled={!profile || !!nameErr} />
      {saved ? <Notice kind="info" text={t('profile.displayName.saved')} /> : null}
      <Button label={t('setup.addSensor')} onPress={onAddSensor} />
      <Body muted>{t('profile.plantsSoon')}</Body>
      <Button label={t('profile.signOut')} variant="secondary" onPress={() => { service.signOut().catch(() => setError(t('auth.error.unknown'))); }} />
      <Button label={t('profile.deleteAccount')} variant="ghost" onPress={onDelete} />
      <LegalLine contactEmail={contactEmail} />
    </Screen>
  );
}

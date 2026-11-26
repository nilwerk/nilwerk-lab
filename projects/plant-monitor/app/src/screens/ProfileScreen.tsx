// S03 Profile. Requirements: FR-A01 (profile, sign out, entry to delete), FR-P04 (plan mirrors profiles.is_premium; the server decides; the premium dashboard and Connect-your-AI (FR-P03) entries show only for premium),
// NFR-06 (reads/writes only the caller's own profiles row under RLS).
import React, { useCallback, useEffect, useState } from 'react';
import { Body, Button, Field, Notice, Screen } from '../ui/primitives';
import { Card, Caption, ListRow } from '../ui/kit';
import { Column } from '../ui/kit';
import { LegalLine } from '../ui/LegalLine';
import { t } from '../i18n';
import { useAuth } from '../auth/AuthContext';
import type { Profile } from '../auth/types';
import { validateDisplayName } from '../validation';

export function ProfileScreen({ onPremium, onDelete, onAddSensor, onDashboard, onConnectAi, contactEmail }: { onPremium: () => void; onDelete: () => void; onAddSensor: () => void; onDashboard: () => void; onConnectAi: () => void; contactEmail: string }) {
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

  return (
    <Screen fade title={t('profile.title')}>
      {error ? <Notice kind="error" text={error} /> : null}
      <Card>
        <ListRow last>
          <Caption>{t('profile.email')}</Caption>
          <Body>{state.user?.email ?? ''}</Body>
        </ListRow>
      </Card>
      <Card>
        <Caption>{t('profile.plan')}</Caption>
        <Body>{profile ? t(profile.isPremium ? 'profile.plan.premium' : 'profile.plan.free') : t('common.loading')}</Body>
        {/* #238 decision: the plan prices are shown on Profile before Premium is opened. Values are in strings/en.json only. */}
        <Column gap="xs" accessibilityLabel={t('profile.price.heading')}>
          <Caption>{t('profile.price.free')}</Caption>
          <Caption>{t('profile.price.premium')}</Caption>
        </Column>
        {profile && !profile.isPremium ? <Button label={t('profile.whatIsPremium')} variant="ghost" onPress={onPremium} /> : null}
        {profile && profile.isPremium ? <Button label={t('profile.dashboard')} variant="secondary" onPress={onDashboard} /> : null}
        {profile && profile.isPremium ? <Button label={t('profile.connectAi')} variant="secondary" onPress={onConnectAi} /> : null}
      </Card>
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

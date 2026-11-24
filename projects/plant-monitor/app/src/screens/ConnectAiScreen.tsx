// S42 Connect your AI (task 4.A8). Requirements: FR-P03 (create / revoke a personal MCP key, copy-paste setup text for Claude and other MCP clients),
// FR-P04 (premium only: the plan is read first and free accounts never trigger a key request; the server still answers 403 premium_required and that shows the locked state too),
// NFR-06 (own keys only; the key is shown once, kept in memory only, never stored or listed again).
import React, { useCallback, useEffect, useState } from 'react';
import { Text, View } from 'react-native';
import { Body, Button, Field, Notice, Screen } from '../ui/primitives';
import { useTheme } from '../ui/useTheme';
import { t } from '../i18n';
import { useAuth } from '../auth/AuthContext';
import { ApiKeysError, type ApiKeyInfo, type ApiKeysService, type CreatedApiKey } from '../mcp/apiKeysApi';
import { claudeSetupText, genericSetupText } from '../mcp/setupText';
import { copyText, type CopyText } from '../mcp/copyText';
import { validateKeyName } from '../mcp/keyName';

type Plan = 'checking' | 'premium' | 'free' | 'planError';
type Keys = { status: 'loading' } | { status: 'error' } | { status: 'ready'; items: ApiKeyInfo[] };
type Msg = { kind: 'error' | 'info'; text: string } | null;

function SetupBlock({ title, text, copy }: { title: string; text: string; copy: CopyText }) {
  const th = useTheme();
  const [msg, setMsg] = useState<Msg>(null);
  const press = async () => {
    try { await copy(text); setMsg({ kind: 'info', text: t('mcp.setup.copied') }); } catch { setMsg({ kind: 'error', text: t('mcp.setup.copyError') }); }
  };
  return (
    <View style={{ gap: th.spacing.sm }}>
      <Text accessibilityRole="header" style={{ color: th.color.ink, ...th.type.h3 }}>{title}</Text>
      <View style={{ padding: th.spacing.md, borderRadius: th.radius.md, backgroundColor: th.color.surface, borderWidth: 1, borderColor: th.color.line }}>
        <Text selectable accessibilityLabel={title} style={{ color: th.color.ink, ...th.type.caption, fontFamily: th.fontFamily.mono }}>{text}</Text>
      </View>
      <Button label={t('mcp.setup.copy')} a11yLabel={`${t('mcp.setup.copy')}: ${title}`} variant="secondary" onPress={press} />
      {msg ? <Notice kind={msg.kind} text={msg.text} /> : null}
    </View>
  );
}

/** The one-time key box. The key lives only in this screen's state and disappears when the user confirms (FR-P03, NFR-06). */
function CreatedKey({ created, copy, onDone }: { created: CreatedApiKey; copy: CopyText; onDone: () => void }) {
  const th = useTheme();
  const [msg, setMsg] = useState<Msg>(null);
  const press = async () => {
    try { await copy(created.key); setMsg({ kind: 'info', text: t('mcp.created.copied') }); } catch { setMsg({ kind: 'error', text: t('mcp.created.copyError') }); }
  };
  return (
    <View accessibilityLabel={t('mcp.created.title')} style={{ gap: th.spacing.sm }}>
      <Text accessibilityRole="header" style={{ color: th.color.ink, ...th.type.h2 }}>{t('mcp.created.title')}</Text>
      <Notice kind="info" text={t('mcp.created.warning')} />
      <View style={{ padding: th.spacing.md, borderRadius: th.radius.md, backgroundColor: th.color.surface, borderWidth: 1, borderColor: th.color.line }}>
        <Text selectable accessibilityLabel={t('mcp.created.title')} style={{ color: th.color.ink, ...th.type.body, fontFamily: th.fontFamily.mono }}>{created.key}</Text>
      </View>
      <Button label={t('mcp.created.copy')} onPress={press} />
      {msg ? <Notice kind={msg.kind} text={msg.text} /> : null}
      <Button label={t('mcp.created.done')} variant="secondary" onPress={onDone} />
    </View>
  );
}

function KeyRow({ k, confirming, busy, onAsk, onCancel, onConfirm }: { k: ApiKeyInfo; confirming: boolean; busy: boolean; onAsk: () => void; onCancel: () => void; onConfirm: () => void }) {
  const th = useTheme();
  const revoked = k.revokedAt !== null;
  return (
    <View accessibilityLabel={t('mcp.keys.row', { name: k.name, prefix: k.prefix })} style={{ gap: th.spacing.xs, paddingVertical: th.spacing.sm, borderTopWidth: 1, borderColor: th.color.line }}>
      <Text style={{ color: th.color.ink, ...th.type.bodyStrong }}>{k.name}</Text>
      <Text style={{ color: th.color.muted, ...th.type.caption, fontFamily: th.fontFamily.mono }}>{`${k.prefix}...`}</Text>
      <Text style={{ color: revoked ? th.color.danger : th.color.ok, ...th.type.caption }}>{revoked ? t('mcp.keys.revoked') : t('mcp.keys.active')}</Text>
      <Text style={{ color: th.color.muted, ...th.type.caption }}>{k.lastUsedAt ? t('mcp.keys.lastUsed', { date: k.lastUsedAt.slice(0, 10) }) : t('mcp.keys.neverUsed')}</Text>
      {!revoked && !confirming ? <Button label={t('mcp.keys.revoke')} a11yLabel={t('mcp.keys.revoke.a11y', { name: k.name })} variant="danger" onPress={onAsk} /> : null}
      {!revoked && confirming ? (
        <>
          <Notice kind="error" text={t('mcp.keys.revoke.confirm', { name: k.name })} />
          <Button label={t('mcp.keys.revoke.yes')} variant="danger" busy={busy} disabled={busy} onPress={onConfirm} />
          <Button label={t('mcp.keys.revoke.no')} variant="secondary" disabled={busy} onPress={onCancel} />
        </>
      ) : null}
    </View>
  );
}

/** FR-P04: the plan comes from the server (profiles.is_premium via getProfile); no key request is made until it says premium. */
export function ConnectAiScreen({ apiKeys, onBack, onPremium, copy = copyText }: { apiKeys: ApiKeysService; onBack: () => void; onPremium: () => void; copy?: CopyText }) {
  const th = useTheme();
  const { service } = useAuth();
  const [plan, setPlan] = useState<Plan>('checking');
  const [keys, setKeys] = useState<Keys>({ status: 'loading' });
  const [name, setName] = useState(t('mcp.keys.nameDefault'));
  const [creating, setCreating] = useState(false);
  const [created, setCreated] = useState<CreatedApiKey | null>(null);
  const [confirmId, setConfirmId] = useState<string | null>(null);
  const [revoking, setRevoking] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  const load = useCallback(async () => {
    setKeys({ status: 'loading' });
    try {
      setKeys({ status: 'ready', items: await apiKeys.list() });
    } catch (e) {
      if (e instanceof ApiKeysError && e.code === 'premium_required') { setPlan('free'); return; }
      setKeys({ status: 'error' });
    }
  }, [apiKeys]);

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

  const nameErr = validateKeyName(name);
  const create = async () => {
    if (nameErr || creating) return;
    setCreating(true); setNotice(null);
    try {
      const c = await apiKeys.create(name.trim());
      setCreated(c);
      await load();
    } catch (e) {
      if (e instanceof ApiKeysError && e.code === 'premium_required') { setPlan('free'); setNotice(null); } else { setNotice(t('mcp.error.create')); }
    } finally {
      setCreating(false);
    }
  };
  const revoke = async (id: string) => {
    setRevoking(true); setNotice(null);
    try {
      await apiKeys.revoke(id);
      setConfirmId(null);
      await load();
    } catch {
      setNotice(t('mcp.error.revoke')); // the key was NOT revoked: say so, keep the row and the confirm open (playbook rule 12)
    } finally {
      setRevoking(false);
    }
  };

  const title = t('mcp.title');
  if (plan === 'checking') return <Screen title={title} onBack={onBack}><Body muted>{t('common.loading')}</Body></Screen>;
  if (plan === 'planError') return (
    <Screen title={title} onBack={onBack}>
      <Notice kind="error" text={t('mcp.profileError')} />
      <Button label={t('common.tryAgain')} variant="secondary" onPress={checkPlan} />
    </Screen>
  );
  if (plan === 'free') return (
    <Screen title={title} onBack={onBack}>
      <View accessibilityLabel={t('mcp.locked.title')} style={{ gap: th.spacing.sm }}>
        <Text style={{ color: th.color.ink, ...th.type.h2 }}>{t('mcp.locked.title')}</Text>
        <Body>{t('mcp.locked.body')}</Body>
        <Button label={t('profile.whatIsPremium')} variant="secondary" onPress={onPremium} />
      </View>
    </Screen>
  );

  const items = keys.status === 'ready' ? keys.items : [];
  return (
    <Screen title={title} onBack={onBack}>
      <Body muted>{t('mcp.intro')}</Body>
      {notice ? <Notice kind="error" text={notice} /> : null}
      {created ? <CreatedKey created={created} copy={copy} onDone={() => setCreated(null)} /> : null}
      <View style={{ gap: th.spacing.sm }}>
        <Text accessibilityRole="header" style={{ color: th.color.ink, ...th.type.h2 }}>{t('mcp.keys.title')}</Text>
        {keys.status === 'loading' ? <Body muted>{t('mcp.loading')}</Body> : null}
        {keys.status === 'error' ? (
          <>
            <Notice kind="error" text={t('mcp.error.load')} />
            <Button label={t('common.tryAgain')} variant="secondary" onPress={load} />
          </>
        ) : null}
        {keys.status === 'ready' && items.length === 0 ? <Body muted>{t('mcp.keys.none')}</Body> : null}
        {items.map((k) => (
          <KeyRow key={k.id} k={k} confirming={confirmId === k.id} busy={revoking}
            onAsk={() => { setConfirmId(k.id); setNotice(null); }} onCancel={() => setConfirmId(null)} onConfirm={() => revoke(k.id)} />
        ))}
        {keys.status === 'ready' ? (
          <>
            <Field label={t('mcp.keys.name')} value={name} maxLength={60} onChangeText={setName} error={nameErr ? t(nameErr.key, nameErr.params) : null} />
            <Button label={t('mcp.keys.create')} onPress={create} busy={creating} disabled={!!nameErr || creating} />
          </>
        ) : null}
      </View>
      <SetupBlock title={t('mcp.setup.claude.title')} text={claudeSetupText()} copy={copy} />
      <SetupBlock title={t('mcp.setup.generic.title')} text={genericSetupText()} copy={copy} />
      <Body muted>{t('mcp.setup.hint')}</Body>
    </Screen>
  );
}

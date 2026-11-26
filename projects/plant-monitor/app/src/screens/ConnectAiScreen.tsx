// S42 Connect your AI (task 4.A8). Requirements: FR-P03 (create / revoke a personal MCP key, copy-paste setup text for Claude and other MCP clients),
// FR-P04 (premium only: the plan is read first and free accounts never trigger a key request; the server still answers 403 premium_required and that shows the locked state too),
// NFR-06 (own keys only; the key is shown once, kept in memory only, never stored or listed again).
import React, { useCallback, useEffect, useState } from 'react';
import { Body, Button, Field, Notice, Screen } from '../ui/primitives';
import { Card, SectionTitle } from '../ui/kit';
import { ListRow, Stack, Type } from '../ui/layout';
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
  const [msg, setMsg] = useState<Msg>(null);
  const press = async () => {
    try { await copy(text); setMsg({ kind: 'info', text: t('mcp.setup.copied') }); } catch { setMsg({ kind: 'error', text: t('mcp.setup.copyError') }); }
  };
  return (
    <Stack>
      <Type variant="h3" header>{title}</Type>
      <Card>
        <Type variant="caption" mono selectable accessibilityLabel={title}>{text}</Type>
      </Card>
      <Button label={t('mcp.setup.copy')} a11yLabel={`${t('mcp.setup.copy')}: ${title}`} variant="secondary" onPress={press} />
      {msg ? <Notice kind={msg.kind} text={msg.text} /> : null}
    </Stack>
  );
}

/** The one-time key box. The key lives only in this screen's state and disappears when the user confirms (FR-P03, NFR-06). */
function CreatedKey({ created, copy, onDone }: { created: CreatedApiKey; copy: CopyText; onDone: () => void }) {
  const [msg, setMsg] = useState<Msg>(null);
  const press = async () => {
    try { await copy(created.key); setMsg({ kind: 'info', text: t('mcp.created.copied') }); } catch { setMsg({ kind: 'error', text: t('mcp.created.copyError') }); }
  };
  return (
    <Stack accessibilityLabel={t('mcp.created.title')}>
      <SectionTitle>{t('mcp.created.title')}</SectionTitle>
      <Notice kind="info" text={t('mcp.created.warning')} />
      <Card>
        <Type mono selectable accessibilityLabel={t('mcp.created.title')}>{created.key}</Type>
      </Card>
      <Body muted>{t('mcp.created.share')}</Body>
      <Button label={t('mcp.created.copy')} onPress={press} />
      {msg ? <Notice kind={msg.kind} text={msg.text} /> : null}
      <Button label={t('mcp.created.done')} variant="secondary" onPress={onDone} />
    </Stack>
  );
}

function KeyRow({ k, confirming, busy, onAsk, onCancel, onConfirm }: { k: ApiKeyInfo; confirming: boolean; busy: boolean; onAsk: () => void; onCancel: () => void; onConfirm: () => void }) {
  const revoked = k.revokedAt !== null;
  return (
    <ListRow padded accessibilityLabel={t('mcp.keys.row', { name: k.name, prefix: k.prefix })}>
      <Stack gap="xs">
        <Type variant="bodyStrong">{k.name}</Type>
        <Type variant="caption" tone="muted" mono>{`${k.prefix}...`}</Type>
        <Type variant="caption" tone={revoked ? 'danger' : 'ok'}>{revoked ? t('mcp.keys.revoked') : t('mcp.keys.active')}</Type>
        <Type variant="caption" tone="muted">{k.lastUsedAt ? t('mcp.keys.lastUsed', { date: k.lastUsedAt.slice(0, 10) }) : t('mcp.keys.neverUsed')}</Type>
        {!revoked && !confirming ? <Button label={t('mcp.keys.revoke')} a11yLabel={t('mcp.keys.revoke.a11y', { name: k.name })} variant="danger" onPress={onAsk} /> : null}
        {!revoked && confirming ? (
          <>
            <Notice kind="error" text={t('mcp.keys.revoke.confirm', { name: k.name })} />
            <Button label={t('mcp.keys.revoke.yes')} variant="danger" busy={busy} disabled={busy} onPress={onConfirm} />
            <Button label={t('mcp.keys.revoke.no')} variant="secondary" disabled={busy} onPress={onCancel} />
          </>
        ) : null}
      </Stack>
    </ListRow>
  );
}

/** FR-P04: the plan comes from the server (profiles.is_premium via getProfile); no key request is made until it says premium. */
export function ConnectAiScreen({ apiKeys, onBack, onPremium, copy = copyText }: { apiKeys: ApiKeysService; onBack: () => void; onPremium: () => void; copy?: CopyText }) {
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
      if (e instanceof ApiKeysError && e.code === 'premium_required') { setPlan('free'); setNotice(null); return; }
      setNotice(t('mcp.error.create'));
      // a lost response or an unusable 201 body can leave a key the user never saw: the list is the source of truth
      if (e instanceof ApiKeysError && (e.code === 'network' || e.code === 'bad_response')) await load();
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
    } catch (e) {
      if (e instanceof ApiKeysError && e.code === 'not_found') { setConfirmId(null); await load(); return; } // already gone: show the real state, do not claim it still works
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
      <Stack accessibilityLabel={t('mcp.locked.title')}>
        <Type variant="h2">{t('mcp.locked.title')}</Type>
        <Body>{t('mcp.locked.body')}</Body>
        <Button label={t('profile.whatIsPremium')} variant="secondary" onPress={onPremium} />
      </Stack>
    </Screen>
  );

  const items = keys.status === 'ready' ? keys.items : [];
  return (
    <Screen title={title} onBack={onBack}>
      <Body muted>{t('mcp.intro')}</Body>
      {notice ? <Notice kind="error" text={notice} /> : null}
      {created ? <CreatedKey created={created} copy={copy} onDone={() => setCreated(null)} /> : null}
      <Stack>
        <SectionTitle>{t('mcp.keys.title')}</SectionTitle>
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
      </Stack>
      <SetupBlock title={t('mcp.setup.claude.title')} text={claudeSetupText()} copy={copy} />
      <SetupBlock title={t('mcp.setup.generic.title')} text={genericSetupText()} copy={copy} />
      <Body muted>{t('mcp.setup.hint')}</Body>
    </Screen>
  );
}

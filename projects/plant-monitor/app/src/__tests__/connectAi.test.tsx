// Connect your AI screen (4.A8, S42): premium generate (key shown once + copy), see that a key exists, revoke, free locked, error and loading states.
// Requirements: FR-P03 (create / revoke key, setup text), FR-P04 (free: locked, no key request), NFR-06 (key never stored or listed again).
// Mocked backend: an in-memory ApiKeysService and an in-memory auth service. No Supabase call, no network, no phone.
import React from 'react';
import { render, screen, fireEvent, waitFor, cleanup } from '@testing-library/react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { AuthProvider } from '../auth/AuthContext';
import { createFakeAuth } from '../auth/fakeAuth';
import { ConnectAiScreen } from '../screens/ConnectAiScreen';
import { ApiKeysError, type ApiKeyInfo, type ApiKeysService } from '../mcp/apiKeysApi';
import { claudeSetupText, genericSetupText } from '../mcp/setupText';
import { t } from '../i18n';

const SECRET = 'nwk_TESTONLY_not_a_real_key_0123456789abcdef'; // test fixture, not a key
const info = (over: Partial<ApiKeyInfo> = {}): ApiKeyInfo => ({ id: 'k-1', name: 'My AI assistant', prefix: 'nwk_TEST', createdAt: '2026-11-24T10:00:00Z', lastUsedAt: null, revokedAt: null, ...over });

/** In-memory backend: create adds a row, revoke sets revokedAt. Every method is a jest.fn so calls can be counted. */
function backend(initial: ApiKeyInfo[] = [], over: Partial<ApiKeysService> = {}) {
  let rows = [...initial];
  const svc = {
    list: jest.fn(async () => rows.map((r) => ({ ...r }))),
    create: jest.fn(async (name: string) => { rows = [...rows, info({ id: 'k-new', name, prefix: SECRET.slice(0, 8) })]; return { id: 'k-new', key: SECRET, prefix: SECRET.slice(0, 8) }; }),
    revoke: jest.fn(async (id: string) => { rows = rows.map((r) => (r.id === id ? { ...r, revokedAt: '2026-11-24T11:00:00Z' } : r)); }),
    ...over,
  };
  return svc as unknown as ApiKeysService & { list: jest.Mock; create: jest.Mock; revoke: jest.Mock };
}

const authWith = (isPremium: boolean | 'error') => ({
  ...createFakeAuth(),
  getSession: async () => ({ id: 'user-test', email: 'test@example.invalid' }),
  getProfile: async () => { if (isPremium === 'error') throw new Error('boom'); return { displayName: null, isPremium }; },
});

const frame = { frame: { x: 0, y: 0, width: 390, height: 844 }, insets: { top: 0, left: 0, right: 0, bottom: 0 } };
// keysAvailable defaults to true here so the create and revoke flows below stay covered; the v1 tests at the end mount with it off.
const mount = async (auth: ReturnType<typeof authWith>, apiKeys: ApiKeysService, copy = jest.fn(async () => undefined), keysAvailable = true) => {
  const onPremium = jest.fn();
  await render(<SafeAreaProvider initialMetrics={frame}><AuthProvider service={auth}><ConnectAiScreen apiKeys={apiKeys} onBack={() => undefined} onPremium={onPremium} copy={copy} keysAvailable={keysAvailable} /></AuthProvider></SafeAreaProvider>);
  return { onPremium, copy };
};

// The first render of this screen lazily loads and transforms the React Native / Expo modules it uses.
// On a cold jest cache that one-time cost is ~3 s here (more on a loaded CI runner), and it landed inside
// the first test (the free-locked test), which then hit the 5 s test timeout. The warm-up runs once in its own
// hook with its own budget, so every test below measures only its own work (~0.1 s each).
beforeAll(async () => {
  await mount(authWith(false), backend());
  await screen.findByText(t('mcp.locked.title'));
  await cleanup();
}, 60000);

describe('connect your AI: free account is locked (FR-P04)', () => {
  test('free: locked message, no key request of any kind, no create button', async () => {
    const b = backend();
    const { onPremium } = await mount(authWith(false), b);
    expect(await screen.findByText(t('mcp.locked.title'))).toBeTruthy();
    expect(screen.getByText(t('mcp.locked.body'))).toBeTruthy();
    expect(b.list).not.toHaveBeenCalled();
    expect(b.create).not.toHaveBeenCalled();
    expect(b.revoke).not.toHaveBeenCalled();
    expect(screen.queryByRole('button', { name: t('mcp.keys.create') })).toBeNull();
    await fireEvent.press(screen.getByRole('button', { name: t('profile.whatIsPremium') }));
    expect(onPremium).toHaveBeenCalled();
  });

  test('plan cannot be read: error, nothing requested (fails closed)', async () => {
    const b = backend();
    await mount(authWith('error'), b);
    expect(await screen.findByText(t('mcp.profileError'))).toBeTruthy();
    expect(b.list).not.toHaveBeenCalled();
    expect(screen.queryByText(t('mcp.locked.title'))).toBeNull();
  });

  test('server answers premium_required on create although the app thought premium: locked state, no key shown', async () => {
    const b = backend([], { create: jest.fn(async () => { throw new ApiKeysError('premium_required'); }) });
    await mount(authWith(true), b);
    await fireEvent.press(await screen.findByRole('button', { name: t('mcp.keys.create') }));
    expect(await screen.findByText(t('mcp.locked.title'))).toBeTruthy();
    expect(screen.queryByText(SECRET)).toBeNull();
  });
});

describe('connect your AI: premium generate, shown once, copy (FR-P03)', () => {
  test('loading: shows the loading line until the key list answers, no create button yet', async () => {
    const b = backend([], { list: jest.fn(() => new Promise<ApiKeyInfo[]>(() => undefined)) });
    await mount(authWith(true), b);
    expect(await screen.findByText(t('mcp.loading'))).toBeTruthy();
    expect(screen.queryByRole('button', { name: t('mcp.keys.create') })).toBeNull();
  });

  test('premium with no key: says so and offers Create key with the default name', async () => {
    const b = backend();
    await mount(authWith(true), b);
    expect(await screen.findByText(t('mcp.keys.none'))).toBeTruthy();
    expect(screen.getByDisplayValue(t('mcp.keys.nameDefault'))).toBeTruthy();
  });

  test('generate: the full key is shown with a warning, copy hands exactly that key to the clipboard', async () => {
    const b = backend();
    const { copy } = await mount(authWith(true), b);
    await fireEvent.changeText(await screen.findByLabelText(t('mcp.keys.name')), '  Kitchen laptop  ');
    await fireEvent.press(screen.getByRole('button', { name: t('mcp.keys.create') }));
    expect(await screen.findByText(SECRET)).toBeTruthy();
    expect(b.create).toHaveBeenCalledWith('Kitchen laptop');
    expect(screen.getByText(t('mcp.created.warning'))).toBeTruthy();
    await fireEvent.press(screen.getByRole('button', { name: t('mcp.created.copy') }));
    expect(await screen.findByText(t('mcp.created.copied'))).toBeTruthy();
    expect(copy).toHaveBeenCalledWith(SECRET);
  });

  test('the one-time key box carries the "never share your key" hint (the phone copy goes through the share sheet, accepted for the demo with this hint, A-133)', async () => {
    await mount(authWith(true), backend());
    expect(screen.queryByText(t('mcp.created.share'))).toBeNull();
    await fireEvent.press(await screen.findByRole('button', { name: t('mcp.keys.create') }));
    expect(await screen.findByText(t('mcp.created.share'))).toBeTruthy();
    expect(t('mcp.created.share')).toMatch(/never share your key/i);
  });

  test('a key exists afterwards: the list shows name, prefix and Active, never the full key', async () => {
    const b = backend();
    await mount(authWith(true), b);
    await fireEvent.press(await screen.findByRole('button', { name: t('mcp.keys.create') }));
    await screen.findByText(SECRET);
    expect(await screen.findByLabelText(t('mcp.keys.row', { name: 'My AI assistant', prefix: 'nwk_TEST' }))).toBeTruthy();
    expect(screen.getByText(t('mcp.keys.active'))).toBeTruthy();
    expect(screen.getByText('nwk_TEST...')).toBeTruthy();
  });

  test('shown once: after "I have saved my key" the full key is gone and no later load brings it back', async () => {
    const b = backend();
    await mount(authWith(true), b);
    await fireEvent.press(await screen.findByRole('button', { name: t('mcp.keys.create') }));
    await screen.findByText(SECRET);
    await fireEvent.press(screen.getByRole('button', { name: t('mcp.created.done') }));
    await waitFor(() => expect(screen.queryByText(SECRET)).toBeNull());
    expect(screen.queryByText(t('mcp.created.warning'))).toBeNull();
    expect(screen.getByText('nwk_TEST...')).toBeTruthy(); // only the prefix remains
  });

  test('create fails (network): honest message, no key shown, user can try again', async () => {
    const b = backend([], { create: jest.fn(async () => { throw new ApiKeysError('network'); }) });
    await mount(authWith(true), b);
    await fireEvent.press(await screen.findByRole('button', { name: t('mcp.keys.create') }));
    expect(await screen.findByText(t('mcp.error.create'))).toBeTruthy();
    expect(screen.queryByText(t('mcp.created.title'))).toBeNull();
    expect(screen.getByRole('button', { name: t('mcp.keys.create') })).toBeTruthy();
  });

  test.each(['network', 'bad_response'] as const)('create fails with %s: copy says it MAY not exist and the list is reloaded', async (code) => {
    const rows: ApiKeyInfo[] = [];
    const b = backend([], {
      list: jest.fn(async () => rows.map((r) => ({ ...r }))),
      create: jest.fn(async () => { rows.push(info({ id: 'k-ghost', name: 'Ghost' })); throw new ApiKeysError(code); }), // server created it, the response was lost
    });
    await mount(authWith(true), b);
    await fireEvent.press(await screen.findByRole('button', { name: t('mcp.keys.create') }));
    expect(await screen.findByText(t('mcp.error.create'))).toBeTruthy();
    expect(t('mcp.error.create')).toMatch(/may not have been created/);
    expect(await screen.findByLabelText(t('mcp.keys.row', { name: 'Ghost', prefix: 'nwk_TEST' }))).toBeTruthy();
    expect(b.list).toHaveBeenCalledTimes(2);
  });

  test('create fails with server error: no reload needed beyond the first load', async () => {
    const b = backend([], { create: jest.fn(async () => { throw new ApiKeysError('server'); }) });
    await mount(authWith(true), b);
    await fireEvent.press(await screen.findByRole('button', { name: t('mcp.keys.create') }));
    expect(await screen.findByText(t('mcp.error.create'))).toBeTruthy();
    expect(b.list).toHaveBeenCalledTimes(1);
  });

  test('empty name: field error and no create request', async () => {
    const b = backend();
    await mount(authWith(true), b);
    await fireEvent.changeText(await screen.findByLabelText(t('mcp.keys.name')), '   ');
    expect(screen.getByText(t('mcp.keys.name.required'))).toBeTruthy();
    await fireEvent.press(screen.getByRole('button', { name: t('mcp.keys.create') }));
    expect(b.create).not.toHaveBeenCalled();
  });

  test('copy fails: tells the user to copy by hand, key stays visible', async () => {
    const b = backend();
    await mount(authWith(true), b, jest.fn(async () => { throw new Error('no clipboard'); }));
    await fireEvent.press(await screen.findByRole('button', { name: t('mcp.keys.create') }));
    await screen.findByText(SECRET);
    await fireEvent.press(screen.getByRole('button', { name: t('mcp.created.copy') }));
    expect(await screen.findByText(t('mcp.created.copyError'))).toBeTruthy();
    expect(screen.getByText(SECRET)).toBeTruthy();
  });

  test('list cannot be loaded: error with Try again, no create button until it loads', async () => {
    let fail = true;
    const b = backend([info()], { list: jest.fn(async () => { if (fail) throw new ApiKeysError('server'); return [info()]; }) });
    await mount(authWith(true), b);
    expect(await screen.findByText(t('mcp.error.load'))).toBeTruthy();
    expect(screen.queryByRole('button', { name: t('mcp.keys.create') })).toBeNull();
    fail = false;
    await fireEvent.press(screen.getByRole('button', { name: t('common.tryAgain') }));
    expect(await screen.findByRole('button', { name: t('mcp.keys.create') })).toBeTruthy();
  });
});

describe('connect your AI: revoke (FR-P03)', () => {
  test('revoke asks first; "Keep it" cancels without a request', async () => {
    const b = backend([info()]);
    await mount(authWith(true), b);
    await fireEvent.press(await screen.findByRole('button', { name: t('mcp.keys.revoke.a11y', { name: 'My AI assistant' }) }));
    expect(screen.getByText(t('mcp.keys.revoke.confirm', { name: 'My AI assistant' }))).toBeTruthy();
    await fireEvent.press(screen.getByRole('button', { name: t('mcp.keys.revoke.no') }));
    expect(b.revoke).not.toHaveBeenCalled();
    expect(screen.queryByText(t('mcp.keys.revoke.confirm', { name: 'My AI assistant' }))).toBeNull();
  });

  test('confirm: revoke is called with the key id and the row turns Revoked with no revoke button', async () => {
    const b = backend([info()]);
    await mount(authWith(true), b);
    await fireEvent.press(await screen.findByRole('button', { name: t('mcp.keys.revoke.a11y', { name: 'My AI assistant' }) }));
    await fireEvent.press(screen.getByRole('button', { name: t('mcp.keys.revoke.yes') }));
    expect(await screen.findByText(t('mcp.keys.revoked'))).toBeTruthy();
    expect(b.revoke).toHaveBeenCalledWith('k-1');
    expect(screen.queryByText(t('mcp.keys.active'))).toBeNull();
    expect(screen.queryByRole('button', { name: t('mcp.keys.revoke.a11y', { name: 'My AI assistant' }) })).toBeNull();
  });

  test('revoke fails: says the key was NOT revoked and still works; row stays Active', async () => {
    const b = backend([info()], { revoke: jest.fn(async () => { throw new ApiKeysError('network'); }) });
    await mount(authWith(true), b);
    await fireEvent.press(await screen.findByRole('button', { name: t('mcp.keys.revoke.a11y', { name: 'My AI assistant' }) }));
    await fireEvent.press(screen.getByRole('button', { name: t('mcp.keys.revoke.yes') }));
    expect(await screen.findByText(t('mcp.error.revoke'))).toBeTruthy();
    expect(screen.getByText(t('mcp.keys.active'))).toBeTruthy();
  });

  test('revoke answers 404 (already gone): no "still works" claim, the list is reloaded and shows the real state', async () => {
    let rows = [info()];
    const b = backend([], {
      list: jest.fn(async () => rows.map((r) => ({ ...r }))),
      revoke: jest.fn(async () => { rows = [info({ revokedAt: '2026-11-24T09:00:00Z' })]; throw new ApiKeysError('not_found'); }),
    });
    await mount(authWith(true), b);
    await fireEvent.press(await screen.findByRole('button', { name: t('mcp.keys.revoke.a11y', { name: 'My AI assistant' }) }));
    await fireEvent.press(screen.getByRole('button', { name: t('mcp.keys.revoke.yes') }));
    expect(await screen.findByText(t('mcp.keys.revoked'))).toBeTruthy();
    expect(screen.queryByText(t('mcp.error.revoke'))).toBeNull();
    expect(b.list).toHaveBeenCalledTimes(2);
  });

  test('an already revoked key is listed as Revoked with its last-used date and cannot be revoked again', async () => {
    const b = backend([info({ revokedAt: '2026-11-20T08:00:00Z', lastUsedAt: '2026-11-19T09:30:00Z' })]);
    await mount(authWith(true), b);
    expect(await screen.findByText(t('mcp.keys.revoked'))).toBeTruthy();
    expect(screen.getByText(t('mcp.keys.lastUsed', { date: '2026-11-19' }))).toBeTruthy();
    expect(screen.queryByRole('button', { name: t('mcp.keys.revoke.a11y', { name: 'My AI assistant' }) })).toBeNull();
  });
});

describe('connect your AI: setup text (FR-P03)', () => {
  test('Claude and generic text use placeholders only: no key, no host', () => {
    for (const text of [claudeSetupText(), genericSetupText()]) {
      expect(text).toContain('<YOUR_API_KEY>');
      expect(text).toContain('<MCP_SERVER_URL>');
      expect(text).not.toMatch(/nwk_[A-Za-z0-9_-]{8,}/);
      expect(text).not.toMatch(/https?:\/\/(?!<)/);
    }
    expect(claudeSetupText()).toMatch(/^claude mcp add --transport http nilwerk-plant-monitor /);
    const parsed = JSON.parse(genericSetupText());
    expect(parsed.mcpServers['nilwerk-plant-monitor'].headers.Authorization).toBe('Bearer <YOUR_API_KEY>');
  });

  test('setup blocks are shown and each copy button copies its own text; a fresh key is never put into them', async () => {
    const b = backend();
    const { copy } = await mount(authWith(true), b);
    await screen.findByText(t('mcp.keys.none'));
    expect(screen.getByText(claudeSetupText())).toBeTruthy();
    expect(screen.getByText(genericSetupText())).toBeTruthy();
    await fireEvent.press(screen.getByRole('button', { name: `${t('mcp.setup.copy')}: ${t('mcp.setup.claude.title')}` }));
    await waitFor(() => expect(copy).toHaveBeenCalledWith(claudeSetupText()));
    await fireEvent.press(screen.getByRole('button', { name: `${t('mcp.setup.copy')}: ${t('mcp.setup.generic.title')}` }));
    await waitFor(() => expect(copy).toHaveBeenCalledWith(genericSetupText()));
    await fireEvent.press(screen.getByRole('button', { name: t('mcp.keys.create') }));
    await screen.findByText(SECRET);
    expect(screen.getByText(claudeSetupText())).toBeTruthy(); // still the placeholder text
  });
});

describe('connect your AI: v1 actions coming in a later version (owner decision)', () => {
  // Generate and revoke are disabled in v1: they show "Coming in a later version" and call nothing on the server.
  test('premium: no Create key action; a disabled "Coming in a later version" button; pressing it creates nothing', async () => {
    const b = backend();
    await mount(authWith(true), b, undefined, false);
    await waitFor(() => expect(screen.getByRole('button', { name: t('mcp.comingSoon') })).toBeTruthy());
    expect(screen.queryByRole('button', { name: t('mcp.keys.create') })).toBeNull();
    const generate = screen.getByRole('button', { name: t('mcp.comingSoon') });
    expect(generate.props.accessibilityState).toEqual(expect.objectContaining({ disabled: true }));
    fireEvent.press(generate);
    expect(b.create).not.toHaveBeenCalled();
  });

  test('premium with an active key: revoke is disabled and says "Coming in a later version"; no revoke request, no confirm', async () => {
    const b = backend([info()]);
    await mount(authWith(true), b, undefined, false);
    expect(await screen.findByText('My AI assistant')).toBeTruthy();
    expect(screen.queryByRole('button', { name: t('mcp.keys.revoke.a11y', { name: 'My AI assistant' }) })).toBeTruthy();
    const revoke = screen.getByRole('button', { name: t('mcp.keys.revoke.a11y', { name: 'My AI assistant' }) });
    expect(revoke.props.accessibilityState).toEqual(expect.objectContaining({ disabled: true }));
    expect(screen.getAllByText(t('mcp.comingSoon'))).toHaveLength(2);   // revoke button (name) and the disabled generate button
    fireEvent.press(revoke);
    expect(screen.queryByText(t('mcp.keys.revoke.confirm', { name: 'My AI assistant' }))).toBeNull();
    expect(b.revoke).not.toHaveBeenCalled();
  });

  test('the list still reads the user keys (no key is created or revoked); the setup text stays available', async () => {
    const b = backend([info()]);
    const { copy } = await mount(authWith(true), b, undefined, false);
    expect(await screen.findByText(t('mcp.setup.claude.title'))).toBeTruthy();
    expect(b.list).toHaveBeenCalledTimes(1);
    expect(b.create).not.toHaveBeenCalled();
    expect(copy).not.toHaveBeenCalled();
  });
});

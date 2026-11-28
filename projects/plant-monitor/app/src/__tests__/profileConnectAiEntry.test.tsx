// Profile -> Connect your AI journey (4.A8): what a first-time premium user taps, and that a free user never sees the entry.
// Requirements: FR-P03 (connect your AI), FR-P04 (premium only). Fake auth and a mocked key backend; no network, no phone.
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { Root } from '../../App';
import { AuthProvider } from '../auth/AuthContext';
import { createFakeAuth } from '../auth/fakeAuth';
import { PlantsProvider } from '../plants/PlantsContext';
import { createFakePlants } from '../plants/fakePlants';
import { createFakeSetup } from '../provisioning/fakeProvisioning';
import type { ApiKeysService } from '../mcp/apiKeysApi';
import { t } from '../i18n';

const frame = { frame: { x: 0, y: 0, width: 390, height: 844 }, insets: { top: 0, left: 0, right: 0, bottom: 0 } };
const svcWith = (isPremium: boolean) => ({
  ...createFakeAuth(),
  getSession: async () => ({ id: 'user-test', email: 'test@example.invalid' }),
  getProfile: async () => ({ displayName: null, isPremium }),
});
const SECRET = 'nwk_TESTONLY_journey_fixture_0123456789';
const keys = () => ({ list: jest.fn(async () => []), create: jest.fn(async () => ({ id: 'k-1', key: SECRET, prefix: 'nwk_TEST' })), revoke: jest.fn(async () => undefined) });

const mountRoot = async (isPremium: boolean, apiKeys: ReturnType<typeof keys>) => {
  await render(<SafeAreaProvider initialMetrics={frame}><AuthProvider service={svcWith(isPremium)}><PlantsProvider service={createFakePlants()}>
    <Root contactEmail="hello@example.invalid" setup={createFakeSetup().services} apiKeys={apiKeys as unknown as ApiKeysService} />
  </PlantsProvider></AuthProvider></SafeAreaProvider>);
};

describe('profile entry to Connect your AI (FR-P03, FR-P04)', () => {
  test('free account: no Connect your AI button and no key request', async () => {
    const k = keys();
    await mountRoot(false, k);
    await fireEvent.press(await screen.findByRole('tab', { name: t('nav.profile') }));
    await screen.findByRole('button', { name: t('profile.whatIsPremium') });
    expect(screen.queryByRole('button', { name: t('profile.connectAi') })).toBeNull();
    expect(k.list).not.toHaveBeenCalled();
  });

  test('premium journey: profile -> Connect your AI shows the v1 notice; the generate action is disabled and creates no key (owner decision)', async () => {
    const k = keys();
    await mountRoot(true, k);
    await fireEvent.press(await screen.findByRole('tab', { name: t('nav.profile') }));
    await fireEvent.press(await screen.findByRole('button', { name: t('profile.connectAi') }));
    expect(await screen.findByRole('header', { name: t('mcp.title') })).toBeTruthy();
    const generate = await screen.findByRole('button', { name: t('mcp.comingSoon') });
    expect(generate.props.accessibilityState).toEqual(expect.objectContaining({ disabled: true }));
    await fireEvent.press(generate);
    expect(screen.queryByText(SECRET)).toBeNull();
    expect(k.create).not.toHaveBeenCalled();
  });
});

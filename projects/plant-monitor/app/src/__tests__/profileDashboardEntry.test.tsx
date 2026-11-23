// Profile -> premium dashboard entry (4.A6, FR-P04): the entry is shown to premium accounts only. Fake auth and analytics; no network.
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { Root } from '../../App';
import { AuthProvider } from '../auth/AuthContext';
import { createFakeAuth } from '../auth/fakeAuth';
import { PlantsProvider } from '../plants/PlantsContext';
import { createFakePlants } from '../plants/fakePlants';
import { createFakeSetup } from '../provisioning/fakeProvisioning';
import type { AnalyticsService } from '../analytics/analyticsApi';
import { t } from '../i18n';

const frame = { frame: { x: 0, y: 0, width: 390, height: 844 }, insets: { top: 0, left: 0, right: 0, bottom: 0 } };
const svcWith = (isPremium: boolean) => ({
  ...createFakeAuth(),
  getSession: async () => ({ id: 'user-test', email: 'test@example.invalid' }),
  getProfile: async () => ({ displayName: null, isPremium }),
});
const analytics = { fetchWindow: jest.fn(async () => { throw new Error('not expected in this test'); }) } as unknown as AnalyticsService;

const mountRoot = async (isPremium: boolean) => {
  await render(<SafeAreaProvider initialMetrics={frame}><AuthProvider service={svcWith(isPremium)}><PlantsProvider service={createFakePlants()}>
    <Root contactEmail="hello@example.invalid" setup={createFakeSetup().services} analytics={analytics} />
  </PlantsProvider></AuthProvider></SafeAreaProvider>);
};

describe('profile entry to the premium dashboard (FR-P04)', () => {
  test('free account: no dashboard button on the profile', async () => {
    await mountRoot(false);
    fireEvent.press(await screen.findByRole('tab', { name: t('nav.profile') }));
    await screen.findByRole('button', { name: t('profile.whatIsPremium') });
    expect(screen.queryByRole('button', { name: t('profile.dashboard') })).toBeNull();
  });

  test('premium account: the dashboard button opens the dashboard screen', async () => {
    await mountRoot(true);
    fireEvent.press(await screen.findByRole('tab', { name: t('nav.profile') }));
    fireEvent.press(await screen.findByRole('button', { name: t('profile.dashboard') }));
    expect(await screen.findByRole('header', { name: t('dashboard.title') })).toBeTruthy();
  });
});

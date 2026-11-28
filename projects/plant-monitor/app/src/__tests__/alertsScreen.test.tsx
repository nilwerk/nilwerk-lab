// Alerts screen (4.A5, FR-A07) and its entry from the plant list. Runs against the in-memory fake plants (MOCK data), not a backend.
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { AlertsScreen } from '../screens/AlertsScreen';
import { PlantsScreen } from '../screens/PlantsScreen';
import { PlantsProvider } from '../plants/PlantsContext';
import { createFakePlants } from '../plants/fakePlants';
import { t } from '../i18n';
import { OFFLINE_AFTER_MIN } from '../plants/alerts';

const frame = { frame: { x: 0, y: 0, width: 390, height: 844 }, insets: { top: 0, left: 0, right: 0, bottom: 0 } };
const withPlants = async (ui: React.ReactElement, service = createFakePlants()) =>
  await render(<SafeAreaProvider initialMetrics={frame}><PlantsProvider service={service}>{ui}</PlantsProvider></SafeAreaProvider>);

describe('alerts screen', () => {
  test('lists the mock alerts for the plants with a sensor, with their values', async () => {
    await withPlants(<AlertsScreen onBack={() => undefined} />);
    expect(await screen.findByRole('header', { name: 'Alerts' })).toBeTruthy();
    expect(screen.getByText('Cactus')).toBeTruthy();
    expect(screen.getByText('Soil moisture 12.0 %, below the dry limit of 25 %.')).toBeTruthy();
    expect(screen.getByText('Fern')).toBeTruthy();
    expect(screen.getByText('Sensor battery 3.35 V, below 3.40 V.')).toBeTruthy();
    expect(screen.getByText(/^No report from the sensor for 5 h \d+ min\.$/)).toBeTruthy();
    expect(screen.getByText('Orchid')).toBeTruthy();
  });

  test('plants without an alert and without a sensor are not listed', async () => {
    await withPlants(<AlertsScreen onBack={() => undefined} />);
    await screen.findByText('Cactus');
    expect(screen.queryByText('Basil')).toBeNull();
    expect(screen.queryByText('Rubber tree')).toBeNull();
  });

  test('says push is not built, on the same screen', async () => {
    await withPlants(<AlertsScreen onBack={() => undefined} />);
    expect(await screen.findByText(t('alerts.intro'))).toBeTruthy();
    expect(t('alerts.intro')).toMatch(/Push notifications are not built yet/);
  });

  test('empty state when no plant has an alert', async () => {
    await withPlants(<AlertsScreen onBack={() => undefined} />, createFakePlants({
      plants: [{ id: 'p1', name: 'Mint', locationType: 'house', area: 'Sill', soilType: 'potting', deviceId: 'aa1122', deviceName: 'NW-aa1122', lastSeenAt: new Date().toISOString(), openAlerts: [], dryThresholdPct: 25, wetThresholdPct: 85, latest: { ts: new Date().toISOString(), moisturePct: 40, tempC: 21, rhPct: 48, lux: 900, vbatMv: 3800 } }],
      hourly: {},
    }));
    expect(await screen.findByText('No alerts right now')).toBeTruthy();
  });

  test('empty-state copy states the offline rule as the rule has it (190 min = 3 h 10 min)', () => {
    expect(OFFLINE_AFTER_MIN).toBe(190);
    expect(t('alerts.empty.body')).toMatch(/more than 3 h 10 min\./);
    expect(t('alerts.empty.body')).not.toMatch(/3 hours/);
  });

  test('a failed load shows the error and a retry button', async () => {
    await withPlants(<AlertsScreen onBack={() => undefined} />, createFakePlants({ failList: true }));
    expect(await screen.findByText(t('alerts.error.load'))).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Try again' })).toBeTruthy();
  });
});

describe('entry from the plant list', () => {
  test('the plant list no longer has a View alerts button (alerts are in the footer tab; owner feedback 28 Nov)', async () => {
    await withPlants(<PlantsScreen onOpen={() => undefined} />);
    expect(await screen.findByText('Cactus')).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'View alerts' })).toBeNull();
  });
});

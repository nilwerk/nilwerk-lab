// v3 structure (My plants and plant detail): needs-attention counts computed on the client from the loaded list, empty-state actions,
// sticky title on long lists only, and the soil hero number that is not repeated. Runs against the in-memory fake plants (MOCK data).
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { PlantsScreen, isLongList } from '../screens/PlantsScreen';
import { PlantDetailScreen } from '../screens/PlantDetailScreen';
import { PlantsProvider } from '../plants/PlantsContext';
import { createFakePlants, sampleFixture } from '../plants/fakePlants';
import { attentionCounts } from '../plants/status';
import { type PlantSummary } from '../plants/types';

const frame = { frame: { x: 0, y: 0, width: 390, height: 844 }, insets: { top: 0, left: 0, right: 0, bottom: 0 } };
const NOW = new Date();
const mountWith = async (ui: React.ReactElement, service = createFakePlants({ now: () => NOW })) =>
  await render(<SafeAreaProvider initialMetrics={frame}><PlantsProvider service={service}>{ui}</PlantsProvider></SafeAreaProvider>);
const plantsScreen = (over: Partial<React.ComponentProps<typeof PlantsScreen>> = {}) =>
  <PlantsScreen onOpen={() => undefined} onAlerts={() => undefined} onAddSensor={() => undefined} {...over} />;

describe('needs-attention counts (client side, no endpoint)', () => {
  test('counts plants per state from the open alerts already in the list', () => {
    const { plants } = sampleFixture(NOW);
    // fixture: Cactus too dry, Fern low battery, Orchid offline, Rubber tree no sensor
    expect(attentionCounts(plants)).toEqual({ dry: 1, wet: 0, lowBattery: 1 });
  });
  test('a plant with several states counts once in each', () => {
    const p = { deviceId: 'd', openAlerts: ['too_dry', 'low_battery'] as PlantSummary['openAlerts'] };
    expect(attentionCounts([p, p])).toEqual({ dry: 2, wet: 0, lowBattery: 2 });
  });
  test('the strip shows the counts when at least one is above zero', async () => {
    await mountWith(plantsScreen());
    expect(await screen.findByText('Needs attention')).toBeTruthy();
    expect(screen.getByText('1 too dry')).toBeTruthy();
    expect(screen.getByText('1 low battery')).toBeTruthy();
    expect(screen.queryByText(/too wet/)).toBeNull(); // zero counts are not listed
  });
  test('no strip when nothing needs attention (no false reassurance either)', async () => {
    await mountWith(plantsScreen(), createFakePlants({ now: () => NOW, plants: [] }));
    await screen.findByRole('header', { name: 'No plants yet' });
    expect(screen.queryByText('Needs attention')).toBeNull();
  });
});

describe('empty state (My plants)', () => {
  test('one primary action adds the first plant, and the link explains the sensor', async () => {
    const onAddSensor = jest.fn();
    await mountWith(plantsScreen({ onAddSensor }), createFakePlants({ plants: [] }));
    expect(await screen.findByRole('header', { name: 'No plants yet' })).toBeTruthy();
    expect(screen.queryByText('Measures every 15 minutes')).toBeNull();
    await fireEvent.press(screen.getByRole('button', { name: 'Add your first plant' }));
    expect(onAddSensor).toHaveBeenCalledTimes(1);
    expect(screen.queryByText('The sensor measures every 15 minutes.')).toBeNull();
    await fireEvent.press(screen.getByRole('button', { name: 'How the sensor works' }));
    expect(screen.getByText('The sensor measures every 15 minutes.')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Hide how the sensor works' })).toBeTruthy();
  });
});

describe('sticky title (long lists only)', () => {
  test('the threshold: a list of four or fewer is not long, five or more is', () => {
    expect(isLongList(4)).toBe(false);
    expect(isLongList(5)).toBe(true);
  });
  test('the title stays a header in a long list (sticky layout keeps the same accessible title)', async () => {
    const { plants, hourly, photos } = sampleFixture(NOW);
    const many = Array.from({ length: 6 }, (_, i) => ({ ...plants[0], id: `m${i}`, name: `Plant ${i}` }));
    await mountWith(plantsScreen(), createFakePlants({ now: () => NOW, plants: many, hourly, photos }));
    expect(await screen.findByRole('header', { name: 'My plants' })).toBeTruthy();
    expect(await screen.findByText('Plant 0')).toBeTruthy();
  });
});

describe('plant detail hero (v3)', () => {
  test('the soil value is shown once, as the hero number, and the other readings follow', async () => {
    const svc = createFakePlants({ now: () => NOW });
    const detail = await svc.getPlantDetail('p-basil');
    await mountWith(<PlantDetailScreen plantId="p-basil" onBack={() => undefined} onRemove={() => undefined} onGallery={() => undefined} now={() => NOW} />, svc);
    expect(await screen.findByRole('header', { name: 'Basil' })).toBeTruthy();
    expect(screen.getAllByText(`${Math.round(detail.plant.latest!.moisturePct!)} %`)).toHaveLength(1);
    expect(screen.getByText('Soil')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Photos' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Remove plant' })).toBeTruthy();
  });
  test('a plant with no reading shows a dash in the hero', async () => {
    const svc = createFakePlants({ now: () => NOW });
    await mountWith(<PlantDetailScreen plantId="p-rubber" onBack={() => undefined} onRemove={() => undefined} onGallery={() => undefined} now={() => NOW} />, svc);
    await screen.findByRole('header', { name: 'Rubber tree' });
    expect(screen.getByText('Soil')).toBeTruthy();
    expect(screen.getAllByText('-').length).toBeGreaterThan(0);
  });
});

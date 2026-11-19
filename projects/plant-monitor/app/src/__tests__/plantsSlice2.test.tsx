// Plants slice 2 (4.A4): metadata on detail, hourly table with boundary cases, photo gallery (unlimited, dated), export before delete, photo objects removed from storage.
// Requirements: FR-A04 (location type, room, soil type), FR-A05 (unlimited dated photos), FR-A06 (hourly table), FR-D02 (24 reports a day), FR-A06 (gaps), FR-A08 + A-022 (remove after export), NFR-06, NFR-07.
// Against the in-memory PlantsService mock (no network, no Supabase). Pure boundary logic is in hourly.test.ts.
import React from 'react';
import { render, screen, fireEvent, within } from '@testing-library/react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { Root } from '../../App';
import { createFakeSetup } from '../provisioning/fakeProvisioning';
import { AuthProvider } from '../auth/AuthContext';
import { createFakeAuth } from '../auth/fakeAuth';
import { PlantsProvider } from '../plants/PlantsContext';
import { createFakePlants, sampleFixture, syntheticPhotos, syntheticRows } from '../plants/fakePlants';
import { fmtDay, fmtHour } from '../plants/format';
import { HOURS } from '../plants/hourly';
import { sortPhotos } from '../screens/PlantGalleryScreen';
import type { HourlyPoint, PlantSummary } from '../plants/types';

const NOW = new Date('2026-11-09T12:30:00Z');
const H = 3600_000;
const END = Date.parse('2026-11-09T12:00:00Z');
const row = (hoursAgo: number, v = 40): HourlyPoint => ({ hour: new Date(END - hoursAgo * H).toISOString(), n: 4, moistureAvg: v, moistureMin: v, moistureMax: v, tempAvg: 20.5, rhAvg: 50, luxAvg: 900, vbatMinMv: 3600 });
const basil = (): PlantSummary => sampleFixture(NOW).plants[0];

const mount = async (svc: ReturnType<typeof createFakePlants>) => {
  const auth = createFakeAuth();
  await auth.signUp('sam@example.com', 'long-enough-1', 'Sam');
  await render(
    <SafeAreaProvider initialMetrics={{ frame: { x: 0, y: 0, width: 390, height: 844 }, insets: { top: 0, left: 0, right: 0, bottom: 0 } }}>
      <AuthProvider service={auth}><PlantsProvider service={svc}><Root contactEmail="x@example.invalid" setup={createFakeSetup().services} /></PlantsProvider></AuthProvider>
    </SafeAreaProvider>,
  );
  await screen.findByRole('header', { name: 'My plants' });
};
const press = async (name: string, role: 'button' | 'tab' = 'button') => fireEvent.press(await screen.findByRole(role, { name }));
const openPlant = async (name: RegExp) => { await fireEvent.press(await screen.findByRole('button', { name })); };
const rowsOf = () => screen.queryAllByTestId('hourly-row');
type Node = ReturnType<typeof screen.getByTestId>;
const gapCells = (r: Node) => within(r).queryAllByText('—');

describe('plant detail metadata (FR-A04)', () => {
  test('location type, room and soil type are shown on the detail', async () => {
    await mount(createFakePlants({ now: () => NOW }));
    await openPlant(/^Basil/);
    await screen.findByRole('header', { name: 'Basil' });
    expect(within(screen.getByTestId('plant-meta-location')).getByText('House')).toBeTruthy();
    expect(within(screen.getByTestId('plant-meta-room')).getByText('Kitchen window')).toBeTruthy();
    expect(within(screen.getByTestId('plant-meta-soil')).getByText('Potting soil')).toBeTruthy();
  });
});

describe('hourly data table on the plant detail (FR-A06, FR-D02)', () => {
  test('full series: 168 rows, newest first, exact column headers, values from the last hour', async () => {
    const svc = createFakePlants({ now: () => NOW });
    await mount(svc);
    await openPlant(/^Basil/);
    await screen.findByRole('header', { name: 'Hourly readings, last 7 days' });
    expect(rowsOf()).toHaveLength(HOURS);
    const head = within(screen.getByTestId('hourly-head')).getAllByText(/.+/).map((n) => n.props.children);
    expect(head).toEqual(['Time', 'Soil %', 'Temp °C', 'RH %', 'Light lx', 'Battery V']);
    const detail = await svc.getPlantDetail('p-basil');
    const newest = detail.hourly[HOURS - 1];
    const first = rowsOf()[0];
    expect(within(first).getByText(fmtHour(newest.hour))).toBeTruthy();
    expect(within(first).getByText(String(Math.round(newest.moistureAvg!)))).toBeTruthy();
    expect(within(first).getByText((newest.tempAvg as number).toFixed(1))).toBeTruthy();
    expect(within(first).getByText('3.60')).toBeTruthy();
  });

  test('gap in time (Orchid, 5 offline hours): those rows show dashes, the next row shows values', async () => {
    await mount(createFakePlants({ now: () => NOW }));
    await openPlant(/^Orchid/);
    await screen.findByRole('header', { name: 'Orchid' });
    expect(rowsOf()).toHaveLength(HOURS);
    for (let i = 0; i < 5; i++) expect(gapCells(rowsOf()[i])).toHaveLength(5);
    expect(gapCells(rowsOf()[5])).toHaveLength(0);
  });

  test('boundary ONE reading: one filled row, 167 gap rows, chart shows one bar', async () => {
    const svc = createFakePlants({ now: () => NOW, plants: [basil()], hourly: { 'p-basil': [row(0, 33)] } });
    await mount(svc);
    await openPlant(/^Basil/);
    await screen.findByRole('header', { name: 'Basil' });
    expect(rowsOf()).toHaveLength(HOURS);
    expect(screen.getAllByTestId('chart-bar')).toHaveLength(1);
    expect(screen.getAllByText('—')).toHaveLength((HOURS - 1) * 5);
    expect(within(rowsOf()[0]).getByText('33')).toBeTruthy();
  });

  test('boundary 24 READINGS (FR-D02): 24 filled rows at the newest end, 144 gap rows', async () => {
    const rows = Array.from({ length: 24 }, (_, i) => row(i));
    await mount(createFakePlants({ now: () => NOW, plants: [basil()], hourly: { 'p-basil': rows } }));
    await openPlant(/^Basil/);
    await screen.findByRole('header', { name: 'Basil' });
    expect(screen.getAllByTestId('chart-bar')).toHaveLength(24);
    expect(gapCells(rowsOf()[23])).toHaveLength(0);
    expect(gapCells(rowsOf()[24])).toHaveLength(5);
  });

  test('boundary EMPTY (sensor never reported): no table rows, the empty text instead', async () => {
    await mount(createFakePlants({ now: () => NOW }));
    await openPlant(/^Rubber tree/);
    await screen.findByRole('header', { name: 'Rubber tree' });
    expect(rowsOf()).toHaveLength(0);
    expect(screen.getByText('No hourly rows in the last 7 days.')).toBeTruthy();
  });
});

describe('photo gallery (S23, FR-A05): unlimited, dated, newest or oldest first', () => {
  const open = async (svc: ReturnType<typeof createFakePlants>) => {
    await mount(svc);
    await openPlant(/^Basil/);
    await screen.findByRole('header', { name: 'Basil' });
    await press('Photos');
    await screen.findByRole('header', { name: 'Photos of Basil' });
  };
  test('Basil has 12 photos: all shown, newest first by default, each with its date and the plant metadata', async () => {
    await open(createFakePlants({ now: () => NOW }));
    expect(screen.getByTestId('gallery-count').props.children).toBe('12 photos');
    const tiles = screen.getAllByTestId('gallery-photo');
    expect(tiles).toHaveLength(12);
    expect(tiles[0].props.accessibilityLabel).toBe(`Photo taken ${fmtDay(NOW.toISOString())}`);
    expect(tiles[11].props.accessibilityLabel).toBe(`Photo taken ${fmtDay(new Date(NOW.getTime() - 22 * 24 * H).toISOString())}`);
    expect(within(screen.getByTestId('plant-meta-soil')).getByText('Potting soil')).toBeTruthy();
    expect(within(screen.getByTestId('plant-meta-room')).getByText('Kitchen window')).toBeTruthy();
  });
  test('Oldest first flips the order', async () => {
    await open(createFakePlants({ now: () => NOW }));
    await press('Oldest first');
    const tiles = screen.getAllByTestId('gallery-photo');
    expect(tiles[0].props.accessibilityLabel).toBe(`Photo taken ${fmtDay(new Date(NOW.getTime() - 22 * 24 * H).toISOString())}`);
  });
  test('no limit: 60 photos of one plant are all rendered and counted (FR-A05, FR-A02 spirit)', async () => {
    const many = syntheticPhotos('p-basil', NOW, 60);
    await open(createFakePlants({ now: () => NOW, photos: { 'p-basil': many } }));
    expect(screen.getAllByTestId('gallery-photo')).toHaveLength(60);
    expect(screen.getByTestId('gallery-count').props.children).toBe('60 photos');
  });
  test('a plant with no photos shows the empty state', async () => {
    await mount(createFakePlants({ now: () => NOW }));
    await openPlant(/^Cactus/);
    await screen.findByRole('header', { name: 'Cactus' });
    await press('Photos');
    expect(await screen.findByRole('header', { name: 'No photos yet' })).toBeTruthy();
    expect(screen.queryAllByTestId('gallery-photo')).toHaveLength(0);
  });
  test('load error shows the message; Try again recovers', async () => {
    const svc = createFakePlants({ now: () => NOW });
    await mount(svc);
    await openPlant(/^Basil/);
    await screen.findByRole('header', { name: 'Basil' });
    svc.options.failList = true;
    await press('Photos');
    expect(await screen.findByText('Could not load the photos. Try again.')).toBeTruthy();
    svc.options.failList = false;
    await press('Try again');
    expect(await screen.findAllByTestId('gallery-photo')).toHaveLength(12);
  });
  test('sortPhotos orders by the taken date both ways and does not mutate its input', () => {
    const ps = syntheticPhotos('x', NOW, 3);
    const copy = [...ps];
    expect(sortPhotos(ps, 'newest').map((p) => p.id)).toEqual([ps[0].id, ps[1].id, ps[2].id]);
    expect(sortPhotos(ps, 'oldest').map((p) => p.id)).toEqual([ps[2].id, ps[1].id, ps[0].id]);
    expect(ps).toEqual(copy);
  });
});

describe('export before delete (A-022, NFR-07) and photo objects in storage', () => {
  const open = async (svc: ReturnType<typeof createFakePlants>) => {
    await mount(svc);
    await openPlant(/^Basil/);
    await screen.findByRole('header', { name: 'Basil' });
    await press('Remove plant');
    await screen.findByRole('header', { name: 'Remove Basil?' });
  };
  const typeName = (name: string) => fireEvent.changeText(screen.getByLabelText('Type the plant name to confirm'), name);
  const deleteBtn = () => screen.getByRole('button', { name: 'Delete plant and all its data' });

  test('a failed export keeps the delete blocked and says so; a retry unlocks it', async () => {
    const svc = createFakePlants({ now: () => NOW, failExport: true });
    await open(svc);
    await press('Export JSON');
    expect(await screen.findByText('The export failed. Nothing was removed. Try again.')).toBeTruthy();
    await typeName('Basil');
    expect(deleteBtn().props.accessibilityState.disabled).toBe(true);
    await fireEvent.press(deleteBtn());
    expect(svc.deleted).toEqual([]);
    expect(screen.getByRole('header', { name: 'Remove Basil?' })).toBeTruthy();
    svc.options.failExport = false;
    await press('Export JSON');
    await screen.findByText(/^Export ready: plant-monitor-export-\S+\.zip \(your data and 15 photos\)\. You can delete now\.$/); // account-wide: Basil 12 + Fern 3
    expect(deleteBtn().props.accessibilityState.disabled).toBe(false);
    expect(svc.exports).toEqual([expect.objectContaining({ format: 'json', photoCount: 15 })]);
  });

  test('CSV export does NOT unlock the delete (no photos inside, A-107); delete after the JSON export removes every returned photo path from storage (NFR-07)', async () => {
    const svc = createFakePlants({ now: () => NOW });
    await open(svc);
    await press('Export CSV');
    await screen.findByText(/CSV lists your photos but does not contain them, so delete stays locked/);
    await typeName('Basil');
    expect(deleteBtn().props.accessibilityState.disabled).toBe(true);
    await fireEvent.press(deleteBtn());
    expect(svc.deleted).toEqual([]);
    await press('Export JSON');
    await screen.findByText(/You can delete now/);
    await press('Delete plant and all its data');
    expect(await screen.findByRole('header', { name: 'Basil was removed' })).toBeTruthy();
    expect(svc.deleted).toEqual(['p-basil']);
    expect(svc.removedObjects).toHaveLength(12);
    expect(svc.removedObjects.every((p) => p.includes('/p-basil/'))).toBe(true);
    expect(svc.exports.map((e) => e.format)).toEqual(['csv', 'json']);
  });

  test('photo cleanup failure keeps the paths on the next screen; Retry removes them', async () => {
    const svc = createFakePlants({ now: () => NOW, failPhotoRemoval: true });
    await open(svc);
    await press('Export JSON');
    await screen.findByText(/You can delete now/);
    await typeName('Basil');
    await press('Delete plant and all its data');
    expect(await screen.findByText('12 photo(s) could not be deleted from storage yet.')).toBeTruthy();
    expect(svc.removedObjects).toEqual([]);
    svc.options.failPhotoRemoval = false;
    await press('Retry photo cleanup');
    expect(svc.removedObjects).toHaveLength(12);
    expect(screen.queryByText('12 photo(s) could not be deleted from storage yet.')).toBeNull();
  });
});

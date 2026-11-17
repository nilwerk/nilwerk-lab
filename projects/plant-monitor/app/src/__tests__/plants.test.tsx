// Plants slice (4.A4 slices 1+2): FR-A06 list + status chips + detail with latest values and 7-day chart, FR-A08/A-022 remove flow (export gate, NFR-07), FR-A02 no cap.
// Against the in-memory PlantsService mock. Not a real backend. Slice 2 cases (gallery, hourly table, boundaries) are in plantsSlice2.test.tsx and hourly.test.ts.
import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { Root } from '../../App';
import { createFakeSetup } from '../provisioning/fakeProvisioning';
import { AuthProvider } from '../auth/AuthContext';
import { createFakeAuth } from '../auth/fakeAuth';
import { PlantsProvider } from '../plants/PlantsContext';
import { createFakePlants, sampleFixture, syntheticHourly } from '../plants/fakePlants';
import { ageParts, plantChips } from '../plants/status';
import { chartSummary } from '../ui/MoistureChart';
import { PlantsError, type HourlyPoint, type PlantSummary } from '../plants/types';
import { hourlyGrid } from '../plants/hourly';
import { colors, statusStyle, type PlantStatus } from '../../theme';
import { contrast } from './contrastUtil';

const FIXED = new Date('2026-11-09T12:30:00Z');
const NOW = new Date();
const base = { deviceId: 'd1', openAlerts: [] as PlantSummary['openAlerts'] };

describe('status chips (unit)', () => {
  test('no open alert = OK; no sensor = No sensor yet', () => {
    expect(plantChips(base)).toEqual(['ok']);
    expect(plantChips({ deviceId: null, openAlerts: [] })).toEqual(['noSensor']);
  });
  test('maps alert kinds to dry / wet / lowBattery / offline', () => {
    expect(plantChips({ ...base, openAlerts: ['too_dry'] })).toEqual(['dry']);
    expect(plantChips({ ...base, openAlerts: ['too_wet'] })).toEqual(['wet']);
    expect(plantChips({ ...base, openAlerts: ['low_battery'] })).toEqual(['lowBattery']);
    expect(plantChips({ ...base, openAlerts: ['device_offline'] })).toEqual(['offline']);
  });
  test('several alerts: all chips, most urgent first, de-duplicated', () => {
    expect(plantChips({ ...base, openAlerts: ['low_battery', 'too_dry', 'device_offline'] })).toEqual(['offline', 'dry', 'lowBattery']);
    expect(plantChips({ ...base, openAlerts: ['too_wet', 'waterlogged'] })).toEqual(['wet']);
  });
  test('sensor faults show Error; an informational event alone is still OK', () => {
    expect(plantChips({ ...base, openAlerts: ['sensor_fault'] })).toEqual(['error']);
    expect(plantChips({ ...base, openAlerts: ['wetting_unexpected'] })).toEqual(['ok']);
  });
  test('age text keys', () => {
    const at = (min: number) => new Date(FIXED.getTime() - min * 60000).toISOString();
    expect(ageParts(null, FIXED)).toEqual({ key: 'plant.updated.never' });
    expect(ageParts(at(0), FIXED).key).toBe('plant.updated.now');
    expect(ageParts(at(14), FIXED)).toEqual({ key: 'plant.updated.min', n: 14 });
    expect(ageParts(at(300), FIXED)).toEqual({ key: 'plant.updated.hours', n: 5 });
    expect(ageParts(at(3000), FIXED)).toEqual({ key: 'plant.updated.days', n: 2 });
  });
});

describe('mock service + chart data (unit)', () => {
  test('synthetic series has exactly 168 hourly points ending at the current hour', () => {
    const h = syntheticHourly(FIXED, 50, 10);
    expect(h).toHaveLength(168);
    expect(h[167].hour).toBe('2026-11-09T12:00:00.000Z');
    expect(h[0].hour).toBe('2026-11-02T13:00:00.000Z');
  });
  test('chart summary skips gaps and reports min/max/last', () => {
    const at = (h: number, v: number | null): HourlyPoint => ({ hour: `2026-11-09T${String(h).padStart(2, '0')}:00:00.000Z`, n: v === null ? null : 4, moistureAvg: v, moistureMin: v, moistureMax: v, tempAvg: null, rhAvg: null, luxAvg: null, vbatMinMv: null });
    const s = chartSummary([at(0, 30), at(1, null), at(2, 50), at(3, null)]);
    expect(s).toEqual({ count: 2, min: 30, max: 50, last: 50 });
    expect(chartSummary([])).toBeNull();
    expect(chartSummary(hourlyGrid([], FIXED))).toBeNull();
  });
  test('fixture covers dry, low battery, offline and no-sensor; delete clears the plant and returns its photo paths; unknown id is not_found', async () => {
    const svc = createFakePlants({ now: () => NOW });
    expect((await svc.listPlants()).map((p) => plantChips(p)[0])).toEqual(['ok', 'dry', 'lowBattery', 'offline', 'noSensor']);
    const r = await svc.deletePlant('p-basil');
    expect(r.photoPaths).toHaveLength(12);
    expect(r.photoPaths.every((x) => x.includes('/p-basil/'))).toBe(true);
    expect(await svc.listPlants()).toHaveLength(4);
    await expect(svc.getPlantDetail('p-basil')).rejects.toBeInstanceOf(PlantsError);
  });
  test('FR-A02 (mock only): 30 plants render in the list (the mock has no cap; the real no-cap check is the 5.6 device test)', async () => {
    const { plants } = sampleFixture(FIXED);
    const many = Array.from({ length: 30 }, (_, i) => ({ ...plants[0], id: `x${i}`, name: `Plant ${i}` }));
    expect(await createFakePlants({ now: () => NOW, plants: many }).listPlants()).toHaveLength(30);
  });
});

describe('AA contrast of the new surfaces (both schemes)', () => {
  const all: PlantStatus[] = ['ok', 'dry', 'wet', 'lowBattery', 'offline', 'error'];
  describe.each(['light', 'dark'] as const)('%s', (s) => {
    const c = colors[s];
    test.each(all)('chip %s: colour on its chip background and on surface >= 4.5', (k) => {
      const st = statusStyle(k, s);
      expect(contrast(st.color, st.background)).toBeGreaterThanOrEqual(4.5);
      expect(contrast(st.color, c.surface)).toBeGreaterThanOrEqual(4.5);
    });
    test('list/detail text pairs on surface and bg >= 4.5; chart bars >= 3 (non-text) on surface', () => {
      for (const fg of [c.ink, c.muted]) for (const bg of [c.surface, c.bg]) expect(contrast(fg, bg)).toBeGreaterThanOrEqual(4.5);
      for (const bar of [c.accent, c.dry, c.wet]) expect(contrast(bar, c.surface)).toBeGreaterThanOrEqual(3);
      expect(contrast(c.accent, c.surface)).toBeGreaterThanOrEqual(4.5); // active tab label
    });
  });
});

const mount = async (plants = createFakePlants({ now: () => NOW })) => {
  const auth = createFakeAuth();
  await auth.signUp('sam@example.com', 'long-enough-1', 'Sam');
  await render(
    <SafeAreaProvider initialMetrics={{ frame: { x: 0, y: 0, width: 390, height: 844 }, insets: { top: 0, left: 0, right: 0, bottom: 0 } }}>
      <AuthProvider service={auth}><PlantsProvider service={plants}><Root contactEmail="x@example.invalid" setup={createFakeSetup().services} /></PlantsProvider></AuthProvider>
    </SafeAreaProvider>,
  );
  await screen.findByRole('header', { name: 'My plants' });
  return plants;
};
const press = async (name: string, role: 'button' | 'tab' = 'button') => fireEvent.press(await screen.findByRole(role, { name }));
const row = (name: RegExp) => screen.findByRole('button', { name });

describe('plant list (S20, FR-A06)', () => {
  test('after sign-in the plants tab is selected and lists all five plants with their chips', async () => {
    await mount();
    expect(screen.getByRole('tab', { name: 'Plants' }).props.accessibilityState.selected).toBe(true);
    expect(await row(/^Basil, Kitchen window, OK, soil moisture 38 %/)).toBeTruthy();
    expect(await row(/^Cactus, Balcony, Too dry, soil moisture 12 %/)).toBeTruthy();
    expect(await row(/^Fern, Bedroom, Low battery/)).toBeTruthy();
    expect(await row(/^Orchid, Living room, Offline/)).toBeTruthy();
    expect(await row(/^Rubber tree, Office, No sensor yet, soil moisture No reading/)).toBeTruthy();
  });
  test('chips carry a text label (not colour alone)', async () => {
    await mount();
    for (const label of ['OK', 'Too dry', 'Low battery', 'Offline', 'No sensor yet']) expect(await screen.findByLabelText(`Status: ${label}`)).toBeTruthy();
  });
  test('empty account shows the empty state', async () => {
    await mount(createFakePlants({ plants: [] }));
    expect(await screen.findByRole('header', { name: 'No plants yet' })).toBeTruthy();
  });
  test('load error shows a message and Try again recovers', async () => {
    const svc = createFakePlants({ now: () => NOW, failList: true });
    await mount(svc);
    expect(await screen.findByText(/Could not load your plants/)).toBeTruthy();
    svc.options.failList = false;
    await press('Try again');
    expect(await row(/^Basil/)).toBeTruthy();
  });
});

describe('plant detail (S21, FR-A06)', () => {
  test('shows latest values equal to the last report, age, thresholds and a 168-point chart', async () => {
    const svc = createFakePlants({ now: () => NOW });
    await mount(svc);
    await fireEvent.press(await row(/^Basil/));
    expect(await screen.findByRole('header', { name: 'Basil' })).toBeTruthy();
    const last = (await svc.getPlantDetail('p-basil')).plant.latest!;
    expect(screen.getByText(`${last.moisturePct} %`)).toBeTruthy();
    expect(screen.getByText('21.4 °C')).toBeTruthy();
    expect(screen.getByText('48 %')).toBeTruthy();
    expect(screen.getByText('1240 lx')).toBeTruthy();
    expect(screen.getByText('3.82 V')).toBeTruthy();
    expect(screen.getByText(/^Updated \d+ (min|h) ago$/)).toBeTruthy();
    expect(screen.getByText('Dry below 25 %, wet above 85 %')).toBeTruthy();
    expect(screen.getAllByTestId('chart-bar')).toHaveLength(168);
    expect(screen.getByTestId('chart-dry-line')).toBeTruthy();
    expect(screen.getByTestId('chart-wet-line')).toBeTruthy();
    expect(screen.getByLabelText(/^Soil moisture, last 7 days, 168 hourly points, lowest \d+ %, highest \d+ %, latest \d+ %$/)).toBeTruthy();
  });
  test('gaps (offline hours) are empty, not zero bars', async () => {
    await mount();
    await fireEvent.press(await row(/^Orchid/));
    await screen.findByRole('header', { name: 'Orchid' });
    expect(screen.getAllByTestId('chart-bar').length).toBe(163);
  });
  test('plant without sensor: dashes instead of values, empty chart text', async () => {
    await mount();
    await fireEvent.press(await row(/^Rubber tree/));
    await screen.findByRole('header', { name: 'Rubber tree' });
    expect(screen.getAllByText('-')).toHaveLength(5);
    expect(screen.getByText('No readings in the last 7 days.')).toBeTruthy();
    expect(screen.getByText('No report from the sensor yet')).toBeTruthy();
  });
  test('Back returns to the list; Profile tab still reachable', async () => {
    await mount();
    await fireEvent.press(await row(/^Basil/));
    await press('Go back');
    expect(await screen.findByRole('header', { name: 'My plants' })).toBeTruthy();
    await press('Profile', 'tab');
    expect(await screen.findByRole('header', { name: 'Profile' })).toBeTruthy();
  });
  test('detail load error is shown with Try again', async () => {
    const svc = createFakePlants({ now: () => NOW });
    await mount(svc);
    svc.options.failList = true;
    await fireEvent.press(await row(/^Basil/));
    expect(await screen.findByText('Could not load this plant. Try again.')).toBeTruthy();
  });
});

describe('remove plant (S24b/S24c, FR-A08, A-022)', () => {
  const open = async (svc = createFakePlants({ now: () => NOW })) => {
    await mount(svc);
    await fireEvent.press(await row(/^Basil/));
    await screen.findByRole('header', { name: 'Basil' });
    await press('Remove plant');
    await screen.findByRole('header', { name: 'Remove Basil?' });
    return svc;
  };
  const exportFirst = async (format: 'JSON' | 'CSV' = 'JSON') => {
    await press(`Export ${format}`);
    await screen.findByText(/^Export ready: plant-monitor-export-\S+\.(json|zip) \(\d+ photos\)\. You can delete now\.$/);
  };
  test('warning names what is deleted; delete stays disabled until export ran AND the exact plant name is typed', async () => {
    await open();
    expect(screen.getByText(/permanently deletes the plant, all its readings, events, alerts, tips and photos/)).toBeTruthy();
    const btn = () => screen.getByRole('button', { name: 'Delete plant and all its data' });
    expect(btn().props.accessibilityState.disabled).toBe(true);
    await fireEvent.changeText(screen.getByLabelText('Type the plant name to confirm'), 'Basil');
    expect(btn().props.accessibilityState.disabled).toBe(true); // name typed, but no export yet
    await exportFirst();
    expect(btn().props.accessibilityState.disabled).toBe(false);
    await fireEvent.changeText(screen.getByLabelText('Type the plant name to confirm'), 'basil');
    expect(btn().props.accessibilityState.disabled).toBe(true);
    await fireEvent.changeText(screen.getByLabelText('Type the plant name to confirm'), 'Basil');
    expect(btn().props.accessibilityState.disabled).toBe(false);
  });
  test('Cancel returns to the plant', async () => {
    const svc = await open();
    await press('Cancel');
    expect(await screen.findByRole('header', { name: 'Basil' })).toBeTruthy();
    expect(svc.deleted).toEqual([]);
  });
  test('delete, then Keep sensor: plant gone from list, sensor not released', async () => {
    const svc = await open();
    await exportFirst();
    await fireEvent.changeText(screen.getByLabelText('Type the plant name to confirm'), 'Basil');
    await press('Delete plant and all its data');
    expect(await screen.findByRole('header', { name: 'Basil was removed' })).toBeTruthy();
    expect(screen.getByText(/Your sensor NW-d4e5f6 is still linked to your account/)).toBeTruthy();
    await press('Keep sensor (set up a new plant later)');
    expect(await screen.findByRole('header', { name: 'My plants' })).toBeTruthy();
    expect(screen.queryByRole('button', { name: /^Basil/ })).toBeNull();
    expect(svc.deleted).toEqual(['p-basil']);
    expect(svc.released).toEqual([]);
  });
  test('delete, then Release sensor calls device-release for that device', async () => {
    const svc = await open();
    await exportFirst('CSV');
    await fireEvent.changeText(screen.getByLabelText('Type the plant name to confirm'), 'Basil');
    await press('Delete plant and all its data');
    await press('Release sensor');
    await waitFor(() => expect(svc.released).toEqual(['d4e5f6']));
    expect(await screen.findByRole('header', { name: 'My plants' })).toBeTruthy();
  });
  test('failed delete keeps the plant and says so; failed release stays on the screen', async () => {
    const svc = await open();
    await exportFirst();
    svc.options.failDelete = true;
    await fireEvent.changeText(screen.getByLabelText('Type the plant name to confirm'), 'Basil');
    await press('Delete plant and all its data');
    expect(await screen.findByText(/Nothing was removed/)).toBeTruthy();
    expect(svc.plants).toHaveLength(5);
    svc.options.failDelete = false; svc.options.failRelease = true;
    await press('Delete plant and all its data');
    await screen.findByRole('header', { name: 'Basil was removed' });
    await press('Release sensor');
    expect(await screen.findByText('The sensor could not be released. Try again.')).toBeTruthy();
    expect(within(screen.root!).queryByRole('header', { name: 'My plants' })).toBeNull();
  });
  test('removing a plant without a sensor offers no release', async () => {
    await mount();
    await fireEvent.press(await row(/^Rubber tree/));
    await screen.findByRole('header', { name: 'Rubber tree' });
    await press('Remove plant');
    await exportFirst();
    await fireEvent.changeText(await screen.findByLabelText('Type the plant name to confirm'), 'Rubber tree');
    await press('Delete plant and all its data');
    expect(await screen.findByText('This plant had no sensor.')).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Release sensor' })).toBeNull();
  });
});

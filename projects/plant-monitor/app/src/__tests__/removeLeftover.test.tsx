// Screen-level leftover handling after a partial photo delete (4.A3b follow-up, review finding on PR #139).
// Requirements: NFR-07 (delete removes readings and photo objects from storage; export before delete), FR-A08 + A-022 (remove plant, sensor stays claimed).
// RemovePlantScreen and PlantRemovedScreen are driven through the real Root with the in-memory plants fake. The fake's
// removePhotoObjects is wrapped so that it fails part-way and reports PlantsError.leftover (the paths still in Storage),
// which is the only way the screens learn which photos to keep. The existing failPhotoRemoval case throws without a leftover,
// so it never exercises this branch; this file does.
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { Root } from '../../App';
import { createFakeSetup } from '../provisioning/fakeProvisioning';
import { AuthProvider } from '../auth/AuthContext';
import { createFakeAuth } from '../auth/fakeAuth';
import { PlantsProvider } from '../plants/PlantsContext';
import { createFakePlants } from '../plants/fakePlants';
import { PlantsError } from '../plants/types';

const NOW = new Date('2026-11-09T12:30:00Z');

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
const press = async (name: string) => fireEvent.press(await screen.findByRole('button', { name }));

describe('remove plant: leftover photo paths are kept and retried exactly (NFR-07, FR-A08, A-022)', () => {
  test('a partial storage delete keeps only the leftover paths; each retry sends only those and the count follows them', async () => {
    const svc = createFakePlants({ now: () => NOW });
    const realRemove = svc.removePhotoObjects;
    const calls: string[][] = [];
    // Call 1 (RemovePlantScreen): 10 of 12 removed, the last 2 still in Storage.
    // Call 2 (retry): one of the 2 removed, the last one still in Storage.
    // Call 3 (second retry): succeeds.
    svc.removePhotoObjects = async (paths: string[]) => {
      calls.push([...paths]);
      if (calls.length === 1) { await realRemove(paths.slice(0, -2)); throw new PlantsError('network', 'partial', paths.slice(-2)); }
      if (calls.length === 2) { await realRemove(paths.slice(0, -1)); throw new PlantsError('network', 'partial', paths.slice(-1)); }
      return realRemove(paths);
    };

    await mount(svc);
    await fireEvent.press(await screen.findByRole('button', { name: /^Basil/ }));
    await screen.findByRole('header', { name: 'Basil' });
    await press('Remove plant');
    await screen.findByRole('header', { name: 'Remove Basil?' });
    await press('Export JSON');
    await screen.findByText(/You can delete now/);
    fireEvent.changeText(screen.getByLabelText('Type the plant name to confirm'), 'Basil');
    await press('Delete plant and all its data');

    // Remove screen -> removed screen: the notice counts the 2 leftover paths, not the 12 photos of the plant.
    expect(await screen.findByRole('header', { name: 'Basil was removed' })).toBeTruthy();
    expect(await screen.findByText('2 photo(s) could not be deleted from storage yet.')).toBeTruthy();
    expect(screen.queryByText('12 photo(s) could not be deleted from storage yet.')).toBeNull();
    expect(calls).toHaveLength(1);
    const all = calls[0];
    expect(all).toHaveLength(12);

    // Retry 1 sends exactly the 2 leftover paths and fails again with 1 leftover: the screen must narrow to that 1 path.
    await press('Retry photo cleanup');
    expect(calls[1]).toEqual(all.slice(-2));
    expect(await screen.findByText('Photo cleanup failed again. Try later.')).toBeTruthy();
    expect(await screen.findByText('1 photo(s) could not be deleted from storage yet.')).toBeTruthy();
    expect(screen.queryByText('2 photo(s) could not be deleted from storage yet.')).toBeNull();

    // Retry 2 sends only that last path and succeeds: the notice goes away and every photo was removed exactly once.
    await press('Retry photo cleanup');
    expect(calls[2]).toEqual(all.slice(-1));
    expect(screen.queryByText(/could not be deleted from storage yet/)).toBeNull();
    expect(svc.removedObjects.slice().sort()).toEqual(all.slice().sort());
  });
});

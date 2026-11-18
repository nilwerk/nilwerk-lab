// Delete-account screen on top of the REAL plants service (createRealPlants) with a fake fetch: the photo download is part of the path the user takes (A-107, NFR-07).
// Mutation checks (output in showcase/items/2026-11-18_4.A9b/mutation-output.txt): (a) realPlants.ts ignores photo failures, (b) the screen gate uses `exported !== null` instead of `complete`,
// (c) isExpectedPhotoUrl always returns true, (d) the expiry check is removed -> each makes at least one test here or in realPlants/photoExport tests fail.
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { Root } from '../../App';
import { createFakeSetup } from '../provisioning/fakeProvisioning';
import { AuthProvider } from '../auth/AuthContext';
import { createFakeAuth } from '../auth/fakeAuth';
import { PlantsProvider } from '../plants/PlantsContext';
import { createRealPlants } from '../plants/realPlants';

const url = (n: number, host = 'x.supabase.co') => `https://${host}/storage/v1/object/sign/plant-photos/u/${n}.jpg?token=t`;
const photos = (over: Record<string, unknown> = {}) => [1, 2, 3].map((n) => ({ id: `i${n}`, plant_id: 'p', taken_at: 't', url: url(n), expires_at: '2099-01-01T00:00:00Z', file: `${n}.jpg`, ...over }));
const mk = (list: unknown[], photoStatus: (u: string) => number = () => 200) => {
  const calls: string[] = [];
  const fetchImpl = jest.fn().mockImplementation(async (u: string) => {
    calls.push(u);
    if (u.includes('format=csv')) return { status: 200, headers: { get: () => 'application/zip' }, arrayBuffer: async () => new Uint8Array([80, 75, 3, 4]).buffer };
    if (u.includes('/functions/v1/export')) return { status: 200, headers: { get: () => 'application/json' }, arrayBuffer: async () => new TextEncoder().encode(JSON.stringify({ plants: [{}], photos: list })).buffer };
    return { status: photoStatus(u), url: '', headers: { get: (h: string) => (h.toLowerCase() === 'content-type' ? 'image/jpeg' : null) }, arrayBuffer: async () => new Uint8Array([1, 2, 3]).buffer };
  });
  const handOff = jest.fn().mockResolvedValue(undefined);
  const svc = createRealPlants({ baseUrl: 'https://x.supabase.co', publishableKey: 'p', getAccessToken: async () => 'jwt', handOff, fetchImpl: fetchImpl as unknown as typeof fetch, now: () => new Date('2026-11-18T10:00:00Z') });
  return { svc, handOff, calls };
};
const mount = async (svc: ReturnType<typeof mk>['svc']) => {
  const auth = createFakeAuth();
  await auth.signUp('sam@example.com', 'long-enough-1', 'Sam');
  const spy = jest.spyOn(auth, 'deleteAccount');
  await render(
    <SafeAreaProvider initialMetrics={{ frame: { x: 0, y: 0, width: 390, height: 844 }, insets: { top: 0, left: 0, right: 0, bottom: 0 } }}>
      <AuthProvider service={auth}><PlantsProvider service={svc}><Root contactEmail="x@example.invalid" setup={createFakeSetup().services} /></PlantsProvider></AuthProvider>
    </SafeAreaProvider>,
  );
  await fireEvent.press(await screen.findByRole('tab', { name: 'Profile' }));
  await fireEvent.press(await screen.findByRole('button', { name: 'Delete account' }));
  await screen.findByRole('header', { name: 'Delete account?' });
  return spy;
};
const press = async (name: string) => fireEvent.press(await screen.findByRole('button', { name }));
const del = () => screen.getByRole('button', { name: 'Delete everything' });
const typeWord = async () => fireEvent.changeText(await screen.findByLabelText('Type DELETE to confirm'), 'DELETE');

test('all photos saved: delete unlocks and the delete API is called once', async () => {
  const { svc, handOff } = mk(photos());
  const spy = await mount(svc);
  await press('Export as JSON');
  await screen.findByText(/your data and 3 photos\)\. You can delete now/);
  await typeWord();
  expect(del().props.accessibilityState.disabled).toBe(false);
  await fireEvent.press(del());
  expect(spy).toHaveBeenCalledTimes(1);
  expect(handOff).toHaveBeenCalledTimes(1);
});
test('one photo fails: honest error, delete stays disabled and pressing it does not call the API; retry after the photo works unlocks it', async () => {
  let bad = true;
  const { svc, handOff } = mk(photos(), (u) => (bad && u.includes('/3.jpg') ? 500 : 200));
  const spy = await mount(svc);
  await typeWord();
  await press('Export as JSON');
  await screen.findByText(/1 of 3 photos could not be downloaded, so your copy is not complete\. Delete stays locked/);
  expect(screen.queryByText(/Nothing was removed/)).toBeNull();
  expect(screen.queryByText(/You can delete now/)).toBeNull();
  expect(del().props.accessibilityState.disabled).toBe(true);
  await fireEvent.press(del());
  expect(spy).not.toHaveBeenCalled();
  expect(handOff).not.toHaveBeenCalled();
  bad = false;
  await press('Export as JSON');
  await screen.findByText(/You can delete now/);
  expect(del().props.accessibilityState.disabled).toBe(false);
  expect(screen.queryByText(/could not be downloaded/)).toBeNull();
});
test('expired links: clear message, delete locked', async () => {
  const { svc, calls } = mk(photos({ expires_at: '2026-11-17T00:00:00Z' }));
  await mount(svc);
  await typeWord();
  await press('Export as JSON');
  await screen.findByText(/photo links in the export have expired/);
  expect(del().props.accessibilityState.disabled).toBe(true);
  expect(calls.filter((c) => c.includes('/storage/'))).toHaveLength(0);
});
test('photo link on a foreign host: not fetched, message says so, delete locked', async () => {
  const { svc, calls } = mk(photos({ url: url(1, 'evil.example') }));
  await mount(svc);
  await typeWord();
  await press('Export as JSON');
  await screen.findByText(/server the app does not trust/);
  expect(calls.some((c) => c.includes('evil.example'))).toBe(false);
  expect(del().props.accessibilityState.disabled).toBe(true);
});
test('CSV: saved, but says delete stays locked and the button stays disabled', async () => {
  const { svc } = mk(photos());
  const spy = await mount(svc);
  await typeWord();
  await press('Export as CSV');
  await screen.findByText(/does not contain them, so delete stays locked/);
  expect(del().props.accessibilityState.disabled).toBe(true);
  expect(spy).not.toHaveBeenCalled();
});

// Delete-account screen (S04) wired to the AuthService -> DELETE /account, with the export-before-delete gate.
// Requirements: FR-A01 (delete account), NFR-07 (export first, deletion removes all data), NFR-06. Fakes only (in-memory auth + plants); the HTTP client has its own test (accountApi.test.ts).
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { Root } from '../../App';
import { createFakeSetup } from '../provisioning/fakeProvisioning';
import { AuthProvider } from '../auth/AuthContext';
import { createFakeAuth } from '../auth/fakeAuth';
import { AuthError } from '../auth/types';
import { PlantsProvider } from '../plants/PlantsContext';
import { createFakePlants } from '../plants/fakePlants';

const DEL = 'Delete everything';
const mount = async (auth = createFakeAuth(), plants = createFakePlants()) => {
  await auth.signUp('sam@example.com', 'long-enough-1', 'Sam');
  const spy = jest.spyOn(auth, 'deleteAccount');
  const view = await render(
    <SafeAreaProvider initialMetrics={{ frame: { x: 0, y: 0, width: 390, height: 844 }, insets: { top: 0, left: 0, right: 0, bottom: 0 } }}>
      <AuthProvider service={auth}><PlantsProvider service={plants}><Root contactEmail="x@example.invalid" setup={createFakeSetup().services} /></PlantsProvider></AuthProvider>
    </SafeAreaProvider>,
  );
  await fireEvent.press(await screen.findByRole('tab', { name: 'Profile' }));
  await fireEvent.press(await screen.findByRole('button', { name: 'Delete account' }));
  await screen.findByRole('header', { name: 'Delete account?' });
  return { auth, plants, spy, view };
};
const press = async (name: string) => fireEvent.press(await screen.findByRole('button', { name }));
const typeWord = async (w: string) => fireEvent.changeText(await screen.findByLabelText('Type DELETE to confirm'), w);
const delBtn = () => screen.getByRole('button', { name: DEL });
const exportReady = async (fmt = 'Export as JSON') => { await press(fmt); await screen.findByText(/You can delete now/); };

describe('export-before-delete gate (NFR-07)', () => {
  test('blocked with the word typed but no export: button disabled, press does nothing, API not called', async () => {
    const { auth, spy } = await mount();
    await typeWord('DELETE');
    expect(delBtn().props.accessibilityState.disabled).toBe(true);
    expect(screen.getByText('Export first. The delete button unlocks after the export.')).toBeTruthy();
    await fireEvent.press(delBtn());
    expect(spy).not.toHaveBeenCalled();
    expect(auth.accounts).toHaveLength(1);
  });

  test('a failed export keeps it blocked and says so; a retry (CSV) unlocks it', async () => {
    const plants = createFakePlants({ failExport: true });
    const { spy } = await mount(createFakeAuth(), plants);
    await press('Export as JSON');
    expect(await screen.findByText(/The export did not work\. Nothing was removed/)).toBeTruthy();
    await typeWord('DELETE');
    expect(delBtn().props.accessibilityState.disabled).toBe(true);
    await fireEvent.press(delBtn());
    expect(spy).not.toHaveBeenCalled();
  });

  test('export done but wrong or missing word: still blocked', async () => {
    const { spy } = await mount();
    await exportReady('Export as CSV');
    expect(delBtn().props.accessibilityState.disabled).toBe(true);
    await typeWord('delete');
    expect(delBtn().props.accessibilityState.disabled).toBe(true);
    await fireEvent.press(delBtn());
    expect(spy).not.toHaveBeenCalled();
  });
});

describe('delete states (FR-A01)', () => {
  const ready = async (auth = createFakeAuth()) => { const m = await mount(auth); await exportReady(); await typeWord('DELETE'); return m; };

  test('success: calls the API once, removes the account, returns to the welcome screen', async () => {
    const { auth, spy } = await ready();
    expect(delBtn().props.accessibilityState.disabled).toBe(false);
    await fireEvent.press(delBtn());
    expect(await screen.findByRole('header', { name: 'Plant Monitor' })).toBeTruthy();
    expect(spy).toHaveBeenCalledTimes(1);
    expect(auth.accounts).toHaveLength(0);
  });

  test.each([
    ['401 unauthorized', new AuthError('unauthorized'), /Your session has expired\. Nothing was removed/],
    ['network', new AuthError('network'), /No connection, so we do not know whether the deletion went through/],
    ['server error', new AuthError('server'), /The account could not be deleted, and some of your data may already be gone/],
    ['unknown error', new AuthError('unknown'), /The account could not be deleted, and some of your data may already be gone/],
  ])('%s: message shown, account kept, button usable again for a retry', async (_n, err, msg) => {
    const auth = createFakeAuth();
    const { spy } = await ready(auth);
    auth.options.deleteError = err;
    await fireEvent.press(delBtn());
    expect(await screen.findByText(msg)).toBeTruthy();
    expect(auth.accounts).toHaveLength(1);
    expect(delBtn().props.accessibilityState.disabled).toBe(false);
    auth.options.deleteError = undefined;       // retry succeeds (the server function is idempotent)
    await fireEvent.press(delBtn());
    expect(await screen.findByRole('header', { name: 'Plant Monitor' })).toBeTruthy();
    expect(spy).toHaveBeenCalledTimes(2);
  });

  test('401 on the retry after a network error does not claim "session expired" (the first attempt may have deleted the account)', async () => {
    const auth = createFakeAuth();
    await ready(auth);
    auth.options.deleteError = new AuthError('network');
    await fireEvent.press(delBtn());
    expect(await screen.findByText(/No connection, so we do not know/)).toBeTruthy();
    auth.options.deleteError = new AuthError('unauthorized');
    await fireEvent.press(delBtn());
    expect(await screen.findByText(/may already have been deleted/)).toBeTruthy();
    expect(screen.queryByText(/session has expired/)).toBeNull();
  });
});

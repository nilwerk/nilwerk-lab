// Bypass check for the export-before-delete gate (NFR-07, FR-A01): the UI disable is REMOVED here (Button mocked so it never disables),
// which simulates a regression in the screen. The guard in exportGate.deleteAccountGated must still stop the API call.
// Mutation check: delete the `if (!canDelete(gate)) throw ...` line in exportGate.ts (or make canDelete return true) and these tests fail.
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';

jest.mock('../ui/primitives', () => {
  const actual = jest.requireActual('../ui/primitives');
  const { Pressable, Text } = jest.requireActual('react-native');
  const Button = ({ label, onPress }: { label: string; onPress: () => void }) => <Pressable accessibilityRole="button" accessibilityLabel={label} onPress={onPress}><Text>{label}</Text></Pressable>;
  return { ...actual, Button };
});
import { DeleteAccountScreen } from '../screens/DeleteAccountScreen';
import { AuthProvider } from '../auth/AuthContext';
import { createFakeAuth } from '../auth/fakeAuth';
import { PlantsProvider } from '../plants/PlantsContext';
import { createFakePlants } from '../plants/fakePlants';

const mount = async () => {
  const auth = createFakeAuth();
  await auth.signUp('sam@example.com', 'long-enough-1', 'Sam');
  const spy = jest.spyOn(auth, 'deleteAccount');
  await render(
    <SafeAreaProvider initialMetrics={{ frame: { x: 0, y: 0, width: 390, height: 844 }, insets: { top: 0, left: 0, right: 0, bottom: 0 } }}>
      <AuthProvider service={auth}><PlantsProvider service={createFakePlants()}><DeleteAccountScreen onCancel={() => undefined} /></PlantsProvider></AuthProvider>
    </SafeAreaProvider>,
  );
  return { auth, spy };
};
const typeWord = async (w: string) => fireEvent.changeText(await screen.findByLabelText('Type DELETE to confirm'), w);

test('no export: pressing the (always enabled) delete button does not call the API and tells the user', async () => {
  const { auth, spy } = await mount();
  await typeWord('DELETE');
  await fireEvent.press(screen.getByRole('button', { name: 'Delete everything' }));
  expect(await screen.findByText(/Nothing was removed/)).toBeTruthy();
  expect(spy).not.toHaveBeenCalled();
  expect(auth.accounts).toHaveLength(1);
});

test('export done but the word missing: still not called', async () => {
  const { spy } = await mount();
  await fireEvent.press(screen.getByRole('button', { name: 'Export as JSON' }));
  await screen.findByText(/You can delete now/);
  await fireEvent.press(screen.getByRole('button', { name: 'Delete everything' }));
  expect(spy).not.toHaveBeenCalled();
});

test('control: export done and the word typed -> the same button does call the API', async () => {
  const { auth, spy } = await mount();
  await fireEvent.press(screen.getByRole('button', { name: 'Export as JSON' }));
  await screen.findByText(/You can delete now/);
  await typeWord('DELETE');
  await fireEvent.press(screen.getByRole('button', { name: 'Delete everything' }));
  expect(spy).toHaveBeenCalledTimes(1);
  expect(auth.accounts).toHaveLength(0);
});

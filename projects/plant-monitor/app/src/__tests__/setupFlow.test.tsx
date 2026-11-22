// Device setup flow against the fake ProvisioningService (4.A3, FR-A03 / FR-D03 / FR-A04 / FR-A05 / NFR-03). No Bluetooth, no backend.
import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { SetupFlow } from '../screens/setup/SetupFlow';
import { createFakeSetup, FAKE_LABEL, FAKE_SENSOR, FAKE_WIFI, unavailableProvisioning } from '../provisioning/fakeProvisioning';

const metrics = { frame: { x: 0, y: 0, width: 390, height: 844 }, insets: { top: 0, left: 0, right: 0, bottom: 0 } };
let clock = 0;
const mount = async (fake = createFakeSetup(), onExit = jest.fn()) => {
  clock = 0;
  await render(<SafeAreaProvider initialMetrics={metrics}><SetupFlow services={fake.services} onExit={onExit} now={() => clock} /></SafeAreaProvider>);
  return { fake, onExit };
};
const type = async (label: string, text: string) => fireEvent.changeText(await screen.findByLabelText(label), text);
const tap = async (label: string | RegExp) => fireEvent.press(await screen.findByRole('button', { name: label }));
const choose = async (label: string | RegExp) => fireEvent.press(await screen.findByRole('radio', { name: label }));
const header = (name: string) => screen.findByRole('header', { name });

async function toWifi() {
  await tap('Find my sensor');
  await tap(/^Sensor NW-d4e5f6/);
  await type('Sensor code (from the label)', FAKE_LABEL);
  await tap('Connect');
  await header('Choose your Wi-Fi');
}
async function toName(password = FAKE_WIFI.password) {
  await toWifi();
  await choose(/^HomeNet-2G/);
  await type('Wi-Fi password', password);
  await tap('Continue');
  await header('Name your sensor');
}
async function toPhoto() {
  await toName();
  await type('Sensor name', 'Basil on the sill');
  await tap('Connect sensor');
  await header('Take a photo');
}
const fillDetails = async () => {
  await type('Plant name', 'Basil');
  await choose('Balcony');
  await type('Room or area', 'Kitchen window');
  await choose('Garden soil');
  await type('City', 'Berlin');
};

describe('device setup flow', () => {
  test('happy path: scan, connect, Wi-Fi, name, photo, details, done (no hub step, A-023)', async () => {
    const { fake } = await mount();
    expect(await header('Add a sensor')).toBeTruthy();
    expect(screen.queryByText(/hub/i)).toBeNull();
    await toPhoto();
    expect(fake.prov.state.provisioned).toEqual([{ hwId: FAKE_SENSOR.hwId, ssid: 'HomeNet-2G', name: 'Basil on the sill' }]);
    clock = 161000;
    await tap('Take photo');
    await header('About your plant');
    await fillDetails();
    await tap('Save plant');
    expect(await header('All set!')).toBeTruthy();
    expect(fake.plants.created).toEqual([{ deviceId: 'device-1', photoUri: 'file:///fake/basil.jpg', details: { name: 'Basil', location: 'balcony', area: 'Kitchen window', soil: 'garden', species: '', city: 'Berlin' } }]);
    expect(await screen.findByText(/Basil is connected/)).toBeTruthy();
    expect(await screen.findByText('Setup time 2:41 (target: 3 minutes or less)')).toBeTruthy();
    expect(screen.queryByText(/hub/i)).toBeNull();
  }, 15000); // Full 5-step flow with many async UI steps; under parallel CI load it exceeded Jest's 5000 ms default (flaky, seen on main). Only this test gets the longer budget.

  test('photo can be skipped; plant is saved without it', async () => {
    const { fake } = await mount();
    await toPhoto();
    await tap('Skip for now');
    await fillDetails();
    await tap('Save plant');
    await header('All set!');
    expect(fake.plants.created[0].photoUri).toBeNull();
    expect(fake.photos.calls).toEqual([]);
  });

  test('cancelled camera stays on the photo step with a plain note', async () => {
    const fake = createFakeSetup();
    fake.photos.takePhoto = async () => null;
    await mount(fake);
    await toPhoto();
    await tap('Take photo');
    expect(await screen.findByText('No photo was chosen.')).toBeTruthy();
    expect(screen.getByRole('header', { name: 'Take a photo' })).toBeTruthy();
  });

  test('progress and timer are announced on each step', async () => {
    await mount();
    expect(screen.getByLabelText('Step 1 of 5. Time so far 0:00.')).toBeTruthy();
    clock = 25000;
    await toWifi();
    expect(await screen.findByLabelText(/^Step 2 of 5\. Time so far 0:2\d\.$/)).toBeTruthy();
  });

  test('no sensor found: plain advice, can try again', async () => {
    await mount(createFakeSetup({ sensors: [] }));
    await tap('Find my sensor');
    expect(await screen.findByText(/No sensor found/)).toBeTruthy();
  });

  test('Bluetooth permission refused and no-BLE build show plain messages', async () => {
    await mount(createFakeSetup({ failScan: 'permission_denied' }));
    await tap('Find my sensor');
    expect(await screen.findByText(/Bluetooth is not allowed/)).toBeTruthy();
  });
  test('build without BLE (unavailable service) says so', async () => {
    const fake = createFakeSetup();
    fake.services.provisioning = unavailableProvisioning();
    await mount(fake);
    await tap('Find my sensor');
    expect(await screen.findByText(/needs the full app build/)).toBeTruthy();
  });

  test('wrong code: error, then correct code works; a code of another sensor is refused locally', async () => {
    await mount();
    await tap('Find my sensor');
    await tap(/^Sensor NW-d4e5f6/);
    await type('Sensor code (from the label)', 'hello');
    await tap('Connect');
    expect(await screen.findByText(/does not look like a sensor code/)).toBeTruthy();
    await type('Sensor code (from the label)', 'NW1:nw-000000aaaaaa:7KQ2M9XD');
    await tap('Connect');
    expect(await screen.findByText(/belongs to a different sensor than NW-d4e5f6/)).toBeTruthy();
    await type('Sensor code (from the label)', 'NW1:nw-a1b2c3d4e5f6:AAAAAAAA');
    await tap('Connect');
    expect(await screen.findByText(/Code doesn't match/)).toBeTruthy();
    await type('Sensor code (from the label)', FAKE_LABEL);
    await tap('Connect');
    await header('Choose your Wi-Fi');
  });

  test('5 wrong codes close setup mode and say to press the button again', async () => {
    await mount();
    await tap('Find my sensor');
    await tap(/^Sensor NW-d4e5f6/);
    for (let i = 0; i < 5; i++) { await type('Sensor code (from the label)', 'NW1:nw-a1b2c3d4e5f6:AAAAAAAA'); await tap('Connect'); }
    expect(await screen.findByText(/Setup mode closed/)).toBeTruthy();
  });

  test('Wi-Fi step validates the password; open network needs none; other network needs a name', async () => {
    await mount();
    await toWifi();
    await tap('Continue');
    expect(await screen.findByText('Enter the Wi-Fi password.')).toBeTruthy();
    expect(screen.getByText('Only 2.4 GHz networks work. The password goes straight to the sensor, never to our cloud.')).toBeTruthy();
    await choose('Other network...');
    await tap('Continue');
    expect(await screen.findByText('Enter the network name.')).toBeTruthy();
  });

  test('Wi-Fi step rejects a 7-character password (WPA2 needs 8-63, PR #56 C2)', async () => {
    await mount();
    await toWifi();
    await type('Wi-Fi password', 'x'.repeat(7));
    await tap('Continue');
    expect(await screen.findByText('A Wi-Fi password has 8 to 63 characters.')).toBeTruthy();
  });

  test('the sensor name is validated and sent trimmed (4.F2: firmware refuses control characters)', async () => {
    const { fake } = await mount();
    await toName();
    await type('Sensor name', '  Kitchen\n');
    await tap('Connect sensor');
    await header('Take a photo');
    expect(fake.prov.state.provisioned.map((p) => p.name)).toEqual(['Kitchen']);
  });

  test('wrong Wi-Fi password: error screen, re-enter keeps the network, then succeeds', async () => {
    await mount();
    await toName('wrong-password');
    await type('Sensor name', 'Basil');
    await tap('Connect sensor');
    expect(await header("Wi-Fi didn't work")).toBeTruthy();
    expect(screen.getByText("The sensor couldn't join HomeNet-2G. Wrong password?")).toBeTruthy();
    await tap('Re-enter password');
    await header('Choose your Wi-Fi');
    expect((await screen.findByRole('radio', { name: /^HomeNet-2G/ })).props.accessibilityState.selected).toBe(true);
    await type('Wi-Fi password', FAKE_WIFI.password);
    await tap('Continue');
    await type('Sensor name', 'Basil');
    await tap('Connect sensor');
    await header('Take a photo');
  });

  test('sensor owned by someone else: message, reset how-to, start over', async () => {
    await mount(createFakeSetup({ sensors: [{ ...FAKE_SENSOR, owned: true }] }));
    await toName();
    await type('Sensor name', 'Basil');
    await tap('Connect sensor');
    expect(await header('Sensor already belongs to someone')).toBeTruthy();
    await tap('How to reset');
    expect(await screen.findByText(/Press the pinhole button on the sensor until the LED blinks/)).toBeTruthy();
    await tap('Start over');
    expect(await header('Add a sensor')).toBeTruthy();
  });

  test('network failure while claiming can be retried', async () => {
    await mount(createFakeSetup({ claimFailsOnce: 'claim_network' }));
    await toName();
    await type('Sensor name', 'Basil');
    await tap('Connect sensor');
    expect(await header('Linking to your account failed')).toBeTruthy();
    await tap('Try again');
    await header('Take a photo');
  });

  test('plant details: required fields are validated, a failed save says the sensor is not linked to the plant and can be retried', async () => {
    const { fake } = await mount();
    await toPhoto();
    await tap('Skip for now');
    await tap('Save plant');
    expect(await screen.findByText('Enter the plant name.')).toBeTruthy();
    expect(screen.getByText('Enter a room or area.')).toBeTruthy();
    expect(screen.getByText('Enter a city.')).toBeTruthy();
    expect(fake.plants.created).toHaveLength(0);
    await fillDetails();
    fake.plants.options.failNext = true;
    await tap('Save plant');
    expect(await screen.findByText(/The plant could not be saved, so your sensor is not linked to it/)).toBeTruthy();
    await tap('Save plant');
    await header('All set!');
  });

  test('a sensor that already has a plant is not moved silently: the user chooses keep (leave, nothing saved) or move', async () => {
    const { fake, onExit } = await mount();
    fake.plants.options.linked = true;
    await toPhoto();
    await tap('Skip for now');
    await fillDetails();
    await tap('Save plant');
    expect(await header('This sensor already has a plant')).toBeTruthy();
    expect(fake.plants.created).toHaveLength(0);
    await tap('Keep the sensor on its current plant');
    expect(onExit).toHaveBeenCalled();
    expect(fake.plants.created).toHaveLength(0);
  });

  test('a sensor that already has a plant: choosing move saves the plant and moves the link', async () => {
    const { fake } = await mount();
    fake.plants.options.linked = true;
    await toPhoto();
    await tap('Skip for now');
    await fillDetails();
    await tap('Save plant');
    await header('This sensor already has a plant');
    await tap('Move the sensor to the new plant');
    await header('All set!');
    expect(fake.plants.created).toHaveLength(1);
    expect(fake.plants.moved).toEqual(['device-1']);
  });

  test('add another sensor restarts at step 1; cancel exits and disconnects', async () => {
    const { onExit } = await mount();
    await toPhoto();
    await tap('Skip for now');
    await fillDetails();
    await tap('Save plant');
    await tap('Add another sensor');
    expect(await header('Add a sensor')).toBeTruthy();
    await tap('Go back');
    expect(onExit).toHaveBeenCalled();
  });
});

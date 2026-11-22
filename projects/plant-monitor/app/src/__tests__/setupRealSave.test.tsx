// Device setup screens driven into the REAL plant save (4.A4c): SetupFlow -> createRealPlantSetup -> fake fetch. Photo step offers only Skip.
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { SetupFlow } from '../screens/setup/SetupFlow';
import { createFakeSetup, FAKE_LABEL, FAKE_SENSOR, FAKE_WIFI } from '../provisioning/fakeProvisioning';
import { createRealPlantSetup, noPhotoSource } from '../provisioning/realPlantSetup';
import type { SetupServices } from '../provisioning/types';

const metrics = { frame: { x: 0, y: 0, width: 390, height: 844 }, insets: { top: 0, left: 0, right: 0, bottom: 0 } };
const BASE = 'https://proj.example.test';
const USER = '11111111-1111-4111-8111-111111111111';
const DEVICE = '22222222-2222-4222-8222-222222222222';
const PLANT = '33333333-3333-4333-8333-333333333333';
const UNSAVED = 'The plant could not be saved, so your sensor is not linked to it. Please try again.';

const res = (status: number, body: unknown) => ({ status, json: async () => body }) as unknown as Response;

/** fake sensor link that answers with a uuid device id, as the real claim does (the fake's own id is not a uuid) */
function servicesWith(patchAnswer: () => Response) {
  const fake = createFakeSetup();
  const provisioning = { ...fake.services.provisioning, provision: async (req: Parameters<typeof fake.services.provisioning.provision>[0], on: Parameters<typeof fake.services.provisioning.provision>[1]) => {
    await fake.services.provisioning.provision(req, on);
    return { deviceId: DEVICE, hwId: FAKE_SENSOR.hwId };
  } };
  const fetchImpl = jest.fn(async (url: string, init: RequestInit) => {
    if (init.method === 'POST' && url.endsWith('/rest/v1/plants')) return res(201, [{ id: PLANT }]);
    if (init.method === 'PATCH' && url.includes('/rest/v1/devices')) return patchAnswer();
    if (init.method === 'DELETE') return res(204, null);
    throw new Error(`unexpected ${init.method} ${url}`);
  });
  const plants = createRealPlantSetup({ baseUrl: BASE, publishableKey: 'k', getAccessToken: async () => 'jwt', getUserId: async () => USER, fetchImpl: fetchImpl as unknown as typeof fetch });
  const services: SetupServices = { provisioning, plants, photos: noPhotoSource };
  return { services, fetchImpl };
}

const mount = async (services: SetupServices) => {
  await render(<SafeAreaProvider initialMetrics={metrics}><SetupFlow services={services} onExit={jest.fn()} now={() => 0} /></SafeAreaProvider>);
};
const type = async (label: string, text: string) => fireEvent.changeText(await screen.findByLabelText(label), text);
const tap = async (label: string | RegExp) => fireEvent.press(await screen.findByRole('button', { name: label }));
const choose = async (label: string | RegExp) => fireEvent.press(await screen.findByRole('radio', { name: label }));
const header = (name: string) => screen.findByRole('header', { name });

async function toPhoto() {
  await tap('Find my sensor');
  await tap(/^Sensor NW-d4e5f6/);
  await type('Sensor code (from the label)', FAKE_LABEL);
  await tap('Connect');
  await header('Choose your Wi-Fi');
  await choose(/^HomeNet-2G/);
  await type('Wi-Fi password', FAKE_WIFI.password);
  await tap('Continue');
  await header('Name your sensor');
  await type('Sensor name', 'Basil on the sill');
  await tap('Connect sensor');
  await header('Take a photo');
}
async function fillAndSave() {
  await type('Plant name', 'Basil');
  await choose('Balcony');
  await type('Room or area', 'Kitchen window');
  await choose('Garden soil');
  await type('City', 'Berlin');
  await tap('Save plant');
}

describe('setup save in the real build', () => {
  test('photo step offers only Skip and says why; the saved plant is written to the cloud and linked to the sensor', async () => {
    const { services, fetchImpl } = servicesWith(() => res(200, [{ id: DEVICE, plant_id: PLANT }]));
    await mount(services);
    await toPhoto();
    expect(screen.queryByRole('button', { name: 'Take photo' })).toBeNull();
    expect(screen.queryByRole('button', { name: 'Choose from library' })).toBeNull();
    expect(await screen.findByText('Photos are not available in this version yet. The plant is saved without one.')).toBeTruthy();
    await tap('Skip for now');
    await header('About your plant');
    await fillAndSave();
    expect(await header('All set!')).toBeTruthy();
    const ins = fetchImpl.mock.calls[0] as unknown as [string, RequestInit];
    expect(JSON.parse(String(ins[1].body))).toMatchObject({ owner_id: USER, name: 'Basil', location_type: 'balcony', soil_type: 'garden', city: 'Berlin' });
    const link = fetchImpl.mock.calls[1] as unknown as [string, RequestInit];
    expect(link[0]).toBe(`${BASE}/rest/v1/devices?id=eq.${DEVICE}`);
    expect(JSON.parse(String(link[1].body))).toEqual({ plant_id: PLANT });
  });

  test('when the sensor link is not visible, the screen says the plant was not saved (no "All set!")', async () => {
    const { services } = servicesWith(() => res(200, []));
    await mount(services);
    await toPhoto();
    await tap('Skip for now');
    await header('About your plant');
    await fillAndSave();
    expect(await screen.findByText(UNSAVED)).toBeTruthy();
    expect(screen.queryByRole('header', { name: 'All set!' })).toBeNull();
    await waitFor(() => expect(screen.getByRole('button', { name: 'Save plant' })).toBeTruthy());
  });
});

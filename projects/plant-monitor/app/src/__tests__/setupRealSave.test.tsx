// Device setup screens driven into the REAL plant save (4.A4c): SetupFlow -> createRealPlantSetup -> fake fetch. Photo step offers only Skip.
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react-native';
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
const UNSAVED = 'The save could not be confirmed. Check your plant list before you try again.';
const MOVE = 'Move the sensor to the new plant';

const res = (status: number, body: unknown) => ({ status, json: async () => body }) as unknown as Response;
const OTHER = '44444444-4444-4444-8444-444444444444';

/** the fake sensor link returns a uuid device id, as the real claim does; the plant service talks to a fake fetch.
 *  devicePlant: what GET devices shows before any save ('hidden' = RLS hides the device).
 *  rpc: answer of create_plant_and_link_device. commitThenLose: the RPC commits on the server, but its answer is lost (network error);
 *  after that, GET devices shows postPlant (the plant the sensor is now on). */
function servicesWith(opts: { devicePlant?: string | null | 'hidden'; rpc?: () => Response; commitThenLose?: boolean; postPlant?: string | null }) {
  const fake = createFakeSetup();
  const provisioning = { ...fake.services.provisioning, provision: async (req: Parameters<typeof fake.services.provisioning.provision>[0], on: Parameters<typeof fake.services.provisioning.provision>[1]) => {
    await fake.services.provisioning.provision(req, on);
    return { deviceId: DEVICE, hwId: FAKE_SENSOR.hwId };
  } };
  let committed = false;
  const rpcCalls: RequestInit[] = [];
  const fetchImpl = jest.fn(async (url: string, init: RequestInit) => {
    if ((init.method ?? 'GET') === 'GET' && url.includes('/rest/v1/devices')) {
      if (committed) return res(200, [{ plant_id: opts.postPlant ?? null }]);
      return opts.devicePlant === 'hidden' ? res(200, []) : res(200, [{ plant_id: opts.devicePlant ?? null }]);
    }
    if (init.method === 'POST' && url.endsWith('/rest/v1/rpc/create_plant_and_link_device')) {
      rpcCalls.push(init);
      if (opts.commitThenLose) { committed = true; throw new TypeError('response lost after commit'); }
      const answer = opts.rpc ? opts.rpc() : res(200, PLANT);
      committed = answer.status === 200;
      return answer;
    }
    throw new Error(`unexpected ${init.method} ${url}`);
  });
  const plants = createRealPlantSetup({ baseUrl: BASE, publishableKey: 'k', getAccessToken: async () => 'jwt', getUserId: async () => USER, fetchImpl: fetchImpl as unknown as typeof fetch });
  const services: SetupServices = { provisioning, plants, photos: noPhotoSource };
  return { services, fetchImpl, rpcCalls };
}

const mount = async (services: SetupServices) => {
  const onExit = jest.fn();
  await render(<SafeAreaProvider initialMetrics={metrics}><SetupFlow services={services} onExit={onExit} now={() => 0} /></SafeAreaProvider>);
  return { onExit };
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
  test('photo step offers only Skip and says why; the plant is saved in one call and linked to the sensor', async () => {
    const { services, fetchImpl } = servicesWith({ devicePlant: null });
    await mount(services);
    await toPhoto();
    expect(screen.queryByRole('button', { name: 'Take photo' })).toBeNull();
    expect(screen.queryByRole('button', { name: 'Choose from library' })).toBeNull();
    expect(await screen.findByText('Photos are not available in this version yet. The plant is saved without one.')).toBeTruthy();
    await tap('Skip for now');
    await header('About your plant');
    await fillAndSave();
    expect(await header('All set!')).toBeTruthy();
    const rpc = fetchImpl.mock.calls.find((c) => String(c[0]).endsWith('/rpc/create_plant_and_link_device')) as unknown as [string, RequestInit];
    expect(JSON.parse(String(rpc[1].body))).toMatchObject({ p_device: DEVICE, p_name: 'Basil', p_location_type: 'balcony', p_soil_type: 'garden', p_city: 'Berlin', p_move: false });
    expect(fetchImpl.mock.calls.some((c) => (c[1] as RequestInit).method === 'PATCH')).toBe(false);
  });

  test('when the sensor is not visible, the screen says the save could not be confirmed (no "All set!", no retry)', async () => {
    const { services, rpcCalls } = servicesWith({ devicePlant: 'hidden' });
    await mount(services);
    await toPhoto();
    await tap('Skip for now');
    await header('About your plant');
    await fillAndSave();
    expect(await header('The save could not be confirmed')).toBeTruthy();
    expect(screen.queryByRole('header', { name: 'All set!' })).toBeNull();
    expect(rpcCalls).toHaveLength(0);
  });

  test('the RPC fails: the screen says the plant was not saved, and no plant is left behind (one statement)', async () => {
    const { services, fetchImpl } = servicesWith({ devicePlant: null, rpc: () => res(403, { code: '42501' }) });
    await mount(services);
    await toPhoto();
    await tap('Skip for now');
    await header('About your plant');
    await fillAndSave();
    expect(await screen.findByText(UNSAVED)).toBeTruthy();
    expect(fetchImpl.mock.calls.filter((c) => (c[1] as RequestInit).method === 'POST')).toHaveLength(1);
    expect(screen.getByRole('button', { name: 'Save plant' })).toBeTruthy();   // not on a plant: a plain retry is allowed
  });

  test('the save committed but its answer was lost: the re-read shows the sensor on a plant, so no retry is offered', async () => {
    const { services, rpcCalls } = servicesWith({ devicePlant: null, commitThenLose: true, postPlant: PLANT });
    await mount(services);
    await toPhoto();
    await tap('Skip for now');
    await header('About your plant');
    await fillAndSave();
    expect(await header('Your sensor is already on a plant')).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Save plant' })).toBeNull();
    expect(screen.queryByRole('button', { name: MOVE })).toBeNull();
    expect(rpcCalls).toHaveLength(1);
  });

  test('exact sequence: Move commits, its answer is lost, the re-read shows the sensor on the new plant: keep only, p_move is never sent again', async () => {
    const { services, rpcCalls } = servicesWith({ devicePlant: OTHER, commitThenLose: true, postPlant: PLANT });
    const { onExit } = await mount(services);
    await toPhoto();
    await tap('Skip for now');
    await header('About your plant');
    await fillAndSave();
    await header('This sensor already has a plant');
    await tap(MOVE);
    expect(await header('Your sensor is already on a plant')).toBeTruthy();
    expect(screen.queryByRole('button', { name: MOVE })).toBeNull();
    expect(screen.queryByRole('button', { name: 'Keep the sensor on its current plant' })).toBeNull();
    expect(rpcCalls).toHaveLength(1);
    expect(JSON.parse(String(rpcCalls[0].body))).toMatchObject({ p_move: true });
    await tap('Go to my plants');
    expect(onExit).toHaveBeenCalled();
    expect(rpcCalls).toHaveLength(1);
  });

  test('sensor already on a plant: the user is asked, nothing is written, and "keep" leaves without saving', async () => {
    const { services, fetchImpl } = servicesWith({ devicePlant: OTHER });
    const { onExit } = await mount(services);
    await toPhoto();
    await tap('Skip for now');
    await header('About your plant');
    await fillAndSave();
    expect(await header('This sensor already has a plant')).toBeTruthy();
    expect(fetchImpl.mock.calls.some((c) => (c[1] as RequestInit).method === 'POST')).toBe(false);
    await tap('Keep the sensor on its current plant');
    expect(onExit).toHaveBeenCalled();
    expect(fetchImpl.mock.calls.some((c) => (c[1] as RequestInit).method === 'POST')).toBe(false);
  });

  test('sensor already on a plant: "move" saves the new plant and moves the link (p_move true)', async () => {
    const { services, fetchImpl } = servicesWith({ devicePlant: OTHER });
    await mount(services);
    await toPhoto();
    await tap('Skip for now');
    await header('About your plant');
    await fillAndSave();
    await header('This sensor already has a plant');
    await tap('Move the sensor to the new plant');
    expect(await header('All set!')).toBeTruthy();
    const rpc = fetchImpl.mock.calls.find((c) => String(c[0]).endsWith('/rpc/create_plant_and_link_device')) as unknown as [string, RequestInit];
    expect(JSON.parse(String(rpc[1].body))).toMatchObject({ p_move: true });
  });
});

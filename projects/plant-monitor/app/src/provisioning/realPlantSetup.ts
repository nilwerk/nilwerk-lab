// Real PlantSetupService (4.A4c): the setup flow's "save plant" reads the sensor's current plant, then calls create_plant_and_link_device
// (one atomic RPC: plant insert + devices.plant_id link, or neither). A sensor that already has a plant is not moved without an explicit choice.
// Communication: PostgREST with the user's JWT, the same client as plants/plantsRest.ts (no second Supabase client, no new backend).
// Contract: docs/interfaces/db-schema.sql create_plant_and_link_device (also in migration 20261107000001, byte-identical copy).
// Photos are NOT saved here: a photo is refused, never dropped silently. The real build offers no photo (noPhotoSource.supported = false).
// NOT run against a live backend (no project in this session).
import { call, type RestDeps } from '../plants/plantsRest';
import { PlantSetupError, type PhotoSource, type PlantDetails, type PlantSaveResult, type PlantSetupService } from './types';

export interface RealPlantSetupDeps {
  baseUrl: string;
  publishableKey: string;
  getAccessToken: () => Promise<string | null>;
  /** the signed-in user's id (auth.uid()); null when signed out */
  getUserId: () => Promise<string | null>;
  fetchImpl?: typeof fetch;
}

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
/** optional text: an empty field is stored as null, not as ''. */
const opt = (s: string): string | null => (s.trim() === '' ? null : s.trim());

export function createRealPlantSetup(d: RealPlantSetupDeps): PlantSetupService {
  const rest: RestDeps = { baseUrl: d.baseUrl, publishableKey: d.publishableKey, getAccessToken: d.getAccessToken, fetchImpl: d.fetchImpl };
  return {
    async createPlant(deviceId: string, details: PlantDetails, photoUri: string | null, opts: { moveFromCurrent?: boolean } = {}): Promise<PlantSaveResult> {
      if (photoUri !== null) throw new PlantSetupError('photo_unsupported');
      if (!UUID.test(deviceId)) throw new PlantSetupError('device_not_found');
      const ownerId = await d.getUserId().catch(() => null);
      if (!ownerId) throw new PlantSetupError('not_signed_in');

      // 1. read the sensor's current plant (RLS: only the owner's device is visible). Nothing is written yet.
      let currentPlant: string | null;
      try {
        const dev = await call(rest, `/rest/v1/devices?select=plant_id&id=eq.${deviceId}`);
        // an empty answer means the device is not visible (RLS), so it is not a silent "no plant"
        if (!Array.isArray(dev.json) || dev.json.length !== 1) throw new PlantSetupError('device_not_found');
        currentPlant = (dev.json[0] as { plant_id?: string | null }).plant_id ?? null;
      } catch (e) {
        if (e instanceof PlantSetupError) throw e;
        throw new PlantSetupError();
      }
      if (currentPlant !== null && !opts.moveFromCurrent) return { status: 'already_linked' };

      // 2. one server call: plant insert + device link in one transaction (create_plant_and_link_device, migration 1 / db-schema.sql).
      //    If the link fails the server rolls the insert back too, so no orphan plant is left behind.
      try {
        const r = await call(rest, '/rest/v1/rpc/create_plant_and_link_device', {
          method: 'POST',
          body: {
            p_device: deviceId, p_name: details.name.trim(), p_location_type: details.location, p_area: opt(details.area),
            p_soil_type: details.soil, p_species: opt(details.species), p_city: opt(details.city), p_move: currentPlant !== null,
          },
        });
        if (typeof r.json !== 'string' || !UUID.test(r.json)) throw new PlantSetupError();
        return { status: 'saved', plantId: r.json };
      } catch {
        throw new PlantSetupError();
      }
    },
  };
}

/** Real build without a configured backend: saving says so; it never pretends. */
export const unconfiguredPlantSetup: PlantSetupService = {
  async createPlant() { throw new PlantSetupError('not_configured'); },
};

/** Real build: no photo source yet (expo-image-picker and the upload come later). supported=false makes the photo step offer only "Skip". */
export const noPhotoSource: PhotoSource = { supported: false, takePhoto: async () => null, pickFromLibrary: async () => null };

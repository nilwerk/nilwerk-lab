// Real PlantSetupService (4.A4c, minimum for the bench test): the setup flow's "save plant" writes the plants row and points the device at it.
// Communication: PostgREST with the user's JWT, the same client as plants/plantsRest.ts (no second Supabase client, no new backend).
// Contract: plants insert (docs/interfaces/db-schema.sql L82 plants_all_own: owner_id must be auth.uid()); devices.plant_id update
// (migration 20261108000005_devices_plant_check.sql: the plant must be the caller's; db-schema.sql L109 is the older clause without it).
// Photos are NOT saved here: a photo is refused, never dropped silently. The real build offers no photo (noPhotoSource.supported = false).
// NOT run against a live backend (no project in this session).
import { call, type RestDeps } from '../plants/plantsRest';
import { PlantSetupError, type PhotoSource, type PlantDetails, type PlantSetupService } from './types';

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
    async createPlant(deviceId: string, details: PlantDetails, photoUri: string | null): Promise<{ plantId: string }> {
      if (photoUri !== null) throw new PlantSetupError('photo_unsupported');
      if (!UUID.test(deviceId)) throw new PlantSetupError('device_not_found');
      const ownerId = await d.getUserId().catch(() => null);
      if (!ownerId) throw new PlantSetupError('not_signed_in');

      let plantId: string;
      try {
        const ins = await call(rest, '/rest/v1/plants', {
          method: 'POST',
          body: { owner_id: ownerId, name: details.name.trim(), location_type: details.location, area: opt(details.area), soil_type: details.soil, species: opt(details.species), city: opt(details.city) },
          prefer: 'return=representation',
        });
        const row = Array.isArray(ins.json) ? (ins.json[0] as { id?: unknown } | undefined) : undefined;
        if (typeof row?.id !== 'string' || !UUID.test(row.id)) throw new PlantSetupError();
        plantId = row.id;
      } catch {
        throw new PlantSetupError();
      }

      try {
        // PostgREST answers 200 with [] when RLS hides the device, so an empty answer is a failed link, not a success
        const link = await call(rest, `/rest/v1/devices?id=eq.${deviceId}`, { method: 'PATCH', body: { plant_id: plantId }, prefer: 'return=representation' });
        if (!Array.isArray(link.json) || link.json.length !== 1) throw new PlantSetupError();
      } catch {
        // do not leave a plant without its sensor behind; if this clean-up fails too, the plant row stays (see the PR)
        await call(rest, `/rest/v1/plants?id=eq.${plantId}`, { method: 'DELETE' }).catch(() => undefined);
        throw new PlantSetupError();
      }
      return { plantId };
    },
  };
}

/** Real build without a configured backend: saving says so; it never pretends. */
export const unconfiguredPlantSetup: PlantSetupService = {
  async createPlant() { throw new PlantSetupError('not_configured'); },
};

/** Real build: no photo source yet (expo-image-picker and the upload come later). supported=false makes the photo step offer only "Skip". */
export const noPhotoSource: PhotoSource = { supported: false, takePhoto: async () => null, pickFromLibrary: async () => null };

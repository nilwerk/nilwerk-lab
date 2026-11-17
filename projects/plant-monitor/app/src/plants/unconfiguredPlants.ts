// Used when the app runs against a real auth backend: plants have no real client yet (4.A4 is mock-only), so every call says "not configured".
import { PlantsError, type PlantsService } from './types';

export function unconfiguredPlants(): PlantsService {
  const no = async (): Promise<never> => { throw new PlantsError('not_configured'); };
  return { listPlants: no, getPlantDetail: no, listPhotos: no, deletePlant: no, removePhotoObjects: no, releaseDevice: no, exportData: no };
}

// Real PlantsService export + gate (4.A9, NFR-07, FR-A01, A-106). Replaces the two test.todo items from the #114 gates.
import { createRealPlants } from '../plants/realPlants';
import { PlantsError } from '../plants/types';
import { unconfiguredPlants } from '../plants/unconfiguredPlants';
import { canDelete } from '../export/exportGate';
import { handOffFile, HandOffError, type HandOffDeps } from '../export/fileHandOff';

const ok = () => ({ status: 200, headers: { get: () => 'application/json' }, arrayBuffer: async () => new TextEncoder().encode('{"plants":[{}],"photos":[{},{}]}').buffer }) as unknown as Response;
const mk = (o: { handOff?: (f: any) => Promise<void>; fetchImpl?: any; token?: string | null } = {}) => {
  const handOff = jest.fn(o.handOff ?? (async () => undefined));
  const svc = createRealPlants({ baseUrl: 'https://x.supabase.co', publishableKey: 'p', getAccessToken: async () => (o.token === undefined ? 'jwt' : o.token), handOff, now: () => new Date('2026-11-17T10:00:00Z'), fetchImpl: o.fetchImpl ?? jest.fn().mockResolvedValue(ok()) });
  return { svc, handOff };
};
// what the screens do: exported = exportData resolved
const screenExported = async (svc: ReturnType<typeof mk>['svc']) => svc.exportData('json').then(() => true, () => false);

describe('real exportData hands the file over before it resolves', () => {
  test('resolves with metadata after the hand-off got the exact bytes and name', async () => {
    const { svc, handOff } = mk();
    const r = await svc.exportData('json');
    expect(handOff).toHaveBeenCalledTimes(1);
    expect(handOff.mock.calls[0][0]).toMatchObject({ fileName: 'plant-monitor-export-2026-11-17.json', contentType: 'application/json' });
    expect(handOff.mock.calls[0][0].bytes.length).toBeGreaterThan(0);
    expect(r).toMatchObject({ format: 'json', fileName: 'plant-monitor-export-2026-11-17.json', plantCount: 1, photoCount: 2 });
  });
  test('exported is NOT set when the hand-off fails (fetch ok, file never reached the user)', async () => {
    const { svc } = mk({ handOff: async () => { throw new HandOffError('not_confirmed'); } });
    expect(await screenExported(svc)).toBe(false);
    const gate = { exported: await screenExported(svc), typed: 'Basil', expected: 'Basil' };
    expect(canDelete(gate)).toBe(false);
  });
  test('hand-off is not called when the fetch fails; no token -> no fetch, no hand-off', async () => {
    const a = mk({ fetchImpl: jest.fn().mockResolvedValue({ status: 500, headers: { get: () => null }, arrayBuffer: async () => new ArrayBuffer(0) }) });
    await expect(a.svc.exportData('json')).rejects.toBeInstanceOf(PlantsError);
    expect(a.handOff).not.toHaveBeenCalled();
    const f = jest.fn();
    const b = mk({ token: null, fetchImpl: f });
    expect(await screenExported(b.svc)).toBe(false);
    expect(f).not.toHaveBeenCalled(); expect(b.handOff).not.toHaveBeenCalled();
  });
  test('end to end with the real handOffFile and a share sheet the user dismisses: gate stays closed', async () => {
    const deps: HandOffDeps = { write: async (f) => ({ uri: 'u', size: f.bytes.length }), isShareAvailable: async () => true, share: async () => undefined, confirmSaved: async () => false };
    const svc = createRealPlants({ baseUrl: 'https://x.supabase.co', publishableKey: 'p', getAccessToken: async () => 'jwt', handOff: (f) => handOffFile(f, deps), fetchImpl: jest.fn().mockResolvedValue(ok()) });
    expect(await screenExported(svc)).toBe(false);
  });
  test('every other call is still not_configured (only the export is real in this slice)', async () => {
    const { svc } = mk();
    await expect(svc.listPlants()).rejects.toMatchObject({ code: 'not_configured' });
    expect(Object.keys(svc).sort()).toEqual(Object.keys(unconfiguredPlants()).sort());
  });
});

// Export-before-delete gate (NFR-07; plant removal A-022 + openapi /plants/{id}; account delete openapi /account "Export before deleting is the app's job"). Pure logic, no UI.
import { canDelete } from '../export/exportGate';

describe('canDelete (export before delete)', () => {
  test('blocked before any export, even with the exact name typed', () => {
    expect(canDelete({ exported: false, typed: 'Basil', expected: 'Basil' })).toBe(false);
  });
  test('blocked after the export when the name is missing or different', () => {
    expect(canDelete({ exported: true, typed: '', expected: 'Basil' })).toBe(false);
    expect(canDelete({ exported: true, typed: 'basil', expected: 'Basil' })).toBe(false);
  });
  test('allowed only after the export AND the exact name (surrounding spaces ignored)', () => {
    expect(canDelete({ exported: true, typed: 'Basil', expected: 'Basil' })).toBe(true);
    expect(canDelete({ exported: true, typed: '  Basil ', expected: 'Basil' })).toBe(true);
  });
});

// Account delete guard (FR-A01, NFR-07). deleteAccountGated is the only path to AuthService.deleteAccount, so a missed UI disable cannot delete.
import { DeleteGateError, deleteAccountGated } from '../export/exportGate';

describe('deleteAccountGated', () => {
  const closed = [
    { name: 'no export, word typed', gate: { exported: false, typed: 'DELETE', expected: 'DELETE' } },
    { name: 'export done, word missing', gate: { exported: true, typed: '', expected: 'DELETE' } },
    { name: 'export done, wrong case', gate: { exported: true, typed: 'delete', expected: 'DELETE' } },
  ];
  test.each(closed)('closed gate ($name): rejects with DeleteGateError and never calls delete', async ({ gate }) => {
    const del = jest.fn(async () => undefined);
    await expect(deleteAccountGated(gate, del)).rejects.toBeInstanceOf(DeleteGateError);
    expect(del).not.toHaveBeenCalled();
  });
  test('open gate calls delete exactly once and passes its failure through', async () => {
    const del = jest.fn(async () => undefined);
    await deleteAccountGated({ exported: true, typed: 'DELETE', expected: 'DELETE' }, del);
    expect(del).toHaveBeenCalledTimes(1);
    const boom = new Error('boom');
    await expect(deleteAccountGated({ exported: true, typed: 'DELETE', expected: 'DELETE' }, async () => { throw boom; })).rejects.toBe(boom);
  });
});

// Gate from Theo's review of PR #114 (N2): exportData returns metadata only, no file reaches the user yet.
describe('real client gate (not built)', () => {
  test.todo('real PlantsService must not replace unconfiguredPlants until the export file hand-off (share sheet or download) exists');
  test.todo('exported is set only after the file hand-off succeeded, not when exportData resolves');
});

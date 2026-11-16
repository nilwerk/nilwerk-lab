// Export-before-delete gate (A-022, NFR-07, openapi.yaml: "the app MUST offer the JSON/CSV export before removal"). Pure logic, no UI.
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

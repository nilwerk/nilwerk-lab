// Export before delete (A-022, openapi.yaml /plants/{id} and /account: "the app MUST show a warning first and offer the JSON/CSV export").
// Deleting is allowed only after an export has run in this session AND the exact name is typed. Pure function, tested in __tests__/exportGate.test.ts.
// Requirements: NFR-07 (delete removes all data, export first), FR-A08 (remove plant), FR-A01 (account delete, screen owned by 4.A2 and not wired here).
export interface DeleteGate {
  /** an export (GET /export) has completed successfully */
  exported: boolean;
  /** what the user typed in the confirmation field */
  typed: string;
  /** the name that must be typed exactly (plant name; account uses the word DELETE) */
  expected: string;
}

export function canDelete({ exported, typed, expected }: DeleteGate): boolean {
  return exported && typed.trim() === expected;
}

// Export before delete (A-022, openapi.yaml /plants/{id} and /account: "the app MUST show a warning first and offer the JSON/CSV export").
// Deleting is allowed only after an export has run in this session AND the exact name is typed. Pure function, tested in __tests__/exportGate.test.ts.
// Requirements: NFR-07 (delete removes all data, export first), FR-A08 (remove plant), FR-A01 (account delete: DeleteAccountScreen, 4.A2).
// There is NO skip option: the requirements (NFR-07 / A-022 "export first") name none, and the OpenAPI says the app MUST offer the export first. A skip needs an owner decision (see the PR, Needs Arsany).
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

/** Thrown when a delete is attempted while the gate is closed. The UI disables the button, but the guard lives here so a missed disable cannot delete (NFR-07). */
export class DeleteGateError extends Error {
  constructor() { super('delete blocked: export first and confirm'); this.name = 'DeleteGateError'; }
}

/** The only way the app deletes the account: runs `del` only when the gate is open, otherwise rejects with DeleteGateError and calls nothing. */
export async function deleteAccountGated(gate: DeleteGate, del: () => Promise<void>): Promise<void> {
  if (!canDelete(gate)) throw new DeleteGateError();
  await del();
}

// Key name check for POST /api-keys (docs/interfaces/openapi.yaml: name required, maxLength 60; db-schema.sql api_keys.name length 1-60). FR-P03.
// Returns a string-catalogue key, never user-facing text. The server stays the authority.
import type { FieldResult } from '../validation';

export const KEY_NAME_MAX = 60;

export function validateKeyName(value: string): FieldResult {
  const v = value.trim();
  if (!v) return { key: 'mcp.keys.name.required' };
  if (v.length > KEY_NAME_MAX) return { key: 'mcp.keys.name.long', params: { max: KEY_NAME_MAX } };
  return null;
}

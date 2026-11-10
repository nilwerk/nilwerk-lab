// Sensor label / QR text: NW1:<hw_id>:<pop> (ble-provisioning.md section 1). PoP = 8 chars Crockford base32. Typing is forgiving about case and spaces.
export interface ParsedLabel { hwId: string; pop: string }

export function parseLabel(raw: string): ParsedLabel | null {
  const [v, hw, pop, ...rest] = raw.trim().split(':').map((p) => p.trim());
  if (rest.length || !v || !hw || !pop || v.toUpperCase() !== 'NW1') return null;
  const hwId = hw.toLowerCase();
  const p = pop.toUpperCase();
  return /^nw-[0-9a-f]{12}$/.test(hwId) && /^[0-9A-HJKMNP-TV-Z]{8}$/.test(p) ? { hwId, pop: p } : null;
}

/** Advertised name for a hw_id: NW-<last 6 hex>. */
export const advertisedName = (hwId: string): string => `NW-${hwId.slice(-6)}`;

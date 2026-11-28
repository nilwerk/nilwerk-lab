// Care tips (task 4.A7, read side of 4.B3). Requirements: FR-P02 (tips come only from the guardrailed cache, never unsafe; a tip stored under another
// guardrail version is not shown), FR-P04 (premium only; the screen gates on the plan before any read), NFR-06 (own plant only, enforced by RLS).
// Contract: docs/interfaces/mcp-tools.json get_tips (item = {id, category, text}, text <= 400) and the public.tips row in docs/interfaces/db-schema.sql.
// Pure TypeScript, no network. The checks mirror cloud/supabase/functions/_shared/mcp.ts (get_tips): a stored answer that fails them is an error,
// never a partial list. No tip text is written in the app: every string shown is the text the server stored.

/** Must equal GUARDRAIL_VERSION in cloud/tips/guardrails.ts (g1.1 at the time of writing). Tips stored under another version are not shown (FR-P02). */
export const GUARDRAIL_VERSION_EXPECTED = 'g1.1';

export const TIP_CATEGORIES = ['watering', 'light', 'temperature', 'feeding', 'safety', 'other'] as const;
export type TipCategory = (typeof TIP_CATEGORIES)[number];
export const TIP_TEXT_MAX = 400;

/** One tip as the contract returns it. The contract has no caveat or reason field (action/reason stay internal, cloud/tips/mcp.ts), so none is shown. */
export interface Tip { id: string; category: TipCategory; text: string }

/** The current tips of one plant. `null` from the service means "no current tips" (the empty state). */
export interface PlantTips { plantId: string; generatedAt: string; items: Tip[] }

const isObj = (v: unknown): v is Record<string, unknown> => typeof v === 'object' && v !== null && !Array.isArray(v);

/** Every item must match the contract; one bad item rejects the whole answer (same rule as the MCP server). */
export function parseTipItems(content: unknown): Tip[] | null {
  if (!isObj(content) || !Array.isArray(content.items)) return null;
  const out: Tip[] = [];
  for (const it of content.items) {
    if (!isObj(it)) return null;
    const { id, category, text } = it;
    if (typeof id !== 'string' || id.length === 0) return null;
    if (typeof category !== 'string' || !(TIP_CATEGORIES as readonly string[]).includes(category)) return null;
    if (typeof text !== 'string' || text.length === 0 || text.length > TIP_TEXT_MAX) return null;
    out.push({ id, category: category as TipCategory, text });
  }
  return out;
}

/** One row of GET /rest/v1/tips (selected columns only). Returns null when the row does not match the contract. */
export function parseTipsRow(row: unknown, plantId: string): PlantTips | null {
  if (!isObj(row)) return null;
  const { generated_at: generatedAt, content, guardrail_version: version } = row;
  if (typeof generatedAt !== 'string' || Number.isNaN(Date.parse(generatedAt))) return null;
  if (version !== GUARDRAIL_VERSION_EXPECTED) return null;
  const items = parseTipItems(content);
  if (!items) return null;
  return { plantId, generatedAt, items };
}

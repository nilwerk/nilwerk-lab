// Maps the engine result to the published contracts (task 4.B3 slice 1b, Theo C1/C2).
//  - docs/interfaces/mcp-tools.json get_tips: {plant_id, generated_at, items:[{id, category, text}]}, category enum
//    watering|light|temperature|feeding|safety|other, text <= 400. Only those fields are emitted (no silent divergence);
//    action, reason and evidence stay internal until an ADR extends the contract (additive proposal in the PR).
//  - db-schema.sql tips: content = {"items":[...]}, weather = forecast snapshot, guardrail_version = GUARDRAIL_VERSION.
import { GUARDRAIL_VERSION } from "./guardrails.ts";
import type { Tip, TipsResult } from "./types.ts";

export type McpCategory = "watering" | "light" | "temperature" | "feeding" | "safety" | "other";
export interface McpTipItem { id: string; category: McpCategory; text: string }
export interface McpTips { plant_id: string; generated_at: string; items: McpTipItem[] }

/** Tips whose engine category is too coarse are refined by id (rule-based ones) so frost is "temperature", storm "safety". */
const BY_ID: Record<string, McpCategory> = { "frost-protect": "temperature", "storm-shelter": "safety", "heat-shade": "light", "sensor-stale": "other" };
const BY_CATEGORY: Record<Tip["category"], McpCategory> = {
  watering: "watering", fertilising: "feeding", placement: "light", protection: "safety", sensor: "other", general: "other",
};
export const MCP_TEXT_MAX = 400;

export function mcpCategory(t: Pick<Tip, "id" | "category" | "source">): McpCategory {
  return (t.source === "rules" && BY_ID[t.id]) || BY_CATEGORY[t.category] || "other";
}
export function toMcpTips(r: TipsResult): McpTips {
  return { plant_id: r.plantId, generated_at: r.generatedAt, items: r.tips.map((t) => ({ id: t.id, category: mcpCategory(t), text: t.text.slice(0, MCP_TEXT_MAX) })) };
}
/** Columns for public.tips (expires_at, owner_id, model are the caller's). */
export function toTipsRow(r: TipsResult): { plant_id: string; generated_at: string; content: { items: McpTipItem[] }; weather: TipsResult["weather"]; guardrail_version: string } {
  return { plant_id: r.plantId, generated_at: r.generatedAt, content: { items: toMcpTips(r).items }, weather: r.weather, guardrail_version: r.guardrailVersion || GUARDRAIL_VERSION };
}

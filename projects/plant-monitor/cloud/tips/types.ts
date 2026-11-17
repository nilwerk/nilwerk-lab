// Care-tips engine, slice 1 (task 4.B3). Pure types, no dependencies: runs in Deno and Node 22+.
// Requirements: FR-P02 (tips from location, weather, season, plant + soil type, readings; never unsafe),
// FR-P04 (premium only), ADR-006 (rule layer always wins), architecture.md O-7 (schema-validate model output).

export type LocationType = "house" | "balcony" | "garden" | "farm" | "greenhouse"; // db-schema plants.location_type
export type SoilType = "potting" | "garden" | "sand" | "clay" | "peat" | "other";   // db-schema plants.soil_type
export type Season = "spring" | "summer" | "autumn" | "winter";
export type TipCategory = "watering" | "fertilising" | "placement" | "protection" | "sensor" | "general";
export type TipAction = "do" | "avoid";

export interface PlantInput {
  id: string;
  name: string;
  locationType: LocationType;
  soilType: SoilType;
  species?: string | null;
  city?: string | null;
  dryThresholdPct: number; // plants.dry_threshold_pct (G1: dry < 25)
  wetThresholdPct: number; // plants.wet_threshold_pct (G1: wet > 85)
}
export interface ReadingInput { ts: string; moisturePct: number | null; tempC?: number | null }

/** Forecast for the next 24 h at the plant's city. Provided by an injected WeatherProvider (Q-13 still open). */
export interface Forecast { minTempC: number; maxTempC: number; rainMm: number; stormWarning: boolean; heatWarning: boolean }
export interface WeatherProvider { forecast(city: string, signal?: AbortSignal): Promise<Forecast> }

export interface Evidence { kind: "reading" | "weather" | "plant" | "season"; key: string; value: string | number | boolean }
export interface Tip {
  id: string;
  category: TipCategory;
  action: TipAction;
  text: string;
  reason: string;
  evidence: Evidence[];
  source: "rules" | "llm";
}
/** What an injected text assistant may propose. Everything is re-checked by the guardrails. */
export interface ProposedTip { id: string; category: string; action: string; text: string; reason: string }
export interface TextAssistant { propose(ctx: AssistantContext, signal?: AbortSignal): Promise<unknown> }
export interface AssistantContext {
  plant: Pick<PlantInput, "name" | "locationType" | "soilType" | "species">;
  season: Season;
  weather: Forecast | null;
  moisturePct: number | null;
  baseline: Tip[]; // rule-based tips the assistant may rephrase or extend
}

export interface GuardrailState {
  season: Season;
  outdoor: boolean;             // balcony, garden, farm
  moisturePct: number | null;   // latest plausible, fresh reading; null = none usable
  saturated: boolean;           // moisture >= plant wet threshold
  dry: boolean;                 // moisture < plant dry threshold
  weather: Forecast | null;
  frost: boolean;               // forecast min <= FROST_C
  heat: boolean;                // heat warning or max >= HEAT_C
  storm: boolean;
  rainExpected: boolean;        // rain >= RAIN_MM
  plant: PlantInput;
}
export interface Removed { tip: Tip; ruleId: string; why: string }
export interface TipsResult {
  plantId: string;
  generatedAt: string;
  guardrailVersion: string;
  mode: "rule_based" | "live";
  tips: Tip[];
  removed: Removed[];            // advice the rule layer dropped (audit trail)
  weather: Forecast | null;      // snapshot used (tips.weather column)
  notes: string[];               // e.g. weather_unavailable, assistant_failed, no_fresh_reading
}
export type TipsErrorCode = "premium_required" | "invalid_input";
export class TipsError extends Error {
  code: TipsErrorCode;
  constructor(code: TipsErrorCode, message: string) { super(message); this.code = code; this.name = "TipsError"; }
}

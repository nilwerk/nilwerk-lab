// Care-tips engine, slice 1 (4.B3): rule-based candidates -> optional injected text assistant -> deterministic guardrails.
// Requirements: FR-P02, FR-P04, ADR-006 (TIPS_MODE rule_based | live), A-029. No I/O of its own: weather and the text
// assistant are injected, the clock is a parameter. No LLM, no keys, no network in this slice.
import { applyGuardrails, deriveState, GUARDRAIL_VERSION, validateProposals, validForecast } from "./guardrails.ts";
import type { AssistantContext, Evidence, Forecast, GuardrailState, PlantInput, ReadingInput, TextAssistant, Tip, TipCategory, TipsResult, WeatherProvider } from "./types.ts";
import { TipsError } from "./types.ts";

export interface TipsRequest { plant: PlantInput; readings: ReadingInput[]; now: string; premium: boolean }
export interface TipsDeps { weather: WeatherProvider; assistant?: TextAssistant; mode?: "rule_based" | "live"; timeoutMs?: number }

const LOC = ["house", "balcony", "garden", "farm", "greenhouse"], SOIL = ["potting", "garden", "sand", "clay", "peat", "other"];
function validate(r: TipsRequest): void {
  const bad = (m: string) => { throw new TipsError("invalid_input", m); };
  const p = r?.plant;
  if (!p || typeof p.id !== "string" || !p.id) bad("plant.id missing");
  if (!LOC.includes(p.locationType)) bad("plant.locationType unknown");
  if (!SOIL.includes(p.soilType)) bad("plant.soilType unknown");
  const n = (v: unknown) => typeof v === "number" && Number.isFinite(v) && v >= 0 && v <= 100;
  if (!n(p.dryThresholdPct) || !n(p.wetThresholdPct) || p.dryThresholdPct >= p.wetThresholdPct) bad("thresholds invalid (need 0 <= dry < wet <= 100)");
  if (!Array.isArray(r.readings)) bad("readings must be an array");
  if (!Number.isFinite(Date.parse(r.now))) bad("now is not a valid timestamp");
}

const ev = (kind: Evidence["kind"], key: string, value: Evidence["value"]): Evidence => ({ kind, key, value });
function plantEv(s: GuardrailState): Evidence[] {
  return [ev("plant", "soilType", s.plant.soilType), ev("plant", "locationType", s.plant.locationType), ev("season", "season", s.season)];
}

/** Canned, rule-selected tips (TIPS_MODE=rule_based, cost 0). Deliberately simple: safety is the guardrails' job, not this list's. */
export function baselineTips(s: GuardrailState): Tip[] {
  const t: Tip[] = [];
  const add = (id: string, category: TipCategory, action: "do" | "avoid", text: string, reason: string, evidence: Evidence[]) =>
    t.push({ id, category, action, text, reason, evidence, source: "rules" });
  const m = s.moisturePct;
  const mEv = m === null ? [] : [ev("reading", "moisturePct", m)];
  if (m === null) {
    add("sensor-stale", "sensor", "do", "No recent soil reading. Check the sensor, and test the soil with a finger before deciding anything.", "No plausible reading in the last 6 hours.", [ev("reading", "moisturePct", "none")]);
  } else if (s.dry) {
    const soil = s.plant.soilType === "sand" ? " Sandy soil drains fast, so water slowly and in two rounds." : s.plant.soilType === "clay" ? " Clay holds water, so water slowly and let it soak in." : "";
    add("water-now", "watering", "do", `Water the plant thoroughly.${soil}`, `Soil moisture is ${m}%, below the dry threshold of ${s.plant.dryThresholdPct}%.`, [...mEv, ev("plant", "dryThresholdPct", s.plant.dryThresholdPct), ...plantEv(s)]);
  } else if (s.saturated) {
    add("water-hold", "watering", "avoid", "Do not water. Let the soil drain and dry out; empty any saucer.", `Soil moisture is ${m}%, at or above the wet threshold of ${s.plant.wetThresholdPct}%.`, [...mEv, ev("plant", "wetThresholdPct", s.plant.wetThresholdPct)]);
  } else {
    add("water-ok", "watering", "avoid", "No watering needed right now.", `Soil moisture is ${m}%, between ${s.plant.dryThresholdPct}% and ${s.plant.wetThresholdPct}%.`, mEv);
  }
  if (s.weather) {
    const w = s.weather;
    if (s.frost && s.outdoor) add("frost-protect", "protection", "do", "Bring the plant inside or cover it tonight.", `Forecast minimum is ${w.minTempC} C.`, [ev("weather", "minTempC", w.minTempC)]);
    if (s.storm && s.outdoor) add("storm-shelter", "protection", "do", "Move the plant to a sheltered spot before the storm.", "A storm warning is active.", [ev("weather", "stormWarning", true)]);
    if (s.heat) add("heat-shade", "placement", "do", "Give the plant shade in the afternoon and check the soil twice a day.", `Heat expected (maximum ${w.maxTempC} C).`, [ev("weather", "maxTempC", w.maxTempC)]);
    if (s.rainExpected && s.outdoor) add("rain-skip", "watering", "avoid", "Skip watering, rain is coming.", `${w.rainMm} mm of rain forecast in 24 h.`, [ev("weather", "rainMm", w.rainMm)]);
  }
  if ((s.season === "spring" || s.season === "summer") && m !== null) {
    add("fertilise", "fertilising", "do", "A light dose of liquid fertiliser every 2 to 4 weeks suits the growing season.", `It is ${s.season}, the main growing period.`, [...plantEv(s)]);
  }
  return t;
}

/** Calls the injected assistant under a timeout. Any failure or nonsense degrades to rule-based tips, never to unchecked output. */
async function assist(a: TextAssistant, ctx: AssistantContext, ms: number, notes: string[]): Promise<Tip[]> {
  const ac = new AbortController(); let timer: ReturnType<typeof setTimeout> | undefined;
  try {
    const raw = await Promise.race([
      a.propose(ctx, ac.signal),
      new Promise<never>((_, rej) => { timer = setTimeout(() => { ac.abort(); rej(new Error("timeout")); }, ms); }),
    ]);
    const { ok, rejected } = validateProposals(raw);
    if (rejected.length) notes.push(`assistant_rejected:${rejected.join("; ")}`);
    return ok.map((p) => ({ id: `llm-${p.id}`, category: p.category as TipCategory, action: p.action as "do" | "avoid", text: p.text, reason: p.reason, evidence: [], source: "llm" as const }));
  } catch (e) {
    notes.push(`assistant_failed:${(e as Error).message}`); return [];
  } finally { if (timer) clearTimeout(timer); }
}

export async function generateTips(req: TipsRequest, deps: TipsDeps): Promise<TipsResult> {
  if (!req || req.premium !== true) throw new TipsError("premium_required", "care tips are a premium feature (FR-P04)");
  validate(req);
  const notes: string[] = [];
  let weather: Forecast | null = null;
  if (req.plant.city) {
    try {
      const f: unknown = await deps.weather.forecast(req.plant.city);
      if (validForecast(f)) weather = f; else notes.push("weather_unavailable:invalid forecast from provider");
    } catch (e) { notes.push(`weather_unavailable:${(e as Error).message}`); }
  } else notes.push("weather_unavailable:no city");
  const s = deriveState(req.plant, req.readings, weather, req.now);
  if (s.moisturePct === null) notes.push("no_fresh_reading");

  const base = baselineTips(s);
  const mode = deps.mode ?? "rule_based";
  let candidates = base;
  if (mode === "live" && deps.assistant) {
    const ctx: AssistantContext = { plant: { name: req.plant.name, locationType: req.plant.locationType, soilType: req.plant.soilType, species: req.plant.species }, season: s.season, weather, moisturePct: s.moisturePct, baseline: base };
    const extra = await assist(deps.assistant, ctx, deps.timeoutMs ?? 5000, notes);
    const ids = new Set(base.map((b) => b.id));
    candidates = [...base, ...extra.filter((x) => !ids.has(x.id))];
  }
  const { kept, removed } = applyGuardrails(candidates, s);
  return { plantId: req.plant.id, generatedAt: req.now, guardrailVersion: GUARDRAIL_VERSION, mode, tips: kept, removed, weather, notes };
}

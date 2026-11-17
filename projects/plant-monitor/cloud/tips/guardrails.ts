// Deterministic rule layer (FR-P02, ADR-006): runs on EVERY tip, whether from the rules or from an LLM, and always wins.
// No I/O, no clock, no randomness. Each rule has an ID that tests, audit trail and the tips.guardrail_version column refer to.
import type { Forecast, GuardrailState, PlantInput, ProposedTip, ReadingInput, Removed, Season, Tip, TipCategory } from "./types.ts";

export const GUARDRAIL_VERSION = "g1.1";
export const FROST_C = 2;          // forecast min at or below: frost risk (outdoor)
export const HEAT_C = 30;          // forecast max at or above (or heatWarning): heat
export const RAIN_MM = 5;          // rain expected over 24 h that makes outdoor watering pointless
export const MAX_READING_AGE_MS = 6 * 3600_000; // older than 6 h: not "current soil state" (sampling is 15 min, hourly report)
export const MAX_TEXT = 280;
export const CATEGORIES: TipCategory[] = ["watering", "fertilising", "placement", "protection", "sensor", "general"];

export function seasonOf(iso: string): Season {
  const m = new Date(iso).getUTCMonth() + 1; // northern hemisphere assumed (city only is known; documented limit)
  if (m >= 3 && m <= 5) return "spring";
  if (m >= 6 && m <= 8) return "summer";
  if (m >= 9 && m <= 11) return "autumn";
  return "winter";
}

/** Latest plausible reading not older than MAX_READING_AGE_MS, else null (never act on a stale or implausible value). */
export function currentMoisture(readings: ReadingInput[], nowIso: string): number | null {
  const now = Date.parse(nowIso);
  let best: { t: number; m: number } | null = null;
  for (const r of readings) {
    const t = Date.parse(r.ts);
    if (!Number.isFinite(t) || t > now || now - t > MAX_READING_AGE_MS) continue;
    if (r.moisturePct === null || !Number.isFinite(r.moisturePct) || r.moisturePct < 0 || r.moisturePct > 100) continue;
    if (!best || t > best.t) best = { t, m: r.moisturePct };
  }
  return best ? best.m : null;
}

/** Provider output is untrusted: anything but a complete, finite forecast is "no forecast" (fail safe, G-09 etc. apply). */
export function validForecast(f: unknown): f is Forecast {
  if (typeof f !== "object" || f === null) return false;
  const o = f as Record<string, unknown>;
  const num = (v: unknown) => typeof v === "number" && Number.isFinite(v);
  return num(o.minTempC) && num(o.maxTempC) && num(o.rainMm) && (o.rainMm as number) >= 0 && (o.minTempC as number) <= (o.maxTempC as number)
    && typeof o.stormWarning === "boolean" && typeof o.heatWarning === "boolean";
}

export function deriveState(plant: PlantInput, readings: ReadingInput[], weather: Forecast | null, nowIso: string): GuardrailState {
  const moisturePct = currentMoisture(readings, nowIso);
  return {
    season: seasonOf(nowIso),
    outdoor: plant.locationType === "balcony" || plant.locationType === "garden" || plant.locationType === "farm",
    moisturePct,
    saturated: moisturePct !== null && moisturePct >= plant.wetThresholdPct,
    dry: moisturePct !== null && moisturePct < plant.dryThresholdPct,
    weather,
    frost: weather !== null && weather.minTempC <= FROST_C,
    heat: weather !== null && (weather.heatWarning || weather.maxTempC >= HEAT_C),
    storm: weather !== null && weather.stormWarning,
    rainExpected: weather !== null && weather.rainMm >= RAIN_MM,
    plant,
  };
}

// --- what a tip really says (a model may mislabel category/action, so the text is classified too) ---------------
const NEGATION = /\b(do not|don't|dont|never|avoid|skip|no need to|hold off|stop)\b|\b(not|no)\b/i;
// Keyword lists are deliberately wide (English + German, synonyms). Stems have no trailing \b: JS \b is ASCII-only (ß, ü).
const WATER = /\b(water(?!proof|ed down)\w*|irrigat\w*|soak\w*|drench\w*|hydrat\w*|moisten\w*|dampen\w*|sprinkl\w*|hose\w*|pour\w*|drink|jug|watering[- ]can|top(ping)? up|giess|gie(ß|ss)|wasser|bew(ä|ae)sser|tr(ä|ae)nk|benetz|befeucht|tauch|feucht\w*)/i;
const FERT = /\b(fertili[sz]\w*|feed\w*|plant food|nutrient\w*|compost|manure|npk|d(ü|ue)ng|n(ä|ae)hrstoff|n(ä|ae)hr(l(ö|oe)sung)?)/i;
const OUTSIDE = /\b(move|put|place|set|leave|take|bring|keep|stand)\b[^.]*\b(outside|outdoors?|out|balcony|garden|terrace|patio|porch|draussen|drau(ß|ss)en|balkon|garten|terrasse)\b/i;
const SUN = /\b(direct|full|afternoon|midday|noon|strong|bright)\b[^.]*\b(sun(light|shine)?|sonne)\b|\b(sun(light|shine)?|sonne)\b[^.]*\b(direct|full|south[- ]facing|noon|midday)\b|\bsonne\b/i;

export interface Effective { watering: boolean; fertilising: boolean; goOutside: boolean; directSun: boolean }
/**
 * Positive advice only: "do not water" from the RULES is not watering advice. Text from the assistant (source "llm") is never
 * excused by a negation word or by a declared 'avoid': "Avoid letting it dry out, water it now" / "Never let it go thirsty:
 * water daily" are watering advice. An assistant tip that matches a keyword is judged as if it advised it (fail safe; the
 * baseline rule tips already carry the legitimate "do not water" messages).
 */
export function effective(t: Pick<Tip, "category" | "action" | "text"> & { source?: string }): Effective {
  const negated = t.source !== "llm" && t.action === "avoid" && NEGATION.test(t.text);
  const positive = !negated;
  return {
    watering: positive && (t.category === "watering" || WATER.test(t.text)),
    fertilising: positive && (t.category === "fertilising" || FERT.test(t.text)),
    goOutside: positive && OUTSIDE.test(t.text),
    directSun: positive && SUN.test(t.text),
  };
}

interface Rule { id: string; why: (s: GuardrailState, e: Effective) => string | null }
export const RULES: Rule[] = [
  { id: "G-01", why: (s, e) => e.watering && s.saturated ? `soil is saturated (${s.moisturePct}% >= ${s.plant.wetThresholdPct}%)` : null },
  { id: "G-02", why: (s, e) => e.watering && s.outdoor && s.rainExpected ? `rain expected (${s.weather?.rainMm} mm) for an outdoor plant` : null },
  { id: "G-03", why: (s, e) => e.watering && s.outdoor && s.frost ? `frost forecast (${s.weather?.minTempC} C) for an outdoor plant` : null },
  { id: "G-04", why: (s, e) => e.watering && s.moisturePct === null ? "no fresh plausible soil reading, cannot tell that the plant needs water" : null },
  { id: "G-05", why: (s, e) => e.watering && s.moisturePct !== null && !s.dry && !s.saturated ? `soil is not dry (${s.moisturePct}% >= ${s.plant.dryThresholdPct}%)` : null },
  { id: "G-06", why: (s, e) => e.fertilising && s.frost ? `frost forecast (${s.weather?.minTempC} C)` : null },
  { id: "G-07", why: (s, e) => e.fertilising && s.season === "winter" ? "winter dormancy" : null },
  { id: "G-08", why: (s, e) => e.fertilising && s.dry ? "dry soil: fertiliser would burn roots" : null },
  { id: "G-09", why: (s, e) => e.fertilising && s.outdoor && s.weather === null ? "outdoor plant and no forecast to rule out frost" : null },
  { id: "G-10", why: (s, e) => e.goOutside && s.storm ? "storm warning" : null },
  { id: "G-11", why: (s, e) => e.goOutside && s.frost ? `frost forecast (${s.weather?.minTempC} C)` : null },
  { id: "G-13", why: (s, e) => e.watering && s.outdoor && s.weather === null ? "outdoor plant and no valid forecast to rule out frost or rain" : null },
  { id: "G-12", why: (s, e) => e.directSun && s.heat ? "heat warning or forecast maximum >= 30 C" : null },
];

/** Structural check of untrusted assistant output (architecture O-7). Returns tips that passed and a reason per rejected entry. */
export function validateProposals(raw: unknown): { ok: ProposedTip[]; rejected: string[] } {
  const ok: ProposedTip[] = []; const rejected: string[] = [];
  if (!Array.isArray(raw)) return { ok, rejected: ["not an array"] };
  const ids = new Set<string>();
  raw.slice(0, 20).forEach((x, i) => {
    const o = (x ?? {}) as Record<string, unknown>;
    const str = (k: string) => typeof o[k] === "string" ? (o[k] as string).trim() : "";
    const id = str("id"), text = str("text"), reason = str("reason");
    let bad: string | null = null;
    if (!/^[a-z0-9_-]{1,40}$/i.test(id) || ids.has(id)) bad = "bad or duplicate id";
    else if (!CATEGORIES.includes(str("category") as TipCategory)) bad = "unknown category";
    else if (str("action") !== "do" && str("action") !== "avoid") bad = "unknown action";
    else if (text.length < 5 || text.length > MAX_TEXT || reason.length < 3 || reason.length > MAX_TEXT) bad = "text/reason length";
    else if (/[<>]|https?:|www\.|\bjavascript:/i.test(text + reason)) bad = "markup or link in text";
    if (bad) rejected.push(`#${i}: ${bad}`); else { ids.add(id); ok.push({ id, category: str("category"), action: str("action"), text, reason }); }
  });
  if (raw.length > 20) rejected.push("more than 20 entries, rest ignored");
  return { ok, rejected };
}

/** The rule layer. Drops every tip a rule forbids; the survivors are safe given the state. Order of tips is kept. */
export function applyGuardrails(tips: Tip[], s: GuardrailState): { kept: Tip[]; removed: Removed[] } {
  const kept: Tip[] = []; const removed: Removed[] = [];
  for (const tip of tips) {
    const e = effective(tip);
    let hit: { ruleId: string; why: string } | null = null;
    for (const r of RULES) { const w = r.why(s, e); if (w) { hit = { ruleId: r.id, why: w }; break; } }
    if (hit) removed.push({ tip, ...hit }); else kept.push(tip);
  }
  return { kept, removed };
}

// Slice 1b regression tests: false negation, forecast validation, keyword gaps, MCP contract mapping, guardrail version. FR-P02, FR-P03.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { generateTips } from "../engine.ts";
import { effective, GUARDRAIL_VERSION, validForecast } from "../guardrails.ts";
import { mcpCategory, toMcpTips, toTipsRow } from "../mcp.ts";
import type { Tip } from "../types.ts";

const NOW = "2026-06-15T10:00:00Z";
const plant = (o = {}) => ({ id: "p", name: "T", locationType: "house" as const, soilType: "potting" as const, city: "Berlin", dryThresholdPct: 25, wetThresholdPct: 85, ...o });
const mild = { minTempC: 12, maxTempC: 22, rainMm: 0, stormWarning: false, heatWarning: false };
const rd = (m: number) => [{ ts: "2026-06-15T09:50:00Z", moisturePct: m }];
const go = (p: ReturnType<typeof plant>, m: number, f: unknown, items?: unknown[]) =>
  generateTips({ plant: p, readings: rd(m), now: NOW, premium: true }, { weather: { forecast: () => Promise.resolve(f as never) }, assistant: items ? { propose: () => Promise.resolve(items) } : undefined, mode: items ? "live" : "rule_based" });
const one = (category: string, text: string, action = "do") => [{ id: "a", category, action, text, reason: "model says" }];

test("N-1 false negation / N-2 synonyms: assistant text advising water/fertiliser/outside/sun never survives a forbidding state", async () => {
  const water = ["Avoid letting it dry out, water it generously now.", "Don't forget to water the plant today.", "Never let it go thirsty: water it every day.",
    "No need to wait, water it now.", "Do not skip watering.", "Hose it down and give it a good drink.", "Gib der Pflanze heute viel Wasser.",
    "Top up the pot with a full jug today.", "Pour a litre into the pot.", "Soak the root ball.", "Bitte giessen Sie kraeftig.", "Bewässern Sie die Pflanze.",
    "Moisten the soil well.", "Empty a jug into the pot.", "Hose the plant.", "Top up the pot.", "Give it a splash of liquid.".replace("liquid", "drink")];
  for (const text of water) for (const [category, action] of [["general", "do"], ["watering", "avoid"], ["other", "avoid"]] as const) {
    const r = await go(plant(), 95, mild, one(category === "other" ? "general" : category, text, action));
    assert.ok(!r.tips.some((t) => t.id === "llm-a"), `survived: ${category}/${action}: ${text}`);
  }
  const fert = ["Never skip fertiliser: feed it now.", "Give it some plant food.", "Dünge die Pflanze kräftig.", "Add compost around the stem."];
  for (const text of fert) { const r = await go(plant({ locationType: "garden" }), 10, mild.constructor === Object ? { ...mild, minTempC: -3 } : mild, one("general", text, "avoid")); assert.ok(!r.tips.some((t) => t.id === "llm-a"), text); }
  const out = await go(plant({ locationType: "balcony" }), 50, { ...mild, stormWarning: true }, one("general", "Don't worry, just put it out on the balcony.", "avoid"));
  assert.ok(!out.tips.some((t) => t.id === "llm-a"));
  const sun = await go(plant(), 50, { ...mild, maxTempC: 35, heatWarning: true }, one("general", "Never hide it: give it full afternoon sun.", "avoid"));
  assert.ok(!sun.tips.some((t) => t.id === "llm-a"));
});
test("rule-sourced negation still works; the baseline 'Do not water' tip survives on saturated soil", async () => {
  const r = await go(plant(), 95, mild);
  assert.ok(r.tips.some((t) => t.id === "water-hold")); assert.ok(!r.tips.some((t) => effective(t).watering));
  assert.equal(effective({ category: "watering", action: "avoid", text: "Do not water.", source: "rules" } as Tip).watering, false);
  assert.equal(effective({ category: "watering", action: "avoid", text: "Do not water.", source: "llm" } as Tip).watering, true);
});
test("a harmless assistant tip without keywords still passes", async () => {
  const r = await go(plant(), 50, mild, one("general", "Dust the leaves with a soft cloth."));
  assert.ok(r.tips.some((t) => t.id === "llm-a"));
});

test("N-3 validForecast", () => {
  assert.equal(validForecast(mild), true);
  for (const bad of [null, undefined, {}, "x", 5, { ...mild, minTempC: NaN }, { ...mild, rainMm: Infinity }, { ...mild, rainMm: -1 }, { ...mild, maxTempC: undefined },
    { ...mild, minTempC: 30, maxTempC: 10 }, { ...mild, stormWarning: "no" }, { ...mild, heatWarning: undefined }, { ...mild, minTempC: "2" }]) assert.equal(validForecast(bad), false, JSON.stringify(bad));
});
test("N-3 invalid provider output = no forecast: weather null, note, outdoor fertilise blocked, watering still sensor-driven", async () => {
  for (const bad of [{}, null, { ...mild, minTempC: NaN, rainMm: NaN }, "sunny"]) {
    const r = await go(plant({ locationType: "garden" }), 10, bad, one("fertilising", "Fertilise heavily today."));
    assert.equal(r.weather, null); assert.ok(r.notes.some((n) => n.startsWith("weather_unavailable:invalid")), JSON.stringify(r.notes));
    assert.ok(!r.tips.some((t) => effective(t).fertilising));
    assert.ok(!r.tips.some((t) => t.id === "heat-shade" || t.id === "rain-skip"));
  }
});

const contract = JSON.parse(readFileSync(new URL("../../../docs/interfaces/mcp-tools.json", import.meta.url), "utf8")).tools.find((t: { name: string }) => t.name === "get_tips").outputSchema;
const ENUM: string[] = contract.properties.items.items.properties.category.enum;
test("C1 get_tips output matches mcp-tools.json: required keys, category enum, text length, no extra item fields", async () => {
  const cases = [await go(plant({ locationType: "garden" }), 10, { ...mild, minTempC: -2, stormWarning: true, maxTempC: 34, heatWarning: true }), await go(plant(), 95, mild), await go(plant(), 50, mild, one("general", "Dust the leaves."))];
  for (const r of cases) {
    const m = toMcpTips(r);
    for (const k of contract.required) assert.ok(k in m, k);
    assert.deepEqual(Object.keys(m).sort(), ["generated_at", "items", "plant_id"]);
    for (const it of m.items) { assert.deepEqual(Object.keys(it).sort(), ["category", "id", "text"]); assert.ok(ENUM.includes(it.category), it.category); assert.ok(it.text.length <= 400); }
  }
  const cats = new Set(cases.flatMap((r) => toMcpTips(r).items.map((i) => i.category)));
  for (const c of ["watering", "feeding", "temperature", "safety", "light", "other"]) assert.ok(cats.has(c as never), `category ${c} is produced`);
});
test("C1 every engine category maps into the enum; long text truncated to 400", () => {
  for (const c of ["watering", "fertilising", "placement", "protection", "sensor", "general"] as const) assert.ok(ENUM.includes(mcpCategory({ id: "x", category: c, source: "llm" })));
  assert.equal(mcpCategory({ id: "frost-protect", category: "protection", source: "rules" }), "temperature");
  assert.equal(mcpCategory({ id: "frost-protect", category: "protection", source: "llm" }), "safety");
  const r = { plantId: "p", generatedAt: NOW, guardrailVersion: "v", mode: "rule_based" as const, removed: [], weather: null, notes: [], tips: [{ id: "i", category: "general" as const, action: "do" as const, text: "x".repeat(900), reason: "r", evidence: [], source: "rules" as const }] };
  assert.equal(toMcpTips(r).items[0].text.length, 400);
});
test("C2 guardrail version exposed on the result and the tips row", async () => {
  const r = await go(plant(), 95, mild);
  assert.equal(GUARDRAIL_VERSION, "g1.1"); assert.equal(r.guardrailVersion, GUARDRAIL_VERSION);
  const row = toTipsRow(r);
  assert.equal(row.guardrail_version, GUARDRAIL_VERSION); assert.deepEqual(Object.keys(row.content), ["items"]); assert.deepEqual(row.weather, r.weather);
});

test("C-a/C-b: G-13 removes outdoor watering without forecast and a neutral rules tip replaces it; it is not watering advice", async () => {
  const dryOut = plant({ locationType: "garden" });
  const r = await go(dryOut, 10, null);
  assert.ok(r.removed.some((x) => x.ruleId === "G-13" && x.tip.id === "water-now"));
  assert.ok(!r.tips.some((t) => t.category === "watering"));
  const n = r.tips.find((t) => t.id === "no-forecast-check-soil");
  assert.ok(n, "neutral tip present"); assert.equal(n!.source, "rules"); assert.equal(n!.text, "No forecast available: check the soil by finger.");
  const e = effective(n!); assert.equal(e.watering, false); assert.equal(e.fertilising, false); assert.equal(e.goOutside, false); assert.equal(e.directSun, false);
  assert.ok(!r.removed.some((x) => x.tip.id === n!.id), "passes the guardrails itself");
  assert.equal(r.guardrailVersion, "g1.1");
  assert.equal(mcpCategory(n!), "other");
});
test("C-b: neutral tip appears only when G-13 fired, exactly once, also for an assistant watering tip and for invalid forecast", async () => {
  assert.ok(!(await go(plant({ locationType: "garden" }), 10, mild)).tips.some((t) => t.id === "no-forecast-check-soil"), "forecast ok: no neutral tip");
  assert.ok(!(await go(plant(), 10, null)).tips.some((t) => t.id === "no-forecast-check-soil"), "indoor: G-13 does not apply");
  assert.ok(!(await go(plant({ locationType: "garden" }), 50, null)).tips.some((t) => t.id === "no-forecast-check-soil"), "no watering tip removed");
  const bad = await go(plant({ locationType: "balcony" }), 10, { minTempC: NaN });
  assert.equal(bad.tips.filter((t) => t.id === "no-forecast-check-soil").length, 1);
  const llm = await go(plant({ locationType: "garden" }), 10, null, one("general", "Give it a good drink today."));
  assert.equal(llm.tips.filter((t) => t.id === "no-forecast-check-soil").length, 1);
});
test("C-b: the neutral tip text is never a watering instruction (classifier on the exported text)", async () => {
  const { NO_FORECAST_TIP } = await import("../engine.ts");
  const e = effective(NO_FORECAST_TIP);
  assert.deepEqual(e, { watering: false, fertilising: false, goOutside: false, directSun: false });
});
test("C-b: the neutral tip goes through the guardrails; a watering-worded one is removed, never kept", async () => {
  const { addNoForecastTip, NO_FORECAST_TIP } = await import("../engine.ts");
  const { deriveState } = await import("../guardrails.ts");
  const s = deriveState(plant({ locationType: "garden" }), rd(10), null, NOW);
  const g13 = { tip: { ...NO_FORECAST_TIP, id: "x" }, ruleId: "G-13", why: "w" };
  const k: Tip[] = [], rm = [g13];
  addNoForecastTip(k, rm, s, { ...NO_FORECAST_TIP, text: "Water the soil by finger." });
  assert.equal(k.length, 0); assert.equal(rm.length, 2); assert.equal(rm[1].ruleId, "G-13");
  const k2: Tip[] = [], rm2: typeof rm = [];
  addNoForecastTip(k2, rm2, s); assert.equal(k2.length + rm2.length, 0, "no G-13, no tip");
});

// Regression tests from QA (Ines, PR #118 comment): adversarial bypass attempts against the guardrails. Do not weaken.
import { test } from "node:test";
import assert from "node:assert/strict";
import type { Forecast, TextAssistant, Tip, TipsResult } from "../types.ts";
const D = new URL("../", import.meta.url).href;
const { generateTips } = await import(D + "engine.ts");
const { effective, currentMoisture, deriveState } = await import(D + "guardrails.ts");
const NOW = "2026-06-15T10:00:00Z";
const plant = (o: Record<string, unknown> = {}) => ({ id: "p", name: "T", locationType: "house", soilType: "potting", city: "Berlin", dryThresholdPct: 25, wetThresholdPct: 85, ...o });
const mild = { minTempC: 12, maxTempC: 22, rainMm: 0, stormWarning: false, heatWarning: false };
const rd = (m: number | null, ms = 600000) => [{ ts: new Date(Date.parse(NOW) - ms).toISOString(), moisturePct: m }];
const run = (p: unknown, r: unknown, f: Forecast | Error | null, asst?: TextAssistant, now = NOW) => generateTips({ plant: p, readings: r, now, premium: true }, { weather: { forecast: () => (f instanceof Error ? Promise.reject(f) : Promise.resolve(f)) }, assistant: asst, mode: asst ? "live" : "rule_based" });
const llm = (id: string, category: string, text: string, action = "do") => ({ propose: () => Promise.resolve([{ id, category, action, text, reason: "model says" }]) });
const watered = (r: TipsResult) => r.tips.some((t: Tip) => effective(t).watering);

test("A1 negation trick: action=avoid, text 'Avoid letting it dry out, water it generously' on saturated soil", async () => {
  const r = await run(plant(), rd(95), mild, llm("a", "watering", "Avoid letting it dry out, water it generously now.", "avoid"));
  assert.ok(!watered(r), JSON.stringify(r.tips.map((t: Tip) => t.text)));
});
test("A2 negation trick: action=avoid, text 'Don't forget to water the plant today' on saturated soil", async () => {
  const r = await run(plant(), rd(95), mild, llm("a", "general", "Don't forget to water the plant today.", "avoid"));
  assert.ok(!watered(r), JSON.stringify(r.tips.map((t: Tip) => t.text)));
});
test("A3 genuine 'Do not water' (action=do, category=watering) on saturated soil is dropped, not crashing", async () => {
  const r = await run(plant(), rd(95), mild, llm("a", "watering", "Do not water this plant.", "do"));
  assert.ok(!r.tips.some((t: Tip) => t.id === "llm-a"));
});
test("A4 mislabelled category general + German 'gießen' on saturated soil", async () => {
  const r = await run(plant(), rd(95), mild, llm("a", "general", "Bitte gießen Sie die Pflanze kräftig."));
  assert.ok(!watered(r));
});
test("A5 mislabelled category sensor, uppercase 'WATER NOW' on dry-not soil (50%)", async () => {
  const r = await run(plant(), rd(50), mild, llm("a", "sensor", "WATER NOW"));
  assert.ok(!watered(r));
});
test("A6 synonym not in keyword list: 'Give the plant a good drink of Wasser / hose it down' on saturated soil", async () => {
  const r = await run(plant(), rd(95), mild, llm("a", "general", "Hose it down and give it a good drink."));
  assert.ok(!watered(r), "keyword classifier bypass: " + JSON.stringify(r.tips.map((t: Tip) => t.text)));
});
test("A7 German synonym 'Gib der Pflanze Wasser'", async () => {
  const r = await run(plant(), rd(95), mild, llm("a", "general", "Gib der Pflanze heute viel Wasser."));
  assert.ok(!watered(r), "german 'Wasser' bypass");
});
test("A8 missing reading entirely (empty array) + assistant says water", async () => {
  const r = await run(plant(), [], mild, llm("a", "watering", "Water the plant now."));
  assert.ok(!watered(r)); assert.ok(r.notes.includes("no_fresh_reading"));
});
test("A9 null moisture reading + stale reading both ignored", async () => {
  const r = await run(plant(), [...rd(null), ...rd(10, 7 * 3600e3)], mild, llm("a", "watering", "Water now."));
  assert.ok(!watered(r));
});
test("A10 missing forecast (weather throws), outdoor plant, fertilise + water on dry soil", async () => {
  const r = await run(plant({ locationType: "garden" }), rd(10), new Error("down"), llm("f", "fertilising", "Fertilise heavily today."));
  assert.ok(!r.tips.some((t: Tip) => effective(t).fertilising));
  assert.ok(r.notes.some((n: string) => n.startsWith("weather_unavailable")));
});
test("A11 missing city -> no forecast; indoor fertilise allowed in summer, outdoor not", async () => {
  const i = await run(plant({ city: null }), rd(50), mild); assert.ok(i.tips.some((t: Tip) => t.id === "fertilise"));
  const o = await run(plant({ city: null, locationType: "balcony" }), rd(50), mild); assert.ok(!o.tips.some((t: Tip) => t.id === "fertilise"));
});
test("A12 boundary: reading exactly 6h old accepted, 6h+1ms rejected, future by 1ms rejected, exactly now accepted", () => {
  assert.equal(currentMoisture([{ ts: new Date(Date.parse(NOW) - 6 * 3600e3).toISOString(), moisturePct: 5 }], NOW), 5);
  assert.equal(currentMoisture([{ ts: new Date(Date.parse(NOW) - 6 * 3600e3 - 1).toISOString(), moisturePct: 5 }], NOW), null);
  assert.equal(currentMoisture([{ ts: new Date(Date.parse(NOW) + 1).toISOString(), moisturePct: 5 }], NOW), null);
  assert.equal(currentMoisture([{ ts: NOW, moisturePct: 0 }], NOW), 0);
  assert.equal(currentMoisture([{ ts: NOW, moisturePct: 100 }], NOW), 100);
  assert.equal(currentMoisture([{ ts: NOW, moisturePct: 100.01 }], NOW), null);
  assert.equal(currentMoisture([{ ts: NOW, moisturePct: -0.01 }], NOW), null);
  assert.equal(currentMoisture([{ ts: "garbage", moisturePct: 50 }], NOW), null);
});
test("A13 boundary: moisture == dry threshold is NOT dry; == wet threshold IS saturated; thresholds 0/100", () => {
  const s = (m: number, p = plant()) => deriveState(p, rd(m), mild, NOW);
  assert.equal(s(25).dry, false); assert.equal(s(24.99).dry, true);
  assert.equal(s(85).saturated, true); assert.equal(s(84.99).saturated, false);
  assert.equal(s(100, plant({ dryThresholdPct: 0, wetThresholdPct: 100 })).saturated, true);
  assert.equal(s(0, plant({ dryThresholdPct: 0, wetThresholdPct: 100 })).dry, false);
});
test("A14 boundary: forecast exactly 2C frost, 2.01 not; 30C heat, 29.99 not; 5mm rain, 4.99 not", () => {
  const d = (f: Partial<Forecast>) => deriveState(plant({ locationType: "garden" }), rd(20), { ...mild, ...f }, NOW);
  assert.equal(d({ minTempC: 2 }).frost, true); assert.equal(d({ minTempC: 2.01 }).frost, false);
  assert.equal(d({ maxTempC: 30 }).heat, true); assert.equal(d({ maxTempC: 29.99 }).heat, false);
  assert.equal(d({ rainMm: 5 }).rainExpected, true); assert.equal(d({ rainMm: 4.99 }).rainExpected, false);
});
test("A15 malformed forecast from provider (NaN temps) must not be read as benign for outdoor watering", async () => {
  const r = await run(plant({ locationType: "garden" }), rd(10), { ...mild, minTempC: NaN, rainMm: NaN });
  assert.ok(!watered(r), "NaN forecast treated as no frost/rain, watering advised");
});
test("A16 provider returns {} (missing fields) for outdoor plant on dry soil", async () => {
  const r = await run(plant({ locationType: "garden" }), rd(10), {} as Forecast);
  assert.ok(!watered(r), "empty forecast object treated as benign");
});
test("A17 outdoor+frost+assistant says 'Leave it outside overnight' / storm 'Put it on the balcony'", async () => {
  const r = await run(plant({ locationType: "balcony" }), rd(50), { ...mild, minTempC: -3, stormWarning: true }, llm("o", "placement", "Leave it outside overnight to harden off."));
  assert.ok(!r.tips.some((t: Tip) => t.id === "llm-o"));
});
test("A18 non-boolean premium ('true' string, 1) rejected", async () => {
  for (const p of ["true", 1, undefined, null]) await assert.rejects(generateTips({ plant: plant(), readings: [], now: NOW, premium: p as never }, { weather: { forecast: () => Promise.resolve(mild) } }), { code: "premium_required" });
});

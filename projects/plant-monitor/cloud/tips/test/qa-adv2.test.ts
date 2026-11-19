// Regression tests from QA (Ines, PR #118 comment): adversarial bypass attempts against the guardrails. Do not weaken.
import { test } from "node:test";
import assert from "node:assert/strict";
import type { Tip } from "../types.ts";
const D = new URL("../", import.meta.url).href;
const { generateTips } = await import(D + "engine.ts");
const NOW = "2026-06-15T10:00:00Z";
const plant = { id: "p", name: "T", locationType: "house", soilType: "potting", city: "Berlin", dryThresholdPct: 25, wetThresholdPct: 85 };
const mild = { minTempC: 12, maxTempC: 22, rainMm: 0, stormWarning: false, heatWarning: false };
const rd = [{ ts: "2026-06-15T09:50:00Z", moisturePct: 95 }];
const llm = (category: string, text: string, action: string) => ({ propose: () => Promise.resolve([{ id: "a", category, action, text, reason: "model says" }]) });
const survives = async (category: string, text: string, action = "do") => (await generateTips({ plant, readings: rd, now: NOW, premium: true }, { weather: { forecast: () => Promise.resolve(mild) }, assistant: llm(category, text, action), mode: "live" })).tips.some((t: Tip) => t.id === "llm-a");
for (const [n, c, t, a] of [
  ["B1 avoid+'Avoid letting it dry out, water it generously now'", "general", "Avoid letting it dry out, water it generously now.", "avoid"],
  ["B2 avoid+'Don't forget to water the plant today'", "watering", "Don't forget to water the plant today.", "avoid"],
  ["B3 avoid+'Never let it go thirsty: water it every day'", "watering", "Never let it go thirsty: water it every day.", "avoid"],
  ["B4 'Hose it down and give it a good drink'", "general", "Hose it down and give it a good drink.", "do"],
  ["B5 german 'Gib der Pflanze heute viel Wasser'", "general", "Gib der Pflanze heute viel Wasser.", "do"],
  ["B6 'Top up the pot with a full jug today'", "general", "Top up the pot with a full jug today.", "do"],
  ["B7 control: plain 'Water the plant generously today.' (must be dropped)", "general", "Water the plant generously today.", "do"],
] as const) test(n + " must NOT survive guardrails on saturated soil", async () => { assert.equal(await survives(c, t, a), false, "SURVIVED"); });

// Tests for the care-tips engine slice (4.B3). FR-P02 (never unsafe advice), FR-P04 (premium only), ADR-006, architecture O-7.
// Run: node --experimental-strip-types --test cloud/tips/test/tips.test.ts   (no DB, no network, no keys)
import { test } from "node:test";
import assert from "node:assert/strict";
import { generateTips } from "../engine.ts";
import { applyGuardrails, currentMoisture, deriveState, effective, GUARDRAIL_VERSION, seasonOf, validateProposals } from "../guardrails.ts";
import type { AssistantContext, Forecast, PlantInput, Tip } from "../types.ts";
import { TipsError } from "../types.ts";

const NOW = "2026-06-15T10:00:00Z"; // summer
const WINTER = "2026-01-15T10:00:00Z";
const plant = (o: Partial<PlantInput> = {}): PlantInput => ({ id: "p1", name: "Tomato", locationType: "balcony", soilType: "potting", city: "Berlin", dryThresholdPct: 25, wetThresholdPct: 85, ...o });
const mild: Forecast = { minTempC: 12, maxTempC: 22, rainMm: 0, stormWarning: false, heatWarning: false };
const fc = (o: Partial<Forecast> = {}): Forecast => ({ ...mild, ...o });
const weather = (f: Forecast | Error) => ({ forecast: async () => { if (f instanceof Error) throw f; return f; } });
const read = (m: number | null, minAgo = 10) => [{ ts: new Date(Date.parse(NOW) - minAgo * 60_000).toISOString(), moisturePct: m }];
const run = (p: PlantInput, readings: ReturnType<typeof read>, f: Forecast | Error, o: { now?: string; premium?: boolean; assistant?: unknown; mode?: "live" | "rule_based"; timeoutMs?: number } = {}) =>
  generateTips({ plant: p, readings, now: o.now ?? NOW, premium: o.premium ?? true }, { weather: weather(f), assistant: o.assistant as never, mode: o.mode, timeoutMs: o.timeoutMs });
const advisesWatering = (tips: Tip[]) => tips.some((t) => effective(t).watering);
const advisesFert = (tips: Tip[]) => tips.some((t) => effective(t).fertilising);
const llm = (items: unknown) => ({ propose: async () => items });
const evil = (id: string, category: string, text: string, action = "do") => ({ id, category, action, text, reason: "because the model said so" });

// ---------- contract: tips carry reason + evidence -------------------------------------------------------------------
test("dry soil -> watering tip with reason and evidence (FR-P02)", async () => {
  const r = await run(plant(), read(18), mild);
  const t = r.tips.find((x) => x.id === "water-now")!;
  assert.equal(t.action, "do"); assert.match(t.reason, /18%.*25%/);
  assert.ok(t.evidence.some((e) => e.kind === "reading" && e.key === "moisturePct" && e.value === 18));
  assert.equal(r.guardrailVersion, GUARDRAIL_VERSION); assert.deepEqual(r.weather, mild);
  for (const x of r.tips) { assert.ok(x.reason.length > 0); assert.ok(x.evidence.length > 0, `${x.id} has evidence`); }
});
test("soil type changes the text (FR-P02 plant + soil type)", async () => {
  const sand = (await run(plant({ soilType: "sand" }), read(18), mild)).tips.find((x) => x.id === "water-now")!;
  const pot = (await run(plant(), read(18), mild)).tips.find((x) => x.id === "water-now")!;
  assert.match(sand.text, /Sandy/); assert.doesNotMatch(pot.text, /Sandy/);
});
test("tips change with weather and season (FR-P02)", async () => {
  const a = await run(plant(), read(50), mild);
  const b = await run(plant(), read(50), fc({ maxTempC: 34, heatWarning: true }));
  assert.ok(!a.tips.some((t) => t.id === "heat-shade")); assert.ok(b.tips.some((t) => t.id === "heat-shade"));
  const w = await run(plant(), read(50), mild, { now: WINTER });
  assert.ok(a.tips.some((t) => t.id === "fertilise")); assert.ok(!w.tips.some((t) => t.id === "fertilise"));
});
test("the newest usable reading wins, in either input order", async () => {
  const old = { ts: "2026-06-15T08:00:00Z", moisturePct: 10 }, fresh = { ts: "2026-06-15T09:50:00Z", moisturePct: 50 };
  for (const rd of [[old, fresh], [fresh, old]]) {
    const r = await generateTips({ plant: plant({ locationType: "house" }), readings: rd, now: NOW, premium: true }, { weather: weather(mild) });
    assert.ok(!advisesWatering(r.tips));
  }
});
test("seasonOf, boundaries", () => {
  assert.equal(seasonOf("2026-03-01T00:00:00Z"), "spring"); assert.equal(seasonOf("2026-02-28T23:59:59Z"), "winter");
  assert.equal(seasonOf("2026-09-01T00:00:00Z"), "autumn"); assert.equal(seasonOf("2026-12-01T00:00:00Z"), "winter");
});

// ---------- guardrails, one test per rule (these are also the mutation targets) ---------------------------------------
test("G-01 never advise watering when the soil is saturated, even if the assistant insists", async () => {
  const r = await run(plant({ locationType: "house" }), read(92), mild, { mode: "live", assistant: llm([evil("w", "watering", "Water the plant generously today.")]) });
  assert.ok(!advisesWatering(r.tips), JSON.stringify(r.tips));
  assert.ok(r.removed.some((x) => x.ruleId === "G-01"));
  assert.ok(r.tips.some((t) => t.id === "water-hold"), "the safe 'do not water' tip is kept");
});
test("G-01 boundary: exactly at the wet threshold is saturated, one below is not", () => {
  const w = (m: number) => deriveState(plant(), read(m), null, NOW);
  assert.equal(w(85).saturated, true); assert.equal(w(84.9).saturated, false);
});
test("G-01 uses the plant's own thresholds", async () => {
  const r = await run(plant({ locationType: "house", wetThresholdPct: 60 }), read(65), mild, { mode: "live", assistant: llm([evil("w", "watering", "Water it now.")]) });
  assert.ok(!advisesWatering(r.tips));
});
test("G-02 no watering outdoors when rain is expected; indoors it is allowed", async () => {
  const out = await run(plant(), read(10), fc({ rainMm: 8 }));
  assert.ok(!advisesWatering(out.tips)); assert.ok(out.removed.some((x) => x.ruleId === "G-02")); assert.ok(out.tips.some((t) => t.id === "rain-skip"));
  const inn = await run(plant({ locationType: "house" }), read(10), fc({ rainMm: 8 }));
  assert.ok(advisesWatering(inn.tips));
  assert.ok(advisesWatering((await run(plant(), read(10), fc({ rainMm: 4.9 }))).tips));
  assert.ok(!advisesWatering((await run(plant(), read(10), fc({ rainMm: 5 }))).tips), "5 mm is the threshold");
});
test("G-03 no watering outdoors with frost forecast (<= 2 C)", async () => {
  const r = await run(plant({ locationType: "garden" }), read(10), fc({ minTempC: 2 }));
  assert.ok(!advisesWatering(r.tips)); assert.ok(r.removed.some((x) => x.ruleId === "G-03")); assert.ok(r.tips.some((t) => t.id === "frost-protect"));
  assert.ok(advisesWatering((await run(plant({ locationType: "garden" }), read(10), fc({ minTempC: 2.1 }))).tips));
  assert.ok(advisesWatering((await run(plant({ locationType: "greenhouse" }), read(10), fc({ minTempC: -3 }))).tips), "greenhouse is not outdoor here");
});
test("G-04 no watering advice without a fresh plausible reading (missing, stale, implausible, future)", async () => {
  const bad = [[], read(null), read(10, 6 * 60 + 1), read(-5), read(120), [{ ts: "2026-06-15T11:00:00Z", moisturePct: 10 }], [{ ts: "garbage", moisturePct: 10 }]];
  for (const rd of bad) {
    const r = await run(plant({ locationType: "house" }), rd as never, mild, { mode: "live", assistant: llm([evil("w", "watering", "Water the plant now.")]) });
    assert.ok(!advisesWatering(r.tips), JSON.stringify(rd)); assert.ok(r.notes.includes("no_fresh_reading"));
    assert.ok(r.tips.some((t) => t.id === "sensor-stale"));
  }
  assert.equal(currentMoisture(read(10, 6 * 60), NOW), 10, "exactly 6 h old is still usable");
});
test("G-05 no watering advice when the soil is not dry (assistant says water, sensor says 50%)", async () => {
  const r = await run(plant({ locationType: "house" }), read(50), mild, { mode: "live", assistant: llm([evil("w", "watering", "Give it a good watering.")]) });
  assert.ok(!advisesWatering(r.tips)); assert.ok(r.removed.some((x) => x.ruleId === "G-05"));
  assert.ok(advisesWatering((await run(plant({ locationType: "house" }), read(24.9), mild)).tips)); // below dry
  assert.ok(!advisesWatering((await run(plant({ locationType: "house" }), read(25), mild)).tips));  // at dry threshold: not dry
});
test("G-06 no fertilising with frost forecast", async () => {
  const r = await run(plant(), read(50), fc({ minTempC: 1 }));
  assert.ok(!advisesFert(r.tips)); assert.ok(r.removed.some((x) => x.ruleId === "G-06"));
});
test("G-07 no fertilising in winter (any location)", async () => {
  const r = await run(plant({ locationType: "house" }), [{ ts: "2026-01-15T09:50:00Z", moisturePct: 50 }], mild, { now: WINTER, mode: "live", assistant: llm([evil("f", "fertilising", "Feed it with plant food now.")]) });
  assert.ok(!advisesFert(r.tips)); assert.ok(r.removed.some((x) => x.ruleId === "G-07"));
});
test("G-08 no fertilising on dry soil", async () => {
  const r = await run(plant({ locationType: "house" }), read(10), mild, { mode: "live", assistant: llm([evil("f", "fertilising", "Add fertiliser today.")]) });
  assert.ok(!advisesFert(r.tips)); assert.ok(r.removed.some((x) => x.ruleId === "G-08"));
});
test("G-09 outdoor fertilising needs a forecast (fail safe when weather is down)", async () => {
  const r = await run(plant(), read(50), new Error("503"));
  assert.ok(!advisesFert(r.tips)); assert.ok(r.removed.some((x) => x.ruleId === "G-09"));
  assert.ok(advisesFert((await run(plant({ locationType: "house" }), read(50), new Error("503"))).tips), "indoors needs no forecast");
});
test("G-10 / G-11 never tell the user to move the plant outside in a storm or in frost", async () => {
  for (const f of [fc({ stormWarning: true }), fc({ minTempC: -1 })]) {
    const r = await run(plant({ locationType: "house" }), read(50), f, { mode: "live", assistant: llm([evil("o", "placement", "Put the plant outside on the balcony for fresh air.")]) });
    assert.ok(!r.tips.some((t) => effective(t).goOutside)); assert.ok(r.removed.some((x) => x.ruleId === "G-10" || x.ruleId === "G-11"));
  }
  const ok = await run(plant({ locationType: "house" }), read(50), mild, { mode: "live", assistant: llm([evil("o", "placement", "Put the plant outside on the balcony for fresh air.")]) });
  assert.ok(ok.tips.some((t) => t.id === "llm-o"), "same advice is fine in mild weather");
});
test("G-12 no direct-sun advice under a heat warning (or max >= 30)", async () => {
  for (const f of [fc({ heatWarning: true }), fc({ maxTempC: 30 })]) {
    const r = await run(plant({ locationType: "house" }), read(50), f, { mode: "live", assistant: llm([evil("s", "placement", "Place it in direct sun on the south-facing window.")]) });
    assert.ok(!r.tips.some((t) => effective(t).directSun)); assert.ok(r.removed.some((x) => x.ruleId === "G-12"));
  }
  const ok = await run(plant({ locationType: "house" }), read(50), fc({ maxTempC: 29.9 }), { mode: "live", assistant: llm([evil("s", "placement", "Place it in direct sun on the south-facing window.")]) });
  assert.ok(ok.tips.some((t) => t.id === "llm-s"));
});

// ---------- adversarial assistant output --------------------------------------------------------------------------------
test("mislabelled category: text says water, category says general -> still caught", async () => {
  const r = await run(plant({ locationType: "house" }), read(95), mild, { mode: "live", assistant: llm([evil("x", "general", "Water the plant until it drips from the pot.")]) });
  assert.ok(!advisesWatering(r.tips));
});
test("mislabelled action: declared 'avoid' but text is positive advice -> still caught", async () => {
  const r = await run(plant({ locationType: "house" }), read(95), mild, { mode: "live", assistant: llm([evil("x", "watering", "Water the plant generously.", "avoid")]) });
  assert.ok(!advisesWatering(r.tips));
});
test("effective(): negated advice is not advice", () => {
  const e = (text: string, action: "do" | "avoid" = "avoid") => effective({ category: "watering", action, text });
  assert.equal(e("Do not water.").watering, false); assert.equal(e("No watering needed right now.").watering, false);
  assert.equal(e("Do not water.", "do").watering, true, "declared 'do' is never trusted as negation");
  assert.equal(e("Water the plant.").watering, true);
});

// ---------- error paths ---------------------------------------------------------------------------------------------------
test("non-premium user gets premium_required, weather is not even called (FR-P04)", async () => {
  let called = 0;
  await assert.rejects(generateTips({ plant: plant(), readings: read(10), now: NOW, premium: false }, { weather: { forecast: async () => { called++; return mild; } } }), (e: TipsError) => e instanceof TipsError && e.code === "premium_required");
  assert.equal(called, 0);
  await assert.rejects(generateTips({ plant: plant(), readings: [], now: NOW, premium: undefined as never }, { weather: weather(mild) }), (e: TipsError) => e.code === "premium_required");
});
test("invalid input is rejected with invalid_input", async () => {
  const bad: Array<[string, Partial<PlantInput> | null, string?]> = [
    ["bad location", { locationType: "moon" as never }], ["bad soil", { soilType: "lava" as never }],
    ["dry >= wet", { dryThresholdPct: 90 }], ["NaN threshold", { wetThresholdPct: NaN }], ["no id", { id: "" }],
  ];
  for (const [name, o] of bad) await assert.rejects(run(plant(o!), read(10), mild), (e: TipsError) => e.code === "invalid_input", name);
  await assert.rejects(run(plant(), read(10), mild, { now: "nope" }), (e: TipsError) => e.code === "invalid_input");
  await assert.rejects(generateTips({ plant: plant(), readings: null as never, now: NOW, premium: true }, { weather: weather(mild) }), (e: TipsError) => e.code === "invalid_input");
});
test("weather provider failure degrades, does not fail; no city also degrades", async () => {
  const r = await run(plant({ locationType: "house" }), read(10), new Error("provider down"));
  assert.ok(r.notes.some((n) => n.startsWith("weather_unavailable:provider down"))); assert.equal(r.weather, null); assert.ok(advisesWatering(r.tips));
  const c = await run(plant({ city: null }), read(10), mild); assert.ok(c.notes.includes("weather_unavailable:no city"));
});
test("assistant failure / timeout / garbage falls back to rule-based tips", async () => {
  const base = (await run(plant({ locationType: "house" }), read(10), mild)).tips.map((t) => t.id);
  const cases: Array<[string, unknown]> = [
    ["throws", { propose: async () => { throw new Error("boom"); } }],
    ["hangs", { propose: () => new Promise(() => {}) }],
    ["not json shape", llm("hello")], ["null", llm(null)],
  ];
  for (const [name, a] of cases) {
    const r = await run(plant({ locationType: "house" }), read(10), mild, { mode: "live", assistant: a, timeoutMs: 30 });
    assert.deepEqual(r.tips.map((t) => t.id), base, name);
    assert.ok(r.notes.some((n) => n.startsWith("assistant_")), name);
  }
});
test("validateProposals rejects bad ids, categories, actions, lengths, markup and links (architecture O-7)", () => {
  const good = evil("a", "general", "Wipe the leaves with a damp cloth.");
  const { ok, rejected } = validateProposals([good, { ...good }, evil("b b", "general", "Valid text here"), evil("c", "magic", "Valid text here"), evil("d", "general", "Valid text here", "maybe"),
    evil("e", "general", "x"), evil("f", "general", "y".repeat(281)), evil("g", "general", "See <b>this</b> now"), evil("h", "general", "Visit https://evil.example"), null, 5]);
  assert.deepEqual(ok.map((x) => x.id), ["a"]); assert.equal(rejected.length, 10);
  assert.deepEqual(validateProposals({}).ok, []);
});
test("rule-based mode ignores an assistant entirely (TIPS_MODE default, A-029)", async () => {
  let called = 0;
  const r = await run(plant(), read(10), mild, { assistant: { propose: async () => { called++; return []; } } });
  assert.equal(called, 0); assert.equal(r.mode, "rule_based"); assert.ok(r.tips.every((t) => t.source === "rules"));
});
test("a harmless assistant tip passes through, marked source=llm", async () => {
  const r = await run(plant({ locationType: "house" }), read(50), mild, { mode: "live", assistant: llm([evil("leaf", "general", "Wipe the leaves with a damp cloth.")]) });
  assert.equal(r.tips.find((t) => t.id === "llm-leaf")?.source, "llm");
});
test("deterministic: same input twice gives identical output", async () => {
  const a = await run(plant(), read(10), fc({ rainMm: 9 })), b = await run(plant(), read(10), fc({ rainMm: 9 }));
  assert.deepEqual(a, b);
});
test("property sweep: over moisture x weather x location x season no result ever advises watering unsafely", async () => {
  const forecasts = [mild, fc({ rainMm: 10 }), fc({ minTempC: -2 }), fc({ stormWarning: true }), fc({ heatWarning: true, maxTempC: 35 })];
  let n = 0;
  for (const loc of ["house", "balcony", "garden", "farm", "greenhouse"] as const)
    for (const m of [0, 10, 24.9, 25, 50, 84.9, 85, 99]) for (const f of forecasts) for (const now of [NOW, WINTER]) {
      const rd = [{ ts: new Date(Date.parse(now) - 600_000).toISOString(), moisturePct: m }];
      const r = await generateTips({ plant: plant({ locationType: loc }), readings: rd, now, premium: true }, { weather: weather(f) });
      const out = loc === "balcony" || loc === "garden" || loc === "farm";
      if (advisesWatering(r.tips)) {
        assert.ok(m < 25, `watering at ${m}%`); assert.ok(!(out && f.rainMm >= 5), "rain"); assert.ok(!(out && f.minTempC <= 2), "frost");
      }
      if (advisesFert(r.tips)) { assert.ok(m >= 25); assert.ok(f.minTempC > 2); assert.ok(now === NOW); }
      n++;
    }
  assert.equal(n, 5 * 8 * 5 * 2);
});
test("applyGuardrails keeps order and loses nothing silently", () => {
  const s = deriveState(plant(), read(95), mild, NOW);
  const mk = (id: string, text: string): Tip => ({ id, category: "general", action: "do", text, reason: "r", evidence: [], source: "llm" });
  const { kept, removed } = applyGuardrails([mk("a", "Dust the leaves."), mk("b", "Water the plant."), mk("c", "Rotate the pot.")], s);
  assert.deepEqual(kept.map((t) => t.id), ["a", "c"]); assert.deepEqual(removed.map((x) => x.tip.id), ["b"]);
});
void ({} as AssistantContext);

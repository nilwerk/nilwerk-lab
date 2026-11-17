#!/usr/bin/env bash
# Mutation check for the care-tips guardrails (FR-P02). Each mutant changes one expression in guardrails.ts/engine.ts/mcp.ts and
# MUST make test/*.test.ts fail ("killed"). A surviving mutant = a rule the tests do not protect: exit 1. Files are restored.
set -uo pipefail
cd "$(dirname "$0")/.."
G=guardrails.ts; E=engine.ts; M=mcp.ts
BK="$(mktemp -d)"; cp "$G" "$BK/g"; cp "$E" "$BK/e"; cp "$M" "$BK/m"
restore() { cp "$BK/g" "$G"; cp "$BK/e" "$E"; cp "$BK/m" "$M"; }
trap 'restore; rm -rf "$BK"' EXIT
run() { node --experimental-strip-types --disable-warning=ExperimentalWarning --test test/*.test.ts >"$BK/out.txt" 2>&1; }
survived=0; total=0
mutant() { # name file old new
  restore
  OLD="$3" NEW="$4" python3 - "$2" <<'PY' || { echo "BAD MUTANT (pattern not found or not unique): $1"; exit 2; }
import os, sys
p = sys.argv[1]; s = open(p).read(); o = os.environ["OLD"]
if s.count(o) != 1: sys.exit(1)
open(p, "w").write(s.replace(o, os.environ["NEW"]))
PY
  total=$((total+1))
  if run; then echo "SURVIVED  $1"; survived=$((survived+1)); else echo "killed    $1  ($(grep -m1 -E '^ *not ok' "$BK/out.txt" | cut -c1-100))"; fi
}
restore; run && echo "baseline ok" || { echo "baseline FAILS"; exit 1; }
mutant "G-01 rule removed (watering on waterlogged soil allowed)" $G 'e.watering && s.saturated ?' 'false && s.saturated ?'
mutant "G-01 saturated uses > instead of >= (boundary)" $G 'moisturePct >= plant.wetThresholdPct' 'moisturePct > plant.wetThresholdPct'
mutant "G-01 saturated ignores plant threshold (hard 95)" $G 'moisturePct >= plant.wetThresholdPct' 'moisturePct >= 95'
mutant "G-02 rain rule applies to indoor too" $G 'e.watering && s.outdoor && s.rainExpected' 'e.watering && s.rainExpected'
mutant "G-02 rain rule removed" $G 'e.watering && s.outdoor && s.rainExpected ?' 'false ?'
mutant "RAIN_MM 5 -> 6" $G 'RAIN_MM = 5;' 'RAIN_MM = 6;'
mutant "G-03 frost rule removed" $G 'e.watering && s.outdoor && s.frost ?' 'false ?'
mutant "FROST_C 2 -> 1" $G 'FROST_C = 2;' 'FROST_C = 1;'
mutant "FROST_C 2 -> 3" $G 'FROST_C = 2;' 'FROST_C = 3;'
mutant "G-04 no-reading rule removed" $G 'e.watering && s.moisturePct === null ?' 'false ?'
mutant "stale limit 6 h -> 12 h" $G 'MAX_READING_AGE_MS = 6 * 3600_000' 'MAX_READING_AGE_MS = 12 * 3600_000'
mutant "stale limit 6 h -> 5 h" $G 'MAX_READING_AGE_MS = 6 * 3600_000' 'MAX_READING_AGE_MS = 5 * 3600_000'
mutant "future reading accepted" $G '|| t > now ||' '||'
mutant "implausible >100 accepted" $G '|| r.moisturePct > 100) continue' ') continue'
mutant "implausible <0 accepted" $G '|| r.moisturePct < 0 ||' '||'
mutant "newest reading not preferred (first wins)" $G 'if (!best || t > best.t)' 'if (!best)'
mutant "G-05 not-dry rule removed" $G 'e.watering && s.moisturePct !== null && !s.dry && !s.saturated ?' 'false ?'
mutant "dry uses <= (boundary)" $G 'moisturePct < plant.dryThresholdPct' 'moisturePct <= plant.dryThresholdPct'
mutant "G-06 fertilise-in-frost removed" $G 'e.fertilising && s.frost ?' 'false ?'
mutant "G-07 winter fertilise removed" $G 'e.fertilising && s.season === "winter" ?' 'false ?'
mutant "G-08 fertilise-dry removed" $G 'e.fertilising && s.dry ?' 'false ?'
mutant "G-09 no-forecast fail-safe removed" $G 'e.fertilising && s.outdoor && s.weather === null ?' 'false ?'
mutant "G-10 storm rule removed" $G 'e.goOutside && s.storm ?' 'false ?'
mutant "G-11 outside-in-frost removed" $G 'e.goOutside && s.frost ?' 'false ?'
mutant "G-12 heat/sun rule removed" $G 'e.directSun && s.heat ?' 'false ?'
mutant "HEAT_C 30 -> 31" $G 'HEAT_C = 30;' 'HEAT_C = 31;'
mutant "text not classified (category only)" $G 'watering: positive && (t.category === "watering" || WATER.test(t.text))' 'watering: positive && t.category === "watering"'
mutant "declared avoid trusted without negation in text" $G 'const negated = t.source !== "llm" && t.action === "avoid" && NEGATION.test(t.text);' 'const negated = t.source !== "llm" && t.action === "avoid";'
mutant "'do not water' counted as advice" $G 'const negated = t.source !== "llm" && t.action === "avoid" && NEGATION.test(t.text);' 'const negated = false;'
mutant "applyGuardrails keeps everything" $G 'if (hit) removed.push({ tip, ...hit }); else kept.push(tip);' 'kept.push(tip);'
mutant "first rule (G-01) skipped in the loop" $G 'for (const r of RULES) {' 'for (const r of RULES.slice(1)) {'
mutant "assistant output not validated" $G 'if (!Array.isArray(raw)) return { ok, rejected: ["not an array"] };' 'if (!Array.isArray(raw)) return { ok, rejected: [] };'
mutant "markup/link check removed" $G 'else if (/[<>]|https?:|www\.|\bjavascript:/i.test(text + reason)) bad = "markup or link in text";' ''
mutant "duplicate ids accepted" $G '|| ids.has(id)' ''
mutant "premium check removed (FR-P04)" $E 'if (!req || req.premium !== true)' 'if (!req)'
mutant "premium check: truthy instead of === true" $E 'req.premium !== true' '!req.premium && req.premium !== undefined'
mutant "threshold order check removed" $E '|| p.dryThresholdPct >= p.wetThresholdPct' ''
mutant "weather failure propagates" $E 'notes.push(`weather_unavailable:${(e as Error).message}`); }' 'throw e; }'
mutant "assistant failure propagates" $E 'notes.push(`assistant_failed:${(e as Error).message}`); return [];' 'throw e;'
mutant "assistant tips bypass guardrails" $E 'applyGuardrails(candidates, s)' 'applyGuardrails(base, s)'
mutant "live mode ignored flag: assistant used in rule_based" $E 'if (mode === "live" && deps.assistant)' 'if (deps.assistant)'
mutant "guardrail results dropped (tips = candidates)" $E 'tips: kept,' 'tips: candidates,'
mutant "N-1 assistant negation excuses text again" $G 'const negated = t.source !== "llm" && t.action' 'const negated = t.action'
mutant "N-1 llm source check inverted (rules tips never negated)" $G 't.source !== "llm" && t.action' 't.source === "llm" && t.action'
mutant "N-2 keyword 'drink' removed" $G '|drink|jug|' '|'
mutant "N-2 keyword 'jug' removed" $G '|drink|jug|' '|drink|'
mutant "N-2 keyword 'hose' removed" $G '|hose\w*|' '|'
mutant "N-2 keyword 'top up' removed" $G '|top(ping)? up|' '|'
mutant "N-2 German 'wasser' removed" $G '|wasser|' '|'
mutant "N-2 'pour' removed" $G '|pour\w*|' '|'
mutant "N-2 German 'duengen' stem removed" $G '|d(ü|ue)ng|' '|'
mutant "N-3 forecast validation removed" $E 'if (validForecast(f)) weather = f;' 'weather = f as Forecast;'
mutant "N-3 NaN allowed (finite check dropped)" $G 'typeof v === "number" && Number.isFinite(v);' 'typeof v === "number";'
mutant "N-3 boolean flags not required" $G '&& typeof o.stormWarning === "boolean" && typeof o.heatWarning === "boolean"' ''
mutant "N-3 null forecast object accepted" $G 'if (typeof f !== "object" || f === null) return false;' 'if (typeof f !== "object") return false;'
mutant "G-13 outdoor watering without forecast allowed" $G 'e.watering && s.outdoor && s.weather === null ?' 'false ?'
mutant "C1 fertilising not mapped to feeding" $M 'fertilising: "feeding"' 'fertilising: "fertilising" as McpCategory'
mutant "C1 protection mapped outside enum" $M 'protection: "safety"' 'protection: "protection" as McpCategory'
mutant "C1 text not truncated" $M 't.text.slice(0, MCP_TEXT_MAX)' 't.text'
mutant "C1 frost id refinement dropped" $M '"frost-protect": "temperature", ' ''
mutant "C2 guardrail_version not exposed on row" $M 'guardrail_version: r.guardrailVersion || GUARDRAIL_VERSION' 'guardrail_version: ""'
mutant "C-a guardrail version not bumped" $G 'GUARDRAIL_VERSION = "g1.1"' 'GUARDRAIL_VERSION = "g1.0"'
mutant "C-b neutral tip not added when G-13 fires" $E 'if (!removed.some((x) => x.ruleId === "G-13")) return;' 'return;'
mutant "C-b neutral tip added without G-13 (always)" $E 'if (!removed.some((x) => x.ruleId === "G-13")) return;' ''
mutant "C-b neutral tip bypasses guardrail re-check" $E 'applyGuardrails([tip], s)' '{ kept: [tip], removed: [] as typeof removed }'
mutant "C-b neutral tip becomes a watering instruction" $E 'text: "No forecast available: check the soil by finger."' 'text: "No forecast available: water the soil by finger."'
echo "mutants: $total, survived: $survived"
[ "$survived" -eq 0 ] && echo "ALL MUTANTS KILLED" || exit 1

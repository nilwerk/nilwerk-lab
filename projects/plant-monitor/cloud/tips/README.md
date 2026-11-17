# Care-tips engine (4.B3)

Requirements: FR-P02 (tips from location, weather, season, plant + soil, readings; never unsafe), FR-P04 (premium), ADR-006.
Run tests: `node --experimental-strip-types --test cloud/tips/test/*.test.ts`; mutation check: `bash cloud/tips/test/mutation.sh`.

## Thresholds (approved)
Arsany approved the guardrail thresholds on 2026-11-17 (decision A-105): frost <= 2 C, heat >= 30 C (or heat warning),
rain >= 5 mm / 24 h, reading freshness 6 h, dry < 25 % and wet >= 85 % soil moisture (per-plant overridable), as in `guardrails.ts`.
Changing any of them is a new decision and a `GUARDRAIL_VERSION` bump.

## Contracts
- `mcp.ts` maps the engine result to `docs/interfaces/mcp-tools.json` get_tips (`items[{id,category,text}]`, category enum
  watering|light|temperature|feeding|safety|other) and to the `public.tips` row (`guardrail_version` = `GUARDRAIL_VERSION`).
- Not in the contract (kept internal): `action` (do/avoid), `reason`, `evidence`. Proposal for an ADR: add optional `action`
  and `reason` to the items (additive, non-breaking) so MCP clients can show why.

## Assistant output policy
Assistant text is untrusted: schema-validated, then classified by keywords (EN/DE, synonyms). A negation word or a declared
`avoid` never excuses assistant text; a matching tip is judged as advice. Provider forecasts must be complete and finite, else
"no forecast". Residual risk: keyword lists are a deny-list; an allow-list (assistant may only rephrase baseline tips) is the
stricter option if QA finds more bypasses.

## Guardrail version g1.1
`g1.1` (was `g1.0`): G-13 (no outdoor watering advice without a valid forecast) and the rewritten text classifier change which tips are
removed. When G-13 removes a watering tip, the engine adds a rules-sourced neutral tip `no-forecast-check-soil`
("No forecast available: check the soil by finger."). It is re-checked by the guardrails like every tip and must never read as a
watering instruction (tests + mutants C-b).

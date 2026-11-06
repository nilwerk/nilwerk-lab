# ADR-006: Tips = weather API + Claude API + deterministic safety rules

Status: Proposed for G2 (follows Q-13) · Date: 2026-11-03 · Deciders: Arsany (Q-13), Theo, Sana

## Context
FR-P02: tips change with weather/season input and must never be unsafe.

## Decision
Edge function builds a prompt from plant, soil, place, season, forecast and recent readings, and requests schema-constrained JSON from Claude. A deterministic rule layer, owned in code and fully unit-tested, runs after the model: it removes or rewrites advice that conflicts with rules (e.g. watering while waterlogged, fertilising at frost, outdoor moves in storm warnings) and always wins. Output is cached per plant for hours. Only pseudonymous data is sent (no user identity, city only). The weather provider is an adapter; the choice is made in 2.6 (free tier, licence check).

**Mode flag (A-029, 2026-11-06).** The tips engine has two switchable modes behind one flag, `TIPS_MODE` (edge-function secret / config, default `rule_based`):
- `rule_based` (default, **demo**): canned tips selected by the deterministic rule layer from plant, soil, season, weather and readings; no LLM call, cost 0, no data leaves the EU, same output schema.
- `live`: the Claude path above, followed by the same rule layer. Used when a paying customer needs richer tips; changing the flag takes effect on the next refresh, no deploy.
The rule layer and its guardrail tests (FR-P02) run in both modes; `live` only adds the model step in front of it. Cost: `rule_based` = 0, `live` = see `stack-and-costs.md` (`demo_tips_mode`).

## Alternatives
Rules only (no LLM): safe but fails "care tips" richness. LLM only: violates the guardrail requirement.

## Consequences
+ Testable safety. - Data leaves the EU (risk O-5, needs Arsany A-1); cost per premium user goes to 2.6.

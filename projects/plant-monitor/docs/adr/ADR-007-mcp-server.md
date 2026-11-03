# ADR-007: MCP server as an edge function with personal API keys

Status: Accepted for G2 review · Date: 2026-11-03 · Deciders: Theo, Sana

## Context
FR-P03: tools `list_plants`, `get_plant_status`, `get_history`, `get_tips`; revocable key; NFR-06.

## Decision
Remote MCP server (Streamable HTTP) in TypeScript on Supabase Edge Functions. Keys are random, shown once, stored hashed, mapped to one user; all tools read-only; each call checks the premium flag (ADR-008). Data access goes through SQL RPCs keyed by the verified user, not an unrestricted service-role client. Revoking deletes the hash.

## Alternatives
Local stdio server: users would need to run code; fails the "favourite AI" use case. OAuth: nicer, more work; out of demo scope, noted for client projects.

## Consequences
Rate limits per key needed (to be set in 2.4). Tool schemas are a contract in `docs/interfaces/mcp-tools.json`.

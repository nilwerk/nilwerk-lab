# ADR-003: Supabase EU as the standalone backend; ingest as an edge function

Status: Accepted (follows Q-04, Q-12) · Date: 2026-11-03 · Deciders: Arsany (Q-04/Q-12), Theo

## Context
Standalone cloud with accounts (Q-04); EU hosting and deletion/export (NFR-07); RLS (NFR-06); data visible <= 2 min (NFR-04); TypeScript across edge functions and MCP (TEAM.md §6).

## Decision
Supabase EU region: Postgres + RLS, Auth, Storage, Realtime, pg_cron, Edge Functions (TypeScript). Devices never access tables directly; they call `/ingest` which validates the device token and writes with the service role inside the function. The app uses supabase-js directly for CRUD under RLS and edge functions for claim/release/delete/export, tips, analytics.

## Alternatives
- Firebase: rejected in Q-12. - Home Assistant as hub: rejected in Q-04. - Dedicated server (Node/Fly): more ops, no RLS/Auth for free.

## Consequences
+ One platform, one language, EU. - Edge function limits (time, memory) shape tips/analytics design; service-role code must be small and reviewed. Details of schema and API: task 2.4.

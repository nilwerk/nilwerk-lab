# ADR-008: Premium is a server-side per-user flag, no payments

Status: Accepted (follows Q-14) · Date: 2026-11-03 · Deciders: Arsany (Q-14), Theo

## Context
FR-P04; payments are out of scope (Req §8).

## Decision
A boolean `is_premium` on the user profile, changeable only by service role or an admin tool (not by the user via RLS). Tips, analytics and MCP functions check it on every call; the app only uses it to show or hide UI.

## Alternatives
Client-side gating only: trivially bypassed, fails FR-P01 "free user cannot open".

## Consequences
Replacing the flag with a billing provider later changes one function. Enforcement points: C-09, C-10, C-11 (and RLS on premium-only views).

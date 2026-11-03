# ADR-005: React Native (Expo) + TypeScript, supabase-js under RLS

Status: Accepted (follows Q-03) · Date: 2026-11-03 · Deciders: Arsany (Q-03), Theo

## Context
FR-A01..A08, FR-P01..P04 UI, NFR-03. One language across app, edge functions and MCP.

## Decision
Expo (development build with config plugins for BLE provisioning and notifications), TypeScript, supabase-js for auth/CRUD/Realtime under RLS. The app contains no secrets other than the public anon key. Premium screens call edge functions; the flag is also enforced server-side (ADR-008).

## Alternatives
Flutter: equivalent performance, but no shared language and a less maintained ESP provisioning plugin (Q-03).

## Consequences
Dev build required for BLE; app-store release is out of scope (Req §8), distribution via TestFlight/internal builds is for task 4.A/5.x to settle.

# ADR-014: App palette, brand mark and status colours

Status: Accepted (owner decision 2026-11-07, A-040, answer 2) · Date: 2026-11-08 · Deciders: Arsany (decision), Theo (record) · Amends: nothing in the contracts; supersedes the wireframe palette for the built app

## Context
Leo's app wireframes (PR #19) use their own palette. The approved v0.1 brand kit (`showcase/brand/`) defines a different one and ships a typed app theme (`showcase/brand/app/theme.ts`, `tokens.json`), status tokens (`showcase/brand/brand-status.css`), an icon and splash set. FR-A01..A08 screens (task 4.A2/4.A3) need one palette. Differences are listed in `showcase/brand/app/WIREFRAME-MAPPING.md`. The owner answered A-040 on 2026-11-07 as recommended.

## Decision
1. **The app uses the aligned palette** from `showcase/brand/app/theme.ts` / `tokens.json` and the status tokens in `showcase/brand/brand-status.css` (single source: `brand.css` + `brand-status.css`; `tokens.json` is generated from them). The wireframe palette is not used in the built app.
2. **Brand mark as app identity:** the dark plate with the trace-N mark is the app icon (`icon-1024.png`, Android adaptive foreground with real alpha) and the splash (light and dark), wired through `app.json` and the `expo-splash-screen` plugin as in `showcase/brand/app/README.md`.
3. **Status colours** (ok, dry, wet, lowBattery, offline, error) come from `brand-status.css` / `theme.ts` (`statusStyle`). A status is never shown by colour alone: always a word plus a shape. Contrast is checked by `showcase/brand/check_status_contrast.py` (WCAG AA).
4. **Mapping of alerts to statuses** is the table in `showcase/brand/app/README.md` (FR-A07 owns thresholds and timing; not repeated here). `ok` = no open alert.

## Alternatives
- Keep the wireframe palette: two palettes in one product, no checked contrast, icon and splash off-brand. Rejected by the owner.
- Derive a new app-only palette: duplicates the brand kit. Rejected.

## Consequences
+ One source for web, slides and app; contrast checked in CI-able scripts; plain, bilingual status labels.
- Tasks 4.A2 and 4.A3 build on `theme.ts` (copy `theme.ts`, `tokens.json`, `assets/` into the app; the Expo config keys must be re-checked against the Expo SDK in use, they were never run in an app).
- The app needs `en.json` (and `de.json`) keys `status.ok`, `status.dry`, `status.wet`, `status.lowBattery`, `status.offline`, `status.error`; labels in plain words.
- The wireframes (`projects/plant-monitor/app/wireframes/`) keep the old palette as a historical design artefact; they are not updated.
- If the brand tokens change, `theme.ts` and `tokens.json` are regenerated, not edited by hand.

## Open decision for 4.A2 (Leo, Theo reviews)
The edge-AI alert kinds `wetting_unexpected`, `waterlogged`, `sensor_out_of_soil` and `sensor_fault` (FR-A07) have no status of their own. Either map them to the existing `error` key (simplest, red cross, one extra word in the label), or add a new key (for example `status.attention`) with its own colour and shape, which needs a contrast check and a token in `brand-status.css`. Not decided here; the priority order when several alerts are open is also still a proposal (README, section "Alerts to statuses"). Decide in the 4.A2 PR.

## Source
Owner decision 2026-11-07 (A-040, answer 2; `team/reports/2026-11-07.md`, extra round 5). FR-A01..A08, FR-A07.

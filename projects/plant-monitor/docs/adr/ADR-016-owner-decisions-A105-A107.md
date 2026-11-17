# ADR-016: Owner decisions A-105, A-106, A-107 (tips thresholds, export before delete)

Status: Accepted (Arsany; A-105, A-106, A-107 as given to the Theo task by the Lead on 2026-11-17; original answer text not in this repo) · Date: 2026-11-17 · Deciders: Arsany (decision), Theo (record)
Place: `docs/decisions/` is empty; accepted decisions in this repo live as ADRs in `docs/adr/` (see ADR-011, ADR-015). The Questions tab remains the source of the original answers; this file only records them (TEAM.md section 9).

## Decisions
1. **A-105 (FR-P02, 4.B3):** care-tips guardrail thresholds approved on 2026-11-17: frost <= 2 C, heat >= 30 C (or heat warning), rain >= 5 mm / 24 h, reading freshness 6 h, dry < 25 % and wet >= 85 % soil moisture (per-plant overridable). Single source: constants in `cloud/tips/guardrails.ts` (`FROST_C`, `HEAT_C`, `RAIN_MM`, `MAX_READING_AGE_MS`); text in `cloud/tips/README.md`. Changing one is a new decision and a `GUARDRAIL_VERSION` bump.
2. **A-106 (NFR-07, FR-A01, 4.A9):** no "skip export" option. Delete stays blocked until the user really received the export (file written, share sheet used, user confirmed). Code: `app/src/export/exportGate.ts`, `fileHandOff.ts`.
3. **A-107 (NFR-07, FR-A01, 4.A9):** option (b): the app downloads the photos before the delete button unlocks. Not yet in code: `app/src/export/exportClient.ts` only counts photos from the JSON export. Owner: Leo (app), with Sana for the photo URLs (4.B2c). Needs a test that the gate stays closed until photo files are saved.

## Consequences
- A-105 values are cited, not retyped, by other documents (playbook: one source per contract value).
- A-106 and A-107 together make delete a three-step gate: export file received, photos saved, exact name typed. The `/export` edge function does not exist yet (task 4.B2c), so on a live project delete is blocked until it does.

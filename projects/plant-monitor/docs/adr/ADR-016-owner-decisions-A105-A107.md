# ADR-016: Owner decisions A-105, A-106, A-107 (tips thresholds, export before delete)

Status: Accepted (Arsany, 2026-11-17, sheet answers quoted below) · Date: 2026-11-17 · Deciders: Arsany (decision), Theo (record)
Place: `docs/decisions/` is empty; accepted decisions in this repo live as ADRs in `docs/adr/` (see ADR-011, ADR-015). Source of the owner's answers: Google Sheet id `1jMOJ6xobyxt3_gUw53l5tN0n2tA5wimcgU8V84_QfPA`, tab `Needs Arsany`, column "Your answer / outcome", rows A-105 (sheet row 106), A-106 (row 107), A-107 (row 109), all Status Done. This file records them (TEAM.md section 9); the sheet stays the source.

## Decisions

### A-105 (FR-P02, task 4.B3): care-tips thresholds
**Owner decision**, verbatim: "2026-11-17 Arsany: approve the proposal. Thresholds accepted as proposed for the demo (frost <= 2 C, heat >= 30 C, rain >= 5 mm, readings older than 6 h ignored, winter Dec-Feb). Lead: Theo/Sana record them as agreed in the tips README in the next 4.B3 slice."
The owner approved only: frost <= 2 C, heat >= 30 C, rain >= 5 mm (per 24 h in the question), readings older than 6 h ignored, winter = Dec-Feb (northern hemisphere), all "for the demo".
**Implementation (engineering, not owner decisions):** constants in `cloud/tips/guardrails.ts` (`FROST_C`, `HEAT_C`, `RAIN_MM`, `MAX_READING_AGE_MS`), text in `cloud/tips/README.md`; changing an approved value is a new decision and a `GUARDRAIL_VERSION` bump.
**Engineering defaults, NOT approved by the owner** (they come from the tips README/code; the A-105 question did not list them): dry < 25 % and wet >= 85 % soil moisture (per-plant overridable), and the "heat warning" trigger as an alternative to the 30 C threshold. Changeable by engineering; they need no owner decision unless the owner asks for one.

### A-106 (NFR-07, FR-A01, task 4.A9): no skip export
**Owner decision**, verbatim: "2026-11-17 Arsany: approve the proposal. No skip-export option (data-loss risk, GDPR). Lead: new Plan task 4.A9 real GET /export client + file hand-off added; delete stays blocked until export succeeds."
**Implementation:** the delete stays blocked until the user really received the export: file written, share sheet used, user confirmed "I saved it" (`app/src/export/exportGate.ts`, `fileHandOff.ts`); delete also needs the typed name or word.

### A-107 (NFR-07, FR-A01, task 4.A9b): photos downloaded before delete
**Owner decision**, verbatim: "2026-11-17 Arsany: accept the recommendation, option (b): the app downloads the photos before delete unlocks, so the export is a complete archive. Lead: new Plan task 4.A9b (Leo) for the photo download; 4.B2c (Sana) export function spec stays signed photo URLs (app downloads them before delete)."
**Implementation:** task 4.A9b (Leo), **not built yet**: `app/src/export/exportClient.ts` (4.A9) only counts photos from the JSON export. Signed photo URLs come from the export function (4.B2c, Sana). Needs a test that the gate stays closed until photo files are saved.

## Consequences
- A-105 values are cited, not retyped, by other documents (playbook: one source per contract value).
- A-106 and A-107 together make delete a three-step gate: export file received, photos saved, exact name typed. The `/export` edge function does not exist yet (task 4.B2c), so on a live project delete is blocked until it does.

# ADR-013: Data model and API conventions (task 2.4)

Status: Proposed for G2 · Date: 2026-11-04 · Deciders: Theo (Arsany for the G1 constants, already answered on PR #2) · Amends: architecture.md section 5, ADR-012, ADR-008 (detail only)

## Context
Contracts in `docs/interfaces/` need a few decisions the earlier ADRs left open (architecture D-1..D-8). FR-D01, FR-D02, FR-D04, FR-A07, FR-A08, FR-P01, FR-P04, NFR-06, NFR-07.

## Decision
1. **Unit of record is the 15-min sample**; the report is a batch of up to 192 samples; `(device_id, ts)` dedupes. (FR-D04)
2. **Plausible ranges are flags, not rejections** (`plausible=false`). (FR-D01)
3. **Claim is a separate endpoint** `/device-claim` using the one-time claim token; `/ingest` accepts only the device token. This changes architecture section 5 step 5 ("calls /ingest once with the claim token"). (FR-D03, ADR-002)
4. **History is owned by the owner at record time** (`owner_id` on readings, events, alerts); release revokes the token and clears `devices.owner_id`; history stays with the previous owner. (FR-A08)
5. **Premium** is `profiles.is_premium`, guarded by trigger, enforced in RLS on `readings` (7-day window for free) and `tips`, in the key endpoint and in `mcp_resolve_key()`. (ADR-008 unchanged in substance.)
6. **Offline = 3 missed hourly reports** (last report older than 3 h 10 min); replaces the 2.5 h proposal in architecture D-6 and ADR-012. (G1)
7. **Retention (NFR-13, A-028; supersedes the G1 "12 months raw, no roll-up" choice, which A-025 made unaffordable on one free database):** raw 15-min readings ~3 months, then an **hourly roll-up table** (`readings_hourly`: count, avg/min/max moisture, avg temp/rh/lux, min vbat; plausible samples only) kept 12 months; daily values are a view over it (`readings_daily`). `rollup_readings()` runs hourly; `apply_retention()` runs nightly, rolls up every expiring hour first, then deletes raw rows older than 3 months and roll-up rows older than 12 months (replaces `purge_old_readings()`; roll-up never shrinks). Month counts are parameters, not constants spread over the code. Charts of 30/90 days use raw/hourly, the 12-month chart uses daily. Free users keep the 7-day window on the roll-up too.
8. **OTA integrity = SHA-256 over TLS**; image signing is a follow-up and needs its own ADR. (G1, A-009; ADR-009 unchanged)
9. **No MQTT Last-Will** on the device-to-hub link; the hub derives offline from silence, because clean disconnects never fire a LWT. Hub identity is `hw_id`. (ADR-012 amended)
10. **Deleting a plant deletes its photos, readings, events, alerts and tips** after a warning with JSON/CSV export first; the sensor stays claimed and is released separately (`delete_plant()`, `DELETE /plants/{id}`). Arsany A-022. (FR-A08, NFR-07)

## Alternatives
- Reject out-of-range samples: loses the rest of the batch and breaks FR-D04. Rejected.
- Claim inside `/ingest`: mixes two auth modes in one endpoint. Rejected.
- Readings keyed only by device with RLS through `devices.owner_id`: a new owner would see the old owner's history. Rejected.
- Hourly roll-up tables: no benefit at 3 units; revisit if charts are slow.

## Consequences
+ One predicate per RLS policy, retry-safe ingest, testable premium gate. - `owner_id` is denormalised and must be stamped by the ingest function; six tables beyond the Plan's seven. Arch/ADR text updated for items 3, 6, 9 in the same PR where marked.

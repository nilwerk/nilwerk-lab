# ADR-004: Per-device bearer token, stored hashed

Status: Accepted for G2 review · Date: 2026-11-03 · Deciders: Theo

## Context
NFR-06 requires per-device credentials over TLS; FR-A08 requires release/re-claim; secrets must not be in the repo.

## Decision
Each device gets a random 256-bit token at claim time, stored in NVS on the device and as a SHA-256 hash in the DB. `/ingest` accepts `Authorization: Bearer`. Compromise or release revokes by deleting the hash. TLS with pinned CA bundle on the device. No shared fleet key, no secrets in firmware images.

### Addendum 2026-11-28: upload TLS must use the pinned CA bundle (NFR-06, owner row A-155)
Required behaviour: the device trusts only the pinned CA bundle defined for this ADR, not the full ESP-IDF certificate bundle. The current firmware does not do this (finding F-01): `projects/plant-monitor/firmware/components/upload/src/nw_upload_idf.c:142` sets `.crt_bundle_attach = esp_crt_bundle_attach`, which trusts the full bundle. This ADR records the requirement only; no code is changed here. Mira fixes the code in a separate PR. No owner decision accepts this gap: the A-155 accepted risk below covers token storage in flash, not the TLS trust store.

## Alternatives
- Per-device X.509 client certificates: stronger but needs a CA and provisioning line; excessive for 3 units (revisit for a client project).
- Shared API key: violates NFR-06.

## Consequences
+ Simple and revocable. - Token readable from flash of a physical unit (no flash encryption planned; see open question Q-H6 in `docs/architecture.md` section 10.4).
- **Owner decision A-155 (2026-11-28, Arsany, NFR-06):** the device token stored in flash without flash encryption is an **accepted risk for the v1 demo**, because all three units are owned by Arsany. **Flash encryption becomes a required task before the first customer unit** (open point Q-H6 in `docs/architecture.md` section 10.4). No customer unit ships without it.

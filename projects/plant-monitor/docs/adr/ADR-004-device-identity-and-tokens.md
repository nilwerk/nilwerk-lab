# ADR-004: Per-device bearer token, stored hashed

Status: Accepted · Date: 2026-11-03 · Deciders: Theo

## Context
NFR-06 requires per-device credentials over TLS; FR-A08 requires release/re-claim; secrets must not be in the repo.

## Decision
Each device gets a random 256-bit token at claim time, stored in NVS on the device and as a SHA-256 hash in the DB. `/ingest` accepts `Authorization: Bearer`. Compromise or release revokes by deleting the hash. TLS with pinned CA bundle on the device. No shared fleet key, no secrets in firmware images.

## Alternatives
- Per-device X.509 client certificates: stronger but needs a CA and provisioning line; excessive for 3 units (revisit for a client project).
- Shared API key: violates NFR-06.

## Consequences
+ Simple and revocable. - Token readable from flash of a physical unit (no flash encryption planned; see risk O-3).

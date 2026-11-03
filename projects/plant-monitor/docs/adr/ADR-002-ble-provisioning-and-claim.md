# ADR-002: BLE provisioning with proof-of-possession and one-time claim token

Status: Accepted for G2 review; amendment proposed by ADR-011 · Date: 2026-11-03 · Deciders: Theo (Arsany informed)

## Context
FR-D03, FR-A03, FR-A08, NFR-03, NFR-06, UC-02. Device must get Wi-Fi credentials, a name, and be bound to exactly one user, set up in <= 3 min on iOS and Android.

## Decision
Use ESP-IDF `wifi_provisioning` over BLE (protocomm, security with proof-of-possession from the label/QR) plus one custom endpoint for name and claim token. The app obtains a single-use, short-lived claim token from the cloud (user-bound). The device presents it on its first `/ingest` call and receives its per-device token (ADR-004). Release revokes the token and clears the owner; factory reset clears NVS.

## Alternatives
- SoftAP provisioning: worse phone UX (network switching), esp. iOS.
- Claim by device ID typed in: no proof of physical possession.

## Consequences
+ Maintained library with Expo plugin (Q-03). - Needs an Expo dev build, not Expo Go (risk O-4). PoP must be provisioned per unit in production flow (3 units: manual).

## Amendment (proposed, see ADR-011)
The "security with proof-of-possession" is narrowed to protocomm security 2 (SRP6a + AES-GCM); the custom endpoints grow to carry hub configuration (ADR-012); BLE is explicitly off outside setup mode; Wi-Fi credentials are not stored in the cloud profile. The claim-token mechanism is unchanged.

# ADR-011: BLE-only setup with encrypted credential provisioning; Wi-Fi-only operation; no Wi-Fi password in the cloud

Status: Accepted (A-080, Arsany 2026-11-12; device cut-off from the A-070 answer 2026-11-10) · Date: 2026-11-03 · Deciders: Theo (Arsany to decide at G2) · Amends: ADR-002

## Context
Owner request: the user initialises the sensor from the app over Bluetooth, the sensor is connected to the user's profile, the Wi-Fi data is transferred encrypted (and possibly kept encrypted in the profile), and afterwards the sensor uses only Wi-Fi to send data. Relevant: FR-D03, FR-A03, FR-A08, NFR-03, NFR-06, NFR-07, UC-02. Home Wi-Fi passwords are sensitive: they unlock the user's whole LAN.

## Decision
1. **Setup over BLE only**, using ESP-IDF `wifi_provisioning` / protocomm **security 2**: SRP6a handshake where the password is the proof-of-possession on the label/QR (device stores a per-unit salt and verifier, not the PoP), followed by AES-GCM on every payload. (From my knowledge of ESP-IDF; I could not check the 5.4 docs in this session. Fallback is security 1: X25519 + PoP, AES-CTR. Verify in week 1.)
2. **What is encrypted:** Wi-Fi SSID and passphrase, device name, claim token, hub configuration and MQTT credential (ADR-012), all in transit over BLE. **Not encrypted:** BLE advertisement and its address. No BLE link-layer bonding is used; the application-layer channel is the security boundary. SRP6a verifier leaks nothing usable but a wrong PoP lets an attacker in range try online guesses: the device limits attempts and leaves setup mode after a timeout (5 attempts, 300 s device cut-off, A-070 answer 2026-11-10; NFR-03 stays the user-time target, not enforced by the device).
3. **Claim:** unchanged from ADR-002. A user-bound, single-use token binds the device to the profile at first `/ingest`; the sensor receives its per-device token (ADR-004) then.
4. **After setup the BLE stack is disabled.** Normal operation is Wi-Fi only (hourly cloud POST + hub MQTT). Setup mode returns on first boot, button press or factory reset.
5. **Storage:** Wi-Fi credentials and tokens live in the device NVS. NVS encryption (HMAC-based key in eFuse) is recommended for production, optional for the demo (irreversible eFuse step, needs Arsany; question Q-H6).
6. **Profile:** the cloud profile stores **no Wi-Fi password**. At most the SSID as a convenience hint. The app may remember the password in the phone keystore (expo-secure-store) to re-use it for the next sensor.

## Alternatives for "Wi-Fi data encrypted in the user's profile"
- **A. Not in the cloud (chosen).** Nothing to leak server-side, no GDPR duty for credentials, simplest. Cost: a new phone, or a second user, re-types the password.
- **B. Client-side encrypted blob in the profile.** Key derived on the phone from a user passphrase or held in the OS keystore; server stores ciphertext only. Gives convenience across phones. Costs: key management and recovery UX, lost passphrase means re-enter; if the key sits only in the keystore it does not roam. Still a breach target (offline guessing of a weak passphrase). More work (about +3 h, not in estimates).
- **C. Server-side encryption (e.g. Supabase Vault, KMS).** Rejected: we could decrypt it, so a breach, a rogue admin or a subpoena exposes users' home networks; also pulls the data into NFR-07 scope.
Recommendation: A, with B only if Arsany explicitly wants roaming. The sensor never needs the credential from the cloud, so cloud storage adds risk without enabling any flow in the spec.

## Consequences
+ Stronger than PoP-only setup; credentials never in plaintext over the air or in our database. - Heavier crypto on the C3 during setup (SRP6a big-number math, a few seconds, setup only); app library must support security 2 (risk O-13); setup mode must be hardened against guessing; Wi-Fi password in device flash is plaintext unless NVS encryption is enabled (O-3). Interfaces: `interfaces/ble-provisioning.md` (endpoints `nw-claim`, `nw-hub`). Tests: 5.5 (setup on iOS/Android, wrong PoP rejected), 5.9 (no plaintext credential in cloud, capture shows no SSID/passphrase over BLE).

## Verification note (4.F2, PR #215, 2026-11-25)
Item 1 above said the ESP-IDF API was "from my knowledge, verify in week 1". Checked against ESP-IDF tag v5.4 (sparse clone, reviewer's local check; not re-run in the firmware CI):
- `components/protocomm/src/common/protocomm.c:120`: endpoints added with `protocomm_add_endpoint` get `REQ_EP`. `protocomm.c:199-204`: the `REQ_EP` handler runs only after `pc->sec->decrypt` succeeds.
- `components/protocomm/src/security/security2.c:452-467`: `sec2_decrypt` refuses unless the session state is `DONE`. `security2.c:220`: the SRP exchange. `security2.c:273-274`: the state becomes `DONE` and `PROTOCOMM_SECURITY_SESSION_SETUP_OK` is posted with `esp_event_post` on the default loop.
- `components/protocomm/include/security/protocomm_security.h:16, 23-27`: the `PROTOCOMM_SECURITY_SESSION_EVENT` base and its `SETUP_OK` and `CREDENTIALS_MISMATCH` ids.
- `components/wifi_provisioning/src/manager.c:323-339`: the manager sets the protocomm security for the chosen security version.

Consequence for this ADR: a wrong PoP fails inside the SRP exchange, so it is counted by `CREDENTIALS_MISMATCH` and never reaches an endpoint. The firmware drives the 5-failed-handshake limit from those two events (`nw_prov_idf.c`, `on_session_event`). Security impact: the setup state is global, so a failed handshake drops the session and the next attempt starts from ADVERTISING. ADR-011 accepts this as the guessing-DoS trade-off in item 2 (a wrong PoP can end setup for everyone in range; the owner accepted the 5-attempt limit).
Still open: the bench check in `tests/procedures/4.F2-claim-diagnostics.md` (NOT RUN). The FR-D09 requirement text is not in this checkout; see the PR for the question raised to the Lead.

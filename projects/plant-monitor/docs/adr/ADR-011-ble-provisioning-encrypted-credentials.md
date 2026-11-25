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

## Amendment (2026-11-25, PR #218): app sequence after a successful Wi-Fi apply
Decided by Theo (System Architect) on review of head 06983d2 (PR #218, `[app] Keep the setup session closed after Wi-Fi apply`). Amends section 3 step 5 of `interfaces/ble-provisioning.md` and the app README setup paragraph. Decisions 1-6 above are unchanged, including decision 4 (BLE stack off after setup). Requirements: FR-D03, FR-D07, NFR-03, NFR-06, FR-A08, ADR-011 decision 4. Owner sign-off not requested: the change alters no requirement, no cost and no device behaviour; the firmware alternative in item F below is the part that needs Arsany.

### A. What the app does now
1. **Apply succeeded:** the app sends nothing more over BLE. It waits for a `devices` row in the cloud (visible under RLS, claimed after the token was issued) for the link budget (90 s, polled once a second). Row found: `claimed`. No row: app error `link_lost`. The cloud row decides; the device's own `nw-status` is not read.
2. **Apply refused:** the app reads `nw-status` once a second for the device's reason (`wifi_failed` -> `wifi_auth` / `wifi_no_ap` / `wifi_timeout`; `claim_failed` -> claim codes), as before. FR-D03 wrong-passphrase handling is unchanged.
3. **A BLE drop** seen at any point after the claim token is sent (a rejection of `provision()` with `E_DEVICE_DISCONNECTED`, a failed `nw-status` read with a disconnect, or the `onDisconnected` watch) sets one drop flag. The flag ends `nw-status` polling and sends the app to the cloud check. Its outcome is `link_lost`, never a Wi-Fi code.
4. **Rule for the window after a drop (target, see condition C-A below):** every path that goes to the cloud check after a drop uses the same link budget (90 s) as item 1. Until that is implemented, the apply-refused path after a drop checks the cloud for only 8 tries (8 s, the `confirmTries` default). The contract and README say 90 s for every path, so they are wrong for that path until the code changes.

### B. Why
- The Android SDK (`esp-idf-provisioning-android` lib-2.4.4, `ESPDevice.java:1189`) sets its security session to `null` when the device reports Wi-Fi "Connected". The npm wrapper `@orbital-systems/react-native-esp-idf-provisioning` 0.7.1 resolves `provision()` only on success, and its `sendData` then starts a new SRP handshake for each custom-endpoint request. A poll after a successful apply therefore ran a handshake the device might reject, which dropped the link in the middle of the claim.
- The wrapper's own docs say custom-endpoint requests after `provision()` may fail "unless the device explicitly keeps the session available".
- Not polling after a success removes that risk. The cost is the trade-off in C.

### C. Trade-off accepted for v1
After a **successful** apply the app no longer shows the device's claim reasons. `device_owned`, `claim_token_invalid`, `claim_server` and `claim_network` are not reported; each becomes `link_lost` ("the sensor's Wi-Fi details were sent, but the server has not confirmed the sensor yet"). This is a loss of an intended path, not a regression against real behaviour: the old post-apply poll never worked on a phone, so no bench run ever showed these messages.
- **FR-A08 (release for re-claim):** a sensor already owned by another account gives `device_owned` on the device. After this amendment the user sees `link_lost` and no pointer to "release it in the other account first". A retry of the same setup gets the same answer, so the user can loop. Accepted for v1 only with the copy condition C-B below; the loop must be closed by the release flow or by a copy change before a customer uses it.
- **FR-D03:** a wrong Wi-Fi passphrase is still reported as `wifi_auth` with the sensor still in setup mode, because that path is an apply refusal and reads `nw-status`. Bench check (B-a below).
- **NFR-06:** no weakening. "Claimed" still needs the cloud row under RLS. Fewer BLE requests after apply means no new handshake after apply on the success path.
- **NFR-03:** the success path is not slower. The failure path can now take up to 90 s before `link_lost`.
- **FR-D07:** not touched.

### D. Verification status (what is and is not checked)
| Item | Status on 2026-11-25 |
|---|---|
| Wrapper 0.7.1 (npm tarball, `src/index.tsx`): `provision()` delegates to the native module; `sendData` error text says custom endpoints need an active session after `provision()`; `onDisconnected` fires only for an unrequested disconnect (lines 17-18, 203-209). | **Verified** from the tarball in this amendment. The tarball is the one in the lock file. |
| Android SDK lib-2.4.4 `ESPDevice.java:1189` (`session = null` on Wi-Fi "Connected"); wrapper resolves `provision()` only on `deviceProvisioningSuccess`. | **Verified** from the SDK source in the Architect's review of 31205b3 (comment 7167509054). Not re-read in this amendment. The SDK source has no version metadata; it was matched to the lock-file version by content, not by tag. |
| iOS SDK behaviour after apply. | **Not verified.** The iOS library was not readable. The app ships both platforms. |
| What the device does with a **new** handshake after apply. | **Not verified.** The contract (section 3 step 5, now corrected) says the device "rejects" it and drops the link. That is an inference from the SDK, not a device observation. Firmware `components/provisioning/src/nw_prov_idf.c` (`on_session_event`) counts a new correct-PoP handshake as `SETUP_OK`, and it keeps BLE on until the setup loop ends (about line 320). So the device may accept the new handshake. Bench check B-b decides. |
| Timing: 1 s poll, 90 s budget, SDK sleeps about 2 s before its first Wi-Fi status poll. | **Not verified.** Design values. The 2 s figure is from the review, not reproduced from source; device log timestamps are needed. |
| Jest and tsc on `06983d2`. | **Not run** in this amendment (no `node_modules` in the review worktree). |
| Bench (setup on hardware). | **NOT RUN.** Nothing in this amendment is evidence that setup works on a phone. |

**Bench checks before the task leaves "In review" (B-a/B-b/B-c):**
- B-a: successful setup sends no BLE request after apply (app log shows no `nw-status` after `provision` resolves; the device log shows no new handshake).
- B-b: after a successful apply, a new handshake with the correct PoP succeeds and `nw-status` reads `claimed` or `claiming`, **or** it fails and the device log shows why. Either result decides the firmware alternative in F. Record both logs.
- B-c: a wrong Wi-Fi passphrase still shows `wifi_auth` and the sensor stays in setup mode; a wrong PoP still shows `wrong_code`.

### E. Conditions on the code and docs (owner: Full-stack, Leo; before merge)
- **C-A:** the apply-refused path after a drop uses the same link budget (90 s, `ceil(maxLinkMs / pollMs)` tries) as the applied path, with a test that a drop after a refused apply waits for a row that appears after 8 s. (`bleProvisioning.ts` line 210 uses `confirmInCloud` with the default 8 tries.)
- **C-B:** `link_lost` copy or the `device_owned` loop above: either add one sentence that a sensor already owned by another account must be released there first, or state in the PR why not (FR-A08 owner decision).
- **C-C:** `docs/interfaces/ble-provisioning.md` section 3 step 5 says the device "rejects" a new handshake. Reword to "may reject: not verified on the device (B-b)". Keep the 90 s budget text for the applied path and add the refused-path window once C-A is in.
- **C-D:** `projects/plant-monitor/app/README.md` (line 32): same window statement as C-C.

### F. Firmware alternative (open decision; not decided here)
Option F: the device accepts a new handshake (same PoP, same five-failure rule) and keeps `nw-status` readable until it claims, so the app can keep polling after apply as before. It would restore the device's own claim reasons (`device_owned`, `claim_token_invalid`) on the success path, which closes the FR-A08 gap in C.
- Cost: firmware work in `nw_prov_idf.c` and `nw_prov_proto.c`; a longer window in which a wrong PoP can be guessed while the sensor joins Wi-Fi (ADR-011 decision 2); needs a firmware and security review and a bench run.
- If B-b shows the device already accepts a new handshake, option F may be an app-only change (re-handshake and poll), which changes the security analysis but not the firmware.
- **Decision needed:** Arsany with Theo, and the firmware owner (Mira). Raise it as a Needs Arsany item (the Lead logs the A-ID). If raised, it gets its own ADR, the next free number after ADR-018 (ADR-019), citing ADR-011 decision 2 and FR-A08. This amendment does not write it.
- Until decided: option A (this amendment) stands for v1.

Traceability: `docs/traceability.md` rows for FR-D03, FR-A08 and NFR-06 cite this amendment once it is merged (the row moves with the ADR; Architect playbook rule 6).

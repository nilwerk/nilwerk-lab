# ADR-012: Raspberry Pi local hub (MQTT broker + local dashboard), fed in parallel to the cloud path

Status: Proposed (owner comment on PR #3) · Date: 2026-11-03 · Deciders: Theo (Arsany to decide at G2; open questions Q-H1..Q-H10 in architecture.md section 10.4)

## Context
Owner request: a Raspberry Pi is required for a local dashboard; each sensor sends MQTT data, in parallel to the cloud. Changes the earlier "standalone cloud, HA optional" stance (Q-04). Relevant: FR-D02, FR-I01, NFR-01, NFR-06, ADR-010. Open point: "required" as hard product dependency vs required for the local-dashboard feature (Q-H1). This ADR assumes the feature-only reading: setup and cloud path work without a hub; the hub is configured when present.

## Decision
**Topology.** The Pi sits on the same LAN as the sensors and runs: Mosquitto 2.x (TLS on 8883, anonymous disabled, dynamic-security plugin for per-device users and topic ACLs); a **hub service** in TypeScript on Node (MQTT subscriber, SQLite store, registrar API for pairing and device credentials, optional HA bridge); a static **web dashboard** served by the same service. Dashboard choice: own small web UI (recommended: same language as the rest, the registrar is code anyway). Grafana+InfluxDB or Node-RED are alternatives with less UI code but more services and RAM; decision Q-H4. Access on the LAN only; no port forwarding, no cloud relay.
**Topics** (all prefixed `nilwerk/v1/<device_id>/`): `telemetry` (QoS 1, not retained, one message per sample), `event` (QoS 1, critical events), `status` (retained; `online`/`offline`, device sets an LWT; `offline` also published by the hub when no data for 2.5 h).
**Payload** (UTF-8 JSON, same field names as the cloud report schema, which 2.4 defines): `{"v":1,"ts":<unix s>,"seq":<n>,"moisture_pct":..,"moisture_raw":..,"temp_c":..,"rh_pct":..,"lux":..,"vbat_mv":..,"forecast_h":..,"events":[..],"fw":".."}`. `device_id`+`ts` dedupes.
**Auth.** Per-device MQTT username (= device id) and random password; ACL allows publish only below its own prefix. The app obtains the credential from the hub registrar during setup (pairing code shown on the hub) and sends it to the sensor over the encrypted BLE channel (ADR-011); release revokes it. TLS with a private CA created on the hub at first boot; the sensor pins that CA certificate (about 1 KB in NVS). Plain MQTT on the LAN is rejected by default (Q-H7).
**Discovery.** The BLE setup message carries hub hostname (e.g. `nilwerk-hub.local`), port and, optionally, a static IP. The firmware caches the last resolved IP in NVS and tries it first; on failure it resolves via mDNS (ESP-IDF `mdns` component) once per wake, then gives up. Recommendation: DHCP reservation for the Pi. The hub also advertises `_nilwerk-hub._tcp` for the app.
**Timing and offline.** In the hourly Wi-Fi session: cloud POST first, then hub publish (connect, publish up to 4 samples QoS 1, disconnect, 3 s overall timeout). If the hub is unreachable the hub publish is skipped and not buffered (the cloud copy is complete); the dashboard shows a gap and "offline" after 2.5 h. If the internet is down but the hub is up, the hub still receives data and the cloud buffer fills as today (FR-D04).
**Battery (NFR-01).** The second publish adds one TCP+TLS connection on the LAN, no extra Wi-Fi association. Rough, **unmeasured** arithmetic: assume +1 s awake at about 100 mA = 0.028 mAh per report, x24 = 0.67 mAh/day, about 120 mAh over 182 days, i.e. roughly 6-12 % of a 1000-2000 mAh cell. If the measured value in 5.4 breaks the target: drop TLS on the LAN, publish only every 2nd report, or shorten timeouts. Live 15-min publishing is rejected (4x the Wi-Fi wakes).
**HA bridge.** ADR-010 amended: the hub service publishes HA discovery from local data to the hub's own broker (HA connects to it) or bridges to the user's broker. Optional, Could.

## Alternatives
- Device publishes to the cloud only, local dashboard from the cloud: no Pi, but fails without internet; contradicts the owner request.
- Pi pulls from the cloud API: needs cloud credentials on the Pi, no local-only operation.
- Bluetooth to the Pi: contradicts Wi-Fi-only operation (ADR-011).
- Broker in the cloud (e.g. HiveMQ/EMQX): another service and cost; no offline benefit.

## Consequences
+ Local view works offline; HA integration becomes cheap and local; sensor holds two credentials (cloud token, hub credential). - Required extra hardware and install step (BOM +about EUR 60-100 unverified), a second set of software to maintain and secure (OS updates, SD card wear, backups), same-LAN requirement (client isolation, guest networks, mDNS blocked), +about 38 h on the plan, and a second TLS session per hour. Cites: FR-D02, FR-I01, NFR-01, NFR-06; proposed FR-D08, FR-H01..H03, NFR-11. Contracts to write in 2.4: `interfaces/hub-mqtt.md`, `interfaces/hub-api.md`.

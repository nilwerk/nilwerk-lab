# Hub MQTT contract (device -> Raspberry Pi hub), v1 DRAFT

Task 2.4 · Author: Theo · Implements ADR-012 (Proposed) · Link L-21/L-22 in `architecture.md`.
Requirements: FR-D02 (hourly), FR-D04, FR-D01, NFR-01, NFR-06, proposed FR-D08, FR-H01, NFR-11.
Status: draft. Nothing here has been run against a broker.

## 1. Connection
| | |
|---|---|
| Broker | Mosquitto 2.x on the hub, TLS on **8883**, anonymous access off (ADR-012; TLS vs plain still open as Q-H7, this spec assumes the recommended TLS) |
| Protocol | MQTT 3.1.1 |
| Client ID / username | `device_id` = the hardware id `nw-<12 hex>` (same as `devices.hw_id` in the cloud, printed on the label). The hub knows nothing about cloud UUIDs, and the credential is issued before the cloud claim |
| Password | random, issued by the hub registrar during setup, delivered over BLE (`nw-hub`, see `ble-provisioning.md`) |
| TLS | device pins the hub's private CA (PEM, about 1 KB, in NVS) |
| Session | `clean session = true`; connect, publish, disconnect once per hourly Wi-Fi wake (ADR-012 timing: 3 s overall timeout, cloud POST first) |
| ACL (per device) | publish `nilwerk/v1/<device_id>/#`; **no subscribe** (the device receives nothing from the hub; config comes from the cloud) |
| Hub service account | subscribe `nilwerk/v1/+/#`; may also publish `nilwerk/v1/<device_id>/status` for offline marking |

## 2. Topics
All below `nilwerk/v1/<device_id>/`.

| Topic | QoS | Retain | Sender | Content |
|---|---|---|---|---|
| `telemetry` | 1 | no | device | one message per 15-min sample, up to 4 per session |
| `event` | 1 | no | device | one message per event (same list as the cloud report) |
| `status` | 1 | **yes** | device, hub | last-report marker; the hub overwrites it with `offline` |

**Deviation from ADR-012 (needs your OK, see ADR-013):** ADR-012 gives the device a Last-Will `offline`. The device
connects only for a few seconds per hour and disconnects cleanly, and a clean DISCONNECT never fires the LWT; an LWT would
only fire on a crash mid-session. So there is no LWT. Offline is decided by the hub: **no `telemetry` or `status` for
3 hours 10 minutes = 3 missed hourly reports** (G1 decision, same rule as the cloud, replaces ADR-012's 2.5 h).

## 3. Payloads (UTF-8 JSON, one object per message, field names identical to `device-report.schema.json`)
`telemetry`:
```json
{"v":1,"ts":1798999000,"moisture_pct":41.2,"moisture_raw":1900,"temp_c":21.4,"rh_pct":48.0,"lux":320,"vbat_mv":3920,"forecast_h":36.5,"fw":"0.1.0"}
```
| Field | Type | Unit / range (plausible, G1) | Req |
|---|---|---|---|
| `v` | int = 1 | schema version | |
| `ts` | int | unix s, SNTP-synced; dedupe key with `device_id` | FR-D04 |
| `moisture_pct` | number or null | relative 0-100 | FR-D01 |
| `moisture_raw` | int or null | ADC counts 0-4095 | FR-D01 |
| `temp_c` | number or null | -10 .. 60 degC | FR-D01 |
| `rh_pct` | number or null | 0 .. 100 %RH | FR-D01 |
| `lux` | number or null | 0 .. 100000 | FR-D01 |
| `vbat_mv` | int or null | 3000 .. 4250 mV | FR-D01, FR-D06 |
| `forecast_h` | number or null | 0 .. 72 h (latest, same on all messages of the session) | FR-E01 |
| `fw` | string | firmware version | |

`event`: `{"v":1,"ts":1798999000,"type":"wetting_unexpected"}`; `type` is the enum from the report schema.
`status` (device): `{"v":1,"state":"online","ts":1799000000,"fw":"0.1.0","vbat_mv":3920}`; (hub): `{"v":1,"state":"offline","ts":<unix s>}`.

The hub (Node-RED) applies the same plausible ranges as the cloud: out-of-range values are stored but flagged and not charted.
Max message size 1 KiB. Per hour: 4 telemetry + 0..n events + 1 status.

## 4. Failure behaviour (FR-D04, ADR-012)
Hub unreachable or timeout: skip, do not buffer, do not retry in this session. The cloud copy is the complete record; the hub
dashboard shows a gap. Cloud unreachable but hub up: still publish to the hub (NFR-11), the cloud buffer fills as usual.

## 5. Acceptance (to test in 5.5 / 5.9)
- Wrong password and wrong topic publish are refused by the ACL (NFR-06).
- 4 telemetry messages per hour arrive with the `ts` the cloud stored for the same samples.
- Hub shows `offline` 3 h 10 min after the last report.

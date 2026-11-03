# ADR-010: Optional Home Assistant bridge as a cloud-side MQTT publisher

Status: Proposed (Could, FR-I01; follows Q-04) · Date: 2026-11-03 · Deciders: Theo (Arsany to confirm at G2)

## Context
FR-I01: plant entities appear in an existing HA instance via MQTT discovery. The cloud is the system of record; devices must not hold extra connections (battery).

## Decision
If time allows, a bridge function publishes HA discovery topics and state to a broker the user configures (credentials stored encrypted, TLS). The device stays HTTPS-only. Disabled by default.

## Alternatives
Device publishes MQTT directly: more battery, second credential on device. HA custom integration polling our API: more work and no MQTT-discovery demo.

## Consequences
First item to cut under schedule pressure (risk O-11). Needs a reachable broker (e.g. user's HA instance); verify live state before design, not assumed (playbook rule about earlier unverified MQTT claims).

## Amendment (proposed, see ADR-012)
With a required Raspberry Pi hub running Mosquitto, the HA bridge no longer needs to live in the cloud: the hub service publishes HA MQTT-discovery entities from its local data, either to its own broker (HA connects to it) or bridged to the user's HA broker. This removes the cloud-side broker credentials from the design and keeps the integration working offline. Plan 4.B6 shrinks accordingly. Still Could, still the first item to cut. Device remains one publisher (to the hub); it never publishes to HA directly.

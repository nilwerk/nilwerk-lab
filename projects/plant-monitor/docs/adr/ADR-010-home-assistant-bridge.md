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

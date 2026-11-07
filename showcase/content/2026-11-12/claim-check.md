# Claim check: Logbook Day 4 (EU decision)

| # | Claim | Type | Source | Status |
|---|---|---|---|---|
| 1 | One platform for accounts, data and access rules, hosted in an EU region | D | `projects/plant-monitor/docs/adr/ADR-003-supabase-backend-and-ingest.md` (Decision; Status Accepted, 2026-11-03) | ok |
| 2 | Alternatives considered: Firebase, Home Assistant as hub, a dedicated server (three) | D | ADR-003 "Alternatives" | ok. "decided against them for now": ADR says rejected (Firebase in Q-12, Home Assistant as hub in Q-04); the dedicated server "more ops, no RLS/Auth for free". "For now" is Poppy's softening: Theo to confirm wording |
| 3 | Export and deletion as a requirement | D | ADR-003 Context "EU hosting and deletion/export (NFR-07)" | ok |
| 4 | "Simplest way" to keep data in Europe | opinion | ADR consequences "One platform, one language, EU" | (T) Theo confirms phrase |
| 5 | Devices call an ingest function, never touch tables directly | D | ADR-003 Decision | ok |
| 6 | Tested on a local database only; not on a real Supabase project | M | `showcase/items/2026-11-07_4.B1/caption.md` "Unverified" | ok |
| 7 | No price or quota statement | n/a | stack-and-costs prices are unverified and are not used | on purpose |

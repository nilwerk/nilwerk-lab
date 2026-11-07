# Claim check: Logbook Day 4 (EU decision)

| # | Claim | Type | Source | Status |
|---|---|---|---|---|
| 1 | One platform for accounts, data and access rules, hosted in an EU region | D | `projects/plant-monitor/docs/adr/ADR-003-supabase-backend-and-ingest.md` (Decision; Status Accepted, 2026-11-03) | ok |
| 2 | Alternatives **rejected**: Firebase, Home Assistant as hub, a dedicated server (three) | D | ADR-003 "Alternatives" (Firebase rejected in Q-12, Home Assistant as hub in Q-04, self-run server: more ops, no RLS/Auth for free) | ok; wording now "rejected" as in the ADR |
| 3 | Export and deletion as a requirement | D | ADR-003 Context "EU hosting and deletion/export (NFR-07)" | ok |
| 4 | "Simplest way" to keep data in Europe | opinion | ADR consequences "One platform, one language, EU" | (T) Theo confirms phrase |
| 5 | Devices call an ingest function, never touch tables directly | D | ADR-003 Decision | ok |
| 6 | Tested on a local database only; not on a real Supabase project | M | `showcase/items/2026-11-07_4.B1/caption.md` "Unverified" | ok |
| 7 | No price or quota statement | n/a | stack-and-costs prices are unverified and are not used | on purpose |
| 8 | The **database** is planned for an EU region (decision, not live; local test only); "in the EU" is not claimed for all data | D | ADR-003; `stack-and-costs.md` decision A-025 "one free Supabase database ... in the EU region" | ok |
| 9 | Helper services (Claude API for care tips, Expo push) may process pseudonymous data outside the EU | D | `projects/plant-monitor/docs/stack-and-costs.md`: "Claude and Expo still only ever receive a pseudonymous user id (plus readings and the city name)"; S4 Claude API "Processed outside the EU (O-5)" | ok (T) Theo confirms Expo push location wording; the post says "may" |

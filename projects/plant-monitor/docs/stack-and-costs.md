# Software stack and running costs (task 2.6)

Theo (System Architect) · 2026-11-05, updated 2026-11-06 for A-025 · Status: Proposed, for Arsany's review · Follows ADR-003, ADR-005, ADR-006, ADR-007, ADR-008 and `architecture.md` section 6.

**Read this first: every price, quota and licence statement below is `unverified`.** The network hosts of all providers were blocked in the session that wrote this, so nothing was checked on a provider page. The numbers come from the author's memory or are our own assumptions, and each row names the URL a human must open. Do not quote any figure to a customer before the "Check here" column has been ticked off. Requirement trace: FR-P01..P04 (premium cost), NFR-06/07 (security, EU), Q-13 ("free" weather), O-5, O-6, O-9 in `architecture.md`.

## 1. Stack at a glance

One language, TypeScript, for app, edge functions and MCP server (TEAM.md section 6). Firmware (C, ESP-IDF) and ML (Python, offline) are outside the cloud stack.

| Layer | Choice | Language |
|---|---|---|
| Mobile app (iOS + Android) | React Native with Expo (dev build, not Expo Go, because of BLE provisioning, O-4) | TypeScript |
| Backend | Supabase EU: Postgres + RLS, Auth, Storage, Realtime, pg_cron, Edge Functions | TypeScript (Deno) for functions, SQL for schema |
| MCP server | Edge function, personal API key (ADR-007) | TypeScript |
| Tips | Weather API + Claude API + deterministic rule layer (ADR-006) | TypeScript |
| Push | Expo push service, alert engine in an edge function (C-08) | TypeScript |
| Local hub (v0.2, ADR-012) | Mosquitto + Node-RED on Raspberry Pi, own web UI | JavaScript/TypeScript |

## 2. Services, data residency, licence and cost formula

**Decision A-025 (Arsany, supersedes the separate profile DB of A-011):** the demo uses **one free Supabase database** for profiles and sensor/plant data, in the EU region. **Claude and Expo still only ever receive a pseudonymous user id** (plus plant readings and, for tips, the city name; no name, e-mail or address); that rule is enforced in the code (allow-list below), not by a second database. Weather is **DWD open data via Bright Sky**. **Demo builds first** (TestFlight / sideloaded APK, no store accounts) and the **free Supabase tier for the demo**; Pro starts with the first paying customer. If a customer later requires hard separation of identity data, a second project is a one-line change (`profile_db_projects = 1`, +10 USD/month, unverified).

| # | Service | Purpose | Plan / tier assumed | Data residency | Licence / commercial-use note (all unverified) | Monthly cost formula |
|---|---|---|---|---|---|---|
| S1 | Supabase (one project, A-025) | Postgres + RLS, Auth, Storage, Edge Functions, Realtime; profiles and sensor data in the same DB | Free for the demo; Pro from `min_users_for_pro` customers | EU region (NFR-07). Holds profile, plant, reading, device data; Claude/Expo see only the pseudonymous id | Hosted service, commercial use allowed on all paid plans; free-tier terms and pause-on-inactivity to be checked | `0` (free) or `pro_base` + overage |
| S2 | ~~Supabase profile project~~ | removed by A-025 (one database) | n/a | n/a | n/a | `0` (optional later: `extra_project`) |
| S3 | Weather API (pick in section 3) | Forecast for tips | DWD open data via Bright Sky (primary), Open-Meteo (fallback) | Request carries city/coordinates only, never a user id. Bright Sky is a German service; Open-Meteo is EU-hosted (to verify) | See section 3 | `0` or fixed plan fee |
| S4 | Claude API (Anthropic) | Care-tip generation (ADR-006) | Pay per token, small model tier; output schema-validated and rule-clamped | Processed outside the EU (O-5). Receives pseudonymous id, plant type, readings, forecast, city. No profile data | Commercial API terms; check data retention and the no-training default in the commercial terms | `tips_calls * (in_tokens * price_in + out_tokens * price_out)` |
| S5 | Expo push service | Alert push notifications | Free | Relays via Expo (US, to verify). Payload: pseudonymous id, push token, short alert text without user name | Free to use; check fair-use limits | `0` |
| S6 | Expo EAS (build/update) | Dev builds, OTA JS updates | Free plan | Build metadata only, no user data | Check free-plan build quota and commercial use | `0` (paid plan if the quota is not enough) |
| S7 | Apple Developer Program | iOS distribution (TestFlight/App Store) | Individual or organisation | n/a | Required for iOS distribution | `99 / 12` |
| S8 | Google Play Console | Android distribution | One-off fee | n/a | Required for Play distribution; sideloaded APK is free for the demo | `25 / 36` (amortised) |
| S9 | GitHub Actions | CI, edge function deploy | Free tier | Source and build logs | already in use | `0` |
| S10 | Hub (Raspberry Pi), **v1.1, not in v1 (A-023)** | Local dashboard (ADR-012) | One-off hardware, not cloud | Stays in the home | Mosquitto (EPL/EDL), Node-RED (Apache-2.0): licences to verify | one-off BOM, not in this model |

Data-flow rule the code must keep (testable by Ines): the tips and push functions build their outbound payload from an allow-list of fields; profile columns (name, e-mail, premium flag) are read only by account functions (claim, export, delete) and never copied into those payloads. With one database this rule, RLS and the allow-list test are the whole privacy boundary, so Ines should test the allow-list.

## 3. Weather API pick

Requirement: Q-13 asked for a "free" weather source; O-6 warned that some free tiers are non-commercial only. A sales demo and later paid client use are commercial.

| Candidate | Commercial use | Coverage | Verdict |
|---|---|---|---|
| **DWD open data via Bright Sky** (primary) | Believed allowed with source attribution under the DWD open-data terms; Bright Sky is an open-source wrapper that can be self-hosted. **Unverified.** Check https://www.dwd.de/DE/leistungen/opendata/nutzungsbedingungen.html and https://brightsky.dev/docs/ | Germany and surroundings | Pick for the demo and German customers |
| Open-Meteo (fallback / outside Germany) | Believed free for **non-commercial** use only; commercial use needs a paid plan. **Unverified.** Check https://open-meteo.com/en/terms and https://open-meteo.com/en/pricing | Global | Use only on a paid plan; model includes it as a sensitivity row |
| Other (OpenWeatherMap, Met.no) | not evaluated | | Out of scope unless Arsany asks |

The provider stays behind the adapter from ADR-006, so the pick can change without touching the tips code. A-2 from `architecture.md` (confirm weather licence) remains open until a human has read the two pages above.

## 4. Cost model

Source of truth: `costs/cost_model.py` (Python stdlib only, runs on 3.11) with `costs/test_cost_model.py`. Regenerate with `python costs/cost_model.py --markdown`; a unit test fails if the tables below no longer match the script. Run tests: `cd projects/plant-monitor/docs/costs && python -m unittest discover -v`.

### 4.1 Prices and quotas used (all unverified)

<!-- BEGIN:PRICES -->
| Item | Assumed value | Unit | Status | Check here |
|---|---|---|---|---|
| `supabase_pro_base` | 25 | USD/month per org | unverified | https://supabase.com/pricing |
| `supabase_extra_project` | 10 | USD/month per extra Micro project | unverified | https://supabase.com/pricing |
| `supabase_fn_overage` | 2 | USD per 1M edge-function invocations over quota | unverified | https://supabase.com/pricing |
| `supabase_db_overage` | 0.125 | USD per GB-month DB over quota | unverified | https://supabase.com/pricing |
| `supabase_storage_overage` | 0.021 | USD per GB-month storage over quota | unverified | https://supabase.com/pricing |
| `claude_in` | 1 | USD per 1M input tokens (small model tier) | unverified | https://www.anthropic.com/pricing |
| `claude_out` | 5 | USD per 1M output tokens (small model tier) | unverified | https://www.anthropic.com/pricing |
| `expo_push` | 0 | USD, push service free of charge | unverified | https://docs.expo.dev/push-notifications/overview/ |
| `eas_build` | 0 | USD, EAS free plan (limited builds) | unverified | https://expo.dev/pricing |
| `apple_developer` | 99 | USD/year | unverified | https://developer.apple.com/programs/ |
| `google_play` | 25 | USD one-off (amortised over 36 months here) | unverified | https://play.google.com/console/about/ |
| `weather_dwd_brightsky` | 0 | USD, DWD open data via Bright Sky | unverified | https://brightsky.dev/docs/ and https://www.dwd.de/DE/leistungen/opendata/nutzungsbedingungen.html |
| `weather_openmeteo_commercial` | 29 | USD/month fallback plan, size unknown | unverified | https://open-meteo.com/en/pricing |
| Supabase `free` quotas | DB 0.5 GB, storage 1 GB, 500,000 fn calls | per month | unverified | https://supabase.com/pricing |
| Supabase `pro` quotas | DB 8 GB, storage 100 GB, 2,000,000 fn calls | per month | unverified | https://supabase.com/pricing |
<!-- END:PRICES -->

### 4.2 Usage assumptions (ours, not provider data)

<!-- BEGIN:ASSUMPTIONS -->
| Assumption | Value | Why |
|---|---|---|
| `devices_per_user` | 2 | typical household; 3 demo units are 1 demo user |
| `premium_share` | 0.2 | planning guess, no data |
| `reports_per_device_month` | 720 | hourly upload = 1 POST/hour, counts function calls |
| `samples_per_device_month` | 2880 | 15-min samples = DB rows, 96/day (PR #15 db-schema) |
| `other_calls_per_user_month` | 600 | app, alerts, analytics, MCP |
| `db_kb_per_sample` | 0.3 | row plus index, rough |
| `retention_months` | 12 | total history kept 12 months (raw + roll-up) |
| `raw_months` | 3 | A-025: about 3 months raw 15-min samples, older data rolled up |
| `rollup_rows_per_device_month` | 720 | hourly min/avg/max, 24 * 30 |
| `db_kb_per_rollup` | 0.3 | roll-up row plus index, rough |
| `photo_mb_per_device` | 0.5 | one compressed photo per plant |
| `tips_per_premium_device_month` | 30 | one cached refresh a day (ADR-006) |
| `demo_tips_mode` | rule_based | A-029: demo tips are canned/rule-based (cost 0); live Claude is a switchable option (feature flag TIPS_MODE=live) |
| `demo_live_tips_per_device_month` | 30 | only when demo_tips_mode = live: one cached refresh a day per demo device |
| `tips_tokens_in` | 2000 | plant, readings, forecast, instructions |
| `tips_tokens_out` | 500 | schema-constrained JSON |
| `profile_db_projects` | 0 | A-025: one database for profiles and sensor data (no second project) |
| `min_users_for_pro` | 100 | free tier is for the demo only |
<!-- END:ASSUMPTIONS -->

### 4.3 Formulas

<!-- BEGIN:FORMULAS -->
```text
fn_calls   = devices * reports_per_device_month + users * other_calls_per_user_month
db_gb      = devices * (samples_per_device_month * raw_months * kb_sample + rollup_rows_per_device_month * (retention_months - raw_months) * kb_rollup) / 1024^2
storage_gb = devices * photo_mb_per_device / 1024
tips_calls = premium_devices * tips_per_premium_device_month   (premium_devices = premium_users * devices_per_user)
claude     = tips_calls * (tokens_in * price_in + tokens_out * price_out) / 1e6
supabase   = tier base (pro: base + profile_db_projects * extra_project; free: 0) + overage over quota
store      = apple_year / 12 + google_once / 36        (only when published in the stores)
total      = supabase + claude + push + weather + store
per user   = total / users;  marginal premium = marginal free + one user's tips calls * claude cost
```
<!-- END:FORMULAS -->

### 4.4 Result: monthly running cost

<!-- BEGIN:TOTALS -->
| Monthly cost (USD) | 3 demo units | 100 users | 1000 users |
|---|---|---|---|
| Users / devices / premium | 1 / 3 / 1 | 100 / 200 / 20 | 1000 / 2000 / 200 |
| Supabase tier | free | pro | pro |
| Supabase plan | 0.00 | 25.00 | 25.00 |
| Supabase overage | 0.00 | 0.00 | 0.16 |
| Claude API (tips) | 0.00 | 5.40 | 54.00 |
| Expo push + EAS | 0.00 | 0.00 | 0.00 |
| Weather API | 0.00 | 0.00 | 0.00 |
| Store accounts | 0.00 | 8.94 | 8.94 |
| **Total USD** | **0.00** | **39.34** | **88.11** |
| **Total EUR** (FX 0.92) | **0.00** | **36.20** | **81.06** |
<!-- END:TOTALS -->

### 4.4a Result: database size (A-025: about 3 months raw, then hourly roll-up)

The unit of record is one 15-minute sample, 96 per day = 2880 rows per device-month (PR #15, `db-schema.sql`, interface decision 1). Function calls stay hourly. **A-025: raw samples are kept about 3 months; older data is rolled up to hourly min/avg/max rows (720 per device-month, a pg_cron job) up to 12 months** (daily roll-ups can follow later and are negligible in size). The 12-month charts stay; only the 15-minute resolution is limited to 3 months.

<!-- BEGIN:DBSIZE -->
| DB size (3 months raw, then hourly roll-up to 12 months) | 3 demo units | 100 users | 1000 users |
|---|---|---|---|
| Rows (raw + roll-up) | 45,360 | 3,024,000 | 30,240,000 |
| DB size GB | 0.01 | 0.87 | 8.65 |
| Pro quota 8 GB: | within | within | OVER by 0.65 GB |
| For comparison: all 12 months raw, GB | 0.03 | 1.98 | 19.78 |
| For comparison: free quota 0.5 GB: | within | OVER | OVER |
<!-- END:DBSIZE -->

**Consequence:** with roll-up, 100 users need 0.87 GB (all-raw: 1.98 GB) and 1000 users 8.65 GB (all-raw: 19.78 GB), so the 1000-user case is only 0.65 GB over the 8 GB Pro quota (unverified), about 0.08 USD of overage. The free tier (0.5 GB, unverified) holds the 3-unit demo easily. **This changes two PR #15 contracts:** NFR-13 / `purge_old_readings()` currently keep **raw** readings 12 months (G1 point 21); under A-025 they must become "raw 3 months, hourly roll-up 12 months", with a roll-up job and a roll-up table. That is a follow-up on the 2.4 branch (new table `readings_hourly`, job, export of both, premium window for charts) and needs Arsany's OK on the wording (question Q5).

### 4.5 Result: cost per user (free vs premium)

<!-- BEGIN:PERUSER -->
| Cost per user per month (USD) | 3 demo units | 100 users | 1000 users |
|---|---|---|---|
| Fully loaded (total / users, mixed free+premium) | 0.00 | 0.39 | 0.09 |
| Marginal free user (worst case, over quota) | 0.0041 | 0.0041 | 0.0041 |
| Marginal premium user (adds tips) | 0.27 | 0.27 | 0.27 |
| Fully loaded if weather = Open-Meteo commercial plan | 29.00 | 0.68 | 0.12 |
<!-- END:PERUSER -->

### 4.6 Reading the numbers

- The cloud is cheap per user once past the fixed Supabase fee: a free user costs a fraction of a cent in function calls; a premium user costs about 0.27 USD a month, almost all of it Claude tips. Under these unverified prices, a premium price above roughly 1 USD a month covers the variable cost, with the fixed fee as the real hurdle at 100 users.
- The "100 users" column is dominated by fixed costs (Supabase Pro + store accounts); the 1000-user column by Claude. **The demo costs 0.00 USD**: free Supabase tier, free push/EAS/GitHub, DWD weather, no store accounts, and no live Claude calls (**A-029: the demo shows canned, rule-based tips; live Claude is a switchable option**, feature flag `TIPS_MODE=live`, default `rule_based`). Switching live tips on in the demo would cost about 0.40 USD a month for 3 units (3 devices x 30 refreshes x 0.0045 USD, unverified token prices): see Q6 (decided).
- Open-Meteo's commercial plan would add a fixed fee that is large relative to the demo and the first customers; this is why the weather pick matters.
- Sensitivity worth re-running once prices are verified: `tips_per_premium_device_month` (caching hit rate), the model tier (token price), `premium_share`, and the raw-retention length (`raw_months`). The separate profile project is gone (A-025); re-adding it costs 10 USD a month.
- Not modelled: hardware, shipping, payment-provider fees (no payments yet, ADR-008), support time, VAT, a domain, e-mail sending for auth, Supabase compute add-ons if load grows, backups beyond the plan.

## 5. Decisions recorded and questions for Arsany

| ID | Item | Status |
|---|---|---|
| Q1 / A-011 | Profiles in a separate DB | **Superseded by A-025:** one free Supabase DB for the demo; Claude and Expo get only the pseudonymous user id |
| Q2 / A-2 | Weather provider | **Decided (A-025):** DWD open data via Bright Sky. A human still reads the two terms pages in section 3 before the first customer demo (unverified) |
| Q3 | Stores or demo builds | **Decided (A-025):** demo builds first; no Apple/Google account until a customer needs it |
| Q4 | Supabase tier | **Decided (A-025):** free tier for the demo, Pro from the first paying customer |
| Q5 | Raw retention | **Decided (A-025, A-028):** about 3 months raw, then hourly/daily roll-up kept 12 months. NFR-13 changed accordingly; PR #15 implements it (`readings_hourly`, `apply_retention()`, replaces `purge_old_readings()`). The model's `raw_months = 3` matches |
| Q6 | Live Claude tips in the demo | **Decided (A-029):** demo tips are canned / rule-based (cost 0). Live Claude stays as a switchable option: feature flag `TIPS_MODE` = `rule_based` (default) or `live`; the cost model has `demo_tips_mode` (live = about 0.40 USD a month for 3 units, unverified). Needed for any customer who pays for tips |

Note for Kai (DevOps): CI does not run `docs/costs/` (no workstream gate covers it), so the doc-drift test only protects the doc when someone runs it: `cd projects/plant-monitor/docs/costs && python3 -m unittest discover -v`. Please add a gate or step; `ci.yml` is not changed in this PR.

Not decisions, but tasks for a human: tick every "Check here" URL in 4.1 and section 3 and replace `unverified` in `cost_model.py` with the verified date (Nora can list this as a work item).

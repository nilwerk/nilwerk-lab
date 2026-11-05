# Software stack and running costs (task 2.6)

Theo (System Architect) · 2026-11-05 · Status: Proposed, for Arsany's review · Follows ADR-003, ADR-005, ADR-006, ADR-007, ADR-008 and `architecture.md` section 6.

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

Data residency follows decision **A-011**: user profiles (identity, e-mail, premium flag) live in a **separate database** from sensor/plant data, and **Claude and Expo only ever receive a pseudonymous id** (plus plant readings and, for tips, the city name; no name, e-mail or address). Caveat: the Needs Arsany tab entry A-011 is listed in the 2026-11-03 report as "Open, recommendation: accept pseudonymised flow"; this document applies that decision as instructed by the Lead. If Arsany answers differently the table and the model change (question Q1 below).

| # | Service | Purpose | Plan / tier assumed | Data residency | Licence / commercial-use note (all unverified) | Monthly cost formula |
|---|---|---|---|---|---|---|
| S1 | Supabase (data project) | Postgres + RLS, Auth, Storage, Edge Functions, Realtime | Free for the demo; Pro from `min_users_for_pro` customers | EU region (NFR-07). Holds plant, reading, device data keyed by pseudonymous id | Hosted service, commercial use allowed on all paid plans; free-tier terms and pause-on-inactivity to be checked | `0` (free) or `pro_base` + overage |
| S2 | Supabase (profile project, A-011) | User profiles in a separate DB | One extra project | EU region. Only place that links the pseudonymous id to a person | as S1 | `extra_project` (Pro only) |
| S3 | Weather API (pick in section 3) | Forecast for tips | DWD open data via Bright Sky (primary), Open-Meteo (fallback) | Request carries city/coordinates only, never a user id. Bright Sky is a German service; Open-Meteo is EU-hosted (to verify) | See section 3 | `0` or fixed plan fee |
| S4 | Claude API (Anthropic) | Care-tip generation (ADR-006) | Pay per token, small model tier; output schema-validated and rule-clamped | Processed outside the EU (O-5). Receives pseudonymous id, plant type, readings, forecast, city. No profile data | Commercial API terms; check data retention and the no-training default in the commercial terms | `tips_calls * (in_tokens * price_in + out_tokens * price_out)` |
| S5 | Expo push service | Alert push notifications | Free | Relays via Expo (US, to verify). Payload: pseudonymous id, push token, short alert text without user name | Free to use; check fair-use limits | `0` |
| S6 | Expo EAS (build/update) | Dev builds, OTA JS updates | Free plan | Build metadata only, no user data | Check free-plan build quota and commercial use | `0` (paid plan if the quota is not enough) |
| S7 | Apple Developer Program | iOS distribution (TestFlight/App Store) | Individual or organisation | n/a | Required for iOS distribution | `99 / 12` |
| S8 | Google Play Console | Android distribution | One-off fee | n/a | Required for Play distribution; sideloaded APK is free for the demo | `25 / 36` (amortised) |
| S9 | GitHub Actions | CI, edge function deploy | Free tier | Source and build logs | already in use | `0` |
| S10 | Hub (Raspberry Pi) | Local dashboard (ADR-012) | One-off hardware, not cloud | Stays in the home | Mosquitto (EPL/EDL), Node-RED (Apache-2.0): licences to verify | one-off BOM, not in this model |

Data-flow rule the code must keep (testable by Ines): the tips and push functions build their outbound payload from an allow-list of fields; the profile DB is reachable only from account functions (claim, export, delete). That is the contract that makes the A-011 statement true.

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
| `retention_months` | 12 | history kept 12 months |
| `photo_mb_per_device` | 0.5 | one compressed photo per plant |
| `tips_per_premium_device_month` | 30 | one cached refresh a day (ADR-006) |
| `tips_tokens_in` | 2000 | plant, readings, forecast, instructions |
| `tips_tokens_out` | 500 | schema-constrained JSON |
| `profile_db_projects` | 1 | A-011: user profiles in a separate DB |
| `min_users_for_pro` | 100 | free tier is for the demo only |
<!-- END:ASSUMPTIONS -->

### 4.3 Formulas

<!-- BEGIN:FORMULAS -->
```text
fn_calls   = devices * reports_per_device_month + users * other_calls_per_user_month
db_gb      = devices * samples_per_device_month * retention_months * db_kb_per_sample / 1024^2
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
| Supabase plan | 0.00 | 35.00 | 35.00 |
| Supabase overage | 0.00 | 0.00 | 1.55 |
| Claude API (tips) | 0.40 | 5.40 | 54.00 |
| Expo push + EAS | 0.00 | 0.00 | 0.00 |
| Weather API | 0.00 | 0.00 | 0.00 |
| Store accounts | 0.00 | 8.94 | 8.94 |
| **Total USD** | **0.40** | **49.34** | **99.50** |
| **Total EUR** (FX 0.92) | **0.37** | **45.40** | **91.54** |
<!-- END:TOTALS -->

### 4.4a Result: database size (corrected: 15-minute samples)

The unit of record is one 15-minute sample, 96 per day = 2880 rows per device-month (PR #15, `db-schema.sql`, interface decision 1). Function calls stay hourly (one POST per hour). An earlier version of this model counted rows at the hourly rate, which understated DB size by 4x.

<!-- BEGIN:DBSIZE -->
| DB size (raw sample rows, 12 months kept) | 3 demo units | 100 users | 1000 users |
|---|---|---|---|
| Rows | 103,680 | 6,912,000 | 69,120,000 |
| DB size GB | 0.03 | 1.98 | 19.78 |
| Pro quota 8 GB: | within | within | OVER by 11.78 GB |
| Max retention (months) that fits the Pro quota | >120 | 48.5 | 4.9 |
<!-- END:DBSIZE -->

**Consequence:** at 1000 users the raw 12-month history (19.78 GB) exceeds the 8 GB Pro quota (unverified). The model prices the excess as overage (0.125 USD per GB-month, about 1.5 USD), so the money is small; the real effects are a growing disk, slower history queries and backups, and the need to decide a retention policy before the first customers. 100 users (1.98 GB) fit with room. Options, not decided here: (a) keep 12 months raw and pay the overage; (b) keep raw samples about 4 months and roll older data up to hourly or daily min/avg/max (pg_cron job), which keeps the 12-month charts; (c) shorter raw retention only. This is a product/data decision (Q5), not a technical blocker.

### 4.5 Result: cost per user (free vs premium)

<!-- BEGIN:PERUSER -->
| Cost per user per month (USD) | 3 demo units | 100 users | 1000 users |
|---|---|---|---|
| Fully loaded (total / users, mixed free+premium) | 0.40 | 0.49 | 0.10 |
| Marginal free user (worst case, over quota) | 0.0041 | 0.0041 | 0.0041 |
| Marginal premium user (adds tips) | 0.27 | 0.27 | 0.27 |
| Fully loaded if weather = Open-Meteo commercial plan | 29.41 | 0.78 | 0.13 |
<!-- END:PERUSER -->

### 4.6 Reading the numbers

- The cloud is cheap per user once past the fixed Supabase fee: a free user costs a fraction of a cent in function calls; a premium user costs about 0.27 USD a month, almost all of it Claude tips. Under these unverified prices, a premium price above roughly 1 USD a month covers the variable cost, with the fixed fee as the real hurdle at 100 users.
- The "100 users" column is dominated by fixed costs (Supabase Pro + second project + store accounts); the 1000-user column by Claude. The demo costs about the Claude calls only, and nothing if tips are cached or switched off.
- Open-Meteo's commercial plan would add a fixed fee that is large relative to the demo and the first customers; this is why the weather pick matters.
- Sensitivity worth re-running once prices are verified: `tips_per_premium_device_month` (caching hit rate), the model tier (token price), `premium_share`, and whether a separate profile project is really needed (`profile_db_projects`).
- Not modelled: hardware, shipping, payment-provider fees (no payments yet, ADR-008), support time, VAT, a domain, e-mail sending for auth, Supabase compute add-ons if load grows, backups beyond the plan.

## 5. Questions for Arsany (real decisions only)

| ID | Decision | Options | Recommendation |
|---|---|---|---|
| Q1 | A-011: confirm that profiles live in a separate DB and that Claude/Expo get only a pseudonymous id | accept / require EU-only LLM and push path (costs more, blocks Expo push) | Accept; it is cheap (one extra project) and keeps the privacy notes honest |
| Q2 | Weather provider (A-2): may we rely on DWD open data via Bright Sky for the demo and German customers, subject to someone reading the DWD terms? | accept / pay Open-Meteo commercial plan from day one | Accept DWD; a human reads the two URLs in section 3 before the first customer demo |
| Q3 | Are the apps published in the App Store and Play Store, or is the first phase a demo with TestFlight/sideloaded builds? Store accounts need an Arsany sign-up and card, which agents may not do | stores now / demo builds only | Demo builds first; sign up for the Apple programme only when a customer needs iOS |
| Q4 | Supabase tier for the first paying customers: Pro (backups, no pausing) from the first customer, or free tier until the demo is over | Pro from first customer / free for demo | Free for the 3-unit demo, Pro from the first customer |
| Q5 | Retention of raw 15-minute sample history (see 4.4a): at 1000 users 12 months raw is 19.78 GB, over the 8 GB Pro quota | keep 12 months raw and pay overage / 4 months raw plus hourly or daily roll-up for older data / shorter history | Roll-up after about 4 months: charts keep their 12-month range, DB stays near the quota; decide before the first customers, not now |

Note for Kai (DevOps): CI does not run `docs/costs/` (no workstream gate covers it), so the doc-drift test only protects the doc when someone runs it: `cd projects/plant-monitor/docs/costs && python3 -m unittest discover -v`. Please add a gate or step; `ci.yml` is not changed in this PR.

Not decisions, but tasks for a human: tick every "Check here" URL in 4.1 and section 3 and replace `unverified` in `cost_model.py` with the verified date (Nora can list this as a work item).

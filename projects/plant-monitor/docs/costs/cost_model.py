#!/usr/bin/env python3
"""Running-cost model for the Plant Monitor cloud (task 2.6, FR-P01..P04, NFR-04, NFR-07).

Decisions applied: A-025 (one free Supabase DB for the demo, ~3 months raw then roll-up, demo costs zero).

Stdlib only. Every price/limit below is UNVERIFIED: network access was blocked when this
was written and nothing was checked against the provider's page. Each entry carries the
URL a human must check. Change a number here, run `python cost_model.py --markdown`, and
paste the output into stack-and-costs.md (a unit test fails if the doc drifts).

All money is in USD as the providers list it; EUR is shown with FX below.
"""
from __future__ import annotations

import argparse
import math
from dataclasses import dataclass, replace

STATUS = "unverified"

# ---- provider prices and limits (all UNVERIFIED) ---------------------------------------
PRICES = {
    # name: (value, unit, source URL a human must check)
    "supabase_pro_base":        (25.0, "USD/month per org", "https://supabase.com/pricing"),
    "supabase_extra_project":   (10.0, "USD/month per extra Micro project", "https://supabase.com/pricing"),
    "supabase_fn_overage":      (2.0, "USD per 1M edge-function invocations over quota", "https://supabase.com/pricing"),
    "supabase_db_overage":      (0.125, "USD per GB-month DB over quota", "https://supabase.com/pricing"),
    "supabase_storage_overage": (0.021, "USD per GB-month storage over quota", "https://supabase.com/pricing"),
    "claude_in":                (1.0, "USD per 1M input tokens (small model tier)", "https://www.anthropic.com/pricing"),
    "claude_out":               (5.0, "USD per 1M output tokens (small model tier)", "https://www.anthropic.com/pricing"),
    "expo_push":                (0.0, "USD, push service free of charge", "https://docs.expo.dev/push-notifications/overview/"),
    "eas_build":                (0.0, "USD, EAS free plan (limited builds)", "https://expo.dev/pricing"),
    "apple_developer":          (99.0, "USD/year", "https://developer.apple.com/programs/"),
    "google_play":              (25.0, "USD one-off (amortised over 36 months here)", "https://play.google.com/console/about/"),
    "weather_dwd_brightsky":    (0.0, "USD, DWD open data via Bright Sky", "https://brightsky.dev/docs/ and https://www.dwd.de/DE/leistungen/opendata/nutzungsbedingungen.html"),
    "weather_openmeteo_commercial": (29.0, "USD/month fallback plan, size unknown", "https://open-meteo.com/en/pricing"),
}

LIMITS = {
    # tier: dict of included quotas (UNVERIFIED, https://supabase.com/pricing)
    "free": {"db_gb": 0.5, "storage_gb": 1.0, "fn_invocations": 500_000},
    "pro":  {"db_gb": 8.0, "storage_gb": 100.0, "fn_invocations": 2_000_000},
}

FX_EUR_PER_USD = 0.92  # assumption, not a quote
AMORTISE_GOOGLE_MONTHS = 36


@dataclass(frozen=True)
class Assumptions:
    """Usage assumptions (ours, not provider data). Change and regenerate."""
    devices_per_user: float = 2.0
    premium_share: float = 0.20
    reports_per_device_month: int = 24 * 30       # hourly upload = one POST per hour (function calls)
    samples_per_device_month: int = 96 * 30       # 15-min samples = DB rows (PR #15 db-schema, 2880)
    other_calls_per_user_month: int = 600          # app, alerts, claim, analytics, MCP
    db_kb_per_sample: float = 0.3                  # row + index
    retention_months: int = 12                     # total history visible (raw + roll-up)
    raw_months: int = 3                            # A-025: ~3 months of raw 15-min samples, then roll-up
    rollup_rows_per_device_month: int = 720        # hourly min/avg/max row per device (24 * 30)
    db_kb_per_rollup: float = 0.3                  # roll-up row plus index, rough (same as a sample)
    photo_mb_per_device: float = 0.5
    tips_per_premium_device_month: float = 30.0    # about one refresh per day, cached
    demo_tips_per_device_month: float = 0.0        # A-025: demo costs nothing -> no live Claude tips in the demo (canned rule-layer tips)
    tips_tokens_in: int = 2000
    tips_tokens_out: int = 500
    profile_db_projects: int = 0                   # A-025: ONE database (supersedes the separate profile DB of A-011)
    min_users_for_pro: int = 100                   # free tier pauses/has no backups: not for customers


@dataclass(frozen=True)
class Scenario:
    name: str
    users: int
    devices: int          # total devices
    premium_users: int
    store_accounts: bool  # App Store / Play fees apply
    weather: str = "dwd_brightsky"
    premium_devices: float = -1  # devices owned by premium users; -1 = premium_users * devices_per_user
    demo: bool = False           # demo units: live LLM tips off (a.demo_tips_per_device_month per device)


def supabase_tier(sc: Scenario, a: Assumptions) -> str:
    """Pick tier: free for demo; pro when customers exist or any free quota is exceeded."""
    if sc.users >= a.min_users_for_pro:
        return "pro"
    u = usage(sc, a)
    lim = LIMITS["free"]
    if u["db_gb"] > lim["db_gb"] or u["storage_gb"] > lim["storage_gb"] or u["fn"] > lim["fn_invocations"]:
        return "pro"
    return "free"


def db_gb_for(devices: float, a: Assumptions, raw_only: bool = False) -> float:
    """DB size: raw 15-min samples for raw_months, then hourly roll-up rows for the rest of retention_months.
    raw_only=True gives the old model (everything raw for retention_months) for comparison."""
    raw_m = a.retention_months if raw_only else min(a.raw_months, a.retention_months)
    roll_m = 0 if raw_only else max(0, a.retention_months - a.raw_months)
    kb = a.samples_per_device_month * raw_m * a.db_kb_per_sample + a.rollup_rows_per_device_month * roll_m * a.db_kb_per_rollup
    return devices * kb / 1024 / 1024


def usage(sc: Scenario, a: Assumptions) -> dict:
    fn = sc.devices * a.reports_per_device_month + sc.users * a.other_calls_per_user_month
    db_gb = db_gb_for(sc.devices, a)
    storage_gb = sc.devices * a.photo_mb_per_device / 1024
    pdev = sc.premium_devices if sc.premium_devices >= 0 else sc.premium_users * a.devices_per_user
    tips = sc.devices * a.demo_tips_per_device_month if sc.demo else pdev * a.tips_per_premium_device_month
    return {"fn": fn, "db_gb": db_gb, "storage_gb": storage_gb, "tips_calls": tips}


def claude_cost_per_call(a: Assumptions) -> float:
    return (a.tips_tokens_in * PRICES["claude_in"][0] + a.tips_tokens_out * PRICES["claude_out"][0]) / 1e6


def monthly_costs(sc: Scenario, a: Assumptions = Assumptions()) -> dict:
    """Monthly cost lines in USD for one scenario."""
    u = usage(sc, a)
    tier = supabase_tier(sc, a)
    lim = LIMITS[tier]
    lines = {}
    if tier == "pro":
        lines["Supabase plan"] = PRICES["supabase_pro_base"][0] + a.profile_db_projects * PRICES["supabase_extra_project"][0]
    else:
        lines["Supabase plan"] = 0.0
    lines["Supabase overage"] = (
        max(0.0, u["fn"] - lim["fn_invocations"]) / 1e6 * PRICES["supabase_fn_overage"][0]
        + max(0.0, u["db_gb"] - lim["db_gb"]) * PRICES["supabase_db_overage"][0]
        + max(0.0, u["storage_gb"] - lim["storage_gb"]) * PRICES["supabase_storage_overage"][0]
    )
    lines["Claude API (tips)"] = u["tips_calls"] * claude_cost_per_call(a)
    lines["Expo push + EAS"] = PRICES["expo_push"][0] + PRICES["eas_build"][0]
    wkey = "weather_dwd_brightsky" if sc.weather == "dwd_brightsky" else "weather_openmeteo_commercial"
    lines["Weather API"] = PRICES[wkey][0]
    lines["Store accounts"] = (
        PRICES["apple_developer"][0] / 12 + PRICES["google_play"][0] / AMORTISE_GOOGLE_MONTHS
        if sc.store_accounts else 0.0
    )
    lines["_tier"] = tier
    return lines


def total(lines: dict) -> float:
    return sum(v for k, v in lines.items() if not k.startswith("_"))


def per_user(sc: Scenario, a: Assumptions = Assumptions()) -> dict:
    """Fully loaded cost per user plus marginal cost of one free / one premium user."""
    lines = monthly_costs(sc, a)
    tot = total(lines)
    # marginal: usage-driven lines only (what one more user adds), at current tier
    free_user = Scenario("m", 1, math.ceil(a.devices_per_user), 0, False)
    prem_user = Scenario("m", 1, math.ceil(a.devices_per_user), 1, False)
    fn_cost = lambda s: usage(s, a)["fn"] / 1e6 * PRICES["supabase_fn_overage"][0]
    claude = usage(prem_user, a)["tips_calls"] * claude_cost_per_call(a)
    return {
        "total": tot,
        "loaded": tot / sc.users,
        "marginal_free": fn_cost(free_user),   # priced as if over quota (worst case)
        "marginal_premium": fn_cost(prem_user) + claude,
    }


def scenarios(a: Assumptions = Assumptions()) -> list:
    def mk(name, users, store):
        prem = round(users * a.premium_share)
        return Scenario(name, users, round(users * a.devices_per_user), prem, store)
    return [
        Scenario("3 demo units", 1, 3, 1, False, premium_devices=3, demo=True),
        mk("100 users", 100, True),
        mk("1000 users", 1000, True),
    ]


# ---- markdown generation ----------------------------------------------------------------
def _usd(x: float, nd: int = 2) -> str:
    return f"{x:,.{nd}f}"


def table_prices() -> str:
    rows = ["| Item | Assumed value | Unit | Status | Check here |", "|---|---|---|---|---|"]
    for k, (v, unit, url) in PRICES.items():
        rows.append(f"| `{k}` | {v:g} | {unit} | {STATUS} | {url} |")
    for tier, lim in LIMITS.items():
        rows.append(f"| Supabase `{tier}` quotas | DB {lim['db_gb']:g} GB, storage {lim['storage_gb']:g} GB, "
                    f"{lim['fn_invocations']:,} fn calls | per month | {STATUS} | https://supabase.com/pricing |")
    return "\n".join(rows)


def table_assumptions(a: Assumptions = Assumptions()) -> str:
    rows = ["| Assumption | Value | Why |", "|---|---|---|"]
    why = {
        "devices_per_user": "typical household; 3 demo units are 1 demo user",
        "premium_share": "planning guess, no data",
        "reports_per_device_month": "hourly upload = 1 POST/hour, counts function calls",
        "samples_per_device_month": "15-min samples = DB rows, 96/day (PR #15 db-schema)",
        "other_calls_per_user_month": "app, alerts, analytics, MCP",
        "db_kb_per_sample": "row plus index, rough",
        "retention_months": "total history kept 12 months (raw + roll-up)",
        "raw_months": "A-025: about 3 months raw 15-min samples, older data rolled up",
        "rollup_rows_per_device_month": "hourly min/avg/max, 24 * 30",
        "db_kb_per_rollup": "roll-up row plus index, rough",
        "demo_tips_per_device_month": "A-025: demo must cost zero, so no live Claude tips in the demo",
        "photo_mb_per_device": "one compressed photo per plant",
        "tips_per_premium_device_month": "one cached refresh a day (ADR-006)",
        "tips_tokens_in": "plant, readings, forecast, instructions",
        "tips_tokens_out": "schema-constrained JSON",
        "profile_db_projects": "A-025: one database for profiles and sensor data (no second project)",
        "min_users_for_pro": "free tier is for the demo only",
    }
    for k, v in a.__dict__.items():
        rows.append(f"| `{k}` | {v:g} | {why[k]} |")
    return "\n".join(rows)


def table_totals(a: Assumptions = Assumptions()) -> str:
    scs = scenarios(a)
    names = list(monthly_costs(scs[0], a))
    names = [n for n in names if not n.startswith("_")]
    head = "| Monthly cost (USD) | " + " | ".join(s.name for s in scs) + " |"
    rows = [head, "|---|" + "---|" * len(scs)]
    rows.append("| Users / devices / premium | " + " | ".join(f"{s.users} / {s.devices} / {s.premium_users}" for s in scs) + " |")
    rows.append("| Supabase tier | " + " | ".join(monthly_costs(s, a)["_tier"] for s in scs) + " |")
    for n in names:
        rows.append(f"| {n} | " + " | ".join(_usd(monthly_costs(s, a)[n]) for s in scs) + " |")
    rows.append("| **Total USD** | " + " | ".join(f"**{_usd(total(monthly_costs(s, a)))}**" for s in scs) + " |")
    rows.append("| **Total EUR** (FX %.2f) | " % FX_EUR_PER_USD + " | ".join(
        f"**{_usd(total(monthly_costs(s, a)) * FX_EUR_PER_USD)}**" for s in scs) + " |")
    return "\n".join(rows)


def table_per_user(a: Assumptions = Assumptions()) -> str:
    scs = scenarios(a)
    rows = ["| Cost per user per month (USD) | " + " | ".join(s.name for s in scs) + " |", "|---|" + "---|" * len(scs)]
    pu = [per_user(s, a) for s in scs]
    rows.append("| Fully loaded (total / users, mixed free+premium) | " + " | ".join(_usd(p["loaded"]) for p in pu) + " |")
    rows.append("| Marginal free user (worst case, over quota) | " + " | ".join(_usd(p["marginal_free"], 4) for p in pu) + " |")
    rows.append("| Marginal premium user (adds tips) | " + " | ".join(_usd(p["marginal_premium"]) for p in pu) + " |")
    alt = [replace(s, weather="openmeteo") for s in scs]
    rows.append("| Fully loaded if weather = Open-Meteo commercial plan | " + " | ".join(
        _usd(total(monthly_costs(s, a)) / s.users) for s in alt) + " |")
    return "\n".join(rows)


def table_db(a: Assumptions = Assumptions()) -> str:
    scs = scenarios(a)
    q = LIMITS["pro"]["db_gb"]
    rows = ["| DB size (%d months raw, then hourly roll-up to %d months) | " % (a.raw_months, a.retention_months)
            + " | ".join(s.name for s in scs) + " |", "|---|" + "---|" * len(scs)]
    gb = [usage(s, a)["db_gb"] for s in scs]
    raw12 = [db_gb_for(s.devices, a, raw_only=True) for s in scs]
    rows.append("| Rows (raw + roll-up) | " + " | ".join(
        f"{s.devices * (a.samples_per_device_month * a.raw_months + a.rollup_rows_per_device_month * (a.retention_months - a.raw_months)):,}"
        for s in scs) + " |")
    rows.append("| DB size GB | " + " | ".join(_usd(g) for g in gb) + " |")
    rows.append("| Pro quota %g GB: | " % q + " | ".join("OVER by %s GB" % _usd(g - q) if g > q else "within" for g in gb) + " |")
    rows.append("| For comparison: all %d months raw, GB | " % a.retention_months + " | ".join(_usd(g) for g in raw12) + " |")
    rows.append("| For comparison: free quota %g GB: | " % LIMITS["free"]["db_gb"] + " | ".join(
        "OVER" if g > LIMITS["free"]["db_gb"] else "within" for g in gb) + " |")
    return "\n".join(rows)


def formulas() -> str:
    return "\n".join([
        "```text",
        "fn_calls   = devices * reports_per_device_month + users * other_calls_per_user_month",
        "db_gb      = devices * (samples_per_device_month * raw_months * kb_sample + rollup_rows_per_device_month * (retention_months - raw_months) * kb_rollup) / 1024^2",
        "storage_gb = devices * photo_mb_per_device / 1024",
        "tips_calls = premium_devices * tips_per_premium_device_month   (premium_devices = premium_users * devices_per_user)",
        "claude     = tips_calls * (tokens_in * price_in + tokens_out * price_out) / 1e6",
        "supabase   = tier base (pro: base + profile_db_projects * extra_project; free: 0) + overage over quota",
        "store      = apple_year / 12 + google_once / 36        (only when published in the stores)",
        "total      = supabase + claude + push + weather + store",
        "per user   = total / users;  marginal premium = marginal free + one user's tips calls * claude cost",
        "```",
    ])


def markdown() -> str:
    parts = [
        ("PRICES", table_prices()), ("ASSUMPTIONS", table_assumptions()), ("FORMULAS", formulas()),
        ("TOTALS", table_totals()), ("DBSIZE", table_db()), ("PERUSER", table_per_user()),
    ]
    return "\n\n".join(f"<!-- BEGIN:{k} -->\n{v}\n<!-- END:{k} -->" for k, v in parts)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--markdown", action="store_true", help="print the generated doc tables")
    p.parse_args()
    print(markdown())


if __name__ == "__main__":
    main()

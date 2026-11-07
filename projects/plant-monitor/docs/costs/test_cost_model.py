"""Unit tests for cost_model.py (stdlib unittest). Run: python -m unittest discover -v"""
import re
import unittest
from pathlib import Path

import cost_model as cm

A = cm.Assumptions()
DOC = Path(__file__).resolve().parent.parent / "stack-and-costs.md"


class ModelTests(unittest.TestCase):
    def test_every_price_is_unverified_and_has_url(self):
        for k, (v, unit, url) in cm.PRICES.items():
            self.assertTrue(url.startswith("http"), k)
        self.assertEqual(cm.STATUS, "unverified")

    def test_claude_cost_per_call(self):
        # 2000*1 + 500*5 = 4500 / 1e6 USD
        self.assertAlmostEqual(cm.claude_cost_per_call(A), 0.0045)

    def test_demo_costs_zero(self):
        # A-025/A-029: demo = free tier, one DB, DWD weather, no store accounts, rule-based tips (live Claude is off by default)
        sc = cm.scenarios()[0]
        lines = cm.monthly_costs(sc)
        self.assertEqual(lines["_tier"], "free")
        self.assertEqual(cm.total(lines), 0.0)
        self.assertEqual(lines["Claude API (tips)"], 0)
        self.assertTrue(sc.demo)
        self.assertEqual(A.demo_tips_mode, "rule_based")

    def test_demo_with_live_tips_costs_only_claude(self):
        sc = cm.scenarios()[0]
        a = cm.Assumptions(demo_tips_mode="live")  # A-029 flag on
        lines = cm.monthly_costs(sc, a)
        self.assertAlmostEqual(cm.total(lines), 90 * 0.0045)

    def test_demo_fits_free_quotas(self):
        u = cm.usage(cm.scenarios()[0], A)
        free = cm.LIMITS["free"]
        self.assertLess(u["db_gb"], free["db_gb"])
        self.assertLess(u["storage_gb"], free["storage_gb"])
        self.assertLess(u["fn"], free["fn_invocations"])

    def test_one_database_by_default(self):
        self.assertEqual(A.profile_db_projects, 0)
        lines = cm.monthly_costs(cm.scenarios()[1])
        self.assertEqual(lines["_tier"], "pro")
        self.assertAlmostEqual(lines["Supabase plan"], 25)   # A-025: no second project

    def test_second_project_would_add_ten(self):
        sc = cm.scenarios()[1]
        a1 = cm.Assumptions(profile_db_projects=1)
        self.assertAlmostEqual(cm.monthly_costs(sc, a1)["Supabase plan"] - cm.monthly_costs(sc)["Supabase plan"], 10)

    def test_usage_numbers_100_users(self):
        sc = cm.scenarios()[1]
        u = cm.usage(sc, A)
        self.assertEqual(sc.devices, 200)
        self.assertEqual(u["fn"], 200 * 720 + 100 * 600)
        self.assertEqual(u["tips_calls"], 20 * 2 * 30)

    def test_db_rows_use_15min_samples(self):
        self.assertEqual(A.samples_per_device_month, 2880)
        self.assertEqual(A.reports_per_device_month, 720)

    def test_rollup_after_three_months_raw(self):
        self.assertEqual(A.raw_months, 3)
        u = cm.usage(cm.scenarios()[2], A)
        raw = 2000 * 2880 * 3 * 0.3
        roll = 2000 * 720 * 9 * 0.3
        self.assertAlmostEqual(u["db_gb"], (raw + roll) / 1024 / 1024)
        # all-raw for 12 months would be 19.78 GB (old model), roll-up is less than half
        all_raw = cm.db_gb_for(2000, A, raw_only=True)
        self.assertAlmostEqual(all_raw, 2000 * 2880 * 12 * 0.3 / 1024 / 1024)
        self.assertLess(u["db_gb"], all_raw / 2)

    def test_overage_kicks_in_over_quota(self):
        big = cm.Scenario("big", 5000, 10000, 0, True)
        self.assertGreater(cm.monthly_costs(big)["Supabase overage"], 0)
        self.assertEqual(cm.monthly_costs(cm.scenarios()[1])["Supabase overage"], 0)

    def test_free_tier_auto_upgrades_when_exceeded(self):
        sc = cm.Scenario("x", 50, 1000, 0, False)  # 720k calls > 500k free quota
        self.assertEqual(cm.supabase_tier(sc, A), "pro")

    def test_premium_marginal_exceeds_free_marginal_by_tips(self):
        p = cm.per_user(cm.scenarios()[2])
        self.assertAlmostEqual(p["marginal_premium"] - p["marginal_free"], 60 * 0.0045)

    def test_loaded_cost_decreases_with_scale(self):
        l = [cm.per_user(s)["loaded"] for s in cm.scenarios()[1:]]
        self.assertGreater(l[0], l[1])

    def test_total_is_sum_of_lines(self):
        lines = cm.monthly_costs(cm.scenarios()[2])
        self.assertAlmostEqual(cm.total(lines), sum(v for k, v in lines.items() if k[0] != "_"))

    def test_weather_alternative_adds_fixed_fee(self):
        sc = cm.scenarios()[1]
        alt = cm.replace(sc, weather="openmeteo")
        self.assertAlmostEqual(cm.total(cm.monthly_costs(alt)) - cm.total(cm.monthly_costs(sc)), 29.0)


class DocDriftTests(unittest.TestCase):
    def test_doc_tables_match_script(self):
        self.assertTrue(DOC.exists(), f"doc missing: {DOC}")
        text = DOC.read_text(encoding="utf-8")
        for key in ("PRICES", "ASSUMPTIONS", "FORMULAS", "TOTALS", "DBSIZE", "PERUSER"):
            m = re.search(rf"<!-- BEGIN:{key} -->\n(.*?)\n<!-- END:{key} -->", text, re.S)
            self.assertIsNotNone(m, key)
            self.assertIn(f"<!-- BEGIN:{key} -->\n{m.group(1)}\n<!-- END:{key} -->", cm.markdown(), key)


if __name__ == "__main__":
    unittest.main()

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

    def test_demo_is_free_tier_and_costs_only_claude(self):
        sc = cm.scenarios()[0]
        lines = cm.monthly_costs(sc)
        self.assertEqual(lines["_tier"], "free")
        self.assertEqual(lines["Supabase plan"], 0)
        self.assertEqual(lines["Store accounts"], 0)
        # 3 demo devices, 30 tips each
        self.assertAlmostEqual(lines["Claude API (tips)"], 90 * 0.0045)

    def test_pro_from_100_users_with_separate_profile_db(self):
        lines = cm.monthly_costs(cm.scenarios()[1])
        self.assertEqual(lines["_tier"], "pro")
        self.assertAlmostEqual(lines["Supabase plan"], 25 + 10)  # A-011 second project

    def test_no_profile_db_is_cheaper(self):
        sc = cm.scenarios()[1]
        a0 = cm.Assumptions(profile_db_projects=0)
        self.assertAlmostEqual(cm.monthly_costs(sc)["Supabase plan"] - cm.monthly_costs(sc, a0)["Supabase plan"], 10)

    def test_usage_numbers_100_users(self):
        sc = cm.scenarios()[1]
        u = cm.usage(sc, A)
        self.assertEqual(sc.devices, 200)
        self.assertEqual(u["fn"], 200 * 720 + 100 * 600)
        self.assertEqual(u["tips_calls"], 20 * 2 * 30)

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
        if not DOC.exists():
            self.skipTest("doc not present")
        text = DOC.read_text(encoding="utf-8")
        for key in ("PRICES", "ASSUMPTIONS", "FORMULAS", "TOTALS", "PERUSER"):
            m = re.search(rf"<!-- BEGIN:{key} -->\n(.*?)\n<!-- END:{key} -->", text, re.S)
            self.assertIsNotNone(m, key)
            self.assertIn(f"<!-- BEGIN:{key} -->\n{m.group(1)}\n<!-- END:{key} -->", cm.markdown(), key)


if __name__ == "__main__":
    unittest.main()

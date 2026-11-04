"""Unit tests for power_budget.py (NFR-01).  Run: python3 -m unittest -v  (in this folder)."""
import dataclasses
import unittest

import power_budget as pb


def simple() -> pb.Params:
    """Round numbers so every expected value can be checked by hand."""
    return pb.Params(
        i_mcu_sleep_ua=10, i_ldo_iq_ua=0, i_charger_prot_ua=0, r_divider_mohm=3.7,   # divider = 1 uA
        i_aht20_sleep_ua=0, i_bh1750_pd_ua=0, i_soil_gate_leak_ua=0,
        interval_min=15, t_boot_s=1.0, t_sense_s=2.0, t_infer_s=0.0, t_store_s=0.0,
        i_cpu_ma=10, i_periph_ma=10,
        reports_per_day=24, critical_wakes_per_day=0,
        t_connect_s=2.0, t_cloud_s=1.0, t_hub_s=1.0, hub_every_n=1,
        i_rx_ma=100, i_tx_ma=200, f_tx=0.5,
        self_discharge_pct_month=0, usable_fraction=1.0)


class HandCalc(unittest.TestCase):
    def test_sleep_current(self):
        self.assertAlmostEqual(pb.sleep_current_ua(simple()), 11.0)          # 10 + 3.7/3.7

    def test_daily_budget(self):
        d = pb.daily_budget(simple())
        self.assertAlmostEqual(d["sleep"], 0.011 * 24)                       # 0.264 mAh
        # one sample wake: 1 s*10 mA + 2 s*20 mA = 50 mA*s ; 96 wakes
        self.assertAlmostEqual(pb.sample_wake_mas(simple()), 50.0)
        self.assertAlmostEqual(d["sample"], 96 * 50 / 3600)                  # 1.3333 mAh
        # session: 4 s at 0.5*200 + 0.5*100 = 150 mA = 600 mA*s ; 24 sessions
        self.assertAlmostEqual(pb.wifi_avg_ma(simple()), 150.0)
        self.assertAlmostEqual(d["wifi"], 24 * 600 / 3600)                   # 4.0 mAh
        self.assertAlmostEqual(d["total"], 0.264 + 96 * 50 / 3600 + 4.0)

    def test_hub_every_second_report_and_critical_wakes(self):
        p = pb.with_(simple(), hub_every_n=2)
        self.assertAlmostEqual(pb.wifi_session_s(p), 3.5)
        p = pb.with_(simple(), critical_wakes_per_day=6)
        self.assertAlmostEqual(pb.daily_budget(p)["wifi"], 30 * 600 / 3600)

    def test_required_capacity_no_self_discharge(self):
        d = pb.daily_budget(simple())["total"]
        expect = d * 4380 / 24 / 0.8                                         # derating 20 %
        self.assertAlmostEqual(pb.required_rated_mah(simple()), expect)

    def test_required_capacity_with_self_discharge(self):
        p = pb.with_(simple(), self_discharge_pct_month=2.0)                 # 12 % over 6 months
        load = pb.daily_budget(p)["total"] * 4380 / 24
        self.assertAlmostEqual(pb.required_rated_mah(p), load / (0.8 - 0.12))


class Consistency(unittest.TestCase):
    def test_required_capacity_reaches_exactly_six_months(self):
        for p in pb.SCENARIOS.values():
            c = pb.required_rated_mah(p)
            self.assertAlmostEqual(pb.life_days(p, c), 4380 / 24, delta=1.0)  # 182.5 d vs 6*30.4167

    def test_sleep_limit_is_inverse_of_required_capacity(self):
        p = pb.TYPICAL
        c = pb.required_rated_mah(p)
        self.assertAlmostEqual(pb.max_sleep_current_ua(p, c), pb.sleep_current_ua(p), places=6)

    def test_sleep_limit_sets_boundary(self):
        c = 2000.0
        lim = pb.max_sleep_current_ua(pb.TYPICAL, c)
        p = pb.with_(pb.TYPICAL, i_mcu_sleep_ua=pb.TYPICAL.i_mcu_sleep_ua + lim - pb.sleep_current_ua(pb.TYPICAL))
        self.assertAlmostEqual(pb.sleep_current_ua(p), lim, places=6)
        self.assertAlmostEqual(pb.required_rated_mah(p), c, places=3)

    def test_scenarios_are_ordered(self):
        b, t, w = (pb.daily_budget(p)["total"] for p in (pb.BEST, pb.TYPICAL, pb.WORST))
        self.assertLess(b, t)
        self.assertLess(t, w)
        self.assertLess(pb.required_rated_mah(pb.BEST), pb.required_rated_mah(pb.TYPICAL))
        self.assertLess(pb.required_rated_mah(pb.TYPICAL), pb.required_rated_mah(pb.WORST))

    def test_life_increases_with_capacity(self):
        self.assertLess(pb.life_days(pb.TYPICAL, 1000), pb.life_days(pb.TYPICAL, 2000))

    def test_impossible_when_self_discharge_eats_derated_capacity(self):
        p = pb.with_(pb.TYPICAL, self_discharge_pct_month=15.0)              # 90 % over 6 months > 80 %
        self.assertEqual(pb.required_rated_mah(p), float("inf"))


class Provenance(unittest.TestCase):
    def test_every_parameter_has_a_source_tag(self):
        names = {f.name for f in dataclasses.fields(pb.Params)}
        self.assertEqual(names, set(pb.SOURCES))
        for n, s in pb.SOURCES.items():
            self.assertTrue(s.split(":")[0] in ("datasheet-unverified", "assumption", "computed")
                            or s.startswith(("FR-", "edge-ai", "ADR-")), n)

    def test_constants_follow_owner_decisions(self):
        self.assertEqual(pb.DERATING, 0.8)           # PR #2 item 12
        self.assertEqual(pb.NFR01_HOURS, 4380.0)     # 6 months, acceptance matrix
        self.assertEqual(pb.LOW_BATTERY_V, 3.4)

    def test_report_runs(self):
        text = pb.report()
        for key in ("Scenario results", "Sensitivity", "What-if", "best", "typical", "worst"):
            self.assertIn(key, text)


if __name__ == "__main__":
    unittest.main()

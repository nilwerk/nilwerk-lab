"""Unit tests for power_budget.py (NFR-01).  Run: python3 -m unittest -v  (in this folder)."""
import dataclasses
import pathlib
import re
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
        expect = d * pb.NFR01_HOURS / 24 / 0.8                                         # derating 20 %
        self.assertAlmostEqual(pb.required_rated_mah(simple()), expect)

    def test_required_capacity_with_self_discharge(self):
        p = pb.with_(simple(), self_discharge_pct_month=2.0)                 # 6 % over 3 months
        load = pb.daily_budget(p)["total"] * pb.NFR01_HOURS / 24
        self.assertAlmostEqual(pb.required_rated_mah(p, with_self_discharge=True), load / (0.8 - 0.06))
        self.assertAlmostEqual(pb.required_rated_mah(p), load / 0.8)        # the rule has no SD term


class Consistency(unittest.TestCase):
    def test_required_capacity_reaches_exactly_nfr01_hours(self):
        for p in pb.SCENARIOS.values():
            for sd in (False, True):
                c = pb.required_rated_mah(p, with_self_discharge=sd)
                self.assertAlmostEqual(pb.life_days(p, c, with_self_discharge=sd), pb.NFR01_HOURS / 24, delta=1.0)

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
        p = pb.with_(pb.TYPICAL, self_discharge_pct_month=30.0)              # 90 % over 3 months > 80 %
        self.assertEqual(pb.required_rated_mah(p, with_self_discharge=True), float("inf"))


class Rule(unittest.TestCase):
    def test_headline_rule_is_derated_capacity_over_average_current(self):
        p = pb.TYPICAL
        i_avg = pb.avg_current_ma(p)
        hours_1500 = 0.8 * 1500 / i_avg
        self.assertAlmostEqual(pb.life_days(p, 1500) * 24, hours_1500, places=6)
        self.assertGreaterEqual(hours_1500, pb.NFR01_HOURS)                      # 1500 mAh passes by the rule
        self.assertAlmostEqual(hours_1500 / 24 / pb.MONTH_DAYS, 6.7, delta=0.05)
        self.assertGreaterEqual(pb.life_days(p, 1500, with_self_discharge=True) * 24, pb.NFR01_HOURS)   # SD line still passes 3 months
        self.assertLess(pb.life_days(p, 1000) * 24, pb.STRETCH_HOURS)       # 1000 mAh misses the 6-month stretch (information only)
        self.assertAlmostEqual(pb.required_rated_mah(p), pb.NFR01_HOURS * i_avg / 0.8)

    def test_cell_verdict_uses_1000_mah_minimum(self):
        """A-020 / A-021: 603449 cell, verdict on the 1000 mAh minimum, literal rule, no self-discharge term."""
        t = pb.TYPICAL
        hours = 0.8 * 1000 / pb.avg_current_ma(t)
        self.assertAlmostEqual(pb.derated_hours(t, pb.CELL_RATED_MIN_MAH), hours, places=6)
        self.assertGreaterEqual(hours, pb.NFR01_HOURS)                       # typical passes 3 months
        self.assertAlmostEqual(hours / pb.HOURS_PER_MONTH, 4.5, delta=0.05)
        self.assertLess(pb.derated_hours(pb.WORST, 1000), pb.NFR01_HOURS)    # stress bound fails
        self.assertGreaterEqual(pb.derated_hours(pb.BEST, 1000), pb.NFR01_HOURS)
        p = pb.with_(t, self_discharge_pct_month=50.0)                       # absurd value must not change the rule
        self.assertAlmostEqual(pb.derated_hours(p, 1000), pb.derated_hours(t, 1000))
        self.assertEqual((pb.CELL_RATED_TYP_MAH, pb.CELL_RATED_MIN_MAH), (1100.0, 1000.0))
        self.assertEqual(pb.BAY_MM, (51.0, 34.5, 6.3))

    def test_nfr12_limit_is_derived(self):
        lim = pb.max_sleep_current_ua(pb.TYPICAL, 1000)
        self.assertAlmostEqual(lim, 134.6, delta=0.5)
        self.assertEqual(pb.nfr12_limit_ua(), 50.0)                          # floor(0.4 x 134.6 / 25) x 25, accepted A-027
        self.assertAlmostEqual(50.0 / pb.sleep_current_ua(pb.WORST), 1.6, delta=0.05)
        self.assertAlmostEqual(50.0 / pb.sleep_current_ua(pb.TYPICAL), 3.8, delta=0.05)
        self.assertLess(pb.nfr12_limit_ua(), pb.NFR12_CEILING_UA)
        self.assertLessEqual(pb.nfr12_limit_ua(), lim)
        # a board at exactly the limit, other terms typical, still meets the rule
        p = pb.with_(pb.TYPICAL, i_mcu_sleep_ua=pb.TYPICAL.i_mcu_sleep_ua + 50 - pb.sleep_current_ua(pb.TYPICAL))
        self.assertGreaterEqual(pb.derated_hours(p, 1000), pb.NFR01_HOURS)
        # not hard-coded: margin and step change the value
        self.assertEqual(pb.nfr12_limit_ua(margin=1.0, step_ua=25.0), 125.0)
        self.assertEqual(pb.nfr12_limit_ua(margin=0.75), 100.0)
        self.assertLess(pb.max_sleep_current_ua(pb.TYPICAL, 1000, hours=4380.0), lim)   # 6-month stretch: tighter

    def test_light_sleep_lever_and_default_neutral(self):
        base = pb.daily_budget(pb.TYPICAL)["sample"]
        lever = pb.daily_budget(pb.with_(pb.TYPICAL, i_warmup_cpu_ma=0.5))["sample"]
        # 96 wakes x 1.5 s x (20 - 0.5) mA / 3600
        self.assertAlmostEqual(base - lever, 96 * 1.5 * 19.5 / 3600)
        same = pb.with_(pb.TYPICAL, i_warmup_cpu_ma=pb.TYPICAL.i_cpu_ma)
        self.assertAlmostEqual(pb.daily_budget(same)["sample"], base)

    def test_hub_unreachable_costs_more_and_backoff_helps(self):
        base = pb.daily_budget(pb.TYPICAL)["total"]
        down = pb.daily_budget(pb.with_(pb.TYPICAL, t_hub_s=3.0))["total"]
        back = pb.daily_budget(pb.with_(pb.TYPICAL, t_hub_s=3.0, hub_every_n=4))["total"]
        self.assertGreater(down, base)
        self.assertLess(back, base)

    def test_typical_wifi_session_is_5_5_s(self):
        self.assertAlmostEqual(pb.wifi_session_s(pb.TYPICAL), 5.5)
        p = pb.with_(pb.TYPICAL, t_connect_s=1.0, hub_every_n=2)
        self.assertAlmostEqual(pb.wifi_session_s(p), 3.5)              # the design target needs both levers


DOC = pathlib.Path(__file__).with_name("power-budget.md").read_text(encoding="utf-8")


class DocMatchesScript(unittest.TestCase):
    def test_generated_blocks_are_identical_to_script_output(self):
        for name, body in pb.report_sections().items():
            m = re.search(rf"<!-- BEGIN:{name} -->\n(.*?)<!-- END:{name} -->", DOC, re.S)
            self.assertIsNotNone(m, name)
            self.assertEqual(m.group(1).strip(), body.strip(), f"{name} stale: run --update-doc")

    def test_headline_numbers_in_section_1(self):
        sec1 = DOC.split("## 2.")[0]
        t = pb.TYPICAL
        d = pb.daily_budget(t)
        expect = [
            f"**{d['total']:.1f} mAh/day**", f"{pb.avg_current_ma(t):.3f} mA",
            f"**about {round(pb.required_rated_mah(t), -1):.0f} mAh rated**",
            f"best **about {round(pb.required_rated_mah(pb.BEST), -1):.0f} mAh**",
            f"worst **about {round(pb.required_rated_mah(pb.WORST), -1):.0f} mAh**",
            f"**yes, {pb.life_days(t, 1500) / pb.MONTH_DAYS:.1f} months**",
            f"typical **{pb.life_days(t, 2000) / pb.MONTH_DAYS:.1f} months**",
            f"1500 mAh: **{pb.life_days(t, 1500, with_self_discharge=True) / pb.MONTH_DAYS:.1f} months**",
            f"2000 mAh: **{pb.life_days(t, 2000, with_self_discharge=True) / pb.MONTH_DAYS:.1f} months**",
            f"rated capacity needed {pb.required_rated_mah(t, with_self_discharge=True):.0f} mAh instead of {pb.required_rated_mah(t):.0f} mAh",
            f"**{pb.max_sleep_current_ua(t, 2000):.0f} uA whole board for a 2000 mAh rated cell, {pb.max_sleep_current_ua(t, 1500):.0f} uA for 1500 mAh**",
            f"(with self-discharge: {pb.max_sleep_current_ua(t, 2000, with_self_discharge=True):.0f} uA and {pb.max_sleep_current_ua(t, 1500, with_self_discharge=True):.0f} uA)",
        ]
        for e in expect:
            self.assertIn(e, sec1)
        light = pb.with_(t, i_warmup_cpu_ma=0.5)
        self.assertIn(f"**-{d['total'] - pb.daily_budget(light)['total']:.2f} mAh/day", sec1)
        down = pb.daily_budget(pb.with_(t, t_hub_s=3.0))["total"] - d["total"]
        self.assertIn(f"costs **+{down:.1f} mAh/day**", sec1)

    def test_doc_session_statement_and_references(self):
        self.assertIn("5.5 s at about 99 mA", DOC)
        self.assertNotIn("typical row; to be confirmed", DOC)
        self.assertIn("A-008.2", DOC)
        self.assertIn("Levers are in section 7".lower(), DOC.lower().replace("the levers are", "levers are"))


class Provenance(unittest.TestCase):
    def test_every_parameter_has_a_source_tag(self):
        names = {f.name for f in dataclasses.fields(pb.Params)}
        self.assertEqual(names, set(pb.SOURCES))
        for n, s in pb.SOURCES.items():
            self.assertTrue(s.split(":")[0] in ("datasheet-unverified", "datasheet-read", "assumption", "computed")
                            or s.startswith(("FR-", "edge-ai", "ADR-")), n)

    def test_constants_follow_owner_decisions(self):
        self.assertEqual(pb.DERATING, 0.8)           # PR #2 item 12
        self.assertEqual(pb.NFR01_MONTHS, 3.0)       # A-020
        self.assertEqual(pb.NFR01_HOURS, 2190.0)     # 3 months, acceptance matrix
        self.assertEqual(pb.STRETCH_HOURS, 4380.0)   # 6 months stretch, information only
        self.assertEqual(pb.LOW_BATTERY_V, 3.4)      # A-008.2 'ok' on PR #2

    def test_report_runs(self):
        text = pb.report()
        for key in ("Scenario results", "Sensitivity", "What-if", "best", "typical", "worst"):
            self.assertIn(key, text)


if __name__ == "__main__":
    unittest.main()

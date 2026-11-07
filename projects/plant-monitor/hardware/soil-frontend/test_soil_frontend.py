"""Tests for soil_frontend.py.  Run: python3 -m unittest -v  (in this folder)."""
import math
import unittest

import soil_frontend as sf


class Soil(unittest.TestCase):
    def test_formula_hand_calc(self):
        # R=100k, C=100pF, Vcc=3, VT+=2, VT-=1: t = 1e-5 * (ln(2/1) + ln(2/1))
        f = sf.freq_hz(100.0, 2.0, 1.0, r=100e3, vcc=3.0)
        self.assertAlmostEqual(f, 1.0 / (1e-5 * 2 * math.log(2)), delta=1.0)

    def test_wetter_is_slower(self):
        self.assertLess(sf.freq_hz(60, 1.7, 1.0), sf.freq_hz(15, 1.7, 1.0))

    def test_limits_pass(self):
        for name, ok in sf.checks().items():
            self.assertTrue(ok, name)

    def test_limits_can_fail(self):
        # a 10 MOhm timing resistor must break the 10 kHz lower limit (the checks are not vacuous)
        self.assertLess(sf.freq_hz(58.5, 1.5, 1.14, r=10e6), sf.F_MIN_HZ)


if __name__ == "__main__":
    unittest.main()

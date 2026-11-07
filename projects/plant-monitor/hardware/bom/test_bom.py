"""BOM tests (Plan 2.5 follow-up).  Run: python3 -m unittest -v  (in this folder).  Offline: reads bom-draft.csv only."""
import pathlib
import re
import unittest

import bom_calc as bc

HERE = pathlib.Path(__file__).parent
ROWS = bc.load()
BY = {r["ref"]: r for r in ROWS}


class Charger(unittest.TestCase):
    """TP4056 datasheet REV_2.4 p.9: R_PROG = 1100 / I_BAT (R in kOhm, I in mA)."""
    CELL_MIN_MAH = 1000.0   # EEMB LP603449 datasheet: minimum capacity 1000 mAh; max charge 1C

    def test_r9_value_and_current(self):
        r_k = float(re.search(r"([\d.]+)k", BY["R9"]["description"]).group(1))
        i_ma = 1100.0 / r_k
        self.assertAlmostEqual(r_k, 2.4)
        self.assertAlmostEqual(i_ma, 458.3, delta=0.1)
        self.assertTrue(0.4 <= i_ma / self.CELL_MIN_MAH <= 0.5)               # about 0.5C, not above it
        self.assertLessEqual(i_ma * 1.15 / self.CELL_MIN_MAH, 0.55)           # datasheet +15 % tolerance
        self.assertLessEqual(i_ma * 1.15, 1100.0)                             # cell max charge 1C

    def test_r9_part_is_2k4(self):
        self.assertEqual(BY["R9"]["mpn"], "0603WAF2401T5E")                   # 2401 = 240 x 10 Ohm


class Completeness(unittest.TestCase):
    def test_required_lines_exist(self):
        for ref in ("B1", "U7", "R12", "J2", "R9"):
            self.assertIn(ref, BY)

    def test_unverified_rows_have_no_price(self):
        for r in ROWS:
            if r["status"] == "unverified":
                self.assertEqual(r["lcsc_pn"], "")
                self.assertEqual(r["price_breaks_usd(qty:price)"], "")

    def test_verified_rows_have_everything(self):
        for r in bc.priced(ROWS):
            for k in ("lcsc_pn", "lcsc_stock", "jlc_stock", "jlc_library_type", "verified_utc"):
                self.assertTrue(r[k] != "", (r["ref"], k))

    def test_basic_swap_done(self):
        self.assertEqual(BY["D3"]["jlc_library_type"], "base")


class Costs(unittest.TestCase):
    def test_hand_example(self):
        rows = [dict(ref="X", qty=2, status="verified-live", breaks=[(10, 1.0), (1000, 0.5), (2000, 0.25)],
                     jlc_library_type="expand", jlc_preferred="False")]
        self.assertEqual(bc.totals(rows), (2.0, 0.5))      # 3 pcs: first break; 1k needs 2000 pcs -> 0.25 x 2
        s = bc.summary(rows)
        self.assertEqual(s["fee_parts"], 1)
        self.assertAlmostEqual(s["fee3"], 3.07 / 3)

    def test_preferred_pays_no_fee(self):
        rows = [dict(ref="X", qty=1, status="verified-live", breaks=[(1, 1.0)], jlc_library_type="expand",
                     jlc_preferred="True")]
        self.assertEqual(bc.summary(rows)["fee_parts"], 0)

    def test_doc_matches_csv(self):
        doc = (HERE / "bom-draft.md").read_text()
        s = bc.summary(ROWS)
        for v in (s["comp3"], s["comp1k"], s["total3"], s["total1k"]):
            self.assertIn(f"{v:.2f}", doc)
        self.assertIn(bc.md_variants(ROWS), doc)           # generated tables are pasted verbatim
        self.assertIn(bc.md_lines(ROWS), doc)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""BOM cost per board at 3 and 1000 boards from bom-draft.csv (Plan 2.5).  Standard library only.

    python3 bom_calc.py            # prints the Markdown tables used in bom-draft.md

Rules (same as the first draft, so numbers stay comparable):
  * 3 boards: unit price at the FIRST LCSC price break (that is the minimum order; you pay for the break quantity).
  * 1000 boards: unit price at the highest break <= 1000 x qty_per_board (first break if none).
  * Lines with status `unverified` (no live price) are excluded from the sums and listed separately.
  * JLC Economic PCBA: loading fee per unique Extended part that is NOT flagged Preferred; Basic and Preferred are free.
    Fee amounts are read from jlcpcb.com/help/article/pcb-assembly-price (see FEES), per ORDER, spread over the boards.
"""
from __future__ import annotations

import csv
import pathlib

HERE = pathlib.Path(__file__).parent
CSV = HERE / "bom-draft.csv"

# jlcpcb.com/help/article/pcb-assembly-price and /pcb-assembly-faqs, read 2026-11-07 (USD)
FEES = {"extended_loading": 3.07, "setup": 8.18, "stencil": 1.53}
USD_EUR = 0.90          # ASSUMPTION, unverified rate
TARGET_EUR = 10.0       # NFR-09 about 10 EUR


def load(path=CSV):
    rows = []
    for r in csv.DictReader(open(path)):
        r["qty"] = int(r["qty_per_board"])
        r["breaks"] = [(int(a), float(b)) for a, b in
                       (t.split(":") for t in r["price_breaks_usd(qty:price)"].split())]
        rows.append(r)
    return rows


def unit_3pcs(r):
    return r["breaks"][0][1]


def unit_1k(r, boards=1000):
    need = boards * r["qty"]
    ok = [p for q, p in r["breaks"] if q <= need]
    return ok[-1] if ok else r["breaks"][0][1]


def priced(rows):
    return [r for r in rows if r["status"] == "verified-live" and r["breaks"] and r.get("alternative") != "yes"]


def totals(rows):
    p = priced(rows)
    return (sum(r["qty"] * unit_3pcs(r) for r in p), sum(r["qty"] * unit_1k(r) for r in p))


def fee_parts(rows):
    """Unique Extended, non-Preferred parts (each pays the Economic loading fee once per order)."""
    return [r for r in priced(rows) if r["jlc_library_type"] == "expand" and r["jlc_preferred"] != "True"]


def summary(rows, boards3=3, boards1k=1000):
    c3, c1k = totals(rows)
    n_fee = len(fee_parts(rows))
    fee = n_fee * FEES["extended_loading"]
    one_time = FEES["setup"] + FEES["stencil"]
    return dict(
        lines=len(rows), pieces=sum(r["qty"] for r in priced(rows)),
        unique_extended=sum(1 for r in priced(rows) if r["jlc_library_type"] == "expand"),
        unique_preferred=sum(1 for r in priced(rows) if r["jlc_preferred"] == "True"),
        unique_basic=sum(1 for r in priced(rows) if r["jlc_library_type"] == "base"),
        fee_parts=n_fee, comp3=c3, comp1k=c1k,
        fee3=fee / boards3, fee1k=fee / boards1k,
        onetime3=one_time / boards3, onetime1k=one_time / boards1k,
        total3=c3 + (fee + one_time) / boards3, total1k=c1k + (fee + one_time) / boards1k,
        unverified=[r["ref"] for r in rows if r not in priced(rows)])


def variant(rows, drop=(), qty_delta=None):
    """Copy of rows without `drop` refs and with qty changes {ref: delta}."""
    out = []
    for r in rows:
        if r["ref"] in drop:
            continue
        r = dict(r)
        r["qty"] += (qty_delta or {}).get(r["ref"], 0)
        out.append(r)
    return out


VARIANTS = {
    "A baseline (this BOM)": dict(),
    "B zero-IC soil front end (RC timing on GPIO, no U7/R12, one cap less)": dict(drop=("U7", "R12"), qty_delta={"C5-C11": -1}),
    "C = B + cell with built-in protection (no U4/Q1)": dict(drop=("U7", "R12", "U4", "Q1"), qty_delta={"C5-C11": -1}),
    "D = A, delete the second protection (cell has a PCM): no U4/Q1/R15, C9 (one 100 nF)": dict(drop=("U4", "Q1", "R15"), qty_delta={"C5-C11": -1}),
}


def md_tables(rows):
    return md_variants(rows) + "\n\n" + md_lines(rows)


def md_variants(rows):
    out = ["| Variant | Extended parts paying the fee | 3 boards USD/board (components + fee + setup/stencil) | 1000 boards USD/board |", "|---|---|---|---|"]
    for name, kw in VARIANTS.items():
        v = summary(variant(rows, **kw))
        out.append(f"| {name} | {v['fee_parts']} | {v['total3']:.2f} (EUR {v['total3'] * USD_EUR:.2f}) | {v['total1k']:.2f} (EUR {v['total1k'] * USD_EUR:.2f}) |")
    return "\n".join(out)


def md_lines(rows):
    s = summary(rows)
    out = ["| Line | Qty | LCSC | Type | Preferred | 3 pcs unit | 1k unit | USD/board 3 | USD/board 1k |", "|---|---|---|---|---|---|---|---|---|"]
    for r in priced(rows):
        out.append(f"| {r['ref']} | {r['qty']} | {r['lcsc_pn']} | {r['jlc_library_type']} | {r['jlc_preferred']} | {unit_3pcs(r):.4f} | {unit_1k(r):.4f} | {r['qty'] * unit_3pcs(r):.3f} | {r['qty'] * unit_1k(r):.3f} |")
    out.append(f"| **Total components** | {s['pieces']} pcs | | | | | | **{s['comp3']:.2f}** | **{s['comp1k']:.2f}** |")
    return "\n".join(out)


if __name__ == "__main__":
    rows = load()
    print(md_tables(rows))
    print()
    for k, v in summary(rows).items():
        print(f"{k}: {v:.4f}" if isinstance(v, float) else f"{k}: {v}")

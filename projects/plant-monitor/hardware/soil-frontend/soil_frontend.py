#!/usr/bin/env python3
"""Soil front end sizing check (Plan 2.5 follow-up, input to 4.P1).  Standard library only.  Run: python3 soil_frontend.py

Topology: one Schmitt-trigger inverter (U7 = SN74LVC1G14) with a timing resistor R12 from output to input and the
probe capacitance (PCB copper on the stake, to GND) at the input = RC relaxation oscillator.  U7 is powered from an
ESP32 GPIO (GPIO low = 0 uA leakage, no gate MOSFET).  The ESP32 counts edges (PCNT) for a fixed gate time; wetter
soil = more capacitance = lower frequency.

    t_high = R C ln((Vcc - VT-) / (Vcc - VT+))      output high, C charges from VT- to VT+
    t_low  = R C ln(VT+ / VT-)                      output low,  C discharges from VT+ to VT-
    f      = 1 / (t_high + t_low)

Thresholds: SN74LVC1G14 datasheet SCES218AA (Oct 2025), section 5.5 Electrical Characteristics, DBV package,
-40..85 C, VCC = 3 V row (the table has no 3.3 V row; 3.0 V is used for Vcc as well, 3.3 V would move f by a few %):
VT+ 1.50..1.87 V, VT- 0.84..1.14 V.  Every combination of the four corners is checked.

NOT from a datasheet (assumptions, to be measured on the real stake, tasks 4.P2/5.x): the probe capacitance range
and the parasitic capacitance.  They are inputs below and tagged ASSUMPTION.
"""
from __future__ import annotations

import itertools
import math

VCC = 3.0                      # V, thresholds are tabulated at 3 V
VT_PLUS = (1.50, 1.87)         # V min, max (datasheet)
VT_MINUS = (0.84, 1.14)        # V min, max (datasheet)
C_IN_PF = 4.5                  # pF, datasheet Ci at 3.3 V (typ)
C_PARASITIC_PF = 3.0           # pF, ASSUMPTION: pads and trace
C_PROBE_PF = (5.0, 50.0)       # pF, ASSUMPTION: electrode capacitance dry air ... saturated soil (unverified)
R_OHM = 470e3                  # R12, 1 % (0603WAF4703T5E)
R_TOL = 0.01
GATE_S = 0.020                 # s, PCNT gate time per measurement
DELTA_ICC_MAX_A = 500e-6       # datasheet: delta ICC, one input at VCC-0.6 V (upper bound while the input ramps)

# pass/fail limits (derived, not from a requirement): see limits_note()
F_MIN_HZ = 10e3                # counted with 20 ms gate: >= 200 counts
F_MAX_HZ = 2e6                 # well inside ESP32-C3 PCNT/GPIO capability, far from the LVC1G14's MHz-range limit
MIN_COUNTS = 200
MIN_SPREAD_COUNTS = 100        # dry-to-wet count difference must stay resolvable at the worst threshold corner


def freq_hz(c_pf: float, vtp: float, vtm: float, r: float = R_OHM, vcc: float = VCC) -> float:
    c = c_pf * 1e-12
    t = r * c * (math.log((vcc - vtm) / (vcc - vtp)) + math.log(vtp / vtm))
    return 1.0 / t


def corners():
    for vtp, vtm, r in itertools.product(VT_PLUS, VT_MINUS, (R_OHM * (1 - R_TOL), R_OHM * (1 + R_TOL))):
        yield vtp, vtm, r


def sweep():
    """Return dict of worst/best frequencies over all threshold corners and the assumed probe range."""
    c_lo = C_PROBE_PF[0] + C_IN_PF + C_PARASITIC_PF
    c_hi = C_PROBE_PF[1] + C_IN_PF + C_PARASITIC_PF
    f_all = [freq_hz(c, vtp, vtm, r) for vtp, vtm, r in corners() for c in (c_lo, c_hi)]
    spread_counts = min((freq_hz(c_lo, vtp, vtm, r) - freq_hz(c_hi, vtp, vtm, r)) * GATE_S for vtp, vtm, r in corners())
    nominal = {"dry_hz": freq_hz(c_lo, 1.685, 0.99), "wet_hz": freq_hz(c_hi, 1.685, 0.99)}
    return {"f_min": min(f_all), "f_max": max(f_all), "min_counts": min(f_all) * GATE_S,
            "min_spread_counts": spread_counts, **nominal,
            "delta_icc_max_ua": DELTA_ICC_MAX_A * 1e6}


def checks():
    s = sweep()
    return {
        "f_min >= 10 kHz": s["f_min"] >= F_MIN_HZ,
        "f_max <= 2 MHz": s["f_max"] <= F_MAX_HZ,
        "counts in gate >= 200": s["min_counts"] >= MIN_COUNTS,
        "dry-wet spread >= 100 counts at worst corner": s["min_spread_counts"] >= MIN_SPREAD_COUNTS,
    }


def main():
    s = sweep()
    print(f"R12 = {R_OHM / 1e3:.0f} k, probe {C_PROBE_PF[0]}..{C_PROBE_PF[1]} pF (ASSUMPTION), total C incl. input+parasitic")
    for k, v in s.items():
        print(f"  {k}: {v:.4g}")
    for k, ok in checks().items():
        print(("PASS " if ok else "FAIL ") + k)


if __name__ == "__main__":
    main()

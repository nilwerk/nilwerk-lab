#!/usr/bin/env python3
"""LDO dropout / rail sag at low battery under a Wi-Fi TX burst (role file: 'LDO dropout at low battery'; M8 in power-budget.md).

    python3 -I ldo_dropout.py            # needs `ngspice` on PATH (apt install ngspice) and optionally matplotlib for the PNG

Circuit (ngspice, transient): cell OCV + series resistance R_BAT (cell + PCM + DW01A/8205A + connector + trace, ALL ASSUMED)
-> 4 x 10 uF at the LDO input -> XC6220B331 as a static dropout model (Vout = min(3.3 V, Vin - R_DO x I), a behavioural source)
-> 22 uF (ESR 5 mOhm) -> load = ESP32-C3 TX burst 335 mA (datasheet v2.4 Table 5-7 peak, 100 % duty, from power-budget.md)
on top of 25 mA CPU current.  Not modelled: LDO loop dynamics (the static model is conservative for the burst: the real loop
sags more in the first microseconds, the 22 uF + 40 uF bulk carry that), cell OCV change during the burst, temperature.

R_DO readings (XC6220 datasheet C86534 read 2026-11-08, Voltage Chart 1: Vdif1 at 300 mA typ 60 / max 95 mV; the chart prints the values once
for the 3.5 V row group, so for the 3.3 V part they are a reading, not a certainty; the integrated driver is 0.2 Ohm on-resistance):
  A) 60 mV at 300 mA (datasheet typ)                                         -> 0.20 Ohm
  C) 95 mV at 300 mA (datasheet max)                                         -> 0.317 Ohm
  B) 655 mV at 1 A (LCSC listing text in bom-draft.md, linear scaling)       -> 0.655 Ohm  (pessimistic bound)
Limit: V(3V3) >= V_MIN_MODULE during the burst.  3.0 V = VDD33 minimum, ESP32-C3-MINI-1 datasheet v2.2 Table 6-2 (read 2026-11-08).
Exit code 1 if any case marked REQUIRED fails.
"""
import itertools, os, subprocess, sys, tempfile

V_MIN_MODULE = 3.0        # V, datasheet v2.2 Table 6-2 VDD33 min
V_OUT = 3.3
I_TX, I_BASE = 0.335, 0.025   # A (TX peak 335 mA worst, CPU 25 mA on top: A-model sum = 0.36 A)
OCV = [3.4, 3.3, 3.0]         # cell open-circuit-ish voltage: 3.4 = low-battery warning (A-008.2); 3.0 = PCM over-discharge region (3.0 +- 0.1)
R_BAT = {"0.15 (README assumption)": 0.15, "0.30 (aged / cold, assumed)": 0.30}
R_DO = {"A 60mV@300mA": 0.20, "C 95mV@300mA": 0.95 / 3.0, "B 655mV@1A": 0.655}
REQUIRED = {(3.4, "0.15 (README assumption)", "A 60mV@300mA"), (3.4, "0.15 (README assumption)", "B 655mV@1A"), (3.4, "0.15 (README assumption)", "C 95mV@300mA"), (3.4, "0.30 (aged / cold, assumed)", "C 95mV@300mA"),
            (3.4, "0.30 (aged / cold, assumed)", "A 60mV@300mA")}   # the 3.4 V warning point must hold in the nominal case for all readings and the aged case for the datasheet readings A and C


def netlist(ocv, rbat, rdo, outfile):
    # Viw carries the load-current waveform as a voltage (1 V = 1 A); Iload sinks it from the rail; the LDO model reads the same number.
    return f"""* LDO dropout at low battery
Vcell cell 0 {ocv}
Rbat cell vin {rbat}
Cin vin 0 40u
Viw iw 0 PULSE({I_BASE} {I_BASE + I_TX} 100u 10u 10u 3m 10m)
Bldo ldoint 0 V=min({V_OUT}, V(vin)-{rdo}*V(iw))
Rldo ldoint v33 0.01
Cout v33 esr 22u
Resr esr 0 0.005
Bload v33 0 I=V(iw)
Bin vin 0 I=V(iw)
.tran 2u 5m
.control
run
wrdata {outfile} v(v33) v(vin)
.endc
.end
"""


def run(ocv, rbat, rdo):
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "o.txt")
        p = os.path.join(d, "n.cir")
        open(p, "w").write(netlist(ocv, rbat, rdo, out))
        r = subprocess.run(["ngspice", "-b", p], capture_output=True, text=True)
        if not os.path.exists(out):
            sys.exit("ngspice produced no output:\n" + r.stdout[-800:] + r.stderr[-800:])
        rows = [list(map(float, l.split())) for l in open(out) if l.strip()]
    return [x[0] for x in rows], [x[1] for x in rows], [x[3] for x in rows]


def main():
    out, fails, curves = [], 0, {}
    print(f"{'OCV':>5} {'R_bat':<28} {'LDO reading':<14} {'Vin min':>8} {'V3V3 min':>9} {'margin':>8}  result")
    for ocv, (rn, rb), (dn, rd) in itertools.product(OCV, R_BAT.items(), R_DO.items()):
        t, v33, vin = run(ocv, rb, rd)
        vmin, imin = min(v33), min(vin)
        ok = vmin >= V_MIN_MODULE
        req = (ocv, rn, dn) in REQUIRED
        # analytic cross-check at the burst plateau: Vin = OCV - R*I, Vout = min(3.3, Vin - Rdo*I)
        i = I_BASE + I_TX
        an = min(V_OUT, ocv - rb * i - rd * i)
        assert abs(vmin - an) < 0.01, (vmin, an)
        print(f"{ocv:5.1f} {rn:<28} {dn:<14} {imin:8.3f} {vmin:9.3f} {vmin - V_MIN_MODULE:+8.3f}  {'PASS' if ok else 'FAIL'}{' (REQUIRED)' if req else ''}")
        if req and not ok:
            fails += 1
        curves[(ocv, rn, dn)] = (t, v33)
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(8, 4.5))
        for (ocv, rn, dn), (t, v) in curves.items():
            if rn.startswith("0.30") or ocv == 3.3:
                continue
            ax.plot([x * 1e3 for x in t], v, label=f"OCV {ocv} V, R_bat {rn.split()[0]}, LDO {dn[0]}")
        ax.axhline(V_MIN_MODULE, color="r", ls="--", label=f"limit {V_MIN_MODULE} V (VDD33 min, datasheet)")
        ax.set_xlabel("ms"); ax.set_ylabel("V(3V3)"); ax.set_title("Rail during a 360 mA Wi-Fi TX burst (static LDO model)"); ax.legend(fontsize=7); ax.grid(alpha=.3)
        fig.tight_layout(); fig.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ldo_dropout.png"), dpi=120)
    except ImportError:
        print("matplotlib not available: no PNG")
    print("REQUIRED cases failed:", fails)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

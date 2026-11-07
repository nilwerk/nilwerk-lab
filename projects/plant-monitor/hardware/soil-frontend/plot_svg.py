#!/usr/bin/env python3
"""Write an SVG of oscillator frequency vs probe capacitance (best/worst threshold corners).  No dependencies.

    python3 plot_svg.py OUT.svg
"""
import sys
import soil_frontend as sf

W, H, L, R, T, B = 640, 380, 70, 20, 40, 60
cs = [5 + i * 0.5 for i in range(91)]                      # probe pF 5..50 (ASSUMED range)
ctot = lambda c: c + sf.C_IN_PF + sf.C_PARASITIC_PF
fs = lambda c: [sf.freq_hz(ctot(c), vtp, vtm, r) for vtp, vtm, r in sf.corners()]
lo = [min(fs(c)) for c in cs]
hi = [max(fs(c)) for c in cs]
nom = [sf.freq_hz(ctot(c), 1.685, 0.99) for c in cs]
fmax = 4e5
x = lambda c: L + (c - 5) / 45 * (W - L - R)
y = lambda f: T + (1 - f / fmax) * (H - T - B)
poly = lambda a: " ".join(f"{x(c):.1f},{y(f):.1f}" for c, f in zip(cs, a))
band = poly(hi) + " " + " ".join(f"{x(c):.1f},{y(f):.1f}" for c, f in zip(reversed(cs), reversed(lo)))
out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="sans-serif" font-size="12">',
       f'<rect width="{W}" height="{H}" fill="#fff"/>',
       f'<text x="{L}" y="22" font-size="14" font-weight="bold">Soil oscillator (SN74LVC1G14, R12 = 470 k): frequency vs probe capacitance</text>',
       f'<polygon points="{band}" fill="#cfe3f5" stroke="none"/>',
       f'<polyline points="{poly(nom)}" fill="none" stroke="#1f6fb2" stroke-width="2"/>',
       f'<line x1="{L}" y1="{y(sf.F_MIN_HZ):.1f}" x2="{W - R}" y2="{y(sf.F_MIN_HZ):.1f}" stroke="#c0392b" stroke-dasharray="5 4"/>',
       f'<text x="{L + 6}" y="{y(sf.F_MIN_HZ) - 5:.1f}" fill="#c0392b">limit 10 kHz (200 counts in 20 ms gate)</text>']
for f in range(0, 400001, 100000):
    out.append(f'<line x1="{L}" y1="{y(f):.1f}" x2="{W - R}" y2="{y(f):.1f}" stroke="#ddd"/>'
               f'<text x="{L - 8}" y="{y(f) + 4:.1f}" text-anchor="end">{f // 1000} kHz</text>')
for c in range(5, 51, 5):
    out.append(f'<text x="{x(c):.1f}" y="{H - B + 18}" text-anchor="middle">{c}</text>')
out += [f'<text x="{(L + W - R) / 2}" y="{H - 22}" text-anchor="middle">probe capacitance, pF (ASSUMED range, not measured)</text>',
        f'<text x="{L}" y="{H - 6}" fill="#555">band = all datasheet threshold corners (SCES218AA, 3 V row) and R +-1 %; line = typical thresholds</text>',
        '</svg>']
open(sys.argv[1], "w").write("\n".join(out))
print("wrote", sys.argv[1])

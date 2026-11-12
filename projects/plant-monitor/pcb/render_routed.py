#!/usr/bin/env python3
"""Render the routed copper of plant-monitor.kicad_pcb (4.P2 slice 3).  Run: python3 -I render_routed.py out.png
F.Cu tracks red, B.Cu blue, vias grey, pads gold, the power-section connections still open marked with a cross.
Pure drawing from the board file (not a KiCad screenshot).  Uses check_layout.py's parser."""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import check_layout as C
from PIL import Image, ImageDraw

OPEN = [("J1", "A9"), ("R1", "1"), ("Q1", "5")]   # the 3 power-section connections that the router could not complete (layout-4P2.md)


def main(out):
    B = C.load()
    text = open(C.PCB).read()
    segs = [(float(a), float(b), float(c), float(d), float(w), l) for a, b, c, d, w, l in
            re.findall(r'\(segment \(start ([-\d.]+) ([-\d.]+)\) \(end ([-\d.]+) ([-\d.]+)\) \(width ([-\d.]+)\) \(layer "([FB]\.Cu)"\)', text)]
    xs = [p[0] for e in B["edges"] for p in e]; ys = [p[1] for e in B["edges"] for p in e]
    scale = 22
    x0, y0, x1, y1 = min(xs) - 1.5, min(ys) - 1.5, max(xs) + 1.5, max(ys) + 1.5
    im = Image.new("RGB", (int((x1 - x0) * scale), int((y1 - y0) * scale)), (250, 250, 247))
    d = ImageDraw.Draw(im, "RGBA")
    T = lambda x, y: ((x - x0) * scale, (y - y0) * scale)
    # board fill and outline
    pts = [T(*e[0]) for e in B["edges"]]
    d.polygon(pts, fill=(24, 92, 56, 255))
    for e in B["edges"]:
        d.line([T(*e[0]), T(*e[1])], fill=(230, 230, 120, 255), width=2)
    # tracks: back layer first, front on top
    for lay, col in (("B", (60, 110, 230, 215)), ("F", (200, 40, 40, 235))):
        for x1_, y1_, x2_, y2_, w, l in segs:
            if l[0] != lay:
                continue
            d.line([T(x1_, y1_), T(x2_, y2_)], fill=col, width=max(2, int(w * scale)))
    # pads
    for f in B["fps"]:
        for p in f["pads"]:
            if p["w"] <= 0:
                continue
            cx, cy = T(p["x"], p["y"])
            d.rectangle([cx - p["w"] * scale / 2, cy - p["h"] * scale / 2, cx + p["w"] * scale / 2, cy + p["h"] * scale / 2],
                        fill=(214, 178, 84, 255))
    # vias
    for v in B["vias"]:
        cx, cy = T(v["x"], v["y"])
        r = 0.35 * scale
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(170, 170, 170, 255), outline=(60, 60, 60, 255))
        r2 = 0.15 * scale
        d.ellipse([cx - r2, cy - r2, cx + r2, cy + r2], fill=(24, 92, 56, 255))
    # open connections
    for ref, num in OPEN:
        for f in B["fps"]:
            if f["ref"] != ref:
                continue
            for p in f["pads"]:
                if p["num"] == num:
                    cx, cy = T(p["x"], p["y"]); r = 0.5 * scale
                    d.line([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 0, 255), width=3)
                    d.line([cx - r, cy + r, cx + r, cy - r], fill=(255, 255, 0, 255), width=3)
    # legend
    d.rectangle([8, 8, 620, 96], fill=(255, 255, 255, 200))
    lines = ["plant-monitor.kicad_pcb, 4.P2 slice 3: power section routed (grid router, route_power.py)",
             "red = F.Cu track, blue = B.Cu track, grey ring = via, gold = pad, yellow X = open power-section connection (3)",
             "NOT routed: signal nets, 3V3 distribution to module/sensors, GND (bottom zone not filled). Not fab-ready."]
    for k, t in enumerate(lines):
        d.text((14, 14 + k * 26), t, fill=(20, 20, 20, 255))
    im.save(out)
    print("wrote", out, im.size, "tracks", len(segs))


if __name__ == "__main__":
    main(sys.argv[1])

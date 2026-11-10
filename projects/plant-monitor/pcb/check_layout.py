#!/usr/bin/env python3
"""Layout self-check + render for plant-monitor.kicad_pcb (Plan 4.P2 slice 1).  Run: python3 -I check_layout.py [--render out.png]

THIS IS NOT KiCad DRC.  KiCad ERC/DRC run only in CI (job `pcb`, kicad-cli 9).  This script reads the .kicad_pcb file with its own
S-expression reader (independent of gen_pcb.py) and checks the geometric rules from layout-brief.md that can be checked on a
placed, unrouted board.  Each check prints the requirement/brief ID it comes from.  Exit 1 on any FAIL."""
from __future__ import annotations
import math, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, "plant-monitor.kicad_pcb")
FAILS = []

def check(ok, msg):
    print(("PASS  " if ok else "FAIL  ") + msg)
    if not ok:
        FAILS.append(msg)

def parse(text):
    tok = re.findall(r'"(?:[^"\\]|\\.)*"|\(|\)|[^\s()"]+', text)
    pos = 0
    def rd():
        nonlocal pos
        t = tok[pos]; pos += 1
        if t == "(":
            lst = []
            while tok[pos] != ")":
                lst.append(rd())
            pos += 1
            return lst
        return t[1:-1] if t.startswith('"') else t
    return rd()

def sub(n, name):
    return [c for c in n if isinstance(c, list) and c and c[0] == name]

def num(x): return float(x)

def load(path=PCB):
    root = parse(open(path).read())
    fps, edges, vias, zones, user, segs = [], [], [], [], [], []
    for n in root[1:]:
        if not isinstance(n, list):
            continue
        if n[0] == "footprint":
            at = sub(n, "at")[0]
            x, y = num(at[1]), num(at[2]); r = num(at[3]) if len(at) > 3 else 0.0
            ref = [p for p in sub(n, "property") if p[1] == "Reference"][0][2]
            cy = sub(n, "fp_rect")[0]
            cs, ce = sub(cy, "start")[0], sub(cy, "end")[0]
            court = (num(cs[1]), num(cs[2]), num(ce[1]), num(ce[2]))
            pads = []
            for p in sub(n, "pad"):
                pat = sub(p, "at")[0]; sz = sub(p, "size")[0]
                lx, ly = num(pat[1]), num(pat[2])
                wx = x + lx * math.cos(math.radians(r)) + ly * math.sin(math.radians(r))
                wy = y - lx * math.sin(math.radians(r)) + ly * math.cos(math.radians(r))
                w, h = num(sz[1]), num(sz[2])
                pang = num(pat[3]) if len(pat) > 3 else 0.0      # absolute pad orientation (KiCad board file convention, footprint rotation included)
                if int(round(pang)) % 180 == 90:
                    w, h = h, w
                nt = sub(p, "net")
                pads.append(dict(num=p[1], ptype=p[2], x=wx, y=wy, w=w, h=h, net=nt[0][2] if nt else None, layers=sub(p, "layers")[0][1:], drill=bool(sub(p, "drill"))))
            # courtyard to world box
            cx = [(court[0], court[1]), (court[2], court[3])]
            pts = []
            for lx, ly in [(court[0], court[1]), (court[2], court[1]), (court[2], court[3]), (court[0], court[3])]:
                pts.append((x + lx * math.cos(math.radians(r)) + ly * math.sin(math.radians(r)), y - lx * math.sin(math.radians(r)) + ly * math.cos(math.radians(r))))
            box = (min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts))
            fps.append(dict(ref=ref, x=x, y=y, rot=r, pads=pads, box=box, layer=sub(n, "layer")[0][1]))
        elif n[0] == "gr_line" and sub(n, "layer")[0][1] == "Edge.Cuts":
            s, e = sub(n, "start")[0], sub(n, "end")[0]
            edges.append(((num(s[1]), num(s[2])), (num(e[1]), num(e[2]))))
        elif n[0] == "gr_rect":
            s, e = sub(n, "start")[0], sub(n, "end")[0]
            user.append((sub(n, "layer")[0][1], num(s[1]), num(s[2]), num(e[1]), num(e[2])))
        elif n[0] == "segment":
            s_, e_ = sub(n, "start")[0], sub(n, "end")[0]
            segs.append(dict(a=(num(s_[1]), num(s_[2])), b=(num(e_[1]), num(e_[2])), w=num(sub(n, "width")[0][1]), net=sub(n, "net")[0][1]))
        elif n[0] == "via":
            at = sub(n, "at")[0]
            vias.append(dict(x=num(at[1]), y=num(at[2]), size=num(sub(n, "size")[0][1]), drill=num(sub(n, "drill")[0][1]), net=sub(n, "net")[0][1]))
        elif n[0] == "zone":
            nm = sub(n, "name")[0][1]
            pts = [(num(p[1]), num(p[2])) for p in sub(sub(n, "polygon")[0], "pts")[0][1:]]
            zones.append(dict(name=nm, pts=pts, keepout=bool(sub(n, "keepout")), layers=sub(n, "layers")[0][1:] if sub(n, "layers") else sub(n, "layer")[0][1:]))
    return dict(fps=fps, edges=edges, vias=vias, zones=zones, user=user, segs=segs, root=root)

def rect_gap(a, b):
    dx = max(a[0] - b[2], b[0] - a[2], 0); dy = max(a[1] - b[3], b[1] - a[3], 0)
    return math.hypot(dx, dy)

def pad_box(p):
    return (p["x"] - p["w"] / 2, p["y"] - p["h"] / 2, p["x"] + p["w"] / 2, p["y"] + p["h"] / 2)

def inside_poly(pt, poly):
    x, y = pt; c = False
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c

def dist_pt_seg(p, a, b):
    ax, ay = a; bx, by = b; px, py = p
    t = max(0, min(1, ((px - ax) * (bx - ax) + (py - ay) * (by - ay)) / ((bx - ax) ** 2 + (by - ay) ** 2)))
    return math.hypot(px - (ax + t * (bx - ax)), py - (ay + t * (by - ay)))

def main():
    B = load()
    fps = {f["ref"]: f for f in B["fps"]}
    poly = [e[0] for e in B["edges"]]
    xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
    W, H = max(xs) - min(xs), max(ys) - min(ys)
    print(f"board outline bbox {W:.2f} x {H:.2f} mm, {len(B['fps'])} footprints, {len(B['vias'])} vias, {len(B['zones'])} zones")
    check(len(B["edges"]) >= 4 and all(B["edges"][i][1] == B["edges"][(i + 1) % len(B["edges"])][0] for i in range(len(B["edges"]))),
          "outline is one closed polygon (Edge.Cuts)  [O8]")
    from itertools import combinations
    # single side assembly
    check(all(f["layer"] == "F.Cu" for f in B["fps"]), "all footprints on the top side, bottom side free for the flat cell bay / single-side SMT  [O1, section 5 Assembly]")
    # in the board outline (U1 antenna end and the stake tail are special)
    bad = []
    for f in B["fps"]:
        if f["ref"] == "U1":
            continue
        b = tuple(v + (0.01 if i < 2 else -0.01) for i, v in enumerate(f["box"]))
        for pt in [(b[0], b[1]), (b[2], b[1]), (b[2], b[3]), (b[0], b[3])]:
            if not inside_poly((min(max(pt[0], 0.001), 34.499), pt[1]), poly) and f["ref"] != "J1":
                bad.append(f["ref"]); break
    check(not bad, f"every courtyard inside the outline (U1 antenna overhang excepted){' ' + str(bad) if bad else ''}  [O1]")
    # courtyard overlaps
    ov = [(a["ref"], b["ref"]) for a, b in combinations(B["fps"], 2) if a["box"][0] < b["box"][2] and b["box"][0] < a["box"][2] and a["box"][1] < b["box"][3] and b["box"][1] < a["box"][3]]
    check(not ov, f"no courtyard overlap {ov if ov else '(0 overlaps)'}  [section 5 pad/pad spacing]")
    # pad to pad, different nets, 0.2 mm design rule
    viol = []
    cu = lambda p: any(l in p["layers"] for l in ("F.Cu", "*.Cu"))     # paste-only pads (library footprints) carry no copper
    for a, b in combinations(B["fps"], 2):
        for pa in [q for q in a["pads"] if cu(q)]:
            for pb in [q for q in b["pads"] if cu(q)]:
                if pa["net"] != pb["net"] or pa["net"] is None:
                    if rect_gap(pad_box(pa), pad_box(pb)) < 0.2 - 1e-9:
                        viol.append((a["ref"], pa["num"], b["ref"], pb["num"]))
    for a in B["fps"]:
        for pa, pb in combinations([q for q in a["pads"] if cu(q)], 2):
            if (pa["net"] != pb["net"] or pa["net"] is None) and rect_gap(pad_box(pa), pad_box(pb)) < 0.2 - 1e-9 and (pa["w"] * pa["h"] > 0):
                viol.append((a["ref"], pa["num"], a["ref"], pb["num"]))
    check(not viol, f"pad-to-pad clearance >= 0.2 mm between different nets, {len(viol)} violations {viol[:6]}  [section 5 clearance rule]")
    # copper to edge >= 0.5 (J1 mouth pads are inside; U1 antenna overhang is off-board; tail electrodes)
    segs = B["edges"]
    close = []
    for f in B["fps"]:
        if f["ref"] == "U1":
            continue
        for p in f["pads"]:
            bx = pad_box(p)
            for (cx, cy) in [(bx[0], bx[1]), (bx[2], bx[1]), (bx[2], bx[3]), (bx[0], bx[3]), (p["x"], p["y"])]:
                d = min(dist_pt_seg((cx, cy), a, b) for a, b in segs)
                if d < 0.5 - 1e-9 and inside_poly((cx, cy), poly):
                    close.append((f["ref"], p["num"], round(d, 2))); break
    check(not close, f"copper (pads) >= 0.5 mm from the routed edge {close[:6]}  [section 5 Copper to routed edge]")
    # keepout
    ko = [z for z in B["zones"] if z["keepout"]][0]
    kb = (min(p[0] for p in ko["pts"]), min(p[1] for p in ko["pts"]), max(p[0] for p in ko["pts"]), max(p[1] for p in ko["pts"]))
    inko = [(f["ref"], p["num"]) for f in B["fps"] for p in f["pads"] if rect_gap(pad_box(p), kb) == 0 and f["ref"] != "U1"]
    inko += [("U1", p["num"]) for p in fps["U1"]["pads"] if rect_gap(pad_box(p), kb) == 0]
    inko += [("via", i) for i, v in enumerate(B["vias"]) if kb[0] <= v["x"] <= kb[2] and kb[1] <= v["y"] <= kb[3]]
    other_in = [f["ref"] for f in B["fps"] if f["ref"] != "U1" and rect_gap(f["box"], kb) == 0]
    check(not inko and not other_in and set(ko["layers"]) == {"F.Cu", "B.Cu"},
          f"antenna keep-out {kb[2]-kb[0]:.1f} x {kb[3]-kb[1]:.1f} mm on F.Cu and B.Cu: no pad/via/other footprint inside {inko + other_in}  [O2, playbook rule 14]")
    # antenna to cell bay (cell bay is on Dwgs.User rect 1, antenna 15 mm box on Cmts.User)
    cell = [u for u in B["user"] if u[0] == "Dwgs.User"][0][1:]
    u1 = fps["U1"]["box"]
    top_pad = min(pad_box(p)[1] for p in fps["U1"]["pads"] if cu(p))
    ant_area = (u1[0], u1[1], u1[2], top_pad)  # antenna area = module width (courtyard) from the module end to the first pad row (datasheet Fig 11-1: antenna area above the pad rows)
    ant_tip = (u1[0], u1[1], u1[2], 0.0)       # the part beyond the board edge
    d = rect_gap(ant_area, cell)
    d_edge = rect_gap(ant_tip, cell)
    print(f"INFO  antenna distances to the cell cavity: antenna area {d:.1f} mm (rule value); overhang strip only {d_edge:.1f} mm; module end corner to cavity corner {math.hypot(u1[0]-cell[2], u1[1]-cell[1]):.1f} mm")
    check(d >= 15.0, f"antenna area (module width x module end to first pad row) to cell bay rectangle = {d:.1f} mm, need >= 15  [O2, R-06]")
    soil_end = min(abs(fps["E1"]["y"] + 25 - u1[1]), 999)
    check(fps["E1"]["y"] > fps["U1"]["y"] + 20, "soil tail is at the end opposite the antenna (tail y > module y + 20)  [O5, R-06, rule 14]")
    # heat
    d = rect_gap(fps["U5"]["box"], fps["U3"]["box"])
    check(d >= 10.0, f"AHT20 U5 to TP4056 U3 courtyard distance {d:.1f} mm, need >= 10  [O6]")
    d = rect_gap(fps["D1"]["box"], fps["J1"]["box"])
    check(d <= 10.0, f"ESD D1 to USB-C J1 courtyard distance {d:.1f} mm, need <= 10  [O4]")
    d = rect_gap(fps["J1"]["box"], ant_area)
    check(d >= 15.0, f"USB-C J1 to antenna end {d:.1f} mm (far from the antenna, >= 15)  [O4]")
    # HRO TYPE-C-31-M-12 library footprint: body (F.Fab) front edge at local y = +3.65; J1 is rotated 90 so local +y points to +x
    j1 = fps["J1"]
    check(abs(j1["rot"] - 90) < 0.01 and abs(j1["x"] + 3.65 - max(xs)) < 0.01, "USB-C mouth (body front, library F.Fab 3.65 mm) flush with the right outline edge  [O4]")
    # vias
    u1v = [v for v in B["vias"] if rect_gap((v["x"], v["y"], v["x"], v["y"]), fps["U1"]["box"]) == 0]
    check(len(u1v) >= 9, f"{len(u1v)} ground vias under the module (>= 9)  [O3, Espressif]")
    u3 = fps["U3"]; ep = [p for p in u3["pads"] if p["num"] == "9"][0]; epb = pad_box(ep)
    u3v = [v for v in B["vias"] if rect_gap((v["x"], v["y"], v["x"], v["y"]), (epb[0] - 3.0, epb[1] - 3.0, epb[2] + 3.0, epb[3] + 3.0)) == 0]
    check(4 <= len(u3v) <= 6, f"{len(u3v)} thermal vias at the TP4056 exposed pad (4-6)  [section 5 Cell/charger]")
    stub_ok = all(any(abs(s["a"][0] - v["x"]) < 1e-6 and abs(s["a"][1] - v["y"]) < 1e-6 and s["net"] == v["net"] and epb[0] <= s["b"][0] <= epb[2] and epb[1] <= s["b"][1] <= epb[3] for s in B["segs"]) for v in u3v)
    check(stub_ok, "every TP4056 thermal via is joined to the exposed pad by a track stub (the via is outside the pad)  [Needs-Arsany A-069]")
    # A-069: no via hole inside any SMD pad (distance from the hole centre to the pad rectangle must exceed the hole radius)
    inpad = []
    for v in B["vias"]:
        for f in B["fps"]:
            for p in f["pads"]:
                if cu(p) and p["ptype"] == "smd" and rect_gap((v["x"], v["y"], v["x"], v["y"]), pad_box(p)) < v["drill"] / 2:
                    inpad.append((f["ref"], p["num"]))
    check(not inpad, f"{len(inpad)} via holes inside an SMD pad (0 required, A-069 option 'move vias out of pads') {inpad[:4]}  [JLC via-in-pad rule]")
    ovl = sum(1 for v in B["vias"] for f in B["fps"] for p in f["pads"] if cu(p) and p["ptype"] == "smd" and rect_gap((v["x"], v["y"], v["x"], v["y"]), pad_box(p)) < v["size"] / 2)
    print(f"INFO  {ovl} via copper/pad copper overlaps (hole outside the pad, annulus touches a same-net pad; not via-in-pad)")
    netname = {n[1]: n[2] for n in B["root"][1:] if isinstance(n, list) and n[0] == "net" and len(n) > 2}
    bad = [(i, f["ref"], p["num"]) for i, v in enumerate(B["vias"]) for f in B["fps"] for p in f["pads"] if cu(p) and p["net"] != netname.get(v["net"]) and rect_gap((v["x"], v["y"], v["x"], v["y"]), pad_box(p)) < v["size"] / 2 + 0.2 - 1e-9]
    check(not bad, f"via copper to a pad of another net >= 0.2 mm, {len(bad)} violations {bad[:4]}  [section 5 clearance rule]")
    check(all(abs(v["size"] - 0.7) < 1e-9 and abs(v["drill"] - 0.3) < 1e-9 for v in B["vias"]), "all vias 0.3 mm drill / 0.7 mm pad  [section 5 Via]")
    vv = [(i, j) for (i, a), (j, b) in combinations(enumerate(B["vias"]), 2) if math.hypot(a["x"] - b["x"], a["y"] - b["y"]) - 0.7 < 0.25 - 1e-9]
    check(not vv, f"via-to-via hole/copper spacing >= 0.25 mm, {len(vv)} violations  [section 5 Via]")
    # no part on the bottom, no THT
    tht = sorted({f["ref"] for f in B["fps"] for p in f["pads"] if p["ptype"] != "smd"})
    check(all(("F.Cu" in p["layers"]) or p["ptype"] != "smd" or "F.Cu" not in p["layers"] and "F.Paste" in p["layers"] for f in B["fps"] for p in f["pads"]) and tht == ["J1"],
          f"SMD pads on the top side only; through-hole/NPTH pads only on {tht} (USB-C shield legs and positioning pegs of the real footprint)  [section 5 Assembly]")
    print(f"\nrouting: {len(B['segs'])} track segments (TP4056 GND stubs only), GND zone not filled, nets not routed (next slice).")
    print(f"RESULT: {len(FAILS)} FAIL" if FAILS else "RESULT: all layout checks PASS")
    return B

def render(B, out, scale=14):
    from PIL import Image, ImageDraw
    xs = [p[0] for e in B["edges"] for p in e]; ys = [p[1] for e in B["edges"] for p in e]
    cell = [u for u in B["user"] if u[0] == "Dwgs.User"][0][1:]
    x0, y0 = cell[0] - 4, -6 - 17
    x1, y1 = max(max(xs), max(u[3] for u in B['user'])) + 3, max(ys) + 4
    Wp, Hp = int((x1 - x0) * scale), int((y1 - y0) * scale)
    im = Image.new("RGB", (Wp, Hp), (250, 250, 247)); d = ImageDraw.Draw(im, "RGBA")
    T = lambda x, y: ((x - x0) * scale, (y - y0) * scale)
    # user layers
    for lay, a, b, c, e in B["user"]:
        col = (60, 90, 200, 255) if lay == "Dwgs.User" else (235, 140, 20, 255)
        d.rectangle([*T(a, b), *T(c, e)], outline=col, width=2, fill=(60, 90, 200, 25) if lay == "Dwgs.User" else (235, 140, 20, 22))
    d.text(T(cell[0] + 12, (cell[1] + cell[3]) / 2), "LiPo cell bay 53.0 x 35.1 mm (cavity, not copper)", fill=(40, 60, 160, 255))
    # board fill
    pts = [T(*e[0]) for e in B["edges"]]
    d.polygon(pts, fill=(24, 92, 56, 255))
    # keepout
    for z in B["zones"]:
        if z["keepout"]:
            d.polygon([T(*p) for p in z["pts"]], fill=(230, 40, 40, 150))
    for f in B["fps"]:
        b = f["box"]
        d.rectangle([*T(b[0], b[1]), *T(b[2], b[3])], outline=(255, 255, 255, 120), width=1)
        if f["ref"] == "U1":
            d.rectangle([*T(b[0], b[1]), *T(b[2], b[3])], fill=(30, 30, 30, 120), outline=(255, 255, 255, 200), width=2)
        for p in f["pads"]:
            pb = pad_box(p)
            e1 = f["ref"] == "E1"
            d.rectangle([*T(pb[0], pb[1]), *T(pb[2], pb[3])], fill=(150, 120, 60, 255) if e1 else (225, 190, 90, 255))
        d.text(T(b[0], b[1] - 0.9), f["ref"], fill=(255, 255, 255, 255))
    for v in B["vias"]:
        cx, cy = T(v["x"], v["y"]); r = v["size"] / 2 * scale
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(200, 200, 200, 255), outline=(40, 40, 40, 255))
    # outline stroke
    d.line(pts + [pts[0]], fill=(240, 230, 120, 255), width=2)
    d.text((8, 8), "plant-monitor.kicad_pcb (slice 1: placed, NOT routed; drawn from the board file, not a KiCad screenshot)", fill=(0, 0, 0, 255))
    lg = [((230, 40, 40, 255), "solid dark-red strip = the antenna KEEP-OUT rule area (17.2 x 2.0 mm, Emil's assumption, datasheet not read)"),
          ((235, 140, 20, 255), "large orange rectangle = 15 mm antenna clear box (comment layer, distance rule to the cell, not a keep-out)"),
          ((60, 90, 200, 255), "blue rectangle = LiPo cell cavity (not copper)")]
    for i, (c, t) in enumerate(lg):
        d.rectangle([8, 26 + i * 16, 20, 36 + i * 16], fill=c); d.text((26, 26 + i * 16), t, fill=(0, 0, 0, 255))
    im.save(out)
    print("wrote", out, im.size)

if __name__ == "__main__":
    B = main()
    if "--render" in sys.argv:
        render(B, sys.argv[sys.argv.index("--render") + 1])
    sys.exit(1 if FAILS else 0)

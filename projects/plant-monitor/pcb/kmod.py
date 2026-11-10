"""Minimal reader for KiCad .kicad_mod footprint files (pads + courtyard), used by gen_pcb.py.  Emil (PCB Designer), 4.P2 slice 2."""
from __future__ import annotations
import os, re

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, "footprints")


def _parse(text):
    tok = re.findall(r'"(?:[^"\\]|\\.)*"|\(|\)|[^\s()"]+', text)
    pos = 0

    def rd():
        nonlocal pos
        t = tok[pos]
        pos += 1
        if t == "(":
            lst = []
            while tok[pos] != ")":
                lst.append(rd())
            pos += 1
            return lst
        return t[1:-1] if t.startswith('"') else t
    return rd()


def _sub(n, name):
    return [c for c in n if isinstance(c, list) and c and c[0] == name]


def load(name):
    """name = file stem in footprints/.  Returns dict(pads=[...], court=(x0,y0,x1,y1)).  Pad: num,type,shape,x,y,ang,w,h,drill,layers,rratio."""
    root = _parse(open(os.path.join(LIB, name + ".kicad_mod")).read())
    pads, cy = [], []
    for n in root[1:]:
        if not isinstance(n, list):
            continue
        if n[0] == "pad":
            at = _sub(n, "at")[0]
            sz = _sub(n, "size")[0]
            dr = _sub(n, "drill")
            drill = None
            if dr:
                d = [x for x in dr[0][1:] if x != "oval"]
                drill = (float(d[0]), float(d[1]) if len(d) > 1 else float(d[0]))
            rr = _sub(n, "roundrect_rratio")
            pads.append(dict(num=n[1], type=n[2], shape=n[3], x=float(at[1]), y=float(at[2]), ang=float(at[3]) if len(at) > 3 else 0.0,
                             w=float(sz[1]), h=float(sz[2]), drill=drill, layers=list(_sub(n, "layers")[0][1:]),
                             rratio=float(rr[0][1]) if rr else None))
        elif n[0] in ("fp_line", "fp_rect", "fp_poly") and _sub(n, "layer") and _sub(n, "layer")[0][1] == "F.CrtYd":
            if n[0] == "fp_poly":
                cy += [(float(p[1]), float(p[2])) for p in _sub(_sub(n, "pts")[0], "xy")]
            else:
                s, e = _sub(n, "start")[0], _sub(n, "end")[0]
                cy += [(float(s[1]), float(s[2])), (float(e[1]), float(e[2]))]
    court = (min(p[0] for p in cy), min(p[1] for p in cy), max(p[0] for p in cy), max(p[1] for p in cy))
    return dict(pads=pads, court=court)

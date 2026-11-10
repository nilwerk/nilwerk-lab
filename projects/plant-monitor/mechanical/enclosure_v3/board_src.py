"""Reads the 4.P2 board (jlc_prep/input, copied from agent/pcb/4.P2 @ da39d2c) into component boxes in the DXF frame."""
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "jlc_prep"))
import board_step as bs
import params_v3 as P

def components():
    root = bs.parse_sexpr(open(bs.IN_PCB, encoding="utf-8").read())
    out = {}
    for fp in bs.kids(root, "footprint"):
        at = bs.kid(fp, "at"); fx, fy = float(at[1]), float(at[2]); fr = float(at[3]) if len(at) > 3 else 0.0
        ref = [p[2] for p in bs.kids(fp, "property") if p[1] == "Reference"][0]
        r = bs.kid(fp, "fp_rect")   # courtyard
        pts = []
        if r is not None:
            (x0, y0), (x1, y1) = bs.xy(bs.kid(r, "start")), bs.xy(bs.kid(r, "end"))
            pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        for pd in bs.kids(fp, "pad"):
            pat = bs.kid(pd, "at"); sz = bs.kid(pd, "size")
            hx, hy = float(sz[1]) / 2, float(sz[2]) / 2
            if int(round(fr)) % 180 == 90:
                hx, hy = hy, hx   # footprint rotated by 90/270: swap the pad half-extents (applied in the rotated frame below)
            px, py = float(pat[1]), float(pat[2])
            pts += [(px - hx, py - hy), (px + hx, py + hy)] if hx == float(sz[1]) / 2 else [("pad", px, py, hx, hy)]
        world = []
        for p_ in pts:
            if p_[0] == "pad":
                rx, ry = bs.rot(p_[1], p_[2], fr); cx_, cy_ = fx + rx, -(fy + ry)
                world += [(cx_ - p_[3], cy_ - p_[4]), (cx_ + p_[3], cy_ + p_[4])]; continue
            lx, ly = p_
            rx, ry = bs.rot(lx, ly, fr); world.append((fx + rx, -(fy + ry)))   # KiCad y down -> DXF y up
        xs = [w[0] for w in world]; ys = [w[1] for w in world]
        out[ref] = dict(ref=ref, box=(min(xs), min(ys), max(xs), max(ys)), h=P.H_BY_REF.get(ref, P.H_DEFAULT))
    return out

def gap(a, b):
    dx = max(b[0] - a[2], a[0] - b[2], 0.0); dy = max(b[1] - a[3], a[1] - b[3], 0.0)
    return math.hypot(dx, dy)

def placeholder_refs():
    """Footprints that gen_pcb.py tags 'placeholder' or 'electrode' (read from the file text, not remembered)."""
    import re
    src = os.path.join(os.path.dirname(bs.IN_PCB), "..", "..", "..", "..", "..")
    txt = open(bs.IN_PCB, encoding="utf-8").read()
    res = []
    for m in re.finditer(r'\(footprint "[^"]+"\s*\(layer "F.Cu"\)\s*\(uuid "[^"]+"\)\s*\(at [^)]*\)\s*\(descr "(PLACEHOLDER|ELECTRODE):[^"]*"\)\s*\(property "Reference" "([^"]+)"', txt):
        res.append((m.group(2), m.group(1)))
    return res

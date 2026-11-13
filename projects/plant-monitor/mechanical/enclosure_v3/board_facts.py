"""Facts read from the 4.P2 board copy in input/ (no hard-coded board numbers elsewhere). No CAD needed.
Source of the copy: branch agent/pcb/4.P2-s2 (PR #73) @ b2e211f, see input/SOURCE.txt."""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
IN_PCB = os.path.join(HERE, "input", "plant-monitor.kicad_pcb")
IN_DXF = os.path.join(HERE, "input", "plant-monitor-outline.dxf")
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "jlc_prep"))
import board_step as bs


def dxf_layers(path=IN_DXF):
    t = [l.strip() for l in open(path, encoding="utf-8").read().splitlines()]
    out, i = {}, 0
    while i < len(t) - 1:
        if t[i] == "0" and t[i + 1] == "LINE":
            r, j = {}, i + 2
            while j < len(t) - 1 and t[j] != "0":
                r[t[j]] = t[j + 1]; j += 2
            out.setdefault(r.get("8"), []).extend([(float(r["10"]), float(r["20"])), (float(r["11"]), float(r["21"]))])
            i = j
        else:
            i += 1
    return out


def bbox(pts):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def electrode_span():
    """Soil electrode copper (E1, pad 1 = SOIL_PROBE, 20 mm long) read from the board: returns (copper_end_y, rotation) in DXF y (negative)."""
    root = bs.parse_sexpr(open(IN_PCB, encoding="utf-8").read())
    for fp in bs.kids(root, "footprint"):
        ref = [p[2] for p in bs.kids(fp, "property") if p[1] == "Reference"][0]
        if ref != "E1":
            continue
        at = bs.kid(fp, "at"); fy = float(at[2]); rot = float(at[3]) if len(at) > 3 else 0.0
        assert rot == 0.0, "E1 rotation not handled"
        for pd in bs.kids(fp, "pad"):
            if pd[1] == "1":
                pat = bs.kid(pd, "at"); sz = bs.kid(pd, "size")
                cu_bot_kicad = fy + float(pat[2]) + float(sz[2]) / 2
                return -cu_bot_kicad
    raise ValueError("E1 pad 1 not found")


def facts():
    L = dxf_layers()
    ob = bbox(L["OUTLINE"]); cav = bbox(L["CELL_BAY_CAVITY"]); mod = bbox(L["MODULE_U1"])
    xs_tail = sorted({p[0] for p in L["OUTLINE"] if p[1] == ob[1]})
    ys = sorted({p[1] for p in L["OUTLINE"]})
    root = bs.parse_sexpr(open(IN_PCB, encoding="utf-8").read())
    at = {}
    for fp in bs.kids(root, "footprint"):
        ref = [p[2] for p in bs.kids(fp, "property") if p[1] == "Reference"][0]
        a = bs.kid(fp, "at"); at[ref] = (float(a[1]), -float(a[2]), float(a[3]) if len(a) > 3 else 0.0)  # DXF frame
    g = bs.kid(root, "general")
    return dict(
        board_w=ob[2] - ob[0], board_len=ob[3] - ob[1], body_l=-ys[-2], tail_w=xs_tail[-1] - xs_tail[0], tail_x0=xs_tail[0],
        tail_l=ys[-2] - ob[1] if False else -ob[1] - (-ys[-2]), overhang=mod[3] - 0.0,
        module_x0=mod[0], module_x1=mod[2], module_ymin=mod[1],
        cell=(cav[0], cav[1], cav[2], cav[3]), thickness=float(bs.kid(g, "thickness")[1]), at=at, max_x=max(b[2] for b in boxes().values() if b[2] < 40.0),
        copper_end=electrode_span(), tail_end=ob[1])


def placeholder_refs():
    txt = open(IN_PCB, encoding="utf-8").read()
    return [(m.group(2), m.group(1)) for m in re.finditer(
        r'\(footprint "[^"]+"\s*\(layer "F.Cu"\)\s*\(uuid "[^"]+"\)\s*\(at [^)]*\)\s*\(descr "(PLACEHOLDER|ELECTRODE):[^"]*"\)\s*\(property "Reference" "([^"]+)"', txt)]


def boxes():
    root = bs.parse_sexpr(open(IN_PCB, encoding="utf-8").read())
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
        out[ref] = (min(xs), min(ys), max(xs), max(ys))
    return out


if __name__ == "__main__":
    f = facts(); print({k: v for k, v in f.items() if k != "at"}); print(placeholder_refs())

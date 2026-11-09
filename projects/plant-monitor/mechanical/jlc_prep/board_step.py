"""4.E3 JLC prep: STEP of the 4.P2 board outline + placed footprints (dry run, no order, no upload).

Source (not merged to main when this was written): branch agent/pcb/4.P2, commit da39d2c, copied unchanged to
`input/plant-monitor.kicad_pcb` and `input/plant-monitor-outline.dxf` (see README.md, provenance).

What the STEP contains (all mm, STEP Y = DXF Y = -KiCad Y, so the top view matches the KiCad screen view):
  - BOARD: outline from Edge.Cuts, 1.6 mm FR-4 (Z 0..1.6), 16 via holes (0.3 mm drill) cut through.
  - FP_<ref>: each placed footprint as its copper pads only (top copper, nominal 35 um). The source has
    NO component bodies and NO 3D models, so no component height is shown.
  - VIA_RINGS: annular rings (0.7 mm pad, 0.3 mm drill) on top and bottom of each via.
  - No routing (the board has no tracks), no zones filled, no silkscreen, no mask.

Run:  python board_step.py            (writes out/plant-monitor-board.step)
Needs: cadquery (OCC). Pure parsing (parse_board) works without it.
"""
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
IN_PCB = os.path.join(HERE, "input", "plant-monitor.kicad_pcb")
IN_DXF = os.path.join(HERE, "input", "plant-monitor-outline.dxf")
OUT_STEP = os.path.join(HERE, "out", "plant-monitor-board.step")

BOARD_T = 1.6            # general (thickness 1.6) in input/plant-monitor.kicad_pcb; layout-4P2.md section "Files" / layout-brief s.5 (2 layers, FR-4 1.6 mm)
COPPER_T = 0.035         # NOT in the repo: nominal 1 oz copper (layout-brief s.5 says "1 oz outer"), 35 um is the usual nominal value. Flagged in README.


# ---------------- minimal s-expression reader (KiCad files) ----------------
def parse_sexpr(text):
    tokens = re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+', text)
    stack = [[]]
    for t in tokens:
        if t == "(":
            stack.append([])
        elif t == ")":
            done = stack.pop()
            stack[-1].append(done)
        elif t.startswith('"'):
            stack[-1].append(t[1:-1])
        else:
            stack[-1].append(t)
    if len(stack) != 1 or len(stack[0]) != 1:
        raise ValueError("unbalanced s-expression")
    return stack[0][0]


def kids(node, name):
    return [c for c in node if isinstance(c, list) and c and c[0] == name]


def kid(node, name):
    k = kids(node, name)
    return k[0] if k else None


def xy(node):
    return float(node[1]), float(node[2])


def rot(lx, ly, deg):
    # KiCad footprint rotation (same convention as pcb/gen_pcb.py rot()): counter-clockwise on screen, y down
    a = math.radians(deg)
    return lx * math.cos(a) + ly * math.sin(a), -lx * math.sin(a) + ly * math.cos(a)


def parse_board(path=IN_PCB):
    root = parse_sexpr(open(path, encoding="utf-8").read())
    assert root[0] == "kicad_pcb", "not a kicad_pcb file"
    board = {"edge": [], "footprints": [], "vias": [], "thickness": None}
    g = kid(root, "general")
    board["thickness"] = float(kid(g, "thickness")[1]) if g and kid(g, "thickness") else None
    for ln in kids(root, "gr_line"):
        if kid(ln, "layer")[1] == "Edge.Cuts":
            board["edge"].append((xy(kid(ln, "start")), xy(kid(ln, "end"))))
    for v in kids(root, "via"):
        at = xy(kid(v, "at"))
        board["vias"].append(dict(x=at[0], y=at[1], dia=float(kid(v, "size")[1]), drill=float(kid(v, "drill")[1])))
    for fp in kids(root, "footprint"):
        at = kid(fp, "at")
        fx, fy = float(at[1]), float(at[2])
        fr = float(at[3]) if len(at) > 3 else 0.0
        ref = None
        for p in kids(fp, "property"):
            if p[1] == "Reference":
                ref = p[2]
        pads = []
        for pd in kids(fp, "pad"):
            pat = kid(pd, "at")
            px, py = float(pat[1]), float(pat[2])
            pr = float(pat[3]) if len(pat) > 3 else 0.0
            sz = kid(pd, "size")
            pads.append(dict(num=pd[1], shape=pd[3], px=px, py=py, pr=pr, w=float(sz[1]), h=float(sz[2]),
                             layers=kid(pd, "layers")[1:]))
        board["footprints"].append(dict(ref=ref, lib=fp[1], x=fx, y=fy, r=fr, pads=pads))
    return board


def outline_loop(edge):
    """Chain Edge.Cuts segments into one closed polygon (KiCad coordinates)."""
    segs = list(edge)
    pts = [segs[0][0]]
    cur = segs[0][1]
    used = {0}
    while len(used) < len(segs):
        nxt = None
        for i, (a, b) in enumerate(segs):
            if i in used:
                continue
            if a == cur:
                nxt, cur2 = i, b
                break
            if b == cur:
                nxt, cur2 = i, a
                break
        if nxt is None:
            raise ValueError("Edge.Cuts is not one closed chain")
        used.add(nxt)
        pts.append(cur)
        cur = cur2
    if cur != pts[0]:
        raise ValueError("Edge.Cuts does not close")
    return pts


def parse_dxf_outline(path=IN_DXF):
    """DXF OUTLINE layer LINE entities as a list of (x, y) in DXF coordinates (y up)."""
    lines = [l.strip() for l in open(path, encoding="utf-8").read().splitlines()]
    segs = []
    i = 0
    while i < len(lines) - 1:
        if lines[i] == "0" and lines[i + 1] == "LINE":
            rec = {}
            j = i + 2
            while j < len(lines) - 1 and not (lines[j] == "0"):
                rec[lines[j]] = lines[j + 1]
                j += 2
            if rec.get("8") == "OUTLINE":
                segs.append(((float(rec["10"]), float(rec["20"])), (float(rec["11"]), float(rec["21"]))))
            i = j
        else:
            i += 1
    return segs


def to_step_xy(p):
    # KiCad y is down; STEP / DXF use y up.  Same flip as pcb/gen_pcb.py write_dxf().
    return (p[0], -p[1])


def pad_polygon(cx, cy, w, h, ang):
    pts = []
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        lx, ly = sx * w / 2, sy * h / 2
        a = math.radians(ang)
        gx = lx * math.cos(a) - ly * math.sin(a) + cx
        gy = lx * math.sin(a) + ly * math.cos(a) + cy
        pts.append((gx, gy))
    return pts


def build_step(out_path=OUT_STEP):
    import cadquery as cq

    b = parse_board()
    loop = [to_step_xy(p) for p in outline_loop(b["edge"])]
    loop = loop[:-1] if loop[-1] == loop[0] else loop
    thick = b["thickness"] or BOARD_T
    assert abs(thick - BOARD_T) < 1e-9, "board thickness in source differs from BOARD_T"

    board = cq.Workplane("XY").polyline(loop).close().extrude(thick).val()
    holes = []
    rings = []
    for v in b["vias"]:
        x, y = to_step_xy((v["x"], v["y"]))
        holes.append(cq.Solid.makeCylinder(v["drill"] / 2, thick + 0.2, cq.Vector(x, y, -0.1)))
        ring_top = cq.Solid.makeCylinder(v["dia"] / 2, COPPER_T, cq.Vector(x, y, thick)).cut(
            cq.Solid.makeCylinder(v["drill"] / 2, COPPER_T, cq.Vector(x, y, thick)))
        ring_bot = cq.Solid.makeCylinder(v["dia"] / 2, COPPER_T, cq.Vector(x, y, -COPPER_T)).cut(
            cq.Solid.makeCylinder(v["drill"] / 2, COPPER_T, cq.Vector(x, y, -COPPER_T)))
        rings += [ring_top, ring_bot]
    board = board.cut(cq.Compound.makeCompound(holes))

    parts = {"BOARD": cq.Compound.makeCompound([board])}
    vr = cq.Compound.makeCompound(rings)
    parts["VIA_RINGS"] = vr
    n_pads = 0
    for fp in b["footprints"]:
        solids = []
        for pd in fp["pads"]:
            # KiCad: pad angle in the file is relative to the footprint; global angle = footprint + pad.
            # NOTE: pcb/gen_pcb.py writes the footprint angle again on every pad, so R16 (footprint 90 deg)
            # gets a global pad angle of 180 deg. Reproduced as KiCad would read the file; flagged in README.
            lx, ly = pd["px"], pd["py"]
            gx, gy = rot(lx, ly, fp["r"])
            cx, cy = fp["x"] + gx, fp["y"] + gy
            cx, cy = to_step_xy((cx, cy))
            ang = -(fp["r"] + pd["pr"])  # step y is flipped, so the angle flips too
            poly = pad_polygon(cx, cy, pd["w"], pd["h"], ang)
            solids.append(cq.Workplane("XY").polyline(poly).close().extrude(COPPER_T).translate((0, 0, thick)).val())
            n_pads += 1
        parts[f"FP_{fp['ref']}"] = cq.Compound.makeCompound(solids)

    assy = cq.Assembly(name="plant-monitor-board")
    for name, shp in parts.items():
        assy.add(shp, name=name)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    assy.export(out_path, "STEP")
    return dict(n_footprints=len(b["footprints"]), n_pads=n_pads, n_vias=len(b["vias"]), outline_pts=len(loop),
                out=out_path)


if __name__ == "__main__":
    info = build_step()
    print(info)
    sys.exit(0)

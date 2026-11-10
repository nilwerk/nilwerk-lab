#!/usr/bin/env python3
"""JLCPCB panel for plant-monitor (Plan 4.P4, Nora round 2026-11-10 / Arsany A-069 follow-up).

The board outline is NOT changed: the panel is 2 copies of the board outline (read from ../plant-monitor.kicad_pcb through
check_layout.load) with rails, tooling holes and fiducials around them. Written as a spec (panel/panel-spec.md, checked numbers),
and as a DXF for the JLC panel/3D view (panel/panel.dxf). Nothing here is a Gerber: the panel Gerber/drill set still has to be
generated from a KiCad panel (CI, KiCad 9) or by the JLC panelizer. Emil (PCB Designer).

Run: python3 -I panel.py            (writes panel/, prints the checks; exit 1 on any FAIL)
Used by make_jlcpcb_package.py for checklist rows F5 and F6.
"""
from __future__ import annotations
import math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, PCB)
import check_layout as CL  # noqa: E402  (own reader of the board file, independent of gen_pcb.py)

# --- panel rules (JLC, from the checklist F5/F6 source: https://jlcpcb.com/capabilities/pcb-capabilities, read 2026-11-09) ---
MIN_PANEL = 70.0            # min panel 70 x 70 mm (V-cut); used as the size floor here too
RAIL_MIN = 5.0              # SMT tooling edge 5 mm: rail must be >= 5 mm
BOARD_GAP = 2.0             # mouse-bite panel: 2 mm board spacing
TOOL_HOLE = 2.0             # tooling hole 2 mm (NPTH)
TOOL_EDGE = 2.0             # tooling hole centre-to-edge chosen = 2.0 mm from panel edge (edge distance of the hole >= 1 mm + radius)
FID_DIA = 1.0               # 1 mm fiducial (copper)
FID_MASK = 2.0              # mask opening 2 mm (2 x copper dia) [mine: JLC default]
FID_EDGE = 3.85             # fiducial copper edge >= 3.85 mm from panel edge
COPPER_EDGE = 0.5           # copper to routed edge (same as the board rule)
RAIL = 6.0                  # [mine] rail width: 5 mm tooling edge, plus fiducial centre at 4.35 mm from the edge and 0.5 mm copper clear of the board

def board():
    B = CL.load()
    pts = [e[0] for e in B["edges"]]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return dict(poly=pts, w=max(xs) - min(xs), h=max(ys) - min(ys), x0=min(xs), y0=min(ys))

def layout():
    b = board()
    n = 2
    W = n * b["w"] + (n - 1) * BOARD_GAP + 2 * RAIL
    H = b["h"] + 2 * RAIL
    offs = [(RAIL + i * (b["w"] + BOARD_GAP), RAIL) for i in range(n)]
    # tooling holes: left and right rail, middle height (diagonal pair would also do; the pair on one axis is simpler to check)
    tools = [(TOOL_EDGE + 1.0, H / 2), (W - TOOL_EDGE - 1.0, H / 2)]
    fids = [(FID_EDGE + FID_DIA / 2, FID_EDGE + FID_DIA / 2), (W - FID_EDGE - FID_DIA / 2, FID_EDGE + FID_DIA / 2),
            (FID_EDGE + FID_DIA / 2, H - FID_EDGE - FID_DIA / 2)]
    return dict(b=b, W=W, H=H, offs=offs, tools=tools, fids=fids)

def checks(L=None):
    L = L or layout()
    b, W, H, offs = L["b"], L["W"], L["H"], L["offs"]
    out = []
    def ck(ok, msg):
        out.append((bool(ok), msg))
    ck(W >= MIN_PANEL and H >= MIN_PANEL, f"panel {W:.1f} x {H:.1f} mm >= {MIN_PANEL:.0f} x {MIN_PANEL:.0f} mm")
    ck(RAIL >= RAIL_MIN, f"rails {RAIL:.1f} mm >= {RAIL_MIN:.0f} mm (SMT tooling edge)")
    # every board inside the panel with the rail on all sides
    inside = all(ox >= RAIL - 1e-9 and oy >= RAIL - 1e-9 and ox + b["w"] <= W - RAIL + 1e-9 and oy + b["h"] <= H - RAIL + 1e-9 for ox, oy in offs)
    ck(inside, "every board copy inside the rails, the rails are the only panel material outside the boards")
    gap = offs[1][0] - (offs[0][0] + b["w"])
    ck(abs(gap - BOARD_GAP) < 1e-9, f"board-to-board spacing {gap:.2f} mm = {BOARD_GAP:.0f} mm (mouse-bite spacing)")
    # tooling holes: 2 mm NPTH, hole edge >= 1 mm from the panel edge, not in a board
    th_ok = all(min(x, W - x, y, H - y) - TOOL_HOLE / 2 >= 1.0 for x, y in L["tools"]) and all(
        not (ox - 0.5 < x < ox + b["w"] + 0.5 and oy - 0.5 < y < oy + b["h"] + 0.5) for x, y in L["tools"] for ox, oy in offs)
    ck(th_ok, f"{len(L['tools'])} tooling holes {TOOL_HOLE:.1f} mm NPTH in the rails, edge distance >= 1 mm, 0.5 mm clear of boards")
    # fiducials: 1 mm copper, centre 4.35 mm from panel edge, copper clear of board >= 0.5 mm
    fe = [min(x, W - x, y, H - y) - FID_DIA / 2 for x, y in L["fids"]]
    ck(all(abs(e - FID_EDGE) < 1e-9 for e in fe), f"{len(L['fids'])} fiducials, copper edge {FID_EDGE} mm from the panel edge (JLC)")
    fc = []
    for x, y in L["fids"]:
        for ox, oy in offs:
            dx = max(ox - x, 0, x - (ox + b["w"])); dy = max(oy - y, 0, y - (oy + b["h"]))
            fc.append(math.hypot(dx, dy) - FID_DIA / 2)
    ck(min(fc) >= COPPER_EDGE, f"fiducial copper to board edge >= {COPPER_EDGE} mm (min {min(fc):.2f} mm)")
    return out

def write(L=None):
    L = L or layout()
    b = L["b"]
    d = os.path.join(HERE, "panel"); os.makedirs(d, exist_ok=True)
    segs = []
    def poly(pts, layer):
        for i in range(len(pts)):
            segs.append((layer, pts[i], pts[(i + 1) % len(pts)]))
    poly([(0, 0), (L["W"], 0), (L["W"], L["H"]), (0, L["H"])], "PANEL_OUTLINE")
    for ox, oy in L["offs"]:
        poly([(ox + x - b["x0"], oy + y - b["y0"]) for x, y in b["poly"]], "BOARD_OUTLINE")
    out = ["0", "SECTION", "2", "ENTITIES"]
    for layer, p, q in segs:
        out += ["0", "LINE", "8", layer, "10", f"{p[0]:.3f}", "20", f"{L['H'] - p[1]:.3f}", "30", "0", "11", f"{q[0]:.3f}", "21", f"{L['H'] - q[1]:.3f}", "31", "0"]
    for x, y in L["tools"]:
        out += ["0", "CIRCLE", "8", "TOOLING_HOLE", "10", f"{x:.3f}", "20", f"{L['H'] - y:.3f}", "30", "0", "40", f"{TOOL_HOLE / 2:.3f}"]
    for x, y in L["fids"]:
        out += ["0", "CIRCLE", "8", "FIDUCIAL_CU", "10", f"{x:.3f}", "20", f"{L['H'] - y:.3f}", "30", "0", "40", f"{FID_DIA / 2:.3f}"]
    out += ["0", "ENDSEC", "0", "EOF"]
    open(os.path.join(d, "panel.dxf"), "w").write("\n".join(out) + "\n")

if __name__ == "__main__":
    L = layout()
    res = checks(L)
    write(L)
    for ok, msg in res:
        print(("PASS  " if ok else "FAIL  ") + msg)
    print(f"panel {L['W']:.1f} x {L['H']:.1f} mm, 2 boards {L['b']['w']:.2f} x {L['b']['h']:.2f} mm each (outline unchanged), wrote panel/panel.dxf")
    print("RESULT: panel checks PASS" if all(o for o, _ in res) else "RESULT: panel checks FAIL")
    sys.exit(0 if all(o for o, _ in res) else 1)

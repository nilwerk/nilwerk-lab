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

# --- panel rules. Source: JLCPCB PCB capabilities page, https://jlcpcb.com/capabilities/pcb-capabilities (read 2026-11-12) ---
# Quoted from the page: "Mouse bites Panel" 3 (board spacing 1.6 or 2 mm), 5 (min tooling edge width 3 mm; for SMT assembly
# use 5 mm tooling edges, 2 mm tooling holes, and 1 mm fiducials centered at 3.85 mm from the panel edges), and
# "V-Cut" 4 (min. panel dimensions 70 x 70 mm: this figure is stated for V-cut panels only).
N_BOARDS = 2                # boards per panel (this panel: 2 copies of the outline)
MIN_PANEL = 70.0            # [mine] conservative size floor: the 70 x 70 mm figure is the V-cut minimum, not a mouse-bite one
RAIL_MIN = 5.0              # SMT tooling edge 5 mm (JLC SMT figure): rail must be >= 5 mm
BOARD_GAP = 2.0             # board spacing 2 mm (JLC: 1.6 or 2 mm)
TOOL_HOLE = 2.0             # tooling hole diameter 2 mm, NPTH (JLC SMT figure)
TOOL_CENTRE = 3.0           # [mine, UNVERIFIED] tooling hole centre 3.0 mm from the panel edge: the page gives the diameter, not the position
                            # (hole edge 2.0 mm from the panel edge; checks require >= 1 mm)
FID_DIA = 1.0               # 1 mm fiducial, copper (JLC SMT figure)
FID_CENTRE = 3.85           # fiducial CENTRE 3.85 mm from the panel edge (JLC SMT figure); copper edge is 3.35 mm from the edge
FID_MASK = 2.0              # [mine, UNVERIFIED] mask opening 2 mm (2 x copper dia): not on the JLC page
COPPER_EDGE = 0.5           # [mine] fiducial copper to routed board edge: same 0.5 mm as check_layout's board-edge rule (JLC minimum 0.2 mm)
RAIL = 6.0                  # [mine] rail width: >= 5 mm SMT tooling edge; holds the tooling holes and fiducials
# --- breakaway tabs and mouse bites (A-085, accepted by Arsany 2026-11-12). Source: the same JLCPCB page, section "Mouse Bites Panel (Outline)", read 2026-11-12, quoted:
#   "The minimum width of breakaway tab is 4mm."   "For breakaway with mouse-bites, the minimum width is 5mm."
#   "Recommended diameter of mouse bite is 0.5mm-0.8mm"   "Recommended distance between the two mouse-bites is 0.2-0.3mm."
#   "Copper clearance from non-mouse-bite board edges: >=0.2 mm"
TAB_W = 5.0                 # tab width: 5 mm = JLC minimum for a mouse-bite breakaway (the 4 mm figure is for tabs without mouse bites)
MB_DIA = 0.5                # mouse-bite hole diameter, 0.5 mm = low end of the JLC range 0.5-0.8 mm
MB_WEB = 0.3                # [mine] the page's "distance between the two mouse-bites 0.2-0.3 mm" read as the web between hole edges; 0.3 mm = top of range
MB_PITCH = MB_DIA + MB_WEB  # hole centre pitch 0.8 mm
MB_CLEAR = 0.2              # [mine, UNVERIFIED for mouse-bite holes] copper to hole edge >= 0.2 mm, taken from the JLC copper clearance for non-mouse-bite edges
TABS_MIN = 4                # [mine] tabs per board: 4 minimum, this panel uses 9 per board (see mouse_bites())
COURT_CLEAR = 0.25          # [mine] hole edge to footprint courtyard (keeps holes out of parts and the antenna overhang)

def board():
    B = CL.load()
    pts = [e[0] for e in B["edges"]]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return dict(poly=pts, w=max(xs) - min(xs), h=max(ys) - min(ys), x0=min(xs), y0=min(ys), fps=B["fps"])

def mouse_bites(b, offs):
    """Tabs and mouse-bite holes on every outline edge of every board copy (panel coordinates, y down).
    Every outline edge faces panel material (the boards are 2 mm apart and 6 mm from the rails), so every edge is perforated;
    the tabs are the uncut stretches that keep each board attached to the rail frame (and the 2 mm gap strip).
    Tabs: the top edge gets 2 (at 1/4 and 3/4 of its length), every other outline edge 1 at mid-length.
    Holes: centred on the outline line, pitch MB_PITCH, none within TAB_W/2 + MB_DIA/2 of a tab centre."""
    pts = [(x - b["x0"], y - b["y0"]) for x, y in b["poly"]]     # board-local, y down, origin at the outline's top-left
    n = len(pts)
    ymin = min(p[1] for p in pts)
    tabs, holes = [], []
    for bi, (ox, oy) in enumerate(offs):
        # no hole in a courtyard of a connector or the module: U1 antenna overhang, J1 USB-C mouth and J2 flush with the edge.
        # Those stretches stay uncut (they act as tabs). The stake electrodes E1 are not in this list: their copper is checked
        # against the holes in checks() (the tail frame is the stake itself).
        keep_out = []
        for fp in b["fps"]:
            if fp["ref"].startswith("E"):
                continue
            x0, y0 = panel_pts(b, ox, oy, fp["box"][0], fp["box"][1]); x1, y1 = panel_pts(b, ox, oy, fp["box"][2], fp["box"][3])
            keep_out.append((x0 - COURT_CLEAR, y0 - COURT_CLEAR, x1 + COURT_CLEAR, y1 + COURT_CLEAR))
        for ei in range(n):
            p, q = pts[ei], pts[(ei + 1) % n]
            ln = math.hypot(q[0] - p[0], q[1] - p[1])
            ux, uy = (q[0] - p[0]) / ln, (q[1] - p[1]) / ln
            top = p[1] == q[1] == ymin
            tc = [ln * f for f in ((0.25, 0.75) if top and ln >= 30 else (0.5,))]
            tabs += [(bi, ei, s) for s in tc]
            s = MB_PITCH / 2
            while s <= ln - MB_PITCH / 2 + 1e-9:
                hx, hy = ox + p[0] + ux * s, oy + p[1] + uy * s
                if all(abs(s - t) >= TAB_W / 2 + MB_DIA / 2 for t in tc) and not any(
                        a <= hx <= c and d <= hy <= e for a, d, c, e in keep_out):
                    holes.append((hx, hy))
                s += MB_PITCH
    return tabs, holes

def panel_pts(b, ox, oy, x, y):
    """Board world point (KiCad board coords) -> panel coords."""
    return (ox + x - b["x0"], oy + y - b["y0"])

def layout():
    b = board()
    n = N_BOARDS
    W = n * b["w"] + (n - 1) * BOARD_GAP + 2 * RAIL
    H = b["h"] + 2 * RAIL
    offs = [(RAIL + i * (b["w"] + BOARD_GAP), RAIL) for i in range(n)]
    # tooling holes: left and right rail, middle height (diagonal pair would also do; the pair on one axis is simpler to check)
    tools = [(TOOL_CENTRE, H / 2), (W - TOOL_CENTRE, H / 2)]
    fids = [(FID_CENTRE, FID_CENTRE), (W - FID_CENTRE, FID_CENTRE), (FID_CENTRE, H - FID_CENTRE)]
    tabs, holes = mouse_bites(b, offs)
    return dict(b=b, W=W, H=H, offs=offs, tools=tools, fids=fids, tabs=tabs, holes=holes)

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
    # fiducials: 1 mm copper, CENTRE 3.85 mm from the panel edge (JLC SMT figure), copper clear of board >= 0.5 mm
    fe = [min(x, W - x, y, H - y) for x, y in L["fids"]]
    ck(all(abs(e - FID_CENTRE) < 1e-9 for e in fe), f"{len(L['fids'])} fiducials, centre {FID_CENTRE} mm from the panel edge (JLC SMT rule), copper edge {FID_CENTRE - FID_DIA / 2:.2f} mm")
    fc = []
    for x, y in L["fids"]:
        for ox, oy in offs:
            dx = max(ox - x, 0, x - (ox + b["w"])); dy = max(oy - y, 0, y - (oy + b["h"]))
            fc.append(math.hypot(dx, dy) - FID_DIA / 2)
    ck(min(fc) >= COPPER_EDGE, f"fiducial copper to board edge >= {COPPER_EDGE} mm (min {min(fc):.2f} mm)")
    # tabs and mouse bites (A-085)
    ck(TAB_W >= 5.0, f"breakaway tab width {TAB_W:.1f} mm >= 5 mm (JLC minimum for mouse-bite breakaways)")
    per_board = [sum(1 for t in L["tabs"] if t[0] == bi) for bi in range(len(offs))]
    ck(min(per_board) >= TABS_MIN, f"tabs per board {min(per_board)}..{max(per_board)} >= {TABS_MIN} (every outline edge has a tab or a perforation)")
    ck(0.5 <= MB_DIA <= 0.8 and 0.2 <= MB_WEB <= 0.3, f"mouse-bite holes {MB_DIA:.1f} mm dia, web {MB_WEB:.1f} mm (pitch {MB_PITCH:.1f} mm) within JLC 0.5-0.8 mm / 0.2-0.3 mm")
    # holes stay out of footprint courtyards (parts, antenna overhang) and copper keeps MB_CLEAR from every hole
    boxes = []
    for bi, (ox, oy) in enumerate(offs):
        for fp in b["fps"]:
            if fp["ref"].startswith("E"):
                continue
            x0, y0 = panel_pts(b, ox, oy, fp["box"][0], fp["box"][1]); x1, y1 = panel_pts(b, ox, oy, fp["box"][2], fp["box"][3])
            boxes.append((x0 - COURT_CLEAR, y0 - COURT_CLEAR, x1 + COURT_CLEAR, y1 + COURT_CLEAR))
    in_court = sum(1 for hx, hy in L["holes"] for x0, y0, x1, y1 in boxes if x0 <= hx <= x1 and y0 <= hy <= y1)
    ck(in_court == 0, f"no mouse-bite hole within {COURT_CLEAR} mm of a U1/J1/J2 courtyard, uncut there ({in_court} inside; E1 tail checked by copper)")
    pads = []
    for bi, (ox, oy) in enumerate(offs):
        for fp in b["fps"]:
            for pd in fp["pads"]:
                px, py = panel_pts(b, ox, oy, pd["x"], pd["y"])
                pads.append((px - pd["w"] / 2, py - pd["h"] / 2, px + pd["w"] / 2, py + pd["h"] / 2))
    worst = min((math.hypot(max(x0 - hx, 0, hx - x1), max(y0 - hy, 0, hy - y1)) - MB_DIA / 2
                 for hx, hy in L["holes"] for x0, y0, x1, y1 in pads), default=99.0)
    ck(worst >= MB_CLEAR, f"copper to mouse-bite hole edge >= {MB_CLEAR} mm (min {worst:.2f} mm, pad boxes)")
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
    for x, y in L["holes"]:
        out += ["0", "CIRCLE", "8", "MOUSE_BITE", "10", f"{x:.3f}", "20", f"{L['H'] - y:.3f}", "30", "0", "40", f"{MB_DIA / 2:.3f}"]
    out += ["0", "ENDSEC", "0", "EOF"]
    open(os.path.join(d, "panel.dxf"), "w").write("\n".join(out) + "\n")

if __name__ == "__main__":
    L = layout()
    res = checks(L)
    write(L)
    for ok, msg in res:
        print(("PASS  " if ok else "FAIL  ") + msg)
    print(f"panel {L['W']:.1f} x {L['H']:.1f} mm, 2 boards {L['b']['w']:.2f} x {L['b']['h']:.2f} mm each (outline from the board file, tail 25.8 mm per A-071), wrote panel/panel.dxf")
    print(f"tabs {len(L['tabs'])} ({len(L['tabs']) // N_BOARDS} per board), mouse-bite holes {len(L['holes'])}")
    print("RESULT: panel checks PASS" if all(o for o, _ in res) else "RESULT: panel checks FAIL")
    sys.exit(0 if all(o for o, _ in res) else 1)

"""Enclosure v3 slice 2 (CadQuery): tray, lid, tail seal plug, plus reference bodies (board, cell). Frame: see params_v3.py."""
import cadquery as cq
import params_v3 as P
import board_src as B


def _box(x0, y0, z0, x1, y1, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def _cyl(x, y, z0, z1, d):
    return cq.Workplane("XY").workplane(offset=z0).center(x, y).circle(d / 2).extrude(z1 - z0)


def free_clamp_pads():
    """Component-free 2.0 x 2.0 mm squares on the board top near the 4 corner regions (lid clamp pads). Computed from the board file."""
    comps = B.components(); res = []
    regions = {"TL": (0.3, -9.0, 8.0, -0.3), "TR": (26.0, -9.0, 34.2, -0.3), "BL": (0.3, -41.7, 9.0, -33.0), "BR": (24.0, -41.7, 34.2, -33.0)}
    for k, (x0, y0, x1, y1) in regions.items():
        # brute force on a 0.25 grid
        cand = []
        gx = x0 + 1.0
        while gx <= x1 - 1.0 + 1e-9:
            gy = y0 + 1.0
            while gy <= y1 - 1.0 + 1e-9:
                sq = (gx - 1.0, gy - 1.0, gx + 1.0, gy + 1.0)
                if all(B.gap(sq, c["box"]) > 0.2 for c in comps.values()):
                    cand.append((gx, gy))
                gy += 0.25
            gx += 0.25
        if cand:
            res.append((k, cand[0]))
    return res


def tray():
    h = P.FLOOR + P.INNER_H
    body = _box(P.OUT_X0, P.OUT_Y0, -P.FLOOR, P.OUT_X1, P.OUT_Y1, P.INNER_H).edges("|Z").fillet(P.FILLET)
    cav = _box(P.INNER_X0, P.INNER_Y0, 0, P.INNER_X1, P.INNER_Y1, P.INNER_H + 1)
    t = body.cut(cav)
    # board standoff pads under the 4 board corners (bottom of the board is GND copper only)
    for (x, y) in [(1.8, -1.8), (32.7, -1.8), (1.8, -40.2), (32.7, -40.2)]:
        t = t.union(_box(x - 1.5, y - 1.5, 0, x + 1.5, y + 1.5, P.STANDOFF))
    # screw bosses with insert holes
    for (x, y) in P.BOSS_XY:
        t = t.union(_cyl(x, y, 0, P.INNER_H, P.BOSS_D))
    for (x, y) in P.BOSS_XY:
        t = t.cut(_cyl(x, y, P.INNER_H - P.INSERT_DEPTH, P.INNER_H + 1, P.INSERT_HOLE))
    # tail notch (open to the rim, no bridge) in the bottom wall; plug drops in from above
    cx = P.BOARD_W / 2
    t = t.cut(_box(cx - P.NOTCH_W / 2, P.OUT_Y0 - 1, 0, cx + P.NOTCH_W / 2, P.INNER_Y0 + 0.01, P.INNER_H + 1))
    # USB-C window in the right wall (closed rectangle, 9.6 mm bridge) + overmold pocket from outside
    t = t.cut(_box(P.INNER_X1 - 0.5, P.J1_Y - P.USB_W / 2, P.J1_Z - P.USB_H / 2, P.OUT_X1 + 1, P.J1_Y + P.USB_W / 2, P.J1_Z + P.USB_H / 2))
    pw, ph, pd = P.USB_POCKET
    t = t.cut(_box(P.OUT_X1 - pd, P.J1_Y - pw / 2, P.J1_Z - ph / 2, P.OUT_X1 + 1, P.J1_Y + pw / 2, P.J1_Z + ph / 2))
    return t


def lid():
    """Lid prints outer face down on the bed; everything below is drawn in assembled position (underside at z = INNER_H)."""
    z0 = P.INNER_H
    L = _box(P.OUT_X0, P.OUT_Y0, z0, P.OUT_X1, P.OUT_Y1, z0 + P.LID_T).edges("|Z").fillet(P.FILLET)
    top = z0 + P.LID_T
    # screw clearance holes (M2, counterbored head not needed: pan head sits on the 2.4 mm lid)
    for (x, y) in P.BOSS_XY:
        L = L.cut(_cyl(x, y, z0 - 1, top + 1, P.SCREW_D))
    # light window: collar tube under the lid + through hole + counterbore for the film
    ux, uy = P.U6
    sensor_top = P.BOARD_Z1 + P.H_BY_REF["U6"]
    c_len = z0 - (sensor_top + P.COLLAR_GAP)
    L = L.union(_cyl(ux, uy, z0 - c_len, z0, P.COLLAR_OD))
    L = L.cut(_cyl(ux, uy, z0 - c_len - 1, top + 1, P.WIN_D)).cut(_cyl(ux, uy, top - P.WIN_CB_DEPTH, top + 1, P.WIN_CB_D))
    # AHT20 vents: baffle cup under the lid, open toward the board interior (-Y), slots through the lid
    vx, vy = P.U5
    cup_len = P.CUP_DEPTH
    cup = _box(vx - P.CUP_W / 2, vy - P.CUP_L / 2, z0 - cup_len, vx + P.CUP_W / 2, vy + P.CUP_L / 2, z0)
    cup = cup.cut(_box(vx - P.CUP_W / 2 + P.CUP_WALL, vy - P.CUP_L / 2 + P.CUP_WALL, z0 - cup_len - 1, vx + P.CUP_W / 2 - P.CUP_WALL, vy + P.CUP_L / 2 - P.CUP_WALL, z0 + 0.01))
    cup = cup.cut(_box(vx - 2.0, vy - P.CUP_L / 2 - 1, z0 - cup_len - 1, vx + 2.0, vy - P.CUP_L / 2 + P.CUP_WALL + 0.1, z0 - 1.0))  # opening low, on the -Y side
    L = L.union(cup)
    for i in range(P.VENT_N):
        sx = vx + (i - (P.VENT_N - 1) / 2) * P.VENT_PITCH
        L = L.cut(_box(sx - P.VENT_W / 2, vy - P.VENT_L / 2 + 0.2, z0 - 0.5, sx + P.VENT_W / 2, vy + P.VENT_L / 2 - 0.2, top + 1))
    # pinhole reset: guide tube to PIN_GAP above SW3 body top
    px, py = P.SW3
    sw_top = P.BOARD_Z1 + P.H_BY_REF["SW3"]
    p_len = z0 - (sw_top + P.PIN_GAP)
    L = L.union(_cyl(px, py, z0 - p_len, z0, P.PIN_TUBE_OD))
    L = L.cut(_cyl(px, py, z0 - p_len - 1, top + 1, P.PIN_D))
    # board clamp pads (free squares on the board top, tip 0.4 mm above the board)
    for k, (x, y) in free_clamp_pads():
        L = L.union(_box(x - 1.0, y - 1.0, P.BOARD_Z1 + 0.4, x + 1.0, y + 1.0, z0))
    return L


def plug():
    """Tail seal plug (prints with Y up). Slides over the tail from its free end, drops into the notch, tunnel filled with sealant [ASSUMED]."""
    cx = P.BOARD_W / 2
    p = _box(cx - P.PLUG_W / 2, P.INNER_Y0 - P.WALL, 0, cx + P.PLUG_W / 2, P.INNER_Y0, P.INNER_H)
    zc = (P.BOARD_Z0 + P.BOARD_Z1) / 2
    return p.cut(_box(cx - P.TUNNEL_W / 2, P.INNER_Y0 - P.WALL - 1, zc - P.TUNNEL_H / 2, cx + P.TUNNEL_W / 2, P.INNER_Y0 + 1, zc + P.TUNNEL_H / 2))


def board_ghost():
    """Reference body: 1.6 mm board from the outline + tallest-part boxes per component (heights ASSUMED). Not printed."""
    W, Lb, Lt = P.BOARD_W, P.BODY_L, P.BODY_L + P.TAIL_L
    pts = [(0, 0), (W, 0), (W, -Lb), (P.TAIL_X0 + P.TAIL_W, -Lb), (P.TAIL_X0 + P.TAIL_W, -Lt), (P.TAIL_X0, -Lt), (P.TAIL_X0, -Lb), (0, -Lb)]
    b = cq.Workplane("XY").workplane(offset=P.BOARD_Z0).polyline(pts).close().extrude(P.BOARD_T)
    for ref, c in B.components().items():
        x0, y0, x1, y1 = c["box"]
        b = b.union(_box(x0, y0, P.BOARD_Z1, x1, y1, P.BOARD_Z1 + c["h"]))
    return b


def cell_ghost():
    return _box(P.CELL_X0 + 1.0, P.CELL_Y0 + 0.3, 0, P.CELL_X1 - 1.0, P.CELL_Y1 - 0.3, 6.3)

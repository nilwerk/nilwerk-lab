"""CadQuery model of the v1 demo housing (4.E5), COMPACT round 2: tray + lid. Assembled position (STEP): tray z 0..Z_SPLIT, lid Z_SPLIT..Z_LID_TOP
(its guide tubes and collar hang below Z_SPLIT, inside the base). Print orientation (STL/3MF): tray as is (floor on the bed), lid flipped
(top face on the bed, skirt and posts grow upward): no supports. The LiPo cell lies under the perfboard in a floor cradle (no bay)."""
import cadquery as cq
import params_v1 as P


def _box(x0, y0, z0, x1, y1, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def _rbox(x0, y0, z0, x1, y1, z1, r):
    return _box(x0, y0, z0, x1, y1, z1).edges("|Z").fillet(r)


def _cyl(x, y, z0, z1, d):
    return cq.Workplane("XY").circle(d / 2.0).extrude(z1 - z0).translate((x, y, z0))


def hold_xy():
    return [(x, P.cy(y)) for x, y in P.HOLD_DOC]


def btn_xy():
    return [(P.BTN_XDOC, P.cy(y)) for y in P.BTN_YDOC]


def _openings():
    """Cuts through the wall (apply to both parts): two USB-C openings in the left wall, soil cable exit in the bottom wall.
    Round 2: the parting plane is above both USB-C openings, so only the base carries them."""
    cuts = []
    for ydoc, zc in ((P.USB_SM_YDOC, P.USB_SM_Z), (P.USB_TP_YDOC, P.USB_TP_Z)):
        yc = P.cy(ydoc)
        cuts.append(_box(P.OX0 - 1.0, yc - P.PLUG_W / 2, zc - P.PLUG_H / 2, P.IX0 + 0.5, yc + P.PLUG_W / 2, zc + P.PLUG_H / 2))
    xc = P.J3_XYDOC[0]
    cuts.append(_box(xc - P.CABLE_W / 2, P.OY0 - 1.0, P.CABLE_Z - P.CABLE_H / 2, xc + P.CABLE_W / 2, P.IY0 + 0.5, P.CABLE_Z + P.CABLE_H / 2))
    return cuts


def tray():
    t = _rbox(P.OX0, P.OY0, 0, P.OX1, P.OY1, P.Z_SPLIT, P.R_OUT)
    t = t.cut(_rbox(P.IX0, P.IY0, P.Z_FLOOR, P.IX1, P.IY1, P.Z_SPLIT + 1, P.R_IN))
    # board support pads (under the long edges) and locator fins beside them
    for xa, xb in P.PAD_XS:
        for y0 in (0.0, P.PB_W - P.PAD_W):
            t = t.union(_box(xa, y0, P.Z_FLOOR - 0.01, xb, y0 + P.PAD_W, P.Z_PB_BOT))
        t = t.union(_box(xa, -P.FIT - P.FIN_T, P.Z_FLOOR - 0.01, xa + P.FIN_L, -P.FIT, P.Z_PB_TOP + P.FIN_H))
        t = t.union(_box(xa, P.PB_W + P.FIT, P.Z_FLOOR - 0.01, xa + P.FIN_L, P.PB_W + P.FIT + P.FIN_T, P.Z_PB_TOP + P.FIN_H))
    # LiPo cradle under the board: keep-out-side wall, two stops at the cell ends (bottom stop notched for the lead)
    z1 = P.Z_FLOOR + P.LOW_H
    t = t.union(_box(P.CAV_X0 - P.STOP_T, P.CAV_Y0 - P.STOP_T, P.Z_FLOOR - 0.01, P.CAV_X0, P.CAV_Y1 + P.STOP_T, z1))
    t = t.union(_box(P.CAV_X0, P.CAV_Y0 - P.STOP_T, P.Z_FLOOR - 0.01, P.CAV_X1, P.CAV_Y0, z1))
    t = t.union(_box(P.CAV_X0, P.CAV_Y1, P.Z_FLOOR - 0.01, P.CAV_X1, P.CAV_Y1 + P.STOP_T, z1))
    t = t.cut(_box(P.LEAD_NOTCH_X[0], P.CAV_Y0 - P.STOP_T - 0.1, P.Z_FLOOR, P.LEAD_NOTCH_X[1], P.CAV_Y0 + 0.01, z1 + 0.01))
    # strain relief S-bend posts in the bottom strip
    for x, y in P.SR_POSTS:
        t = t.union(_cyl(x, y, P.Z_FLOOR - 0.01, z1, P.POST_D))
    # screw bosses with insert hole and spigot counterbore at the top
    for x, y in P.boss_xy():
        t = t.union(_cyl(x, y, P.Z_FLOOR - 0.01, P.Z_SPLIT, P.BOSS_D))
        t = t.cut(_cyl(x, y, P.Z_SPLIT - P.INSERT_HOLE_DEPTH, P.Z_SPLIT + 1, P.INSERT_HOLE))
        t = t.cut(_cyl(x, y, P.Z_SPLIT - P.SPIGOT_H, P.Z_SPLIT + 1, P.SPIGOT_D + 2 * P.SPIGOT_CLEAR))
    for c in _openings():
        t = t.cut(c)
    return t


def lid():
    zt, zb = P.Z_TOP, P.Z_SPLIT
    plate = _rbox(P.OX0, P.OY0, zt, P.OX1, P.OY1, zt + P.LID_T, P.R_OUT)
    if P.DESIGN_TOUCH:
        plate = plate.faces(">Z").edges().chamfer(P.TOP_CHAMFER)
    skirt = _rbox(P.OX0, P.OY0, zb, P.OX1, P.OY1, zt + 0.01, P.R_OUT).cut(_rbox(P.IX0, P.IY0, zb - 1, P.IX1, P.IY1, zt + 0.02, P.R_IN))
    L = plate.union(skirt)
    # screw posts with spigot, clearance hole and head recess
    for x, y in P.boss_xy():
        L = L.union(_cyl(x, y, zb - P.SPIGOT_H, zt + 0.01, P.SPIGOT_D))
        L = L.union(_cyl(x, y, zb, zt + 0.01, P.BOSS_D))
        L = L.cut(_cyl(x, y, zb - 2, zt + P.LID_T + 1, P.SCREW_D))
        L = L.cut(_cyl(x, y, zt + P.LID_T - P.CB_HEAD_DEPTH, zt + P.LID_T + 1, P.CB_HEAD_D))
    # board hold-down pins (stop 0.3 above the board top)
    for x, y in hold_xy():
        L = L.union(_cyl(x, y, P.Z_PB_TOP + P.HOLD_GAP, zt + 0.01, P.HOLD_D))
    # BOOT / RESET pin guides: tube down to 1 mm above the assumed button top
    z_btn = P.Z_PB_TOP + P.BTN_PRESS_H + P.BTN_GAP
    for x, y in btn_xy():
        L = L.union(_cyl(x, y, z_btn, zt + 0.01, P.BTN_TUBE_OD))
        L = L.cut(_cyl(x, y, z_btn - 1, zt + P.LID_T + 1, P.BTN_HOLE_D))
    # BH1750 light window with a collar (stops stray light from the box interior)
    bx, by = P.BH_XYDOC[0], P.cy(P.BH_XYDOC[1])
    z_bh = P.Z_PB_TOP + P.PARTS["BH1750"][4] + P.BH_COLLAR_GAP
    L = L.union(_cyl(bx, by, z_bh, zt + 0.01, P.BH_COLLAR_OD))
    L = L.cut(_cyl(bx, by, z_bh - 1, zt + P.LID_T + 1 - P.LIGHT_SKIN, P.BH_WIN_D))
    # AHT20 vent slots
    ax, ay = P.AHT_XYDOC[0], P.cy(P.AHT_XYDOC[1])
    for i in range(P.VENT_N):
        dx = (i - (P.VENT_N - 1) / 2) * P.VENT_PITCH
        L = L.cut(_box(ax + dx - P.VENT_W / 2, ay - P.VENT_L / 2, zt - 1, ax + dx + P.VENT_W / 2, ay + P.VENT_L / 2, zt + P.LID_T + 1))
    # TP4056 charge LED window
    lx, ly = P.LED_XYDOC[0], P.cy(P.LED_XYDOC[1])
    L = L.cut(_box(lx - P.LED_WIN[0] / 2, ly - P.LED_WIN[1] / 2, zt - 1, lx + P.LED_WIN[0] / 2, ly + P.LED_WIN[1] / 2, zt + P.LID_T + 1))
    # J1 jumper hatch
    jx, jy = P.J1_XYDOC[0], P.cy(P.J1_XYDOC[1])
    L = L.cut(_box(jx - P.HATCH[0] / 2, jy - P.HATCH[1] / 2, zt - 1, jx + P.HATCH[0] / 2, jy + P.HATCH[1] / 2, zt + P.LID_T + 1))
    for c in _openings():
        L = L.cut(c)
    return L


def lid_print():
    """Lid flipped for printing: top face on the bed."""
    return lid().rotate((0, 0, 0), (1, 0, 0), 180).translate((0, 0, P.Z_LID_TOP))


def perfboard_ghost():
    return _box(0, 0, P.Z_PB_BOT, P.PB_L, P.PB_W, P.Z_PB_TOP)


def parts_ghost():
    """Component boxes on the perfboard (heights ASSUMED), one solid."""
    g = None
    for name, (x0, y0, x1, y1, h, _s) in P.PARTS.items():
        b = _box(x0, P.cy(y1), P.Z_PB_TOP, x1, P.cy(y0), P.Z_PB_TOP + h)
        g = b if g is None else g.union(b)
    return g


def cell_ghost():
    """LiPo cell (BRIEF size) lying on the cradle floor under the perfboard, 51 along Y, lead end at the bottom stop."""
    return _box(P.CELL_X0, P.CELL_Y0, P.Z_FLOOR, P.CELL_X1, P.CELL_Y1, P.Z_FLOOR + P.CELL_CELL[2])

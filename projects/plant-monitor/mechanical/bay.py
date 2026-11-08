"""Parametric battery bay (tray + flat lid; retention screws wait for the PCB outline, 4.P1) for enclosure v3, CadQuery.

Print orientation: tray open side up, lid flat (plate on the bed). No supports: the wire notch is open to
the top rim (no bridge), the lid lip is a vertical extrusion. (NFR-05 seal, screws, board
region come later with 4.P1.)
"""
import math
import params as P


def snap_up(x, step=P.LAYER):
    return math.ceil(round(x / step, 6)) * step


def dims(key, **over):
    """All derived dimensions of one variant as a plain dict (no CAD needed)."""
    v = dict(P.VARIANTS[key])
    v.update(over)
    bay_l = v["L"] + 2 * P.END_CLEAR
    bay_w = v["W"] + 2 * P.FDM_CLEAR
    bay_h_raw = v["H"] * (1 + P.SWELL_FRAC) + P.Z_CLEAR
    bay_h = snap_up(bay_h_raw)               # cavity depth snapped to whole layers
    out_l, out_w = bay_l + 2 * P.WALL, bay_w + 2 * P.WALL
    out_h = P.FLOOR + bay_h + P.LID
    return dict(key=key, name=v["name"], cell_l=v["L"], cell_w=v["W"], cell_h=v["H"],
                bay_l=bay_l, bay_w=bay_w, bay_h_raw=bay_h_raw, bay_h=bay_h,
                out_l=out_l, out_w=out_w, out_h=out_h, wall=P.WALL,
                tray_h=P.FLOOR + bay_h,
                spare_h=bay_h - v["H"], spare_w=bay_w - v["W"], spare_l=bay_l - v["L"])


def tray(key, **over):
    import cadquery as cq
    d = dims(key, **over)
    body = cq.Workplane("XY").box(d["out_l"], d["out_w"], d["tray_h"], centered=(True, True, False)) \
        .edges("|Z").fillet(2.0)
    cav = cq.Workplane("XY").workplane(offset=P.FLOOR) \
        .box(d["bay_l"], d["bay_w"], d["bay_h"] + 1, centered=(True, True, False))
    t = body.cut(cav)
    # wire/plug notch in the +X end wall, open to the top rim
    notch = cq.Workplane("XY").box(P.WALL + 2, P.WIRE_NOTCH_W, P.WIRE_NOTCH_H, centered=(True, True, False)) \
        .translate((d["bay_l"] / 2 + P.WALL / 2, 0, d["tray_h"] - P.WIRE_NOTCH_H))
    return t.cut(notch)


def lid(key, **over):
    import cadquery as cq
    d = dims(key, **over)
    plate = cq.Workplane("XY").box(d["out_l"], d["out_w"], P.LID, centered=(True, True, False)) \
        .edges("|Z").fillet(2.0)
    return plate


def cell_ghost(key, **over):
    """Cell envelope (visual only, never exported as a part)."""
    import cadquery as cq
    d = dims(key, **over)
    return cq.Workplane("XY").box(d["cell_l"], d["cell_w"], d["cell_h"], centered=(True, True, False)) \
        .translate((0, 0, P.FLOOR))

#!/usr/bin/env python3
"""Generate plant-monitor.kicad_pcb (KiCad 9) and the DFM rules in plant-monitor.kicad_pro (Plan 4.P2, slice 1).

Emil (PCB Designer).  No GUI and no KiCad were available, so the board is WRITTEN, not drawn.  Run: python3 gen_pcb.py
Inputs: design.py (parts, nets), layout-brief.md (rules O1-O8, section 5 DFM), docs/interfaces/pcb-enclosure-bay.md (cell bay),
mechanical/params.py is NOT imported (bay allowances belong to Yara); the cell cavity below is copied from pcb-enclosure-bay.md.

SCOPE OF THIS SLICE: outline, placement, antenna keep-out, GND vias, DFM rules.  NOT routed (no tracks, no zone fill).
Tags: [brief] = from layout-brief.md, [mine] = my proposal/assumption for this slice, [open] = Yara/Arsany question.
Footprints marked PLACEHOLDER have the right pad NUMBERS and nets but pad geometry NOT read from the manufacturer drawing:
they are good enough to place and test spacing, NOT to send to a fab.  Replace them with the KiCad library / drawn footprints
before the Gerber gate (4.P3).
"""
from __future__ import annotations
import json, math, os, sys, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design as D

NS = uuid.UUID("6f1d3a52-0b1e-4c57-9a3e-6e696c77726b")
def uid(*k):
    return str(uuid.uuid5(NS, "/".join(map(str, k))))

# ---------------------------------------------------------------------------------------------
# Board geometry (mm, KiCad y axis points DOWN; antenna at the top y=0; board x 0..W, body y 0..BODY_L, stake tail below)
# ---------------------------------------------------------------------------------------------
BOARD_W = 34.5        # [mine] = cell width 34.5; brief section 3 option A (cell beside), board about 34.5 x 38 -> 42 here for the parts
BODY_L = 42.0         # [mine] result of the placement below (not a given); Yara Q2 (inner length) still [open]
TAIL_W, TAIL_L = 12.0, 25.8   # [mine] O5/S1: electrodes are copper on a tail of the same board. 25.8 mm = tail for the 14 mm enclosure variant (A-071, accepted by Arsany 2026-11-12; was 25.0). Stake size is Yara Q5 [open]
TAIL_X0 = (BOARD_W - TAIL_W) / 2
# Cell bay beside the board (brief section 3 option A, recommendation).  Cavity from pcb-enclosure-bay.md (Yara 2026-11-08), not computed here.
CELL_CAV = (53.0, 35.1)   # L (along x), W (along y), mm
CELL_GAP = 5.0            # [brief] 5 mm cell-to-board gap for wires/J2
CELL_X1 = -CELL_GAP
CELL_X0 = CELL_X1 - CELL_CAV[0]
CELL_Y1 = BODY_L
CELL_Y0 = CELL_Y1 - CELL_CAV[1]
# Antenna (O2): the module antenna end overhangs the top board edge, module on the right side so the cell is far away.
U1_W, U1_L = 13.2, 16.6           # [read] datasheet v2.2 Fig 11-1; footprint origin = module centre (Espressif footprint: body y -8.3..+8.3)
U1_PAD_TOP_REL = -2.6             # [read] top edge of the top pad row relative to the footprint origin (Espressif footprint, matches Fig 11-1: 5.7 mm antenna area above it)
U1_PAD_TOP_Y = 1.2                # [mine] top pad row edge 1.2 mm below the board edge: copper-to-edge >= 0.5 and 0.2 mm clear of the keep-out strip
U1_CY = U1_PAD_TOP_Y - U1_PAD_TOP_REL
U1_OVERHANG = U1_L / 2 - U1_CY    # antenna end beyond the board edge (derived, 4.5 mm; slice 1 assumed 6.0 with a placeholder land pattern)
U1_CX = BOARD_W - 1.0 - U1_W / 2  # 1.0 mm from the right edge [mine]
ANT_KEEPOUT = (U1_CX - U1_W / 2 - 3.0, 0.0, BOARD_W, U1_PAD_TOP_Y - 0.2)   # [mine] 3 mm beside the module, down to 0.2 mm above the first pad row; both layers (O2)
ANT_CLEAR_MM = 15.0               # [brief O2] Espressif: >= 15 mm clear in all directions in the housing
HEAT_CLEAR_MM = 10.0              # [brief O6] AHT20 >= 10 mm from TP4056
USBC_ESD_MAX_MM = 10.0            # [brief O4] D1 within 10 mm of J1

# DFM rules [brief section 5, design-rule column]
RULES = dict(clearance=0.2, track=0.2, power_track=0.4, vbat_track=0.5, via_dia=0.7, via_drill=0.3,
             copper_edge=0.5, mask_margin=0.05, min_text=1.0, min_line=0.15)

# ---------------------------------------------------------------------------------------------
# Footprints (slice 2).  Pads are dicts: num,type(smd|thru_hole|np_thru_hole),shape,x,y,ang,w,h,drill,layers,rratio.
# kind "lib"        = pad geometry read from a KiCad / Espressif library .kicad_mod in footprints/ (footprints/SOURCES.md says where from)
# kind "datasheet"  = drawn by Emil from a manufacturer drawing (XKB TS-1187A P.C.B. LAYOUT; AHT20 Fig. 1 bottom view)
# kind "placeholder"= pad NUMBERS right, geometry NOT from a drawing (BH1750 still, see footprints/SOURCES.md)
# kind "electrode"  = our own copper (soil probe), not a part
# ---------------------------------------------------------------------------------------------
import kmod

def P(num, x, y, w, h, shape="rect", layers=("F.Cu", "F.Mask", "F.Paste")):
    return dict(num=num, type="smd", shape=shape, x=x, y=y, ang=0.0, w=w, h=h, drill=None, layers=list(layers), rratio=None)

FOOT = {}
_LIB = {
    "Resistor_SMD:R_0603_1608Metric": "R_0603_1608Metric",
    "Capacitor_SMD:C_0603_1608Metric": "C_0603_1608Metric",
    "LED_SMD:LED_0603_1608Metric": "LED_0603_1608Metric",
    "LED_SMD:LED_0805_2012Metric": "LED_0805_2012Metric",
    "Package_TO_SOT_SMD:SOT-23-5": "SOT-23-5",
    "Package_TO_SOT_SMD:SOT-23-6": "SOT-23-6",
    "Package_SO:TSSOP-8_4.4x3mm_P0.65mm": "TSSOP-8_4.4x3mm_P0.65mm",
    "Package_SO:SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.41x3.81mm": "SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.41x3.81mm",
    "RF_Module:ESP32-C3-MINI-1": "ESP32-C3-MINI-1",
    "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12": "USB_C_Receptacle_HRO_TYPE-C-31-M-12",
    "Connector_JST:JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal": "JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal",
}
for _k, _v in _LIB.items():
    _d = kmod.load(_v)
    FOOT[_k] = dict(pads=_d["pads"], court=_d["court"], kind="lib")
# XKB TS-1187A-x-x-x drawing, "P.C.B. LAYOUT TOP VIEW": pad rows 7.0 outer / 5.0 inner apart in x (pad 1.0 wide, centres +-3.0),
# 4.5 outer / 3.0 inner in y (pad 0.75 high, centres +-1.875).  Terminals A,B are joined inside, C,D likewise (switch symbol on the drawing):
# A-B = one contact, C-D = the other.  Pad numbers: 1=A top left, 2=B top right (signal pair), 3=C bottom left, 4=D bottom right (GND pair).
FOOT["NW:SW_TS-1187A-B-A-B_5.1x5.1"] = dict(
    pads=[P("1", -3.0, -1.875, 1.0, 0.75), P("2", 3.0, -1.875, 1.0, 0.75), P("3", -3.0, 1.875, 1.0, 0.75), P("4", 3.0, 1.875, 1.0, 0.75)],
    court=(-3.75, -2.85, 3.75, 2.85), kind="datasheet")
# U5 / U6 (slice 3): LCSC/EasyEDA footprint data, copied to footprints/*.kicad_mod (source and open points in footprints/SOURCES.md).
# Pad 7 (EP) of the BH1750 is NOT copied: ROHM datasheet note 10 says the central pad must not be soldered or connected.
# U5 AHT20 (A-083, accepted 2026-11-12): pads from the datasheet, Fig. 1 bottom view 0.55 x 0.4 mm, pitch 1.0 mm; pin 1 = top right of the
# bottom view (Table 5 top view mirrored). Replaces the LCSC/EasyEDA 0.8 x 0.5 mm pads. Source and open points: footprints/SOURCES.md.
FOOT["NW:AHT20_DFN-6_3x3"] = dict(pads=kmod.load("AHT20_DFN-6_3x3")["pads"], court=kmod.load("AHT20_DFN-6_3x3")["court"], kind="datasheet")
FOOT["NW:WSOF-6_BH1750FVI"] = dict(pads=kmod.load("WSOF-6_BH1750FVI")["pads"], court=kmod.load("WSOF-6_BH1750FVI")["court"], kind="easyeda")
# E1: soil electrodes, copper only on F.Cu (no mask opening: covered by solder mask, O5), tail frame, origin = tail top centre
FOOT["NW:SOIL_PROBE_STAKE"] = dict(pads=[P("2", -4.0, 11.0, 1.5, 20.0, layers=("F.Cu",)), P("1", 0.0, 11.0, 3.5, 20.0, layers=("F.Cu",)),
                                         P("2", 4.0, 11.0, 1.5, 20.0, layers=("F.Cu",))],
                                   court=(-TAIL_W / 2, 0, TAIL_W / 2, TAIL_L), kind="electrode")
# Design pin name -> library pad names where the library names differ (J1: the design merges A1/B12 etc. into one pin name)
PADMAP = {"J1": {"A1B12": ["A1", "B12"], "B1A12": ["B1", "A12"], "A4B9": ["A4", "B9"], "B4A9": ["B4", "A9"]}}

# ---------------------------------------------------------------------------------------------
# Placement: ref -> (x, y, rot) board coordinates of the footprint origin.  Zones follow brief O6, rules in the comments.
# ---------------------------------------------------------------------------------------------
PLACE = {
    # O2/O3: module at the top right, antenna end overhanging the board edge, away from the cell, wet-soil end is the opposite end (R-06)
    "U1": (U1_CX, U1_CY, 0),
    # FR-D01 decoupling right at the module 3V3 side (below the module)
    "C5": (22.0, 14.0, 0), "C4": (25.6, 14.0, 0), "C12": (29.2, 14.0, 0),
    "R3": (22.0, 16.2, 0), "R4": (25.6, 16.2, 0), "R5": (29.2, 16.2, 0), "R16": (32.6, 14.0, 0),
    # sensors, top left, >= 10 mm from the TP4056 (O6); BH1750 on the face that sees the light window (Q6 [open])
    "U5": (4.5, 4.5, 0), "C6": (4.5, 8.0, 0),
    "U6": (11.5, 4.5, 0), "C7": (11.5, 8.0, 0),
    "R13": (4.5, 11.0, 0), "R14": (11.5, 11.0, 0),
    # switches: BOOT/RESET reachable with the case open, SW3 pinhole position from Yara (Q6 [open])
    "SW1": (5.0, 17.5, 0), "SW2": (13.5, 17.5, 0), "SW3": (5.0, 23.5, 0),
    # power block (O6): LDO + rail caps in the middle, charger near USB-C
    "U2": (15.5, 25.0, 0), "C3": (16.5, 28.0, 0), "C14": (19.5, 22.5, 0), "C13": (19.5, 24.8, 0),
    "R7": (11.0, 21.5, 0), "R8": (14.6, 21.5, 0), "C11": (11.0, 23.6, 0),
    "U3": (21.8, 31.0, 0), "C1": (24.0, 26.0, 0), "C2": (19.5, 27.0, 0), "R9": (19.8, 36.0, 0),
    "R10": (12.0, 37.6, 0), "R11": (12.0, 39.6, 0), "D2": (8.0, 37.8, 0), "D3": (8.0, 40.2, 0),
    # J1 USB-C: right edge, mouth flush (O4), far from the antenna; ESD D1 and C10 right at it (<= 10 mm)
    "J1": (BOARD_W - 3.65, 33.0, 90), "D1": (23.45, 36.0, 0), "C10": (BOARD_W - 3.6, 26.8, 0), "R1": (27.0, 40.4, 0), "R2": (30.5, 40.4, 0),
    # cell connector at the cell side (left edge, mouth toward the cell), protection next to it
    "J2": (5.2, 31.4, 270), "U4": (12.6, 29.5, 0), "Q1": (14.2, 33.5, 0), "R15": (3.0, 37.6, 0), "C9": (3.0, 39.5, 0),
    # soil front end at the neck of the tail: SOIL_PROBE short (O5/O6)
    "U7": (16.0, 38.0, 0), "R12": (20.5, 40.2, 0), "C8": (16.2, 40.6, 0),
    # tail with the electrodes
    "E1": (BOARD_W / 2, BODY_L, 0),
}
# vias [brief O3 / section 5]: >= 9 on the module ground pad, 4-6 under the TP4056 exposed pad; 0.3 / 0.7 mm
def via_list():
    """4.P2 slice 2 / Needs-Arsany A-069: NO via inside any SMD pad (lowest-risk option, no filled-and-capped vias needed at JLC).
    Module: 12 GND vias in the 0.525 mm gaps of the 3 x 3 ground pad grid (Espressif Fig 11-1 draws the thermal vias between the pads).
    A via copper circle (0.7 mm) overlaps the neighbouring pad copper by about 0.09 mm (same net), the hole itself is in the gap.
    TP4056: 4 vias just outside the exposed pad, joined to it by short 0.4 mm GND stubs (see stub_tracks)."""
    v = []
    gx, gy = U1_CX, U1_CY
    xs, ys = (-1.975, 0.0, 1.975), (0.725, 2.7, 4.675)
    gapx, gapy = (-0.9875, 0.9875), (1.7125, 3.6875)
    for x in gapx:                       # 4 crossings + 6 midpoints of the two vertical gaps
        for y in gapy + ys:
            v.append(("U1gnd", gx + x, gy + y))
    for y in gapy:                       # 2 midpoints of the horizontal gaps (centre column)
        v.append(("U1gnd", gx + 0.0, gy + y))
    ux, uy, _ = PLACE["U3"]
    for dx in (-0.6, 0.6):
        for dy in (-2.75, 2.75):
            v.append(("U3ep", ux + dx, uy + dy))
    return v

def stub_tracks():
    """(x1,y1,x2,y2,width) GND stubs from each TP4056 via into the exposed pad (this is the only routing in slice 2)."""
    ux, uy, _ = PLACE["U3"]
    out = []
    for dx in (-0.6, 0.6):
        for sgn in (-1, 1):
            out.append((ux + dx, uy + sgn * 2.75, ux + dx, uy + sgn * 1.5, RULES["power_track"]))
    return out

# ---------------------------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------------------------
def rot(lx, ly, deg):
    a = math.radians(deg)
    return lx * math.cos(a) + ly * math.sin(a), -lx * math.sin(a) + ly * math.cos(a)

def f(v):
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s

NETS = {}
for p in D.PARTS:
    for pin in p.pins:
        if pin[2] != "NC":
            NETS.setdefault(pin[2], len(NETS) + 1)

def netref(name):
    return f'(net {NETS[name]} "{name}")' if name in NETS else ""

def pad_nets(p: D.Part):
    """library/drawing pad name -> net name (design pin names mapped through PADMAP)."""
    m = PADMAP.get(p.ref, {})
    out = {}
    for pin in p.pins:
        for pn in m.get(pin[0], [pin[0]]):
            out[pn] = pin[2]
    return out

def fmt_pad(pd, fp_rot, net_text, uid_s):
    ang = (pd["ang"] + fp_rot) % 360       # KiCad board file: pad angle is the ABSOLUTE orientation (footprint rotation included); position stays in the footprint frame
    at = f'(at {f(pd["x"])} {f(pd["y"])}{" " + f(ang) if ang else ""})'
    layers = " ".join(f'"{l}"' for l in pd["layers"])
    dr = ""
    if pd["drill"]:
        dr = f' (drill {f(pd["drill"][0])})' if abs(pd["drill"][0] - pd["drill"][1]) < 1e-9 and pd["shape"] != "oval" else f' (drill oval {f(pd["drill"][0])} {f(pd["drill"][1])})'
    rr = f' (roundrect_rratio {f(pd["rratio"])})' if pd["rratio"] is not None else ""
    return f'\t\t(pad "{pd["num"]}" {pd["type"]} {pd["shape"]} {at} (size {f(pd["w"])} {f(pd["h"])}){dr} (layers {layers}){rr} {net_text} (uuid "{uid_s}"))'

def footprint_text(p: D.Part):
    spec = FOOT[p.footprint]
    pads, court, kind = spec["pads"], spec["court"], spec["kind"]
    x, y, r = PLACE[p.ref]
    pinnet = pad_nets(p)
    cw, ch = court[2] - court[0], court[3] - court[1]
    L = []
    L.append(f'\t(footprint "{p.footprint}"')
    L.append(f'\t\t(layer "F.Cu")')
    L.append(f'\t\t(uuid "{uid("fp", p.ref)}")')
    L.append(f'\t\t(at {f(x)} {f(y)}{" " + f(r) if r else ""})')
    L.append(f'\t\t(descr "{kind.upper()}: {p.value}")' if kind != "lib" else f'\t\t(descr "{p.value}")')
    L.append(f'\t\t(property "Reference" "{p.ref}" (at 0 {f(court[1] - 0.9)} {f(-r % 360 if r else 0)}) (layer "F.Fab") (uuid "{uid("ref", p.ref)}") (effects (font (size 0.8 0.8) (thickness 0.12))))')
    L.append(f'\t\t(property "Value" "{p.value}" (at 0 {f(court[3] + 0.9)} {f(-r % 360 if r else 0)}) (layer "F.Fab") (hide yes) (uuid "{uid("val", p.ref)}") (effects (font (size 0.8 0.8) (thickness 0.12))))')
    L.append(f'\t\t(property "LCSC" "{p.lcsc}" (at 0 0) (layer "F.Fab") (hide yes) (uuid "{uid("lcsc", p.ref)}") (effects (font (size 0.8 0.8) (thickness 0.12))))')
    L.append(f'\t\t(attr {"smd" if kind != "electrode" else "smd exclude_from_bom exclude_from_pos_files"})')
    L.append(f'\t\t(fp_rect (start {f(court[0])} {f(court[1])}) (end {f(court[2])} {f(court[3])}) (stroke (width 0.05) (type default)) (fill no) (layer "F.CrtYd") (uuid "{uid("cy", p.ref)}"))')
    for i, pd in enumerate(pads):
        nm = pinnet.get(pd["num"], "NC")
        net = netref(nm) if nm != "NC" and any(l in pd["layers"] for l in ("F.Cu", "*.Cu")) else ""
        L.append(fmt_pad(pd, r, net, uid("pad", p.ref, i)))
    L.append("\t)")
    return "\n".join(L)

# ---------------------------------------------------------------------------------------------
# F.Silkscreen (A-086, accepted 2026-11-12): reference designators and polarity only, no logos.
# Text height 1.0 mm, line 0.15 mm (JLC F15). Every label is placed where its box keeps >= 0.15 mm (min silk clearance) from every
# pad and from the other labels, and stays inside the outline. Checked by KiCad DRC (silk rules) in CI.
# ---------------------------------------------------------------------------------------------
SILK_REFS = ["U1", "U5", "U6", "J1", "J2", "D2", "D3"]
SILK_H, SILK_LINE, SILK_CLR = 1.0, 0.15, 0.15
SILK_CHECKS = []                  # filled by silk_items(): one PASS/FAIL line per silk element, printed by __main__
SILK_CHAR_W = 0.62 * SILK_H       # [mine] character advance of KiCad's default font, used for the label box estimate

def _pads_world():
    out = []
    for p in D.PARTS:
        x, y, r = PLACE[p.ref]
        for pd in FOOT[p.footprint]["pads"]:
            cx, cy = rot(pd["x"], pd["y"], r)
            w, h = (pd["h"], pd["w"]) if round(r) % 180 == 90 else (pd["w"], pd["h"])
            out.append(dict(ref=p.ref, num=pd["num"], x=x + cx, y=y + cy, w=w, h=h))
    return out

def _court_world(p):
    x, y, r = PLACE[p.ref]
    c = FOOT[p.footprint]["court"]
    pts = [rot(a, b, r) for a, b in [(c[0], c[1]), (c[2], c[1]), (c[2], c[3]), (c[0], c[3])]]
    xs = [q[0] + x for q in pts]; ys = [q[1] + y for q in pts]
    return min(xs), min(ys), max(xs), max(ys)

def _inside_outline(x0, y0, x1, y1):
    pts = outline_pts()
    def inside(px, py):
        c = False
        for i in range(len(pts)):
            (ax, ay), (bx, by) = pts[i], pts[(i + 1) % len(pts)]
            if (ay > py) != (by > py) and px < (bx - ax) * (py - ay) / (by - ay) + ax:
                c = not c
        return c
    return all(inside(px, py) for px in (x0, x1) for py in (y0, y1))

def _sep(a, b):
    """Gap between two boxes (x0,y0,x1,y1); >= SILK_CLR means clear."""
    dx = max(b[0] - a[2], a[0] - b[2]); dy = max(b[1] - a[3], a[1] - b[3])
    return max(dx, dy)

def _label_box(cx, cy, text):
    w = SILK_CHAR_W * len(text); h = SILK_H
    return (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)

def silk_items():
    pads = _pads_world()
    pad_boxes = [(q["x"] - q["w"] / 2, q["y"] - q["h"] / 2, q["x"] + q["w"] / 2, q["y"] + q["h"] / 2) for q in pads]
    placed = []     # label boxes already placed
    labels = []     # every silk element (text or bar): (name, box). All of them go through the final check below
    out, notes = [], []
    def try_place(text, cands):
        for cx, cy in cands:
            bx = _label_box(cx, cy, text)
            if not _inside_outline(*bx):
                continue
            if any(_sep(bx, pb) < SILK_CLR for pb in pad_boxes) or any(_sep(bx, o) < SILK_CLR for o in placed):
                continue
            placed.append(bx); labels.append((text, bx))
            return cx, cy
        raise SystemExit(f"silk: no clear place for {text!r}")
    def emit(text, cx, cy, tag):
        out.append(f'\t(gr_text "{text}" (at {f(cx)} {f(cy)}) (layer "F.SilkS") (uuid "{uid("silk", tag)}") '
                   f'(effects (font (size {SILK_H} {SILK_H}) (thickness {SILK_LINE}))))')
    # reference designators: 4 sides of the courtyard, nearest first
    gap = 0.4
    for ref in SILK_REFS:
        p = next(q for q in D.PARTS if q.ref == ref)
        x0, y0, x1, y1 = _court_world(p)
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        w, h = SILK_CHAR_W * len(ref) / 2, SILK_H / 2
        cands = [(mx, y0 - gap - h), (mx, y1 + gap + h), (x0 - gap - w, my), (x1 + gap + w, my),
                 (mx - (x1 - x0) / 4, y0 - gap - h), (mx + (x1 - x0) / 4, y1 + gap + h)]
        cx, cy = try_place(ref, cands)
        emit(ref, cx, cy, "ref-" + ref)
        notes.append(f"{ref} label at ({cx:.2f}, {cy:.2f})")
    # battery connector polarity: + at CELL+ (J2 pad 1), - at CELL- (pad 2); pads from the library footprint
    j2 = [q for q in pads if q["ref"] == "J2"]
    for num, sign in (("1", "+"), ("2", "-")):
        q = next(z for z in j2 if z["num"] == num)
        d = SILK_H / 2 + 0.5 + q["w"] / 2
        cands = [(q["x"], q["y"] + d + 0.2), (q["x"], q["y"] - d - 0.2), (q["x"] + d, q["y"]), (q["x"] - d, q["y"])]
        cx, cy = try_place(sign, cands)
        emit(sign, cx, cy, "pol-J2-" + num)
        notes.append(f"J2 pad {num} ({'CELL+' if sign == '+' else 'CELL-'}) polarity mark '{sign}' at ({cx:.2f}, {cy:.2f})")
    # LED cathode bar on the outer side of pad 1 (cathode, design.py D2/D3 pin 1 = K: [mine, UNVERIFIED] against the LED datasheet, see design.py)
    for ref in ("D2", "D3"):
        ps = [q for q in pads if q["ref"] == ref]
        p1 = next(q for q in ps if q["num"] == "1"); p2 = next(q for q in ps if q["num"] == "2")
        side = -1 if p1["x"] < p2["x"] else 1
        xb = p1["x"] + side * (p1["w"] / 2 + 0.3)
        yb0, yb1 = p1["y"] - 0.45, p1["y"] + 0.45
        bar = (xb - 0.02, yb0, xb + 0.02, yb1)
        labels.append((f"{ref} cathode bar", bar))
        out.append(f'\t(gr_line (start {f(xb)} {f(yb0)}) (end {f(xb)} {f(yb1)}) (stroke (width {SILK_LINE}) (type solid)) (layer "F.SilkS") (uuid "{uid("silk", "cath-" + ref)}"))')
        notes.append(f"{ref} cathode bar at x={xb:.2f} (pad 1 side)")
    # No antenna keep-out label on the silk (A-086 lists references and polarity only; the keep-out is labelled in the PR text).
    # Final enforcement, for EVERY silk element in `labels`: inside the board outline and SILK_CLR from pads and from other labels.
    global SILK_CHECKS
    SILK_CHECKS = []
    bad = []
    for i, (name, bx) in enumerate(labels):
        others = [b for j, (_, b) in enumerate(labels) if j != i]
        d_pad = min((_sep(bx, pb) for pb in pad_boxes), default=99.0)
        d_lab = min((_sep(bx, o) for o in others), default=99.0)
        ok = _inside_outline(*bx) and d_pad >= SILK_CLR and d_lab >= SILK_CLR
        SILK_CHECKS.append(f"{'PASS' if ok else 'FAIL'}  silk {name!r}: inside outline, pad clearance {d_pad:.2f} mm, "
                           f"label clearance {d_lab:.2f} mm (>= {SILK_CLR:.2f} mm; text box estimated, see SILK_CHAR_W)")
        if not ok:
            bad.append(name)
    if bad:
        raise SystemExit("silk: FAIL " + ", ".join(bad))
    return out, notes

def outline_pts():
    return [(0, 0), (BOARD_W, 0), (BOARD_W, BODY_L), (TAIL_X0 + TAIL_W, BODY_L), (TAIL_X0 + TAIL_W, BODY_L + TAIL_L),
            (TAIL_X0, BODY_L + TAIL_L), (TAIL_X0, BODY_L), (0, BODY_L)]

def build_pcb(extra_segs=(), extra_vias=()):
    o = []
    o.append('(kicad_pcb')
    o.append('\t(version 20241229)\n\t(generator "nilwerk_gen_pcb")\n\t(generator_version "9.0")')
    o.append('\t(general (thickness 1.6) (legacy_teardrops no))\n\t(paper "A4")')
    o.append('\t(layers (0 "F.Cu" signal) (2 "B.Cu" signal) (9 "F.Adhes" user "F.Adhesive") (11 "B.Adhes" user "B.Adhesive") '
             '(13 "F.Paste" user) (15 "B.Paste" user) (5 "F.SilkS" user "F.Silkscreen") (7 "B.SilkS" user "B.Silkscreen") '
             '(1 "F.Mask" user) (3 "B.Mask" user) (17 "Dwgs.User" user "User.Drawings") (19 "Cmts.User" user "User.Comments") '
             '(21 "Eco1.User" user "User.Eco1") (23 "Eco2.User" user "User.Eco2") (25 "Edge.Cuts" user) (27 "Margin" user) '
             '(31 "F.CrtYd" user "F.Courtyard") (29 "B.CrtYd" user "B.Courtyard") (35 "F.Fab" user "F.Fabrication") (33 "B.Fab" user "B.Fabrication"))')
    o.append('\t(setup (pad_to_mask_clearance 0) (allow_soldermask_bridges_in_footprints no) '
             '(pcbplotparams (layerselection 0x00000000_00000000_55555555_5755f5ff) (plot_on_all_layers_selection 0x00000000_00000000_00000000_00000000) (disableapertmacros no) (usegerberextensions no) (usegerberattributes yes) (outputformat 1) (outputdirectory "")))')
    o.append('\t(net 0 "")')
    for n, i in NETS.items():
        o.append(f'\t(net {i} "{n}")')
    for p in D.PARTS:
        o.append(footprint_text(p))
    # Edge.Cuts
    pts = outline_pts()
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        o.append(f'\t(gr_line (start {f(a[0])} {f(a[1])}) (end {f(b[0])} {f(b[1])}) (stroke (width 0.05) (type default)) (layer "Edge.Cuts") (uuid "{uid("edge", i)}"))')
    # documentation layer: cell cavity (Yara's numbers), 15 mm antenna clearance circle box, module overhang
    def user_rect(tag, x0, y0, x1, y1, layer="Dwgs.User"):
        o.append(f'\t(gr_rect (start {f(x0)} {f(y0)}) (end {f(x1)} {f(y1)}) (stroke (width 0.1) (type dash)) (fill no) (layer "{layer}") (uuid "{uid("ur", tag)}"))')
    user_rect("cell", CELL_X0, CELL_Y0, CELL_X1, CELL_Y1)
    user_rect("ant15", U1_CX - U1_W / 2 - ANT_CLEAR_MM, -U1_OVERHANG - ANT_CLEAR_MM, U1_CX + U1_W / 2 + ANT_CLEAR_MM, 0, "Cmts.User")
    o.append(f'\t(gr_text "CELL BAY {CELL_CAV[0]} x {CELL_CAV[1]} mm (enclosure v3 cavity, pcb-enclosure-bay.md); not copper" (at {f((CELL_X0 + CELL_X1) / 2)} {f((CELL_Y0 + CELL_Y1) / 2)}) (layer "Dwgs.User") (uuid "{uid("t1")}") (effects (font (size 1 1) (thickness 0.15))))')
    o.append(f'\t(gr_text "ANTENNA: module overhangs {U1_OVERHANG} mm; 15 mm clear box (Espressif guideline)" (at {f(U1_CX - 12)} {f(-U1_OVERHANG - 8)}) (layer "Cmts.User") (uuid "{uid("t2")}") (effects (font (size 1 1) (thickness 0.15))))')
    silk, silk_notes = silk_items()
    o.extend(silk)
    # vias
    n_gnd = NETS["GND"]
    for k, (tag, x, y) in enumerate(via_list()):
        o.append(f'\t(via (at {f(x)} {f(y)}) (size {RULES["via_dia"]}) (drill {RULES["via_drill"]}) (layers "F.Cu" "B.Cu") (net {n_gnd}) (uuid "{uid("via", k)}"))')
    for k, (x1, y1, x2, y2, w) in enumerate(stub_tracks()):
        o.append(f'\t(segment (start {f(x1)} {f(y1)}) (end {f(x2)} {f(y2)}) (width {f(w)}) (layer "F.Cu") (net {n_gnd}) (uuid "{uid("stub", k)}"))')
    # slice 3: power-section tracks and vias from route_power.py (net name, width, layer)
    for k, (x1, y1, x2, y2, w, lay, nn) in enumerate(extra_segs):
        lname = "F.Cu" if lay == 0 else "B.Cu"
        o.append(f'\t(segment (start {f(x1)} {f(y1)}) (end {f(x2)} {f(y2)}) (width {f(w)}) (layer "{lname}") (net {NETS[nn]}) (uuid "{uid("pwr", k)}"))')
    for k, (x, y, nn) in enumerate(extra_vias):
        o.append(f'\t(via (at {f(x)} {f(y)}) (size {RULES["via_dia"]}) (drill {RULES["via_drill"]}) (layers "F.Cu" "B.Cu") (net {NETS[nn]}) (uuid "{uid("pvia", k)}"))')
    # antenna keep-out (rule area) on both layers: no tracks, vias, pads, copper pour (O2).  Footprints are 'allowed' only because the module U1
    # itself overlaps the zone (its antenna end); check_layout.py asserts that no OTHER footprint touches the zone.
    kx0, ky0, kx1, ky1 = ANT_KEEPOUT
    o.append(f'\t(zone (net 0) (net_name "") (layers "F.Cu" "B.Cu") (uuid "{uid("ko")}") (name "ANT_KEEPOUT") (hatch edge 0.5) '
             f'(connect_pads (clearance 0)) (min_thickness 0.25) (filled_areas_thickness no) '
             f'(keepout (tracks not_allowed) (vias not_allowed) (pads not_allowed) (copperpour not_allowed) (footprints allowed)) '
             f'(fill (thermal_gap 0.5) (thermal_bridge_width 0.5)) '
             f'(polygon (pts (xy {f(kx0)} {f(ky0)}) (xy {f(kx1)} {f(ky0)}) (xy {f(kx1)} {f(ky1)}) (xy {f(kx0)} {f(ky1)}))))')
    # bottom GND pour over the body only (not the tail), 0.5 mm from the edge (O3); NOT filled in this slice
    e = RULES["copper_edge"]
    o.append(f'\t(zone (net {n_gnd}) (net_name "GND") (layer "B.Cu") (uuid "{uid("gnd")}") (name "GND_BOTTOM") (hatch edge 0.5) '
             f'(connect_pads (clearance {RULES["clearance"]})) (min_thickness 0.2) (filled_areas_thickness no) '
             f'(fill (thermal_gap 0.3) (thermal_bridge_width 0.4)) '
             f'(polygon (pts (xy {f(e)} {f(e)}) (xy {f(BOARD_W - e)} {f(e)}) (xy {f(BOARD_W - e)} {f(BODY_L - e)}) (xy {f(e)} {f(BODY_L - e)}))))')
    o.append(")")
    return "\n".join(o) + "\n"

def update_pro():
    path = os.path.join(HERE, "plant-monitor.kicad_pro")
    pro = json.load(open(path))
    R = RULES
    pro["board"] = {"design_settings": {
        "defaults": {"board_outline_line_width": 0.05, "copper_line_width": 0.2, "silk_line_width": 0.15, "silk_text_size_h": 1.0, "silk_text_size_v": 1.0, "silk_text_thickness": 0.15},
        "rules": {"min_clearance": R["clearance"], "min_track_width": R["track"], "min_via_annular_width": 0.2, "min_via_diameter": R["via_dia"],
                  "min_through_hole_diameter": R["via_drill"], "min_copper_edge_clearance": R["copper_edge"], "min_hole_clearance": 0.25,
                  "min_hole_to_hole": 0.25, "min_silk_clearance": 0.15, "min_text_height": R["min_text"], "min_text_thickness": R["min_line"],
                  "min_microvia_diameter": 0.2, "min_microvia_drill": 0.1, "min_resolved_spokes": 2, "min_connection": 0.0,
                  "solder_mask_to_copper_clearance": 0.0, "min_groove_width": 0.0},
        # Slice 1 is NOT routed: unconnected items are expected and shown as warnings, not errors.  Everything else keeps the KiCad default.
        "rule_severities": {"unconnected_items": "warning"},
    }, "layer_presets": [], "viewports": [], "meta": {"version": 2}}
    pro["net_settings"] = {"meta": {"version": 4}, "classes": [
        {"name": "Default", "clearance": R["clearance"], "track_width": R["track"], "via_diameter": R["via_dia"], "via_drill": R["via_drill"],
         "microvia_diameter": 0.3, "microvia_drill": 0.1, "diff_pair_width": 0.2, "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25, "wire_width": 6, "bus_width": 12, "line_style": 0, "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)"},
        {"name": "Power", "clearance": R["clearance"], "track_width": R["power_track"], "via_diameter": R["via_dia"], "via_drill": R["via_drill"],
         "microvia_diameter": 0.3, "microvia_drill": 0.1, "diff_pair_width": 0.2, "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25, "wire_width": 6, "bus_width": 12, "line_style": 0, "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)"},
        {"name": "Battery", "clearance": R["clearance"], "track_width": R["vbat_track"], "via_diameter": R["via_dia"], "via_drill": R["via_drill"],
         "microvia_diameter": 0.3, "microvia_drill": 0.1, "diff_pair_width": 0.2, "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25, "wire_width": 6, "bus_width": 12, "line_style": 0, "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)"}],
        "netclass_assignments": None,
        "netclass_patterns": [{"netclass": "Power", "pattern": "3V3"}, {"netclass": "Power", "pattern": "VBUS"}, {"netclass": "Power", "pattern": "GND"},
                              {"netclass": "Battery", "pattern": "VBAT"}, {"netclass": "Battery", "pattern": "CELL_NEG"}]}
    json.dump(pro, open(path, "w"), indent=2)
    open(path, "a").write("\n")

def write_dxf():
    """Outline + cell cavity + antenna keep-out + module overhang as DXF R12 LINE entities (O8, for Yara).  mm, y flipped to CAD convention (up)."""
    segs = []
    def poly(pts, layer):
        for i in range(len(pts)):
            segs.append((layer, pts[i], pts[(i + 1) % len(pts)]))
    poly(outline_pts(), "OUTLINE")
    c = [(CELL_X0, CELL_Y0), (CELL_X1, CELL_Y0), (CELL_X1, CELL_Y1), (CELL_X0, CELL_Y1)]
    poly(c, "CELL_BAY_CAVITY")
    k = ANT_KEEPOUT
    poly([(k[0], k[1]), (k[2], k[1]), (k[2], k[3]), (k[0], k[3])], "ANT_KEEPOUT")
    poly([(U1_CX - U1_W / 2, -U1_OVERHANG), (U1_CX + U1_W / 2, -U1_OVERHANG), (U1_CX + U1_W / 2, -U1_OVERHANG + U1_L), (U1_CX - U1_W / 2, -U1_OVERHANG + U1_L)], "MODULE_U1")
    out = ["0", "SECTION", "2", "ENTITIES"]
    for layer, a, b in segs:
        out += ["0", "LINE", "8", layer, "10", f(a[0]), "20", f(-a[1]), "30", "0", "11", f(b[0]), "21", f(-b[1]), "31", "0"]
    out += ["0", "ENDSEC", "0", "EOF"]
    open(os.path.join(HERE, "plant-monitor-outline.dxf"), "w").write("\n".join(out) + "\n")

if __name__ == "__main__":
    import route_power
    segs, vias, report = route_power.route_all()
    for row in report:
        print("route:", row)
    open(os.path.join(HERE, "plant-monitor.kicad_pcb"), "w").write(build_pcb(segs, vias))
    for line in SILK_CHECKS:
        print("silk:", line)
    print(f"silk: {sum(l.startswith('PASS') for l in SILK_CHECKS)} of {len(SILK_CHECKS)} silk elements PASS")
    update_pro()
    write_dxf()
    print("wrote plant-monitor.kicad_pcb and updated plant-monitor.kicad_pro")

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
TAIL_W, TAIL_L = 12.0, 25.0   # [mine] O5/S1: electrodes are copper on a tail of the same board; stake size is Yara Q5 [open]
TAIL_X0 = (BOARD_W - TAIL_W) / 2
# Cell bay beside the board (brief section 3 option A, recommendation).  Cavity from pcb-enclosure-bay.md (Yara 2026-11-08), not computed here.
CELL_CAV = (53.0, 35.1)   # L (along x), W (along y), mm
CELL_GAP = 5.0            # [brief] 5 mm cell-to-board gap for wires/J2
CELL_X1 = -CELL_GAP
CELL_X0 = CELL_X1 - CELL_CAV[0]
CELL_Y1 = BODY_L
CELL_Y0 = CELL_Y1 - CELL_CAV[1]
# Antenna (O2): the module antenna end overhangs the top board edge, module on the right side so the cell is far away.
U1_W, U1_L = 13.2, 16.6           # [read] datasheet v2.2 Fig 11-1 (brief section 1)
U1_OVERHANG = 6.0                 # [mine] antenna end beyond the board edge (antenna zone length NOT read from the datasheet figure)
U1_CX = BOARD_W - 1.0 - U1_W / 2  # 1.0 mm from the right edge [mine]
U1_CY = -U1_OVERHANG + U1_L / 2
U1_PAD_Y0 = 3.0 - U1_CY          # first signal pad row at board y = 3.0 (below the 2 mm keep-out) [mine, placeholder pattern]
ANT_KEEPOUT = (U1_CX - U1_W / 2 - 3.0, 0.0, BOARD_W, 2.0)   # x0,y0,x1,y1 on the board; [mine] 3 mm beside the module, 2 mm deep; both layers (O2)
ANT_CLEAR_MM = 15.0               # [brief O2] Espressif: >= 15 mm clear in all directions in the housing
HEAT_CLEAR_MM = 10.0              # [brief O6] AHT20 >= 10 mm from TP4056
USBC_ESD_MAX_MM = 10.0            # [brief O4] D1 within 10 mm of J1

# DFM rules [brief section 5, design-rule column]
RULES = dict(clearance=0.2, track=0.2, power_track=0.4, vbat_track=0.5, via_dia=0.7, via_drill=0.3,
             copper_edge=0.5, mask_margin=0.05, min_text=1.0, min_line=0.15)

# ---------------------------------------------------------------------------------------------
# Footprints: pads in the footprint frame (rot 0).  (num, shape, x, y, w, h)
# ---------------------------------------------------------------------------------------------
def fp_2pad(pitch, w, h):
    return [("1", "rect", -pitch / 2, 0, w, h), ("2", "rect", pitch / 2, 0, w, h)]

def sot23(n):  # SOT-23-5/6, pin pitch 0.95, rows +-1.1 (KiCad SOT-23-5/6 land pattern: 1.325 x 0.6 pads at x +-1.1375)
    pads = []
    for i in range(3):
        pads.append((str(i + 1), "rect", -1.1375, (i - 1) * 0.95, 1.325, 0.6))
    if n == 6:
        for i in range(3):
            pads.append((str(6 - i), "rect", 1.1375, (i - 1) * 0.95, 1.325, 0.6))
    else:  # SOT-23-5: pins 4,5 on the right
        pads.append(("5", "rect", 1.1375, -0.95, 1.325, 0.6))
        pads.append(("4", "rect", 1.1375, 0.95, 1.325, 0.6))
    return pads

def dual_row(npins_side, pitch, xrow, w, h):
    pads = []
    for i in range(npins_side):
        y = (i - (npins_side - 1) / 2) * pitch
        pads.append((str(i + 1), "rect", -xrow, y, w, h))
        pads.append((str(2 * npins_side - i), "rect", xrow, y, w, h))
    return pads

FOOT = {}
FOOT["Resistor_SMD:R_0603_1608Metric"] = (fp_2pad(1.65, 0.8, 0.95), (3.2, 1.8), "std")
FOOT["Capacitor_SMD:C_0603_1608Metric"] = FOOT["Resistor_SMD:R_0603_1608Metric"]
FOOT["LED_SMD:LED_0603_1608Metric"] = FOOT["Resistor_SMD:R_0603_1608Metric"]
FOOT["LED_SMD:LED_0805_2012Metric"] = (fp_2pad(1.825, 1.0, 1.45), (3.6, 2.2), "std")
FOOT["Package_TO_SOT_SMD:SOT-23-5"] = (sot23(5), (4.0, 3.2), "std")
FOOT["Package_TO_SOT_SMD:SOT-23-6"] = (sot23(6), (4.0, 3.2), "std")
FOOT["Package_SO:TSSOP-8_4.4x3mm_P0.65mm"] = (dual_row(4, 0.65, 2.85, 1.5, 0.4), (6.2, 3.4), "std")
_soic = [p for p in dual_row(4, 1.27, 2.475, 1.95, 0.6)]
_soic.append(("9", "rect", 0, 0, 2.41, 3.81))
FOOT["Package_SO:SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.41x3.81mm"] = (_soic, (6.4, 5.2), "std")
# PLACEHOLDERS (pad numbers right, geometry NOT from a drawing)
_sw = [("1", "rect", -2.3, -1.4, 1.4, 1.6), ("2", "rect", -2.3, 1.4, 1.4, 1.6), ("3", "rect", 2.3, -1.4, 1.4, 1.6), ("4", "rect", 2.3, 1.4, 1.4, 1.6)]
FOOT["NW:SW_TS-1187A-B-A-B_5.1x5.1"] = (_sw, (6.0, 6.0), "placeholder")
FOOT["NW:AHT20_DFN-6_3x3"] = ([("1", "rect", -1.4, -1.0, 0.7, 0.5), ("2", "rect", -1.4, 0.0, 0.7, 0.5), ("3", "rect", -1.4, 1.0, 0.7, 0.5),
                              ("4", "rect", 1.4, 1.0, 0.7, 0.5), ("5", "rect", 1.4, 0.0, 0.7, 0.5), ("6", "rect", 1.4, -1.0, 0.7, 0.5)], (3.4, 3.4), "placeholder")
FOOT["NW:WSOF-6_BH1750FVI"] = ([("1", "rect", -1.4, -0.95, 0.8, 0.5), ("2", "rect", -1.4, 0.0, 0.8, 0.5), ("3", "rect", -1.4, 0.95, 0.8, 0.5),
                               ("4", "rect", 1.4, 0.95, 0.8, 0.5), ("5", "rect", 1.4, 0.0, 0.8, 0.5), ("6", "rect", 1.4, -0.95, 0.8, 0.5)], (3.8, 3.4), "placeholder")
# J1 USB-C placeholder: mouth toward +x (local), 12 signal pads 0.5 x 1.2 at pitch 0.7, shield pad
_j1 = []
for i, n in enumerate(["A1B12", "A4B9", "B8", "A5", "B7", "A6", "B6", "A7", "A8", "B5", "B4A9", "B1A12"]):
    _j1.append((n, "rect", -2.6, (i - 5.5) * 0.7, 1.2, 0.5))
_j1.append(("S1", "rect", 0.2, 0.0, 1.6, 8.0))
FOOT["Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12"] = (_j1, (7.5, 9.0), "placeholder", (-3.9, 3.6))  # courtyard x range [-3.9, 3.6]: mouth flush with the board edge
# J2 JST PH SMD, mouth toward +x (local); 2 signal pads + 2 mounting pads (approximate)
FOOT["Connector_JST:JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal"] = (
    [("1", "rect", -1.0, -1.0, 3.0, 1.0), ("2", "rect", -1.0, 1.0, 3.0, 1.0), ("MP1", "rect", 0.2, -3.4, 1.6, 3.0), ("MP2", "rect", 0.2, 3.4, 1.6, 3.0)], (6.0, 7.6), "placeholder")
# ESP32-C3-MINI-1: see U1 below (generated)

def u1_pads():
    """PLACEHOLDER module land pattern: the used signal pins in two columns (0.4 x 0.8 [read: pad size], pitch 0.8), GND pads at the bottom
    and a 3 x 6 centre GND grid for pads 36-53.  The real pad coordinates (datasheet Fig 11-1) are NOT drawn here."""
    sig = [p for p in D.PARTS if p.ref == "U1"][0]
    nums = [p[0] for p in sig.pins if p[2] != "GND"]
    left = nums[: (len(nums) + 1) // 2]
    right = nums[(len(nums) + 1) // 2:]
    pads = []
    for i, n in enumerate(left):
        pads.append((n, "rect", -U1_W / 2 + 0.4, U1_PAD_Y0 + i * 0.8, 0.8, 0.4))
    for i, n in enumerate(right):
        pads.append((n, "rect", U1_W / 2 - 0.4, U1_PAD_Y0 + i * 0.8, 0.8, 0.4))
    for i, n in enumerate(["1", "2", "11", "14"]):
        pads.append((n, "rect", -2.4 + i * 1.6, U1_L / 2 - 0.5, 0.4, 0.8))
    k = 36
    for r in range(6):
        for c in range(3):
            pads.append((str(k), "rect", -1.1 + c * 1.1, U1_PAD_Y0 + 0.5 + r * 1.1, 1.0, 1.0))
            k += 1
    return pads
FOOT["RF_Module:ESP32-C3-MINI-1"] = (u1_pads(), (U1_W, U1_L), "placeholder")
# E1: soil electrodes, copper only on F.Cu (no mask opening: covered by solder mask, O5), tail frame, origin = tail top centre
_e1 = [("2", "rect", -4.0, 11.0, 1.5, 20.0), ("1", "rect", 0.0, 11.0, 3.5, 20.0), ("2", "rect", 4.0, 11.0, 1.5, 20.0)]
FOOT["NW:SOIL_PROBE_STAKE"] = (_e1, (TAIL_W, TAIL_L), "electrode", (0, TAIL_L))

# ---------------------------------------------------------------------------------------------
# Placement: ref -> (x, y, rot) board coordinates of the footprint origin.  Zones follow brief O6, rules in the comments.
# ---------------------------------------------------------------------------------------------
PLACE = {
    # O2/O3: module at the top right, antenna end overhanging the board edge, away from the cell, wet-soil end is the opposite end (R-06)
    "U1": (U1_CX, U1_CY, 0),
    # FR-D01 decoupling right at the module 3V3 side (below the module)
    "C5": (22.0, 14.0, 0), "C4": (25.6, 14.0, 0), "C12": (29.2, 14.0, 0),
    "R3": (22.0, 16.2, 0), "R4": (25.6, 16.2, 0), "R5": (29.2, 16.2, 0), "R16": (32.6, 14.0, 90),
    # sensors, top left, >= 10 mm from the TP4056 (O6); BH1750 on the face that sees the light window (Q6 [open])
    "U5": (4.5, 4.5, 0), "C6": (4.5, 8.0, 0),
    "U6": (11.5, 4.5, 0), "C7": (11.5, 8.0, 0),
    "R13": (4.5, 11.0, 0), "R14": (11.5, 11.0, 0),
    # switches: BOOT/RESET reachable with the case open, SW3 pinhole position from Yara (Q6 [open])
    "SW1": (6.0, 17.5, 0), "SW2": (13.5, 17.5, 0), "SW3": (4.5, 23.5, 0),
    # power block (O6): LDO + rail caps in the middle, charger near USB-C
    "U2": (15.5, 25.0, 0), "C3": (15.5, 28.0, 0), "C14": (19.5, 22.5, 0), "C13": (19.5, 24.8, 0),
    "R7": (11.0, 21.5, 0), "R8": (14.6, 21.5, 0), "C11": (11.0, 23.6, 0),
    "U3": (22.0, 31.0, 0), "C1": (27.0, 27.0, 0), "C2": (17.0, 33.0, 0), "R9": (20.8, 36.8, 0),
    "R10": (12.8, 37.6, 0), "R11": (12.8, 39.6, 0), "D2": (8.0, 37.8, 0), "D3": (8.0, 40.2, 0),
    # J1 USB-C: right edge, mouth flush (O4), far from the antenna; ESD D1 and C10 right at it (<= 10 mm)
    "J1": (BOARD_W - 3.6, 33.0, 0), "D1": (24.5, 36.0, 0), "C10": (BOARD_W - 3.6, 26.8, 0), "R1": (27.0, 40.4, 0), "R2": (30.5, 40.4, 0),
    # cell connector at the cell side (left edge, mouth toward the cell), protection next to it
    "J2": (3.6, 31.4, 180), "U4": (10.5, 30.5, 0), "Q1": (10.5, 35.0, 0), "R15": (3.0, 37.6, 0), "C9": (3.0, 39.5, 0),
    # soil front end at the neck of the tail: SOIL_PROBE short (O5/O6)
    "U7": (16.9, 37.6, 0), "R12": (20.5, 40.2, 0), "C8": (16.2, 40.2, 0),
    # tail with the electrodes
    "E1": (BOARD_W / 2, BODY_L, 0),
}
# vias [brief O3 / section 5]: >= 9 on the module ground pad, 4-6 under the TP4056 exposed pad; 0.3 / 0.7 mm
def via_list():
    v = []
    for r in (0, 2, 4, 5):
        for c in range(3):
            v.append(("U1gnd", U1_CX - 1.1 + c * 1.1, U1_CY + U1_PAD_Y0 + 0.5 + r * 1.1))
    ux, uy, _ = PLACE["U3"]
    for dx in (-0.6, 0.6):
        for dy in (-1.0, 1.0):
            v.append(("U3ep", ux + dx, uy + dy))
    return v

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

def footprint_text(p: D.Part):
    spec = FOOT[p.footprint]
    pads, court, kind = spec[0], spec[1], spec[2]
    cx = spec[3] if len(spec) > 3 else None
    x, y, r = PLACE[p.ref]
    pinnet = {}
    for pin in p.pins:
        pinnet[pin[0]] = pin[2]
    L = []
    L.append(f'\t(footprint "{p.footprint}"')
    L.append(f'\t\t(layer "F.Cu")')
    L.append(f'\t\t(uuid "{uid("fp", p.ref)}")')
    L.append(f'\t\t(at {f(x)} {f(y)}{" " + f(r) if r else ""})')
    L.append(f'\t\t(descr "{kind.upper()}: {p.value}")' if kind != "std" else f'\t\t(descr "{p.value}")')
    fx, fy = (0, -(court[1] / 2 + 0.9))
    L.append(f'\t\t(property "Reference" "{p.ref}" (at {f(fx)} {f(fy)} {f(-r % 360 if r else 0)}) (layer "F.Fab") (uuid "{uid("ref", p.ref)}") (effects (font (size 0.8 0.8) (thickness 0.12))))')
    L.append(f'\t\t(property "Value" "{p.value}" (at 0 {f(court[1] / 2 + 0.9)} {f(-r % 360 if r else 0)}) (layer "F.Fab") (hide yes) (uuid "{uid("val", p.ref)}") (effects (font (size 0.8 0.8) (thickness 0.12))))')
    L.append(f'\t\t(property "LCSC" "{p.lcsc}" (at 0 0) (layer "F.Fab") (hide yes) (uuid "{uid("lcsc", p.ref)}") (effects (font (size 0.8 0.8) (thickness 0.12))))')
    L.append(f'\t\t(attr {"smd" if kind != "electrode" else "smd exclude_from_bom exclude_from_pos_files"})')
    x0, x1 = (cx if cx else (-court[0] / 2, court[0] / 2))
    y0, y1 = (-court[1] / 2, court[1] / 2) if not (cx and kind == "electrode") else (0, court[1])
    if kind == "electrode":
        y0, y1 = 0, court[1]
        x0, x1 = -court[0] / 2, court[0] / 2
    L.append(f'\t\t(fp_rect (start {f(x0)} {f(y0)}) (end {f(x1)} {f(y1)}) (stroke (width 0.05) (type default)) (fill no) (layer "F.CrtYd") (uuid "{uid("cy", p.ref)}"))')
    for i, (num, shape, px, py, w, h) in enumerate(pads):
        nm = pinnet.get(num, "NC")
        layers = '"F.Cu"' if kind == "electrode" else '"F.Cu" "F.Mask" "F.Paste"'
        if p.ref == "U1" and num.isdigit() and 36 <= int(num) <= 53:
            layers = '"F.Cu" "F.Mask"'   # centre ground pad: paste windowed later (brief section 5); no paste in this slice
        net = netref(nm) if nm != "NC" else ""
        L.append(f'\t\t(pad "{num}" smd rect (at {f(px)} {f(py)}{" " + f(r) if r else ""}) (size {f(w)} {f(h)}) (layers {layers}) {net} (uuid "{uid("pad", p.ref, i)}"))')
    L.append("\t)")
    return "\n".join(L)

def outline_pts():
    return [(0, 0), (BOARD_W, 0), (BOARD_W, BODY_L), (TAIL_X0 + TAIL_W, BODY_L), (TAIL_X0 + TAIL_W, BODY_L + TAIL_L),
            (TAIL_X0, BODY_L + TAIL_L), (TAIL_X0, BODY_L), (0, BODY_L)]

def build_pcb():
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
    # vias
    n_gnd = NETS["GND"]
    for k, (tag, x, y) in enumerate(via_list()):
        o.append(f'\t(via (at {f(x)} {f(y)}) (size {RULES["via_dia"]}) (drill {RULES["via_drill"]}) (layers "F.Cu" "B.Cu") (net {n_gnd}) (uuid "{uid("via", k)}"))')
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
    open(os.path.join(HERE, "plant-monitor.kicad_pcb"), "w").write(build_pcb())
    update_pro()
    write_dxf()
    print("wrote plant-monitor.kicad_pcb and updated plant-monitor.kicad_pro")

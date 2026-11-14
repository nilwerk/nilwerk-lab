#!/usr/bin/env python3
"""Generates the v1 (function demo) wiring diagram, the perfboard layout and the wire table.

Single source of truth for WIRING.md section 4 and 5 tables and for the two SVGs.
  gen_wiring.py --write   regenerate SVGs and the tables between the BEGIN/END markers in WIRING.md
  gen_wiring.py --check   fail (exit 1) if WIRING.md tables or SVGs differ from this script, or if two
                          different parts claim the same perfboard hole
Pins follow firmware/main/board.h and are not changed here. All dimensions are UNVERIFIED typical values
(see WIRING.md section 6 measure list) until Arsany measured them.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOC = HERE / "WIRING.md"

# ---- perfboard geometry (UNVERIFIED: counted from photo 1.jpg, not measured) -------------------------------
BOARD_W, BOARD_H = 70.0, 50.0          # mm, landscape: x along the 70 mm side
PITCH = 2.54
COLS, ROWS = 24, 18                    # round holes along 70 mm / along 50 mm
X0 = (BOARD_W - (COLS - 1) * PITCH) / 2  # first hole centre, mm from left edge (symmetric assumption)
Y0 = (BOARD_H - (ROWS - 1) * PITCH) / 2


def hx(c):
    return X0 + (c - 1) * PITCH


def hy(r):
    return Y0 + (r - 1) * PITCH


def hole(c, r):
    return "c%d r%d" % (c, r)


# ---- parts with their pin holes ------------------------------------------------------------------------------
SM_TOP = ["GPIO5", "GPIO6", "GPIO7", "GPIO8", "GPIO9", "GPIO10", "GPIO20", "GPIO21"]  # listing 6.webp, right column
SM_BOT = ["5V", "G", "3V3", "GPIO4", "GPIO3", "GPIO2", "GPIO1", "GPIO0"]              # listing 6.webp, left column
PARTS = {}  # name -> (c, r)
for i, n in enumerate(SM_TOP):
    PARTS["SM." + n] = (1 + i, 1)
for i, n in enumerate(SM_BOT):
    PARTS["SM." + n] = (1 + i, 7)
PARTS.update({
    "J1.A": (1, 8), "J1.B": (1, 9),
    "R1.top": (2, 10), "R1.mid": (6, 10),
    "R2.mid": (6, 11), "R2.bot": (10, 11),
    "Rp1.sda": (17, 9), "Rp2.scl": (19, 9),
    "BH.VCC": (15, 1), "BH.GND": (15, 2), "BH.SCL": (15, 3), "BH.SDA": (15, 4), "BH.ADDR": (15, 5),
    "AHT.SDA": (24, 14), "AHT.SCL": (24, 15), "AHT.GND": (24, 16), "AHT.VIN": (24, 17),
    "J3.GND": (14, 18), "J3.VCC": (15, 18), "J3.AOUT": (16, 18),
})
BUS_GND = (10, 24, 11)   # bare tinned wire along row 11, cols 10..24
BUS_3V3 = (11, 24, 10)   # bare tinned wire along row 10, cols 11..24
# Rp leads that sit on the 3V3 bus: (17,10) and (19,10)

# ---- wire list: id, from, to, colour, where, net / note -----------------------------------------------------
# from/to are either part pins (key of PARTS, shown with their hole) or free text for flying-lead ends.
W = [
    ("W01", "SM.5V", "J1.A", "red", "perfboard", "5V_IN: SuperMini 5V pin to jumper J1 pin A (1-hole link)"),
    ("W02", "J1.B", "R1.top", "red", "perfboard", "VBAT: jumper J1 pin B to the divider top (VBAT node, hole c2 r10)"),
    ("W03", "TP.OUT+", "R1.top", "red", "flying lead", "VBAT: TP4056 OUT+ pad (protected side) to VBAT node c2 r10"),
    ("W04", "TP.OUT-", "BUS_GND c12 r11", "black", "flying lead", "GND: TP4056 OUT- pad to the GND bus"),
    ("W05", "SM.G", "BUS_GND c11 r11", "black", "perfboard", "GND: SuperMini G pin to the GND bus"),
    ("W06", "SM.3V3", "BUS_3V3 c11 r10", "orange", "perfboard", "3V3: SuperMini 3V3 pin to the 3V3 bus"),
    ("W07", "BH.VCC", "BUS_3V3 c15 r10", "orange", "perfboard", "3V3: BH1750 VCC to the 3V3 bus"),
    ("W08", "BH.GND", "BUS_GND c16 r11", "black", "perfboard", "GND: BH1750 GND to the GND bus (insulated wire crosses the 3V3 bus)"),
    ("W09", "BH.ADDR", "BH.GND", "black", "perfboard", "GND: BH1750 ADDR tied low = address 0x23"),
    ("W10", "AHT.VIN", "BUS_3V3 c23 r10", "orange", "perfboard", "3V3: AHT20 VIN to the 3V3 bus (insulated wire crosses the GND bus)"),
    ("W11", "AHT.GND", "BUS_GND c22 r11", "black", "perfboard", "GND: AHT20 GND to the GND bus"),
    ("W12", "J3.GND", "BUS_GND c13 r11", "black", "perfboard", "GND: soil sensor connector J3 GND to the GND bus"),
    ("W13", "SM.GPIO6", "Rp1.sda", "blue", "perfboard", "I2C_SDA (board.h NW_PIN_I2C_SDA = 6): GPIO6 to SDA node c17 r9"),
    ("W14", "Rp1.sda", "BH.SDA", "blue", "perfboard", "I2C_SDA: SDA node to BH1750 SDA"),
    ("W15", "Rp1.sda", "AHT.SDA", "blue", "perfboard", "I2C_SDA: SDA node to AHT20 SDA"),
    ("W16", "SM.GPIO7", "Rp2.scl", "green", "perfboard", "I2C_SCL (board.h NW_PIN_I2C_SCL = 7): GPIO7 to SCL node c19 r9"),
    ("W17", "Rp2.scl", "BH.SCL", "green", "perfboard", "I2C_SCL: SCL node to BH1750 SCL"),
    ("W18", "Rp2.scl", "AHT.SCL", "green", "perfboard", "I2C_SCL: SCL node to AHT20 SCL"),
    ("W19", "SM.GPIO0", "R1.mid", "grey", "perfboard", "BAT_SENS (NW_PIN_BAT_SENS = 0, ADC1_CH0): divider midpoint to GPIO0"),
    ("W20", "SM.GPIO3", "J3.VCC", "purple", "perfboard", "SOIL_PWR (NW_PIN_SOIL_PWR = 3): GPIO3 switches the soil sensor VCC"),
    ("W21", "SM.GPIO4", "J3.AOUT", "yellow", "perfboard", "SOIL_OUT (NW_PIN_SOIL_OUT = 4, ADC1_CH4): soil AOUT to GPIO4"),
    ("W22", "LiPo+ via J_BAT (red)", "TP.B+", "red", "flying lead", "BATT+: JST-PH pigtail red to TP4056 B+ pad (polarity: section 2.5, A-091)"),
    ("W23", "LiPo- via J_BAT (black)", "TP.B-", "black", "flying lead", "BATT-: JST-PH pigtail black to TP4056 B- pad"),
]
# Passive parts on the board (not wires): id, part, leads (holes), note
PASSIVES = [
    ("R1", "100 kOhm 1 %", "c2 r10 to c6 r10", "battery divider top (VBAT to midpoint); matches board.h dev-kit value 100000"),
    ("R2", "100 kOhm 1 %", "c6 r11 to c10 r11", "battery divider bottom (midpoint to GND bus); link c6 r10 - c6 r11 joins R1/R2 midpoint"),
    ("Rp1", "4.7 kOhm (only if needed)", "c17 r9 to c17 r10 (bus)", "SDA pull-up to 3V3, standing; fit ONLY if neither breakout has one"),
    ("Rp2", "4.7 kOhm (only if needed)", "c19 r9 to c19 r10 (bus)", "SCL pull-up to 3V3, standing; fit ONLY if neither breakout has one"),
    ("C1", "100 nF ceramic (optional)", "midpoint c6 r10 to GND c10 r11", "ADC filter on solder side, parallel to R2 (source impedance 50 kOhm)"),
    ("J1", "2-pin header + jumper", "c1 r8 / c1 r9", "programming disconnect in the 5V feed: OPEN to flash over USB-C"),
    ("J3", "3-pin male header", "c14/c15/c16 r18", "soil sensor Dupont plug: GND, VCC (from GPIO3), AOUT"),
]


def pin_text(p):
    if p in PARTS:
        c, r = PARTS[p]
        return "%s (%s)" % (p, hole(c, r))
    return p


def wire_table():
    rows = ["| ID | From | To | Colour | Where | Net / purpose |", "|---|---|---|---|---|---|"]
    for wid, a, b, col, where, note in W:
        rows.append("| %s | %s | %s | %s | %s | %s |" % (wid, pin_text(a), pin_text(b), col, where, note))
    return "\n".join(rows)


def passive_table():
    rows = ["| Ref | Value | Holes | Role |", "|---|---|---|---|"]
    for ref, val, holes, note in PASSIVES:
        rows.append("| %s | %s | %s | %s |" % (ref, val, holes, note))
    return "\n".join(rows)


def pin_table():
    rows = ["| SuperMini pin | Hole | Signal | board.h macro | Use in v1 |", "|---|---|---|---|---|"]
    use = {
        "SM.GPIO0": ("BAT_SENS", "NW_PIN_BAT_SENS", "divider midpoint (ADC1_CH0)"),
        "SM.GPIO3": ("SOIL_PWR", "NW_PIN_SOIL_PWR", "soil VCC switch, LOW in deep sleep"),
        "SM.GPIO4": ("SOIL_OUT", "NW_PIN_SOIL_OUT", "soil AOUT (ADC1_CH4)"),
        "SM.GPIO6": ("I2C_SDA", "NW_PIN_I2C_SDA", "BH1750 + AHT20"),
        "SM.GPIO7": ("I2C_SCL", "NW_PIN_I2C_SCL", "BH1750 + AHT20"),
        "SM.GPIO9": ("BOOT_N", "NW_PIN_BUTTON", "on-board BOOT key, nothing wired"),
        "SM.5V": ("5V_IN", "-", "from J1 (battery OUT+ via jumper)"),
        "SM.G": ("GND", "-", "GND bus"),
        "SM.3V3": ("3V3", "-", "sensor supply"),
    }
    for n in SM_BOT + SM_TOP:
        k = "SM." + n
        if k in use:
            s, m, u = use[k]
            rows.append("| %s | %s | %s | %s | %s |" % (n, hole(*PARTS[k]), s, m, u))
    return "\n".join(rows)


# ---- svg helpers -----------------------------------------------------------------------------------------------
COL = {"red": "#d62728", "black": "#222222", "orange": "#e07b00", "blue": "#1f5fbf", "green": "#2a9d3f",
       "grey": "#808080", "purple": "#7b3fb5", "yellow": "#d4a900"}
FONT = 'font-family="DejaVu Sans, Arial, Helvetica, sans-serif"'


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def T(x, y, s, size=11, anchor="start", fill="#111", weight="normal"):
    return '<text x="%.1f" y="%.1f" font-size="%d" text-anchor="%s" fill="%s" font-weight="%s" %s>%s</text>' % (
        x, y, size, anchor, fill, weight, FONT, esc(s))


def R(x, y, w, h, fill, stroke="#333", sw=1.2, rx=3, extra=""):
    return '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%d" fill="%s" stroke="%s" stroke-width="%.1f" %s/>' % (
        x, y, w, h, rx, fill, stroke, sw, extra)


def L(x1, y1, x2, y2, color, sw=2, dash=""):
    d = ' stroke-dasharray="%s"' % dash if dash else ""
    return '<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="%.1f"%s/>' % (x1, y1, x2, y2, color, sw, d)


def svg_wrap(w, h, body, title):
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d">\n'
            '<title>%s</title>\n<rect width="%d" height="%d" fill="#ffffff"/>\n%s\n</svg>\n') % (
        w, h, w, h, esc(title), w, h, body)


# ---- diagram 1: wiring (block level, net flags) ---------------------------------------------------------------
def wiring_svg():
    b = []
    P = lambda cx, cy, c, r=6: '<circle cx="%d" cy="%d" r="%d" fill="%s" stroke="#222"/>' % (cx, cy, r, c)
    b.append(T(20, 28, "Plant Monitor v1 function demo - wiring (top view, schematic style, not to scale)", 17, weight="bold"))
    b.append(T(20, 48, "Same colour or same net tag = same wire. Pins per firmware/main/board.h. Never plug both USB-C ports; open J1 before USB-C on the SuperMini.", 11, fill="#444"))
    # battery chain
    b.append(R(20, 90, 120, 60, "#fff3cd"))
    b.append(T(80, 115, "LiPo 1S cell", 13, "middle", weight="bold"))
    b.append(T(80, 133, "A-091 answered; still check", 10, "middle", fill="#a00"))
    b.append(R(170, 100, 70, 40, "#ffffff", rx=4))
    b.append(T(205, 118, "J_BAT", 11, "middle", weight="bold"))
    b.append(T(205, 132, "JST-PH 2p", 10, "middle"))
    b.append(L(140, 112, 170, 112, COL["red"], 3))
    b.append(L(140, 138, 170, 138, COL["black"], 3))
    # tp4056
    b.append(R(290, 70, 230, 250, "#cfe3ff"))
    b.append(T(405, 92, "TP4056 USB-C module (protected?)", 12, "middle", weight="bold"))
    b.append(T(405, 108, "3 ICs in photo, UNVERIFIED", 10, "middle", fill="#555"))
    b.append(R(430, 120, 80, 28, "#e8e8e8"))
    b.append(T(470, 138, "USB-C (charge)", 10, "middle"))
    for name, y, c in [("B+", 160, "red"), ("B-", 195, "black"), ("OUT+", 240, "red"), ("OUT-", 285, "black")]:
        b.append(P(290, y, COL[c]))
        b.append(T(302, y + 4, name, 11, weight="bold"))
    b.append(L(240, 112, 290, 160, COL["red"], 3))
    b.append(L(240, 138, 290, 195, COL["black"], 3))
    b.append(T(250, 175, "W22", 9, fill="#444"))
    b.append(T(250, 212, "W23", 9, fill="#444"))
    b.append(T(300, 312, "OUT = protected side: the load connects only here", 10, fill="#444"))
    # VBAT path: OUT+ -> node -> J1 -> 5V, divider tap
    b.append(L(290, 240, 270, 240, COL["red"], 3))
    b.append(L(270, 240, 270, 360, COL["red"], 3))
    b.append(T(120, 356, "VBAT node (c2 r10)", 10, fill=COL["red"], weight="bold"))
    b.append(T(120, 270, "W03", 9, fill="#444"))
    b.append(L(270, 360, 590, 360, COL["red"], 3))
    b.append(L(590, 360, 590, 182, COL["red"], 3))
    b.append(T(598, 290, "W02", 9, fill="#444"))
    b.append(R(540, 140, 100, 42, "#fff3cd", rx=4))
    b.append(T(590, 158, "J1 jumper", 11, "middle", weight="bold"))
    b.append(T(590, 173, "OPEN to flash", 10, "middle", fill="#a00"))
    b.append(L(640, 160, 700, 160, COL["red"], 3))
    b.append(T(648, 150, "W01", 9, fill="#444"))
    # divider
    b.append(R(300, 385, 70, 28, "#ffffff", rx=2))
    b.append(T(335, 404, "R1 100k", 11, "middle"))
    b.append(L(335, 360, 335, 385, COL["red"], 2.5))
    b.append(R(300, 440, 70, 28, "#ffffff", rx=2))
    b.append(T(335, 459, "R2 100k", 11, "middle"))
    b.append(L(335, 413, 335, 440, COL["grey"], 2.5))
    b.append(P(335, 426, COL["grey"], 4))
    b.append(L(335, 426, 600, 426, COL["grey"], 2.5, "6 4"))
    b.append(T(420, 418, "BAT_SENS (W19): midpoint to GPIO0", 11, fill="#555", weight="bold"))
    b.append(T(380, 462, "optional C1 100 nF across R2", 10, fill="#555"))
    b.append(L(600, 426, 600, 510, COL["grey"], 2.5, "6 4"))
    b.append(L(600, 510, 700, 510, COL["grey"], 2.5, "6 4"))
    # gnd
    b.append(L(335, 468, 335, 520, COL["black"], 3))
    b.append(L(290, 285, 250, 285, COL["black"], 3))
    b.append(T(120, 289, "OUT- = GND (W04)", 11, weight="bold"))
    b.append(L(250, 285, 250, 520, COL["black"], 3))
    b.append(L(250, 520, 640, 520, COL["black"], 3))
    b.append(T(450, 538, "GND bus (row 11)", 10, "middle", fill="#444"))
    b.append(L(640, 520, 640, 210, COL["black"], 3))
    b.append(L(640, 210, 700, 210, COL["black"], 3))
    # SuperMini
    b.append(R(700, 60, 300, 520, "#d9f2d9"))
    b.append(T(850, 84, "DUBEUYEW ESP32-C3 SuperMini", 13, "middle", weight="bold"))
    b.append(T(850, 100, "USB-C (program) at top, antenna at bottom end", 10, "middle", fill="#555"))
    b.append(R(790, 108, 120, 24, "#e8e8e8"))
    b.append(T(850, 125, "USB-C (data)", 10, "middle"))
    left = [("5V", "5V_IN from J1", "red"), ("G", "GND", "black"), ("3V3", "3V3 -> tag 3V3", "orange"),
            ("GPIO4", "SOIL_OUT", "yellow"), ("GPIO3", "SOIL_PWR", "purple"),
            ("GPIO2", "unused (strap)", None), ("GPIO1", "unused", None), ("GPIO0", "BAT_SENS", "grey")]
    right = [("GPIO5", "unused", None), ("GPIO6", "I2C_SDA", "blue"), ("GPIO7", "I2C_SCL", "green"),
             ("GPIO8", "LED / strap, unused", None), ("GPIO9", "BOOT key = BUTTON", None),
             ("GPIO10", "unused", None), ("GPIO20", "unused", None), ("GPIO21", "unused", None)]
    ys = [160 + i * 50 for i in range(8)]
    for (pin, lab, c), y in zip(left, ys):
        b.append(P(700, y, COL[c] if c else "#ffffff"))
        b.append(T(712, y + 4, pin, 11, weight="bold"))
        b.append(T(762, y + 4, lab, 10, fill="#555"))
    for (pin, lab, c), y in zip(right, ys):
        b.append(P(1000, y, COL[c] if c else "#ffffff"))
        b.append(T(988, y + 4, pin, 11, "end", weight="bold"))
        b.append(T(1012, y + 4, lab, 10, fill=COL[c] if c else "#777"))
    b.append(T(940, 220, "", 9))
    # soil
    b.append(R(20, 610, 330, 200, "#eeeeee"))
    b.append(T(185, 632, "Capacitive soil moisture sensor v1.2", 12, "middle", weight="bold"))
    b.append(T(185, 648, "JST-PH 3p to Dupont 3p cable", 10, "middle", fill="#555"))
    for i, (n, c, lab) in enumerate([("GND", "black", "J3 GND (W12)"), ("VCC", "purple", "J3 VCC <- GPIO3 (W20)"),
                                     ("AOUT", "yellow", "J3 AOUT -> GPIO4 (W21)")]):
        y = 690 + i * 36
        b.append(P(350, y, COL[c]))
        b.append(T(338, y + 4, n, 11, "end", weight="bold"))
        b.append(T(40, y + 4, lab, 11, fill=COL[c] if c != "yellow" else "#a08000"))
    b.append(T(185, 800, "plug wire colours UNVERIFIED: confirm by continuity", 10, "middle", fill="#a00"))
    b.append(L(350, 690, 640, 690, COL["black"], 2.5))
    b.append(L(640, 520, 640, 690, COL["black"], 3))
    b.append(L(350, 726, 600, 726, COL["purple"], 2.5))
    b.append(L(600, 726, 600, 640, COL["purple"], 2.5))
    b.append(L(600, 640, 662, 640, COL["purple"], 2.5))
    b.append(L(662, 640, 662, ys[4], COL["purple"], 2.5))
    b.append(L(662, ys[4], 700, ys[4], COL["purple"], 2.5))
    b.append(L(350, 762, 680, 762, COL["yellow"], 2.5))
    b.append(L(680, 762, 680, ys[3], COL["yellow"], 2.5))
    b.append(L(680, ys[3], 700, ys[3], COL["yellow"], 2.5))
    # sensors on the right
    b.append(R(1220, 150, 200, 150, "#e6ddf5"))
    b.append(T(1320, 172, "BH1750 (GY-302)", 12, "middle", weight="bold"))
    b.append(T(1320, 187, "0x23, ADDR to GND", 10, "middle", fill="#555"))
    bh = [("VCC", "orange"), ("GND", "black"), ("SCL", "green"), ("SDA", "blue"), ("ADDR", "black")]
    byy = {}
    for i, (n, c) in enumerate(bh):
        y = 208 + i * 18
        byy[n] = y
        b.append(P(1220, y, COL[c], 4))
        b.append(T(1230, y + 4, n, 10))
    b.append(T(1320, 296, "pin order UNVERIFIED: read the silk", 9, "middle", fill="#a00"))
    b.append(R(1220, 340, 200, 110, "#e6ddf5"))
    b.append(T(1320, 362, "AHT20", 12, "middle", weight="bold"))
    b.append(T(1320, 377, "0x38; same nets as BH1750", 10, "middle", fill="#555"))
    for i, (n, c) in enumerate([("SDA", "blue"), ("SCL", "green"), ("GND", "black"), ("VIN", "orange")]):
        y = 392 + i * 15
        b.append(P(1220, y, COL[c], 4))
        b.append(T(1230, y + 4, n, 10))
    # I2C from the SuperMini to the BH1750 (AHT20 and pull-ups share the nets, see tags)
    b.append(L(1000, ys[1], 1180, ys[1], COL["blue"], 2.5))
    b.append(L(1180, ys[1], 1180, byy["SDA"], COL["blue"], 2.5))
    b.append(L(1180, byy["SDA"], 1220, byy["SDA"], COL["blue"], 2.5))
    b.append(L(1000, ys[2], 1150, ys[2], COL["green"], 2.5))
    b.append(L(1150, ys[2], 1150, byy["SCL"], COL["green"], 2.5))
    b.append(L(1150, byy["SCL"], 1220, byy["SCL"], COL["green"], 2.5))
    # net tags
    b.append(T(1060, 500, "Net tags (same tag = same wire; routed on the board, see wire table):", 11, weight="bold"))
    tags = [("3V3", "orange", "SuperMini 3V3 -> BH1750 VCC, AHT20 VIN, Rp1, Rp2 (W06, W07, W10)"),
            ("GND", "black", "OUT-, SuperMini G -> BH1750 GND + ADDR, AHT20 GND, J3 GND (W04..W12)"),
            ("SDA", "blue", "GPIO6 -> Rp1 -> BH1750 SDA, AHT20 SDA (W13..W15)"),
            ("SCL", "green", "GPIO7 -> Rp2 -> BH1750 SCL, AHT20 SCL (W16..W18)")]
    for i, (n, c, t) in enumerate(tags):
        y = 525 + i * 24
        b.append(R(1060, y - 12, 44, 18, COL[c], stroke=COL[c], rx=3))
        b.append(T(1082, y + 1, n, 10, "middle", fill="#ffffff", weight="bold"))
        b.append(T(1112, y + 1, t, 10))
    b.append(T(1060, 640, "Pull-ups Rp1/Rp2 4.7k to 3V3: fit only if the breakouts have none (4.3).", 10, fill="#555"))
    return svg_wrap(1600, 840, "\n".join(b), "Plant Monitor v1 wiring diagram")


# ---- diagram 2: perfboard layout (to scale) -------------------------------------------------------------------
def layout_svg():
    S = 12.0
    OX, OY = 70.0, 76.0
    b = []

    def X(mm):
        return OX + mm * S

    def Y(mm):
        return OY + mm * S

    b.append(T(20, 26, "Plant Monitor v1 - perfboard layout 70 x 50 mm, top view (component side), to scale", 16, weight="bold"))
    b.append(T(20, 44, "Perfboard, TP4056, BH1750, AHT20 L x W measured by Arsany (A-093); SuperMini and all heights UNVERIFIED typical. Hole grid c1..c24 / r1..r18 counted from a photo.", 10, fill="#444"))
    b.append(R(X(0), Y(0), BOARD_W * S, BOARD_H * S, "#2f8f4e", stroke="#123", sw=2, rx=6))
    # edge oval pads
    for side in (2.9, BOARD_W - 2.9):
        for r in range(1, ROWS + 1):
            b.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="4" fill="#d8d8d8" opacity="0.55"/>' % (
                X(side) - 14, Y(hy(r)) - 7, 28, 14))
    # holes
    for c in range(1, COLS + 1):
        for r in range(1, ROWS + 1):
            b.append('<circle cx="%.1f" cy="%.1f" r="2.4" fill="#f5f5f5" opacity="0.9"/>' % (X(hx(c)), Y(hy(r))))
    # rulers
    for c in range(1, COLS + 1):
        b.append(T(X(hx(c)), OY - 8, str(c), 9, "middle", fill="#333"))
    for r in range(1, ROWS + 1):
        b.append(T(OX - 10, Y(hy(r)) + 3, str(r), 9, "end", fill="#333"))
    b.append(T(X(BOARD_W / 2), OY - 24, "column c (x, 2.54 mm pitch)", 10, "middle", fill="#333"))
    # antenna keep-out
    b.append('<defs><pattern id="ko" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
             '<line x1="0" y1="0" x2="0" y2="8" stroke="#c00" stroke-width="2"/></pattern></defs>')
    b.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="url(#ko)" opacity="0.45" stroke="#c00" stroke-width="2" stroke-dasharray="6 4"/>' % (
        X(27.0), Y(0), 13.0 * S, 22.0 * S))
    b.append(T(X(33.5), Y(11), "ANTENNA", 11, "middle", fill="#900", weight="bold"))
    b.append(T(X(33.5), Y(11) + 14, "KEEP-OUT", 11, "middle", fill="#900", weight="bold"))
    b.append(T(X(33.5), Y(11) + 28, "x 27..40, y 0..22", 9, "middle", fill="#900"))
    # SuperMini
    b.append(R(X(4.5), Y(2.0), 22.5 * S, 18.0 * S, "#1c1c1c", stroke="#000", rx=3))
    b.append(R(X(2.2), Y(11.0 - 4.5), 3.3 * S, 9.0 * S, "#bbbbbb", rx=2))
    b.append(T(X(3.9), Y(11.4), "USB-C", 9, "middle", fill="#000"))
    b.append(T(X(17.0), Y(11.0), "SuperMini 22.5 x 18 typ.", 11, "middle", fill="#fff", weight="bold"))
    b.append(T(X(17.5), Y(11.0) + 14, "component side up, USB-C left", 9, "middle", fill="#ddd"))
    b.append(T(X(24.6), Y(14.5), "antenna", 9, "middle", fill="#ffb0b0"))
    b.append(R(X(8.0), Y(7.2), 2.4 * S, 2.4 * S, "#888", rx=2))
    b.append(T(X(9.2), Y(10.9), "RESET", 8, "middle", fill="#fff"))
    b.append(R(X(8.0), Y(12.2), 2.4 * S, 2.4 * S, "#888", rx=2))
    b.append(T(X(9.2), Y(15.9), "BOOT", 8, "middle", fill="#fff"))
    for k, p in PARTS.items():
        if k.startswith("SM."):
            c, r = p
            b.append('<circle cx="%.1f" cy="%.1f" r="3.4" fill="#e8c35a" stroke="#000"/>' % (X(hx(c)), Y(hy(r))))
    for i, n in enumerate(SM_TOP):
        b.append(T(X(hx(1 + i)), Y(hy(1)) + 16, n.replace("GPIO", "IO"), 8, "middle", fill="#fff"))
    for i, n in enumerate(SM_BOT):
        b.append(T(X(hx(1 + i)), Y(hy(7)) - 8, n.replace("GPIO", "IO"), 8, "middle", fill="#fff"))
    # TP4056
    b.append(R(X(0), Y(33.0), 28.0 * S, 17.0 * S, "#1f4fa8", stroke="#000", rx=3))
    b.append(R(X(-0.6), Y(41.5 - 4.5), 3.3 * S, 9.0 * S, "#bbbbbb", rx=2))
    b.append(T(X(1.6), Y(41.8), "USB-C", 9, "middle", fill="#000"))
    b.append(T(X(15.5), Y(41.0), "TP4056 28 x 17", 11, "middle", fill="#fff", weight="bold"))
    b.append(T(X(15.5), Y(41.0) + 14, "flat on Kapton + tape, LEDs up", 9, "middle", fill="#dde"))
    for i, (n, yy) in enumerate([("OUT+", 35.5), ("B+", 39.0), ("B-", 43.0), ("OUT-", 47.0)]):
        b.append('<circle cx="%.1f" cy="%.1f" r="4" fill="#e8c35a" stroke="#000"/>' % (X(26.3), Y(yy)))
        b.append(T(X(25.4), Y(yy) + 3, n, 8, "end", fill="#fff", weight="bold"))
    b.append(T(X(13.5), Y(52.2), "pad order UNVERIFIED (rotated 180 deg from photo 2): read the silk", 9, "middle", fill="#fff"))
    # BH1750
    b.append(R(X(40.1), Y(1.3), 17.0 * S, 14.0 * S, "#2a4fb5", stroke="#000", rx=3))
    b.append(T(X(49.2), Y(8.5), "BH1750 17 x 14", 11, "middle", fill="#fff", weight="bold"))
    b.append(T(X(49.2), Y(8.5) + 14, "sensor faces up: light window", 9, "middle", fill="#dde"))
    # AHT20
    b.append(R(X(49.5), Y(35.2), 15.0 * S, 10.0 * S, "#1f9d55", stroke="#000", rx=3))
    b.append(T(X(55.0), Y(40.0), "AHT20 15 x 10", 11, "middle", fill="#fff", weight="bold"))
    b.append(T(X(55.0), Y(40.0) + 14, "air / vent side", 9, "middle", fill="#eef"))
    # labelled pins of passives and connectors
    pins = {k: v for k, v in PARTS.items() if not k.startswith("SM.")}
    for k, (c, r) in pins.items():
        b.append('<circle cx="%.1f" cy="%.1f" r="3.4" fill="#e8c35a" stroke="#000"/>' % (X(hx(c)), Y(hy(r))))
    lab = {"J1.A": "J1A", "J1.B": "J1B", "R1.top": "VBAT", "R1.mid": "M", "R2.mid": "", "R2.bot": "",
           "Rp1.sda": "SDA", "Rp2.scl": "SCL", "J3.GND": "GND", "J3.VCC": "VCC", "J3.AOUT": "AOUT",
           "BH.VCC": "VCC", "BH.GND": "GND", "BH.SCL": "SCL", "BH.SDA": "SDA", "BH.ADDR": "ADDR",
           "AHT.SDA": "SDA", "AHT.SCL": "SCL", "AHT.GND": "GND", "AHT.VIN": "VIN"}
    for k, t in lab.items():
        c, r = PARTS[k]
        if t:
            side = -1 if k.startswith(("BH.", "AHT.")) else 1
            b.append(T(X(hx(c)) + side * 7, Y(hy(r)) + 3, t, 8, "end" if side < 0 else "start", fill="#fff" if k.startswith(("BH.", "AHT.")) else "#fff"))
    # resistors
    b.append(R(X(hx(2)), Y(hy(10)) - 5, 4 * PITCH * S, 10, "#c9a46b", stroke="#000", rx=3))
    b.append(T(X(hx(4)), Y(hy(10)) - 8, "R1 100k", 9, "middle", fill="#fff"))
    b.append(R(X(hx(6)), Y(hy(11)) - 5, 4 * PITCH * S, 10, "#c9a46b", stroke="#000", rx=3))
    b.append(T(X(hx(8)), Y(hy(11)) + 17, "R2 100k", 9, "middle", fill="#fff"))
    # buses
    b.append(L(X(hx(10)), Y(hy(11)), X(hx(24)), Y(hy(11)), "#222", 3))
    b.append(T(X(hx(24)) + 6, Y(hy(11)) + 3, "GND bus", 9, fill="#fff"))
    b.append(L(X(hx(11)), Y(hy(10)), X(hx(24)), Y(hy(10)), "#e07b00", 3))
    b.append(T(X(hx(24)) + 6, Y(hy(10)) + 3, "3V3 bus", 9, fill="#fff"))
    b.append(R(X(hx(14)) - 4, Y(hy(18)) - 4, 2 * PITCH * S + 8, 8, "#f5f5f5", stroke="#000", rx=2))
    b.append(T(X(hx(15)), Y(hy(18)) - 8, "J3 soil sensor plug (bottom edge)", 9, "middle", fill="#fff"))
    # heat note
    b.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="none" stroke="#ff8" stroke-width="1.5" stroke-dasharray="5 4"/>' % (X(0), Y(30.0), 30 * S, 20 * S))
    b.append(T(X(15), Y(31.6), "hot zone (TP4056 charging, UNVERIFIED)", 9, "middle", fill="#ff8"))
    # dimension labels
    b.append(T(X(35), Y(BOARD_H) + 24, "70 mm", 11, "middle"))
    b.append(T(OX + BOARD_W * S + 28, Y(25), "50 mm", 11, "middle"))
    # legend
    ly = Y(BOARD_H) + 52
    b.append(T(20, ly, "Legend: yellow dot = hole used. Red hatched box = antenna keep-out: no wire, part, metal, battery or screw in it. Wires run on the solder side (not drawn, see table).", 10))
    b.append(T(20, ly + 16, "Left short edge carries both USB-C ports (SuperMini y 11 mm, TP4056 y 41.5 mm, both UNVERIFIED). BOOT/RESET keys are behind the SuperMini USB-C end (need a pin-hole access).", 10))
    b.append(T(20, ly + 32, "Oval pads along both 50 mm edges are exposed copper: put Kapton under anything that overhangs them (TP4056, SuperMini USB-C).", 10))
    return svg_wrap(int(OX + BOARD_W * S + 90), int(ly + 52), "\n".join(b), "Plant Monitor v1 perfboard layout")


def collisions():
    seen = {}
    bad = []
    for k, p in PARTS.items():
        if p in seen:
            bad.append((k, seen[p]))
        seen[p] = k
    return bad


def tables_block():
    return {"wires": wire_table(), "passives": passive_table(), "pins": pin_table()}


def replace_block(text, name, body):
    pat = re.compile(r"(<!-- BEGIN:%s -->\n).*?(<!-- END:%s -->)" % (name, name), re.S)
    if not pat.search(text):
        raise SystemExit("marker %s missing in WIRING.md" % name)
    return pat.sub(lambda m: m.group(1) + body + "\n" + m.group(2), text)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--check"
    bad = collisions()
    if bad:
        print("hole collisions:", bad)
        return 1
    outputs = {"wiring-diagram.svg": wiring_svg(), "perfboard-layout.svg": layout_svg()}
    doc = DOC.read_text(encoding="utf-8")
    new = doc
    for n, body in tables_block().items():
        new = replace_block(new, n, body)
    if mode == "--write":
        for fn, s in outputs.items():
            (HERE / fn).write_text(s, encoding="utf-8")
        DOC.write_text(new, encoding="utf-8")
        print("written")
        return 0
    ok = new == doc
    for fn, s in outputs.items():
        p = HERE / fn
        ok = ok and p.exists() and p.read_text(encoding="utf-8") == s
    print("OK" if ok else "DRIFT: run gen_wiring.py --write")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

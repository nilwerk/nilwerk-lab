"""Enclosure v1 DEMO housing (4.E5) parameters. All mm. Single source of truth.
Housing for the v1 function demo: 70 x 50 mm perfboard (NOT the custom PCB, NOT enclosure v3 / 4.E3, which is stopped).
Frame: CAD X right, Y up, Z up from the underside of the tray floor. Perfboard lower-left corner = (0, 0), so a
WIRING.md hole/doc position (x, y_doc) (origin top left, y down) maps to CAD (x, BOARD_W_Y - y_doc) via cy().
Status tags: MEASURED (Arsany, bare L x W x T), BRIEF (task brief / repo input, no datasheet read), WIRING (Emil's typical value in
projects/plant-monitor/v1/WIRING.md, UNVERIFIED), ASSUMED (my assumption with the stated margin), RULE (team standard).
ASSUMED / WIRING / BRIEF values never produce a PASS row in fit_check_v1.py."""
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
MECH = os.path.dirname(HERE)
sys.path.insert(0, MECH)
import bay  # existing bay study: cell envelope from A-020 (docs/interfaces/pcb-enclosure-bay.md)

# ---- manufacturing [RULE: standards/3d-manufacturing.md] ----
BUILD = (256.0, 256.0, 256.0)     # Bambu Lab P1S
NOZZLE, LINE_W, LAYER = 0.4, 0.42, 0.2
WALL, FLOOR, LID_T = 1.6, 1.6, 1.6          # >= 1.2 rule; 1.6 = 4 perimeters
MIN_WALL = 1.2
FIT = 0.4                                   # sliding fit per side, standard range 0.2-0.4 (printer not calibrated yet: OPEN)

# ---- perfboard [MEASURED by Arsany: 70 x 50 x 2] ----
PB_L, PB_W, PB_T = 70.0, 50.0, 2.0
# Component bodies on the board, WIRING.md section 5 (doc frame: x right, y DOWN from the top edge, component side up).
# (x0, y0, x1, y1, height above perfboard top, status). Footprints of TP4056/BH1750/AHT20 are MEASURED, positions are Emil's layout plan
# (grid count UNVERIFIED), SuperMini size is UNVERIFIED, heights are typical values (UNVERIFIED) from WIRING.md.
PARTS = {
    "SuperMini": (4.5, 2.0, 27.0, 20.0, 6.8, "WIRING"),      # 22.5 x 18 UNVERIFIED; top = USB-C 2.5 header + 1.0 PCB + 3.3
    "TP4056":    (0.0, 33.0, 28.0, 50.0, 5.6, "WIRING"),     # 28 x 17 MEASURED; height 0.3 Kapton + 2.0 + 3.3 UNVERIFIED
    "BH1750":    (40.0, 1.3, 57.0, 15.3, 5.7, "WIRING"),     # 17 x 14 MEASURED; height UNVERIFIED
    "AHT20":     (49.5, 35.0, 64.5, 45.0, 5.5, "WIRING"),    # 15 x 10 MEASURED; height UNVERIFIED
    "J1":        (4.5, 19.9, 7.1, 25.0, 12.0, "WIRING"),     # 2-pin header + jumper shunt, tallest item (about 12)
    "J3":        (37.5, 45.0, 45.2, 48.2, 12.0, "WIRING"),   # 3-pin header + Dupont plug (about 12)
    "R1R2":      (8.3, 25.3, 30.0, 29.8, 7.0, "WIRING"),     # standing resistors
    "Rp":        (45.9, 22.7, 52.0, 27.2, 7.0, "WIRING"),    # pull-ups, only if needed
}
ANT_KEEPOUT_DOC = (27.0, 0.0, 40.0, 22.0)    # WIRING.md: antenna zone x 27-40, y 0-22 (doc frame); no metal/wire/part/cell/screw
ANT_END_DOC = (27.0, 2.0, 27.0, 20.0)        # SuperMini antenna end edge
ANT_MARGIN = 10.0                            # 'about 10+ mm beyond the antenna end' [WIRING, common practice, UNVERIFIED]
USB_SM_YDOC, USB_TP_YDOC = 11.0, 41.5        # USB-C centres on the left edge (WIRING)
BTN_XDOC, BTN_YDOC = 9.0, (6.0, 14.0)        # BOOT / RESET centres (x 8-10, y about 6 and 14) UNVERIFIED which is which
BH_XYDOC, AHT_XYDOC = (49.0, 8.5), (57.0, 40.0)
J1_XYDOC, J3_XYDOC = (5.8, 22.45), (41.36, 46.6)   # J1 mid of c1 r8/r9, J3 mid of c14-c16 r18 (grid UNVERIFIED)
LANE_YDOC = (30.0, 34.0)                     # free lane for the battery lead between the bus/pull-ups and the AHT20 (doc y), ASSUMED

def cy(y_doc):
    """doc y (down from top edge) -> CAD y (up from the bottom edge)."""
    return PB_W - y_doc

# ---- heights (all ASSUMED / WIRING typical, never measured) ----
STANDOFF_H = 5.0                  # solder-side clearance: WIRING says about 4 mm (pin tips trimmed, wires) + 1.0 margin [ASSUMED margin]
Z_FLOOR = FLOOR
Z_PB_BOT = Z_FLOOR + STANDOFF_H   # 6.6
Z_PB_TOP = Z_PB_BOT + PB_T        # 8.6
TALLEST = max(v[4] for v in PARTS.values())          # 12.0 (J1 / J3)
LID_MARGIN = 2.0                  # clearance tallest part to lid underside; heights are unmeasured so +-2 mm [ASSUMED margin]
Z_TOP = Z_PB_TOP + TALLEST + LID_MARGIN             # lid plate underside, 22.6
# USB-C centres above the perfboard top (WIRING stack): SuperMini 2.5 header + 1.0 PCB + 1.65 half connector; TP4056 0.3 + 2.0 + 1.65
USB_SM_Z = Z_PB_TOP + 2.5 + 1.0 + 1.65
USB_TP_Z = Z_PB_TOP + 0.3 + 2.0 + 1.65
PLUG_W, PLUG_H = 14.0, 8.0        # opening for the cable plug overmold [ASSUMED: typical USB-C overmold about 12 x 6.5, +margin; fat plugs up to ~16 x 9 would not fit: prototype check]
Z_SPLIT = round(math.ceil(round((USB_SM_Z + USB_TP_Z) / 2 / LAYER, 6)) * LAYER, 3)   # parting plane, straddles both USB-C openings (13.2)

# ---- plan layout (CAD frame) ----
STRIP_TOP, STRIP_BOT = 8.0, 11.0  # beyond the board edge (+FIT): top = screw bosses; bottom = bosses + soil plug / cable [ASSUMED plug 10 mm long]
IX0 = -FIT
BOARD_X1c = PB_L + FIT
DIV_T = 1.2
DIV_X0, DIV_X1 = BOARD_X1c, BOARD_X1c + DIV_T
CH_W = 7.0                        # lead / connector channel beside the cell [ASSUMED JST-PH 2-pin housing about 6 x 4.5, +margin]
LOW_T = 1.2
CELL_WALL_X0 = DIV_X1 + CH_W      # low cradle wall between channel and cell
_c = bay.dims("A_eemb603449")     # EEMB LP603449, A-020 bay input 51 x 34.5 x 6.3 (BRIEF, no datasheet read)
CELL_CELL = (_c["cell_l"], _c["cell_w"], _c["cell_h"])
CELL_CAV = (_c["bay_l"], _c["bay_w"], _c["bay_h"])    # 53.0 x 35.1 x 7.2 (cell + 0.3/side + 1.0/end, +10 % swell +0.2 snapped)
CELL_ALT = (49.0, 34.0, 6.0)      # WIRING.md part-number convention 6.0 x 34 x 49 (UNVERIFIED): conflicts with the 51 x 34.5 x 6.3 brief value; the bay covers both
CELL_X0 = CELL_WALL_X0 + LOW_T
CELL_X1 = CELL_X0 + CELL_CAV[1]   # cell lies along Y, its short end (lead end) faces down
CELL_Y0 = -4.0
CELL_Y1 = CELL_Y0 + CELL_CAV[0]
IX1 = CELL_X1
IY0, IY1 = -(STRIP_BOT), PB_W + FIT + STRIP_TOP
OX0, OX1, OY0, OY1 = IX0 - WALL, IX1 + WALL, IY0 - WALL, IY1 + WALL
R_OUT = 3.0
R_IN = R_OUT - WALL
TOP_CHAMFER = 0.6                 # the one design touch: soft lid top edge (flag DESIGN_TOUCH)
DESIGN_TOUCH = True

# ---- board standoffs and locators ----
PAD_L, PAD_W = 12.0, 2.2          # under-board support pads along the long edges, outside the solder pads (first hole 3.4 mm from the edge, ring ~1.2)
PAD_X = (2.0, 56.0)               # x start of the two pads per long edge
FIN_T, FIN_L, FIN_H = 1.2, 8.0, 3.0   # locator fins beside the long edges, height above the board top
HOLD_D, HOLD_GAP = 3.6, 0.3       # lid hold-down pins on free corner spots (doc), gap to board top [ASSUMED]
HOLD_DOC = [(2.0, 1.8), (68.0, 1.8), (68.0, 48.2), (2.0, 30.5)]

# ---- fasteners [RULE: M2 + brass heat-set inserts] ----
SCREW_D, INSERT_HOLE, BOSS_D = 2.4, 3.2, 7.2         # M2 clearance 2.4; insert hole 3.2 [ASSUMED for an M2 x 3-4 mm insert, as in v3]
INSERT_DEPTH, INSERT_HOLE_DEPTH = 4.0, 6.0
SPIGOT_D, SPIGOT_H, SPIGOT_CLEAR = 4.2, 1.0, 0.2     # lid post spigot into a counterbore of d 4.6 in the boss top: locates the lid
CB_HEAD_D, CB_HEAD_DEPTH = 4.4, 1.2                  # M2 pan head recess on the lid top [ASSUMED head 4.0 x 1.3]
BOSS_XY = [(9.0, None, "top"), (62.0, None, "top"), (CELL_X1 - 3.5 - 6.0, None, "top"),
           (12.0, None, "bot"), (CELL_X1 - 3.5 - 6.0, None, "bot")]
BOSS_WALL_OVERLAP = 0.2           # boss cylinders sink 0.2 into the outer wall (no tangent contact = clean union)
BOSS_Y_TOP = IY1 - BOSS_D / 2.0 + BOSS_WALL_OVERLAP
BOSS_Y_BOT = IY0 + BOSS_D / 2.0 - BOSS_WALL_OVERLAP
def boss_xy():
    return [(x, BOSS_Y_TOP if side == "top" else BOSS_Y_BOT) for x, _, side in BOSS_XY]
BOSS_GAP_MIN = 1.0                # plan gap boss edge to board outline [ASSUMED threshold]
SCREW_STD = (6, 8, 10, 12, 14, 16, 18, 20)
def screw_len():
    need = (Z_TOP + LID_T - CB_HEAD_DEPTH) - (Z_SPLIT - INSERT_DEPTH + 1.0)   # head seat down to 1 mm above the insert bottom = min length for 3 mm engagement
    return next(s for s in SCREW_STD if s >= need), need

# ---- openings ----
# left wall (x = IX0): SuperMini USB-C (program) and TP4056 USB-C (charge); half-slots meet at Z_SPLIT, open to the rims (no bridging)
# soil cable exit in the bottom wall
CABLE_W, CABLE_H = 9.0, 6.0       # 3-wire ribbon + strain relief tie [ASSUMED]
# lid features
BTN_TUBE_OD, BTN_HOLE_D, BTN_PRESS_H, BTN_GAP = 5.0, 2.2, 5.1, 1.0   # pin guide tube; button top 3.5 + 1.6 above perfboard top ASSUMED
BH_WIN_D, BH_COLLAR_OD, BH_COLLAR_GAP = 5.0, 7.4, 1.0               # light window d 5 (chip centre offset UNVERIFIED), collar down to 1 mm above the chip top
LIGHT_SKIN = 0.0                  # mm of lid left over the window as a diffuser skin (0 = open hole); a skin changes the lux reading: not calibrated
VENT_N, VENT_W, VENT_L, VENT_PITCH = 4, 1.6, 10.0, 3.6
LED_WIN = (14.0, 5.0)             # TP4056 charge LED window over the module: LED position NOT measured (OPEN)
LED_XYDOC = (19.0, 41.5)
HATCH = (7.0, 11.0)               # lid opening over J1 for tweezers / fingernail on the jumper shunt [ASSUMED]
RIB_T, RIB_L = 2.0, 16.0          # lid ribs over the cell, bottom at the cell cavity top
# strain relief for the cell lead: S-bend posts in the channel + U-notch in the divider
POST_D = 2.4
SR_POSTS = [(DIV_X1 + 2.0, 8.0), (DIV_X1 + CH_W - 2.0, 12.5)]
NOTCH_Y = (16.0, 20.0)            # divider U-notch (lane), open to the top
NOTCH_Z0 = Z_PB_TOP + 0.6
DIV_H = 12.0
LOW_H = 4.0                       # cradle wall heights above the floor top
STOP_Y = 1.2

# ---- cell envelope heights ----
CELL_Z0 = Z_FLOOR
CELL_RIB_Z = Z_FLOOR + CELL_CAV[2]   # lid rib bottom = cavity top

STATUS = {   # parameter -> status, for the README table and a test that ASSUMED values never PASS
    "perfboard 70 x 50 x 2": "MEASURED", "TP4056 28 x 17 x 2": "MEASURED", "BH1750 17 x 14 x 2": "MEASURED", "AHT20 15 x 10 x 2": "MEASURED",
    "SuperMini 22.5 x 18": "UNVERIFIED", "component heights": "WIRING/ASSUMED", "cell 51 x 34.5 x 6.3": "BRIEF",
}

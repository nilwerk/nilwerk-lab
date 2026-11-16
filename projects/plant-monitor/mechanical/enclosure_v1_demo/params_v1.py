"""Enclosure v1 DEMO housing (4.E5), COMPACT round 2 (EXTRA from Arsany, 2026-11-16). All mm. Single source of truth.
Housing for the v1 function demo: 70 x 50 mm perfboard (NOT the custom PCB, NOT enclosure v3 / 4.E3, which is stopped).
Frame: CAD X right, Y up, Z up from the underside of the tray floor. Perfboard lower-left corner = (0, 0), so a
WIRING.md hole/doc position (x, y_doc) (origin top left, y down) maps to CAD (x, BOARD_W_Y - y_doc) via cy().

Round 2 changes (Arsany's observations on the printed fit-check part; round 1 stays in git and in enclosure/v1_demo/):
  (a) less free space: the separate LiPo bay (cell bay, divider, channel) is removed from the plan;
  (b) the LiPo sits UNDER the perfboard, between the board underside and the base floor (cell turned, 51 mm along Y);
  (c) the lid shell above the parting plane is about half as tall (11.0 -> 5.4 mm); the parting plane sits above the
      SuperMini USB-C opening, so both USB-C openings are fully in the base.

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
HOLD_DOC = [(2.0, 1.8), (68.0, 1.8), (68.0, 48.2), (2.0, 30.5)]   # lid hold-down pins on free spots (doc)

def cy(y_doc):
    """doc y (down from top edge) -> CAD y (up from the bottom edge)."""
    return PB_W - y_doc

# ---- LiPo cell [BRIEF: A-020 bay input, EEMB LP603449-PCM, 51 x 34.5 x 6.3, no datasheet read in this round] ----
_c = bay.dims("A_eemb603449")
CELL_CELL = (_c["cell_l"], _c["cell_w"], _c["cell_h"])               # (51.0, 34.5, 6.3): 51 along Y, 34.5 along X
CELL_CAV = (_c["bay_l"], _c["bay_w"], _c["bay_h"])                   # (53.0, 35.1, 7.2): cell + 0.3/side, +1.0/end, +10 % swell
# Antenna keep-out in CAD: x 27-40, y cy(22)..cy(0) = 28..50. The cell must stay ANT_MARGIN (10 mm) clear of that box in X.
KO_CAD = (ANT_KEEPOUT_DOC[0], cy(ANT_KEEPOUT_DOC[3]), ANT_KEEPOUT_DOC[2], cy(ANT_KEEPOUT_DOC[1]))
CELL_X0 = KO_CAD[2] + ANT_MARGIN                                     # 50.0: 10.0 mm from the keep-out box (closest option that keeps the margin)
CELL_X1 = CELL_X0 + CELL_CELL[1]                                     # 84.5 (overhangs the board's right edge, x 70, by 14.5 mm)
CELL_Y0 = (PB_W - CELL_CELL[0]) / 2.0                                # -0.5: cell centred on the board's centre line
CELL_Y1 = CELL_Y0 + CELL_CELL[0]                                     # 50.5
CAV_X0 = CELL_X0 - (CELL_CAV[1] - CELL_CELL[1]) / 2.0                # 49.7
CAV_X1 = CAV_X0 + CELL_CAV[1]                                        # 84.8
CAV_Y0 = CELL_Y0 - (CELL_CAV[0] - CELL_CELL[0]) / 2.0                # -1.5
CAV_Y1 = CAV_Y0 + CELL_CAV[0]                                        # 51.5
# Fraction of the cell footprint under the perfboard (board x 0-70, y 0-50)
CELL_UNDER_FRAC = (max(0.0, min(CELL_X1, PB_L) - max(CELL_X0, 0.0)) * max(0.0, min(CELL_Y1, PB_W) - max(CELL_Y0, 0.0))
                   / (CELL_CELL[1] * CELL_CELL[0]))

# ---- heights (all ASSUMED / WIRING typical, never measured) ----
PIN_TIP = 4.0                     # solder-side pin tips and trimmed wires below the board: WIRING.md about 4 mm (UNVERIFIED)
PIN_MARGIN = 1.0                  # [ASSUMED margin]
FLOOR_TO_BOARD_CELL = CELL_CAV[2] + PIN_TIP + PIN_MARGIN     # 12.2: gap needed under the board where the cell lies
STANDOFF_H = FLOOR_TO_BOARD_CELL  # uniform floor-to-board gap (round 1: 5.0); the cell sets it
Z_FLOOR = FLOOR
Z_PB_BOT = Z_FLOOR + STANDOFF_H   # 13.8
Z_PB_TOP = Z_PB_BOT + PB_T        # 15.8
TALLEST = max(v[4] for v in PARTS.values())          # 12.0 (J1 / J3)
LID_MARGIN = 2.0                  # clearance tallest part to lid underside; heights are unmeasured so +-2 mm [ASSUMED margin]
Z_TOP = Z_PB_TOP + TALLEST + LID_MARGIN             # lid plate underside, 29.8
Z_LID_TOP = Z_TOP + LID_T                           # lid plate top, 31.4
# USB-C centres above the perfboard top (WIRING stack): SuperMini 2.5 header + 1.0 PCB + 1.65 half connector; TP4056 0.3 + 2.0 + 1.65
USB_SM_Z = Z_PB_TOP + 2.5 + 1.0 + 1.65
USB_TP_Z = Z_PB_TOP + 0.3 + 2.0 + 1.65
PLUG_W, PLUG_H = 14.0, 8.0        # opening for the cable plug overmold [ASSUMED: typical USB-C overmold about 12 x 6.5, +margin; fat plugs up to ~16 x 9 would not fit: prototype check]
SPLIT_RIM = 1.0                   # solid rim of the base wall above the highest USB-C opening
# Parting plane above BOTH openings with a rim: both openings are fully in the base, the lid carries no USB-C cut
Z_SPLIT = round(math.ceil(round((max(USB_SM_Z, USB_TP_Z) + PLUG_H / 2 + SPLIT_RIM) / LAYER, 6)) * LAYER, 3)   # 26.0
LID_SHELL_H = Z_LID_TOP - Z_SPLIT                   # lid above the parting plane: 5.4 (round 1: 11.0)
LID_SHELL_H_R1 = 24.2 - 13.2                        # round 1 value (enclosure/v1_demo, 24.2 total, split 13.2) for the comparison

# ---- plan layout (CAD frame) ----
STRIP_TOP, STRIP_BOT = 8.0, 11.0  # beyond the board edge (+FIT): top = screw bosses; bottom = bosses, cell stop, strain relief, soil plug / cable [ASSUMED plug 10 mm long]
IX0 = -FIT
IX1 = CELL_X1 + FIT               # no bay any more: the cell's right side sits FIT inside the outer wall
IY0, IY1 = -(STRIP_BOT), PB_W + FIT + STRIP_TOP
OX0, OX1, OY0, OY1 = IX0 - WALL, IX1 + WALL, IY0 - WALL, IY1 + WALL
R_OUT = 3.0
R_IN = R_OUT - WALL
TOP_CHAMFER = 0.6                 # the one design touch: soft lid top edge (flag DESIGN_TOUCH)
DESIGN_TOUCH = True

# ---- board standoffs and locators ----
PAD_W = 2.2                       # under-board support pads along the long edges, outside the solder pads (first hole 3.4 mm from the edge, ring ~1.2)
# (x0, x1) of the two pads per long edge. Round 1: 2-14 and 56-68. Round 2: the second pad must clear the cell (x >= 49.7) and the
# antenna keep-out box (x 27-40, top edge), so it is shorter: 41-48 (7 mm), between the keep-out and the cradle wall (x 48.5)
PAD_XS = [(2.0, 14.0), (41.0, 48.0)]
FIN_T, FIN_L, FIN_H = 1.2, 8.0, 3.0   # locator fins beside the long edges, height above the board top
HOLD_D, HOLD_GAP = 3.6, 0.3       # lid hold-down pins on free corner spots (doc), gap to board top [ASSUMED]

# ---- cell cradle under the board (round 2) ----
STOP_T = 1.2                      # cradle wall / stop thickness (plastic; no metal in the keep-out)
LOW_H = 6.8                       # cradle wall top above the floor: cell 6.3 + 0.5. Below the 7.2 cavity top (the cavity allows swell, the walls do not contain it); 5.4 mm below the board underside
LEAD_NOTCH_X = (53.0, 59.0)       # notch in the bottom stop for the cell lead (lead leaves the cell end at y -0.5 toward the strip)
# Strain relief for the cell lead: S-bend posts in the bottom strip (round 1: in the bay channel)
POST_D = 2.4
SR_POSTS = [(52.5, -6.0), (59.5, -6.0)]
# Parking zone for the mated JST-PH pair (cell plug + pigtail), bottom strip, left of the cable exit (JST-PH about 6 x 4.5 + margin, ASSUMED)
JST_PARK = (18.0, 34.0, -10.5, -4.0)   # x0, x1, y0, y1 (CAD)

# ---- fasteners [RULE: M2 + brass heat-set inserts] ----
SCREW_D, INSERT_HOLE, BOSS_D = 2.4, 3.2, 7.2         # M2 clearance 2.4; insert hole 3.2 [ASSUMED for an M2 x 3-4 mm insert, as in v3]
INSERT_DEPTH, INSERT_HOLE_DEPTH = 4.0, 6.0
SPIGOT_D, SPIGOT_H, SPIGOT_CLEAR = 4.2, 1.0, 0.2     # lid post spigot into a counterbore of d 4.6 in the boss top: locates the lid
CB_HEAD_D, CB_HEAD_DEPTH = 4.4, 1.2                  # M2 pan head recess on the lid top [ASSUMED head 4.0 x 1.3]
BOSS_XY = [(9.0, None, "top"), (62.0, None, "top"), (CELL_X1 - 9.5, None, "top"),
           (12.0, None, "bot"), (CELL_X1 - 9.5, None, "bot")]
BOSS_WALL_OVERLAP = 0.2           # boss cylinders sink 0.2 into the outer wall (no tangent contact = clean union)
BOSS_Y_TOP = IY1 - BOSS_D / 2.0 + BOSS_WALL_OVERLAP
BOSS_Y_BOT = IY0 + BOSS_D / 2.0 - BOSS_WALL_OVERLAP
def boss_xy():
    return [(x, BOSS_Y_TOP if side == "top" else BOSS_Y_BOT) for x, _, side in BOSS_XY]
BOSS_GAP_MIN = 1.0                # plan gap boss edge to board outline [ASSUMED threshold]
SCREW_STD = (6, 8, 10, 12, 14, 16, 18, 20)
def screw_len():
    need = (Z_LID_TOP - CB_HEAD_DEPTH) - (Z_SPLIT - INSERT_DEPTH + 1.0)   # head seat down to 1 mm above the insert bottom = min length for 3 mm engagement
    return next(s for s in SCREW_STD if s >= need), need

# ---- openings ----
# left wall (x = IX0): SuperMini USB-C (program) and TP4056 USB-C (charge), both fully in the base (parting plane above them)
# soil cable exit in the bottom wall, at about the J3 plug mid-height
CABLE_W, CABLE_H = 9.0, 6.0       # 3-wire ribbon + strain relief tie [ASSUMED]
CABLE_Z = Z_PB_TOP + 5.5          # slot centre: 5.5 above the board top (J3 plug, ASSUMED)
# lid features
BTN_TUBE_OD, BTN_HOLE_D, BTN_PRESS_H, BTN_GAP = 5.0, 2.2, 5.1, 1.0   # pin guide tube; button top 5.1 above perfboard top ASSUMED
BH_WIN_D, BH_COLLAR_OD, BH_COLLAR_GAP = 5.0, 7.4, 1.0               # light window d 5 (chip centre offset UNVERIFIED), collar down to 1 mm above the chip top
LIGHT_SKIN = 0.0                  # mm of lid left over the window as a diffuser skin (0 = open hole); a skin changes the lux reading: not calibrated
VENT_N, VENT_W, VENT_L, VENT_PITCH = 4, 1.6, 10.0, 3.6
LED_WIN = (14.0, 5.0)             # TP4056 charge LED window over the module: LED position NOT measured (OPEN)
LED_XYDOC = (19.0, 41.5)
HATCH = (7.0, 11.0)               # lid opening over J1 for tweezers / fingernail on the jumper shunt [ASSUMED]

STATUS = {   # parameter -> status, for the README table and a test that ASSUMED values never PASS
    "perfboard 70 x 50 x 2": "MEASURED", "TP4056 28 x 17 x 2": "MEASURED", "BH1750 17 x 14 x 2": "MEASURED", "AHT20 15 x 10 x 2": "MEASURED",
    "SuperMini 22.5 x 18": "UNVERIFIED", "component heights": "WIRING/ASSUMED", "cell 51 x 34.5 x 6.3": "BRIEF",
    "solder-side pin tips 4 mm": "WIRING (UNVERIFIED)",
}

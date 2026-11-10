"""Enclosure v3 (4.E3) slice 2 parameters. All mm. Frame = DXF frame of the 4.P2 board:
X right, Y up (DXF Y = -KiCad Y), board top-left corner = (0,0), board body y -42..0, tail y -67..-42,
antenna module overhangs the top edge (y 0..+6). Z = thickness: tray floor top = 0, front (lid) side = +Z.
Tags: [src] taken from a repo source, [ASSUMED] my assumption (not datasheet, not repo), [rule] team rule."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
MECH = os.path.dirname(HERE)
sys.path.insert(0, MECH)
import params as P0  # bay params (EEMB baseline numbers)
import bay

# ---- manufacturing [rule: standards/3d-manufacturing.md] ----
BUILD = P0.BUILD_VOLUME
LAYER = 0.2
MIN_WALL = 1.2                     # [rule] role file
# ---- board [src: jlc_prep/input/plant-monitor-outline.dxf, = pcb/gen_pcb.py @ da39d2c] ----
BOARD_W, BODY_L, TAIL_W, TAIL_L = 34.5, 42.0, 12.0, 25.0
BOARD_T = 1.6
OVERHANG = 6.0                     # module antenna end above the board edge [src gen_pcb U1_OVERHANG, Emil's assumption]
TAIL_X0 = (BOARD_W - TAIL_W) / 2
# ---- cell bay [src: pcb-enclosure-bay.md, bay.dims('A_eemb603449')] ----
_d = bay.dims("A_eemb603449")
CELL_CAV = (_d["bay_l"], _d["bay_w"], _d["bay_h"])   # 53.0 x 35.1 x 7.2
CELL_GAP = 5.0                     # [src gen_pcb CELL_GAP]
CELL_X0, CELL_X1 = -CELL_GAP - CELL_CAV[0], -CELL_GAP
CELL_Y1 = -BODY_L + CELL_CAV[1]    # cavity top  (-6.9)
CELL_Y0 = -BODY_L                  # cavity bottom (-42.0)
# ---- stack in Z ----
STANDOFF = 1.0                     # [ASSUMED] board underside above floor (bottom copper is GND only, nothing mounted there)
BOARD_Z0, BOARD_Z1 = STANDOFF, STANDOFF + BOARD_T
LID_CLEAR = 0.5                    # [ASSUMED] min air gap tallest part to lid underside
# Component heights above the board top [ASSUMED: typical datasheet values from memory, NOT read in this repo; the board file has no heights]
H_BY_REF = {"U1": 2.4, "J1": 3.3, "J2": 4.5, "SW1": 1.5, "SW2": 1.5, "SW3": 1.5, "U3": 1.75, "U5": 1.0, "U6": 0.75,
            "D1": 1.1, "U2": 1.1, "U4": 1.1, "Q1": 1.1, "U7": 1.1, "D2": 0.8, "D3": 0.8, "E1": 0.04}
H_DEFAULT = 0.55                   # [ASSUMED] 0603 R/C
TALLEST = max(H_BY_REF.values())
INNER_H = round((BOARD_Z1 + TALLEST + LID_CLEAR) / LAYER + 1e-9) * LAYER   # 1.0+1.6+4.5+0.5 = 7.6
# ---- shell ----
WALL = 2.4                         # rim land for the flat gasket; >= 1.2 rule
FLOOR = 1.6
LID_T = 2.0                        # 1.6 + counterbore 0.6 would leave 1.0 < 1.2, so 2.0 (1.4 left)
GASKET_T = 1.0                     # [ASSUMED] flat silicone sheet gasket, 1.0 mm, about 0.7 mm compressed (not modelled, listed in the BOM)
INNER_X0, INNER_X1 = CELL_X0, BOARD_W + 0.3                    # 0.3 per side FDM / PCB tolerance
INNER_Y1 = OVERHANG + 1.0                                      # [ASSUMED] 1.0 mm air above the antenna tip (Q10: plastic wall detunes, to be verified)
BOSS_STRIP = 5.2                                               # strip below the board body for screw bosses
INNER_Y0 = -BODY_L - BOSS_STRIP
OUT_X0, OUT_X1 = INNER_X0 - WALL, INNER_X1 + WALL
OUT_Y0, OUT_Y1 = INNER_Y0 - WALL, INNER_Y1 + WALL
FILLET = 3.0
# ---- fasteners [rule: M2 + brass heat-set inserts] ----
SCREW_D, INSERT_HOLE, BOSS_D = 2.2, 3.2, 5.6                  # INSERT_HOLE 3.2 [ASSUMED] for M2 x 3 mm insert (check the insert datasheet)
BOSS_XY = [(-55.0, 3.2), (-27.0, 3.2), (-2.5, 3.2), (-2.5, INNER_Y0 + 2.6)]  # all >= 15 mm from the antenna rect (checked)
BOSS_XY += [(-55.0, INNER_Y0 + 2.6), (-27.0, INNER_Y0 + 2.6)]
INSERT_DEPTH = 4.0
# ---- USB-C [ASSUMED plug 8.94 x 3.26 (USB-C spec) + 0.3 per side FDM] ----
J1_Y, J1_Z = -33.0, BOARD_Z1 + 3.3 / 2
USB_W, USB_H = 9.6, 3.9
USB_POCKET = (14.0, 8.0, 1.2)      # overmold pocket w x h x depth from outside; wall left 1.2
# ---- light window over U6 BH1750 at KiCad (11.5, 4.5) ----
U6 = (11.5, -4.5)
WIN_D, WIN_CB_D, WIN_CB_DEPTH = 3.6, 6.4, 0.6    # clear self-adhesive film disc in the counterbore [ASSUMED part]
COLLAR_OD = 6.0                                    # wall (6.0-3.6)/2 = 1.2
COLLAR_GAP = 0.6                                   # collar tip above the sensor top (0.75 ASSUMED)
# ---- AHT20 vents over U5 at KiCad (4.5, 4.5): 3 slots + baffle cup open toward the board interior ----
U5 = (4.5, -4.5)
VENT_N, VENT_W, VENT_L, VENT_PITCH = 3, 0.8, 3.2, 1.6
CUP_W, CUP_L, CUP_WALL, CUP_DEPTH = 7.8, 6.0, 1.2, 3.0
# ---- pinhole reset over SW3 at KiCad (4.5, 23.5) ----
SW3 = (4.5, -23.5)
PIN_D, PIN_TUBE_OD, PIN_GAP = 1.8, 4.2, 0.4       # pin d 1.8 for a 1.0-1.2 mm paperclip / SIM tool
# ---- stake / tail seal plug ----
TUNNEL_W, TUNNEL_H = TAIL_W + 0.6, BOARD_T + 0.3  # 12.6 x 1.9: JLC outline +-0.2 plus FDM
PLUG_W, NOTCH_W = TUNNEL_W + 0.8, TUNNEL_W + 1.2  # 13.4 plug in a 13.8 notch (0.2 per side)
PLUG_T = WALL
DESIGN_TOUCH = False               # nilwerk trace relief: not applied in v3 slice 2 (flag kept off)

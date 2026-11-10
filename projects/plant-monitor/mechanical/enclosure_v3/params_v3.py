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
sys.path.insert(0, HERE)
import board_facts as BF
_F = BF.facts()

# ---- manufacturing [rule: standards/3d-manufacturing.md] ----
BUILD = P0.BUILD_VOLUME
LAYER = 0.2
MIN_WALL = 1.2                     # [rule] role file
# ---- board [src: jlc_prep/input/plant-monitor-outline.dxf, = pcb/gen_pcb.py @ da39d2c] ----
# All board numbers are READ from input/ (copy of agent/pcb/4.P2-s2 @ b2e211f, PR #73) by board_facts.py, none typed here.
BOARD_W, BODY_L, TAIL_W, TAIL_L = _F["board_w"], _F["body_l"], _F["tail_w"], _F["tail_l"]
BOARD_T = _F["thickness"]
OVERHANG = _F["overhang"]   # module antenna end above the top edge (DXF MODULE_U1 top)
MODULE_X0, MODULE_X1 = _F["module_x0"], _F["module_x1"]
TAIL_X0 = _F["tail_x0"]
# ---- cell bay [src: pcb-enclosure-bay.md, bay.dims('A_eemb603449')] ----
_d = bay.dims("A_eemb603449")
CELL_CAV = (_d["bay_l"], _d["bay_w"], _d["bay_h"])   # 53.0 x 35.1 x 7.2
CELL_X0, CELL_Y0, CELL_X1, CELL_Y1 = _F["cell"]      # DXF CELL_BAY_CAVITY
CELL_GAP = -CELL_X1                # 5.0
assert abs((CELL_X1 - CELL_X0) - CELL_CAV[0]) < 1e-6 and abs((CELL_Y1 - CELL_Y0) - CELL_CAV[1]) < 1e-6, "board DXF cavity != bay.dims"

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
LID_T = 2.4                        # PETG lid spans ~98 mm between bosses; 2.4 (was 2.0) for stiffness [ASSUMED sizing, FE not run]; counterbore 0.6 leaves 1.8
GASKET_T = 1.0                     # [ASSUMED] flat silicone sheet gasket, 1.0 mm, about 0.7 mm compressed (not modelled, listed in the BOM)
INNER_X0, INNER_X1 = CELL_X0, max(BOARD_W, _F["max_x"]) + 0.3                    # 0.3 beyond the right-most part (J1 shell protrudes 0.5 beyond the board edge in #73)
INNER_Y1 = OVERHANG + 1.0                                      # [ASSUMED] 1.0 mm air above the antenna tip (Q10: plastic wall detunes, to be verified)
BOSS_STRIP = 5.4                                               # strip below the board body for screw bosses
INNER_Y0 = -BODY_L - BOSS_STRIP
OUT_X0, OUT_X1 = INNER_X0 - WALL, INNER_X1 + WALL
OUT_Y0, OUT_Y1 = INNER_Y0 - WALL, INNER_Y1 + WALL
FILLET = 3.0
# ---- fasteners [rule: M2 + brass heat-set inserts] ----
SCREW_D, INSERT_HOLE, BOSS_D = 2.4, 3.2, 6.4                  # PETG: M2 clearance 2.4 (was 2.2); insert hole 3.2 [ASSUMED] for M2 x 3 mm insert; boss 6.4 = 1.6 mm wall round the hole (was 5.6 = 1.2)
BOSS_XY = [(-55.0, 3.2), (-27.0, 3.2), (-2.5, 3.2)]  # top row; all >= 15 mm from the antenna rect (checked)
# bottom row: 1.2 mm skin to the outside (BOSS_STRIP 5.4 gives room) and the boss top at -42.2 clears the cell cavity (-42.0)
BOSS_XY += [(-55.0, INNER_Y0 + 2.0), (-27.0, INNER_Y0 + 2.0), (-2.5, INNER_Y0 + 2.0)]
INSERT_DEPTH = 4.0
# ---- USB-C [ASSUMED plug 8.94 x 3.26 (USB-C spec) + 0.3 per side FDM] ----
J1_Y, J1_Z = _F["at"]["J1"][1], BOARD_Z1 + 3.3 / 2
USB_W, USB_H = 9.6, 3.9
USB_POCKET = (14.0, 8.0, 1.2)      # overmold pocket w x h x depth from outside; wall left 1.2
# ---- light window over U6 BH1750 at KiCad (11.5, 4.5) ----
U6 = _F["at"]["U6"][:2]
WIN_D, WIN_CB_D, WIN_CB_DEPTH = 3.6, 6.4, 0.6    # clear self-adhesive film disc in the counterbore [ASSUMED part]
COLLAR_OD = 6.0                                    # wall (6.0-3.6)/2 = 1.2
COLLAR_GAP = 0.6                                   # collar tip above the sensor top (0.75 ASSUMED)
# ---- AHT20 vents over U5 at KiCad (4.5, 4.5): 3 slots + baffle cup open toward the board interior ----
U5 = _F["at"]["U5"][:2]
VENT_N, VENT_W, VENT_L, VENT_PITCH = 3, 1.0, 3.2, 1.6    # slot 1.0 (was 0.8): 2.5 lines at 0.42 mm, PETG-safe [ASSUMED]
CUP_W, CUP_L, CUP_WALL, CUP_DEPTH = 7.8, 6.0, 1.2, 3.0
# ---- pinhole reset over SW3 at KiCad (4.5, 23.5) ----
SW3 = _F["at"]["SW3"][:2]
PIN_D, PIN_TUBE_OD, PIN_GAP = 1.8, 4.2, 0.4       # pin d 1.8 for a 1.0-1.2 mm paperclip / SIM tool
# ---- stake / tail seal plug ----
TUNNEL_W, TUNNEL_H = TAIL_W + 0.6, BOARD_T + 0.6  # 12.6 x 2.2 (was 1.9): PETG needs 0.3 mm per side, not 0.15; sealant fills the rest
PLUG_W, NOTCH_W = TUNNEL_W + 0.8, TUNNEL_W + 1.2  # 13.4 plug in a 13.8 notch (0.2 per side)
PLUG_T = WALL
DESIGN_TOUCH = False               # nilwerk trace relief: not applied in v3 slice 2 (flag kept off)

# ---- PETG on the P1S, 0.4 mm nozzle (standards s.2-3). Limits used by fit_check_v3 ----
PETG_MIN_FEATURE = 0.8             # 2 lines at 0.42 mm: smallest feature we accept (standards s.3 quotes ~0.5 practical; 0.8 for reliability)
PETG_BOSS_WALL = 1.6               # wall around a heat-set insert hole in PETG (target; rule floor 1.2)
PETG_SCREW_TORQUE_NM = 0.25        # [ASSUMED] max M2 tightening torque into a PETG insert; the insert datasheet governs
PETG_SHRINK = 0.004                # [ASSUMED] 0.4 % PETG shrink; set by the test print (standards s.3 says calibrate)
SEAL_TYPE = "silicone sheet gasket 1.0 mm (bought part, not PETG; ASSUMED)"
# Tail / stake length is NOT decided (open point, Arsany/Emil). Tunnel and plug are sized for the current 25 mm tail only.

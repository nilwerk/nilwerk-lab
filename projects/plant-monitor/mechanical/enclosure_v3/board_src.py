"""Reads the 4.P2 board (jlc_prep/input, copied from agent/pcb/4.P2 @ da39d2c) into component boxes in the DXF frame."""
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "jlc_prep"))
import board_step as bs
import board_facts as BF
import params_v3 as P

def components():
    return {r: dict(ref=r, box=b, h=P.H_BY_REF.get(r, P.H_DEFAULT)) for r, b in BF.boxes().items()}


def gap(a, b):
    dx = max(b[0] - a[2], a[0] - b[2], 0.0); dy = max(b[1] - a[3], a[1] - b[3], 0.0)
    return math.hypot(dx, dy)

def placeholder_refs():
    return BF.placeholder_refs()

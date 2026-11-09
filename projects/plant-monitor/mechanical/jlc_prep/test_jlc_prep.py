"""4.E3 JLC prep tests. Run: python -m pytest jlc_prep/test_jlc_prep.py  (from projects/plant-monitor/mechanical)

Tests without CAD: source parsing and fit numbers. Tests with CAD (cadquery): the STEP is written and re-opened.
"""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))

import board_step as bs  # noqa: E402
import fit_check as fc  # noqa: E402

README_MECH = os.path.join(os.path.dirname(HERE), "README.md")
STEP_OUT = os.path.join(HERE, "out", "plant-monitor-board.step")


@pytest.fixture(scope="module")
def board():
    return bs.parse_board()


def test_source_counts(board):
    # 46 placed footprints (45 BOM pieces + E1 electrode copper), 184 pads, 16 vias, 8 outline segments, 1.6 mm
    assert len(board["footprints"]) == 46
    assert sum(len(f["pads"]) for f in board["footprints"]) == 184
    assert len(board["vias"]) == 16
    assert len(board["edge"]) == 8
    assert board["thickness"] == pytest.approx(1.6)


def test_outline_is_the_dxf_outline(board):
    loop = {tuple(round(c, 4) for c in bs.to_step_xy(p)) for p in bs.outline_loop(board["edge"])}
    dxf = {tuple(round(c, 4) for c in a) for a, _ in bs.parse_dxf_outline()}
    assert loop == dxf and len(loop) == 8


def test_board_size_and_fit_numbers_match_readme():
    _, rows, ov = fc.checks()
    assert (ov["board_w"], ov["board_l"]) == pytest.approx((34.5, 67.0))  # body 42.0 + tail 25.0 (DXF OUTLINE)
    d = fc.bay.dims("A_eemb603449")
    assert (d["bay_l"], d["bay_w"], d["bay_h"]) == pytest.approx((53.0, 35.1, 7.2))
    assert (d["out_l"], d["out_w"], d["out_h"]) == pytest.approx((56.2, 38.3, 10.4))
    readme = open(README_MECH, encoding="utf-8").read().splitlines()
    assert "53.0 x 35.1 x 7.2" in readme[21]   # README line 22 (cited in fit_check)
    assert "56.2 x 38.3 x 10.4" in readme[24]  # README line 25
    assert len(rows) == 8  # 8 checks in fit_check.checks(): 6 PASS, 2 NOT CHECKED (thickness vs unknown parts, enclosure inner size)


def test_margins():
    rows = {r["item"]: r for r in fc.checks()[1]}
    width = [r for k, r in rows.items() if k.startswith("Board width")][0]
    assert width["value"].startswith("34.5 vs 35.1: 0.30 mm per side")
    gap = [r for k, r in rows.items() if k.startswith("Cell cavity to board edge")][0]
    assert gap["value"] == "5.0 mm"
    ant = [r for k, r in rows.items() if k.startswith("Antenna end")][0]
    assert ant["value"].startswith("28.4 mm") and ant["ok"] is True
    assert [r for k, r in rows.items() if k.startswith("Enclosure v3")][0]["ok"] is None


def test_step_opens_and_is_valid():
    cq = pytest.importorskip("cadquery")
    info = bs.build_step(STEP_OUT)
    assert info["n_footprints"] == 46 and info["n_pads"] == 184 and info["n_vias"] == 16
    assert os.path.getsize(STEP_OUT) > 10_000
    shape = cq.importers.importStep(STEP_OUT).val()
    solids = shape.Solids()
    # 1 board + 16 vias x 2 rings + 184 pads
    assert len(solids) == 1 + 32 + 184
    assert shape.isValid()
    bb = shape.BoundingBox()
    assert bb.xmin == pytest.approx(0.0, abs=1e-3) and bb.xmax == pytest.approx(34.5, abs=1e-3)
    assert bb.zmin == pytest.approx(-bs.COPPER_T, abs=1e-3) and bb.zmax == pytest.approx(1.6 + bs.COPPER_T, abs=1e-3)
    assert bb.ymin == pytest.approx(-67.0, abs=0.5)

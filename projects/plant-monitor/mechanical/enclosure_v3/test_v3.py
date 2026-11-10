"""Tests for enclosure v3 slice 2. Run: python -m pytest test_v3.py"""
import pytest
import params_v3 as P
import board_src as B
import enclosure_v3 as E
import fit_check_v3 as F


@pytest.fixture(scope="module")
def rows():
    F.ROWS.clear()
    return F.main()


def test_all_fit_checks_pass(rows):
    bad = [r for r in rows if r[3] != "PASS"]
    assert not bad, bad


def test_inner_size_numbers():
    assert round(P.INNER_X1 - P.INNER_X0, 1) == 92.8 and round(P.INNER_Y1 - P.INNER_Y0, 1) == 54.2 and P.INNER_H == pytest.approx(7.6)
    assert (round(P.OUT_X1 - P.OUT_X0, 1), round(P.OUT_Y1 - P.OUT_Y0, 1)) == (97.6, 59.0)


def test_source_counts():
    c = B.components()
    assert len(c) == 46
    ph = B.placeholder_refs()
    assert len(ph) == 9 and sorted(r for r, _ in ph) == sorted(["U1", "SW1", "SW2", "SW3", "J1", "J2", "U5", "U6", "E1"])


def test_negative_control_collision_detected():
    """The interference check must be able to fail: a boss dropped on the board body must overlap."""
    import cadquery as cq
    boss = cq.Workplane("XY").workplane(offset=0).center(17, -20).circle(2.8).extrude(7.0)
    assert F.vol_overlap(boss, E.board_ghost()) > 1.0


def test_walls_rule():
    assert min(P.WALL, P.FLOOR, P.LID_T - P.WIN_CB_DEPTH, P.WALL - P.USB_POCKET[2], (P.COLLAR_OD - P.WIN_D) / 2, P.CUP_WALL) >= P.MIN_WALL - 1e-9


def test_antenna_gap_both_methods():
    ant = (20.3, 0.0, 33.5, 6.0); cell = (P.CELL_X0, P.CELL_Y0, P.CELL_X1, P.CELL_Y1)
    assert B.gap(ant, cell) == pytest.approx(26.2, abs=0.05)
    assert B.gap((20.3, 6.0, 33.5, 6.0), cell) == pytest.approx(28.4, abs=0.05)

"""Tests for enclosure v3 slice 2. Run: python -m pytest test_v3.py"""
import pytest
import params_v3 as P
import board_src as B
import board_facts as BF
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
    assert round(P.INNER_X1 - P.INNER_X0, 1) == 93.3 and round(P.INNER_Y1 - P.INNER_Y0, 1) == 52.7 and P.INNER_H == pytest.approx(7.6)
    assert (round(P.OUT_X1 - P.OUT_X0, 1), round(P.OUT_Y1 - P.OUT_Y0, 1)) == (98.1, 57.5)


def test_params_derived_from_board_file_not_hardcoded():
    f = BF.facts()
    assert P.OVERHANG == f["overhang"] == pytest.approx(4.5)
    assert P.BOARD_W == f["board_w"] and P.TAIL_W == f["tail_w"] and P.U6 == f["at"]["U6"][:2] and P.SW3 == f["at"]["SW3"][:2]
    assert abs(P.SW3[0] - 5.0) < 1e-9          # #73 moved SW3 x from 4.5 to 5.0


def test_board_copy_matches_source():
    """Fails if input/ differs from the recorded sha256 (SOURCE.txt) or, when the source branch is reachable, from that branch's blob."""
    import hashlib, os, re, subprocess
    src = open(os.path.join(BF.HERE, "input", "SOURCE.txt")).read()
    for name in ("plant-monitor.kicad_pcb", "plant-monitor-outline.dxf"):
        data = open(os.path.join(BF.HERE, "input", name), "rb").read()
        want = re.search(r"([0-9a-f]{64})\s+" + re.escape(name), src).group(1)
        assert hashlib.sha256(data).hexdigest() == want, f"{name}: copy differs from SOURCE.txt"
        r = subprocess.run(["git", "show", f"origin/agent/pcb/4.P2-s2:projects/plant-monitor/pcb/{name}"], capture_output=True, cwd=BF.HERE)
        if r.returncode == 0:
            assert r.stdout == data, f"{name}: copy differs from origin/agent/pcb/4.P2-s2 (re-copy the board, update SOURCE.txt)"


def test_source_counts():
    c = B.components()
    assert len(c) == 46
    ph = B.placeholder_refs()
    assert sorted(r for r, _ in ph) == ["E1", "U5", "U6"], ph      # #73: U1, J1, J2, SW1-3 are real footprints now


def test_negative_control_collision_detected():
    """The interference check must be able to fail: a boss dropped on the board body must overlap."""
    import cadquery as cq
    boss = cq.Workplane("XY").workplane(offset=0).center(17, -20).circle(2.8).extrude(7.0)
    assert F.vol_overlap(boss, E.board_ghost()) > 1.0


def test_walls_rule():
    assert min(P.WALL, P.FLOOR, P.LID_T - P.WIN_CB_DEPTH, P.WALL - P.USB_POCKET[2], (P.COLLAR_OD - P.WIN_D) / 2, P.CUP_WALL) >= P.MIN_WALL - 1e-9


def test_antenna_gap_both_methods():
    ant = (P.MODULE_X0, 0.0, P.MODULE_X1, P.OVERHANG); cell = (P.CELL_X0, P.CELL_Y0, P.CELL_X1, P.CELL_Y1)
    assert B.gap(ant, cell) == pytest.approx(26.2, abs=0.05)
    assert B.gap((P.MODULE_X0, P.OVERHANG, P.MODULE_X1, P.OVERHANG), cell) == pytest.approx(27.7, abs=0.05)

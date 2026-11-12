"""Tests for enclosure v3 (slice 2 checks, slice 3 tail variants and sourced heights). Run: python -m pytest test_v3.py"""
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


EXPECTED_OPEN = ("Board tail in DXF", "Tallest part to lid underside", "J2 at the distributor value 5.5 mm", "Heights with a datasheet page in the model",
                 "PETG top wall over the antenna", "Screw torque limit")


@pytest.mark.parametrize("tail", ["14", "20"])
def test_all_fit_checks_pass_for_both_tail_variants(tail):
    """No FAIL for either variant. The OPEN rows are exactly EXPECTED_OPEN: board DXF tail (A-071), the J2 height (rows 'Tallest part' and 'J2 5.5', A-076),
    heights not datasheet-sourced, the PETG wall over the antenna, and the unchecked screw torque. Nothing OPEN is counted as PASS."""
    rows = F.main(tail)
    bad = [r for r in rows if r[3] == "FAIL"]
    assert not bad, bad
    opened = tuple(r[0].split(" (")[0] for r in rows if r[3] == "OPEN")
    assert sorted(opened) == sorted(EXPECTED_OPEN), opened
    assert sum(r[3] == "PASS" for r in rows) >= 47


def test_inner_size_numbers():
    assert round(P.INNER_X1 - P.INNER_X0, 1) == 93.3 and round(P.INNER_Y1 - P.INNER_Y0, 1) == 52.9 and P.INNER_H == pytest.approx(7.6)
    assert P.INNER_H_IF_J2_5_5 == pytest.approx(8.6)           # the alternative that the sourced J2 value needs (LOCKED_INTERFACE shows both)
    assert (round(P.OUT_X1 - P.OUT_X0, 1), round(P.OUT_Y1 - P.OUT_Y0, 1)) == (98.1, 57.7)


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


def test_petg_rules_hold():
    """PETG on the P1S: boss wall, skin, lid stiffness and feature floor (params_v3 PETG_*)."""
    assert (P.BOSS_D - P.INSERT_HOLE) / 2 >= P.PETG_BOSS_WALL - 1e-9
    assert min((y - P.OUT_Y0) - P.BOSS_D / 2 for _, y in P.BOSS_XY) >= 1.2 - 1e-9
    assert P.LID_T >= 2.4 - 1e-9 and P.LID_T - P.WIN_CB_DEPTH >= 1.2 - 1e-9
    assert P.VENT_W >= P.PETG_MIN_FEATURE and P.PIN_D >= P.PETG_MIN_FEATURE and P.SCREW_D >= P.PETG_MIN_FEATURE


def test_bosses_clear_cell_and_board_by_boolean():
    """Negative control: a boss moved into the cell must overlap the cell ghost (so the check can fail)."""
    import cadquery as cq
    bad = cq.Workplane("XY").center(-27.0, -40.0).circle(P.BOSS_D / 2).extrude(P.INNER_H)
    assert F.vol_overlap(bad, E.cell_ghost()) > 1.0
    good = cq.Workplane("XY").center(-27.0, P.INNER_Y0 + 2.0).circle(P.BOSS_D / 2).extrude(P.INNER_H)
    assert F.vol_overlap(good, E.cell_ghost()) < 1e-3


def test_height_rows_are_not_vacuous(monkeypatch):
    """QA (Ines): the height rows must move when an ASSUMED part height moves. INNER_H is fixed, so J2 is tested against it."""
    comps = B.components()
    gap, worst = F.lid_clearance(comps)
    assert gap == pytest.approx(0.5, abs=1e-6) and worst["ref"] == "J2" and worst["h"] == 4.5   # positive control: today's J2 = 4.5
    monkeypatch.setitem(P.H_BY_REF, "J2", 5.0)                  # mutation: J2 +0.5 mm
    gap5, worst5 = F.lid_clearance(B.components())
    assert gap5 == pytest.approx(0.0, abs=1e-6) and worst5["ref"] == "J2"
    assert gap5 < P.LID_CLEAR - 1e-9                            # the row would FAIL
    monkeypatch.setitem(P.H_BY_REF, "J2", 4.0)                  # mutation: J2 -0.5 mm -> row passes with more air (no false fail)
    assert F.lid_clearance(B.components())[0] == pytest.approx(1.0, abs=1e-6)


def test_j2_height_mutation_fails_fit_check(monkeypatch):
    """End to end: J2 at 5.0 mm must turn the 'Tallest part to lid' row into a FAIL in the full fit check."""
    monkeypatch.setitem(P.H_BY_REF, "J2", 5.0)
    rows = F.main()
    failed = [r[0] for r in rows if r[3] == "FAIL"]
    assert any(n.startswith("Tallest part to lid") for n in failed), failed


def test_tail_variants_derived_from_board_and_wall():
    """Electrode beyond the outer bottom face: 14 mm and 20 mm map to board tails 25.8 and 31.8 (DXF tail 25.0, copper tip margin 4.0)."""
    assert P.EXPOSED_NOW == pytest.approx(13.2, abs=1e-6)                 # copper tip -63.0 minus outer face -49.8
    assert P.TIP_MARGIN == pytest.approx(4.0, abs=1e-6)
    assert P.TAIL_L_VARIANT["14"] == pytest.approx(25.8, abs=1e-6) and P.TAIL_L_VARIANT["20"] == pytest.approx(31.8, abs=1e-6)
    for tail, tl in P.TAIL_L_VARIANT.items():
        assert P.tail_len_for(P.TAIL_VARIANTS[tail]) == pytest.approx(tl)


def test_board_ghost_follows_tail_variant():
    import cadquery as cq
    for tail, tl in P.TAIL_L_VARIANT.items():
        bb = E.board_ghost(tl).val().BoundingBox()
        assert bb.ymin == pytest.approx(-(P.BODY_L + tl), abs=1e-6)
    assert E.board_ghost().val().BoundingBox().ymin == pytest.approx(-(P.BODY_L + P.TAIL_L), abs=1e-6)   # default = DXF tail


def test_height_sources_cover_the_model():
    """Every height in the fit check has a source tag. Only U1 is read from its datasheet; the rest are SECONDARY, CONFLICT or ASSUMED."""
    assert set(P.H_BY_REF) <= set(P.H_SRC), set(P.H_BY_REF) - set(P.H_SRC)
    assert {k for k, v in P.H_SRC.items() if v[0] == "DATASHEET"} == {"U1"}
    assert "5.5" in P.H_SRC["J2"][1] and P.H_BY_REF["J2"] == 4.5          # the conflict is recorded, the model value is not silently changed


def test_locked_interface_file_is_current():
    """LOCKED_INTERFACE.md is generated; fails if it drifts from params_v3 / board_facts (run locked_interface.py to refresh)."""
    import locked_interface as LI
    assert LI.OUT.read_text(encoding="utf-8") == LI.text()


def test_electrode_span_from_board():
    assert BF.facts()["copper_end"] == pytest.approx(-63.0, abs=1e-6) and BF.facts()["tail_end"] == pytest.approx(-67.0, abs=1e-6)

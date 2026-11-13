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


EXPECTED_OPEN = ("Board tail in DXF", "Tallest part to lid underside", "J2 at 5.5 mm", "Heights with a datasheet page in the model",
                 "PETG top wall over the antenna", "Screw torque limit",
                 # fix round 2 (Ines, Theo, Arsany rule: a pass against an ASSUMED value is not a pass)
                 "Antenna tip to top wall", "Interference lid vs board+parts", "PETG min feature: vent slot width", "PETG min feature: pinhole d",
                 "PETG min feature: light window d", "PETG min feature: lid screw clearance hole", "PETG min feature: plug wall",
                 "Seal tunnel clearance per side", "Model heights equal their cited source",
                 # fix round 3 (Theo verdict on 689c161): seal width and PETG boss wall are passes against ASSUMED / own-target values; J1 upright is A-087 (OPEN)
                 "Seal tunnel clearance per side", "PETG insert boss wall", "J1 USB-C height, flat vs upright",
                 # slice 4 (Yara, 2026-11-13): boss to board outline plan gap, threshold ASSUMED 1.0 mm
                 "Boss to board outline")


@pytest.mark.parametrize("tail", ["14", "20"])
def test_all_fit_checks_pass_for_both_tail_variants(tail):
    """No FAIL for either variant. The OPEN rows are exactly EXPECTED_OPEN (19): the board DXF tail (A-071), the J2 height (A-076, rows 'Tallest part',
    'J2 5.5', 'Interference lid'), heights not datasheet-sourced, the PETG wall over the antenna, the unchecked torque, the J1 upright height (A-087), and every
    pass that rests on an ASSUMED threshold or our own target (antenna air, PETG feature floor, seal clearance, PETG boss wall). Nothing OPEN is counted as PASS."""
    rows = F.main(tail)
    bad = [r for r in rows if r[3] == "FAIL"]
    assert not bad, bad
    opened = tuple(r[0].split(" (")[0] for r in rows if r[3] == "OPEN")
    assert sorted(opened) == sorted(EXPECTED_OPEN), opened
    assert sum(r[3] == "PASS" for r in rows) == 40


def test_inner_size_numbers():
    assert round(P.INNER_X1 - P.INNER_X0, 1) == 93.3 and round(P.INNER_Y1 - P.INNER_Y0, 1) == 53.7 and P.INNER_H == pytest.approx(8.6)   # slice 4: budget 8.6 (J2 5.5)
    assert P.INNER_H_OPT_A == pytest.approx(7.6)                # option A (J2 4.5, ASSUMED) kept as the record
    assert P.INNER_H_IF_J2_5_5 == pytest.approx(8.6)           # the alternative that the sourced J2 value needs (LOCKED_INTERFACE shows both)
    assert (round(P.OUT_X1 - P.OUT_X0, 1), round(P.OUT_Y1 - P.OUT_Y0, 1)) == (97.3, 56.9)     # slice 4 outer footprint (slice 3: 98.1 x 57.7)


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
    assert min(P.WALL, P.WALL_LOW, P.FLOOR, P.LID_T - P.WIN_CB_DEPTH, P.WALL - P.USB_POCKET[2], (P.COLLAR_OD - P.WIN_D) / 2, P.CUP_WALL) >= P.MIN_WALL - 1e-9
    assert P.min_wall_corners() >= P.MIN_WALL - 1e-9            # corner wall between the rounded skin and the cavity corners (slice 4)


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
    assert gap == pytest.approx(0.5, abs=1e-6) and worst["ref"] == "J2" and worst["h"] == 5.5   # positive control: J2 5.5 in the 8.6 budget (0.5 air)
    monkeypatch.setitem(P.H_BY_REF, "J2", 6.6)                  # mutation: J2 +1.1 mm over the budget
    gap5, worst5 = F.lid_clearance(B.components())
    assert gap5 == pytest.approx(-0.6, abs=1e-6) and worst5["ref"] == "J2"
    assert gap5 < P.LID_CLEAR - 1e-9                            # the row would FAIL
    monkeypatch.setitem(P.H_BY_REF, "J2", 4.0)                  # mutation: J2 -0.5 mm -> row passes with more air (no false fail)
    assert F.lid_clearance(B.components())[0] == pytest.approx(2.0, abs=1e-6)


def test_j2_height_mutation_fails_fit_check(monkeypatch):
    """End to end: J2 at 5.0 mm must turn the 'Tallest part to lid' row into a FAIL in the full fit check."""
    monkeypatch.setitem(P.H_BY_REF, "J2", 6.6)
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
    assert "5.5" in P.H_SRC["J2"][1] and P.H_BY_REF["J2"] == 5.5 and P.H_SRC["J2"][0] == "SECONDARY"   # A-076: model value = listing value, not a datasheet
    assert P.H_SRC["J1_UPRIGHT"][0] == "OPEN" and (P.J1_UPRIGHT_H, P.J1_UPRIGHT_TOL) == (11.94, 0.25)   # upright J1 recorded as OPEN (A-087), model keeps flat 3.3


def test_locked_interface_file_is_current():
    """LOCKED_INTERFACE.md is generated; fails if it drifts from params_v3 / board_facts (run locked_interface.py to refresh)."""
    import locked_interface as LI
    assert LI.OUT.read_text(encoding="utf-8") == LI.text()


def test_electrode_span_from_board():
    assert BF.facts()["copper_end"] == pytest.approx(-63.0, abs=1e-6) and BF.facts()["tail_end"] == pytest.approx(-67.0, abs=1e-6)


# ---- fix round 2 (Ines, Theo): one mutation test per SOURCED value. A changed value must make the fit check FAIL or the locked-interface file stale.
def _fit_fails(rows):
    return [r[0] for r in rows if r[3] == "FAIL"]


def _locked_stale():
    import locked_interface as LI
    return LI.OUT.read_text(encoding="utf-8") != LI.text()


@pytest.mark.parametrize("ref,new", [("U1", 3.4), ("U5", 2.0), ("U6", 1.75), ("SW1", 2.5), ("SW2", 2.5), ("SW3", 2.5)])
def test_sourced_height_mutation_fails(monkeypatch, ref, new):
    """Sourced heights (U1 DATASHEET 2.4; U5, U6, SW1-3 SECONDARY). U1 2.4 -> 3.4 is the Ines case: it is not in the locked file, so the
    cited-source row (54) must be the one that FAILS."""
    monkeypatch.setitem(P.H_BY_REF, ref, new)
    fails = _fit_fails(F.main())
    assert any(n.startswith("Model heights equal their cited source") for n in fails) or _locked_stale(), fails
    if ref == "U1":
        assert any(n.startswith("Model heights equal their cited source") for n in fails), fails


def test_j2_above_5_5_budget_mutation_fails_lid_interference(monkeypatch):
    """J2 above the 5.5 mm budget (6.2 mm, inner 8.6): the lid overlaps the tallest part, so the interference row and the clearance row FAIL."""
    monkeypatch.setitem(P.H_BY_REF, "J2", 6.2)
    fails = _fit_fails(F.main())
    assert "Interference lid vs board+parts" in fails and any(n.startswith("Tallest part to lid underside") for n in fails), fails


def test_j2_5_5_with_option_a_inner_7_6_fails_lid_interference(monkeypatch):
    """Sourced J2 5.5 in option A (inner 7.6, the old J2 4.5 budget): the lid overlaps the part. This is why the box moved to 8.6 (A-076)."""
    monkeypatch.setattr(P, "INNER_H", P.INNER_H_OPT_A)
    fails = _fit_fails(F.main())
    assert "Interference lid vs board+parts" in fails and any(n.startswith("Tallest part to lid underside") for n in fails), fails


def test_sourced_overhang_mutation_fails(monkeypatch):
    """DXF antenna overhang (4.5, read from the PCB file): +1.0 mm leaves no air above the antenna."""
    monkeypatch.setattr(P, "OVERHANG", P.OVERHANG + 1.0)
    assert "Antenna tip to top wall" in [n.split(" (")[0] for n in _fit_fails(F.main())]


def test_sourced_cell_cavity_mutation_fails(monkeypatch):
    """Cell bay cavity (bay.dims A_eemb603449, 53.0 x 35.1 x 7.2): +1.0 mm in X must fail the cell row."""
    monkeypatch.setattr(P, "CELL_CAV", (P.CELL_CAV[0] + 1.0, P.CELL_CAV[1], P.CELL_CAV[2]))
    assert any(n.startswith("Cell cavity (X x Y)") for n in _fit_fails(F.main()))


def test_sourced_board_width_mutation_fails_locked_file(monkeypatch):
    """Board outline from the PCB file (DXF body width 34.5): +1.0 mm must make LOCKED_INTERFACE.md stale (the fit check reads the board copy at import)."""
    import board_facts as BF
    real = BF.facts

    def mutated():
        d = dict(real())
        d["board_w"] = d["board_w"] + 1.0
        return d
    monkeypatch.setattr(BF, "facts", mutated)
    assert _locked_stale()

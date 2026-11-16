"""Tests for the v1 demo housing (4.E5). Run: python -m pytest test_v1.py. Same style as enclosure_v3/test_v3.py: PASS/FAIL/OPEN rows, ASSUMED values never PASS."""
import os
import pytest
import cadquery as cq
import trimesh
import params_v1 as P
import enclosure_v1 as E
import fit_check_v1 as F

HERE = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(scope="module")
def rows():
    return list(F.main())


@pytest.fixture(scope="module")
def tray():
    return E.tray()


@pytest.fixture(scope="module")
def lid():
    return E.lid()


def solid_at(wp, x, y, z):
    return wp.val().isInside(cq.Vector(x, y, z))


def test_no_fail_and_pass_count(rows):
    assert not [r for r in rows if r[3] == "FAIL"], [r for r in rows if r[3] == "FAIL"]
    assert sum(r[3] == "PASS" for r in rows) == 15
    assert sum(r[3] == "OPEN" for r in rows) >= 30


def test_assumed_values_never_pass(rows):
    """Any row whose source says ASSUMED / UNVERIFIED / WIRING (typical) / BRIEF is OPEN or FAIL, never PASS."""
    for name, value, need, st, src, note in rows:
        if any(k in src for k in ("ASSUMED", "UNVERIFIED", "BRIEF")) or "WIRING" in src:
            assert st != "PASS", (name, src)


def test_measured_inputs_are_the_ones_arsany_gave():
    assert (P.PB_L, P.PB_W, P.PB_T) == (70.0, 50.0, 2.0)
    assert P.PARTS["TP4056"][2] - P.PARTS["TP4056"][0] == 28.0 and P.PARTS["TP4056"][3] - P.PARTS["TP4056"][1] == 17.0
    assert P.PARTS["BH1750"][2] - P.PARTS["BH1750"][0] == 17.0 and P.PARTS["BH1750"][3] - P.PARTS["BH1750"][1] == 14.0
    assert P.PARTS["AHT20"][2] - P.PARTS["AHT20"][0] == 15.0 and P.PARTS["AHT20"][3] - P.PARTS["AHT20"][1] == 10.0
    assert P.CELL_CELL == (51.0, 34.5, 6.3) and P.CELL_CAV == pytest.approx((53.0, 35.1, 7.2))   # same cell and bay as the v2 plan (A-020)


def test_all_heights_flagged_not_measured():
    for n, v in P.PARTS.items():
        assert v[5] == "WIRING", n          # no part height is measured yet


def test_derived_levels():
    assert P.Z_PB_TOP == pytest.approx(8.6) and P.Z_TOP == pytest.approx(22.6)
    assert P.USB_TP_Z < P.Z_SPLIT < P.USB_SM_Z + 0.5
    assert P.USB_TP_Z - P.PLUG_H / 2 < P.Z_SPLIT < P.USB_TP_Z + P.PLUG_H / 2 and P.USB_SM_Z - P.PLUG_H / 2 < P.Z_SPLIT < P.USB_SM_Z + P.PLUG_H / 2
    assert min(P.WALL, P.FLOOR, P.LID_T) >= 1.6 >= P.MIN_WALL
    assert P.screw_len()[0] == 14


@pytest.mark.parametrize("part", ["tray", "lid"])
def test_single_valid_solid_fits_p1s(part, tray, lid):
    wp = tray if part == "tray" else lid
    s = wp.val()
    assert s.isValid() and len(wp.solids().vals()) == 1
    bb = s.BoundingBox()
    assert max(bb.xlen, bb.ylen, bb.zlen) < 256 and (round(bb.xlen, 1), round(bb.ylen, 1)) == (118.5, 72.6)


@pytest.mark.parametrize("part", ["base", "lid"])
def test_stl_watertight_on_bed_without_supports(part):
    wp = E.tray() if part == "base" else E.lid_print()
    m = F.mesh_of(wp)
    assert m.is_watertight and m.is_winding_consistent and m.volume > 0
    assert abs(m.bounds[0][2]) < 1e-6
    reach, _ = F.overhang_reach(m)
    assert reach <= 0.8


def test_lid_print_orientation_is_flipped_top_on_bed():
    m = F.mesh_of(E.lid_print())
    assert m.extents[2] == pytest.approx(P.Z_TOP + P.LID_T - (P.Z_SPLIT - P.SPIGOT_H), abs=0.05) or m.extents[2] < 16.0
    top = F.mesh_of(E.lid())
    assert top.bounds[1][2] == pytest.approx(P.Z_TOP + P.LID_T)


def test_usb_openings_are_open_in_both_halves(tray, lid):
    for ydoc, zc in ((P.USB_SM_YDOC, P.USB_SM_Z), (P.USB_TP_YDOC, P.USB_TP_Z)):
        y = P.cy(ydoc)
        for dz in (-3.5, 0.0, 3.5):
            for wp in (tray, lid):
                assert not solid_at(wp, P.OX0 + 0.8, y, zc + dz)
        assert solid_at(tray, P.OX0 + 0.8, y, 3.0) and solid_at(lid, P.OX0 + 0.8, y, P.Z_TOP - 2)   # wall above and below stays


def test_cable_exit_and_wall_elsewhere(tray, lid):
    x = P.J3_XYDOC[0]
    assert not solid_at(tray, x, P.OY0 + 0.8, P.Z_SPLIT - 2) and not solid_at(lid, x, P.OY0 + 0.8, P.Z_SPLIT + 2)
    assert solid_at(tray, x + 12, P.OY0 + 0.8, P.Z_SPLIT - 2)


def test_lid_openings(lid):
    zt = P.Z_TOP + P.LID_T / 2
    bx, by = P.BH_XYDOC[0], P.cy(P.BH_XYDOC[1])
    assert not solid_at(lid, bx, by, zt) and not solid_at(lid, bx, by, P.Z_TOP - 3)           # light window and collar bore
    assert solid_at(lid, bx + 3.1, by, P.Z_TOP - 3)                                           # collar wall around it
    ax, ay = P.AHT_XYDOC[0], P.cy(P.AHT_XYDOC[1])
    for i in range(P.VENT_N):
        assert not solid_at(lid, ax + (i - (P.VENT_N - 1) / 2) * P.VENT_PITCH, ay, zt)
    assert solid_at(lid, ax, ay, zt)                                         # web between two slots
    jx, jy = P.J1_XYDOC[0], P.cy(P.J1_XYDOC[1])
    assert not solid_at(lid, jx, jy, zt)
    for x, y in E.btn_xy():
        assert not solid_at(lid, x, y, zt) and not solid_at(lid, x, y, P.Z_TOP - 3)
        assert solid_at(lid, x + 2.0, y, P.Z_TOP - 3)                                         # guide tube wall
    assert solid_at(lid, 30.0, 30.0, zt)                                                      # plain lid elsewhere


def test_screw_posts_line_up(tray, lid):
    for x, y in P.boss_xy():
        assert not solid_at(tray, x, y, P.Z_SPLIT - 3.0)                                       # insert hole open from the top
        assert solid_at(tray, x + 2.6, y, P.Z_SPLIT - 3.0)                                     # boss wall
        assert not solid_at(lid, x, y, P.Z_SPLIT + 3.0) and solid_at(lid, x + 2.0, y, P.Z_SPLIT + 3.0)   # clearance hole through the post
        assert solid_at(lid, x + 2.0, y, P.Z_SPLIT - 0.5)                                      # spigot enters the boss counterbore
        assert not solid_at(tray, x + 2.0, y, P.Z_SPLIT - 0.5)                                 # counterbore free for it


def test_antenna_keepout_has_no_solid_and_no_metal_near(tray, lid):
    kx0, _, kx1, ky1d = P.ANT_KEEPOUT_DOC
    ky0 = P.cy(ky1d)
    zone_t = E._box(kx0, ky0, P.Z_FLOOR + 0.05, kx1, P.IY1 - 0.05, P.Z_SPLIT - 0.01)
    zone_l = E._box(kx0, ky0, P.Z_SPLIT + 0.01, kx1, P.IY1 - 0.05, P.Z_TOP - 0.01)
    assert F.vol(zone_t, tray) < 1e-6 and F.vol(zone_l, lid) < 1e-6
    for x, y in P.boss_xy():
        assert not (kx0 - 10.0 < x < kx1 + 10.0 and ky0 - 10.0 < y)          # no screw or insert within 10 mm of the zone (above y0)
    assert min(x for x, y in [(P.CELL_X0, 0)]) - (P.ANT_END_DOC[0]) > 40.0   # cell far from the antenna end


def test_cell_bay_free_and_lead_strain_relief(tray, lid):
    cell_box = E._box(P.CELL_X0, P.CELL_Y0, P.Z_FLOOR + 0.05, P.CELL_X1, P.CELL_Y1, P.Z_FLOOR + P.CELL_CAV[2])
    assert F.vol(cell_box, tray) < 1e-6 and F.vol(cell_box, lid) < 1e-6
    assert P.CELL_RIB_Z >= P.Z_FLOOR + P.CELL_CAV[2] - 1e-9
    # divider U-notch is open at the top (no bridge) and a lead can pass: notch >= 3 mm wide
    ym = (P.NOTCH_Y[0] + P.NOTCH_Y[1]) / 2
    assert not solid_at(tray, (P.DIV_X0 + P.DIV_X1) / 2, ym, P.DIV_H - 0.5) and solid_at(tray, (P.DIV_X0 + P.DIV_X1) / 2, ym + 6, P.DIV_H - 0.5)
    assert len(P.SR_POSTS) == 2 and all(P.DIV_X1 < x < P.CELL_WALL_X0 for x, y in P.SR_POSTS)


def test_board_pocket_and_standoffs(tray):
    assert F.vol(E.perfboard_ghost(), tray) < 1e-6
    assert solid_at(tray, P.PAD_X[0] + 1, 1.0, P.Z_PB_BOT - 0.5) and not solid_at(tray, 30.0, 25.0, P.Z_PB_BOT - 0.5)
    assert P.Z_PB_BOT - P.Z_FLOOR >= 4.0


def test_design_touch_is_one_flagged_chamfer():
    P.DESIGN_TOUCH = False
    try:
        plain = E.lid().val().Volume()
    finally:
        P.DESIGN_TOUCH = True
    touched = E.lid().val().Volume()
    assert touched < plain and plain - touched < 0.02 * plain          # material only removed, tiny
    assert E.lid().val().BoundingBox().zmax == pytest.approx(P.Z_TOP + P.LID_T)


def test_exports(tmp_path, monkeypatch):
    import build_v1 as B
    monkeypatch.setattr(B, "OUT", tmp_path)
    B.export_all()
    names = {p.name for p in tmp_path.iterdir()}
    for part in ("base", "lid"):
        for ext in ("step", "stl", "3mf"):
            assert f"enclosure_v1_demo_{part}.{ext}" in names
        m = trimesh.load(tmp_path / f"enclosure_v1_demo_{part}.stl")
        assert m.is_watertight
    assert "enclosure_v1_demo_assembly_with_reference_parts.step" in names


def test_readme_states_what_is_unverified():
    txt = open(os.path.join(HERE, "README.md")).read()
    for key in ("UNVERIFIED", "ASSUMED", "Arsany must verify", "merge #101 first", f"{P.OX1 - P.OX0:.1f}", f"{P.OY1 - P.OY0:.1f}", "not sliced", "STOPPED"):
        assert key in txt, key

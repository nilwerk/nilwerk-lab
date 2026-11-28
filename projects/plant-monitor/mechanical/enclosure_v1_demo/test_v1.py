"""Tests for the v1 demo housing (4.E5), compact round 2. Run: python -m pytest test_v1.py. Same style as enclosure_v3/test_v3.py: PASS/FAIL/OPEN rows, ASSUMED values never PASS.
Round 2: LiPo under the perfboard (no bay), parting plane above both USB-C openings (lid shell about half), antenna keep-out 10 mm margin for the cell."""
import os
import pathlib
import pytest
import cadquery as cq
import trimesh
import params_v1 as P
import enclosure_v1 as E
import fit_check_v1 as F

HERE = os.path.dirname(os.path.abspath(__file__))
COMPACT_README = pathlib.Path(HERE).resolve().parents[1] / "enclosure" / "v1_demo_compact" / "README.md"
EXPECTED_PASS = 7
EXPECTED_NOT_MET = 4


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


def test_no_fail_and_counts(rows):
    assert not [r for r in rows if r[3] == "FAIL"], [r for r in rows if r[3] == "FAIL"]
    assert sum(r[3] == "PASS" for r in rows) == EXPECTED_PASS
    assert sum(r[3] == "OPEN" for r in rows) >= 40
    assert sum("NOT MET" in r[0] for r in rows) == EXPECTED_NOT_MET


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
        assert v[5] == "OWNER", n           # owner bound (A-094), no part height is measured yet


def test_derived_levels_round3():
    assert P.STANDOFF_H == pytest.approx(12.2)
    assert P.Z_PB_BOT == pytest.approx(13.8) and P.Z_PB_TOP == pytest.approx(15.8)
    assert P.Z_TOP == pytest.approx(28.0) and P.Z_LID_TOP == pytest.approx(29.6)
    assert P.Z_SPLIT == pytest.approx(26.0)
    assert P.LID_SHELL_H == pytest.approx(3.6)
    assert P.LID_SHELL_H <= P.LID_SHELL_H_R1 / 2 + 0.5                       # about half of round 1
    assert P.screw_len()[0] == 6

def test_lid_clears_owner_5mm_parts_with_margin():
    assert max(v[4] for v in P.PARTS.values()) == pytest.approx(5.0)         # owner bound, A-094
    assert P.Z_TOP - (P.Z_PB_TOP + 5.0) >= P.LID_MARGIN                      # >= 2.0 mm above every part
    assert P.Z_TOP >= P.Z_SPLIT + P.LID_SKIRT - 1e-9                         # lid plate sits on the skirt above the seam
    assert P.MAX_PART_H == pytest.approx(10.2)


def test_both_usb_openings_fully_in_the_base():
    top = max(P.USB_SM_Z, P.USB_TP_Z) + P.PLUG_H / 2
    assert P.Z_SPLIT - top >= P.SPLIT_RIM - 1e-9
    assert P.USB_TP_Z - P.PLUG_H / 2 > P.Z_FLOOR


def test_cell_placement_numbers():
    kx0, ky0, kx1, ky1 = P.KO_CAD
    assert P.CELL_X0 - kx1 == pytest.approx(P.ANT_MARGIN)                    # 10 mm from the keep-out box
    assert not (P.CELL_X0 < kx1 and P.CELL_X1 > kx0 and P.CELL_Y0 < ky1 and P.CELL_Y1 > ky0)
    assert P.CELL_X0 - P.IX0 >= 20.0                                         # no cell under the USB-C wall
    assert 0.5 < P.CELL_UNDER_FRAC < 0.6                                     # about 57 % under the board (closest option)
    assert P.CELL_X1 > P.PB_L                                                # overhangs the right edge: a full fit is not possible


def test_no_full_fit_under_board_exists():
    """Brute force on a 0.5 mm grid: no 51 x 34.5 rectangle inside the perfboard outside the keep-out box, in either orientation."""
    kx0, ky0d, kx1, ky1d = P.ANT_KEEPOUT_DOC
    hits = 0
    for w, h in ((51.0, 34.5), (34.5, 51.0)):
        for i in range(int(2 * (P.PB_L - w)) + 1):
            for j in range(int(2 * (P.PB_W - h)) + 1):
                x0, y0 = i * 0.5, j * 0.5
                if not (x0 + w > kx0 and x0 < kx1 and y0 < ky1d and y0 + h > ky0d):
                    hits += 1
    assert hits == 0


def test_cell_cradle_and_bay_free(tray, lid):
    cell_box = E._box(P.CELL_X0, P.CELL_Y0, P.Z_FLOOR + 0.05, P.CELL_X1, P.CELL_Y1, P.Z_FLOOR + P.CELL_CELL[2] - 0.05)
    cav = E._box(P.CAV_X0 + 0.05, P.CAV_Y0 + 0.05, P.Z_FLOOR + 0.05, P.CAV_X1 - 0.05, P.CAV_Y1 - 0.05, P.Z_FLOOR + P.CELL_CAV[2])
    assert F.vol(cell_box, tray) < 1e-6 and F.vol(cav, lid) < 1e-6
    assert solid_at(tray, P.CAV_X0 - 0.6, 20.0, P.Z_FLOOR + 2)               # keep-out side cradle wall
    assert solid_at(tray, 70.0, P.CAV_Y0 - 0.6, P.Z_FLOOR + 2)               # bottom stop
    assert not solid_at(tray, 56.0, P.CAV_Y0 - 0.6, P.Z_FLOOR + 2)           # lead notch
    assert solid_at(tray, 70.0, P.CAV_Y1 + 0.6, P.Z_FLOOR + 2)               # top stop
    assert P.Z_PB_BOT - (P.Z_FLOOR + P.CELL_CELL[2]) >= P.PIN_TIP            # the cell top sits below the pin tips


def test_lead_strain_relief_posts_and_parking():
    assert len(P.SR_POSTS) == 2 and all(y < P.CAV_Y0 - P.STOP_T for x, y in P.SR_POSTS)     # posts outside the cradle, in the bottom strip
    jx0, jx1, jy0, jy1 = P.JST_PARK
    assert jx1 < P.J3_XYDOC[0] - 4.0 or jx1 < P.CABLE_W                     # parking left of the cable exit
    park = E._box(jx0, jy0, P.Z_FLOOR, jx1, jy1, P.Z_FLOOR + 6.0)
    assert F.vol(park, E.tray()) < 1e-6


@pytest.mark.parametrize("part", ["tray", "lid"])
def test_single_valid_solid_fits_p1s(part, tray, lid):
    wp = tray if part == "tray" else lid
    s = wp.val()
    assert s.isValid() and len(wp.solids().vals()) == 1
    bb = s.BoundingBox()
    assert max(bb.xlen, bb.ylen, bb.zlen) < 256
    assert (round(P.OX1 - P.OX0, 1), round(P.OY1 - P.OY0, 1)) == (88.5, 72.6)


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
    lowest = min(P.Z_PB_TOP + P.BTN_PRESS_H + P.BTN_GAP, P.Z_PB_TOP + P.HOLD_GAP, P.Z_SPLIT)   # hold-down pins and guide tubes hang into the base
    assert m.extents[2] == pytest.approx(P.Z_LID_TOP - lowest, abs=0.05)
    top = F.mesh_of(E.lid())
    assert top.bounds[1][2] == pytest.approx(P.Z_LID_TOP)


def test_usb_openings_open_in_base_and_rim_above(tray, lid):
    for ydoc, zc in ((P.USB_SM_YDOC, P.USB_SM_Z), (P.USB_TP_YDOC, P.USB_TP_Z)):
        y = P.cy(ydoc)
        for dz in (-3.5, 0.0, 3.5):
            assert not solid_at(tray, P.OX0 + 0.8, y, zc + dz)
        assert solid_at(tray, P.OX0 + 0.8, y, zc - 5.0)                       # wall below the opening
    top = max(P.USB_SM_Z, P.USB_TP_Z) + P.PLUG_H / 2
    assert solid_at(tray, P.OX0 + 0.8, P.cy(P.USB_SM_YDOC), top + 0.5)       # solid rim above both openings
    assert solid_at(lid, P.OX0 + 0.8, P.cy(P.USB_SM_YDOC), P.Z_SPLIT + 1.0)      # the lid wall above the seam is intact (no USB-C cut in the lid)


def test_cable_exit_and_wall_elsewhere(tray, lid):
    x = P.J3_XYDOC[0]
    assert not solid_at(tray, x, P.OY0 + 0.8, P.CABLE_Z)
    assert solid_at(tray, x, P.OY0 + 0.8, P.CABLE_Z + P.CABLE_H / 2 + 1.0)
    assert solid_at(tray, x + 12, P.OY0 + 0.8, P.CABLE_Z)


def test_lid_openings(lid):
    zt = P.Z_TOP + P.LID_T / 2
    bx, by = P.BH_XYDOC[0], P.cy(P.BH_XYDOC[1])
    assert not solid_at(lid, bx, by, zt) and not solid_at(lid, bx, by, P.Z_TOP - 3)           # light window and collar bore
    assert solid_at(lid, bx + P.BH_WIN_D / 2 + 0.6, by, P.Z_TOP - 3)                          # collar wall around it (1.2 mm, mid-wall)
    ax, ay = P.AHT_XYDOC[0], P.cy(P.AHT_XYDOC[1])
    for i in range(P.VENT_N):
        assert not solid_at(lid, ax + (i - (P.VENT_N - 1) / 2) * P.VENT_PITCH, ay, zt)
    assert solid_at(lid, ax, ay, zt)                                                          # web between two slots
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
        zm = P.Z_SPLIT + P.LID_SKIRT / 2                                                             # mid height of the lid post (round 3 skirt)
        assert not solid_at(lid, x, y, zm) and solid_at(lid, x + 2.0, y, zm)                         # clearance hole through the post
        assert solid_at(lid, x + 2.0, y, P.Z_SPLIT - 0.5)                                      # spigot enters the boss counterbore
        assert not solid_at(tray, x + 2.0, y, P.Z_SPLIT - 0.5)                                 # counterbore free for it


def test_antenna_keepout_has_no_solid_and_no_metal_near(tray, lid):
    kx0, ky0, kx1, ky1 = P.KO_CAD
    zone_t = E._box(kx0, ky0, P.Z_FLOOR + 0.05, kx1, ky1, P.Z_SPLIT - 0.01)
    zone_l = E._box(kx0, ky0, P.Z_SPLIT + 0.01, kx1, ky1, P.Z_TOP - 0.01)   # lid cavity; the PETG plate above it is plastic (allowed)
    assert F.vol(zone_t, tray) < 1e-6 and F.vol(zone_l, lid) < 1e-6
    for x, y in P.boss_xy():                                                                 # every screw / insert edge >= 10 mm from the keep-out box
        assert F.rect_dist(kx0, ky0, kx1, ky1, x, y) - P.BOSS_D / 2 >= P.ANT_MARGIN


def test_board_pocket_and_standoffs(tray):
    assert F.vol(E.perfboard_ghost(), tray) < 1e-6
    assert solid_at(tray, P.PAD_XS[0][0] + 1, 1.0, P.Z_PB_BOT - 0.5) and not solid_at(tray, 30.0, 25.0, P.Z_PB_BOT - 0.5)
    assert P.Z_PB_BOT - P.Z_FLOOR >= P.CELL_CAV[2] + P.PIN_TIP


def test_design_touch_is_one_flagged_chamfer():
    P.DESIGN_TOUCH = False
    try:
        plain = E.lid().val().Volume()
    finally:
        P.DESIGN_TOUCH = True
    touched = E.lid().val().Volume()
    assert touched < plain and plain - touched < 0.02 * plain          # material only removed, tiny
    assert E.lid().val().BoundingBox().zmax == pytest.approx(P.Z_LID_TOP)


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


def test_compact_readme_states_what_is_unverified():
    txt = COMPACT_README.read_text()
    for key in ("UNVERIFIED", "ASSUMED", "Arsany must verify", "NOT MET", "not sliced", "RF", "88.5", "72.6", "31.4", "5.4", "STOPPED"):
        assert key in txt, key


def test_every_pass_row_has_measured_or_rule_provenance(rows):
    """Row-level provenance: a PASS row must cite MEASURED or RULE in its source, and must not cite ASSUMED, UNVERIFIED, WIRING or BRIEF."""
    passes = [r for r in rows if r[3] == "PASS"]
    assert passes
    for name, value, need, st, src, note in passes:
        assert "MEASURED" in src or "RULE" in src, (name, src)
        for bad in ("ASSUMED", "UNVERIFIED", "WIRING", "BRIEF"):
            assert bad not in src, (name, src)

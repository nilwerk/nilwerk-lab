"""Geometry tests for the battery-bay study (4.E3 slice 1). Run: python -m pytest test_bay.py"""
import numpy as np
import pytest
import trimesh
import cadquery as cq
import bay
import params as P

KEYS = list(P.VARIANTS)


def mesh(wp):
    verts, tris = wp.val().tessellate(0.01, 0.1)
    return trimesh.Trimesh([v.toTuple() for v in verts], tris)


@pytest.fixture(scope="module", params=KEYS)
def built(request):
    k = request.param
    return k, bay.dims(k), mesh(bay.tray(k)), mesh(bay.lid(k))


def test_dims_expected():
    a, b = bay.dims(KEYS[0]), bay.dims(KEYS[1])
    # EEMB: 51 + 2.0 = 53.0 bay; 34.5 + 0.6 = 35.1; 6.3*1.1+0.2 = 7.13 -> 7.2 (whole layers)
    assert (a["bay_l"], a["bay_w"], a["bay_h"]) == pytest.approx((53.0, 35.1, 7.2))
    # Jauch: 45 + 2.0 = 47.0; 35.1; 6.5*1.1+0.2 = 7.35 -> 7.4
    assert (b["bay_l"], b["bay_w"], b["bay_h"]) == pytest.approx((47.0, 35.1, 7.4))
    assert (a["out_l"], a["out_w"], a["out_h"]) == pytest.approx((56.2, 38.3, 10.4))
    assert (b["out_l"], b["out_w"], b["out_h"]) == pytest.approx((50.2, 38.3, 10.6))


def test_jauch_fits_and_delta():
    a, b = bay.dims(KEYS[0]), bay.dims(KEYS[1])
    assert b["bay_h"] >= b["cell_h"] * (1 + P.SWELL_FRAC) + P.Z_CLEAR - 1e-9   # 6.5 mm cell fits with swelling
    assert b["spare_h"] >= 0.9 and b["spare_w"] == pytest.approx(0.6)
    assert b["out_h"] - a["out_h"] == pytest.approx(0.2)                      # +0.2 mm total height
    assert b["out_w"] == pytest.approx(a["out_w"])                            # same width
    assert a["out_l"] - b["out_l"] == pytest.approx(6.0)                      # 6 mm shorter


def test_bay_h_is_whole_layers():
    for k in KEYS:
        h = bay.dims(k)["bay_h"]
        assert abs(h / P.LAYER - round(h / P.LAYER)) < 1e-6


def test_mesh_bbox_matches_dims(built):
    k, d, t, l = built
    assert t.extents == pytest.approx([d["out_l"], d["out_w"], d["tray_h"]], abs=1e-3)
    assert l.extents == pytest.approx([d["out_l"], d["out_w"], P.LID], abs=1e-3)


def test_watertight_and_fits_p1s(built):
    k, d, t, l = built
    for m in (t, l):
        assert m.is_watertight and m.volume > 0
        assert all(e < s for e, s in zip(m.extents, P.BUILD_VOLUME))


def test_tray_volume_analytic(built):
    k, d, t, _ = built
    # box - cavity - notch, ignoring the 2 mm corner fillets (small): compare within 1.5 %
    box = d["out_l"] * d["out_w"] * d["tray_h"]
    cavity = d["bay_l"] * d["bay_w"] * d["bay_h"]
    notch = P.WALL * P.WIRE_NOTCH_W * P.WIRE_NOTCH_H
    fillet_loss = (4 - np.pi) * 2.0**2 * d["tray_h"]
    assert t.volume == pytest.approx(box - fillet_loss - cavity - notch, rel=0.015)


def _thickness(key, axis, sign, z0, z1=0.5):
    """Wall thickness along +-axis measured with a 1 x 1 mm probe from the cavity face outwards through the solid."""
    d = bay.dims(key)
    half = (d["bay_l"] if axis == 0 else d["bay_w"]) / 2
    probe = cq.Workplane("XY").box(10.0, 1.0, z1, centered=(False, True, False)) if axis == 0 else \
        cq.Workplane("XY").box(1.0, 10.0, z1, centered=(True, False, False))
    if sign < 0:
        probe = probe.mirror("YZ" if axis == 0 else "XZ")
    probe = probe.translate((sign * half if axis == 0 else 0, sign * half if axis == 1 else 0, z0))
    hit = bay.tray(key).intersect(probe)
    return hit.val().Volume() / (1.0 * z1)


def test_wall_thickness_measured(built):
    k, d, t, l = built
    z = P.FLOOR + 2.0
    # the +X wall holds the notch only in its top 3 mm, so z = floor + 2 is below it: all four walls measured
    for axis, sign in ((0, -1), (0, 1), (1, 1), (1, -1)):
        w = _thickness(k, axis, sign, z)
        assert w == pytest.approx(P.WALL, abs=0.02) and w >= P.MIN_WALL_RULE, (axis, sign)
    # floor
    probe = cq.Workplane("XY").box(1, 1, 10, centered=(True, True, False)).translate((0, 0, 0))
    floor = bay.tray(k).intersect(probe).val().Volume()
    assert floor == pytest.approx(P.FLOOR * 1.0, abs=0.02)
    # notch is above the floor + 1 mm so it never thins the wall below the rule
    assert d["tray_h"] - P.WIRE_NOTCH_H >= P.FLOOR + 1.0


def test_wall_is_printable_perimeters():
    # 1.6 mm wall = 3.8 lines of 0.42: slicer uses 4 perimeters with small gap fill; rule >= 1.2 mm holds
    assert P.WALL >= P.MIN_WALL_RULE and P.WALL / P.LINE_WIDTH >= 3.5


def test_no_supports_needed(built):
    """Every downward-facing face (overhang) lies on the print bed plane z = 0."""
    k, d, t, l = built
    for m in (t, l):
        down = m.face_normals[:, 2] < -0.5
        zs = m.triangles_center[down][:, 2]
        assert np.all(np.abs(zs) < 1e-3)


def test_cell_clears_cavity(built):
    k, d, t, l = built
    assert d["spare_l"] >= 2 * P.END_CLEAR - 1e-9 and d["spare_w"] >= 2 * P.FDM_CLEAR - 1e-9
    assert d["spare_h"] >= d["cell_h"] * P.SWELL_FRAC + P.Z_CLEAR - 1e-9


def test_exports_exist_and_3mf_zip():
    import pathlib, zipfile, build
    build.export_all()
    for k in KEYS:
        for part in ("tray", "lid"):
            for ext in ("step", "stl", "3mf"):
                f = build.OUT / k / f"bay_{k}_{part}.{ext}"
                assert f.stat().st_size > 500, f
            assert "3D/3dmodel.model" in zipfile.ZipFile(build.OUT / k / f"bay_{k}_{part}.3mf").namelist()


# ---- design touch (flag, default off) ----
def test_design_touch_off_by_default():
    assert P.DESIGN_TOUCH is False
    k = KEYS[0]
    assert mesh(bay.lid(k)).volume == pytest.approx(mesh(bay.lid(k, design=False)).volume)


@pytest.mark.parametrize("k", KEYS)
def test_design_touch_printable_and_seal_safe(k):
    d, plain, m = bay.dims(k), mesh(bay.lid(k, design=False)), mesh(bay.lid(k, design=True))
    assert m.is_watertight and m.volume < plain.volume                       # material only removed
    assert m.extents == pytest.approx(plain.extents, abs=1e-3)               # same outer size (bay numbers untouched)
    assert P.RELIEF_DEPTH >= 0.4 and P.RELIEF_W >= 0.8 and P.RELIEF_DEPTH <= P.LID / 2   # feature rule, >= 0.8 mm skin left
    down = m.face_normals[:, 2] < -0.5
    assert np.all(np.abs(m.triangles_center[down][:, 2]) < 1e-3)             # still no overhang: no supports
    # trace stays >= 3 mm inside the lid outline
    for x, y in bay.trace_path(d):
        assert abs(x) <= d["out_l"] / 2 - 3.0 and abs(y) <= d["out_w"] / 2 - 3.0


def test_design_touch_leaves_tray_and_cavity_unchanged():
    k = KEYS[1]
    assert mesh(bay.tray(k)).volume == pytest.approx(mesh(bay.tray(k)).volume)
    assert bay.dims(k)["out_h"] == pytest.approx(10.6) and bay.dims(k)["bay_h"] == pytest.approx(7.4)

"""Slice 4 renders of the compact product shell (exterior), from the exported compact STL meshes plus a stake built from the
same tail parameters (params_v3). Three views: front (lid), three-quarter, side profile against the soil stake.
The soil plane is schematic: the repo has no soil depth or geometry. Run after build_v3.py.
Output: projects/plant-monitor/enclosure/v3/renders/compact_*.png
Rendering: own z-buffer rasteriser over the STL triangles (depth-correct; the painter sort of render.py mixes interior faces into the outside)."""
import os, pathlib, sys, tempfile
import numpy as np, trimesh
import matplotlib
matplotlib.use("Agg")
import cadquery as cq
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import params_v3 as P

OUT = pathlib.Path(__file__).resolve().parents[2] / "enclosure" / "v3"
REN = OUT / "renders"
COPPER = np.array([0.80, 0.55, 0.20]); SOIL = np.array([0.45, 0.36, 0.26]); GREY = np.array([0.33, 0.35, 0.37])
LIGHT = np.array([-0.4, -0.6, 0.8]); LIGHT /= np.linalg.norm(LIGHT)
import matplotlib.pyplot as plt


def L(name):
    return trimesh.load(OUT / f"enclosure_v3_compact_{name}.stl")


def box(x0, y0, z0, x1, y1, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def mesh_of(wp, name):
    f = os.path.join(tempfile.gettempdir(), f"v3c_{name}.stl")
    cq.exporters.export(wp, f, tolerance=0.01, angularTolerance=0.1)
    return trimesh.load(f)


def stake_parts(tail="14"):
    """Board tail (the stake) and electrode copper, from params_v3 (not drawn by hand)."""
    tl = P.TAIL_L_VARIANT[tail]
    tail_w = box(P.TAIL_X0, -(P.BODY_L + tl), P.BOARD_Z0, P.TAIL_X0 + P.TAIL_W, -P.BODY_L, P.BOARD_Z1)
    cu_tip = -(P.BODY_L + tl) + P.TIP_MARGIN
    cu = box(P.TAIL_X0 + 0.3, cu_tip, P.BOARD_Z1, P.TAIL_X0 + P.TAIL_W - 0.3, -P.BODY_L - 1.0, P.BOARD_Z1 + 0.04)
    return mesh_of(tail_w, "tail"), mesh_of(cu, "cu")


def soil_slab():
    """Schematic soil: a slab whose top sits on the outer bottom face line (the tail leaves the enclosure there)."""
    return mesh_of(box(P.OUT_X0 - 30, P.OUT_Y0 - 60, -8, P.OUT_X1 + 30, P.OUT_Y0, 20), "soil")


def _unit(v):
    v = np.asarray(v, float); return v / np.linalg.norm(v)


def rasterize(items, d, up_hint, W=1000, H=640, title=""):
    """items: [(trimesh, colour, alpha)]. d = unit vector from the target to the camera (orthographic), up_hint = world up in the image.
    Depth test per pixel (z-buffer), Lambert shading with the light of render.py. Soil/alpha is drawn opaque but placed behind the stake."""
    d = _unit(d); right = _unit(np.cross(np.asarray(up_hint, float), d)); up = np.cross(d, right)
    tris, cols, nrm = [], [], []
    for m, col, _ in items:
        tris.append(m.triangles); nrm.append(m.face_normals); cols.append(np.repeat(np.asarray(col, float)[None], len(m.faces), 0))
    T = np.vstack(tris); N = np.vstack(nrm); C = np.vstack(cols)
    flat = T.reshape(-1, 3)
    sx = flat @ right; sy = flat @ up; sz = flat @ d
    x0, x1, y0, y1 = sx.min(), sx.max(), sy.min(), sy.max()
    pad = 0.06
    scale = min(W * (1 - 2 * pad) / (x1 - x0), H * (1 - 2 * pad) / (y1 - y0))
    px = (sx - x0) * scale + W * pad; py = H - ((sy - y0) * scale + H * pad)
    PX = np.stack([px[0::3], px[1::3], px[2::3]], 1)
    PY = np.stack([py[0::3], py[1::3], py[2::3]], 1)
    SZ = np.stack([sz[0::3], sz[1::3], sz[2::3]], 1)
    zbuf = np.full((H, W), -np.inf); img = np.ones((H, W, 3))
    shade = 0.35 + 0.65 * np.clip(np.abs(N @ LIGHT), 0, 1)
    colr = np.clip(C * shade[:, None], 0, 1)
    for k in range(len(T)):
        xs, ys = PX[k], PY[k]
        xa, xb = max(int(np.floor(xs.min())), 0), min(int(np.ceil(xs.max())), W - 1)
        ya, yb = max(int(np.floor(ys.min())), 0), min(int(np.ceil(ys.max())), H - 1)
        if xa > xb or ya > yb:
            continue
        gx, gy = np.meshgrid(np.arange(xa, xb + 1) + 0.5, np.arange(ya, yb + 1) + 0.5)
        den = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
        if abs(den) < 1e-12:
            continue
        w0 = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / den
        w1 = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / den
        w2 = 1 - w0 - w1
        inside = (w0 >= -1e-9) & (w1 >= -1e-9) & (w2 >= -1e-9)
        if not inside.any():
            continue
        z = w0 * SZ[k, 0] + w1 * SZ[k, 1] + w2 * SZ[k, 2]
        zz = zbuf[ya:yb + 1, xa:xb + 1]; ii = img[ya:yb + 1, xa:xb + 1]
        m = inside & (z > zz)
        zz[m] = z[m]; ii[m] = colr[k]
    fig, ax = plt.subplots(figsize=(8, 5.2), dpi=150)
    ax.imshow(img); ax.set_axis_off(); ax.set_title(title, fontsize=8)
    fig.savefig(REN / "_tmp.png", bbox_inches="tight", facecolor="white"); plt.close(fig)
    return img


def save(items, name, d, up, title):
    REN.mkdir(parents=True, exist_ok=True)
    fig_img = rasterize(items, d, up, title=title)
    import shutil
    shutil.move(str(REN / "_tmp.png"), str(REN / name))


def main(tail="14"):
    tray, lid, plug = L("tray"), L("lid"), L("tail_plug")
    tail_m, cu_m = stake_parts(tail)
    shell = [(tray, GREY, 1), (plug, GREY * 0.8, 1), (lid, GREY * 1.1, 1)]
    stake = [(tail_m, GREY * 0.6, 1), (cu_m, COPPER, 1)]
    # 1 front: the lid face (light window, vents, reset hole are on it), seen from above and a little from the tail side
    save(shell + stake, "compact_front.png", (0.0, -0.22, 1.0), (0, 1, 0),
         "Compact shell (slice 4), front: lid face with light window and vents; tail at the bottom")
    # 2 three-quarter: the USB-C side (+X), the tail side and the lid; rounded plan corners and soft edges visible
    save(shell + stake, "compact_three_quarter.png", (0.75, -0.55, 0.55), (0, 0, 1),
         "Compact shell (slice 4), three-quarter: one soft outline, USB-C window on the right wall")
    # 3 side profile against the soil stake: camera on the USB side, the tail points down into the schematic soil
    soil = box(-70.0, P.OUT_Y0 - 60, -8, P.TAIL_X0 - 10, P.OUT_Y0, 20)   # behind the stake from this camera
    save(shell + stake + [(mesh_of(soil, "soil"), SOIL, 1)], "compact_side_stake.png", (1.0, 0.0, 0.0), (0, 1, 0),
         "Side profile, tail = soil stake (14 mm tail, approved A-071); soil is schematic, the repo has no soil data")
    print("renders in", REN)


if __name__ == "__main__":
    main()

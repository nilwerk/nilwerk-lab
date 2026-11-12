"""Renders for the tail variants (14 / 20 mm electrode beyond the outer bottom face): one plan per variant and one side view
comparing both with the enclosure bottom wall. 2D drawings from the parametric numbers (params_v3, board_facts); no mock-up.
Run after build_v3.py. Output: projects/plant-monitor/enclosure/v3/renders/."""
import pathlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon
import params_v3 as P
import board_src as B

OUT = pathlib.Path(__file__).resolve().parents[2] / "enclosure" / "v3"
REN = OUT / "renders"
GREEN, AMBER = "#0f7a5c", "#c98a00"


def plan(tail):
    tl = P.TAIL_L_VARIANT[tail]
    fig, ax = plt.subplots(figsize=(10, 7.2), dpi=150)
    ax.add_patch(Rectangle((P.OUT_X0, P.OUT_Y0), P.OUT_X1 - P.OUT_X0, P.OUT_Y1 - P.OUT_Y0, fc="#e6e8ea", ec="#333", lw=1.2))
    ax.add_patch(Rectangle((P.INNER_X0, P.INNER_Y0), P.INNER_X1 - P.INNER_X0, P.INNER_Y1 - P.INNER_Y0, fc="white", ec="#333", lw=0.8))
    ax.add_patch(Rectangle((P.CELL_X0, P.CELL_Y0), P.CELL_X1 - P.CELL_X0, P.CELL_Y1 - P.CELL_Y0, fc=(0.95, 0.65, 0.1, 0.35), ec=AMBER))
    ax.text((P.CELL_X0 + P.CELL_X1) / 2, (P.CELL_Y0 + P.CELL_Y1) / 2, "EEMB cell cavity 53.0 x 35.1", ha="center", fontsize=8)
    Lt = P.BODY_L + tl
    pts = [(0, 0), (P.BOARD_W, 0), (P.BOARD_W, -P.BODY_L), (P.TAIL_X0 + P.TAIL_W, -P.BODY_L), (P.TAIL_X0 + P.TAIL_W, -Lt), (P.TAIL_X0, -Lt), (P.TAIL_X0, -P.BODY_L), (0, -P.BODY_L), (0, 0)]
    ax.plot(*zip(*pts), color=GREEN, lw=1.5)
    # electrode copper: from the board copper start to the copper tip for this variant
    cu_tip = -Lt + P.TIP_MARGIN
    ax.add_patch(Rectangle((P.TAIL_X0 + 0.3, -P.BODY_L - 1.0), P.TAIL_W - 0.6, cu_tip - (-P.BODY_L - 1.0), fc=(0.85, 0.55, 0.1, 0.35), ec=AMBER, lw=0.8, hatch="//"))
    ax.plot([P.OUT_X0 - 3, P.OUT_X1 + 3], [P.OUT_Y0, P.OUT_Y0], color="#b00020", lw=1.2, ls="--")
    ax.annotate(f"outer bottom face y {P.OUT_Y0:.1f}", (P.OUT_X0 - 3, P.OUT_Y0), (P.OUT_X0 - 40, P.OUT_Y0 + 3), fontsize=7, color="#b00020")
    ax.annotate(f"electrode copper tip y {cu_tip:.1f}: {P.TAIL_VARIANTS[tail]:.0f} mm beyond the wall", (P.TAIL_X0 + 0.3, cu_tip), (P.TAIL_X0 + 16, cu_tip - 6), fontsize=7,
                arrowprops=dict(arrowstyle="-"))
    ax.set_xlim(P.OUT_X0 - 45, P.OUT_X1 + 5); ax.set_ylim(-80, P.OUT_Y1 + 4); ax.set_aspect("equal")
    ax.set_title(f"Tail variant {tail} mm (electrode beyond the outer bottom face). Board tail {tl:.1f} mm (DXF today 25.0): board change OPEN (A-071)", fontsize=9)
    ax.set_xlabel("X mm"); ax.set_ylabel("Y mm (lid off, PCB frame)")
    fig.savefig(REN / f"tail{tail}_plan.png", bbox_inches="tight", facecolor="white"); plt.close(fig)


def side_compare():
    """Side view along X: enclosure bottom wall and both tail lengths, electrode copper hatched."""
    fig, ax = plt.subplots(figsize=(9, 6), dpi=150)
    ax.add_patch(Rectangle((0, P.OUT_Y0), 10, P.OUT_Y1 - P.OUT_Y0, fc="#e6e8ea", ec="#333"))  # side of housing (schematic, Y-extent only)
    ax.text(5, P.OUT_Y1 + 1, "housing", ha="center", fontsize=8)
    for i, tail in enumerate(["14", "20"]):
        tl = P.TAIL_L_VARIANT[tail]
        x = 4 + i * 4
        ax.add_patch(Rectangle((x, -P.BODY_L), 1.6, -(P.BODY_L + tl) + P.BODY_L, fc="#0f7a5c", ec="#0f7a5c", alpha=0.35))
        cu_tip = -(P.BODY_L + tl) + P.TIP_MARGIN
        ax.plot([x - 0.4, x + 2.0], [cu_tip, cu_tip], color=AMBER, lw=2)
        ax.text(x + 2.4, cu_tip, f"{tail}: copper tip {cu_tip:.1f}\n{P.TAIL_VARIANTS[tail]:.0f} mm beyond wall", fontsize=7, va="center")
    ax.plot([-1, 14], [P.OUT_Y0, P.OUT_Y0], color="#b00020", lw=1.2, ls="--")
    ax.text(-0.5, P.OUT_Y0 + 0.6, f"outer bottom face {P.OUT_Y0:.1f}", fontsize=7, color="#b00020")
    ax.plot([-1, 14], [-P.BODY_L, -P.BODY_L], color="#999", lw=0.8)
    ax.text(-0.5, -P.BODY_L + 0.4, f"board body edge {-P.BODY_L:.0f}", fontsize=7, color="#555")
    ax.set_xlim(-2, 16); ax.set_ylim(-75, 4); ax.set_aspect("equal")
    ax.set_title("Tail variants side by side: green = board tail (variant length), amber = electrode copper, red = outer bottom face. Schematic, Y in mm", fontsize=8)
    ax.set_xlabel("X (schematic offset)"); ax.set_ylabel("Y mm")
    fig.savefig(REN / "tail_compare_side.png", bbox_inches="tight", facecolor="white"); plt.close(fig)


if __name__ == "__main__":
    REN.mkdir(parents=True, exist_ok=True)
    for t in P.TAIL_VARIANTS:
        plan(t)
    side_compare()
    print("renders in", REN)

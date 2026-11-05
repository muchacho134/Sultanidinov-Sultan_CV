"""Production-style underbody wire layout (half car, y <= 0). Dimensions taken from the STL;
structure as on a real car:
  front splitter plate  - flat plate at Z_SPLIT, leading edge = nose plan outline
  front undertray       - straight ramp from the front floor up to the splitter
  front floor | seam | main floor (flat panels, z from the STL)
  rocker                - floor edge with a R_ROCK radius into a vertical outer face up to Z_ROCK_TOP
  wheel openings        - straight edges, R_OPEN corner radii at the inner corners
  rear diffuser         - straight ramp DIFF_DEG deg from X_DIFF to the tail, 2 vertical strakes, side walls
Checks: approach / departure angle from the tyre contact points.
"""
import sys, json, numpy as np
P = json.load(open(sys.argv[1])); OUT = sys.argv[2]
X_TIP_F, X_TIP_R = -2240.0, 2240.0
Z_FF, Z_MF = 96.8, 114.5                     # front / main floor
X_STEP = (-1000.0, -950.0)                   # seam + 50 mm ramp between floor levels
X_UT0, X_UT1, Z_SPLIT = -1800.0, -1950.0, 170.0   # undertray ramp (front floor -> splitter level)
Y_SILL, Y_NOSE_SIDE, Y_TAIL_SIDE = 905.0, 935.0, 940.0
NOSE_C, NOSE_N, TAIL_C, TAIL_N = -1800.0, 1.75, 1800.0, 2.2
R_ROCK, Z_ROCK_TOP = 20.0, 260.0
R_OPEN = 30.0
X_DIFF, DIFF_DEG, Y_DIFF = 1700.0, 9.0, 760.0
STRAKES = (-250.0, -520.0)
WELL = {k: (P[k]["x"], P[k]["r"] + g, P[k]["wall"], P[k]["z"], P[k]["r"]) for k, g in (("front", 12.0), ("rear", 8.0))}


def Ye(x):
    x = np.asarray(x, float); y = np.full(x.shape, Y_SILL)
    y = np.where(x < WELL["front"][0], Y_NOSE_SIDE, y); y = np.where(x > WELL["rear"][0], Y_TAIL_SIDE, y)
    tn = np.clip((NOSE_C - x) / (NOSE_C - X_TIP_F), 0, 1); y = np.where(x < NOSE_C, Y_NOSE_SIDE * (1 - tn ** NOSE_N) ** (1 / NOSE_N), y)
    tt = np.clip((x - TAIL_C) / (X_TIP_R - TAIL_C), 0, 1); y = np.where(x > TAIL_C, Y_TAIL_SIDE * (1 - tt ** TAIL_N) ** (1 / TAIL_N), y)
    return y


def Zfloor(x):
    """Underbody height along the car (flat panels joined by straight ramps)."""
    x = np.asarray(x, float)
    z = np.where(x < X_STEP[0], Z_FF, np.where(x < X_STEP[1], Z_FF + (Z_MF - Z_FF) * (x - X_STEP[0]) / 50.0, Z_MF))
    z = np.where(x < X_UT0, Z_FF + (Z_SPLIT - Z_FF) * np.clip((X_UT0 - x) / (X_UT0 - X_UT1), 0, 1), z)
    z = np.where(x > X_DIFF, Z_MF + np.tan(np.radians(DIFF_DEG)) * (x - X_DIFF), z)
    return z


def chord(k):
    xc, rw, wall, za, rt = WELL[k]; zf = Z_FF if k == "front" else Z_MF
    return xc, np.sqrt(rw * rw - (za - zf) ** 2), wall, zf


W = {}
L = lambda *p: np.array(p, float)
xs = np.linspace(X_TIP_F, X_TIP_R, 1200)
W["centreline"] = np.c_[xs, 0 * xs, Zfloor(xs)]
# ---- splitter: leading edge (plan outline at splitter level) and its rear line
xn = np.linspace(X_TIP_F, X_UT1, 80)
W["splitter_leading_edge"] = np.c_[xn, -Ye(xn), np.full(len(xn), Z_SPLIT)]
W["splitter_rear_line"] = np.c_[np.full(40, X_UT1), np.linspace(0, -Ye(X_UT1), 40), np.full(40, Z_SPLIT)]
W["undertray_front_seam"] = np.c_[np.full(40, X_UT0), np.linspace(0, -Ye(X_UT0), 40), np.full(40, Z_FF)]
# ---- floor outline (inner edge of the rocker radius), panel seams
fc, cf, wf, zff = chord("front"); rc, cr, wr, zmf = chord("rear")
for name, x0, x1 in (("floor_edge_front", X_UT0, fc - cf), ("floor_edge_mid", fc + cf, rc - cr), ("floor_edge_rear", rc + cr, X_DIFF)):
    xx = np.linspace(x0, x1, 120); W[name] = np.c_[xx, -(Ye(xx) - R_ROCK), Zfloor(xx)]
for xv, nm in ((X_STEP[0], "seam_floor_step"), (X_STEP[1], "seam_floor_main"), (X_DIFF, "seam_diffuser")):
    yy = np.linspace(0, -(Ye(xv) - R_ROCK), 60); W[nm] = np.c_[np.full(60, xv), yy, np.full(60, Zfloor(xv))]
# ---- rocker (between the wheels): bottom of the vertical face and its top
xx = np.linspace(fc + cf, rc - cr, 120)
W["rocker_bottom"] = np.c_[xx, -Ye(xx), Zfloor(xx) + R_ROCK]
W["rocker_top"] = np.c_[xx, -Ye(xx), np.full(len(xx), Z_ROCK_TOP)]
for xv in (fc + cf, rc - cr):
    W[f"rocker_end_{int(xv)}"] = L((xv, -Ye(xv), Z_MF + R_ROCK), (xv, -Ye(xv), Z_ROCK_TOP))
# lower bumper sides ahead of the front / behind the rear wheel: outline at floor level + radius
for name, x0, x1 in (("lower_side_front", X_UT1, fc - cf), ("lower_side_rear", rc + cr, X_TIP_R - 40)):
    xx = np.linspace(x0, x1, 80); W[name] = np.c_[xx, -Ye(xx), Zfloor(xx) + R_ROCK]
# ---- wheel openings: inner edge, crosswise edges, radiused inner corners
for k in ("front", "rear"):
    xc, c, wall, zf = chord(k)
    a = np.linspace(0, np.pi / 2, 12)
    c1 = np.c_[xc - c + R_OPEN - R_OPEN * np.cos(a), -(wall + R_OPEN) + R_OPEN * np.sin(a)][::-1]   # front-inner corner
    c2 = np.c_[xc + c - R_OPEN + R_OPEN * np.sin(a), -wall - R_OPEN + R_OPEN * np.cos(a)]           # rear-inner corner
    ye_f, ye_r = Ye(xc - c - 1) - R_ROCK, Ye(xc + c + 1) - R_ROCK
    path = np.r_[[(xc - c, -ye_f)], c1[::-1], c2, [(xc + c, -ye_r)]]
    W[f"{k}_opening"] = np.c_[path, np.full(len(path), zf)]
# ---- rear diffuser: side walls, strakes (vertical fins, bottom edge at floor level)
xd = np.linspace(X_DIFF, X_TIP_R - 40, 60)
W["diffuser_side_wall_top"] = np.c_[xd, np.full(60, -Y_DIFF), Zfloor(xd)]
W["diffuser_side_wall_bottom"] = np.c_[xd, np.full(60, -Y_DIFF), np.full(60, Z_MF)]
for ys in STRAKES:
    W[f"strake_y{int(-ys)}_top"] = np.c_[xd, np.full(60, ys), Zfloor(xd)]
    W[f"strake_y{int(-ys)}_bottom"] = np.c_[xd, np.full(60, ys), np.full(60, Z_MF)]
    W[f"strake_y{int(-ys)}_end"] = L((xd[-1], ys, Z_MF), (xd[-1], ys, Zfloor(xd[-1])))
W["diffuser_rear_edge"] = np.c_[np.full(40, xd[-1]), np.linspace(0, -Y_DIFF, 40), np.full(40, Zfloor(xd[-1]))]
json.dump({k: v.tolist() for k, v in W.items()}, open(OUT, "w"))
# ---- real-world checks
af = np.degrees(np.arctan(Z_SPLIT / (WELL["front"][0] - X_TIP_F)))
dr = np.degrees(np.arctan(Zfloor(xd[-1]) / (xd[-1] - WELL["rear"][0])))
print("ground clearance: front floor %.0f, main floor %.0f mm" % (Z_FF, Z_MF))
print("approach angle %.1f deg (sports car typ. 10-14), departure angle %.1f deg (typ. 12-20)" % (af, dr))
print("diffuser: %.0f deg over %.0f mm, exit height %.0f mm" % (DIFF_DEG, xd[-1] - X_DIFF, Zfloor(xd[-1])))
print("wires:", len(W))

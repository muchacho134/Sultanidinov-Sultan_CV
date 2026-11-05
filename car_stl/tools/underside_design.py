"""Real-world underside (half car, y <= 0), defined by design parameters (measured once from the
mesh), not traced. All wires are cut from this one definition, so they meet exactly.

  centre height Zc(x): nose upsweep | front floor 96.8 | straight ramp | main floor 114.5 | straight diffuser
  plan edge   Ye(x):   superellipse nose corner | straight sill(s) | superellipse tail corner
  cross shape:         flat at Zc(x) out to Ye - RW, then a quarter-ellipse roll up to Zc + RH at Ye
  wheel openings:      straight rectangles in the floor (x = xc -/+ c, |y| > slot wall)
"""
import sys, json, numpy as np, trimesh
P = json.load(open(sys.argv[2])); OUT = sys.argv[3]
m = trimesh.load(sys.argv[1], force='mesh')

# ---------------- design parameters
X_TIP_F, X_TIP_R = -2240.0, 2240.0
Z_F, Z_M = 96.8, 114.5                    # floor levels
X_RAMP = (-1000.0, -950.0)                # floor step ramp
X_NOSE, Z_NOSE_TIP = -1800.0, 190.0       # nose upsweep starts / tip height
X_DIFF, DIFF_DEG = 1750.0, 10.0           # diffuser start, angle
Y_SILL, Y_NOSE_SIDE, Y_TAIL_SIDE = 905.0, 935.0, 940.0
NOSE_C, NOSE_N = -1800.0, 1.75            # nose plan corner: superellipse from x = NOSE_C to the tip
TAIL_C, TAIL_N = 1800.0, 2.2
RW, RH = 90.0, 150.0                      # edge roll: width, height
WELL = {k: (P[k]["x"], P[k]["r"] + g, P[k]["wall"], P[k]["z"]) for k, g in (("front", 12.0), ("rear", 8.0))}


def Zc(x):
    x = np.asarray(x, float)
    z = np.where(x < X_RAMP[0], Z_F, np.where(x < X_RAMP[1], Z_F + (Z_M - Z_F) * (x - X_RAMP[0]) / (X_RAMP[1] - X_RAMP[0]), Z_M))
    t = np.clip((X_NOSE - x) / (X_NOSE - X_TIP_F), 0, 1)
    z = np.where(x < X_NOSE, Z_F + (Z_NOSE_TIP - Z_F) * t ** 2, z)            # nose upsweep (tangent to the floor)
    z = np.where(x > X_DIFF, Z_M + np.tan(np.radians(DIFF_DEG)) * (x - X_DIFF), z)   # straight diffuser
    return z


def Ye(x):
    """Plan edge |y| (positive number)."""
    x = np.asarray(x, float)
    y = np.full(x.shape, Y_SILL)
    y = np.where(x < WELL["front"][0], Y_NOSE_SIDE, y)
    y = np.where(x > WELL["rear"][0], Y_TAIL_SIDE, y)
    tn = np.clip((NOSE_C - x) / (NOSE_C - X_TIP_F), 0, 1)
    y = np.where(x < NOSE_C, Y_NOSE_SIDE * (1 - tn ** NOSE_N) ** (1 / NOSE_N), y)
    tt = np.clip((x - TAIL_C) / (X_TIP_R - TAIL_C), 0, 1)
    y = np.where(x > TAIL_C, Y_TAIL_SIDE * (1 - tt ** TAIL_N) ** (1 / TAIL_N), y)
    return y


def Z(x, y):
    """Underside height at (x, y <= 0)."""
    ay = np.abs(y); ye = Ye(x); zc = Zc(x)
    rw = np.minimum(RW, 0.9 * ye)
    s = np.clip((ay - (ye - rw)) / rw, 0, 1)                    # 0 at roll start, 1 at the edge
    return zc + RH * (1 - np.sqrt(1 - s ** 2))                  # quarter ellipse, tangent to the flat


def chord(k):
    xc, rw, wall, za = WELL[k]
    zf = Z_F if k == "front" else Z_M
    return xc, np.sqrt(rw * rw - (za - zf) ** 2), wall


def in_opening(x, y):
    for k in WELL:
        xc, c, wall = chord(k)
        if abs(x - xc) < c and abs(y) > wall - 1e-6: return True
    return False


W = {}
xs = np.linspace(X_TIP_F, X_TIP_R, 900)
W["centreline"] = np.c_[xs, 0 * xs, Zc(xs)]
# outer edge and roll-start line (gaps at the openings)
for name, off in (("outer_edge", 0.0), ("roll_start", RW)):
    yy = -(Ye(xs) - np.minimum(off, 0.9 * Ye(xs)))
    pts = np.c_[xs, yy, Z(xs, yy)]
    keep = np.array([not in_opening(x, y) for x, y in pts[:, :2]])
    idx = np.where(keep)[0]
    for j, r in enumerate(np.split(idx, np.where(np.diff(idx) > 1)[0] + 1)):
        if len(r) > 3: W[f"{name}_{j}"] = pts[r]
# wheel openings: straight rectangle on the floor + its two sides running out over the roll to the edge
for k in WELL:
    xc, c, wall = chord(k); zf = Z_F if k == "front" else Z_M
    W[f"{k}_opening_inner"] = np.array([(xc - c, -wall, zf), (xc + c, -wall, zf)])
    for xe in (xc - c, xc + c):
        yy = -np.linspace(wall, Ye(xe), 60)
        W[f"{k}_opening_side_{int(xe)}"] = np.c_[np.full(60, xe), yy, Z(np.full(60, xe), yy)]
# lengthwise wires (on the flat they are exactly straight)
for yv in (150.0, 300.0, 450.0, 650.0, 800.0):
    ok = Ye(xs) - np.minimum(RW, 0.9 * Ye(xs)) >= yv
    ok &= np.array([not in_opening(x, -yv) for x in xs])
    idx = np.where(ok)[0]
    for j, r in enumerate(np.split(idx, np.where(np.diff(idx) > 1)[0] + 1)):
        if len(r) > 3: W[f"long_y{int(yv)}_{j}"] = np.c_[xs[r], np.full(len(r), -yv), Z(xs[r], np.full(len(r), -yv))]
# crosswise wires: centreline -> roll -> edge
for xv in np.arange(-2100, 2200, 300.0):
    ys = -np.linspace(0, Ye(xv), 120)
    ok = np.array([not in_opening(xv, y) for y in ys])
    r = np.where(ok)[0]; r = r[: np.argmax(np.diff(r) > 1) + 1] if (np.diff(r) > 1).any() else r
    W[f"cross_x{int(xv)}"] = np.c_[np.full(len(r), xv), ys[r], Z(np.full(len(r), xv), ys[r])]
json.dump({k: v.tolist() for k, v in W.items()}, open(OUT, "w"))
# ---------------- how far the design sits from the mesh underside (vertical distance)
FN = m.face_normals
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
down = FN[:, 2] < -0.2; adj = m.face_adjacency; ok_ = down[adj[:, 0]] & down[adj[:, 1]]
_, comp = connected_components(coo_matrix((np.ones(ok_.sum()), (adj[ok_, 0], adj[ok_, 1])), shape=(len(FN), len(FN))), directed=False)
c_ = m.triangles_center
seed = np.where(down & (np.abs(c_[:, 0]) < 300) & (np.abs(c_[:, 1]) < 300) & (c_[:, 2] < 130))[0][0]
U = down & (comp == comp[seed]) & (c_[:, 1] <= 0)
cu = c_[U]; inside = np.abs(cu[:, 1]) < Ye(cu[:, 0]) - 5
d = cu[inside, 2] - Z(cu[inside, 0], cu[inside, 1])
print("design vs mesh underside (vertical): median %.1f  p90 %.1f  p99 %.1f mm" % tuple(np.percentile(np.abs(d), [50, 90, 99])))
for lo, hi, lab in ((-2300, -1800, "nose"), (-1800, -950, "front floor"), (-950, 1750, "main floor"), (1750, 2300, "diffuser")):
    s = (cu[inside, 0] >= lo) & (cu[inside, 0] < hi)
    if s.any(): print("  %-12s median %5.1f  p90 %5.1f mm" % (lab, np.median(np.abs(d[s])), np.percentile(np.abs(d[s]), 90)))
print("wires:", len(W))

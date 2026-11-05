"""Underside wireframe (half car, y <= 0): curves only, no surfaces.

underside = mesh faces facing down (the first surface hit by a ray shot straight up).
Wires:
  outer edge      where the underside turns into the side (outermost underside point per x)
  centreline      underside profile at y = 0 (nose and tail kick-ups)
  well openings   straight edges of the two wheel openings in the floor
  longitudinal    underside profile at fixed y (gaps at the wheel openings outboard of the slot wall)
  transverse      underside profile at fixed x, from the centreline out to the outer edge
Every wire is sampled by vertical rays and faired with a least-squares cubic spline.
"""
import sys, json, numpy as np, trimesh
from scipy.interpolate import make_lsq_spline
m = trimesh.load(sys.argv[1], force='mesh'); P = json.load(open(sys.argv[2])); OUT = sys.argv[3]
FN = m.face_normals
# the underside: the connected set of downward faces that contains the floor
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
down = FN[:, 2] < -0.2
adj = m.face_adjacency; ok_ = down[adj[:, 0]] & down[adj[:, 1]]
g = coo_matrix((np.ones(ok_.sum()), (adj[ok_, 0], adj[ok_, 1])), shape=(len(FN), len(FN)))
_, comp = connected_components(g, directed=False)
c_ = m.triangles_center
seed = np.where(down & (np.abs(c_[:, 0]) < 300) & (np.abs(c_[:, 1]) < 300) & (c_[:, 2] < 130))[0][0]
UNDER = down & (comp == comp[seed])
print("underside faces", UNDER.sum(), "area %.2f m2 (both halves)" % (m.area_faces[UNDER].sum() / 1e6))
WIN = [(P[k]["x"], P[k]["r"] + g, P[k]["wall"], zf) for k, g, zf in (("front", 12.0, 96.8), ("rear", 8.0, 114.5))]
X0, X1 = m.bounds[0, 0] + 8, m.bounds[1, 0] - 8


def in_opening(x, y):
    for xc, rw, wall, zf in WIN:
        c = np.sqrt(max(rw * rw - (P["front" if xc < 0 else "rear"]["z"] - zf) ** 2, 0))
        if abs(x - xc) < c and y < -wall: return True
    return False


def under_z(xs, ys):
    """z of the underside at (x, y) points: first hit of a ray going up, if it faces down."""
    o = np.c_[xs, ys, np.full(len(xs), -200.0)]
    loc, ri, ti = m.ray.intersects_location(o, np.tile([0, 0, 1.0], (len(o), 1)), multiple_hits=False)
    z = np.full(len(xs), np.nan)
    ok = UNDER[ti]
    z[ri[ok]] = loc[ok, 2]
    return z


def fair(t, Q, step=250.0):
    """Least-squares cubic spline of the columns of Q over parameter t."""
    o = np.argsort(t); t, Q = t[o], Q[o]
    _, u = np.unique(t, return_index=True); t, Q = t[u], Q[u]
    n = max(4, int(np.ptp(t) / step) + 3)
    kn = np.r_[[t[0]] * 4, np.linspace(t[0], t[-1], n - 2)[1:-1], [t[-1]] * 4]
    tt = np.linspace(t[0], t[-1], max(40, int(np.ptp(t) / 10)))
    return np.c_[[make_lsq_spline(t, Q[:, j], kn, 3)(tt) for j in range(Q.shape[1])]].T, tt


def runs(mask):
    idx = np.where(mask)[0]
    return [r for r in np.split(idx, np.where(np.diff(idx) > 1)[0] + 1) if len(r) > 5]


wires = {}
# ---- outer edge: outermost y per x where the underside exists (scan y inward from -1100)
ys_scan = np.arange(-1100, 1, 4.0)
edge = []
for x in np.arange(X0, X1, 15.0):
    z = under_z(np.full(len(ys_scan), x), ys_scan)
    ok = ~np.isnan(z)
    if not ok.any(): continue
    j = np.argmax(ok)                                   # first underside hit going inward
    if any(abs(x - xc) < np.sqrt(max(rw * rw - (P["front" if xc < 0 else "rear"]["z"] - zf) ** 2, 0)) + 25
           for xc, rw, wall, zf in WIN): continue          # the opening itself is the edge there
    edge.append((x, ys_scan[j], z[j]))
edge = np.array(edge)
for k, r in enumerate(np.split(edge, np.where(np.diff(edge[:, 0]) > 40)[0] + 1)):
    if len(r) < 6: continue
    Q, _ = fair(r[:, 0], r[:, 1:], 200.0)
    wires[f"outer_edge_{k}"] = np.c_[np.linspace(r[0, 0], r[-1, 0], len(Q)), Q]
# ---- centreline
xs = np.arange(X0, X1, 10.0); zc = under_z(xs, np.full(len(xs), -1.0)); ok = ~np.isnan(zc)
Q, tt = fair(xs[ok], zc[ok][:, None], 150.0)
wires["centreline"] = np.c_[tt, np.zeros(len(tt)), Q[:, 0]]
# ---- well openings: straight edges at the floor
for (xc, rw, wall, zf), name in zip(WIN, ("front", "rear")):
    zc_ = P[name]["z"]; c = np.sqrt(rw * rw - (zc_ - zf) ** 2)
    segs_ = [v for k_, v in wires.items() if k_.startswith("outer_edge")]
    ends = np.vstack([np.r_[v[:1], v[-1:]] for v in segs_])
    ef = ends[np.argmin(np.abs(ends[:, 0] - (xc - c)))]      # edge end just ahead of the opening
    er = ends[np.argmin(np.abs(ends[:, 0] - (xc + c)))]      # edge end just behind it
    wires[f"{name}_opening"] = np.array([ef, (xc - c, ef[1], zf), (xc - c, -wall, zf), (xc + c, -wall, zf), (xc + c, er[1], zf), er])
# ---- longitudinal wires
for y in (-150, -300, -450, -650, -800):
    z = under_z(xs, np.full(len(xs), float(y)))
    ok = ~np.isnan(z) & np.array([not in_opening(x, y) for x in xs])
    for k, r in enumerate(runs(ok)):
        Q, tt = fair(xs[r], z[r][:, None], 200.0)
        wires[f"long_y{-y}_{k}"] = np.c_[tt, np.full(len(tt), float(y)), Q[:, 0]]
# ---- transverse wires
for x in np.arange(-2100, 2200, 300.0):
    yy = np.arange(-1100, 1, 5.0); z = under_z(np.full(len(yy), x), yy)
    ok = ~np.isnan(z) & np.array([not in_opening(x, y) for y in yy])
    rr = runs(ok)
    if not rr: continue
    r = rr[-1]                                          # the run that reaches the centreline
    Q, tt = fair(yy[r], z[r][:, None], 150.0)
    wires[f"cross_x{int(x)}"] = np.c_[np.full(len(tt), x), tt, Q[:, 0]]
json.dump({k: v.tolist() for k, v in wires.items()}, open(OUT, "w"))
for k, v in wires.items():
    print("%-16s x %5.0f..%5.0f  y %5.0f..%5.0f  z %4.0f..%4.0f" % (k, v[:, 0].min(), v[:, 0].max(), v[:, 1].min(), v[:, 1].max(), v[:, 2].min(), v[:, 2].max()))

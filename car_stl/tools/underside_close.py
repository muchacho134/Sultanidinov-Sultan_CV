"""Underside wires that stay close to the STL, only cleaned up.

1. height field of the underside measured on a 10 mm grid by vertical rays (first hit, on the
   connected downward-facing underside only), lightly smoothed
2. flat floors snapped: where the field is within SNAP mm of a floor plane it is set exactly on it
   (with a short blend so there is no step)
3. plan edge = outermost measured underside point per x, faired; a stretch that is already
   nearly straight (< STRAIGHT mm wobble) is made exactly straight
4. all wires sampled from that one field + edge, so they meet exactly
"""
import sys, json, numpy as np, trimesh
from scipy.ndimage import gaussian_filter, gaussian_filter1d, distance_transform_edt
from scipy.interpolate import make_lsq_spline, RegularGridInterpolator
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
m = trimesh.load(sys.argv[1], force='mesh'); P = json.load(open(sys.argv[2])); OUT = sys.argv[3]
G, SNAP, STRAIGHT = 10.0, 4.0, 0.0      # no forced straight runs: edges keep the STL flow
FLOORS = ((-1950.0, -1000.0, 96.8), (-950.0, 1700.0, 114.5))
WELL = {k: (P[k]["x"], P[k]["r"] + g, P[k]["wall"], P[k]["z"], zf) for k, g, zf in (("front", 12.0, 96.8), ("rear", 8.0, 114.5))}
FN = m.face_normals; c_ = m.triangles_center
down = FN[:, 2] < -0.2; adj = m.face_adjacency; ok_ = down[adj[:, 0]] & down[adj[:, 1]]
_, comp = connected_components(coo_matrix((np.ones(ok_.sum()), (adj[ok_, 0], adj[ok_, 1])), shape=(len(FN), len(FN))), directed=False)
seed = np.where(down & (np.abs(c_[:, 0]) < 300) & (np.abs(c_[:, 1]) < 300) & (c_[:, 2] < 130))[0][0]
UNDER = down & (comp == comp[seed])


def chord(k):
    xc, rw, wall, za, zf = WELL[k]
    return xc, np.sqrt(rw * rw - (za - zf) ** 2), wall


def in_opening(x, y):
    x = np.asarray(x); y = np.asarray(y); r = np.zeros(np.broadcast(x, y).shape, bool)
    for k in WELL:
        xc, c, wall = chord(k); r |= (np.abs(x - xc) < c) & (np.abs(y) > wall - 1e-6)
    return r


# ---- 1. height field
xs = np.arange(m.bounds[0, 0] + 5, m.bounds[1, 0] - 5, G); ys = np.arange(-1100.0, 0.1, G)
XX, YY = np.meshgrid(xs, ys, indexing='ij')
o = np.c_[XX.ravel(), YY.ravel(), np.full(XX.size, -200.0)]
loc, ri, ti = m.ray.intersects_location(o, np.tile([0, 0, 1.0], (len(o), 1)), multiple_hits=False)
Z = np.full(XX.size, np.nan); k_ = UNDER[ti]; Z[ri[k_]] = loc[k_, 2]; Z = Z.reshape(XX.shape)
valid = ~np.isnan(Z)
# fill holes (nearest) for smoothing, then smooth lightly
idx = distance_transform_edt(~valid, return_distances=False, return_indices=True)
Zs = gaussian_filter(Z[tuple(idx)], 1.5)
# ---- 2. snap the flat floors
for x0, x1, zf in FLOORS:
    sel = (XX >= x0) & (XX <= x1)
    w = np.clip(1 - (np.abs(Zs - zf) - SNAP) / SNAP, 0, 1) * sel     # 1 inside the snap band, fading to 0
    Zs = w * zf + (1 - w) * Zs
zf_ = RegularGridInterpolator((xs, ys), Zs, bounds_error=False, fill_value=None)
Zf = lambda x, y: zf_(np.c_[np.broadcast_to(x, np.broadcast(x, y).shape).ravel(), np.broadcast_to(y, np.broadcast(x, y).shape).ravel()])
# ---- 3. plan edge: outermost valid y per x (outside the openings), faired; straight where nearly straight
edge = []
for i, x in enumerate(xs):
    v = np.where(valid[i] & ~in_opening(x, ys))[0]
    if len(v) and not any(abs(x - chord(k)[0]) < chord(k)[1] + 20 for k in WELL):
        edge.append((x, ys[v[0]]))
edge = np.array(edge)
segs = [s for s in np.split(edge, np.where(np.diff(edge[:, 0]) > 2 * G)[0] + 1) if len(s) > 8]
E = []
for s in segs:
    x, y = s[:, 0], gaussian_filter1d(s[:, 1], 2)
    n = max(4, int(np.ptp(x) / 150) + 3)
    kn = np.r_[[x[0]] * 4, np.linspace(x[0], x[-1], n - 2)[1:-1], [x[-1]] * 4]
    yf = make_lsq_spline(x, y, kn, 3)(x)
    # straighten a central run whose wobble is small
    mid = np.abs(yf - np.median(yf)) < STRAIGHT
    if STRAIGHT > 0 and mid.mean() > 0.5:
        r = np.where(mid)[0]; a, b = r[0], r[-1]
        yf[a:b + 1] = np.median(yf[a:b + 1])
        bl = 8                                            # blend the ends into the curve
        for j in range(1, bl):
            if a - j >= 0: yf[a - j] = yf[a - j] * (j / bl) + yf[a] * (1 - j / bl)
            if b + j < len(yf): yf[b + j] = yf[b + j] * (j / bl) + yf[b] * (1 - j / bl)
    E.append(np.c_[x, yf])
W = {}
for j, e in enumerate(E):
    W[f"outer_edge_{j}"] = np.c_[e, Zf(e[:, 0], e[:, 1])]
Ye = lambda x: np.interp(x, np.concatenate([e[:, 0] for e in E]), np.concatenate([e[:, 1] for e in E]))
# ---- 4. other wires
xl = np.linspace(xs[0], xs[-1], 900)
W["centreline"] = np.c_[xl, 0 * xl, Zf(xl, 0 * xl)]
for k in WELL:
    xc, c, wall = chord(k); zf = WELL[k][4]
    W[f"{k}_opening_inner"] = np.array([(xc - c, -wall, zf), (xc + c, -wall, zf)])
    for xe in (xc - c, xc + c):
        yy = np.linspace(-wall, Ye(xe + (-25 if xe < xc else 25)), 50)
        W[f"{k}_opening_side_{int(xe)}"] = np.c_[np.full(50, xe), yy, Zf(np.full(50, xe), yy)]
# lengthwise flow lines: fixed fraction of the way from the centreline to the edge (follow the outline)
ax_ = np.concatenate([e[:, 0] for e in E]); ay_ = np.concatenate([e[:, 1] for e in E])
kn_ = np.r_[[ax_[0]] * 4, np.linspace(ax_[0], ax_[-1], 14)[1:-1], [ax_[-1]] * 4]
_sp = make_lsq_spline(ax_, ay_, kn_, 3)                        # one smooth outline, bridges the openings
Yflow = lambda x: np.minimum(_sp(np.clip(x, ax_[0], ax_[-1])), -1.0)
for f in (0.2, 0.4, 0.6, 0.8, 0.92):
    yv = f * np.where(np.isin(np.round(xl), np.round(ax_)) | True, Yflow(xl), 0)
    yv = np.maximum(yv, Ye(xl) + 8)                            # stay inside the real edge
    ok = ~in_opening(xl, yv)
    r_ = np.where(ok)[0]
    for j, r in enumerate(np.split(r_, np.where(np.diff(r_) > 1)[0] + 1)):
        if len(r) > 3: W[f"flow_{int(f * 100)}_{j}"] = np.c_[xl[r], yv[r], Zf(xl[r], yv[r])]
for xv in np.arange(-2100, 2200, 300.0):
    yy = np.linspace(0, Ye(xv), 120); keep = ~in_opening(xv, yy)
    r = np.where(keep)[0]
    if len(r) and (np.diff(r) > 1).any(): r = r[: np.argmax(np.diff(r) > 1) + 1]
    W[f"cross_x{int(xv)}"] = np.c_[np.full(len(r), xv), yy[r], Zf(np.full(len(r), xv), yy[r])]
json.dump({k: v.tolist() for k, v in W.items()}, open(OUT, "w"))
# ---- closeness to the mesh
cu = c_[UNDER & (c_[:, 1] <= 0)]
ins = cu[:, 1] > Ye(cu[:, 0]) + 5
d = cu[ins, 2] - Zf(cu[ins, 0], cu[ins, 1])
print("vs STL underside (vertical): median %.1f  p90 %.1f  p99 %.1f mm" % tuple(np.percentile(np.abs(d), [50, 90, 99])))
ed = np.concatenate([np.abs(gaussian_filter1d(s[:, 1], 2) - Ye(s[:, 0])) for s in segs])
print("plan edge vs STL: median %.1f  p90 %.1f mm" % (np.median(ed), np.percentile(ed, 90)))
print("wires:", len(W))

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
Zs = gaussian_filter(Z[tuple(idx)], 2.2)          # smoother field
# ---- 2. snap the flat floors
for x0, x1, zf in FLOORS:
    sel = (XX >= x0) & (XX <= x1)
    w = np.clip(1 - (np.abs(Zs - zf) - SNAP) / SNAP, 0, 1) * sel     # 1 inside the snap band, fading to 0
    Zs = w * zf + (1 - w) * Zs
zf_ = RegularGridInterpolator((xs, ys), Zs, bounds_error=False, fill_value=None)
Zf = lambda x, y: zf_(np.c_[np.broadcast_to(x, np.broadcast(x, y).shape).ravel(), np.broadcast_to(y, np.broadcast(x, y).shape).ravel()])
# ---- 3. plan outline: one continuous curve, nose tip -> tail tip, through (bridging) the openings
edge = []
for i, x in enumerate(xs):
    v = np.where(valid[i] & ~in_opening(x, ys))[0]
    if len(v) and not any(abs(x - chord(k)[0]) < chord(k)[1] + 20 for k in WELL):
        edge.append((x, ys[v[0]]))
edge = np.array(edge)
x_tf, x_tr = xs[np.where(valid.any(1))[0][0]], xs[np.where(valid.any(1))[0][-1]]
cuts = sorted([chord(k)[0] - chord(k)[1] for k in WELL] + [chord(k)[0] + chord(k)[1] for k in WELL])
spans = [(x_tf, cuts[0]), (cuts[1], cuts[2]), (cuts[3], x_tr)]
OXs, OYs = [], []
for j, (a_, b_) in enumerate(spans):
    lo_ = a_ + (80 if j > 0 else -30); hi_ = b_ - (80 if j < 2 else -30)   # skip the pinch next to an opening
    pe = edge[(edge[:, 0] >= lo_) & (edge[:, 0] <= hi_)]
    if j == 0: pe = np.r_[np.array([(x_tf, 0.0)] * 6), pe]
    if j == 2: pe = np.r_[pe, np.array([(x_tr, 0.0)] * 6)]
    u = np.r_[0, np.cumsum(np.hypot(*np.diff(pe, axis=0).T))]; u /= u[-1]
    nk = max(4, int((b_ - a_) / 220))
    kn = np.r_[[0] * 4, np.linspace(0, 1, nk)[1:-1], [1] * 4]
    wts = np.where(pe[:, 1] == 0.0, 50.0, 1.0)
    sx = make_lsq_spline(u, pe[:, 0], kn, 3, w=wts); sy = make_lsq_spline(u, pe[:, 1], kn, 3, w=wts)
    uu = np.linspace(0, 1, 1500); X_, Y_ = sx(uu), np.minimum(sy(uu), 0.0)
    if j == 0: X_[0], Y_[0] = x_tf, 0.0
    if j == 2: X_[-1], Y_[-1] = x_tr, 0.0
    o_ = np.argsort(X_); X_, Y_ = X_[o_], Y_[o_]
    keep_ = (X_ >= a_) & (X_ <= b_); X_, Y_ = X_[keep_], Y_[keep_]
    # run on to the opening with the end slope (no pinch)
    if j < 2:
        g = (Y_[-1] - Y_[-20]) / (X_[-1] - X_[-20]); xe_ = np.linspace(X_[-1], b_, 30)[1:]
        X_ = np.r_[X_, xe_]; Y_ = np.r_[Y_, Y_[-1] + 0.5 * g * (xe_ - X_[-1])]
    if j > 0:
        g = (Y_[19] - Y_[0]) / (X_[19] - X_[0]); xs_ = np.linspace(a_, X_[0], 30)[:-1]
        X_ = np.r_[xs_, X_]; Y_ = np.r_[Y_[0] + 0.5 * g * (xs_ - X_[0]), Y_]
    OXs.append(X_); OYs.append(Y_)
OXs, OYs = np.concatenate(OXs), np.concatenate(OYs)
def Ye(x):
    return np.interp(x, OXs, OYs)
def Yguide(x):
    """outline with a soft bridge across each opening (only used to space the flow lines)"""
    x = np.asarray(x, float); y = Ye(x)
    for k in WELL:
        xc, c, wall = chord(k); a_, b_ = xc - c - 80, xc + c + 80   # start before the corner pinch
        t = np.clip((x - a_) / (b_ - a_), 0, 1); t = t * t * (3 - 2 * t)
        y = np.where((x > a_) & (x < b_), Ye(a_) * (1 - t) + Ye(b_) * t, y)
    return y
W = {}
# ---- floor region in plan: outline minus the wheel openings, with filleted corners
from shapely.geometry import Polygon as SP, LineString as SL, box as sbox
from shapely.ops import unary_union
R_IN, R_OUT = 60.0, 40.0
half_poly = SP(list(zip(OXs, OYs)) + [(x_tr, 0.0), (x_tf, 0.0)]).buffer(0)
full = unary_union([half_poly, SP([(x, -y) for x, y in half_poly.exterior.coords])]).buffer(0)
holes = []
for k in WELL:
    xc, c, wall = chord(k)
    for sg in (1, -1):
        rect = sbox(xc - c, -3000, xc + c, -wall) if sg < 0 else sbox(xc - c, wall, xc + c, 3000)
        holes.append(rect.buffer(-R_IN, join_style=1).buffer(R_IN, join_style=1) if False else rect)
REG = full.difference(unary_union(holes))
REG = REG.buffer(R_OUT, join_style=1).buffer(-2 * R_OUT, join_style=1).buffer(R_OUT, join_style=1)  # round convex + concave corners
REG = REG.buffer(-R_IN, join_style=1).buffer(R_IN, join_style=1)                                   # bigger radius on the inner slot corners
if REG.geom_type != "Polygon": REG = max(REG.geoms, key=lambda g: g.area)
REG = REG.intersection(sbox(-5000, -3000, 5000, 0.0))
if REG.geom_type != "Polygon": REG = max(REG.geoms, key=lambda g: g.area)
B = np.array(REG.exterior.coords)
B = B[np.abs(B[:, 1]) > 0.5]                                   # drop the y = 0 (mirror) side
# resample the boundary by arc length and split it into outer-edge / opening runs
d = np.r_[0, np.cumsum(np.hypot(*np.diff(B, axis=0).T))]
jump = np.where(np.diff(d) > 2000)[0]                           # the dropped centreline side shows as a jump
if len(jump): B = np.roll(B, -(jump[0] + 1), axis=0)
seg = np.hypot(*np.diff(B, axis=0).T)
if (seg > 2000).any(): B = B[: np.argmax(seg > 2000) + 1]        # never interpolate across the dropped side
d = np.r_[0, np.cumsum(np.hypot(*np.diff(B, axis=0).T))]
t = np.arange(0, d[-1], 5.0); B = np.c_[np.interp(t, d, B[:, 0]), np.interp(t, d, B[:, 1])]
from shapely.geometry import Point as SPt
H_ = unary_union([h for h in holes if h.bounds[3] <= 0])
is_open = np.array([H_.distance(SPt(p)) < R_OUT + R_IN for p in B])
runs_ = np.split(np.arange(len(B)), np.where(np.diff(is_open.astype(int)) != 0)[0] + 1)
ne = no = 0
for r in runs_:
    if len(r) < 3: continue
    P2 = B[np.r_[r, r[-1] + 1]] if r[-1] + 1 < len(B) else B[r]     # share the joint with the next piece
    if is_open[r[0]]:
        W[f"opening_{no}"] = np.c_[P2, Zf(P2[:, 0], P2[:, 1])]; no += 1
    else:
        W[f"outer_edge_{ne}"] = np.c_[P2, Zf(P2[:, 0], P2[:, 1])]; ne += 1
# ---- 4. other wires: cut by the filleted region
xl = np.linspace(x_tf, x_tr, 1200)
W["centreline"] = np.c_[xl, 0 * xl, Zf(xl, 0 * xl)]
def pieces(line):
    g = REG.intersection(line)
    gs = [g] if g.geom_type == "LineString" else list(getattr(g, "geoms", []))
    return [np.array(q.coords) for q in gs if q.geom_type == "LineString" and q.length > 30]
for f in (0.2, 0.4, 0.6, 0.8, 0.92):
    yv = np.minimum(f * Yguide(xl), -0.6)
    for j, Q in enumerate(pieces(SL(list(zip(xl, yv))))):
        if len(Q) < 4: continue
        W[f"flow_{int(f * 100)}_{j}"] = np.c_[Q, Zf(Q[:, 0], Q[:, 1])]
for xv in np.arange(-2100, 2200, 300.0):
    ps = pieces(SL([(xv, -0.6), (xv, -3000)]))
    if not ps: continue
    Q = max(ps, key=lambda q: q[:, 1].max())                    # the piece that starts at the centreline
    yy = np.linspace(Q[:, 1].max(), Q[:, 1].min(), 120)
    W[f"cross_x{int(xv)}"] = np.c_[np.full(120, xv), yy, Zf(np.full(120, xv), yy)]
# ---- smooth the outer-edge height, then pull the wires that end on it onto the smoothed edge
EZ = {}
for k in [k for k in W if k.startswith("outer_edge")]:
    v = W[k]; t = np.r_[0, np.cumsum(np.linalg.norm(np.diff(v[:, :2], axis=0), axis=1))]
    if len(v) < 12 or t[-1] < 100: continue
    n = max(4, int(np.ptp(t) / 300) + 3)
    kn_ = np.r_[[t[0]] * 4, np.linspace(t[0], t[-1], n - 2)[1:-1], [t[-1]] * 4]
    ws_ = np.ones(len(t)); ws_[[0, -1]] = 30.0                     # keep the end heights
    z0 = v[:, 2].copy(); zs = make_lsq_spline(t, v[:, 2], kn_, 3, w=ws_)(t)
    u_ = t / t[-1]; corr = (z0[0] - zs[0]) * np.clip(1 - u_ / 0.15, 0, 1) ** 2 + (z0[-1] - zs[-1]) * np.clip((u_ - 0.85) / 0.15, 0, 1) ** 2
    v[:, 2] = zs + corr; W[k] = v; EZ[k] = v                       # ends pinned to the openings
edge_pts = np.vstack(list(EZ.values()))
from scipy.spatial import cKDTree as _T
_et = _T(edge_pts[:, :2])
for k in [k for k in W if k.startswith("cross_x")]:
    v = W[k]; d, i = _et.query(v[-1, :2])
    if d < 15:
        dz = edge_pts[i, 2] - v[-1, 2]
        s_ = np.r_[0, np.cumsum(np.linalg.norm(np.diff(v[:, :2], axis=0), axis=1))]; s_ /= s_[-1]
        v[:, 2] += dz * np.clip((s_ - 0.6) / 0.4, 0, 1) ** 2         # blend over the last 40 %
        W[k] = v
# ---- connection check: every wire end must lie on another wire
allp = np.vstack([v for v in W.values()])
from scipy.spatial import cKDTree
bad = []
for k, v in W.items():
    for e in (v[0], v[-1]):
        others = np.vstack([w for kk, w in W.items() if kk != k])
        d = cKDTree(others).query(e)[0]
        if d > 6: bad.append((k, round(d, 1)))
print("loose wire ends (> 6 mm from any other wire):", bad if bad else "none")
for k, v in W.items():
    if k.startswith("flow"): print("  %s: %.0f,%.0f -> %.0f,%.0f" % (k, v[0, 0], v[0, 1], v[-1, 0], v[-1, 1]))
json.dump({k: v.tolist() for k, v in W.items()}, open(OUT, "w"))
# ---- closeness to the mesh
cu = c_[UNDER & (c_[:, 1] <= 0)]
ins = cu[:, 1] > Ye(cu[:, 0]) + 5
d = cu[ins, 2] - Zf(cu[ins, 0], cu[ins, 1])
print("vs STL underside (vertical): median %.1f  p90 %.1f  p99 %.1f mm" % tuple(np.percentile(np.abs(d), [50, 90, 99])))
ed = np.abs(edge[:, 1] - Ye(edge[:, 0]))
print("plan edge vs STL: median %.1f  p90 %.1f mm" % (np.median(ed), np.percentile(ed, 90)))
print("wires:", len(W))

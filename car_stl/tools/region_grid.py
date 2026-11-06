"""Floor-style wire network for one direction region (back / front / top / side) of the half car.

Same recipe as the underside:
  1. height field seen from the region's own direction (rays from outside, first hit, only faces of
     this region), 10 mm grid, holes filled, smoothed
  2. outline of each region piece (contour of its mask), faired as a closed spline
  3. flow lines along the long axis at fixed fractions between the outline's lower and upper sides,
     crosswise lines every STEP mm, all clipped by the outline and lifted onto the height field
"""
import sys, json, numpy as np, trimesh
from scipy.ndimage import gaussian_filter, gaussian_filter1d, distance_transform_edt, label as cc_label, binary_closing
from scipy.interpolate import RegularGridInterpolator, splprep, splev
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from shapely.geometry import Polygon, LineString
m = trimesh.load(sys.argv[1], force='mesh'); lab = np.load(sys.argv[2]); REG = sys.argv[3]; OUT = sys.argv[4]
G, SMOOTH, STEP, MIN_AREA = 10.0, 2.2, 150.0, 0.02e6
ID = {"bottom": 0, "back": 1, "front": 2, "top": 3, "side": 4}[REG]
B = m.bounds
# (u axis, v axis, height axis, ray origin value on height axis, ray direction sign)
SPEC = {"back": (1, 2, 0, B[1, 0] + 300, -1), "front": (1, 2, 0, B[0, 0] - 300, +1),
        "top": (0, 1, 2, B[1, 2] + 300, -1), "side": (0, 2, 1, B[0, 1] - 300, +1)}
ua, va, ha, h0, sg = SPEC[REG]
us = np.arange(B[0, ua] - 10, (0.0 if ua == 1 else B[1, ua]) + 10, G)
vs = np.arange(B[0, va] - 10, (0.0 if va == 1 else B[1, va]) + 10, G)
UU, VV = np.meshgrid(us, vs, indexing='ij')
O = np.zeros((UU.size, 3)); O[:, ua] = UU.ravel(); O[:, va] = VV.ravel(); O[:, ha] = h0
D = np.zeros((UU.size, 3)); D[:, ha] = sg
loc, ri, ti = m.ray.intersects_location(O, D, multiple_hits=False)
H = np.full(UU.size, np.nan); ok = lab[ti] == ID; H[ri[ok]] = loc[ok, ha]
H = H.reshape(UU.shape); mask = ~np.isnan(H)
mask = binary_closing(mask, iterations=2) & (np.isfinite(H) | True)
idx = distance_transform_edt(np.isnan(H), return_distances=False, return_indices=True)
Hs = gaussian_filter(H[tuple(idx)], SMOOTH)
fH = RegularGridInterpolator((us, vs), Hs, bounds_error=False, fill_value=None)


def lift(u, v):
    P = np.zeros((len(u), 3)); P[:, ua] = u; P[:, va] = v; P[:, ha] = fH(np.c_[u, v]); return P


W = {}
comp, n = cc_label(mask)
pieces = []
for k in range(1, n + 1):
    area = (comp == k).sum() * G * G
    if area < MIN_AREA: continue
    cs = plt.contour(UU, VV, (comp == k).astype(float), levels=[0.5])
    segs = max(cs.allsegs[0], key=len); plt.close('all')
    seg = np.asarray(segs)
    if len(seg) < 20: continue
    # fair the outline (closed spline), keep points on the centre plane exactly there
    tck, _ = splprep(seg.T, s=len(seg) * 30.0, per=1)
    Q = np.array(splev(np.linspace(0, 1, max(200, len(seg) * 2)), tck)).T
    if ua == 1: Q[:, 0] = np.minimum(Q[:, 0], 0.0)
    if va == 1: Q[:, 1] = np.minimum(Q[:, 1], 0.0)
    poly = Polygon(Q).buffer(0)
    if poly.geom_type != "Polygon": poly = max(poly.geoms, key=lambda g: g.area)
    pieces.append((k, poly, area))
print(f"{REG}: {len(pieces)} piece(s)", [round(a / 1e6, 2) for _, _, a in pieces])
for j, (k, poly, area) in enumerate(pieces):
    Q = np.array(poly.exterior.coords)
    W[f"outer_edge_{j}"] = lift(Q[:, 0], Q[:, 1])
    x0, y0, x1, y1 = poly.bounds
    long_u = (x1 - x0) >= (y1 - y0)                            # flow along the longer extent
    # lower / upper side of the outline along the long axis
    a = np.linspace(x0 if long_u else y0, x1 if long_u else y1, 400)[2:-2]
    lo, hi, aa = [], [], []
    for t in a:
        ln = LineString([(t, -1e5), (t, 1e5)]) if long_u else LineString([(-1e5, t), (1e5, t)])
        g = poly.intersection(ln)
        if g.is_empty: continue
        b = np.array(g.bounds)
        lo.append(b[1] if long_u else b[0]); hi.append(b[3] if long_u else b[2]); aa.append(t)
    aa, lo, hi = np.array(aa), gaussian_filter1d(np.array(lo), 3), gaussian_filter1d(np.array(hi), 3)
    for f in (0.2, 0.4, 0.6, 0.8):
        b_ = lo + f * (hi - lo)
        u, v = (aa, b_) if long_u else (b_, aa)
        inside = np.array([poly.contains(__import__("shapely.geometry", fromlist=["Point"]).Point(p)) for p in zip(u, v)])
        r = np.where(inside)[0]
        for q, rr in enumerate(np.split(r, np.where(np.diff(r) > 1)[0] + 1)):
            if len(rr) > 5: W[f"flow_{j}_{int(f * 100)}_{q}"] = lift(u[rr], v[rr])
    for t in np.arange((x0 if long_u else y0) + STEP / 2, (x1 if long_u else y1), STEP):
        ln = LineString([(t, -1e5), (t, 1e5)]) if long_u else LineString([(-1e5, t), (1e5, t)])
        g = poly.intersection(ln)
        for q, gg in enumerate([g] if g.geom_type == "LineString" else list(getattr(g, "geoms", []))):
            if gg.geom_type != "LineString" or gg.length < 40: continue
            C = np.array(gg.coords); s = np.linspace(0, 1, 60)
            u = C[0, 0] + s * (C[-1, 0] - C[0, 0]); v = C[0, 1] + s * (C[-1, 1] - C[0, 1])
            W[f"cross_{j}_{int(t)}_{q}"] = lift(u, v)
json.dump({k: v.tolist() for k, v in W.items()}, open(OUT, "w"))
# closeness to the mesh: smoothed field vs measured field inside the mask
d = np.abs(Hs - H)[mask & np.isfinite(H)]
print("height field vs STL: median %.1f  p90 %.1f mm" % (np.median(d), np.percentile(d, 90)), "| wires:", len(W))

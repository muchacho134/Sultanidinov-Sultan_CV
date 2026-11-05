"""Step 1 (ground up): the bottom edge of the body - where the underside turns into the side.

On every cross section (x) the half contour is walked outward from the bottom centre; the
bottom edge is the first point where the surface normal turns from 'down' to 'sideways'
(normal angle passes 45 deg). Stations through the wheel openings are skipped (the edge
there is the well opening). The points are faired into one curve and shown in side, top,
front and rear views over the mesh outline.
"""
import sys, json, numpy as np, trimesh
from scipy.ndimage import gaussian_filter1d
from scipy.interpolate import make_lsq_spline
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
m = trimesh.load(sys.argv[1], force='mesh'); P = json.load(open(sys.argv[2])); OUT = sys.argv[3]
GAP = {"front": 12.0, "rear": 8.0}


def in_wheel_opening(x):
    for k in ("front", "rear"):
        w = P[k]
        if abs(x - w["x"]) < w["r"] + GAP[k] + 15: return True
    return False


pts = []
for x in np.arange(m.bounds[0, 0] + 15, m.bounds[1, 0] - 15, 20.0):
    if in_wheel_opening(x): continue
    s = m.section(plane_origin=[x, 0, 0], plane_normal=[1, 0, 0])
    if s is None: continue
    loop = max(s.discrete, key=lambda p: p[:, 2].max())[:, 1:]
    if np.allclose(loop[0], loop[-1]): loop = loop[:-1]
    # orient counter-clockwise in (y, z); start at the lowest point near the centre
    area = 0.5 * np.sum(loop[:-1, 0] * loop[1:, 1] - loop[1:, 0] * loop[:-1, 1])
    if area > 0: loop = loop[::-1]                  # clockwise: from bottom centre we walk to -y first
    near_c = np.abs(loop[:, 0]) < 60
    if not near_c.any(): continue
    i0 = np.where(near_c)[0][np.argmin(loop[near_c, 1])]
    walk = np.roll(loop, -i0, axis=0)
    if walk[min(5, len(walk) - 1), 0] > walk[0, 0]: walk = np.roll(walk[::-1], 1, axis=0)
    # resample, smooth, tangent angle
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(walk, axis=0), axis=1))]
    t = np.arange(0, d[-1] / 2, 5.0)
    W = np.c_[np.interp(t, d, walk[:, 0]), np.interp(t, d, walk[:, 1])]
    W = np.c_[gaussian_filter1d(W[:, 0], 3), gaussian_filter1d(W[:, 1], 3)]
    tg = np.gradient(W, axis=0); ang = np.degrees(np.arctan2(tg[:, 1], -tg[:, 0]))   # 0 = running outward flat
    j = np.where(ang > 45)[0]
    if not len(j): continue
    j = j[0]
    if W[j, 0] > -200: continue                       # still near the centre: not the bottom edge
    pts.append((x, W[j, 0], W[j, 1]))
pts = np.array(pts)
print("bottom-edge points", len(pts))
# fair: y(x) and z(x) as least-squares splines, split at the wheel openings
segs = np.split(pts, np.where(np.diff(pts[:, 0]) > 60)[0] + 1)
curve = []
for sg in segs:
    if len(sg) < 6: continue
    xs = sg[:, 0]; k = 3; n = max(4, min(9, int(np.ptp(xs) / 250)))
    kn = np.r_[[xs[0]] * 4, np.linspace(xs[0], xs[-1], n - 2)[1:-1], [xs[-1]] * 4]
    fy = make_lsq_spline(xs, sg[:, 1], kn, k); fz = make_lsq_spline(xs, sg[:, 2], kn, k)
    xx = np.linspace(xs[0], xs[-1], 120)
    curve.append(np.c_[xx, fy(xx), fz(xx)])
    print("segment x %5.0f..%5.0f  y %5.0f..%5.0f  z %4.0f..%4.0f" % (xs[0], xs[-1], fy(xx).min(), fy(xx).max(), fz(xx).min(), fz(xx).max()))
json.dump(dict(raw=pts.tolist(), segments=[c.tolist() for c in curve]), open(OUT, "w"))
# ---- 3-view drawing
V, F, fn, fc = m.vertices, m.faces, m.face_normals, m.triangles_center
fig = plt.figure(figsize=(22, 14)); gs = fig.add_gridspec(2, 3, height_ratios=[1, 1.3])
aS, aT = fig.add_subplot(gs[0, :]), fig.add_subplot(gs[1, :2]); aF = fig.add_subplot(gs[1, 2])
from matplotlib.collections import PolyCollection
Lt = np.array([0.35, -0.55, 0.75]); Lt /= np.linalg.norm(Lt)
for a, i, j, sel, title in ((aS, 0, 2, (fc[:, 1] <= 5) & (fn[:, 1] < 0), "SIDE"), (aT, 0, 1, (fc[:, 1] <= 5) & (fn[:, 2] < 0), "BOTTOM (seen from below)"),
                            (aF, 1, 2, (fc[:, 1] <= 5) & (fn[:, 0] < 0), "FRONT")):
    sh = 0.45 + 0.5 * np.clip(np.abs(fn[sel] @ Lt), 0, 1)
    a.add_collection(PolyCollection(V[F[sel]][:, :, [i, j]], facecolors=plt.cm.gray(sh), edgecolors='none'))
    a.plot(pts[:, i], pts[:, j], '.', ms=4, color='tab:orange', label='raw edge points')
    for c in curve:
        c = np.array(c); a.plot(c[:, i], c[:, j], '-', lw=3, color='red')
    a.autoscale(); a.set_aspect('equal'); a.set_title(title, fontsize=14); a.grid(alpha=.25)
aS.legend(['raw edge points', 'faired bottom edge'])
fig.tight_layout(); fig.savefig(OUT.replace(".json", ".png"), dpi=60)

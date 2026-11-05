"""Ground-up step 1: the bottom of the car in all three views, as faired 2D lines.

SIDE  : lowest point of the body per x (bottom silhouette in side view), wheels/wells excluded
FRONT : lowest point per y (bottom silhouette seen from the front)
BOTTOM: footprint outline - outermost |y| of the underside (faces facing down) per x
Each is faired with a least-squares spline (few knots) and drawn over the mesh in that view.
"""
import sys, json, numpy as np, trimesh
from scipy.interpolate import make_lsq_spline
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
m = trimesh.load(sys.argv[1], force='mesh'); P = json.load(open(sys.argv[2])); OUT = sys.argv[3]
V, F, fn, fc = m.vertices, m.faces, m.face_normals, m.triangles_center
half = fc[:, 1] <= 5
B = m.bounds


def lsq(x, y, n):
    o = np.argsort(x); x, y = x[o], y[o]
    _, u = np.unique(x, return_index=True); x, y = x[u], y[u]
    kn = np.r_[[x[0]] * 4, np.linspace(x[0], x[-1], n - 2)[1:-1], [x[-1]] * 4]
    s = make_lsq_spline(x, y, kn, 3); xx = np.linspace(x[0], x[-1], 300)
    return np.c_[xx, s(xx)]


def binned(a, b, lo, hi, step, fn_):
    out = []
    for c in np.arange(lo, hi, step):
        sel = np.abs(a - c) < step / 2
        if sel.any(): out.append((c, fn_(b[sel])))
    return np.array(out)


# SIDE: lowest body point per x (vertices of downward-ish faces), excluding the wheel openings
down = half & (fn[:, 2] < -0.3)
vd = np.unique(F[down]); Vd = V[vd]
excl = np.zeros(len(Vd), bool)
for k, gap in (("front", 12.0), ("rear", 8.0)):
    w = P[k]; excl |= np.abs(Vd[:, 0] - w["x"]) < w["r"] + gap + 5
side_raw = []
for x in np.arange(B[0, 0] + 5, B[1, 0] - 5, 20.0):
    if any(abs(x - P[k]["x"]) < P[k]["r"] + g + 5 for k, g in (("front", 12.0), ("rear", 8.0))): continue
    sec = m.section(plane_origin=[x, 0, 0], plane_normal=[1, 0, 0])
    if sec is None: continue
    zz = np.concatenate([p[p[:, 1] <= 2, 2] for p in sec.discrete])
    if len(zz): side_raw.append((x, zz.min()))
side_raw = np.array(side_raw)
segs = np.split(side_raw, np.where(np.diff(side_raw[:, 0]) > 40)[0] + 1)
side = [lsq(s[:, 0], s[:, 1], max(4, min(10, int(np.ptp(s[:, 0]) / 200)))) for s in segs if len(s) > 6]
# FRONT: lowest point per y over the whole body (half), excluding the wheel opening columns
Vb = V[np.unique(F[half])]
inw = np.zeros(len(Vb), bool)
for k, gap in (("front", 12.0), ("rear", 8.0)):
    w = P[k]; inw |= (np.abs(Vb[:, 0] - w["x"]) < w["r"] + gap + 5) & (Vb[:, 1] < -w["wall"] + 5)
front_raw = binned(Vb[~inw, 1], Vb[~inw, 2], B[0, 1] + 5, 0, 15.0, np.min)
front = lsq(front_raw[:, 0], front_raw[:, 1], 8)
# BOTTOM: footprint - outermost |y| of the underside per x
foot_raw = binned(Vd[:, 0], Vd[:, 1], B[0, 0] + 5, B[1, 0] - 5, 20.0, np.min)
fsegs = np.split(foot_raw, np.where(np.diff(foot_raw[:, 0]) > 40)[0] + 1)
foot = [lsq(s[:, 0], s[:, 1], max(4, min(12, int(np.ptp(s[:, 0]) / 200)))) for s in fsegs if len(s) > 6]
json.dump(dict(side=[s.tolist() for s in side], front=front.tolist(), bottom=[s.tolist() for s in foot],
               side_raw=side_raw.tolist(), front_raw=front_raw.tolist(), bottom_raw=foot_raw.tolist()), open(OUT, "w"))
for s in side: print("SIDE   x %5.0f..%5.0f  z %4.0f..%4.0f" % (s[0, 0], s[-1, 0], s[:, 1].min(), s[:, 1].max()))
print("FRONT  y %5.0f..%5.0f  z %4.0f..%4.0f" % (front[0, 0], front[-1, 0], front[:, 1].min(), front[:, 1].max()))
for s in foot: print("BOTTOM x %5.0f..%5.0f  y %5.0f..%5.0f" % (s[0, 0], s[-1, 0], s[:, 1].min(), s[:, 1].max()))
# drawing
Lt = np.array([0.35, -0.55, 0.75]); Lt /= np.linalg.norm(Lt)
fig = plt.figure(figsize=(22, 15)); gs = fig.add_gridspec(2, 3, height_ratios=[1, 1.3])
aS, aB, aF = fig.add_subplot(gs[0, :]), fig.add_subplot(gs[1, :2]), fig.add_subplot(gs[1, 2])
for a, i, j, sel, title in ((aS, 0, 2, half & (fn[:, 1] < 0), "SIDE - bottom line"), (aB, 0, 1, half & (fn[:, 2] < 0), "BOTTOM (from below) - footprint"),
                            (aF, 1, 2, half & (fn[:, 0] < 0), "FRONT - bottom line")):
    sh = 0.45 + 0.5 * np.clip(np.abs(fn[sel] @ Lt), 0, 1)
    a.add_collection(PolyCollection(V[F[sel]][:, :, [i, j]], facecolors=plt.cm.gray(sh), edgecolors='none'))
    a.autoscale(); a.set_aspect('equal'); a.set_title(title, fontsize=14); a.grid(alpha=.25)
aS.plot(side_raw[:, 0], side_raw[:, 1], '.', ms=4, color='tab:orange')
for s in side: aS.plot(s[:, 0], s[:, 1], '-', lw=3, color='red')
aB.plot(foot_raw[:, 0], foot_raw[:, 1], '.', ms=4, color='tab:orange')
for s in foot: aB.plot(s[:, 0], s[:, 1], '-', lw=3, color='red')
aF.plot(front_raw[:, 0], front_raw[:, 1], '.', ms=4, color='tab:orange'); aF.plot(front[:, 0], front[:, 1], '-', lw=3, color='red')
fig.tight_layout(); fig.savefig(OUT.replace(".json", ".png"), dpi=60)

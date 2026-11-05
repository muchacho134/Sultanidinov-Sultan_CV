"""Extract the car's design curves from the mesh (half car, y <= 0) and fair them.

Slice the half body along each axis:
  x-slices (cross sections)   -> lines running along the car (shoulder, canopy base, sill ...)
  y-slices (side planes)      -> lines running across the car (hood front, windshield base, tail top ...)
  z-slices (horizontal)       -> lines running up/down (nose and tail corners, rear face edges ...)
On every slice the contour is resampled by arc length, its curvature computed, and curvature
peaks (corners) recorded. Corners are linked slice to slice into lines; each line is faired
with a smoothing spline. Plus the centreline profile (y = 0 section) and plan outline.
"""
import sys, json, numpy as np, trimesh
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks
from scipy.interpolate import splprep, splev
m = trimesh.load(sys.argv[1], force='mesh'); OUT = sys.argv[2]
STEP, LINK, KMIN = 6.0, 45.0, 1 / 260.0
B = m.bounds
AXES = {  # axis: (stations, min line length along the axis)
    0: (np.arange(B[0, 0] + 30, B[1, 0] - 30, 50.0), 500.0),
    1: (np.arange(-60.0, B[0, 1] + 20, -50.0), 300.0),
    2: (np.arange(B[0, 2] + 40, B[1, 2] - 20, 40.0), 250.0),
}


def resample(seg, closed):
    if closed: seg = np.r_[seg, seg[:1]]
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(seg, axis=0), axis=1))]
    if d[-1] < 200: return None
    t = np.arange(0, d[-1], STEP)
    Q = np.c_[[np.interp(t, d, seg[:, j]) for j in range(seg.shape[1])]].T
    return np.c_[[gaussian_filter1d(Q[:, j], 2.0, mode='wrap' if closed else 'nearest') for j in range(Q.shape[1])]].T


def slice_contours(axis, s):
    nrm = np.eye(3)[axis]
    sec = m.section(plane_origin=nrm * s, plane_normal=nrm)
    if sec is None: return []
    out = []
    for p in sec.discrete:
        if len(p) < 8: continue
        if axis == 1:                                    # side plane: whole loop lies in the half
            out.append((p, True))
        else:                                            # keep the y <= 0 run(s) of the loop
            neg = p[:, 1] <= 1.0
            if neg.all(): out.append((p, True)); continue
            if not neg.any(): continue
            r = np.roll(p, -int(np.argmin(neg)), axis=0); nr = np.roll(neg, -int(np.argmin(neg)))
            idx = np.where(nr)[0]
            splits = np.split(idx, np.where(np.diff(idx) > 1)[0] + 1)
            for sp in splits:
                if len(sp) > 8: out.append((r[sp], False))
    return out


def corners_on(axis):
    pts = []
    stations, _ = AXES[axis]
    o = [j for j in range(3) if j != axis]
    for s in stations:
        for p, closed in slice_contours(axis, s):
            P2 = p[:, o]
            if closed:                                   # counter-clockwise in the slice plane
                area = 0.5 * np.sum(P2[:-1, 0] * P2[1:, 1] - P2[1:, 0] * P2[:-1, 1])
                if area < 0: p = p[::-1]
            else:                                        # open run: start at the higher / front end
                if (axis == 0 and p[0, 2] < p[-1, 2]) or (axis == 2 and p[0, 0] > p[-1, 0]): p = p[::-1]
            Q3 = resample(p, closed)
            if Q3 is None: continue
            Q = Q3[:, o]
            d1 = np.gradient(Q, axis=0); d2 = np.gradient(d1, axis=0)
            k = (d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]) / (np.linalg.norm(d1, axis=1) ** 3 + 1e-9)
            k = gaussian_filter1d(k, 1.5, mode='wrap' if closed else 'nearest')
            for sg in (1, -1):
                pk, _ = find_peaks(sg * k, height=KMIN, distance=int(60 / STEP))
                for i in pk:
                    if Q3[i, 1] < -15:
                        pts.append((s, *Q3[i], k[i]))
    return np.array(pts)


def link(C, axis):
    """C rows: (station, x, y, z, k). Link corners slice to slice into lines."""
    stations, minlen = AXES[axis]
    step = abs(stations[1] - stations[0])
    o = [1 + j for j in range(3) if j != axis]
    lines, active = [], []
    for s in sorted(set(C[:, 0]), key=lambda v: v if axis != 1 else -v):
        P = C[C[:, 0] == s]; used = np.zeros(len(P), bool); still = []
        for ln in active:
            last = ln[-1]; gap = abs(s - last[0]) / step
            if gap > 4.5: lines.append(ln); continue
            dd = np.hypot(P[:, o[0]] - last[o[0]], P[:, o[1]] - last[o[1]])
            dd[(np.sign(P[:, 4]) != np.sign(last[4])) | used] = 1e9
            j = int(np.argmin(dd)) if len(dd) else -1
            if j >= 0 and dd[j] < LINK * max(gap, 1.0):
                ln.append(P[j]); used[j] = True; still.append(ln)
            else:
                lines.append(ln)
        still += [[P[j]] for j in np.where(~used)[0]]
        active = still
    lines += active
    return [np.array(l) for l in lines if np.ptp(np.array(l)[:, 1 + axis]) >= minlen]


def fair(P, s_per_pt=25.0):
    P = np.asarray(P, float)
    if len(P) < 5: return P
    tck, _ = splprep(P.T, s=s_per_pt * len(P), k=3)
    return np.array(splev(np.linspace(0, 1, max(len(P) * 4, 50)), tck)).T


curves = {}
for axis, tag in ((0, "X"), (1, "Y"), (2, "Z")):
    C = corners_on(axis)
    L = link(C, axis) if len(C) else []
    print(f"{tag}-slices: corners {len(C)}  lines {len(L)}")
    for i, ln in enumerate(sorted(L, key=lambda l: -np.ptp(l[:, 1 + axis]))):
        curves[f"{tag}{i:02d}"] = dict(points=fair(ln[:, 1:4]).tolist(), convex=bool(np.median(ln[:, 4]) > 0),
                                      raw=ln[:, 1:4].tolist(), axis=axis)
# centreline profile: the y = 0 section itself (upper part, nose tip -> tail tip)
sc = m.section(plane_origin=[0, -0.5, 0], plane_normal=[0, 1, 0])
L0 = max(sc.discrete, key=lambda p: np.ptp(p[:, 0]))
i0, i1 = np.argmin(L0[:, 0]), np.argmax(L0[:, 0])
a_ = np.roll(L0, -i0, axis=0); k1 = (i1 - i0) % len(L0)
up = a_[:k1 + 1] if a_[:k1 + 1, 2].mean() > a_[k1:, 2].mean() else a_[k1:][::-1]
curves["centre_profile"] = dict(points=fair(up[::2], 4).tolist(), convex=True, raw=up.tolist(), axis=-1)
# plan outline (top-view silhouette): widest point per x slab
plan = []
for x in np.arange(B[0, 0] + 30, B[1, 0] - 30, 25.0):
    sl = m.vertices[(np.abs(m.vertices[:, 0] - x) < 12.5) & (m.vertices[:, 1] <= 0)]
    if len(sl): j = np.argmin(sl[:, 1]); plan.append((x, sl[j, 1], sl[j, 2]))
plan = np.array(plan); plan[:, 2] = gaussian_filter1d(plan[:, 2], 6)
curves["plan_outline"] = dict(points=fair(plan, 15).tolist(), convex=True, raw=plan.tolist(), axis=-1)
json.dump(curves, open(OUT, "w"))
for k, v in curves.items():
    P = np.array(v["points"]); print("%-15s x %5.0f..%5.0f  y %5.0f..%5.0f  z %5.0f..%5.0f  %s" %
                                     (k, P[:, 0].min(), P[:, 0].max(), P[:, 1].min(), P[:, 1].max(), P[:, 2].min(), P[:, 2].max(), "convex" if v["convex"] else "concave"))

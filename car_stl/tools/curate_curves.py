"""Curated design-curve network (half car, y <= 0), built by hand from the candidate curves.

Every curve is assembled from chosen candidates (trimmed / reversed / joined) and refitted as a
least-squares cubic B-spline with few control points, so it is fair (no wiggles).
Curves that reach the centreline are fitted together with their mirror image, so they end on
y = 0 square to the centre plane (a clean mirror seam).
"""
import sys, json, numpy as np, trimesh
from scipy.interpolate import make_lsq_spline
from scipy.ndimage import gaussian_filter1d
C = json.load(open(sys.argv[1])); P = json.load(open(sys.argv[2])); m = trimesh.load(sys.argv[3], force='mesh')
OUT = sys.argv[4]


def pts(k, xmin=-1e9, xmax=1e9, rev=False):
    Q = np.array(C[k]["points"]); Q = Q[(Q[:, 0] >= xmin) & (Q[:, 0] <= xmax)]
    return Q[::-1] if rev else Q


def chord(Q):
    t = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Q, axis=0), axis=1))]
    return t / t[-1]


def lsq(Q, n_ctrl, closed=False, n_out=200):
    """Least-squares cubic B-spline with n_ctrl control points through ordered points Q."""
    Q = np.asarray(Q, float)
    if closed:
        Q = np.r_[Q[-8:], Q, Q[:8]]                      # wrap so the seam is smooth too
    t = chord(Q)
    k = 3; inner = np.linspace(0, 1, n_ctrl - k + 1)[1:-1]
    knots = np.r_[[0.0] * (k + 1), inner, [1.0] * (k + 1)]
    S = [make_lsq_spline(t, Q[:, j], knots, k) for j in range(3)]
    if closed:
        a, b = t[8], t[-9]; u = np.linspace(a, b, n_out)
    else:
        u = np.linspace(0, 1, n_out)
    return np.c_[[s(u) for s in S]].T


def to_centre(Q, n_ctrl):
    """Fit Q (ending near y = 0) together with its mirror image -> ends exactly on y = 0, square."""
    Q = np.asarray(Q, float)
    if Q[0, 1] < Q[-1, 1]: Q = Q[::-1]                  # start at the centre end
    full = np.r_[(Q * [1, -1, 1])[::-1], Q]
    F_ = lsq(full, 2 * n_ctrl, n_out=400)
    half = F_[F_[:, 1] <= 0]
    half = half[np.argsort(-half[:, 1])] if False else half
    if half[0, 1] < half[-1, 1]: half = half[::-1]
    half[0, 1] = 0.0
    return half


def u_shape(Q, n_ctrl):
    """Open curve with BOTH ends on the centreline (a U): closed fit with its mirror image."""
    Q = np.asarray(Q, float)
    full = np.r_[Q, (Q * [1, -1, 1])[::-1]]
    F_ = lsq(full, 2 * n_ctrl, closed=True, n_out=500)
    return F_[F_[:, 1] <= 0.5]


cur = {}
# ---- longitudinal lines
cp = np.array(C["centre_profile"]["raw"]); cp = cp[np.argsort(cp[:, 0])]
cp[:, 2] = gaussian_filter1d(cp[:, 2], 2)
cur["centre_profile"] = lsq(cp[::3], 16)
cur["centre_profile"][:, 1] = 0.0
cur["shoulder"] = lsq(pts("X00"), 9)
cur["canopy_base"] = lsq(pts("X01"), 7)
cur["canopy_side_edge"] = lsq(np.r_[pts("X17"), pts("X08")], 7)
cur["roof_crown_edge"] = lsq(pts("X05"), 6)
cur["sill"] = lsq(pts("X02"), 4)
# ---- side intake: closed loop  top rim (front -> rear) -> bottom rim (rear -> front) -> front edge (up)
loop = np.r_[pts("X03", xmin=-780), pts("X04", rev=True), pts("Z09")]
cur["side_intake"] = lsq(loop, 14, closed=True, n_out=400)
# ---- tail
cur["deck_rear_edge"] = to_centre(pts("Y07"), 4)
cur["light_band"] = u_shape(np.r_[pts("Y00"), pts("Y03")[::-1]], 7)
cur["diffuser_opening"] = u_shape(np.r_[pts("Y05"), pts("Z10")[::-1], pts("Y09")[::-1]], 8)
cur["tail_side_corner"] = lsq(pts("Z00"), 5)
# ---- nose
cur["hood_front_edge"] = to_centre(pts("Y04"), 4)
cur["nose_bottom_edge"] = to_centre(pts("Y01"), 4)
# ---- nose corner intake: traced from the recess depth map, faired as a closed curve
import os
if os.path.exists("front_recesses.json"):
    fr = json.load(open("front_recesses.json"))
    if fr:
        cur["front_corner_intake"] = lsq(np.array(max(fr, key=len)), 10, closed=True, n_out=300)
# ---- wheel-arch lips: well cylinder meets the body side (exact circle in side view)
V = m.vertices
for k, gap in (("front", 12.0), ("rear", 8.0)):
    w = P[k]; rw = w["r"] + gap
    a0 = np.arcsin(np.clip((115.0 - w['z']) / rw, -1, 1))          # down to the floor on both sides
    th = np.linspace(np.pi - a0, a0, 120)
    vv = V[(V[:, 1] < 0) & (np.abs(np.hypot(V[:, 0] - w["x"], V[:, 2] - w["z"]) - rw) < 4)]
    ang = np.arctan2(vv[:, 2] - w["z"], vv[:, 0] - w["x"])
    yl = np.array([(-vv[np.abs(ang - t) < 0.06, 1]).max() if (np.abs(ang - t) < 0.06).any() else np.nan for t in th])
    ok = ~np.isnan(yl); yl = np.interp(np.arange(len(th)), np.where(ok)[0], yl[ok]); yl = gaussian_filter1d(yl, 4, mode='nearest')
    ring = np.c_[w["x"] + rw * np.cos(th), -yl, w["z"] + rw * np.sin(th)]
    ring = ring[ring[:, 2] > 110]
    cur[f"{k}_arch_lip"] = lsq(ring, 8)
json.dump({k: v.tolist() for k, v in cur.items()}, open(OUT, "w"))
for k, v in cur.items():
    print("%-18s pts %4d  x %5.0f..%5.0f  y %5.0f..%5.0f  z %5.0f..%5.0f" % (k, len(v), v[:, 0].min(), v[:, 0].max(), v[:, 1].min(), v[:, 1].max(), v[:, 2].min(), v[:, 2].max()))

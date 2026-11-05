"""Wheels, floor plane and wheel-region (well) cut volumes from the wrapped STL."""
import sys, json, numpy as np, trimesh
m = trimesh.load(sys.argv[1], force='mesh')
V, N = m.vertices, m.vertex_normals
P = {}
AX = {"front": -1297.0, "rear": 1356.0}         # axle x from the full outer-face circles (both sides agree)
FACE = {"front": (630.0, 990.0), "rear": (630.0, 1009.0)}
WALL = {"front": 558.0, "rear": 545.0}           # body-side wall of the slot
for lab, x0 in AX.items():
    zs, rs, xs = [], [], []
    for s in (1, -1):
        y = V[:, 1] * s
        d = np.hypot(V[:, 0] - x0, V[:, 2] - 396)
        radial = ((V[:, 0] - x0) * N[:, 0] + (V[:, 2] - 396) * N[:, 2]) / np.maximum(d, 1)
        sel = (y > 720) & (y < 900) & (d > 300) & (d < 470) & (radial > 0.9) & (V[:, 2] < 396)
        Q = V[sel]
        for _ in range(5):   # free circle fit in x-z: (x,z) on circle (xc, zc, r)
            A = np.c_[2 * Q[:, 0], 2 * Q[:, 2], np.ones(len(Q))]; b = Q[:, 0] ** 2 + Q[:, 2] ** 2
            xc, zc, c = np.linalg.lstsq(A, b, rcond=None)[0]; r = np.sqrt(c + xc * xc + zc * zc)
            res = np.abs(np.hypot(Q[:, 0] - xc, Q[:, 2] - zc) - r)
            Q = Q[res < max(3 * np.median(res), 2)]
        res = np.abs(np.hypot(Q[:, 0] - xc, Q[:, 2] - zc) - r)
        xs.append(xc)
        print(f"{lab} {'+Y' if s > 0 else '-Y'}: xc {xc:.1f} zc {zc:.1f}  r {r:.1f}  bottom z {zc - r:.1f}  (n {len(Q)}, p90 {np.percentile(res, 90):.1f} mm)")
        zs.append(zc); rs.append(r)
    P[lab] = dict(x=float(np.mean(xs)), z=float(np.mean(zs)), r=float(np.mean(rs)), y_in=FACE[lab][0], y_out=FACE[lab][1], wall=WALL[lab])
# floor: robust plane through the downward faces under the body
fc, fn = m.triangles_center, m.face_normals
cand = (fn[:, 2] < -0.95) & (fc[:, 2] < 200); Q = fc[cand]; sel = np.ones(len(Q), bool)
for _ in range(6):
    A = np.c_[np.ones(sel.sum()), Q[sel, 0], Q[sel, 1]]
    coef, *_ = np.linalg.lstsq(A, Q[sel, 2], rcond=None)
    res = Q[:, 2] - np.c_[np.ones(len(Q)), Q[:, 0], Q[:, 1]] @ coef
    sel = np.abs(res) < 6
coef[2] = 0.0   # symmetric car: no roll
print("floor: z = %.1f %+.5f x  (rake %.2f deg; z %.1f at nose x=-2000, %.1f at tail x=2000)  inliers %d  p90 %.1f mm" %
      (coef[0], coef[1], np.degrees(np.arctan(coef[1])), coef[0] - 2000 * coef[1], coef[0] + 2000 * coef[1], sel.sum(), np.percentile(np.abs(res[sel]), 90)))
fl = Q[sel]
P["floor"] = dict(z0=float(coef[0]), kx=float(coef[1]), x_min=float(fl[:, 0].min()), x_max=float(fl[:, 0].max()),
                  y_max=float(np.abs(fl[:, 1]).max()))
# fender clearance above each tyre: smallest distance from axle to the body's outer surface above the wheel
for lab in ("front", "rear"):
    w = P[lab]
    ang = np.arctan2(V[:, 2] - w["z"], V[:, 0] - w["x"])
    d = np.hypot(V[:, 0] - w["x"], V[:, 2] - w["z"])
    top = (np.abs(V[:, 1]) > w["wall"]) & (np.abs(V[:, 1]) < w["y_out"] + 30) & (ang > np.radians(20)) & (ang < np.radians(160)) & (N[:, 2] > 0.3)
    w["fender_min"] = float(np.percentile(d[top & (d > w["r"])], 1))
    print(f"{lab}: tyre r {w['r']:.1f}, nearest fender-top surface {w['fender_min']:.0f} mm from axle -> room {w['fender_min'] - w['r']:.0f} mm")
json.dump(P, open("parts.json", "w"), indent=1)

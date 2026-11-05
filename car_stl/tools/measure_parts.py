import sys, json, numpy as np, trimesh
m = trimesh.load(sys.argv[1], force='mesh')
V, N = m.vertices, m.vertex_normals
def circ(P, it=4, keep=3.0):
    sel = np.ones(len(P), bool)
    for _ in range(it):
        Q = P[sel]
        A = np.c_[2 * Q[:, 0], 2 * Q[:, 1], np.ones(len(Q))]; b = (Q ** 2).sum(1)
        cx, cz, c = np.linalg.lstsq(A, b, rcond=None)[0]; r = np.sqrt(c + cx * cx + cz * cz)
        res = np.abs(np.hypot(P[:, 0] - cx, P[:, 1] - cz) - r)
        sel = res < max(keep * np.median(res[sel]), 2.0)
    return cx, cz, r, res[sel], sel.sum()
out = {}
for lab, (x0, z0) in (("front", (-1297.0, 396.0)), ("rear", (1356.0, 407.0))):
    out[lab] = {}
    for s in (1, -1):
        y = V[:, 1] * s
        d = np.hypot(V[:, 0] - x0, V[:, 2] - z0)
        radial = ((V[:, 0] - x0) * N[:, 0] + (V[:, 2] - z0) * N[:, 2]) / np.maximum(d, 1)
        tread = (y > 720) & (y < 900) & (d > 300) & (d < 470) & (radial > 0.9) & (V[:, 2] < z0)
        cx, cz, r, res, n = circ(V[tread][:, [0, 2]])
        near = (np.abs(V[:, 0] - x0) < 150) & (np.abs(V[:, 2] - z0) < 120)
        yy = y[near & (y > 500) & (y < 700)]
        outer = y[near & (y > 900)].max()
        # arch: fender points just outboard, above the axle, facing the wheel (inward radial normal)
        lip = (y > outer - 80) & (d > 380) & (d < 520) & (V[:, 2] > cz + 50) & (radial < -0.6)
        if lip.sum() > 10:
            ax_, az_, ar, ares, an = circ(V[lip][:, [0, 2]])
        else:
            ar, ares, an = float('nan'), np.array([0.0]), 0
        w = dict(cx=float(cx), cz=float(cz), r=float(r), fit_p90=float(np.percentile(res, 90)), n=int(n),
                 slot_inner=float(np.percentile(yy, 3)), slot_outer=float(np.percentile(yy, 97)),
                 outer_y=float(outer), arch_r=float(ar), arch_p90=float(np.percentile(ares, 90)), arch_n=int(an))
        out[lab]["+Y" if s > 0 else "-Y"] = w
        print(f"{lab:5s} {'+Y' if s > 0 else '-Y'}: centre x {cx:7.1f} z {cz:5.1f}  tyre r {r:5.1f} (p90 {w['fit_p90']:.1f} mm, n {n})"
              f"  slot |y| {w['slot_inner']:.0f}..{w['slot_outer']:.0f}  outer |y| {outer:.0f}  arch r {ar:.0f} (p90 {w['arch_p90']:.1f}, n {an})")
# floor: robust plane through downward faces under the body
fc, fn = m.triangles_center, m.face_normals
cand = (fn[:, 2] < -0.95) & (fc[:, 2] < 200)
P = fc[cand]; sel = np.ones(len(P), bool)
for _ in range(6):
    A = np.c_[np.ones(sel.sum()), P[sel, 0], P[sel, 1]]
    coef, *_ = np.linalg.lstsq(A, P[sel, 2], rcond=None)
    res = P[:, 2] - np.c_[np.ones(len(P)), P[:, 0], P[:, 1]] @ coef
    sel = np.abs(res) < 6
FA = m.area_faces[cand][sel]
print("floor plane z = %.2f %+.5f x %+.5f y  (rake %.3f deg, roll %.3f deg)  inliers %d  area %.2f m2  p90 |res| %.1f mm" %
      (*coef, np.degrees(np.arctan(coef[1])), np.degrees(np.arctan(coef[2])), sel.sum(), FA.sum() / 1e6, np.percentile(np.abs(res[sel]), 90)))
print("floor inlier extent x %.0f..%.0f  y %.0f..%.0f" % (P[sel, 0].min(), P[sel, 0].max(), P[sel, 1].min(), P[sel, 1].max()))
np.save("floor_inliers.npy", P[sel])
out["floor"] = dict(z0=float(coef[0]), kx=float(coef[1]), ky=float(coef[2]))
json.dump(out, open("parts_measure.json", "w"), indent=1)

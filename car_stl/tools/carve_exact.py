"""Mark mesh faces that lie on exact analytic surfaces (within TOL and with matching normal),
label them as finished, and report how much of the half-car dough remains."""
import sys, json, numpy as np, trimesh
sys.path.insert(0, "/home/user/Sultanidinov-Sultan_CV/car")
from shade import render_sheet, vertex_normals
m = trimesh.load(sys.argv[1], force='mesh'); P = json.load(open(sys.argv[2]))
TOL, COS = 3.0, np.cos(np.radians(12))
GAP = {"front": 12.0, "rear": 8.0}
F = m.faces; c = m.triangles_center; n = m.face_normals; A = m.area_faces
half = c[:, 1] <= 5
SURF = []                                   # (name, distance fn, normal fn)
FLOORS = ((-1950, -1000, 96.8, "front floor plane"), (-950, 1700, 114.5, "main floor plane"))
for x0, x1, zf, name in FLOORS:
    SURF.append((name, lambda c, x0=x0, x1=x1, zf=zf: np.where((c[:, 0] > x0) & (c[:, 0] < x1), c[:, 2] - zf, 1e9),
                 lambda c: np.tile([0, 0, -1.0], (len(c), 1))))
for lab in ("front", "rear"):
    w = P[lab]; rw = w["r"] + GAP[lab]
    SURF.append((f"{lab} slot wall plane", lambda c, w=w: c[:, 1] + w["wall"],
                 lambda c: np.tile([0, -1, 0], (len(c), 1))))
    def cyl_d(c, w=w, rw=rw): return np.hypot(c[:, 0] - w["x"], c[:, 2] - w["z"]) - rw
    def cyl_n(c, w=w):
        v = np.c_[w["x"] - c[:, 0], np.zeros(len(c)), w["z"] - c[:, 2]]   # well surface faces the axle
        return v / np.linalg.norm(v, axis=1)[:, None]
    SURF.append((f"{lab} well cylinder", lambda c, f=cyl_d, w=w: np.where(c[:, 2] > w["z"] - 1, f(c), 1e9), cyl_n))
    for sgn in (-1, 1):   # straight well walls below the axle: planes x = xc -/+ rw, facing into the well
        SURF.append((f"{lab} well wall {'front' if sgn < 0 else 'rear'}",
                     lambda c, w=w, rw=rw, sgn=sgn: np.where((c[:, 2] < w["z"] + 1) & (np.abs(c[:, 1]) > w["wall"] - 5), c[:, 0] - (w["x"] + sgn * rw), 1e9),
                     lambda c, sgn=sgn: np.tile([-sgn, 0, 0], (len(c), 1))))
lab = np.full(len(F), -1)
for k, (name, dfn, nfn) in enumerate(SURF):
    on = half & (lab < 0) & (np.abs(dfn(c)) < TOL) & (np.sum(n * nfn(c), 1) > COS)
    lab[on] = k
    print("%-22s %6d faces  %.3f m2" % (name, on.sum(), A[on].sum() / 1e6))
done = A[half & (lab >= 0)].sum(); tot = A[half].sum()
print("done %.2f of %.2f m2 (%.0f %%); dough left %.2f m2" % (done / 1e6, tot / 1e6, 100 * done / tot, (tot - done) / 1e6))
np.save(sys.argv[3], lab); json.dump([s[0] for s in SURF], open(sys.argv[3].replace(".npy", "_names.json"), "w"))
pal = np.array([[0.30, 0.55, 0.95], [0.55, 0.35, 0.90]] + [[0.30, 0.80, 0.45], [0.95, 0.55, 0.20], [0.95, 0.80, 0.25], [0.95, 0.80, 0.25]] * 2)
C = np.where((lab >= 0)[:, None], pal[np.maximum(lab, 0)], [0.86, 0.87, 0.89])
V = np.asarray(m.vertices, float)
render_sheet(V, F[half], C[half], sys.argv[4], N=vertex_normals(V, F))
# underside view
from shade import raster, rot
from PIL import Image
img = raster(V, F[half], C[half], rot(0, np.pi), 1600, 520, N=vertex_normals(V, F))
Image.fromarray(img).save(sys.argv[4].replace(".png", "_bottom.png"))

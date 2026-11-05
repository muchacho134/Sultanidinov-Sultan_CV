"""Render the half-car CAD: fitted patches (one colour each) + finished faces + wheels;
and a deviation map (mesh vertices coloured by distance to their patch surface)."""
import sys, json, numpy as np, trimesh
sys.path.insert(0, "/home/user/Sultanidinov-Sultan_CV/car")
import matplotlib; matplotlib.use("Agg"); import matplotlib.cm as cm
from overlay import load, mesh
from shade import render_sheet, vertex_normals
from build_car import faces as occ_faces
patches, done, out = sys.argv[1], sys.argv[2], sys.argv[3]
rng = np.random.default_rng(5)
Vs, Fs, Cs, off = [], [], [], 0
def add(shape, col_fn):
    global off
    for f in occ_faces(shape):
        v, t = mesh(f, 0.6)
        if len(t) == 0: continue
        Vs.append(np.asarray(v, float)); Fs.append(np.asarray(t) + off); Cs.append(np.tile(col_fn(), (len(t), 1))); off += len(v)
add(load(patches), lambda: rng.uniform(0.45, 0.95, 3) * [0.95, 0.97, 1.0])
names = json.load(open(done.replace(".brep", "_names.json")))
it = iter(names)
COL = {"floor": (0.55, 0.35, 0.9), "cylinder": (0.95, 0.55, 0.2), "slot": (0.3, 0.8, 0.45)}
add(load(done), lambda: COL[(lambda n: "floor" if "floor" in n else ("cylinder" if "cylinder" in n else "slot"))(next(it))])
for wk in ("Wheel_FR", "Wheel_RR"):
    add(load(f"part_{wk}.brep"), lambda: (0.12, 0.12, 0.14))
V, F, C = np.vstack(Vs), np.vstack(Fs), np.vstack(Cs)
render_sheet(V, F, C, out, N=vertex_normals(V, F))
# deviation map on the mesh
if len(sys.argv) > 5:
    m = trimesh.load(sys.argv[4], force='mesh'); dev = np.load(sys.argv[5])
    Fm = m.faces[m.triangles_center[:, 1] <= 5]
    d = np.nanmax(dev[Fm], axis=1)
    t = np.clip(np.nan_to_num(d, nan=-1) / 5.0, 0, 1)        # 0..5 mm
    C2 = cm.turbo(t)[:, :3]; C2[np.isnan(d)] = (0.8, 0.8, 0.82)
    Vm = np.asarray(m.vertices, float)
    render_sheet(Vm, Fm, C2, out.replace(".png", "_deviation.png"), N=vertex_normals(Vm, m.faces))

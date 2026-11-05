"""Render finished CAD faces (coloured) together with the remaining dough mesh (grey); well close-ups."""
import sys, json, numpy as np, trimesh
from PIL import Image
sys.path.insert(0, "/home/user/Sultanidinov-Sultan_CV/car")
from overlay import load, mesh
from shade import raster, rot, vertex_normals, render_sheet
from build_car import faces as occ_faces
m = trimesh.load(sys.argv[1], force='mesh'); lab = np.load(sys.argv[2]); P = json.load(open(sys.argv[3]))
cad = load(sys.argv[4]); names = json.load(open(sys.argv[4].replace(".brep", "_names.json")))
COL = {"floor": (0.55, 0.35, 0.90), "cylinder": (0.95, 0.55, 0.20), "slot": (0.30, 0.80, 0.45)}
Vs, Fs, Cs, Ns = [], [], [], []
dough = (lab < 0) & (m.triangles_center[:, 1] <= 5)
V = np.asarray(m.vertices, float); F = m.faces[dough]
Vs.append(V); Fs.append(F); Cs.append(np.tile([0.86, 0.87, 0.89], (len(F), 1))); Ns.append(vertex_normals(V, m.faces))
off = len(V)
for f, n_ in zip(occ_faces(cad), names):
    v, t = mesh(f, 0.8)
    if len(t) == 0: continue
    key = "floor" if "floor" in n_ else ("cylinder" if "cylinder" in n_ else "slot")
    Vs.append(v); Fs.append(t + off); Cs.append(np.tile(COL[key], (len(t), 1)))
    v_, t_ = np.asarray(v, float), np.asarray(t)
    Ns.append(vertex_normals(v_, t_)); off += len(v)
V, F, C, N = np.vstack(Vs), np.vstack(Fs), np.vstack(Cs), np.vstack(Ns)
render_sheet(V, F, C, sys.argv[5], N=N)
c = V[F].mean(1); tiles = []
for w in (P["front"], P["rear"]):
    near = (np.abs(c[:, 0] - w["x"]) < 750) & (c[:, 1] > -1100)
    Fs_ = F[near]; used = np.unique(Fs_); idx = np.full(len(V), -1); idx[used] = np.arange(len(used))
    for R in (rot(0, np.pi), rot(np.radians(-25), -np.radians(110)), rot(np.radians(25), -np.radians(110))):
        tiles.append(raster(V[used], idx[Fs_], C[near], R, 700, 520, N=N[used]))
rows = [np.concatenate(tiles[i:i + 3], 1) for i in (0, 3)]
Image.fromarray(np.concatenate(rows, 0)).save(sys.argv[5].replace(".png", "_wells.png"))

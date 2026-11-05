"""Render the half car (y <= 0): body mesh grey (optional per-face colours), extra meshes dark."""
import sys, numpy as np, trimesh
sys.path.insert(0, "/home/user/Sultanidinov-Sultan_CV/car")
from shade import render_sheet, vertex_normals
body = trimesh.load(sys.argv[1], force='mesh')
Vs, Fs, Cs = [], [], []; off = 0
keep = body.triangles_center[:, 1] <= 5
Vb, Fb = np.asarray(body.vertices, float), np.asarray(body.faces)[keep]
Vs.append(Vb); Fs.append(Fb); Cs.append(np.tile([0.86, 0.87, 0.89], (len(Fb), 1))); off = len(Vb)
for path in sys.argv[3:]:
    x = trimesh.load(path, force='mesh'); x.unmerge_vertices()   # flat-shaded cylinders
    k = x.triangles_center[:, 1] <= 5
    Vs.append(np.asarray(x.vertices, float)); Fs.append(np.asarray(x.faces)[k] + off)
    Cs.append(np.tile([0.13, 0.13, 0.15], (k.sum(), 1))); off += len(x.vertices)
V, F, C = np.vstack(Vs), np.vstack(Fs), np.vstack(Cs)
render_sheet(V, F, C, sys.argv[2], N=vertex_normals(V, F))

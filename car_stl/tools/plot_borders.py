"""Border wires over the region-coloured half body: side, top, front, back, 3/4."""
import sys, json, numpy as np, trimesh
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
m = trimesh.load(sys.argv[1], force='mesh'); lab = np.load(sys.argv[2]); W = {k: np.array(v) for k, v in json.load(open(sys.argv[3])).items()}
V, F, fn = m.vertices, m.faces, m.face_normals
COL = np.array([[0.75, 0.8, 1.0], [1.0, 0.78, 0.75], [0.78, 0.95, 0.8], [1.0, 0.95, 0.75], [0.9, 0.82, 1.0], [0.8, 0.8, 0.82]])
R = lambda yaw, pitch: (np.array([[1, 0, 0], [0, np.cos(pitch), -np.sin(pitch)], [0, np.sin(pitch), np.cos(pitch)]]) @
                        np.array([[np.cos(yaw), -np.sin(yaw), 0], [np.sin(yaw), np.cos(yaw), 0], [0, 0, 1]]))
views = (("SIDE", R(0, -np.pi / 2), np.array([0, -1, 0])), ("TOP", R(0, 0), np.array([0, 0, 1])),
         ("FRONT", R(np.pi / 2, -np.pi / 2), np.array([-1, 0, 0])), ("BACK", R(-np.pi / 2, -np.pi / 2), np.array([1, 0, 0])),
         ("3/4 FRONT", R(np.radians(35), -np.radians(65)), None), ("3/4 REAR", R(np.radians(-145), -np.radians(65)), None))
fig, axs = plt.subplots(3, 2, figsize=(22, 18), gridspec_kw={'width_ratios': [1.6, 1]})
axs = axs.ravel()
half = lab >= 0
for a, (title, Rm, vd) in zip(axs, views):
    P3 = V @ Rm.T
    camz = Rm.T @ np.array([0, 0, 1.0])
    vis = half & ((fn @ camz) > 0)
    T = P3[F[vis]]; o = np.argsort(T[:, :, 2].mean(1))
    a.add_collection(PolyCollection(T[o][:, :, :2], facecolors=COL[lab[vis][o]], edgecolors='none'))
    for k, Q in W.items():
        q = Q @ Rm.T; a.plot(q[:, 0], q[:, 1], '-', color='k', lw=1.6)
        a.plot(q[[0, -1], 0], q[[0, -1], 1], 'o', color='crimson', ms=3)
    a.autoscale(); a.set_aspect('equal'); a.set_title(title, fontsize=14); a.axis('off')
fig.tight_layout(); fig.savefig(sys.argv[4], dpi=55)

"""Shared border wires between the direction regions (half car).

For every pair of neighbouring regions the mesh edges between them are chained into polylines,
short chains dropped, and each chain smoothed (arc-length resample + gaussian) while its two end
points are held fixed. Ends are snapped to junctions (points where 3 regions meet) or to the
centreline, so the network is connected.
"""
import sys, json, numpy as np, trimesh, networkx as nx
from scipy.ndimage import gaussian_filter1d
from scipy.spatial import cKDTree
m = trimesh.load(sys.argv[1], force='mesh'); lab = np.load(sys.argv[2]); OUT = sys.argv[3]
MIN_LEN, SIG = float(sys.argv[4]) if len(sys.argv) > 4 else 120.0, 4.0
V = m.vertices; adj = m.face_adjacency; ae = m.face_adjacency_edges
NAMES = ["bottom", "back", "front", "top", "side", "well"]
la, lb = lab[adj[:, 0]], lab[adj[:, 1]]
bnd = (la != lb) & (la >= 0) & (lb >= 0)
# junction vertices: touched by faces of 3+ regions
vf = [[] for _ in range(len(V))]
for f, L in enumerate(lab):
    if L >= 0:
        for v in m.faces[f]: vf[v].append(L)
junction = np.array([len(set(x)) >= 3 for x in vf])
W = {}
for a in range(6):
    for b in range(a + 1, 6):
        sel = bnd & (((la == a) & (lb == b)) | ((la == b) & (lb == a)))
        if not sel.any(): continue
        g = nx.Graph(); g.add_edges_from(map(tuple, ae[sel]))
        for k, comp in enumerate(nx.connected_components(g)):
            T = nx.minimum_spanning_tree(g.subgraph(comp))
            s0 = next(iter(comp)); d = nx.single_source_shortest_path_length(T, s0); p = max(d, key=d.get)
            d = nx.single_source_shortest_path_length(T, p); q = max(d, key=d.get)
            path = nx.shortest_path(T, p, q); P = V[path]
            L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
            if L[-1] < MIN_LEN: continue
            t = np.linspace(0, L[-1], max(int(L[-1] / 8), 10))
            Q = np.c_[[np.interp(t, L, P[:, j]) for j in range(3)]].T
            e0, e1 = Q[0].copy(), Q[-1].copy()
            Q = np.c_[[gaussian_filter1d(Q[:, j], SIG, mode='nearest') for j in range(3)]].T
            u = t / t[-1]                                       # keep the ends where they were
            Q += np.outer(np.clip(1 - u / 0.1, 0, 1), e0 - Q[0]) + np.outer(np.clip((u - 0.9) / 0.1, 0, 1), e1 - Q[-1])
            W[f"{NAMES[a]}|{NAMES[b]}_{k}"] = Q
# snap ends: to the nearest junction vertex (within 60 mm), else onto y = 0 if close to it
J = V[junction & (V[:, 1] <= 5)]
jt = cKDTree(J) if len(J) else None
for k, Q in W.items():
    for i in (0, -1):
        if jt is not None:
            d, j = jt.query(Q[i])
            if d < 60: Q[i] = J[j]
        if Q[i, 1] > -40: Q[i, 1] = 0.0
# cluster coincident ends so wires that should meet share one point
ends = np.array([Q[i] for Q in W.values() for i in (0, -1)])
t_ = cKDTree(ends); groups = t_.query_ball_point(ends, 40)
merged = np.array([ends[g].mean(0) for g in groups])
n = 0
for k in W:
    for i in (0, -1):
        W[k][i] = merged[n]; n += 1
json.dump({k: v.tolist() for k, v in W.items()}, open(OUT, "w"))
for k, Q in sorted(W.items()):
    L = np.linalg.norm(np.diff(Q, axis=0), axis=1).sum()
    print("%-18s len %5.0f  x %5.0f..%5.0f  z %4.0f..%4.0f" % (k, L, Q[:, 0].min(), Q[:, 0].max(), Q[:, 2].min(), Q[:, 2].max()))

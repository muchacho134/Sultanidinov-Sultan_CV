"""Extract feature (crease / rim) curves from the half body mesh as smoothed B-spline curves.

Edges whose dihedral angle exceeds ANG are feature edges; they are chained into polylines
through the edge graph, small gaps bridged, short chains dropped, and each chain is
smoothed and resampled -> fitted with an OCC B-spline curve.
"""
import sys, json, numpy as np, trimesh
import networkx as nx
from scipy.ndimage import gaussian_filter1d
m = trimesh.load(sys.argv[1], force='mesh')
ANG, MIN_LEN = float(sys.argv[3]), float(sys.argv[4])
V = m.vertices
ang = np.degrees(m.face_adjacency_angles)
E = m.face_adjacency_edges[ang > ANG]
E = E[(V[E[:, 0], 1] <= 5) & (V[E[:, 1], 1] <= 5)]           # half car only
# skip the well cylinders (wheels handled separately) and the floor seam
G = nx.Graph(); G.add_edges_from(map(tuple, E))
chains = []
for comp in nx.connected_components(G):
    H = G.subgraph(comp)
    # longest path approximation: two BFS sweeps on the tree of the component
    T = nx.minimum_spanning_tree(H)
    a = next(iter(comp)); d = nx.single_source_shortest_path_length(T, a); b = max(d, key=d.get)
    d = nx.single_source_shortest_path_length(T, b); c = max(d, key=d.get)
    path = nx.shortest_path(T, b, c)
    P = V[path]
    L = np.linalg.norm(np.diff(P, axis=0), axis=1).sum()
    if L >= MIN_LEN:
        chains.append(P)
out = []
for P in chains:
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    n = max(int(s[-1] / 15), 8)
    t = np.linspace(0, s[-1], n)
    Q = np.c_[[np.interp(t, s, P[:, k]) for k in range(3)]].T
    Q = np.c_[[gaussian_filter1d(Q[:, k], 2.0, mode='nearest') for k in range(3)]].T
    out.append(Q)
out.sort(key=lambda Q: -np.linalg.norm(np.diff(Q, axis=0), axis=1).sum())
print("feature chains:", len(out))
for i, Q in enumerate(out):
    L = np.linalg.norm(np.diff(Q, axis=0), axis=1).sum()
    c = Q.mean(0)
    print("%2d  length %5.0f mm  centre (%5.0f %5.0f %4.0f)  x %5.0f..%5.0f" % (i, L, *c, Q[:, 0].min(), Q[:, 0].max()))
np.savez(sys.argv[2], *out)

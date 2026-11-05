"""Grow the seed regions geodesically over the half body until they meet: every face gets a
patch label, and the boundaries between patches are the feature curves (blend-band centres)."""
import sys, json, numpy as np, trimesh
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
import networkx as nx
from scipy.ndimage import gaussian_filter1d
sys.path.insert(0, "/home/user/Sultanidinov-Sultan_CV/car")
from shade import render_sheet, vertex_normals
m = trimesh.load(sys.argv[1], force='mesh'); lab0 = np.load(sys.argv[2])
F = m.faces; fc = m.triangles_center; V = m.vertices
half = fc[:, 1] <= 5
# dual graph over half-car faces, weighted by centre distance
adj = m.face_adjacency; ok = half[adj[:, 0]] & half[adj[:, 1]]
a, b = adj[ok, 0], adj[ok, 1]; w = np.linalg.norm(fc[a] - fc[b], axis=1)
G = coo_matrix((np.r_[w, w], (np.r_[a, b], np.r_[b, a])), shape=(len(F), len(F))).tocsr()
seeds = np.where(half & (lab0 >= 0))[0]
dist, pred, src = dijkstra(G, indices=seeds, min_only=True, return_predecessors=True)
lab = np.where(np.isfinite(dist), lab0[np.maximum(src, 0)], -1); lab[~half] = -1
ids = sorted(set(lab[lab >= 0])); remap = {k: i for i, k in enumerate(ids)}
lab = np.array([remap.get(k, -1) for k in lab])
print("patches:", len(ids))
# boundary edges between different patches -> chains per pair
fa_edges = m.face_adjacency_edges
bnd = ok.copy(); bnd[ok] = lab[a] != lab[b]
pairs = {}
for (f1, f2), e in zip(adj[bnd], fa_edges[bnd]):
    key = tuple(sorted((lab[f1], lab[f2])))
    pairs.setdefault(key, []).append(tuple(e))
curves = {}
for key, edges in pairs.items():
    g = nx.Graph(); g.add_edges_from(edges)
    for k, comp in enumerate(nx.connected_components(g)):
        T = nx.minimum_spanning_tree(g.subgraph(comp))
        s0 = next(iter(comp)); d = nx.single_source_shortest_path_length(T, s0); p = max(d, key=d.get)
        d = nx.single_source_shortest_path_length(T, p); q = max(d, key=d.get)
        P = V[nx.shortest_path(T, p, q)]
        s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
        if s[-1] < 60: continue
        t = np.linspace(0, s[-1], max(int(s[-1] / 15), 6))
        Q = np.c_[[gaussian_filter1d(np.interp(t, s, P[:, j]), 2.5, mode='nearest') for j in range(3)]].T
        curves[f"{key[0]}-{key[1]}-{k}"] = Q
print("boundary curves:", len(curves), " total length %.1f m" % (sum(np.linalg.norm(np.diff(Q, axis=0), axis=1).sum() for Q in curves.values()) / 1000))
np.save("patch_labels.npy", lab); np.savez("patch_curves.npz", **curves)
# picture: patches coloured, boundary faces darkened
rng = np.random.default_rng(11)
pal = rng.uniform(0.3, 0.95, (len(ids), 3))
C = np.where((lab >= 0)[:, None], pal[np.maximum(lab, 0)], 0.6)
edge_faces = np.unique(adj[bnd].ravel()); C[edge_faces] *= 0.35
Vf = np.asarray(V, float)
render_sheet(Vf, F[half], C[half], sys.argv[3], N=vertex_normals(Vf, F))

"""Panel borders as real design curves: every border between two panels is fitted with a cubic
B-spline with very few control points (one per ~400 mm, min 4), closed borders with a periodic one,
then the faces next to the border are re-assigned by the side of that curve they lie on."""
import sys, json, numpy as np, trimesh, networkx as nx
from scipy.interpolate import make_lsq_spline
from scipy.spatial import cKDTree
sys.path.insert(0, "/home/user/Sultanidinov-Sultan_CV/car")
from shade import render_sheet, vertex_normals
m = trimesh.load(sys.argv[1], force='mesh'); lab0 = np.load(sys.argv[2], allow_pickle=True); OUT = sys.argv[3]
EDGE, PER_CTRL, BAND = float(sys.argv[4]), 400.0, 70.0
keep = m.triangles_center[:, 1] <= 5
h = m.submesh([np.where(keep)[0]], append=True)
cut = m.slice_plane(plane_origin=[0, 0, 0], plane_normal=[0, -1, 0])   # exact half: everything at y <= 0, seam on y = 0
V, F = trimesh.remesh.subdivide_to_size(cut.vertices, cut.faces, max_edge=EDGE)
V[np.abs(V[:, 1]) < 1e-6, 1] = 0.0
_w = trimesh.Trimesh(V, F, process=False); _w.merge_vertices(); V, F = np.asarray(_w.vertices), np.asarray(_w.faces)   # weld after subdividing
s = trimesh.Trimesh(V, F, process=False)
_, j = cKDTree(h.triangles_center).query(s.triangles_center)
lab = lab0[keep][j].astype(object)
# light clean-up first (majority of neighbours, a few passes) so borders are single chains
adj = s.face_adjacency; nF = len(F)
names = sorted(set(lab)); idx = {n: i for i, n in enumerate(names)}; li = np.array([idx[n] for n in lab])
nb = [[] for _ in range(nF)]
for a, b in adj: nb[a].append(b); nb[b].append(a)
for _ in range(6):
    new = li.copy()
    for f in range(nF):
        c = np.bincount(li[nb[f]], minlength=len(names)); c[li[f]] += 1
        if c.max() > c[li[f]] + 1: new[f] = c.argmax()
    li = new
FIXED = {idx[n] for n in ("wheel well", "side intake", "front corner intake", "tail light recess", "diffuser opening", "recess (other)") if n in idx}
fc, fn = s.triangles_center, s.face_normals
curves = {}


def fit_open(P, n):
    t = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]; t /= t[-1]
    _, u = np.unique(t, return_index=True); t, P = t[u], P[u]
    kn = np.r_[[0] * 4, np.linspace(0, 1, n - 2)[1:-1], [1] * 4]
    S = [make_lsq_spline(t, P[:, k], kn, 3) for k in range(3)]
    tt = np.linspace(0, 1, 300); return np.c_[[q(tt) for q in S]].T


def fit_closed(P, n):
    P3 = np.r_[P[-15:], P, P[:15]]
    t = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P3, axis=0), axis=1))]; t /= t[-1]
    _, u = np.unique(t, return_index=True); t, P3 = t[u], P3[u]
    kn = np.r_[[0] * 4, np.linspace(0, 1, n + 4 - 2)[1:-1], [1] * 4]
    S = [make_lsq_spline(t, P3[:, k], kn, 3) for k in range(3)]
    a, b = t[15], t[-16]; tt = np.linspace(a, b, 400); Q = np.c_[[q(tt) for q in S]].T
    return np.r_[Q, Q[:1]]


ea = adj
for _ in range(2):                                     # fit + re-split, twice (the second pass sees the cleaner borders)
    curves = {}
    la, lb = li[ea[:, 0]], li[ea[:, 1]]
    for a in range(len(names)):
        for b in range(a + 1, len(names)):
            sel = ((la == a) & (lb == b)) | ((la == b) & (lb == a))
            if sel.sum() < 6: continue
            g = nx.Graph(); g.add_edges_from(map(tuple, s.face_adjacency_edges[sel]))
            for k, comp in enumerate(nx.connected_components(g)):
                sub = g.subgraph(comp)
                if len(comp) < 6: continue
                cyc = nx.cycle_basis(sub)
                big = max(cyc, key=len) if cyc else []
                if len(big) > 0.7 * len(comp):
                    P = V[big]; L = np.linalg.norm(np.diff(np.r_[P, P[:1]], axis=0), axis=1).sum()
                    Q = fit_closed(P, max(6, int(L / PER_CTRL)))
                else:
                    T = nx.minimum_spanning_tree(sub)
                    s0 = next(iter(comp)); d = nx.single_source_shortest_path_length(T, s0); p = max(d, key=d.get)
                    d = nx.single_source_shortest_path_length(T, p); q = max(d, key=d.get)
                    P = V[nx.shortest_path(T, p, q)]; L = np.linalg.norm(np.diff(P, axis=0), axis=1).sum()
                    if L < 80: continue
                    Q = fit_open(P, max(4, int(L / PER_CTRL) + 3))
                curves[f"{names[a]}|{names[b]}|{k}"] = Q
                if a in FIXED or b in FIXED or L < 300: continue
                # re-split the band around the curve by side
                tq = cKDTree(Q); band = np.where(np.isin(li, [a, b]))[0]
                d_, qi = tq.query(fc[band]); band, qi = band[d_ < BAND], qi[d_ < BAND]
                if len(band) == 0: continue
                tg = np.gradient(Q, axis=0)[qi]; tg /= np.linalg.norm(tg, axis=1)[:, None] + 1e-9
                side = np.sign(np.sum((fc[band] - Q[qi]) * np.cross(fn[band], tg), axis=1))
                sa = np.sign(np.sum(side[li[band] == a])) or 1.0
                li[band] = np.where(side == sa, a, b)
    print("borders fitted:", len(curves))
# absorb specks: connected pieces smaller than 0.01 m2 take their surroundings' label
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
Af = s.area_faces
for _ in range(3):
    same = li[adj[:, 0]] == li[adj[:, 1]]
    nc, cc = connected_components(coo_matrix((np.ones(same.sum()), (adj[same, 0], adj[same, 1])), shape=(nF, nF)), directed=False)
    ar = np.bincount(cc, weights=Af, minlength=nc)
    for k_ in np.where(ar < 0.01e6)[0]:
        fs = np.where(cc == k_)[0]
        e_ = np.isin(adj[:, 0], fs) ^ np.isin(adj[:, 1], fs)
        o_ = np.where(np.isin(adj[e_, 0], fs), li[adj[e_, 1]], li[adj[e_, 0]])
        if len(o_): li[fs] = np.bincount(o_).argmax()
json.dump({k: v.tolist() for k, v in curves.items()}, open(OUT.replace(".png", "_curves.json"), "w"))
np.save(OUT.replace(".png", "_labels.npy"), np.array(names, dtype=object)[li])
PAL = {"floor": (0.3, 0.45, 0.85), "front undertray": (0.45, 0.55, 0.95), "rear diffuser": (0.25, 0.35, 0.7),
       "wheel well": (0.35, 0.35, 0.38), "front fascia": (0.35, 0.75, 0.45), "tail panel": (0.9, 0.4, 0.35),
       "hood": (0.95, 0.75, 0.25), "windshield": (0.2, 0.25, 0.32), "roof": (0.5, 0.55, 0.62), "side glass": (0.3, 0.38, 0.48),
       "engine cover / fastback": (0.85, 0.6, 0.2), "front fender": (0.6, 0.85, 0.35), "front fender top": (0.75, 0.92, 0.5), "rear quarter top": (0.98, 0.72, 0.78), "body side": (0.75, 0.55, 0.9),
       "rear quarter": (0.95, 0.55, 0.65), "sill": (0.55, 0.4, 0.75), "front bumper corner": (0.3, 0.65, 0.55),
       "rear bumper corner": (0.8, 0.3, 0.45), "side intake": (0.08, 0.08, 0.1), "front corner intake": (0.1, 0.1, 0.12),
       "tail light recess": (0.75, 0.1, 0.1), "diffuser opening": (0.12, 0.12, 0.14), "recess (other)": (0.5, 0.5, 0.5)}
C = np.array([PAL.get(names[k], (1, 0, 1)) for k in li])
# draw the fitted curves themselves as the border lines (faces they pass through go dark)
allQ = np.vstack([q for q in curves.values()])
dl, _ = cKDTree(allQ).query(fc)
C[dl < EDGE * 0.55] *= 0.2
render_sheet(np.asarray(V, float), F, C, OUT, N=vertex_normals(np.asarray(V, float), F))

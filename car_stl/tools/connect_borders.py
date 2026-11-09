"""Connected border network of the panels: nodes where 3+ panels (or a panel and the centre seam)
meet, borders traced node to node, each fitted with few control points and its ends pinned exactly
on the shared nodes -> every border end lands on other borders by construction."""
import sys, json, numpy as np, trimesh, networkx as nx
from scipy.interpolate import make_lsq_spline
from scipy.spatial import cKDTree
sys.path.insert(0, "/home/user/Sultanidinov-Sultan_CV/car")
from shade import render_sheet, vertex_normals
m = trimesh.load(sys.argv[1], force='mesh'); lab = np.load(sys.argv[2], allow_pickle=True); OUT = sys.argv[3]
EDGE, NODE_R, PER_CTRL = float(sys.argv[4]), 45.0, 400.0
cut = m.slice_plane(plane_origin=[0, 0, 0], plane_normal=[0, -1, 0])
V, F = trimesh.remesh.subdivide_to_size(cut.vertices, cut.faces, max_edge=EDGE)
V[np.abs(V[:, 1]) < 1e-6, 1] = 0.0
_w = trimesh.Trimesh(V, F, process=False); _w.merge_vertices(); V, F = np.asarray(_w.vertices), np.asarray(_w.faces)   # weld after subdividing
s = trimesh.Trimesh(V, F, process=False)
assert len(lab) == len(F), (len(lab), len(F))
# border edges: between two panels, or a panel's open edge on the seam
adj, ae = s.face_adjacency, s.face_adjacency_edges
G = nx.Graph()
for (f1, f2), e in zip(adj, ae):
    if lab[f1] != lab[f2]: G.add_edge(*map(int, e), pair=tuple(sorted((lab[f1], lab[f2]))))
bi = trimesh.grouping.group_rows(s.edges_sorted, require_count=1)
edge_face = s.edges_face
seam_v = set()
for i_ in bi:
    e = s.edges[i_]
    if abs(V[e[0], 1]) < 1e-6 and abs(V[e[1], 1]) < 1e-6:
        G.add_edge(*map(int, e), pair=(lab[edge_face[i_]], "seam")); seam_v.update(map(int, e))
# bridge small gaps in the seam (the cut can leave it in pieces)
deg1 = [v for v in seam_v if sum(1 for u in G.neighbors(v) if G.edges[v, u]["pair"][1] == "seam") == 1]
if deg1:
    P1 = V[deg1]; t1 = cKDTree(P1)
    for i_, v in enumerate(deg1):
        d_, j_ = t1.query(P1[i_], k=min(2, len(deg1)))
        if np.ndim(d_) and len(d_) > 1 and d_[1] < 80 and not G.has_edge(v, deg1[j_[1]]):
            u = deg1[j_[1]]; pv = [G.edges[v, w]["pair"] for w in G.neighbors(v) if G.edges[v, w]["pair"][1] == "seam"][0]
            G.add_edge(v, u, pair=pv)
# junction vertices -> clustered nodes
junc = [v for v in G.nodes if G.degree(v) != 2 or len({G.edges[v, u]["pair"] for u in G.neighbors(v)}) > 1]
JP = V[junc]
groups = cKDTree(JP).query_ball_point(JP, NODE_R)
node_of = {}; nodes = []
for i, g in enumerate(groups):
    if junc[i] in node_of: continue
    members = [junc[k] for k in g if junc[k] not in node_of]
    for v_ in members: node_of[v_] = len(nodes)
    nodes.append(V[members].mean(0))
nodes = np.array(nodes)
nodes[np.abs(nodes[:, 1]) < 30, 1] = 0.0
# trace chains between node vertices
is_node = set(node_of)
seen = set(); chains = []
for v in is_node:
    for u in G.neighbors(v):
        if (v, u) in seen: continue
        path = [v, u]; seen.add((v, u)); seen.add((u, v))
        while path[-1] not in is_node:
            nxt = [w for w in G.neighbors(path[-1]) if (path[-1], w) not in seen]
            if not nxt: break
            w = nxt[0]; seen.add((path[-1], w)); seen.add((w, path[-1])); path.append(w)
        chains.append(path)
# closed loops with no node (feature outlines)
rest = nx.Graph([e for e in G.edges if e not in seen and (e[1], e[0]) not in seen])
for comp in nx.connected_components(rest):
    cyc = nx.cycle_basis(rest.subgraph(comp))
    if cyc: chains.append(max(cyc, key=len) + [max(cyc, key=len)[0]])


FEATURES = ("side intake", "front corner intake", "tail light recess", "diffuser opening", "wheel well", "side glass")
def fit(P, a=None, b=None, closed=False, per=None):
    t = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    L = t[-1]
    if L < 1e-6: return P
    t /= L; _, u = np.unique(t, return_index=True); t, P = t[u], P[u]
    n = max(4, int(L / (per or PER_CTRL)) + 3)
    if len(P) <= n + 1: Q = P.copy()
    else:
        kn = np.r_[[0] * 4, np.linspace(0, 1, n - 2)[1:-1], [1] * 4]
        w = np.ones(len(t)); w[[0, -1]] = 1e3
        Q = np.c_[[make_lsq_spline(t, P[:, k], kn, 3, w=w)(np.linspace(0, 1, max(20, int(L / 8)))) for k in range(3)]].T
    if a is not None: Q[0] = a
    if b is not None: Q[-1] = b
    if closed: Q[-1] = Q[0]
    return Q


W = {}; dropped = 0
for i, ch in enumerate(chains):
    P = V[ch].copy()
    a = nodes[node_of[ch[0]]] if ch[0] in node_of else None
    b = nodes[node_of[ch[-1]]] if ch[-1] in node_of else None
    L = np.linalg.norm(np.diff(P, axis=0), axis=1).sum()
    if a is not None and b is not None and node_of[ch[0]] == node_of[ch[-1]] and L < 3 * NODE_R:
        dropped += 1; continue                          # a stub inside one node
    pair = G.edges[ch[0], ch[1]]["pair"]
    if a is None and b is None and ch[0] != ch[-1]:
        dropped += 1; continue                          # dangling fragment: touches nothing
    per = PER_CTRL if any(f in pair for f in FEATURES) else 600.0
    W[f"{pair[0]}|{pair[1]}|{i}"] = fit(P, a, b, closed=(ch[0] == ch[-1] and a is None), per=per)
# check
ends = []
for k, Q in W.items():
    if np.linalg.norm(Q[0] - Q[-1]) > 1: ends += [Q[0], Q[-1]]
ends = np.array(ends); t = cKDTree(ends)
loose = sum(1 for e, c in zip(ends, t.query(ends, k=2)[0][:, 1]) if c > 1.0)
print("nodes %d  borders %d (stubs dropped %d)  loose ends %d" % (len(nodes), len(W), dropped, loose))
json.dump({k: v.tolist() for k, v in W.items()}, open(OUT.replace(".png", ".json"), "w"))
PAL = {"floor": (0.3, 0.45, 0.85), "front undertray": (0.45, 0.55, 0.95), "rear diffuser": (0.25, 0.35, 0.7),
       "wheel well": (0.35, 0.35, 0.38), "front fascia": (0.35, 0.75, 0.45), "tail panel": (0.9, 0.4, 0.35),
       "hood": (0.95, 0.75, 0.25), "windshield": (0.2, 0.25, 0.32), "roof": (0.5, 0.55, 0.62), "side glass": (0.3, 0.38, 0.48),
       "engine cover / fastback": (0.85, 0.6, 0.2), "front fender": (0.6, 0.85, 0.35), "front fender top": (0.75, 0.92, 0.5), "rear quarter top": (0.98, 0.72, 0.78), "body side": (0.75, 0.55, 0.9),
       "rear quarter": (0.95, 0.55, 0.65), "sill": (0.55, 0.4, 0.75), "front bumper corner": (0.3, 0.65, 0.55),
       "rear bumper corner": (0.8, 0.3, 0.45), "side intake": (0.08, 0.08, 0.1), "front corner intake": (0.1, 0.1, 0.12),
       "tail light recess": (0.75, 0.1, 0.1), "diffuser opening": (0.12, 0.12, 0.14), "recess (other)": (0.5, 0.5, 0.5)}
C = np.array([PAL.get(p, (1, 0, 1)) for p in lab]) * 0.55 + 0.45      # pale panels so the curves stand out
allQ = np.vstack(list(W.values())); d, _ = cKDTree(allQ).query(s.triangles_center)
C[d < EDGE * 0.6] = (0.05, 0.05, 0.05)
dn, _ = cKDTree(nodes).query(s.triangles_center); C[dn < 22] = (0.85, 0.05, 0.05)
render_sheet(np.asarray(V, float), F, C, OUT, N=vertex_normals(np.asarray(V, float), F))
